"""AWF Guard: ast mutation."""
from __future__ import annotations

from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional
from pathlib import Path
from typing import Tuple
from typing import Union
from awf_guard_numeric_contracts import finite_call as _finite_call
from awf_guard_numeric_contracts import finite_float as _finite_float
from awf_guard_numeric_contracts import finite_inputs as _finite_inputs
import ast
import copy
import inspect
import math
import numpy as np
import tempfile
from .errors import AntiGoodhartGateError
from .ast_utils import _unwrap_target_fn
from .ast_utils import text_dedent


@_finite_inputs
def scan_ast_for_loose_tolerance_inflation(
    test_source_code: Union[ast.AST, str],
    max_allowed_atol: float = 1e-2,
    max_allowed_rtol: float = 5e-2,
    min_allowed_places: int = 3,
) -> List[Dict[str, Any]]:
    """
    Scan test or verifier AST for artificially inflated numerical tolerances (`atol=10.0`,
    `rtol=0.5`, `rel=0.5`, `abs=5.0`, `places=0`, `delta=10.0`) that let wrong/mutated
    operators pass assertions without detection.
    """
    if isinstance(test_source_code, str):
        if not test_source_code.strip():
            return []
        tree: ast.AST = ast.parse(text_dedent(test_source_code))
    else:
        tree = test_source_code
    findings: List[Dict[str, Any]] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            fn_name = getattr(node.func, "id", None) or getattr(node.func, "attr", None) or ""
            if fn_name in (
                "allclose",
                "isclose",
                "assert_allclose",
                "assert_array_almost_equal",
                "assert_almost_equal",
                "assertAlmostEqual",
                "approx",
                "gmt_approximately",
            ):
                for kw in node.keywords:
                    if kw.arg in ("atol", "abs", "delta", "abs_tol") and isinstance(kw.value, ast.Constant) and isinstance(
                        kw.value.value, (int, float)
                    ):
                        val = _finite_float(kw.value.value)
                        if val > max_allowed_atol:
                            findings.append({
                                "kind": "InflatedAbsoluteTolerance",
                                "call": fn_name,
                                "arg": kw.arg,
                                "value": val,
                                "ceiling": max_allowed_atol,
                                "line": node.lineno,
                                "detail": (
                                    f"`{fn_name}(..., {kw.arg}={val})` at line {node.lineno} exceeds "
                                    f"max_allowed_atol={max_allowed_atol} (tolerance inflation masks errors)."
                                ),
                            })
                    elif kw.arg in ("rtol", "rel") and isinstance(kw.value, ast.Constant) and isinstance(
                        kw.value.value, (int, float)
                    ):
                        val = _finite_float(kw.value.value)
                        if val > max_allowed_rtol:
                            findings.append({
                                "kind": "InflatedRelativeTolerance",
                                "call": fn_name,
                                "arg": kw.arg,
                                "value": val,
                                "ceiling": max_allowed_rtol,
                                "line": node.lineno,
                                "detail": (
                                    f"`{fn_name}(..., {kw.arg}={val})` at line {node.lineno} exceeds "
                                    f"max_allowed_rtol={max_allowed_rtol} (tolerance inflation masks errors)."
                                ),
                            })
                    elif kw.arg in ("places", "decimal") and isinstance(kw.value, ast.Constant) and isinstance(
                        kw.value.value, int
                    ):
                        val_i = int(kw.value.value)
                        if val_i < min_allowed_places:
                            findings.append({
                                "kind": "UnderConstrainedDecimalPlaces",
                                "call": fn_name,
                                "arg": kw.arg,
                                "value": val_i,
                                "floor": min_allowed_places,
                                "line": node.lineno,
                                "detail": (
                                    f"`{fn_name}(..., {kw.arg}={val_i})` at line {node.lineno} is below "
                                    f"min_allowed_places={min_allowed_places}."
                                ),
                            })
    return findings


def _inject_mutant_while_loop_tripwire(node: ast.AST, max_iter: int = 50000) -> None:
    """Inject a bounded iteration tripwire into every `ast.While` in a mutant AST so infinite-loop mutants fail fast."""
    for child in ast.iter_child_nodes(node):
        _inject_mutant_while_loop_tripwire(child, max_iter=max_iter)
    for attr in ("body", "orelse", "finalbody"):
        stmts = getattr(node, attr, None)
        if not isinstance(stmts, list):
            continue
        new_stmts: List[ast.stmt] = []
        for stmt in stmts:
            if isinstance(stmt, ast.While):
                init_stmt = ast.parse("_ag_while_guard = 0").body[0]
                guard_stmts = ast.parse(
                    f"_ag_while_guard += 1\nif _ag_while_guard > {int(max_iter)}:\n    raise RuntimeError('MutantWhileLoopTimeout')"
                ).body
                stmt.body = guard_stmts + list(stmt.body)
                new_stmts.append(init_stmt)
            new_stmts.append(stmt)
        setattr(node, attr, new_stmts)


def _collect_ast_mutation_specs(
    base_tree: ast.Module,
    target_name: str,
    max_mutants: int,
) -> List[Tuple[str, ast.Module]]:
    import copy

    mutant_specs: List[Tuple[str, ast.Module]] = []
    target_fn_node = next(n for n in base_tree.body if isinstance(n, ast.FunctionDef) and n.name == target_name)
    all_nodes = list(ast.walk(target_fn_node))

    for idx, sub in enumerate(all_nodes):
        if len(mutant_specs) >= max_mutants:
            break
        if isinstance(sub, ast.BinOp) and isinstance(sub.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow)):
            mut_tree = copy.deepcopy(base_tree)
            mut_fn_node = next(n for n in mut_tree.body if isinstance(n, ast.FunctionDef) and n.name == target_name)
            mut_sub = list(ast.walk(mut_fn_node))[idx]
            assert isinstance(mut_sub, ast.BinOp)
            if isinstance(sub.op, ast.Add):
                mut_sub.op = ast.Sub()
                desc = f"line {getattr(sub, 'lineno', 0)}: BinOp `+` -> `-`"
            elif isinstance(sub.op, ast.Sub):
                mut_sub.op = ast.Add()
                desc = f"line {getattr(sub, 'lineno', 0)}: BinOp `-` -> `+`"
            elif isinstance(sub.op, ast.Mult):
                mut_sub.op = ast.Div()
                desc = f"line {getattr(sub, 'lineno', 0)}: BinOp `*` -> `/`"
            elif isinstance(sub.op, ast.Div):
                mut_sub.op = ast.Mult()
                desc = f"line {getattr(sub, 'lineno', 0)}: BinOp `/` -> `*`"
            else:
                mut_sub.op = ast.Mult()
                desc = f"line {getattr(sub, 'lineno', 0)}: BinOp `**` -> `*`"
            _inject_mutant_while_loop_tripwire(mut_fn_node)
            mutant_specs.append((desc, mut_tree))

        elif isinstance(sub, ast.Compare) and len(sub.ops) == 1 and isinstance(
            sub.ops[0], (ast.GtE, ast.Gt, ast.LtE, ast.Lt, ast.Eq, ast.NotEq)
        ):
            mut_tree = copy.deepcopy(base_tree)
            mut_fn_node = next(n for n in mut_tree.body if isinstance(n, ast.FunctionDef) and n.name == target_name)
            mut_sub = list(ast.walk(mut_fn_node))[idx]
            assert isinstance(mut_sub, ast.Compare)
            op0 = sub.ops[0]
            if isinstance(op0, ast.GtE):
                mut_sub.ops[0] = ast.Lt()
                desc = f"line {getattr(sub, 'lineno', 0)}: Compare `>=` -> `<`"
            elif isinstance(op0, ast.Gt):
                mut_sub.ops[0] = ast.LtE()
                desc = f"line {getattr(sub, 'lineno', 0)}: Compare `>` -> `<=`"
            elif isinstance(op0, ast.LtE):
                mut_sub.ops[0] = ast.Gt()
                desc = f"line {getattr(sub, 'lineno', 0)}: Compare `<=` -> `>`"
            elif isinstance(op0, ast.Lt):
                mut_sub.ops[0] = ast.GtE()
                desc = f"line {getattr(sub, 'lineno', 0)}: Compare `<` -> `>=`"
            elif isinstance(op0, ast.Eq):
                mut_sub.ops[0] = ast.NotEq()
                desc = f"line {getattr(sub, 'lineno', 0)}: Compare `==` -> `!=`"
            else:
                mut_sub.ops[0] = ast.Eq()
                desc = f"line {getattr(sub, 'lineno', 0)}: Compare `!=` -> `==`"
            _inject_mutant_while_loop_tripwire(mut_fn_node)
            mutant_specs.append((desc, mut_tree))

        elif (
            isinstance(sub, ast.If)
            and len(sub.body) == 1
            and isinstance(sub.body[0], ast.Return)
            and sub.body[0].value is not None
            and not any(isinstance(n, (ast.BinOp, ast.Compare)) for n in ast.walk(sub.body[0].value))
        ):
            mut_tree = copy.deepcopy(base_tree)
            mut_fn_node = next(n for n in mut_tree.body if isinstance(n, ast.FunctionDef) and n.name == target_name)
            mut_if = list(ast.walk(mut_fn_node))[idx]
            assert isinstance(mut_if, ast.If)
            mut_if.body = ast.parse("raise RuntimeError('MutantEarlyReturnBranchTripwire')").body
            desc = f"line {getattr(sub.body[0], 'lineno', 0)}: EarlyReturn branch body tripwire"
            _inject_mutant_while_loop_tripwire(mut_fn_node)
            mutant_specs.append((desc, mut_tree))
    return mutant_specs


@_finite_inputs
def evaluate_ast_mutation_kill_rate(
    fn_or_source: Union[Callable[..., Any], str],
    assertion_check_fn: Callable[[Callable[..., Any]], bool],
    fn_name: Optional[str] = None,
    extra_globals: Optional[Dict[str, Any]] = None,
    min_kill_rate: float = 0.80,
    max_mutants: int = 35,
) -> Dict[str, Any]:
    """
    AST Mutation Testing Engine inspired by `boxed/mutmut`:
    Verifies Clean-Test & Forced-Fail sanity, generates single-site AST mutants (`BinOp` and `Compare`),
    loads each mutant via isolated module loader in a clean-room tempdir (zero `exec`/`eval`), and enforces
    `kill_rate = killed / total_mutants >= min_kill_rate` (`G5j`).
    """
    import copy
    import importlib.util

    if callable(fn_or_source):
        raw_fn = _finite_call(_unwrap_target_fn, fn_or_source)
        src = text_dedent(inspect.getsource(raw_fn))
        target_name = fn_name or raw_fn.__name__
        base_globals: Dict[str, Any] = dict(getattr(raw_fn, "__globals__", {}))
    else:
        src = text_dedent(fn_or_source)
        base_globals = {"np": np, "math": math}
        tree_tmp = ast.parse(src)
        first_fn = next((n for n in tree_tmp.body if isinstance(n, ast.FunctionDef)), None)
        if first_fn is None:
            raise AntiGoodhartGateError("[AST Mutation Engine] No function definition found in source!")
        target_name = fn_name or first_fn.name

    if extra_globals:
        base_globals.update(extra_globals)

    base_tree = ast.parse(src)
    for node in base_tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == target_name:
            node.decorator_list = []

    with tempfile.TemporaryDirectory(prefix="ag_mutmut_") as tmp_dir:
        mod_counter = {"idx": 0}

        def _load_ast_fn(tree_obj: ast.Module) -> Callable[..., Any]:
            ast.fix_missing_locations(tree_obj)
            mod_counter["idx"] += 1
            mod_name = f"_ag_mutant_{mod_counter['idx']}"
            mod_file = Path(tmp_dir) / f"{mod_name}.py"
            mod_file.write_text(ast.unparse(tree_obj) + "\n", encoding="utf-8")
            spec_m = importlib.util.spec_from_file_location(mod_name, mod_file)
            assert spec_m is not None and spec_m.loader is not None
            mod_obj = importlib.util.module_from_spec(spec_m)
            for gk, gv in base_globals.items():
                if not gk.startswith("__"):
                    setattr(mod_obj, gk, gv)
            spec_m.loader.exec_module(mod_obj)
            return getattr(mod_obj, target_name)

        clean_fn = _finite_call(_load_ast_fn, copy.deepcopy(base_tree))
        if not bool(_finite_call(assertion_check_fn, clean_fn)):
            raise AntiGoodhartGateError(
                f"[Mutmut Clean-Test Sanity Failure] Unmutated function `{target_name}` failed `assertion_check_fn`!"
            )

        def _forced_fail_mutant(*_a: Any, **_k: Any) -> Any:
            raise RuntimeError("Forced mutant failure")

        try:
            forced_res = bool(_finite_call(assertion_check_fn, _forced_fail_mutant))
        except Exception:
            forced_res = False
        if forced_res:
            raise AntiGoodhartGateError(
                f"[Mutmut Forced-Fail Sanity Trap] `assertion_check_fn` returned True even when `{target_name}` raised RuntimeError!"
            )

        mutant_specs = _collect_ast_mutation_specs(base_tree, target_name, max_mutants)
        if not mutant_specs:
            raise AntiGoodhartGateError(f"[Mutmut AST Mutation Engine] Zero mutable AST operators found in `{target_name}`!")

        killed = 0
        survived_descriptions: List[str] = []
        for desc, m_tree in mutant_specs:
            try:
                m_fn = _finite_call(_load_ast_fn, m_tree)
                passed_check = bool(_finite_call(assertion_check_fn, m_fn))
            except Exception:
                passed_check = False
            if not passed_check:
                killed += 1
            else:
                survived_descriptions.append(desc)

    total = len(mutant_specs)
    kill_rate = killed / max(total, 1)
    passed = kill_rate >= min_kill_rate
    return {
        "status": "PASS" if passed else "FAIL",
        "function": target_name,
        "total_mutants": total,
        "killed_mutants": killed,
        "survived_mutants": len(survived_descriptions),
        "kill_rate": round(kill_rate, 4),
        "min_kill_rate": min_kill_rate,
        "survived_details": survived_descriptions,
    }


_DEFAULT_MUTATION_MAX_ATOL = 1e-2


_DEFAULT_MUTATION_MAX_RTOL = 5e-2


_DEFAULT_MUTATION_MIN_KILL_RATE = 0.80
