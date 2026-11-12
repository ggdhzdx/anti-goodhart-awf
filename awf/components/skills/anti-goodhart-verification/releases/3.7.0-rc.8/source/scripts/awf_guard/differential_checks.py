"""AWF Guard: differential checks."""
from __future__ import annotations

import copy
from typing import Any, Callable, Dict, List, Optional, Sequence, Union
import numpy as np

from awf_guard_numeric_contracts import finite_array as _finite_array
from awf_guard_numeric_contracts import finite_call as _finite_call
from awf_guard_numeric_contracts import finite_float as _finite_float
from awf_guard_numeric_contracts import finite_inputs as _finite_inputs
from .evidence_contracts import call_without_target_reentry, require_distinct_reference
from .numeric_inputs import _extract_array, _kwargs_materially_differ

_MIN_REFINEMENT_RATIO = 1.0001
_CONVERGENCE_MONOTONE_SLACK = 1.02
_MAX_G2B_RTOL = 1e-2
_MAX_G2B_ATOL = 1e-3
_MAX_G2B_STEP = 0.1
_MAX_ORDER_TOL = 0.50
_PAIRWISE_ORDER_SLACK = 0.35
_MAX_G1E_DRIFT_CEILING = 0.25
_MAX_G1E_NOISE_TOL = 1e-2
_COSINE_SIGN_FLIP_THRESHOLD = -0.5


@_finite_inputs
def verify_analytic_gradient_finite_difference(
    energy_fn: Callable[..., Any],
    force_or_grad_fn: Callable[..., Any],
    sample_input_kwargs: Dict[str, Any],
    coord_arg: str = "r",
    step_h: float = 1e-5,
    is_negative_gradient: bool = True,
    rtol: float = 1e-4,
    atol: float = 1e-6,
    allow_zero_gradient: bool = False,
) -> Dict[str, Any]:
    """
    Verify analytical forces `F = -grad(E)` or analytical gradients `grad(E)` against
    4th-order Richardson-extrapolated central finite differences (`G2b`).
    """
    if coord_arg not in sample_input_kwargs:
        raise ValueError(f"coord_arg `{coord_arg}` not found in sample_input_kwargs")
    h1 = _finite_float(step_h)
    rtol_f = _finite_float(rtol)
    atol_f = _finite_float(atol)
    if not (0.0 < h1 <= _MAX_G2B_STEP) or not (0.0 < rtol_f <= _MAX_G2B_RTOL) or not (0.0 < atol_f <= _MAX_G2B_ATOL):
        raise ValueError(f"Invalid G2b step/tolerance bounds: step_h={h1}, rtol={rtol_f}, atol={atol_f}")
    base_coords = _finite_array(sample_input_kwargs[coord_arg], dtype=np.float64).copy()
    if base_coords.size == 0:
        raise ValueError("G2b coordinate array must be non-empty")
    kw_base = {k: (v.copy() if isinstance(v, np.ndarray) else copy.deepcopy(v)) for k, v in sample_input_kwargs.items()}
    analytic_arr = _extract_array(_finite_call(force_or_grad_fn, **kw_base))
    if analytic_arr.shape != base_coords.shape:
        raise ValueError(
            f"Analytical force/gradient shape {analytic_arr.shape} != coordinate shape {base_coords.shape}"
        )

    fd_rich = np.zeros_like(base_coords, dtype=np.float64)
    flat_coords = base_coords.reshape(-1)
    flat_fd = fd_rich.reshape(-1)
    h2 = 0.5 * h1

    for idx in range(flat_coords.size):
        orig_val = flat_coords[idx]
        deltas: List[float] = []
        for step_val in (h1, h2):
            flat_coords[idx] = orig_val + step_val
            kw_plus = dict(sample_input_kwargs)
            kw_plus[coord_arg] = flat_coords.reshape(base_coords.shape).copy()
            e_plus = _finite_float(np.sum(_extract_array(_finite_call(energy_fn, **kw_plus))))

            flat_coords[idx] = orig_val - step_val
            kw_minus = dict(sample_input_kwargs)
            kw_minus[coord_arg] = flat_coords.reshape(base_coords.shape).copy()
            e_minus = _finite_float(np.sum(_extract_array(_finite_call(energy_fn, **kw_minus))))
            deltas.append((e_plus - e_minus) / (2.0 * step_val))
        flat_coords[idx] = orig_val
        d_rich = (4.0 * deltas[1] - deltas[0]) / 3.0
        flat_fd[idx] = -d_rich if is_negative_gradient else d_rich

    diff = np.abs(analytic_arr - fd_rich)
    max_abs_err = _finite_float(np.max(diff))
    denom = np.maximum(np.maximum(np.abs(analytic_arr), np.abs(fd_rich)), 1e-12)
    max_rel_err = _finite_float(np.max(diff / denom))

    norm_a = _finite_float(np.linalg.norm(analytic_arr))
    norm_f = _finite_float(np.linalg.norm(fd_rich))
    zero_collapse = bool(not allow_zero_gradient and norm_a <= 1e-14 and norm_f <= 1e-14)
    if norm_a > 1e-15 and norm_f > 1e-15:
        cos_sim = _finite_float(np.sum(analytic_arr * fd_rich) / (norm_a * norm_f))
    elif norm_a <= 1e-15 and norm_f <= 1e-15:
        cos_sim = 1.0 if not zero_collapse else 0.0
    else:
        cos_sim = 0.0
    sign_flipped = bool(cos_sim < _COSINE_SIGN_FLIP_THRESHOLD and (norm_f > 1e-14 or norm_a > 1e-14))
    passed = bool(
        not zero_collapse
        and not sign_flipped
        and np.allclose(analytic_arr, fd_rich, rtol=rtol_f, atol=atol_f)
    )
    return {
        "status": "PASS" if passed else "FAIL",
        "max_abs_err": round(max_abs_err, 12),
        "max_rel_err": round(max_rel_err, 10),
        "cosine_similarity": round(cos_sim, 8),
        "sign_flipped": sign_flipped,
        "zero_gradient_collapse": zero_collapse,
        "rtol": rtol_f,
        "atol": atol_f,
    }


@_finite_inputs
def verify_asymptotic_convergence_order(
    solver_fn: Callable[..., Any],
    exact_or_fine_ref: Union[np.ndarray, float, Callable[..., Any]],
    resolution_steps: Sequence[float] = (0.2, 0.1, 0.05),
    step_kwarg: str = "h",
    base_kwargs: Optional[Dict[str, Any]] = None,
    expected_order: float = 2.0,
    min_order_tolerance: float = 0.25,
) -> Dict[str, Any]:
    """
    Verify asymptotic numerical convergence order `O(h^p)` across successively refined grid/time steps (`G1d`).
    """
    if len(resolution_steps) < 3:
        raise ValueError("resolution_steps must contain at least 3 decreasing step sizes (e.g., h, h/2, h/4)")
    steps = [_finite_float(s) for s in resolution_steps]
    if any(s <= 0.0 for s in steps) or any(steps[i + 1] >= steps[i] for i in range(len(steps) - 1)):
        raise ValueError(f"resolution_steps must be strictly positive and strictly decreasing, got {steps}")
    exp_ord = _finite_float(expected_order)
    ord_tol = _finite_float(min_order_tolerance)
    if exp_ord <= 0.0 or not (0.0 <= ord_tol <= _MAX_ORDER_TOL):
        raise ValueError(f"Invalid expected_order={exp_ord} or min_order_tolerance={ord_tol}")

    kw_common = dict(base_kwargs) if base_kwargs is not None else {}
    if callable(exact_or_fine_ref):
        require_distinct_reference(solver_fn, exact_or_fine_ref)
        ref_arr = _extract_array(_finite_call(call_without_target_reentry, exact_or_fine_ref, solver_fn, **kw_common))
    else:
        ref_arr = _extract_array(exact_or_fine_ref)

    errors: List[float] = []
    outputs: List[np.ndarray] = []
    for h_val in steps:
        call_kw = {k: (v.copy() if isinstance(v, np.ndarray) else copy.deepcopy(v)) for k, v in kw_common.items()}
        call_kw[step_kwarg] = h_val
        out_arr = _extract_array(_finite_call(solver_fn, **call_kw))
        outputs.append(out_arr)
        err_val = _finite_float(np.max(np.abs(out_arr - ref_arr)))
        errors.append(err_val)

    step_variation = max(_finite_float(np.max(np.abs(outputs[i] - outputs[-1]))) for i in range(len(outputs) - 1))
    if max(errors) < 1e-13:
        if step_variation == 0.0 and max(errors) == 0.0:
            return {
                "status": "FAIL",
                "steps": steps,
                "errors": errors,
                "pairwise_orders": [0.0 for _ in range(len(steps) - 1)],
                "empirical_order": 0.0,
                "expected_order": exp_ord,
                "monotone_decreasing": False,
            }
        return {
            "status": "PASS",
            "steps": steps,
            "errors": errors,
            "pairwise_orders": [exp_ord for _ in range(len(steps) - 1)],
            "empirical_order": exp_ord,
            "expected_order": exp_ord,
            "monotone_decreasing": True,
        }

    pairwise_orders: List[float] = []
    for i in range(len(steps) - 1):
        e_coarse = max(errors[i], 1e-16)
        e_fine = max(errors[i + 1], 1e-16)
        h_ratio = steps[i] / max(steps[i + 1], 1e-16)
        p_i = _finite_float(np.log(e_coarse / e_fine) / np.log(max(h_ratio, _MIN_REFINEMENT_RATIO)))
        pairwise_orders.append(round(p_i, 4))

    log_h = np.log(_finite_array(steps, dtype=np.float64))
    log_e = np.log(np.maximum(_finite_array(errors, dtype=np.float64), 1e-16))
    slope = _finite_float(np.polyfit(log_h, log_e, 1)[0])
    monotone_decreasing = all(errors[i + 1] <= errors[i] * _CONVERGENCE_MONOTONE_SLACK for i in range(len(errors) - 1))
    pairwise_ok = min(pairwise_orders) >= (exp_ord - ord_tol - _PAIRWISE_ORDER_SLACK)
    passed = bool(monotone_decreasing and pairwise_ok and slope >= (exp_ord - ord_tol))
    return {
        "status": "PASS" if passed else "FAIL",
        "steps": steps,
        "errors": [round(e, 12) for e in errors],
        "pairwise_orders": pairwise_orders,
        "empirical_order": round(slope, 4),
        "expected_order": exp_ord,
        "monotone_decreasing": monotone_decreasing,
    }


@_finite_inputs
def verify_mesh_refinement_invariance_and_noise_floor(
    target_fn: Callable[..., Any],
    resolution_input_builder_fn: Callable[[int], Dict[str, Any]],
    resolutions: Sequence[int] = (16, 32),
    max_refinement_rel_drift: float = 0.05,
    noisy_null_input_kwargs: Optional[Dict[str, Any]] = None,
    expected_null_output: Union[float, np.ndarray] = 0.0,
    noise_floor_tol: float = 1e-6,
) -> Dict[str, Any]:
    """
    Domain-Agnostic Continuum Mesh-Refinement Intensive Invariance &
    Infinitesimal Noise-Floor Zero-Point Stability Gate (`G1e`).
    """
    res_ints = [int(r) for r in resolutions]
    if len(res_ints) < 2 or len(set(res_ints)) < 2 or any(r < 2 for r in res_ints):
        raise ValueError("`resolutions` must contain at least 2 distinct grid sizes >= 2 (e.g., (16, 32)).")
    drift_ceil = _finite_float(max_refinement_rel_drift)
    nf_tol = _finite_float(noise_floor_tol)
    if not (0.0 < drift_ceil <= _MAX_G1E_DRIFT_CEILING) or not (0.0 < nf_tol <= _MAX_G1E_NOISE_TOL):
        raise ValueError(f"Invalid G1e tolerances: max_refinement_rel_drift={drift_ceil}, noise_floor_tol={nf_tol}")

    violations: List[str] = []
    outputs: List[np.ndarray] = []
    built_kwargs: List[Dict[str, Any]] = []
    for n_g in res_ints:
        kw = _finite_call(resolution_input_builder_fn, n_g)
        built_kwargs.append(kw)
        outputs.append(_extract_array(_finite_call(target_fn, **kw)))

    if not _kwargs_materially_differ(built_kwargs[0], built_kwargs[-1], target_fn=target_fn):
        violations.append("Vacuous mesh builder: coarse and fine resolution inputs are identical.")

    ref_out = outputs[-1]
    ref_norm = _finite_float(np.max(np.abs(ref_out)))
    if ref_norm <= 1e-12:
        violations.append("Fine-grid observable collapsed to zero on non-trivial benchmark geometry.")

    max_rel_drift = 0.0
    for idx in range(len(outputs) - 1):
        drift = _finite_float(np.max(np.abs(outputs[idx] - ref_out))) / max(ref_norm, 1e-12)
        if drift > max_rel_drift:
            max_rel_drift = drift
    if max_rel_drift > drift_ceil:
        violations.append(
            f"Mesh-refinement non-invariance: max relative drift across resolutions {res_ints} "
            f"is {max_rel_drift:.4f} > ceiling {drift_ceil:.4f} (voxel-unit / staircase blowup trap)"
        )

    noise_floor_err = 0.0
    if noisy_null_input_kwargs is not None:
        noisy_out = _extract_array(_finite_call(target_fn, **noisy_null_input_kwargs))
        exp_null = _finite_array(expected_null_output, dtype=np.float64)
        noise_floor_err = _finite_float(np.max(np.abs(noisy_out - exp_null)))
        if noise_floor_err > nf_tol:
            violations.append(
                f"Infinitesimal noise-floor amplification: ||f(uniform + eps) - null||_inf = {noise_floor_err:.4e} "
                f"> {nf_tol:.2e} (min-max / z-score noise stretching trap)"
            )

    return {
        "status": "PASS" if not violations else "FAIL",
        "resolutions_tested": res_ints,
        "max_refinement_rel_drift": round(max_rel_drift, 8),
        "noise_floor_amplification_err": round(noise_floor_err, 12),
        "violations": violations,
    }
