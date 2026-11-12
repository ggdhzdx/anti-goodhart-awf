"""AWF Guard: ast structure."""
from __future__ import annotations

from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Set
from typing import Tuple
from typing import Union
from awf_guard_numeric_contracts import finite_float as _finite_float
from awf_guard_numeric_contracts import finite_inputs as _finite_inputs
import ast
import io
import re
import tokenize
import zlib
from .ast_dataflow import _iter_func_body_no_nested
from .ast_dataflow import _name_refs
from .ast_dataflow import compute_parameter_taint_flow


_INTENT_RULES: Tuple[Tuple[str, re.Pattern[str], str], ...] = (
    (
        "no_recursion",
        re.compile(r"\b(recursive|recursion|recurse|recursively)\b", re.IGNORECASE),
        "claims recursion in docstring/contract but contains no self-call in AST",
    ),
    (
        "no_loop",
        re.compile(r"\b(iterative|iteratively|iterate|loop\s+through|loop\s+over|self[-\s]consistent)\b", re.IGNORECASE),
        "claims iterative/loop execution in docstring/contract but contains no For/While/comprehension in AST",
    ),
    (
        "no_sort",
        re.compile(r"\b(sort|sorting|sorted)\b", re.IGNORECASE),
        "claims sorting in docstring/contract but calls neither sorted(), .sort(), argsort(), nor heapq",
    ),
    (
        "no_memoization",
        re.compile(r"\b(dynamic[-\s]programming|memoize|memoized|memoization|tabulation|bottom[-\s]up\s+dp)\b", re.IGNORECASE),
        "claims dynamic programming/memoization but has neither cache decorator nor loop table mutation",
    ),
    (
        "no_computation_or_reduction",
        re.compile(r"(\\int\b|\\sum\b|\\nabla\b|\\partial\b|\bcompute\b|\bcalculate\b|\bintegrate\b)", re.IGNORECASE),
        "claims mathematical computation/integration/summation but performs no arithmetic or array reduction in AST",
    ),
    (
        "no_exponential_operator",
        re.compile(r"(\\exp\b|\bexp\s*\()"),
        "declares explicit exponential operator (`\\exp` or `exp(...)`) in contract/docstring but invokes no exponential or power operator in AST",
    ),
    (
        "no_logarithmic_operator",
        re.compile(r"(\\ln\b|\\log\b|\bln\s*\(|\blog\s*\()"),
        "declares explicit logarithmic operator (`\\ln`, `\\log`, or `log(...)`) in contract/docstring but invokes no logarithm in AST",
    ),
)


_REDUCTION_AND_MATH_CALLS = {
    "sum", "cumsum", "prod", "mean", "std", "var", "dot", "matmul", "einsum",
    "trapz", "trapezoid", "simpson", "quad", "diff", "gradient", "norm", "svd", "eig", "eigh", "solve",
}


_EXP_OPERATOR_CALLS = {"exp", "expm", "exp2", "expm1", "logsumexp", "softmax"}


_LOG_OPERATOR_CALLS = {"log", "log2", "log10", "log1p", "logsumexp"}


def _extract_decorator_math_contract(func_node: Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> str:
    """Extract `math_contract='...'` string literal from `@scientific_atom(...)` decorator if present."""
    for dec in func_node.decorator_list:
        if isinstance(dec, ast.Call):
            for kw in dec.keywords:
                if kw.arg == "math_contract" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                    return kw.value.value
    return ""


_META_VERIFIER_FN_PREFIXES = (
    "audit_",
    "scan_",
    "verify_",
    "detect_",
    "evaluate_",
    "check_",
    "score_",
    "analyze_",
    "find_",
    "compute_verifier_",
)


def _strip_code_spans_from_docstring(doc: str) -> str:
    """Remove inline backtick code spans and fenced code blocks before matching prose intent rules."""
    no_fenced = re.sub(r"```.*?```", " ", doc, flags=re.DOTALL)
    return re.sub(r"`[^`]*`", " ", no_fenced)


def analyze_contract_and_docstring_intent(
    tree: ast.AST,
    extra_contract_by_fn: Optional[Dict[str, str]] = None,
) -> List[Dict[str, Any]]:
    """
    Deterministic Intent-vs-AST Structure Consistency Guard (absorbed & extended from `ast_guard/intent.py`).
    Checks each function's docstring AND `@scientific_atom(math_contract=...)` against its actual AST.
    """
    violations: List[Dict[str, Any]] = []
    extra_map = extra_contract_by_fn or {}

    for func_node in ast.walk(tree):
        if not isinstance(func_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if func_node.name not in extra_map and func_node.name.startswith(_META_VERIFIER_FN_PREFIXES):
            continue
        raw_doc = ast.get_docstring(func_node) or ""
        doc = _strip_code_spans_from_docstring(raw_doc)
        contract_str = extra_map.get(func_node.name, "") or _extract_decorator_math_contract(func_node)
        combined_text = f"{doc}\n{contract_str}".strip()
        if len(combined_text) < 12:
            continue

        body_nodes = list(_iter_func_body_no_nested(func_node))

        for tag, pattern, explanation_suffix in _INTENT_RULES:
            m = pattern.search(combined_text)
            if not m:
                continue

            ok = True
            if tag == "no_recursion":
                ok = any(
                    isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == func_node.name
                    for n in body_nodes
                )
            elif tag == "no_loop":
                ok = any(
                    isinstance(n, (ast.For, ast.While, ast.AsyncFor, ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp))
                    for n in body_nodes
                )
            elif tag == "no_sort":
                ok = any(
                    isinstance(n, ast.Call) and (
                        (isinstance(n.func, ast.Name) and n.func.id in ("sorted", "argsort"))
                        or (isinstance(n.func, ast.Attribute) and n.func.attr in ("sort", "sort_values", "argsort"))
                        or (isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Name) and n.func.value.id == "heapq")
                    )
                    for n in body_nodes
                )
            elif tag == "no_memoization":
                has_cache_dec = any(
                    (isinstance(d, ast.Name) and d.id in ("cache", "lru_cache", "cached_property"))
                    or (isinstance(d, ast.Attribute) and d.attr in ("cache", "lru_cache", "cached_property"))
                    or (isinstance(d, ast.Call) and getattr(d.func, "id", getattr(d.func, "attr", "")) in ("cache", "lru_cache"))
                    for d in func_node.decorator_list
                )
                has_loop_table = False
                for n in body_nodes:
                    if isinstance(n, (ast.For, ast.While, ast.AsyncFor)):
                        for sub in ast.walk(n):
                            if isinstance(sub, ast.Assign) and any(isinstance(t, ast.Subscript) for t in sub.targets):
                                has_loop_table = True
                            elif isinstance(sub, ast.AugAssign) and isinstance(sub.target, ast.Subscript):
                                has_loop_table = True
                            elif isinstance(sub, ast.Call) and isinstance(sub.func, ast.Attribute) and sub.func.attr in ("append", "extend", "update"):
                                has_loop_table = True
                ok = has_cache_dec or has_loop_table
            elif tag == "no_computation_or_reduction":
                has_arith = any(
                    isinstance(n, (ast.BinOp, ast.AugAssign))
                    or (isinstance(n, ast.UnaryOp) and isinstance(n.op, (ast.USub, ast.UAdd, ast.Invert)))
                    for n in body_nodes
                )
                has_math_call = any(
                    isinstance(n, ast.Call) and (
                        (isinstance(n.func, ast.Name) and n.func.id in _REDUCTION_AND_MATH_CALLS)
                        or (isinstance(n.func, ast.Attribute) and n.func.attr in _REDUCTION_AND_MATH_CALLS)
                    )
                    for n in body_nodes
                )
                ok = has_arith or has_math_call
            elif tag == "no_exponential_operator":
                ok = any(
                    (isinstance(n, ast.Call) and getattr(n.func, "id", getattr(n.func, "attr", "")) in _EXP_OPERATOR_CALLS)
                    or (isinstance(n, ast.BinOp) and isinstance(n.op, ast.Pow))
                    for n in body_nodes
                )
            elif tag == "no_logarithmic_operator":
                ok = any(
                    isinstance(n, ast.Call) and getattr(n.func, "id", getattr(n.func, "attr", "")) in _LOG_OPERATOR_CALLS
                    for n in body_nodes
                )

            if not ok:
                violations.append({
                    "kind": f"IntentStructureMismatch_{tag}",
                    "function": func_node.name,
                    "line": func_node.lineno,
                    "matched_keyword": m.group(0),
                    "detail": f"Function `{func_node.name}` {explanation_suffix} (matched: {m.group(0)!r}).",
                })

    return violations


def strip_python_comments(code: str) -> str:
    """Remove Python `#` comments via `tokenize` so comments do not distort LZ77 compression ratios."""
    try:
        tokens = []
        reader = io.StringIO(code).readline
        for tt, ts, _, _, _ in tokenize.generate_tokens(reader):
            if tt == tokenize.COMMENT:
                continue
            tokens.append((tt, ts))
        return tokenize.untokenize(tokens)
    except tokenize.TokenError:
        return code


def compute_ncc_test_overlap(
    solver_code: str,
    test_suite_code: str,
    ncc_floor: float = 0.72,
    min_code_bytes: int = 100,
) -> Dict[str, Any]:
    """
    Information-Theoretic Normalized Compression Complexity (NCC) Test-Literal Overlap Check
    (absorbed from `ast_guard/check_ncc.py`).
    Computes `NCC = C(code | tests) / C(code)` using `zlib` preset dictionary compression.
    Low NCC (< `ncc_floor`) indicates the test suite acts as an LZ77 dictionary for the solver,
    proving the solver memorized/copied test literals!
    """
    cleaned_code = strip_python_comments(solver_code)
    c_bytes = cleaned_code.encode("utf-8")
    t_bytes = test_suite_code.encode("utf-8")
    if len(c_bytes) < min_code_bytes or not t_bytes:
        return {"applicable": False, "ncc_score": None, "passed": True}

    c_alone = len(zlib.compress(c_bytes, 6))
    if c_alone == 0:
        return {"applicable": False, "ncc_score": None, "passed": True}

    comp_obj = zlib.compressobj(6, zlib.DEFLATED, zlib.MAX_WBITS, zlib.DEF_MEM_LEVEL, zlib.Z_DEFAULT_STRATEGY, t_bytes[-32768:])
    c_given_t = len(comp_obj.compress(c_bytes) + comp_obj.flush())
    ncc_val = _finite_float(c_given_t) / _finite_float(c_alone)
    passed = ncc_val >= ncc_floor
    return {
        "applicable": True,
        "ncc_score": round(ncc_val, 4),
        "ncc_floor": ncc_floor,
        "passed": passed,
    }


def _calculate_mccabe(root_node: ast.AST) -> int:
    """Calculate McCabe cyclomatic complexity of a function/module, skipping nested defs/classes."""
    complexity = 1
    queue = [root_node]
    while queue:
        node = queue.pop(0)
        if node is not root_node and isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        if isinstance(node, (ast.If, ast.IfExp, ast.For, ast.While, ast.AsyncFor, ast.ExceptHandler, ast.With, ast.Assert)):
            complexity += 1
        elif isinstance(node, ast.BoolOp):
            complexity += max(0, len(node.values) - 1)
        elif hasattr(ast, "match_case") and isinstance(node, ast.match_case):
            complexity += 1
        for child in ast.iter_child_nodes(node):
            queue.append(child)
    return complexity


def _collect_qualified_functions(tree: ast.AST) -> Dict[str, Union[ast.FunctionDef, ast.AsyncFunctionDef]]:
    funcs: Dict[str, Union[ast.FunctionDef, ast.AsyncFunctionDef]] = {}

    def visit(node: ast.AST, prefix: str) -> None:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            qname = f"{prefix}.{node.name}" if prefix else node.name
            funcs[qname] = node
            child_prefix = qname
        elif isinstance(node, ast.ClassDef):
            child_prefix = f"{prefix}.{node.name}" if prefix else node.name
        else:
            child_prefix = prefix
        for ch in ast.iter_child_nodes(node):
            visit(ch, child_prefix)

    visit(tree, "")
    return funcs


_TRIVIAL_SENTINEL_CONSTANTS = frozenset({0, 1, -1, 2, None, True, False, ""})


@_finite_inputs
def audit_ast_pair_diff(
    original_code: str,
    generated_code: str,
    complexity_drop_limit: float = 0.60,
    min_orig_complexity: int = 5,
) -> Dict[str, Any]:
    """
    Pair-Mode Baseline Structural Regression Scanner (absorbed from `ast_guard` Check 2, Check 7 & Check 8).
    Compares `original_code` against `generated_code` to catch:
    1. Per-function McCabe Cyclomatic Complexity Collapse (>60% drop, including Rename/Drop-Bypass Guard);
    2. New Specific Constant Bypass (`if param == <new_constant>: return <input_independent_literal>`);
    3. Literal Hijack (replacing a non-trivial original function with input-independent literal returns).
    """
    orig_tree = ast.parse(original_code)
    gen_tree = ast.parse(generated_code)

    orig_funcs = _collect_qualified_functions(orig_tree)
    gen_funcs = _collect_qualified_functions(gen_tree)
    orig_mccabe = {k: _calculate_mccabe(v) for k, v in orig_funcs.items()}
    gen_mccabe = {k: _calculate_mccabe(v) for k, v in gen_funcs.items()}

    orig_loops = sum(
        1 for fn in orig_funcs.values() for n in _iter_func_body_no_nested(fn) if isinstance(n, (ast.For, ast.While, ast.AsyncFor))
    )
    gen_loops = sum(
        1 for fn in gen_funcs.values() for n in _iter_func_body_no_nested(fn) if isinstance(n, (ast.For, ast.While, ast.AsyncFor))
    )
    orig_comps = sum(
        1 for fn in orig_funcs.values() for n in _iter_func_body_no_nested(fn) if isinstance(n, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp))
    )
    gen_comps = sum(
        1 for fn in gen_funcs.values() for n in _iter_func_body_no_nested(fn) if isinstance(n, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp))
    )
    legit_comp_upgrade = (gen_loops < orig_loops) and (gen_comps > orig_comps)

    violations: List[Dict[str, Any]] = []

    # 1. Per-function Complexity Collapse + Rename/Drop Bypass Guard
    common_names = sorted(set(orig_mccabe.keys()) & set(gen_mccabe.keys()))
    for qname in common_names:
        c_orig = orig_mccabe[qname]
        c_gen = gen_mccabe[qname]
        branch_kinds = (ast.If, ast.IfExp, ast.Match, ast.Try, ast.BoolOp, ast.For, ast.While, ast.comprehension)
        old_branches = sum(isinstance(n, branch_kinds) for n in _iter_func_body_no_nested(orig_funcs[qname]))
        new_branches = sum(isinstance(n, branch_kinds) for n in _iter_func_body_no_nested(gen_funcs[qname]))
        if old_branches > new_branches:
            violations.append({"kind": "RemovedControlFlow", "function": qname, "line": gen_funcs[qname].lineno, "detail": "Control-flow branch removed; semantic equivalence needs explicit review"})
        if c_orig >= min_orig_complexity and not legit_comp_upgrade:
            drop_ratio = (c_orig - c_gen) / _finite_float(c_orig)
            if drop_ratio >= complexity_drop_limit:
                violations.append({
                    "kind": "ComplexityCollapse",
                    "function": qname,
                    "line": gen_funcs[qname].lineno,
                    "detail": (
                        f"McCabe complexity of `{qname}` collapsed by {int(drop_ratio*100)}% "
                        f"(from {c_orig} to {c_gen}, limit <= {int(complexity_drop_limit*100)}%)."
                    ),
                })

    dropped_names = sorted(set(orig_mccabe.keys()) - set(gen_mccabe.keys()))
    new_names = sorted(set(gen_mccabe.keys()) - set(orig_mccabe.keys()))
    for dropped in dropped_names:
        violations.append({"kind": "RemovedFunction", "function": dropped, "line": 1, "detail": "Function removed or renamed; cannot certify equivalence from complexity"})
    if dropped_names and not legit_comp_upgrade:
        dropped_sum = sum(orig_mccabe[n] for n in dropped_names)
        new_sum = sum(gen_mccabe[n] for n in new_names)
        if dropped_sum >= min_orig_complexity:
            drop_ratio = (dropped_sum - new_sum) / _finite_float(dropped_sum)
            if drop_ratio >= complexity_drop_limit:
                violations.append({
                    "kind": "RenamedOrDroppedComplexityCollapse",
                    "function": ",".join(dropped_names),
                    "line": 1,
                    "detail": (
                        f"Original function(s) {dropped_names} (total complexity {dropped_sum}) were dropped/renamed "
                        f"to {new_names} (total complexity {new_sum}, drop {int(drop_ratio*100)}%)."
                    ),
                })

    # Collect all scalar constants present in original_code
    orig_scalars: Set[Any] = set()
    unhashable_count = 0
    for n in ast.walk(orig_tree):
        if isinstance(n, ast.Constant):
            try:
                hash(n.value)
                orig_scalars.add(n.value)
            except TypeError:
                unhashable_count += 1

    # 2. New Specific Constant Bypass (Check 8) & 3. Literal Hijack (Check 7)
    for qname, gfunc in gen_funcs.items():
        if qname not in orig_funcs:
            continue
        if orig_mccabe[qname] < 1 and len(orig_funcs[qname].body) < 2:
            continue
        orig_tainted = compute_parameter_taint_flow(orig_funcs[qname])
        tainted = compute_parameter_taint_flow(gfunc)
        if not tainted:
            continue

        # Check 7: Literal Hijack (original returns depended on parameters; generated returns are parameter-independent)
        orig_returns = [n for n in _iter_func_body_no_nested(orig_funcs[qname]) if isinstance(n, ast.Return) and n.value is not None]
        gen_returns = [n for n in _iter_func_body_no_nested(gfunc) if isinstance(n, ast.Return) and n.value is not None]
        gen_branch_taint = any(
            isinstance(n, (ast.If, ast.While, ast.For, ast.AsyncFor)) and bool(_name_refs(n) & tainted)
            for n in _iter_func_body_no_nested(gfunc)
        )
        if (
            orig_returns
            and any(bool(_name_refs(r.value) & orig_tainted) for r in orig_returns if r.value is not None)
            and gen_returns
            and not gen_branch_taint
            and not any(bool(_name_refs(r.value) & tainted) for r in gen_returns if r.value is not None)
        ):
            violations.append({
                "kind": "LiteralHijack",
                "function": qname,
                "line": gfunc.lineno,
                "detail": f"Function `{qname}` replaced parameter-dependent baseline computation with input-independent return(s).",
            })

        # Check 8: top-level if branch comparing tainted expr against a new specific constant with input-independent return
        for stmt in _iter_func_body_no_nested(gfunc):
            if isinstance(stmt, ast.If):
                has_new_const_vs_tainted = False
                for sub in ast.walk(stmt.test):
                    if isinstance(sub, ast.Compare):
                        sides = [sub.left] + list(sub.comparators)
                        has_tainted_side = any(bool(_name_refs(s) & tainted) for s in sides)
                        has_new_const_side = any(
                            isinstance(s, ast.Constant)
                            and s.value not in orig_scalars
                            and s.value not in _TRIVIAL_SENTINEL_CONSTANTS
                            for s in sides
                        )
                        if has_tainted_side and has_new_const_side:
                            has_new_const_vs_tainted = True
                            break
                if has_new_const_vs_tainted:
                    has_indep_return = any(
                        isinstance(b, ast.Return) and b.value is not None and not (_name_refs(b.value) & tainted)
                        for b in stmt.body
                    )
                    if has_indep_return:
                        violations.append({
                            "kind": "NewConstantBypass",
                            "function": qname,
                            "line": stmt.lineno,
                            "detail": (
                                f"Function `{qname}` at line {stmt.lineno} compares parameter against a new "
                                f"specific constant absent from baseline and returns an input-independent value."
                            ),
                        })

    return {
        "status": "PASS" if not violations else "FAIL",
        "violation_count": len(violations),
        "unhashable_constant_count": unhashable_count,
        "violations": violations,
    }


_DUNDER_COMPARE_METHODS = frozenset({"__eq__", "__ne__", "__bool__", "__lt__", "__le__", "__gt__", "__ge__"})


_STACK_INTROSPECT_CALLS = frozenset({
    "inspect.currentframe", "inspect.stack", "inspect.getframeinfo", "inspect.getouterframes", "sys._getframe", "_getframe",
})


_TIMER_MONKEYPATCH_ATTRS = frozenset({"time", "perf_counter", "sleep", "monotonic", "process_time"})


@_finite_inputs
def scan_ast_for_harness_tampering(tree: ast.AST) -> List[Dict[str, Any]]:
    """
    Scan AST for anti-harness tampering and obfuscation patterns (absorbed from `ast_guard` Check 3 & Check 6):
    1. `DunderEqualityHijack`: overriding `__eq__`/`__bool__` to return constant `True`/`False`/`0`/`1`;
    2. `ZeroStrideMemorySpoofing`: `as_strided(..., strides=(0, 0, ...))`;
    3. `StackFrameIntrospection`: `sys._getframe()` / `inspect.stack()` probing test harness locals;
    4. `TimerOrModuleMonkeyPatch`: `time.perf_counter = ...`, `sys.modules[...] = ...`, `os.environ['PYTHONOPTIMIZE'] = ...`;
    5. `ObfuscatedExecOrBuiltins`: `eval`/`exec` aliasing (`g = eval`), `__builtins__['ev'+'al']`, `getattr(__builtins__, ...)`.
    """
    violations: List[Dict[str, Any]] = []

    # Track aliases to eval/exec
    forbidden_aliases: Set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Name):
            if node.value.id in ("eval", "exec", "__import__"):
                for tgt in node.targets:
                    if isinstance(tgt, ast.Name):
                        forbidden_aliases.add(tgt.id)
                        violations.append({
                            "kind": "ObfuscatedExecOrBuiltins",
                            "line": getattr(node, "lineno", 0),
                            "detail": f"Forbidden `{node.value.id}` aliased to variable `{tgt.id}`.",
                        })

    for node in ast.walk(tree):
        # 1. Dunder equality/bool hijacking
        if isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name in _DUNDER_COMPARE_METHODS:
                    for stmt in ast.walk(item):
                        if isinstance(stmt, ast.Return) and isinstance(stmt.value, ast.Constant):
                            if stmt.value.value in (True, False, 0, 1):
                                violations.append({
                                    "kind": "DunderEqualityHijack",
                                    "line": getattr(item, "lineno", node.lineno),
                                    "detail": (
                                        f"Class `{node.name}.{item.name}` returns constant `{stmt.value.value!r}` "
                                        f"to spoof equality/truthiness assertions!"
                                    ),
                                })
                                break

        # 2. Call-based checks: Zero-stride `as_strided`, Stack introspection, Obfuscated builtins
        if isinstance(node, ast.Call):
            fn_name = ""
            if isinstance(node.func, ast.Name):
                fn_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                base = getattr(node.func.value, "id", "")
                fn_name = f"{base}.{node.func.attr}" if base else node.func.attr

            if fn_name in _STACK_INTROSPECT_CALLS or node.func == "_getframe" or getattr(node.func, "attr", "") in ("_getframe", "currentframe", "getouterframes"):
                violations.append({
                    "kind": "StackFrameIntrospection",
                    "line": getattr(node, "lineno", 0),
                    "detail": f"Forbidden stack introspection `{fn_name}()` probing caller/harness frame.",
                })

            if fn_name.endswith("as_strided"):
                for kw in node.keywords:
                    if kw.arg == "strides" and isinstance(kw.value, (ast.Tuple, ast.List)) and kw.value.elts:
                        if all(isinstance(e, ast.Constant) and e.value == 0 for e in kw.value.elts):
                            violations.append({
                                "kind": "ZeroStrideMemorySpoofing",
                                "line": getattr(node, "lineno", 0),
                                "detail": "`as_strided()` called with all-zero strides (memory aliasing spoof)!",
                            })

            if isinstance(node.func, ast.Name) and (node.func.id in ("eval", "exec") or node.func.id in forbidden_aliases):
                violations.append({
                    "kind": "ObfuscatedExecOrBuiltins",
                    "line": getattr(node, "lineno", 0),
                    "detail": f"Forbidden dynamic code execution `{node.func.id}()`.",
                })
            elif isinstance(node.func, ast.Name) and node.func.id == "getattr" and len(node.args) >= 1:
                if isinstance(node.args[0], ast.Name) and node.args[0].id in ("builtins", "__builtins__", "_builtins_"):
                    violations.append({
                        "kind": "ObfuscatedExecOrBuiltins",
                        "line": getattr(node, "lineno", 0),
                        "detail": f"Obfuscated `getattr({node.args[0].id}, ...)` builtins lookup.",
                    })
            elif isinstance(node.func, ast.Name) and node.func.id == "setattr" and len(node.args) >= 2:
                if isinstance(node.args[0], ast.Name) and node.args[0].id in ("time", "sys", "os", "builtins", "__builtins__"):
                    violations.append({
                        "kind": "TimerOrModuleMonkeyPatch",
                        "line": getattr(node, "lineno", 0),
                        "detail": f"Dynamic `setattr({node.args[0].id}, ...)` monkey-patching detected.",
                    })

        # 3. Subscript access on __builtins__ / sys.modules / os.environ['PYTHONOPTIMIZE']
        if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name):
            if node.value.id in ("__builtins__", "_builtins_", "builtins"):
                violations.append({
                    "kind": "ObfuscatedExecOrBuiltins",
                    "line": getattr(node, "lineno", 0),
                    "detail": f"Obfuscated subscript access on `{node.value.id}[...]`.",
                })

        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                # time.<attr> = ...
                if (
                    isinstance(tgt, ast.Attribute)
                    and isinstance(tgt.value, ast.Name)
                    and tgt.value.id == "time"
                    and tgt.attr in _TIMER_MONKEYPATCH_ATTRS
                ):
                    violations.append({
                        "kind": "TimerOrModuleMonkeyPatch",
                        "line": getattr(node, "lineno", 0),
                        "detail": f"Timer monkey-patching `time.{tgt.attr} = ...` detected.",
                    })
                # sys.modules[...] = ... or os.environ['PYTHONOPTIMIZE'] = ...
                if isinstance(tgt, ast.Subscript) and isinstance(tgt.value, ast.Attribute) and isinstance(tgt.value.value, ast.Name):
                    mod_id = tgt.value.value.id
                    attr_id = tgt.value.attr
                    if mod_id == "sys" and attr_id == "modules":
                        violations.append({
                            "kind": "TimerOrModuleMonkeyPatch",
                            "line": getattr(node, "lineno", 0),
                            "detail": "`sys.modules[...]` cache manipulation detected.",
                        })
                    elif mod_id == "os" and attr_id == "environ":
                        if isinstance(tgt.slice, ast.Constant) and tgt.slice.value in ("PYTHONOPTIMIZE", "LD_PRELOAD"):
                            violations.append({
                                "kind": "TimerOrModuleMonkeyPatch",
                                "line": getattr(node, "lineno", 0),
                                "detail": f"Forbidden `os.environ[{tgt.slice.value!r}]` harness tampering detected.",
                            })

    return violations
