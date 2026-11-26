"""AWF Guard: stripped-AST physics card extraction, outer-glue closure & dual-entry red-team audit."""
from __future__ import annotations

import ast
import copy
import io
import json
import re
import tokenize
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple
from awf_guard_numeric_contracts import finite_float as _finite_float, finite_inputs as _finite_inputs
from .ast_dataflow import _iter_func_body_no_nested
from .ast_utils import text_dedent
from .source_quality import scan_source_for_todo_placeholders_and_magic_numbers

_DEFAULT_MAX_UNWRAPPED_PHYSICS_LINES = 35
_DEFAULT_MAX_UNWRAPPED_MATH_OPS = 10
_DEFAULT_MIN_CV_JSON_FLOOR = 0.005
_MEAN_ACTIVE_FLOOR = 1e-4
_MIN_JSON_SERIES_LEN = 3
_MATH_CALL_NAMES = frozenset({
    "dot", "einsum", "norm", "svd", "eigh", "eig", "solve", "exp", "log", "sqrt", "mean", "std", "sum",
})
_SHARED_BUILDER_PREFIXES = ("build_", "compute_", "calc_", "derive_", "assemble_")
_MANDATORY_REDTEAM_AXES = frozenset({
    "sub_fragment_symmetry_and_multipole",
    "periodic_boundary_and_size_convergence",
    "functional_environment_and_thermodynamic_bounds",
    "cross_station_shared_observable_lock",
})
_MIN_REDTEAM_RISK_ITEMS = 2
_QM_ROUTE_RE = re.compile(r"#p\s+[^\n\"']+|(?:wb97xd|cam-b3lyp|b3lyp|pbe0|m062x|def2-?svp|6-31g\S*)", re.IGNORECASE)


def _strip_docstring_stmts(stmts: List[ast.stmt]) -> List[ast.stmt]:
    if stmts and isinstance(stmts[0], ast.Expr) and isinstance(stmts[0].value, ast.Constant) and isinstance(stmts[0].value.value, str):
        return stmts[1:]
    return stmts


def _strip_all_docstrings(node: ast.AST) -> ast.AST:
    cloned = copy.deepcopy(node)
    for sub in ast.walk(cloned):
        if isinstance(sub, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            sub.body = _strip_docstring_stmts(list(sub.body))
    return cloned


def _has_scientific_atom_decorator(func_node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    for dec in func_node.decorator_list:
        target = dec.func if isinstance(dec, ast.Call) else dec
        if (getattr(target, "id", None) or getattr(target, "attr", None)) == "scientific_atom":
            return True
    return False


def _is_numeric_constant_node(node: ast.AST) -> Optional[float]:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
        return float(node.value)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        inner = _is_numeric_constant_node(node.operand)
        return (-inner) if inner is not None else None
    return None


def _numeric_default_gets_in_node(root: ast.AST, fn_label: str) -> List[Dict[str, Any]]:
    hits: List[Dict[str, Any]] = []
    for sub in ast.walk(root):
        if not isinstance(sub, ast.Call) or not isinstance(sub.func, ast.Attribute) or sub.func.attr != "get":
            continue
        default_node = sub.args[1] if len(sub.args) >= 2 else next((kw.value for kw in sub.keywords if kw.arg == "default"), None)
        if default_node is None:
            continue
        num_val = _is_numeric_constant_node(default_node)
        if num_val is not None:
            key_str = ast.unparse(sub.args[0]) if sub.args else ""
            hits.append({"function": fn_label, "line": int(getattr(sub, "lineno", 0)), "key": key_str, "default": num_val})
    return hits


def _normalize_fn_ast_dump(func_node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    stripped = _strip_all_docstrings(func_node)
    for item in ast.walk(stripped):
        for attr in ("lineno", "col_offset", "end_lineno", "end_col_offset"):
            if hasattr(item, attr):
                delattr(item, attr)
    return ast.dump(stripped, include_attributes=False)


def extract_stripped_ast_physics_card(source_code: str) -> Dict[str, Any]:
    """
    Strip ALL Python comments and docstrings from `source_code` via tokenize+AST so claims in
    prose cannot mask missing physics, returning executable expressions, numeric `.get` fallbacks,
    decorator coverage, and embedded QM functional/route literals.
    """
    if not isinstance(source_code, str) or not source_code.strip():
        raise ValueError("source_code must be a non-empty Python source string")
    dedented = text_dedent(source_code)
    comment_stripped_tokens = [
        tok for tok in tokenize.generate_tokens(io.StringIO(dedented).readline) if tok.type != tokenize.COMMENT
    ]
    no_comments = tokenize.untokenize(comment_stripped_tokens)
    tree = ast.parse(no_comments)
    stripped_tree = _strip_all_docstrings(tree)

    fn_cards: List[Dict[str, Any]] = []
    all_gets: List[Dict[str, Any]] = []
    qm_routes: List[str] = []
    for sub in ast.walk(stripped_tree):
        if isinstance(sub, ast.Constant) and isinstance(sub.value, str):
            for match in _QM_ROUTE_RE.findall(sub.value):
                cleaned = match.strip()
                if cleaned not in qm_routes:
                    qm_routes.append(cleaned)

    for node in ast.walk(stripped_tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        gets = _numeric_default_gets_in_node(node, node.name)
        all_gets.extend(gets)
        exprs = [ast.unparse(stmt) for stmt in _iter_func_body_no_nested(node) if isinstance(stmt, (ast.Assign, ast.AugAssign, ast.Return))]
        params = [a.arg for a in (node.args.posonlyargs + node.args.args + node.args.kwonlyargs)]
        fn_cards.append({
            "name": node.name,
            "has_scientific_atom": _has_scientific_atom_decorator(node),
            "params": params,
            "return_and_assign_count": len(exprs),
            "numeric_default_gets": gets,
        })

    return {
        "function_count": len(fn_cards),
        "functions": fn_cards,
        "numeric_default_gets": all_gets,
        "qm_route_literals": qm_routes,
        "executable_expressions_joined": ast.unparse(stripped_tree),
    }


@_finite_inputs
def audit_outer_glue_and_single_source_ast(
    outer_source_code: str,
    companion_sources: Optional[Dict[str, str]] = None,
    max_unwrapped_physics_lines: int = _DEFAULT_MAX_UNWRAPPED_PHYSICS_LINES,
    max_unwrapped_math_ops: int = _DEFAULT_MAX_UNWRAPPED_MATH_OPS,
) -> Dict[str, Any]:
    """
    Gate G6q: Catch unverified dense physics formulas hidden inside outer pipeline glue outside
    `@scientific_atom`, hidden `.get(key, numeric_default)` fallback masks, and duplicated/divergent
    shared physics builders copy-pasted across companion station scripts (dual-standard loophole).
    """
    if not isinstance(outer_source_code, str) or not outer_source_code.strip():
        raise ValueError("outer_source_code must be a non-empty string")
    line_cap = int(_finite_float(max_unwrapped_physics_lines))
    op_cap = int(_finite_float(max_unwrapped_math_ops))
    if line_cap <= 0 or op_cap <= 0:
        raise ValueError("max_unwrapped_physics_lines and max_unwrapped_math_ops must be positive")

    outer_tree = ast.parse(text_dedent(outer_source_code))
    unwrapped: List[Dict[str, Any]] = []
    numeric_gets: List[Dict[str, Any]] = []
    outer_fns: Dict[str, str] = {}
    scanned_count = 0

    for node in ast.walk(outer_tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        scanned_count += 1
        outer_fns[node.name] = _normalize_fn_ast_dump(node)
        is_atom = _has_scientific_atom_decorator(node)
        if is_atom:
            continue
        numeric_gets.extend(_numeric_default_gets_in_node(node, node.name))
        span = int(getattr(node, "end_lineno", node.lineno)) - int(node.lineno) + 1
        math_ops = 0
        for sub in _iter_func_body_no_nested(node):
            if isinstance(sub, ast.BinOp) and not isinstance(sub.left, ast.Constant):
                math_ops += 1
            elif isinstance(sub, ast.Call):
                cname = getattr(sub.func, "attr", None) or getattr(sub.func, "id", None) or ""
                if cname in _MATH_CALL_NAMES:
                    math_ops += 1
        if span > line_cap and math_ops > op_cap:
            unwrapped.append({"function": node.name, "lines": span, "math_ops": math_ops})

    if isinstance(outer_tree, ast.Module):
        for stmt in outer_tree.body:
            if not isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                numeric_gets.extend(_numeric_default_gets_in_node(stmt, "<module>"))

    duplicates: List[Dict[str, Any]] = []
    if companion_sources is not None:
        if not isinstance(companion_sources, dict):
            raise ValueError("companion_sources must be a dict mapping label -> source_code")
        seen_builders: Dict[str, Tuple[str, str]] = {
            fname: ("<primary>", dump) for fname, dump in outer_fns.items() if fname.startswith(_SHARED_BUILDER_PREFIXES)
        }
        for label, src in companion_sources.items():
            if not isinstance(src, str) or not src.strip():
                raise ValueError(f"companion source `{label}` must be a non-empty string")
            comp_tree = ast.parse(text_dedent(src))
            for node in ast.walk(comp_tree):
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                dump = _normalize_fn_ast_dump(node)
                if (node.name in outer_fns and node.name not in ("main", "parse_args", "cli")) or node.name.startswith(_SHARED_BUILDER_PREFIXES):
                    if node.name in seen_builders:
                        orig_label, orig_dump = seen_builders[node.name]
                        duplicates.append({
                            "function": node.name,
                            "locations": [orig_label, str(label)],
                            "divergent_ast": orig_dump != dump,
                        })
                    else:
                        seen_builders[node.name] = (str(label), dump)

    violations: List[str] = []
    if unwrapped:
        violations.append("unverified outer-glue physics outside @scientific_atom: " + ", ".join(u["function"] for u in unwrapped))
    if numeric_gets:
        violations.append("outer-glue `.get(key, numeric_default)` fallback mask: " + ", ".join(f"{g['function']}@{g['line']}" for g in numeric_gets))
    if duplicates:
        violations.append("cross-station duplicate/divergent shared physics builder: " + ", ".join(d["function"] for d in duplicates))
    return {
        "status": "FAIL" if violations else "PASS",
        "scanned_function_count": scanned_count,
        "unwrapped_physics_functions": unwrapped,
        "numeric_default_gets": numeric_gets,
        "cross_station_duplicates": duplicates,
        "violations": violations,
    }


def _validate_redteam_pre_code(spec: Dict[str, Any], violations: List[str]) -> None:
    if spec.get("pre_existing_code_present") is not False:
        violations.append("forged retroactive pre_code receipt on existing code; must use post_hoc_audit")
        return
    t_design = _finite_float(spec["design_timestamp_epoch"]) if "design_timestamp_epoch" in spec else 0.0
    t_impl = _finite_float(spec["implementation_start_epoch"]) if "implementation_start_epoch" in spec else 0.0
    if t_design <= 0.0 or t_impl <= t_design:
        violations.append("pre_code requires design_timestamp_epoch < implementation_start_epoch (> 0)")
    ledger = spec.get("approximation_ledger")
    if not isinstance(ledger, list) or not ledger or not all(isinstance(x, dict) and x.get("assumption") for x in ledger):
        violations.append("pre_code requires non-empty approximation_ledger with explicit assumptions")


def _validate_redteam_post_hoc(spec: Dict[str, Any], violations: List[str]) -> int:
    src = spec.get("target_source_code")
    if not isinstance(src, str) or not src.strip():
        violations.append("post_hoc_audit requires non-empty target_source_code")
        return 0
    card = extract_stripped_ast_physics_card(src)
    joined = card["executable_expressions_joined"]
    if card["numeric_default_gets"]:
        violations.append("post_hoc_audit found un-remediated `.get(key, numeric_default)` in executable AST")
    claims = spec.get("claimed_mechanisms")
    if not isinstance(claims, list) or not claims:
        violations.append("post_hoc_audit requires non-empty claimed_mechanisms")
    else:
        for item in claims:
            cid = str(item.get("claim_id", "claim"))
            req = [str(tok) for tok in item.get("required_ast_tokens", [])]
            forb = [str(tok) for tok in item.get("forbidden_ast_tokens", [])]
            missing = [tok for tok in req if tok not in joined]
            present_forb = [tok for tok in forb if tok in joined]
            if missing or present_forb:
                violations.append(f"docstring-vs-executable physics mismatch in `{cid}`: missing={missing}, forbidden={present_forb}")
    verdicts = spec.get("post_hoc_probe_verdicts")
    if not isinstance(verdicts, dict) or not verdicts or any(v != "PASS" for v in verdicts.values()):
        violations.append("post_hoc_audit requires non-empty post_hoc_probe_verdicts with all PASS")
    return int(card["function_count"])


@_finite_inputs
def verify_dual_entry_physics_redteam_audit(redteam_spec: Dict[str, Any]) -> Dict[str, Any]:
    """
    Gate G7j: Dual-Entry Independent Physics Red-Team Audit supporting both `pre_code` review
    of a proposed physical design and `post_hoc_audit` comment/docstring-stripped AST triangulation
    of legacy code (explicitly rejecting forged retroactive `pre_code` receipts).
    """
    if not isinstance(redteam_spec, dict) or not redteam_spec:
        raise ValueError("redteam_spec must be a non-empty dict")
    mode = redteam_spec.get("mode")
    if mode not in ("pre_code", "post_hoc_audit"):
        raise ValueError("redteam_spec['mode'] must be 'pre_code' or 'post_hoc_audit'")
    author_id = str(redteam_spec.get("author_id", "")).strip()
    reviewer_id = str(redteam_spec.get("reviewer_id", "")).strip()
    axes: Set[str] = set(redteam_spec.get("critique_axes_checked", ()))
    risks = redteam_spec.get("identified_risks_and_remediations")

    violations: List[str] = []
    if not author_id or not reviewer_id or author_id == reviewer_id:
        violations.append("independent red-team requires distinct non-empty author_id and reviewer_id")
    missing_axes = sorted(_MANDATORY_REDTEAM_AXES - axes)
    if missing_axes:
        violations.append(f"missing mandatory red-team physics axes: {missing_axes}")
    resolved_count = 0
    if not isinstance(risks, list) or len(risks) < _MIN_REDTEAM_RISK_ITEMS:
        violations.append("requires at least 2 concrete identified_risks_and_remediations")
    else:
        for entry in risks:
            if not isinstance(entry, dict) or not entry.get("risk") or not entry.get("remediation_or_gate"):
                violations.append("malformed entry in identified_risks_and_remediations")
            elif entry.get("resolved") is not True:
                violations.append(f"unresolved physics red-team risk: {entry.get('risk')}")
            else:
                resolved_count += 1

    stripped_fn_count = 0
    if mode == "pre_code":
        _validate_redteam_pre_code(redteam_spec, violations)
    else:
        stripped_fn_count = _validate_redteam_post_hoc(redteam_spec, violations)

    return {
        "status": "FAIL" if violations else "PASS",
        "mode": mode,
        "axes_verified_count": len(axes & _MANDATORY_REDTEAM_AXES),
        "resolved_risk_count": resolved_count,
        "stripped_function_count": stripped_fn_count,
        "violations": violations,
    }


def _scan_json_frozen_metrics(obj: Any, prefix: str, out: List[Dict[str, Any]]) -> None:
    if isinstance(obj, dict):
        if "mean" in obj and ("sd" in obj or "std" in obj):
            mu = obj.get("mean")
            sd = obj.get("sd") if "sd" in obj else obj.get("std")
            if isinstance(mu, (int, float)) and isinstance(sd, (int, float)) and not isinstance(mu, bool) and not isinstance(sd, bool):
                if abs(float(mu)) >= _MEAN_ACTIVE_FLOOR:
                    cv = abs(float(sd)) / abs(float(mu))
                    if cv < _DEFAULT_MIN_CV_JSON_FLOOR:
                        out.append({"path": prefix, "mean": float(mu), "sd": float(sd), "cv": float(cv)})
        for key, val in obj.items():
            child = f"{prefix}.{key}" if prefix else str(key)
            _scan_json_frozen_metrics(val, child, out)
    elif isinstance(obj, list):
        if len(obj) >= _MIN_JSON_SERIES_LEN and all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in obj):
            mu = sum(float(x) for x in obj) / float(len(obj))
            if abs(mu) >= _MEAN_ACTIVE_FLOOR:
                var = sum((float(x) - mu) ** 2 for x in obj) / float(len(obj) - 1)
                sd = var ** 0.5
                cv = sd / abs(mu)
                if cv < _DEFAULT_MIN_CV_JSON_FLOOR:
                    out.append({"path": prefix, "mean": float(mu), "sd": float(sd), "cv": float(cv), "kind": "series"})
        else:
            for idx, item in enumerate(obj):
                _scan_json_frozen_metrics(item, f"{prefix}[{idx}]", out)


def run_audit_existing_cli(
    target_path: Path,
    results_json_paths: Optional[Sequence[Path]] = None,
    companion_paths: Optional[Sequence[Path]] = None,
) -> Dict[str, Any]:
    """Post-hoc audit entry for existing Python scripts and JSON observables (`--audit-existing`)."""
    resolved = target_path.expanduser().resolve()
    py_files = sorted(resolved.rglob("*.py")) if resolved.is_dir() else [resolved]
    if not py_files or not all(p.is_file() for p in py_files):
        raise ValueError(f"Audit target does not contain valid Python files: {resolved}")
    comp_map: Dict[str, str] = {}
    for cp in (companion_paths or ()):
        c_res = cp.expanduser().resolve()
        comp_map[c_res.name] = c_res.read_text(encoding="utf-8")

    cards: Dict[str, Any] = {}
    glue_reports: Dict[str, Any] = {}
    g5n_reports: Dict[str, Any] = {}
    violations: List[str] = []
    for p_file in py_files:
        src = p_file.read_text(encoding="utf-8")
        key = p_file.name
        cards[key] = extract_stripped_ast_physics_card(src)
        glue = audit_outer_glue_and_single_source_ast(src, companion_sources=comp_map or None)
        glue_reports[key] = glue
        g5n = scan_source_for_todo_placeholders_and_magic_numbers(src, check_magic_numbers=True)
        g5n_reports[key] = {"status": g5n["status"], "finding_count": g5n["finding_count"], "findings": g5n["findings"]}
        if glue["status"] != "PASS":
            violations.extend(f"{key}: {msg}" for msg in glue["violations"])
        if g5n["finding_count"] > 0:
            violations.append(f"{key}: {g5n['finding_count']} G5n magic-number/placeholder findings")

    frozen_json: List[Dict[str, Any]] = []
    for jp in (results_json_paths or ()):
        j_res = jp.expanduser().resolve()
        payload = json.loads(j_res.read_text(encoding="utf-8"))
        hits: List[Dict[str, Any]] = []
        _scan_json_frozen_metrics(payload, j_res.name, hits)
        frozen_json.extend(hits)
    if frozen_json:
        violations.append(f"frozen/collapsed dynamic observables in JSON: {len(frozen_json)} entries with CV < {_DEFAULT_MIN_CV_JSON_FLOOR}")

    return {
        "mode": "post_hoc_audit",
        "status": "FAIL" if violations else "PASS",
        "files_audited": [p.name for p in py_files],
        "physics_cards": cards,
        "outer_glue_audit": glue_reports,
        "g5n_audit": g5n_reports,
        "frozen_json_metrics": frozen_json,
        "violations": violations,
    }
