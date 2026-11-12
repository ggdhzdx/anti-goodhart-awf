"""AWF Guard: information."""
from __future__ import annotations

from typing import Any
from typing import Dict
from typing import List
from typing import Set
from typing import Union
from awf_guard_numeric_contracts import finite_call as _finite_call
from awf_guard_numeric_contracts import finite_float as _finite_float
import hashlib
import re
from .errors import InformationBoundaryLeakError


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


def validate_information_boundary(
    payload: Dict[str, Any],
    allowed_keys: Set[str],
    forbidden_keys: Set[str],
    boundary_name: str,
) -> Dict[str, Any]:
    """
    Enforce strict Information-Asymmetry between Planning/Verification and Execution/Coding contexts.
    1. Immediately raises `InformationBoundaryLeakError` if any key in `forbidden_keys` is present.
    2. Strips any undeclared extra keys not in `allowed_keys`.
    """
    present_keys = set(payload.keys())
    leaked = present_keys & forbidden_keys
    if leaked:
        raise InformationBoundaryLeakError(
            f"🚫 [GOODHART INFORMATION BOUNDARY VIOLATION at {boundary_name}] "
            f"Forbidden keys leaked across boundary: {sorted(leaked)}"
        )
    return {k: v for k, v in payload.items() if k in allowed_keys}


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


class SealedHoldoutCapsule:
    """
    Opaque, tamper-evident Hold-Out Target Capsule for Gate 7b.
    Hides the exact hold-out target value and tolerance from `repr()`, `str()`, and `vars()` inspection
    so an execution agent inspecting the spec cannot read the secret target number and tune a magic constant.
    """

    def __init__(
        self,
        metric_name: str,
        secret_target: float,
        secret_tol: float,
        remediation_hint: str = "Verify higher-order physical coupling, measure normalization, and boundary conditions.",
    ) -> None:
        self.metric_name = metric_name
        self.remediation_hint = remediation_hint
        self._commitment_sha256 = hashlib.sha256(
            f"{metric_name}:{secret_target:.12e}:{secret_tol:.12e}".encode("utf-8")
        ).hexdigest()

        def _evaluate(candidate_val: float, borderline_ratio: float = 0.80) -> Dict[str, Any]:
            diff = _finite_float(candidate_val) - _finite_float(secret_target)
            abs_err = abs(diff)
            ratio_to_tol = abs_err / max(_finite_float(secret_tol), 1e-15)
            direction = "OVER-PREDICTED (+)" if diff > 0 else "UNDER-PREDICTED (-)"
            passed = abs_err <= _finite_float(secret_tol)
            is_borderline = passed and (ratio_to_tol >= borderline_ratio)
            return {
                "passed": passed,
                "is_borderline": is_borderline,
                "ratio_to_tol": ratio_to_tol,
                "direction": direction,
                "commitment_sha256": self._commitment_sha256,
            }

        self._evaluate_fn = _evaluate

    @property
    def commitment_sha256(self) -> str:
        return self._commitment_sha256

    def evaluate_blind(self, candidate_value: float, borderline_ratio: float = 0.80) -> Dict[str, Any]:
        return _finite_call(self._evaluate_fn, candidate_value, borderline_ratio=borderline_ratio)

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
        scrubbed = re.sub(r"target\s*=\s*[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", "target=[REDACTED]", raw_msg)
        scrubbed = re.sub(r"tol\s*[-=:]?\s*[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", "tol=[REDACTED]", scrubbed)
        scrubbed = re.sub(r"floor\s*[-=:]?\s*[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", "floor=[REDACTED]", scrubbed)
        for term in _FORBIDDEN_FEEDBACK_TERMS:
            scrubbed = scrubbed.replace(term, "[REDACTED_TERM]")
        guidance.append(scrubbed)

    final_feedback = " ".join(guidance)
    for term in _FORBIDDEN_FEEDBACK_TERMS:
        if term in final_feedback.lower():
            raise InformationBoundaryLeakError(f"Feedback sanitizer failed to scrub `{term}`")
    return final_feedback
