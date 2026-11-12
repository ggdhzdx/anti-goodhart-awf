"""AWF Guard: ast dataflow."""
from __future__ import annotations

from typing import Any
from typing import Callable
from typing import Dict
from typing import Iterable
from typing import List
from typing import Optional
from typing import Sequence
from typing import Set
from typing import Union
from awf_guard_numeric_contracts import finite_inputs as _finite_inputs
import ast
import inspect
import re
from .errors import AtomicContractViolationError
from .ast_utils import text_dedent


def _iter_func_body_no_nested(func_node: Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> Iterable[ast.AST]:
    """Yield every AST node inside `func_node`, without descending into nested defs/classes."""
    queue: List[ast.AST] = list(func_node.body)
    while queue:
        node = queue.pop(0)
        yield node
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        for child in ast.iter_child_nodes(node):
            queue.append(child)


def _name_refs(node: ast.AST) -> Set[str]:
    return {sub.id for sub in ast.walk(node) if isinstance(sub, ast.Name)}


def _lhs_target_names(target: ast.AST) -> Iterable[str]:
    if isinstance(target, ast.Name):
        yield target.id
    elif isinstance(target, (ast.Tuple, ast.List)):
        for elt in target.elts:
            yield from _lhs_target_names(elt)
    elif isinstance(target, ast.Starred):
        yield from _lhs_target_names(target.value)
    elif isinstance(target, ast.Subscript) and isinstance(target.value, ast.Name):
        yield target.value.id


def _is_pure_literal_expr(node: Optional[ast.AST]) -> bool:
    """True when `node` is a compile-time constant scalar or homogeneous constant container."""
    if node is None:
        return True
    if isinstance(node, ast.Constant):
        return True
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd, ast.Invert, ast.Not)):
        return _is_pure_literal_expr(node.operand)
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        return all(_is_pure_literal_expr(e) for e in node.elts)
    if isinstance(node, ast.Dict):
        return all(
            (k is not None and _is_pure_literal_expr(k) and _is_pure_literal_expr(v))
            for k, v in zip(node.keys, node.values)
        )
    return False


def _taint_mutations_in_subtree(root_node: ast.AST, tainted: Set[str]) -> bool:
    """Propagate taint to all LHS assignment targets and container method receivers inside `root_node`."""
    changed = False
    for body_node in ast.walk(root_node):
        if isinstance(body_node, (ast.Assign, ast.AugAssign)):
            targets = body_node.targets if isinstance(body_node, ast.Assign) else [body_node.target]
            for tgt in targets:
                for nm in _lhs_target_names(tgt):
                    if nm not in tainted:
                        tainted.add(nm)
                        changed = True
        elif isinstance(body_node, ast.Expr) and isinstance(body_node.value, ast.Call):
            func = body_node.value.func
            if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
                if func.value.id not in tainted:
                    tainted.add(func.value.id)
                    changed = True
    return changed


def compute_parameter_taint_flow(
    func_node: Union[ast.FunctionDef, ast.AsyncFunctionDef],
    seed_params: Optional[Set[str]] = None,
) -> Set[str]:
    """
    Fixed-point intra-function forward parameter-taint analysis.
    Computes all variable names that transitively depend on `seed_params` (or all formal parameters
    if `seed_params` is None), tracking `Assign`, `AugAssign`, `AnnAssign`, `If` control-dependence,
    `For`/`While` loop iterators and `continue`/`break` guards, `NamedExpr` (`:=`), `nonlocal`
    accumulators, and mutable container mutations.
    """
    if seed_params is None:
        args = func_node.args
        seed_params = {a.arg for a in (args.posonlyargs + args.args + args.kwonlyargs)}
        if args.vararg:
            seed_params.add(args.vararg.arg)
        if args.kwarg:
            seed_params.add(args.kwarg.arg)

    tainted: Set[str] = set(seed_params)
    changed = True
    iterations = 0
    while changed and iterations < 50:
        changed = False
        iterations += 1
        for stmt in _iter_func_body_no_nested(func_node):
            if isinstance(stmt, ast.Assign) and stmt.value is not None:
                if _name_refs(stmt.value) & tainted:
                    for tgt in stmt.targets:
                        for nm in _lhs_target_names(tgt):
                            if nm not in tainted:
                                tainted.add(nm)
                                changed = True
            elif isinstance(stmt, ast.AugAssign):
                if _name_refs(stmt.value) & tainted:
                    for nm in _lhs_target_names(stmt.target):
                        if nm not in tainted:
                            tainted.add(nm)
                            changed = True
            elif isinstance(stmt, ast.AnnAssign) and stmt.value is not None:
                if _name_refs(stmt.value) & tainted:
                    for nm in _lhs_target_names(stmt.target):
                        if nm not in tainted:
                            tainted.add(nm)
                            changed = True
            elif isinstance(stmt, ast.If):
                if _name_refs(stmt.test) & tainted:
                    if _taint_mutations_in_subtree(stmt, tainted):
                        changed = True
            elif isinstance(stmt, (ast.For, ast.AsyncFor)):
                has_tainted_guard = any(
                    isinstance(sub, ast.If)
                    and (_name_refs(sub.test) & tainted)
                    and any(isinstance(b, (ast.Continue, ast.Break)) for b in ast.walk(sub))
                    for sub in ast.walk(stmt)
                )
                if (_name_refs(stmt.iter) & tainted) or has_tainted_guard:
                    for nm in _lhs_target_names(stmt.target):
                        if nm not in tainted:
                            tainted.add(nm)
                            changed = True
                    if _taint_mutations_in_subtree(stmt, tainted):
                        changed = True
            elif isinstance(stmt, ast.While):
                if _name_refs(stmt.test) & tainted:
                    if _taint_mutations_in_subtree(stmt, tainted):
                        changed = True
            elif isinstance(stmt, ast.NamedExpr):
                if _name_refs(stmt.value) & tainted:
                    if isinstance(stmt.target, ast.Name) and stmt.target.id not in tainted:
                        tainted.add(stmt.target.id)
                        changed = True
            elif isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for inner in ast.walk(stmt):
                    if isinstance(inner, ast.Nonlocal):
                        for nm in inner.names:
                            if nm not in tainted:
                                tainted.add(nm)
                                changed = True
            elif isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
                call = stmt.value
                if isinstance(call.func, ast.Attribute) and isinstance(call.func.value, ast.Name):
                    all_args = list(call.args) + [kw.value for kw in call.keywords]
                    if any(_name_refs(a) & tainted for a in all_args):
                        nm = call.func.value.id
                        if nm not in tainted:
                            tainted.add(nm)
                            changed = True
    return tainted


@_finite_inputs
def verify_atom_input_dataflow(
    fn: Callable[..., Any],
    declared_inputs: Sequence[str],
) -> Dict[str, List[str]]:
    """
    Statically verify via single-parameter taint tracking that EVERY declared input tensor in
    `@scientific_atom(inputs={...})` flows into at least one `return` value (or controls a branch/loop
    that routes to a `return`). Catches Mode I dead-input surrogates at import/decoration time!
    """
    try:
        lines, _ = inspect.getsourcelines(fn)
        src = "".join(lines)
        tree = ast.parse(text_dedent(src))
    except (OSError, SyntaxError):
        return {}

    func_nodes = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    if not func_nodes:
        return {}
    func_node = func_nodes[0]

    returns = [
        n for n in _iter_func_body_no_nested(func_node)
        if isinstance(n, ast.Return) and n.value is not None
    ]
    if not returns:
        raise AtomicContractViolationError(
            f"[Atom Dataflow Trap] `@scientific_atom` function `{fn.__name__}` has no `return <expr>` statement!"
        )

    return_Wait_refs: Set[str] = set()
    for ret in returns:
        assert ret.value is not None
        return_Wait_refs |= _name_refs(ret.value)

    # Also collect names controlling If/While/For conditions that enclose a Return
    control_refs: Set[str] = set()
    for node in _iter_func_body_no_nested(func_node):
        if isinstance(node, (ast.If, ast.While)):
            if any(isinstance(sub, ast.Return) for sub in ast.walk(node)):
                control_refs |= _name_refs(node.test)
        elif isinstance(node, (ast.For, ast.AsyncFor)):
            if any(isinstance(sub, ast.Return) for sub in ast.walk(node)):
                control_refs |= _name_refs(node.iter)

    effective_sink_refs = return_Wait_refs | control_refs
    taint_map: Dict[str, List[str]] = {}
    dead_inputs: List[str] = []

    for inp_name in declared_inputs:
        tainted_from_inp = compute_parameter_taint_flow(func_node, seed_params={inp_name})
        taint_map[inp_name] = sorted(tainted_from_inp)
        if not (tainted_from_inp & effective_sink_refs):
            dead_inputs.append(inp_name)

    if dead_inputs:
        raise AtomicContractViolationError(
            f"[Dead Input Parameter / Literal Hijack Trap] In `@scientific_atom` `{fn.__name__}`, "
            f"declared input parameter(s) {dead_inputs} never flow into any `return` expression! "
            f"Every declared physical input must actively participate in the mathematical computation."
        )
    return taint_map


_IUPAC_ELEMENT_SYMBOLS: Set[str] = {
    "H", "He", "Li", "Be", "B", "C", "N", "O", "F", "Ne", "Na", "Mg", "Al", "Si", "P", "S", "Cl", "Ar",
    "K", "Ca", "Sc", "Ti", "V", "Cr", "Mn", "Fe", "Co", "Ni", "Cu", "Zn", "Ga", "Ge", "As", "Se", "Br", "Kr",
    "Rb", "Sr", "Y", "Zr", "Nb", "Mo", "Tc", "Ru", "Rh", "Pd", "Ag", "Cd", "In", "Sn", "Sb", "Te", "I", "Xe",
    "Cs", "Ba", "La", "Ce", "Pr", "Nd", "Pm", "Sm", "Eu", "Gd", "Tb", "Dy", "Ho", "Er", "Tm", "Yb", "Lu",
    "Hf", "Ta", "W", "Re", "Os", "Ir", "Pt", "Au", "Hg", "Tl", "Pb", "Bi", "Po", "At", "Rn", "U",
}


_SCIENTIFIC_UNIT_KEYS: Set[str] = {
    "Hartree", "eV", "kcal/mol", "kJ/mol", "J", "K", "Bohr", "Angstrom", "nm", "pm", "m", "fs", "ps", "ns", "rad", "deg",
}


def _is_scientific_constant_or_periodic_table_dict(
    table_node: Union[ast.Dict, ast.List, ast.Tuple],
    table_name: str = "",
) -> bool:
    """Return True if a literal dict represents an IUPAC periodic-table property or physical unit table."""
    if not isinstance(table_node, ast.Dict) or not table_node.keys:
        return False
    str_keys = [
        k.value for k in table_node.keys
        if isinstance(k, ast.Constant) and isinstance(k.value, str)
    ]
    if len(str_keys) == len(table_node.keys) and len(str_keys) >= 3:
        elem_hits = sum(1 for s in str_keys if s in _IUPAC_ELEMENT_SYMBOLS)
        unit_hits = sum(1 for s in str_keys if s in _SCIENTIFIC_UNIT_KEYS)
        if elem_hits / len(str_keys) >= _SCI_TABLE_MIN_KEY_FRACTION or unit_hits / len(str_keys) >= _SCI_TABLE_MIN_KEY_FRACTION:
            return True
    if table_name and re.search(
        r"(?i)(?:covalent_radi|vdw_radi|atomic_mass|atomic_num|electronegativ|periodic_table|unit_factor)",
        table_name,
    ):
        if len(str_keys) == len(table_node.keys):
            return True
    return False


@_finite_inputs
def detect_extensional_enumeration_and_dispatch(
    tree: ast.AST,
    min_enum_ifs: int = 5,
    enum_ratio_threshold: float = 0.70,
    min_dispatch_table_size: int = 5,
) -> List[Dict[str, Any]]:
    """
    Detect Mode VI Extensional Enumeration (`if x == const: return lit` chains, `match/case` literal tables,
    ternary `IfExp` chains) AND Dict/List Dispatch Table Memorization (`return TABLE[param]`).
    Exempts legitimate IUPAC chemical periodic-table and physical-unit constant dictionaries.
    """
    violations: List[Dict[str, Any]] = []

    module_dicts: Dict[str, ast.Dict] = {}
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Dict):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    module_dicts[t.id] = node.value

    for func_node in ast.walk(tree):
        if not isinstance(func_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        args = func_node.args
        params = {a.arg for a in (args.posonlyargs + args.args + args.kwonlyargs)}
        if not params:
            continue

        local_dicts: Dict[str, ast.Dict] = {}
        for stmt in _iter_func_body_no_nested(func_node):
            if isinstance(stmt, ast.Assign) and isinstance(stmt.value, ast.Dict):
                for t in stmt.targets:
                    if isinstance(t, ast.Name):
                        local_dicts[t.id] = stmt.value
            elif isinstance(stmt, ast.Return) and stmt.value is not None:
                ret = stmt.value
                table_node: Optional[Union[ast.Dict, ast.List, ast.Tuple]] = None
                table_name = ""
                is_param_keyed = False
                if isinstance(ret, ast.Subscript):
                    sl = ret.slice
                    if isinstance(sl, ast.Name) and sl.id in params:
                        is_param_keyed = True
                    elif (
                        isinstance(sl, ast.Call)
                        and isinstance(sl.func, ast.Name)
                        and sl.func.id in ("int", "str", "float", "bool")
                        and len(sl.args) == 1
                        and isinstance(sl.args[0], ast.Name)
                        and sl.args[0].id in params
                    ):
                        is_param_keyed = True
                    if is_param_keyed:
                        if isinstance(ret.value, (ast.Dict, ast.List, ast.Tuple)):
                            table_node = ret.value
                        elif isinstance(ret.value, ast.Name):
                            table_name = ret.value.id
                            table_node = local_dicts.get(table_name) or module_dicts.get(table_name)
                elif (
                    isinstance(ret, ast.Call)
                    and isinstance(ret.func, ast.Attribute)
                    and ret.func.attr == "get"
                    and len(ret.args) >= 1
                    and isinstance(ret.args[0], ast.Name)
                    and ret.args[0].id in params
                    and isinstance(ret.func.value, ast.Name)
                ):
                    is_param_keyed = True
                    table_name = ret.func.value.id
                    table_node = local_dicts.get(table_name) or module_dicts.get(table_name)

                if is_param_keyed and table_node is not None:
                    if _is_scientific_constant_or_periodic_table_dict(table_node, table_name):
                        continue
                    sz = len(table_node.keys) if isinstance(table_node, ast.Dict) else len(table_node.elts)
                    if _is_pure_literal_expr(table_node) and sz >= min_dispatch_table_size:
                        violations.append({
                            "kind": "DictDispatchMemorization",
                            "function": func_node.name,
                            "line": getattr(stmt, "lineno", func_node.lineno),
                            "detail": (
                                f"Function `{func_node.name}` returns a {sz}-entry all-literal lookup table "
                                f"keyed directly by parameter (memorized answer table replacing algorithm)."
                            ),
                        })

        # 2. Extensional Enumeration scan (`if/elif`, `match/case`, `IfExp`)
        enum_ifs = 0
        total_ifs = 0
        loop_count = 0
        for stmt in _iter_func_body_no_nested(func_node):
            if isinstance(stmt, (ast.For, ast.While, ast.AsyncFor)):
                loop_count += 1
            elif isinstance(stmt, ast.If):
                total_ifs += 1
                if len(stmt.body) <= 2 and isinstance(stmt.test, ast.Compare):
                    if any(
                        isinstance(op, (ast.Eq, ast.In))
                        and (isinstance(c, ast.Constant) or isinstance(stmt.test.left, ast.Constant) or _is_pure_literal_expr(c))
                        for op, c in zip(stmt.test.ops, stmt.test.comparators)
                    ):
                        enum_ifs += 1
            elif hasattr(ast, "match_case") and isinstance(stmt, ast.match_case):
                total_ifs += 1
                if stmt.guard is None and len(stmt.body) <= 2:
                    enum_ifs += 1
            elif isinstance(stmt, ast.IfExp):
                total_ifs += 1
                if isinstance(stmt.test, ast.Compare) and any(
                    isinstance(op, ast.Eq) and (isinstance(c, ast.Constant) or isinstance(stmt.test.left, ast.Constant))
                    for op, c in zip(stmt.test.ops, stmt.test.comparators)
                ):
                    enum_ifs += 1

        if total_ifs >= min_enum_ifs and loop_count <= 1:
            ratio = enum_ifs / max(total_ifs, 1)
            if ratio >= enum_ratio_threshold:
                violations.append({
                    "kind": "ExtensionalEnumeration",
                    "function": func_node.name,
                    "line": func_node.lineno,
                    "detail": (
                        f"Function `{func_node.name}` has {enum_ifs}/{total_ifs} ({int(ratio*100)}%) "
                        f"constant-equality enumeration branches with loops={loop_count}."
                    ),
                })

    return violations


_SCI_TABLE_MIN_KEY_FRACTION = 0.80
