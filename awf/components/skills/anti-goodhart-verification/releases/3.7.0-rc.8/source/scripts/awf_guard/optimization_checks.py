"""AWF Guard: optimization checks."""
from __future__ import annotations

from typing import Dict
from awf_guard_numeric_contracts import finite_float as _finite_float
from awf_guard_numeric_contracts import finite_inputs as _finite_inputs
import numpy as np
from .errors import AntiGoodhartGateError


_SVD_EFFECTIVE_RANK_REL_FLOOR = 1e-3


@_finite_inputs
def audit_parameter_update_trajectory(
    theta_history: np.ndarray,
    expected_total_dof: int,
    min_active_fraction: float = 0.90,
    min_effective_rank: int = 3,
) -> Dict[str, float]:
    """
    SVD & Active-DoF Audit on optimization trajectory matrix `theta_history` (shape: [K+1, D]).
    Catches surrogate scalar scaling (e.g., 3 scalars masquerading as 506 parameters) and frozen parameters.
    """
    if theta_history.ndim != 2 or theta_history.shape[1] != expected_total_dof:
        raise AntiGoodhartGateError(
            f"[Gate 5 DoF Mismatch] Trajectory matrix columns ({theta_history.shape[1]}) != "
            f"declared DoF ({expected_total_dof})."
        )
    n_steps = theta_history.shape[0] - 1
    if n_steps < 3:
        raise AntiGoodhartGateError(
            f"[Gate 5 Truncation] Optimization trajectory has only {n_steps} steps (< 3)."
        )
    delta_theta = np.diff(theta_history, axis=0)
    movement = np.linalg.norm(delta_theta, axis=0)
    active_fraction = _finite_float(np.mean(movement > 1e-8))
    if active_fraction < min_active_fraction:
        raise AntiGoodhartGateError(
            f"[Gate 5 Frozen-DoF Trap] Only {active_fraction*100:.1f}% of declared {expected_total_dof} "
            f"parameters moved during optimization (required >= {min_active_fraction*100:.1f}%)."
        )
    _, s_vals, _ = np.linalg.svd(delta_theta, full_matrices=False)
    norm_s = s_vals / (np.sum(s_vals) + 1e-15)
    eff_rank = int(np.sum(norm_s > _SVD_EFFECTIVE_RANK_REL_FLOOR))
    target_rank = min(n_steps, expected_total_dof, min_effective_rank)
    if eff_rank < target_rank:
        raise AntiGoodhartGateError(
            f"[Gate 5 Surrogate-Scaling Trap] Parameter update trajectory SVD effective rank is only "
            f"{eff_rank} (required >= {target_rank}). Low-rank global multipliers are masquerading as "
            f"full {expected_total_dof}-DoF optimization!"
        )
    return {
        "n_steps": _finite_float(n_steps),
        "active_dof_fraction": active_fraction,
        "svd_effective_rank": _finite_float(eff_rank),
    }
