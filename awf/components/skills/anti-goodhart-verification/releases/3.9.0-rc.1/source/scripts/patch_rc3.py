"""Reproducible rc.2 -> rc.3 source edits; run only in the unregistered draft."""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ENGINE = ROOT / "awf_universal_anti_goodhart_gates.py"


def edit_once(text, old, new):
    if text.count(old) != 1:
        raise RuntimeError(f"Expected one patch site: {old[:80]}")
    return text.replace(old, new, 1)


def patch_engine():
    text = ENGINE.read_text()
    text = edit_once(text, "import numpy as np", "import numpy as np\nfrom awf_guard_numeric_contracts import finite_array as _finite_array, finite_float as _finite_float, finite_inputs as _finite_inputs, require_finite as _require_finite\nfrom awf_guard_radius_probes import radius_probe_violations as _radius_probe_violations")
    text = edit_once(text, "check_magic_numbers: bool = False,", "check_magic_numbers: bool = True,")
    text = text.replace("post_fix_source, check_magic_numbers=False", "post_fix_source, check_magic_numbers=True")
    text = edit_once(text, "    if not source_code.strip():\n        return {\"status\": \"PASS\", \"effective_reward\": 1.0, \"finding_count\": 0, \"findings\": []}", "    if not source_code.strip():\n        return {\"status\": \"FAIL\", \"effective_reward\": 0.0, \"finding_count\": 1, \"findings\": [{\"kind\": \"EmptySource\"}]}")
    text = edit_once(text, "        c_gen = gen_mccabe[qname]\n", "        c_gen = gen_mccabe[qname]\n        branch_kinds = (ast.If, ast.IfExp, ast.Match, ast.Try, ast.BoolOp, ast.For, ast.While, ast.comprehension)\n        old_branches = sum(isinstance(n, branch_kinds) for n in ast.walk(orig_funcs[qname]))\n        new_branches = sum(isinstance(n, branch_kinds) for n in ast.walk(gen_funcs[qname]))\n        if old_branches > new_branches:\n            violations.append({\"kind\": \"RemovedControlFlow\", \"function\": qname, \"line\": gen_funcs[qname].lineno, \"detail\": \"Control-flow branch removed; semantic equivalence needs explicit review\"})\n")
    text = edit_once(text, "    if dropped_names and not legit_comp_upgrade:", "    for dropped in dropped_names:\n        violations.append({\"kind\": \"RemovedFunction\", \"function\": dropped, \"line\": 1, \"detail\": \"Function removed or renamed; cannot certify equivalence from complexity\"})\n    if dropped_names and not legit_comp_upgrade:")
    start = text.index("def verify_filtration_monotonicity_and_heterogeneous_radius_clearance(")
    stop = text.index("\ndef verify_rp2_director", start)
    section = text[start:stop]
    section = edit_once(section, "    tol: float = 1e-9,\n", "    tol: float = 1e-9,\n    geometry_argument_names: Optional[Dict[str, str]] = None,\n")
    section = edit_once(section, "    violations: List[str] = []\n", "    violations: List[str] = []\n    if not (0 <= tol <= 1e-3) or partition_total <= 0:\n        raise ValueError(\"G5r requires positive partition_total and tolerance in [0, 1e-3]\")\n    violations.extend(_radius_probe_violations(clearance_fn, base_input_kwargs, geometry_argument_names, _extract_array, filtration_indices[0], partition_total, tol))\n")
    text = text[:start] + section + text[stop:]
    text = edit_once(text, "def _extract_array(output: Any) -> np.ndarray:\n", "def _extract_array(output: Any) -> np.ndarray:\n    _require_finite(output, \"operator output\")\n")
    # Guard actual conversions, leaving documentation/type names and deliberate failure sentinels intact.
    tree = ast.parse(text)
    lines = text.splitlines(keepends=True)
    offsets = [0]
    for line in lines:
        offsets.append(offsets[-1] + len(line))
    replacements = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = node.func
        replacement = None
        if isinstance(name, ast.Name) and name.id == "float":
            sentinel = node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str)
            nan_challenge = "nan_res =" in lines[node.lineno - 1]
            if not sentinel and not nan_challenge:
                replacement = "_finite_float"
        elif isinstance(name, ast.Attribute) and isinstance(name.value, ast.Name) and name.value.id == "np" and name.attr == "asarray":
            replacement = "_finite_array"
        if replacement:
            replacements.append((offsets[name.lineno - 1] + name.col_offset, offsets[name.end_lineno - 1] + name.end_col_offset, replacement))
    for begin, end, replacement in sorted(replacements, reverse=True):
        text = text[:begin] + replacement + text[end:]
    # Wrap gate inputs, not callbacks, preserving source identity and execution-lineage checks.
    footer = '\nfor _gate_name, _gate_fn in list(globals().items()):\n    if _gate_name.startswith(("verify_", "evaluate_", "audit_", "scan_", "detect_")) and inspect.isfunction(_gate_fn):\n        globals()[_gate_name] = _finite_inputs(_gate_fn)\n\n'
    text = edit_once(text, 'if __name__ == "__main__":', footer + 'if __name__ == "__main__":')
    text = text.replace("v3.7.0-rc.2", "v3.7.0-rc.3")
    ENGINE.write_text(text)


if __name__ == "__main__":
    patch_engine()
