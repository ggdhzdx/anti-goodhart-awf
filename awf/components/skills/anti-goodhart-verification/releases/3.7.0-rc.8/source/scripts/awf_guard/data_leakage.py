"""AWF Guard: data leakage."""
from __future__ import annotations

from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Sequence
from typing import Tuple
from typing import Union
from awf_guard_numeric_contracts import finite_array as _finite_array
from awf_guard_numeric_contracts import finite_inputs as _finite_inputs
import ast
import hashlib
import numpy as np
from .ast_utils import text_dedent


def compute_blake2b_row_taints(arr: np.ndarray) -> List[bytes]:
    """
    Compute 16-byte BLAKE2b row-content digests (`splitguard/utils.py:hash_numpy`),
    canonicalizing `-0.0` to `+0.0` so each row gets a deterministic 128-bit identity.
    """
    mat = _finite_array(arr, dtype=np.float64)
    if mat.ndim == 1:
        mat = mat.reshape(-1, 1)
    # Canonicalize -0.0 -> +0.0
    mat = np.where(mat == 0.0, 0.0, mat)
    out: List[bytes] = []
    for i in range(mat.shape[0]):
        row_bytes = np.ascontiguousarray(mat[i]).tobytes()
        out.append(hashlib.blake2b(row_bytes, digest_size=16).digest())
    return out


@_finite_inputs
def scan_ast_for_pre_split_preprocessing_leakage(source_code: Union[ast.AST, str]) -> List[Dict[str, Any]]:
    """
    Static AST scanner inspired by `SE4AIResearch/DataLeakage` & `splitguard`:
    1. `PreSplitPreprocessingLeakage`: Calling `.fit(...)` or `.fit_transform(...)` at a line number
       earlier than `train_test_split(...)` / `GroupKFold(...)` / `KFold(...)` in the same function/module.
    2. `TestSetFitLeakage`: Calling `.fit(X_test)` or `.fit_transform(X_test / val_X / holdout_X)`
       on validation/test/holdout variables instead of `.transform(X_test)`.
    """
    if isinstance(source_code, str):
        if not source_code.strip():
            return []
        tree: ast.AST = ast.parse(text_dedent(source_code))
    else:
        tree = source_code
    findings: List[Dict[str, Any]] = []

    fit_calls: List[Tuple[int, str, List[str]]] = []
    split_lines: List[int] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            fn_name = getattr(node.func, "id", None) or getattr(node.func, "attr", None) or ""
            if fn_name in ("train_test_split", "GroupKFold", "StratifiedKFold", "KFold", "TimeSeriesSplit", "split"):
                split_lines.append(getattr(node, "lineno", 0))
            elif fn_name in ("fit", "fit_transform"):
                arg_names = [
                    getattr(a, "id", "")
                    for a in node.args
                    if isinstance(a, ast.Name)
                ]
                fit_calls.append((getattr(node, "lineno", 0), fn_name, arg_names))
                for a_name in arg_names:
                    low_a = a_name.lower()
                    if any(tok in low_a for tok in ("test", "val", "holdout", "eval")):
                        findings.append({
                            "kind": "TestSetFitLeakage",
                            "line": getattr(node, "lineno", 0),
                            "call": fn_name,
                            "arg": a_name,
                            "detail": (
                                f"`{fn_name}({a_name})` called on test/validation/holdout data at line "
                                f"{getattr(node, 'lineno', 0)} (use `.transform({a_name})` fitted on train only)."
                            ),
                        })

    if split_lines:
        first_split_line = min(split_lines)
        for fit_line, fn_name, arg_names in fit_calls:
            if fit_line < first_split_line:
                findings.append({
                    "kind": "PreSplitPreprocessingLeakage",
                    "line": fit_line,
                    "call": fn_name,
                    "args": arg_names,
                    "detail": (
                        f"`{fn_name}({', '.join(arg_names)})` at line {fit_line} executes BEFORE "
                        f"`train_test_split` at line {first_split_line} (`fit_before_split` data leakage)."
                    ),
                })

    return findings


@_finite_inputs
def audit_splitguard_row_and_group_leakage(
    train_X: np.ndarray,
    test_X: np.ndarray,
    fitted_arrays: Optional[Sequence[np.ndarray]] = None,
    train_groups: Optional[Sequence[Any]] = None,
    test_groups: Optional[Sequence[Any]] = None,
    pipeline_source_code: str = "",
) -> Dict[str, Any]:
    """
    Runtime BLAKE2b Row-Taint & Group/Conformer Split Auditor (`Tommasoaiello13/splitguard`):
    1. **AST Pre-Split FitTransform Check (`G6m`)**:
       - Scans `pipeline_source_code` for `fit_before_split` and `TestSetFitLeakage`.
    2. **Row-Identity Overlap & Pre-Split Fit Taint (`G7g`)**:
       - Hashes every row of `train_X` and `test_X` with 16-byte BLAKE2b (`compute_blake2b_row_taints`).
       - Detects duplicate row leakage (`train_hashes & test_hashes`).
       - For every array in `fitted_arrays` (the array passed to `.fit()`), checks if it contains
         any `test_X` row hashes (`fit_before_split` if it contains both train and test rows;
         `fit_after_split` if fitted directly on test rows).
    3. **Group / Conformer / Molecule Split Leakage (`G7g`)**:
       - Verifies `set(train_groups) & set(test_groups) == empty`, preventing conformers of the
         same molecule, frames of the same MD trajectory, or crystal polymorphs from spanning both
         train and test sets.
    """
    ast_findings = scan_ast_for_pre_split_preprocessing_leakage(pipeline_source_code)
    train_taints = compute_blake2b_row_taints(train_X)
    test_taints = compute_blake2b_row_taints(test_X)
    train_set = set(train_taints)
    test_set = set(test_taints)

    duplicate_row_overlap = len(train_set & test_set)
    runtime_leakage_events: List[Dict[str, Any]] = []
    if not train_taints or not test_taints:
        runtime_leakage_events.append({
            "kind": "vacuous_empty_split",
            "train_rows": len(train_taints),
            "test_rows": len(test_taints),
            "detail": f"Vacuous empty dataset split: train_rows={len(train_taints)}, test_rows={len(test_taints)}.",
        })

    if duplicate_row_overlap > 0:
        runtime_leakage_events.append({
            "kind": "duplicate_row_leakage",
            "overlap_rows": duplicate_row_overlap,
            "detail": f"{duplicate_row_overlap} identical row(s) appear in both `train_X` and `test_X`.",
        })

    for idx, f_arr in enumerate(fitted_arrays or []):
        f_hashes = set(compute_blake2b_row_taints(f_arr))
        in_pure_train = len(f_hashes & (train_set - test_set))
        in_train = len(f_hashes & train_set)
        in_test = len(f_hashes & test_set)
        if in_test > 0 and in_pure_train > 0:
            runtime_leakage_events.append({
                "kind": "fit_before_split",
                "fitted_array_index": idx,
                "train_rows_tainted": in_train,
                "test_rows_tainted": in_test,
                "detail": (
                    f"Fitted array #{idx} contains {in_train} train row(s) and {in_test} test row(s) "
                    f"(transformer was fit on combined pre-split dataset)."
                ),
            })
        elif in_test > 0:
            runtime_leakage_events.append({
                "kind": "fit_after_split",
                "fitted_array_index": idx,
                "test_rows_tainted": in_test,
                "detail": f"Fitted array #{idx} contains {in_test} test row(s) (transformer was fit on test split).",
            })

    overlapping_groups: List[Any] = []
    if (train_groups is None) != (test_groups is None):
        runtime_leakage_events.append({
            "kind": "incomplete_group_labels",
            "detail": "Both `train_groups` and `test_groups` must be supplied together when checking group splits.",
        })
    elif train_groups is not None and test_groups is not None:
        if len(train_groups) != len(train_taints) or len(test_groups) != len(test_taints):
            runtime_leakage_events.append({
                "kind": "group_length_mismatch",
                "detail": "Group label sequence lengths must match `train_X` and `test_X` row counts.",
            })
        overlapping_groups = sorted(set(train_groups) & set(test_groups), key=str)
        if overlapping_groups:
            runtime_leakage_events.append({
                "kind": "group_leakage",
                "overlapping_groups": overlapping_groups,
                "detail": (
                    f"Group/conformer/entity IDs {overlapping_groups} appear in both train and test splits!"
                ),
            })

    passed = (not ast_findings) and (not runtime_leakage_events)
    return {
        "status": "PASS" if passed else "FAIL",
        "ast_leakage_findings": ast_findings,
        "runtime_leakage_events": runtime_leakage_events,
        "duplicate_row_overlap": duplicate_row_overlap,
        "overlapping_groups": overlapping_groups,
    }
