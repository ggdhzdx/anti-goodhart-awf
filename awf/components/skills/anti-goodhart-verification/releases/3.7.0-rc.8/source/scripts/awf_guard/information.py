"""AWF Guard: information."""
from __future__ import annotations

import hashlib
import re
from typing import Any, Dict, List, Set, Tuple, Union
import weakref

from awf_guard_numeric_contracts import finite_float as _finite_float
from .errors import AntiGoodhartGateError, InformationBoundaryLeakError


FORBIDDEN_IN_CODER_CONTEXT: Set[str] = {
    "acceptance_criteria",
    "test_cases",
    "rubric",
    "holdout_orthogonal_target",
    "holdout_secret_target",
    "oracle_tol",
    "limit_tol",
    "worst_slice_floor",
    "min_score",
    "worker_id",
}


FORBIDDEN_IN_VERIFIER_ARTIFACT: Set[str] = {
    "worker_id",
    "task_description",
    "original_prompt",
    "prompt_sent",
    "author_reasoning",
    "self_assessment",
    "confidence_claim",
}


ALLOWED_CODER_TASK_KEYS: Set[str] = {
    "station_id",
    "station_name",
    "math_contract",
    "inputs_contract",
    "outputs_contract",
    "socratic_premortem_question",
    "socratic_premortem_analytic_trap",
    "abstract_retry_feedback",
    "attempt",
}


ALLOWED_VERIFIER_ARTIFACT_KEYS: Set[str] = {
    "station_id",
    "atom_id",
    "git_diff",
    "files_changed",
    "source_code",
    "target_fn_name",
}

_DEFAULT_BORDERLINE_RATIO = 0.80
_MAX_DISTINCT_CAPSULE_QUERIES = 3
_CAPSULE_RATIO_BUCKETS: Tuple[float, ...] = (0.0, 0.25, 0.5, 0.75, 0.9, 1.0, 1.5, 2.0, 5.0, 10.0)
_CAPSULE_SECRET_VAULT: "weakref.WeakKeyDictionary[SealedHoldoutCapsule, Dict[str, Any]]" = weakref.WeakKeyDictionary()


def _find_nested_forbidden_keys(value: Any, forbidden_keys: Set[str]) -> Set[str]:
    found: Set[str] = set()
    if isinstance(value, dict):
        found.update(set(value.keys()) & forbidden_keys)
        for sub in value.values():
            found.update(_find_nested_forbidden_keys(sub, forbidden_keys))
    elif isinstance(value, (list, tuple)):
        for sub in value:
            found.update(_find_nested_forbidden_keys(sub, forbidden_keys))
    return found


def validate_information_boundary(
    payload: Dict[str, Any],
    allowed_keys: Set[str],
    forbidden_keys: Set[str],
    boundary_name: str,
) -> Dict[str, Any]:
    """
    Enforce strict Information-Asymmetry between Planning/Verification and Execution/Coding contexts.
    1. Immediately raises `InformationBoundaryLeakError` if any key in `forbidden_keys` is present
       at top-level or nested inside allowed dictionary/list values.
    2. Strips any undeclared extra keys not in `allowed_keys`.
    """
    present_keys = set(payload.keys())
    leaked = (present_keys & forbidden_keys) | _find_nested_forbidden_keys(payload, forbidden_keys)
    filtered = {k: v for k, v in payload.items() if k in allowed_keys}
    if leaked:
        raise InformationBoundaryLeakError(
            f"🚫 [GOODHART INFORMATION BOUNDARY VIOLATION at {boundary_name}] "
            f"Forbidden keys leaked across boundary: {sorted(leaked)}"
        )
    return filtered


def seal_task_for_coder(raw_task: Dict[str, Any]) -> Dict[str, Any]:
    """Strip all hold-out targets, tolerances, and rubric thresholds before handing a task to the coding context."""
    clean_candidate = {k: v for k, v in raw_task.items() if k not in FORBIDDEN_IN_CODER_CONTEXT}
    return validate_information_boundary(
        clean_candidate,
        allowed_keys=ALLOWED_CODER_TASK_KEYS,
        forbidden_keys=FORBIDDEN_IN_CODER_CONTEXT,
        boundary_name="Planner -> Coder (seal_task_for_coder)",
    )


def seal_artifact_for_verifier(raw_artifact: Dict[str, Any]) -> Dict[str, Any]:
    """Strip worker identity, original prompt, and self-assessment claims before handing code to the verifier."""
    clean_candidate = {k: v for k, v in raw_artifact.items() if k not in FORBIDDEN_IN_VERIFIER_ARTIFACT}
    return validate_information_boundary(
        clean_candidate,
        allowed_keys=ALLOWED_VERIFIER_ARTIFACT_KEYS,
        forbidden_keys=FORBIDDEN_IN_VERIFIER_ARTIFACT,
        boundary_name="Coder -> Verifier (seal_artifact_for_verifier)",
    )


def _quantize_capsule_ratio(raw_ratio: float) -> float:
    if raw_ratio <= 0.0:
        return 0.0
    for bucket in _CAPSULE_RATIO_BUCKETS:
        if raw_ratio <= bucket:
            return bucket
    return _CAPSULE_RATIO_BUCKETS[-1]


class SealedHoldoutCapsule:
    """
    Opaque, tamper-evident Hold-Out Target Capsule for Gate 7b.
    Stores secrets in a module-private WeakKeyDictionary vault outside `vars(self)` and closure cells,
    quantizes `ratio_to_tol` into coarse bands to block 2-query linear inversion, and enforces a strict
    distinct-candidate query budget.
    """

    def __init__(
        self,
        metric_name: str,
        secret_target: float,
        secret_tol: float,
        remediation_hint: str = "Verify higher-order physical coupling, measure normalization, and boundary conditions.",
    ) -> None:
        target_f = _finite_float(secret_target)
        tol_f = _finite_float(secret_tol)
        if tol_f <= 0.0:
            raise ValueError("SealedHoldoutCapsule requires strictly positive secret_tol")
        self.metric_name = metric_name
        self.remediation_hint = remediation_hint
        self._commitment_sha256 = hashlib.sha256(
            f"{metric_name}:{target_f:.12e}:{tol_f:.12e}".encode("utf-8")
        ).hexdigest()
        _CAPSULE_SECRET_VAULT[self] = {
            "target": target_f,
            "tol": tol_f,
            "seen_candidates": set(),
        }

    @property
    def commitment_sha256(self) -> str:
        return self._commitment_sha256

    def _capsule_tol_bound_ok(self, max_tol: float) -> bool:
        entry = _CAPSULE_SECRET_VAULT.get(self)
        if entry is None:
            return False
        return bool(0.0 < entry["tol"] <= _finite_float(max_tol))

    def evaluate_blind(self, candidate_value: float, borderline_ratio: float = _DEFAULT_BORDERLINE_RATIO) -> Dict[str, Any]:
        entry = _CAPSULE_SECRET_VAULT.get(self)
        if entry is None:
            raise AntiGoodhartGateError("[Gate 7b SealedHoldoutCapsule Error] Capsule vault entry missing or uninitialized.")
        cand_f = _finite_float(candidate_value)
        b_ratio = _finite_float(borderline_ratio)
        cand_key = round(cand_f, 12)
        seen = entry["seen_candidates"]
        if cand_key not in seen:
            if len(seen) >= _MAX_DISTINCT_CAPSULE_QUERIES:
                raise AntiGoodhartGateError(
                    f"[Gate 7b SealedHoldoutCapsule Query-Budget Exhausted] Exceeded {_MAX_DISTINCT_CAPSULE_QUERIES} "
                    "distinct candidate queries against blind hold-out capsule!"
                )
            seen.add(cand_key)
        diff = cand_f - entry["target"]
        abs_err = abs(diff)
        raw_ratio = abs_err / entry["tol"]
        direction = "OVER-PREDICTED (+)" if diff > 0 else ("UNDER-PREDICTED (-)" if diff < 0 else "EXACT (0)")
        passed = abs_err <= entry["tol"]
        is_borderline = passed and (raw_ratio >= b_ratio)
        return {
            "passed": passed,
            "is_borderline": is_borderline,
            "ratio_to_tol": _quantize_capsule_ratio(raw_ratio),
            "direction": direction,
            "commitment_sha256": self._commitment_sha256,
        }

    def __repr__(self) -> str:
        return (
            f"<SealedHoldoutCapsule metric='{self.metric_name}' "
            f"sha256='{self._commitment_sha256[:12]}...' target=[REDACTED] tol=[REDACTED]>"
        )

    __str__ = __repr__


_FORBIDDEN_FEEDBACK_TERMS = (
    "target=",
    "secret_target",
    "min_score",
    "rubric",
    "worst_slice_floor=",
    "holdout_orthogonal_target",
)


def generate_abstract_retry_feedback(
    error_or_receipt: Union[Exception, str, Dict[str, Any]],
) -> str:
    """
    Anti-Leak Abstract Diagnostic Sanitizer for Iterative Retry Loops.
    Translates raw `AntiGoodhartGateError` exceptions or `BORDERLINE` receipts into high-level
    mathematical/structural remediation hints while scrubbing exact hold-out target numbers and thresholds.
    """
    if isinstance(error_or_receipt, dict):
        warnings = error_or_receipt.get("borderline_warnings", [])
        if not warnings:
            return "All gates passed cleanly inside the green confidence zone."
        return (
            "Borderline threshold-hugging detected on one or more gates. "
            "Do not tune empirical constants; improve numerical discretization order, convergence tolerance, or measure accuracy."
        )

    raw_msg = str(error_or_receipt)
    guidance: List[str] = []

    if "Gate 1" in raw_msg or "Analytic-Limit" in raw_msg or "Evaluator" in raw_msg:
        guidance.append(
            "[Structural Hint - Gate 1] Analytic limit or null/shift calibration failed: "
            "verify asymptotic limit behavior, spherical/radial Jacobian measure factors, and normalization denominator."
        )
    if "Gate 2" in raw_msg or "Orthogonal-Oracle" in raw_msg:
        guidance.append(
            "[Structural Hint - Gate 2] Fast operator diverges from independent small-sample oracle: "
            "check index broadcasting, sign conventions, and off-by-one boundary indexing."
        )
    if "Gate 3" in raw_msg or "Symmetry" in raw_msg or "Perturbation" in raw_msg:
        guidance.append(
            "[Structural Hint - Gate 3] Symmetry invariance or higher-order perturbation sensitivity failed: "
            "ensure coordinate/permutation equivariance and verify that higher-order inputs are actively coupled."
        )
    if "Gate 4" in raw_msg or "Constraint/Mask" in raw_msg:
        guidance.append(
            "[Structural Hint - Gate 4] Constraint/mask ablation produced negligible change: "
            "confirm mask boolean array is actually applied to the kernel weights inside the computation."
        )
    if "Gate 5" in raw_msg or "Conservation" in raw_msg or "SVD" in raw_msg or "Loop-Truncation" in raw_msg:
        guidance.append(
            "[Structural Hint - Gate 5] Manifold degeneracy, conservation drift, or low-rank update detected: "
            "use adaptive residual convergence loops and update the full parameter vector rather than scalar multipliers."
        )
    if "Gate 6" in raw_msg or "Phantom" in raw_msg or "NCC" in raw_msg:
        guidance.append(
            "[Structural Hint - Gate 6] Execution lineage or test-literal overlap failed: "
            "remove cached/memorized test literals and compute results dynamically from inputs."
        )
    if "Gate 7" in raw_msg or "Hold-Out" in raw_msg or "Worst slice" in raw_msg:
        direction_hint = ""
        if "OVER-PREDICTED" in raw_msg:
            direction_hint = " (candidate OVER-PREDICTED (+) the orthogonal observable)"
        elif "UNDER-PREDICTED" in raw_msg:
            direction_hint = " (candidate UNDER-PREDICTED (-) the orthogonal observable)"
        guidance.append(
            f"[Structural Hint - Gate 7] Worst-slice or blind hold-out orthogonal observable failed{direction_hint}: "
            "inspect tail distribution accuracy and physical coupling without tuning magic constants."
        )

    if not guidance:
        scrubbed = re.sub(r"target\s*=\s*[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", "target=[REDACTED]", raw_msg, flags=re.IGNORECASE)
        scrubbed = re.sub(r"tol\s*[-=:]?\s*[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", "tol=[REDACTED]", scrubbed, flags=re.IGNORECASE)
        scrubbed = re.sub(r"floor\s*[-=:]?\s*[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", "floor=[REDACTED]", scrubbed, flags=re.IGNORECASE)
        for term in _FORBIDDEN_FEEDBACK_TERMS:
            scrubbed = re.sub(re.escape(term), "[REDACTED_TERM]", scrubbed, flags=re.IGNORECASE)
        guidance.append(scrubbed)

    final_feedback = " ".join(guidance)
    for term in _FORBIDDEN_FEEDBACK_TERMS:
        if term in final_feedback.lower():
            raise InformationBoundaryLeakError(f"Feedback sanitizer failed to scrub `{term}`")
    return final_feedback
