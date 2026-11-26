"""AWF Guard: static audit."""
from __future__ import annotations

from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from pathlib import Path
from awf_guard_numeric_contracts import finite_inputs as _finite_inputs
import ast
from .errors import AntiGoodhartGateError
from .source_quality import DEFAULT_MAX_FUNCTION_LINES
from .atoms import _FORBIDDEN_IMPURE_CALLS
from .ast_structure import analyze_contract_and_docstring_intent
from .ast_structure import compute_ncc_test_overlap
from .ast_dataflow import detect_extensional_enumeration_and_dispatch
from .ast_structure import scan_ast_for_harness_tampering
from .harness import scan_ast_for_test_file_reading_and_heuristic_cutoff


@_finite_inputs
def scan_ast_for_hardcoded_short_loops(
    source_code: str,
    min_allowed_bound: int = 10,
) -> None:
    """Static AST check forbidding hardcoded short `for it in range(3/4)` optimization loops."""
    tree = ast.parse(source_code)
    for node in ast.walk(tree):
        if isinstance(node, ast.For) and isinstance(node.iter, ast.Call):
            func = node.iter.func
            if isinstance(func, ast.Name) and func.id == "range" and len(node.iter.args) == 1:
                arg0 = node.iter.args[0]
                if isinstance(arg0, ast.Constant) and isinstance(arg0.value, int):
                    target_name = getattr(node.target, "id", "")
                    if target_name in ("it", "iter", "iteration", "epoch", "step_it", "ibi_it"):
                        if arg0.value < min_allowed_bound:
                            raise AntiGoodhartGateError(
                                f"[Gate 5 AST Loop-Truncation Guard] Detected hardcoded short optimization loop "
                                f"`for {target_name} in range({arg0.value}):` at line {node.lineno} "
                                f"(minimum bound >= {min_allowed_bound} or adaptive `while` convergence loop required)."
                            )


@_finite_inputs
def audit_ast_path(
    target_path: Path,
    min_loop_bound: int = 10,
    max_atom_lines: Optional[int] = None,
    check_numeric_get: bool = True,
    check_nan_to_num: bool = True,
    test_suite_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Comprehensive static AST + Dataflow + Intent + NCC Anti-Shortcut audit across a Python file or directory.
    Detects:
    1. Hardcoded short optimization loops (`for it in range(K < min_loop_bound)`);
    2. Numeric `.get(key, numeric_default)` fallback masking;
    3. `nan_to_num` silent singularity swallowing;
    4. `@scientific_atom` capsule size overflow or impure I/O calls;
    5. Extensional Enumeration (`if x == const: return lit` chains) & Dict-Dispatch Memorization (`return TABLE[param]`);
    6. Docstring / Contract Intent-vs-AST Structure mismatches (`no_loop`, `no_recursion`, `no_sort`, `no_memoization`, `no_computation`);
    7. Anti-Harness Tampering (`DunderEqualityHijack`, `ZeroStrideMemorySpoofing`, `StackFrameIntrospection`, `TimerOrModuleMonkeyPatch`, `ObfuscatedExecOrBuiltins`);
    8. Optional NCC Test-Literal Overlap (`C(code|tests)/C(code) < 0.72`).
    """
    target_path = Path(target_path)
    test_suite_path = Path(test_suite_path) if test_suite_path is not None else None
    files = (
        sorted(p for p in target_path.rglob("*.py") if "__pycache__" not in p.parts)
        if target_path.is_dir()
        else [target_path]
    )
    test_suite_text = test_suite_path.read_text(encoding="utf-8") if test_suite_path and test_suite_path.is_file() else ""
    violations: List[Dict[str, Any]] = []

    for py_file in files:
        src = py_file.read_text(encoding="utf-8")
        try:
            tree = ast.parse(src)
        except SyntaxError as exc:
            violations.append({"file": str(py_file), "line": exc.lineno or 0, "kind": "SyntaxError", "detail": str(exc)})
            continue

        # 1. Short loop check
        try:
            scan_ast_for_hardcoded_short_loops(src, min_allowed_bound=min_loop_bound)
        except AntiGoodhartGateError as exc:
            violations.append({"file": str(py_file), "line": 0, "kind": "ShortLoopTruncation", "detail": str(exc)})

        # 5. Extensional Enumeration & Dict-Dispatch Memorization
        for v in detect_extensional_enumeration_and_dispatch(tree):
            violations.append({"file": str(py_file), **v})

        # 6. Docstring Intent-vs-AST Structure mismatch
        for v in analyze_contract_and_docstring_intent(tree):
            violations.append({"file": str(py_file), **v})

        # 7. Harness tampering & obfuscation
        for v in scan_ast_for_harness_tampering(tree):
            violations.append({"file": str(py_file), **v})

        # 7b. EvilGenie direct test-file reading & size-cutoff heuristic fallback
        for v in scan_ast_for_test_file_reading_and_heuristic_cutoff(tree):
            violations.append({"file": str(py_file), **v})

        # 8. Optional NCC test-literal overlap
        if test_suite_text:
            ncc_res = compute_ncc_test_overlap(src, test_suite_text)
            if ncc_res["applicable"] and not ncc_res["passed"]:
                violations.append({
                    "file": str(py_file),
                    "line": 1,
                    "kind": "NCCTestLiteralMemorization",
                    "detail": f"Normalized Compression Complexity NCC={ncc_res['ncc_score']} < {ncc_res['ncc_floor']} (code copies test literals).",
                })

        for node in ast.walk(tree):
            # 2. Numeric .get(key, numeric_default)
            if check_numeric_get and isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "get":
                if len(node.args) >= 2:
                    arg2 = node.args[1]
                    is_num = (
                        isinstance(arg2, ast.Constant)
                        and isinstance(arg2.value, (int, float))
                        and not isinstance(arg2.value, bool)
                    ) or (
                        isinstance(arg2, ast.UnaryOp)
                        and isinstance(arg2.operand, ast.Constant)
                        and isinstance(arg2.operand.value, (int, float))
                    )
                    if is_num:
                        violations.append({
                            "file": str(py_file),
                            "line": node.lineno,
                            "kind": "SilentNumericGetDefault",
                            "detail": f"Forbidden `.get(key, numeric_default)` at line {node.lineno}",
                        })

            # 3. nan_to_num check
            if check_nan_to_num and isinstance(node, ast.Call):
                fn_name = getattr(node.func, "id", None) or getattr(node.func, "attr", None)
                if fn_name == "nan_to_num":
                    violations.append({
                        "file": str(py_file),
                        "line": node.lineno,
                        "kind": "SilentNanToNumSwallowing",
                        "detail": f"Forbidden `nan_to_num` singularity masking at line {node.lineno}",
                    })

            # 4. @scientific_atom function checks
            if isinstance(node, ast.FunctionDef):
                has_atom_dec = any(
                    (isinstance(d, ast.Name) and d.id == "scientific_atom")
                    or (isinstance(d, ast.Call) and getattr(d.func, "id", None) == "scientific_atom")
                    for d in node.decorator_list
                )
                if has_atom_dec:
                    end_line = getattr(node, "end_lineno", node.lineno)
                    fn_lines = end_line - node.lineno + 1
                    if max_atom_lines is not None and fn_lines > max_atom_lines:
                        violations.append({
                            "file": str(py_file),
                            "line": node.lineno,
                            "kind": "AtomCapsuleSizeOverflow",
                            "detail": f"`{node.name}` spans {fn_lines} lines (> {max_atom_lines})",
                        })
                    for sub in ast.walk(node):
                        if isinstance(sub, ast.Call):
                            sub_name = getattr(sub.func, "id", None) or getattr(sub.func, "attr", None)
                            if sub_name in _FORBIDDEN_IMPURE_CALLS:
                                violations.append({
                                    "file": str(py_file),
                                    "line": getattr(sub, "lineno", node.lineno),
                                    "kind": "ImpureAtomCall",
                                    "detail": f"`{node.name}` calls forbidden I/O `{sub_name}()`",
                                })

    return {
        "status": "PASS" if not violations else "FAIL",
        "files_scanned": len(files),
        "violation_count": len(violations),
        "violations": violations,
    }
