"""AWF Guard: spec integrity."""
from __future__ import annotations

import ast
import inspect
import numpy as np

from awf_guard_numeric_contracts import finite_array as _finite_array
from awf_guard_numeric_contracts import finite_call as _finite_call
from awf_guard_numeric_contracts import finite_float as _finite_float
from awf_guard_numeric_contracts import finite_inputs as _finite_inputs
from .ast_utils import _ast_structure_similarity, _unwrap_target_fn, text_dedent
from .errors import SecondOrderCollusionError
from .evidence_contracts import require_distinct_reference
from .numeric_inputs import _kwargs_materially_differ
from .station_spec import MetaBoundsPolicy, StationVerificationSpec

_MAX_ALLOWED_HOLDOUT_TOL = 0.50
_MIN_ALLOWED_SAFETY_SCORE = 80.0


def _audit_common_tier_bounds(spec: StationVerificationSpec, policy: MetaBoundsPolicy) -> None:
    max_lim_tol = (
        policy.max_allowed_limit_tol_stochastic
        if spec.mode == "stochastic"
        else policy.max_allowed_limit_tol_deterministic
    )
    if spec.limit_tol <= 0.0 or spec.limit_tol > max_lim_tol:
        raise SecondOrderCollusionError(
            f"[Meta-Guard Threshold Dilution] spec.limit_tol ({spec.limit_tol}) outside (0, {max_lim_tol}]."
        )
    if spec.residual_tol <= 0.0 or spec.residual_tol > max_lim_tol:
        raise SecondOrderCollusionError(
            f"[Meta-Guard Threshold Dilution] spec.residual_tol ({spec.residual_tol}) outside (0, {max_lim_tol}]."
        )
    if spec.holdout_orthogonal_tol <= 0.0 or spec.holdout_orthogonal_tol > _MAX_ALLOWED_HOLDOUT_TOL:
        raise SecondOrderCollusionError(
            f"[Meta-Guard Threshold Dilution] spec.holdout_orthogonal_tol ({spec.holdout_orthogonal_tol}) "
            f"outside (0, {_MAX_ALLOWED_HOLDOUT_TOL}]."
        )
    if spec.sealed_holdout_capsule is not None and not spec.sealed_holdout_capsule._capsule_tol_bound_ok(_MAX_ALLOWED_HOLDOUT_TOL):
        raise SecondOrderCollusionError(
            f"[Meta-Guard Threshold Dilution] SealedHoldoutCapsule secret_tol exceeds ceiling {_MAX_ALLOWED_HOLDOUT_TOL}."
        )
    if spec.min_ablation_shock < policy.min_ablation_shock_floor:
        raise SecondOrderCollusionError(
            f"[Meta-Guard Sensitivity Dilution] spec.min_ablation_shock ({spec.min_ablation_shock}) "
            f"is below floor {policy.min_ablation_shock_floor}."
        )
    if spec.ncc_floor < policy.min_ncc_floor:
        raise SecondOrderCollusionError(
            f"[Meta-Guard Provenance Dilution] spec.ncc_floor ({spec.ncc_floor}) is below floor {policy.min_ncc_floor}."
        )
    if spec.min_verifier_safety_score < _MIN_ALLOWED_SAFETY_SCORE:
        raise SecondOrderCollusionError(
            f"[Meta-Guard Verifier-Safety Dilution] spec.min_verifier_safety_score ({spec.min_verifier_safety_score}) "
            f"is below floor {_MIN_ALLOWED_SAFETY_SCORE}."
        )


@_finite_inputs
def audit_spec_integrity(
    spec: StationVerificationSpec,
    policy: MetaBoundsPolicy = MetaBoundsPolicy(),
) -> None:
    """
    Second-Order Anti-Collusion Meta-Guard (`Meta-Guard`).
    Inspects `StationVerificationSpec` BEFORE running G1..G7 to ensure the spec itself was not watered down.
    """
    if type(spec.tier) is not int or spec.tier not in (0, 1, 2):
        raise SecondOrderCollusionError(
            f"[Meta-Guard Invalid Tier] spec.tier must be exact int in {{0, 1, 2}}, got {spec.tier!r} ({type(spec.tier).__name__})."
        )
    if spec.mode not in ("deterministic", "stochastic"):
        raise SecondOrderCollusionError(f"[Meta-Guard Invalid Mode] Unknown spec.mode {spec.mode!r}.")
    if spec.tier == 0:
        return

    _audit_common_tier_bounds(spec, policy)

    if spec.tier >= 2:
        max_ora_tol = (
            policy.max_allowed_oracle_tol_stochastic
            if spec.mode == "stochastic"
            else policy.max_allowed_oracle_tol_deterministic
        )
        if spec.oracle_tol <= 0.0 or spec.oracle_tol > max_ora_tol:
            raise SecondOrderCollusionError(
                f"[Meta-Guard Threshold Dilution] spec.oracle_tol ({spec.oracle_tol}) outside (0, {max_ora_tol}]."
            )
        if spec.min_perturbation_delta < policy.min_perturbation_floor:
            raise SecondOrderCollusionError(
                f"[Meta-Guard Sensitivity Dilution] spec.min_perturbation_delta ({spec.min_perturbation_delta}) "
                f"is below floor {policy.min_perturbation_floor}."
            )
        if spec.orthogonal_oracle_fn is None:
            raise SecondOrderCollusionError(
                "[Meta-Guard Missing Oracle] Tier-2 Production Seal requires a non-null `orthogonal_oracle_fn`."
            )
        try:
            require_distinct_reference(spec.target_fn, spec.orthogonal_oracle_fn)
        except ValueError as exc:
            raise SecondOrderCollusionError(f"[Meta-Guard Collusive Oracle] {exc}") from exc
        raw_target = _finite_call(_unwrap_target_fn, spec.target_fn)
        raw_oracle = _finite_call(_unwrap_target_fn, spec.orthogonal_oracle_fn)
        try:
            src_target = inspect.getsource(raw_target)
            src_oracle = inspect.getsource(raw_oracle)
            if raw_target.__name__ in src_oracle and "def " in src_oracle:
                tree_ora = ast.parse(text_dedent(src_oracle))
                for node in ast.walk(tree_ora):
                    if isinstance(node, ast.Call) and getattr(node.func, "id", "") == raw_target.__name__:
                        raise SecondOrderCollusionError(
                            f"[Meta-Guard Collusive Oracle] `orthogonal_oracle_fn` directly calls `{raw_target.__name__}`!"
                        )
            ast_sim = _ast_structure_similarity(src_target, src_oracle)
            if ast_sim > policy.max_oracle_ast_similarity:
                raise SecondOrderCollusionError(
                    f"[Meta-Guard Collusive Copy-Paste Oracle] `orthogonal_oracle_fn` has AST similarity "
                    f"{ast_sim:.2f} > {policy.max_oracle_ast_similarity} with `target_fn`."
                )
        except (OSError, TypeError):
            src_target = ""

        if spec.symmetry_transform_fn is not None and spec.small_input_kwargs:
            sym_in = _finite_call(spec.symmetry_transform_fn, dict(spec.small_input_kwargs))
            if not _kwargs_materially_differ(spec.small_input_kwargs, sym_in, target_fn=spec.target_fn):
                raise SecondOrderCollusionError(
                    "[Meta-Guard Trivial Symmetry Spoofing] `symmetry_transform_fn` left effective inputs unchanged (Identity Map)!"
                )
            diffs = [
                _finite_float(np.linalg.norm(_finite_array(sym_in[k], dtype=float) - _finite_array(v, dtype=float)))
                for k, v in spec.small_input_kwargs.items()
                if isinstance(v, np.ndarray) and k in sym_in
            ]
            if diffs and max(diffs) < 1e-8:
                raise SecondOrderCollusionError(
                    "[Meta-Guard Trivial Symmetry Spoofing] `symmetry_transform_fn` left all input arrays unchanged (Identity Map)!"
                )
