"""AWF Guard: differential checks."""
from __future__ import annotations

from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional
from typing import Sequence
from typing import Union
from awf_guard_numeric_contracts import finite_array as _finite_array
from awf_guard_numeric_contracts import finite_call as _finite_call
from awf_guard_numeric_contracts import finite_float as _finite_float
from awf_guard_numeric_contracts import finite_inputs as _finite_inputs
import copy
import numpy as np
from .numeric_inputs import _extract_array


_MIN_REFINEMENT_RATIO = 1.0001


_CONVERGENCE_MONOTONE_SLACK = 1.02


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
) -> Dict[str, Any]:
    """
    Verify analytical forces `F = -grad(E)` or analytical gradients `grad(E)` against
    4th-order Richardson-extrapolated central finite differences (`G2b`):
      D(h)   = (E(x + h*e_i) - E(x - h*e_i)) / (2*h)
      D(h/2) = (E(x + h/2*e_i) - E(x - h/2*e_i)) / h
      D_Rich = (4 * D(h/2) - D(h)) / 3
    Detects missing chain-rule terms, wrong force signs, and incomplete Jacobians.
    """
    if coord_arg not in sample_input_kwargs:
        raise ValueError(f"coord_arg `{coord_arg}` not found in sample_input_kwargs")
    base_coords = _finite_array(sample_input_kwargs[coord_arg], dtype=np.float64).copy()
    kw_base = {k: (v.copy() if isinstance(v, np.ndarray) else copy.deepcopy(v)) for k, v in sample_input_kwargs.items()}
    analytic_arr = _extract_array(_finite_call(force_or_grad_fn, **kw_base))
    if analytic_arr.shape != base_coords.shape:
        raise ValueError(
            f"Analytical force/gradient shape {analytic_arr.shape} != coordinate shape {base_coords.shape}"
        )

    fd_rich = np.zeros_like(base_coords, dtype=np.float64)
    flat_coords = base_coords.reshape(-1)
    flat_fd = fd_rich.reshape(-1)
    h1 = _finite_float(step_h)
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
    max_abs_err = _finite_float(np.max(diff)) if diff.size > 0 else 0.0
    denom = np.maximum(np.maximum(np.abs(analytic_arr), np.abs(fd_rich)), 1e-12)
    max_rel_err = _finite_float(np.max(diff / denom)) if diff.size > 0 else 0.0

    norm_a = _finite_float(np.linalg.norm(analytic_arr))
    norm_f = _finite_float(np.linalg.norm(fd_rich))
    cos_sim = (
        _finite_float(np.sum(analytic_arr * fd_rich) / (norm_a * norm_f))
        if (norm_a > 1e-15 and norm_f > 1e-15)
        else 1.0
    )
    sign_flipped = bool(cos_sim < -0.5 and norm_f > 1e-8)
    passed = bool(np.allclose(analytic_arr, fd_rich, rtol=rtol, atol=atol) and not sign_flipped)
    return {
        "status": "PASS" if passed else "FAIL",
        "max_abs_err": round(max_abs_err, 12),
        "max_rel_err": round(max_rel_err, 10),
        "cosine_similarity": round(cos_sim, 8),
        "sign_flipped": sign_flipped,
        "rtol": rtol,
        "atol": atol,
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
    Catches 1st-order Euler/rectangle schemes masquerading as 2nd/4th-order integrators on fine grids.
    """
    if len(resolution_steps) < 3:
        raise ValueError("resolution_steps must contain at least 3 decreasing step sizes (e.g., h, h/2, h/4)")
    steps = [_finite_float(s) for s in resolution_steps]
    kw_common = dict(base_kwargs) if base_kwargs is not None else {}
    ref_arr = (
        _extract_array(exact_or_fine_ref(**kw_common))
        if callable(exact_or_fine_ref)
        else _extract_array(exact_or_fine_ref)
    )

    errors: List[float] = []
    for h_val in steps:
        call_kw = {k: (v.copy() if isinstance(v, np.ndarray) else copy.deepcopy(v)) for k, v in kw_common.items()}
        call_kw[step_kwarg] = h_val
        out_arr = _extract_array(_finite_call(solver_fn, **call_kw))
        err_val = _finite_float(np.max(np.abs(out_arr - ref_arr)))
        errors.append(err_val)

    # If all errors are already at machine precision (< 1e-13), convergence is exact
    if max(errors) < 1e-13:
        return {
            "status": "PASS",
            "steps": steps,
            "errors": errors,
            "pairwise_orders": [expected_order for _ in range(len(steps) - 1)],
            "empirical_order": _finite_float(expected_order),
            "expected_order": _finite_float(expected_order),
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
    passed = bool(monotone_decreasing and slope >= (expected_order - min_order_tolerance))
    return {
        "status": "PASS" if passed else "FAIL",
        "steps": steps,
        "errors": [round(e, 12) for e in errors],
        "pairwise_orders": pairwise_orders,
        "empirical_order": round(slope, 4),
        "expected_order": _finite_float(expected_order),
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
    Infinitesimal Noise-Floor Zero-Point Stability Gate (`G1e`):
    1. Mesh-Refinement Intensive Invariance:
       Evaluates `target_fn(**resolution_input_builder_fn(n_grid))` across grid resolutions `resolutions`
       for the same physical geometry (fixed physical domain size `L = n_grid * h`). Catches voxel-index vs.
       physical-length confusion (e.g. fixed-voxel smoothing `sigma_vox = const`) and staircase threshold-counting
       blowups where refining `n_grid -> 2 * n_grid` inflates intensive observables by +100%..+164%.
    2. Infinitesimal Noise-Floor Zero-Point Stability (Anti-MinMax-Amplification):
       Evaluates `target_fn(**noisy_null_input_kwargs)` on a uniform/single-domain state perturbed by low-amplitude
       noise (`~1e-6`) and verifies `||out - expected_null_output||_inf <= noise_floor_tol`, catching `(x - min)/(max - min)`
       or unregularized z-score normalization that stretches thermal noise into artificial O(1) boundaries.
    """
    if len(resolutions) < 2:
        raise ValueError("`resolutions` must contain at least 2 grid sizes (e.g., (16, 32)).")
    violations: List[str] = []
    outputs: List[np.ndarray] = []
    for n_g in resolutions:
        kw = _finite_call(resolution_input_builder_fn, int(n_g))
        outputs.append(_extract_array(_finite_call(target_fn, **kw)))

    ref_out = outputs[-1]
    ref_norm = _finite_float(np.max(np.abs(ref_out)))
    if ref_norm <= 1e-12:
        violations.append("Fine-grid observable collapsed to zero on non-trivial benchmark geometry.")

    max_rel_drift = 0.0
    for idx in range(len(outputs) - 1):
        drift = _finite_float(np.max(np.abs(outputs[idx] - ref_out))) / max(ref_norm, 1e-12)
        if drift > max_rel_drift:
            max_rel_drift = drift
    if max_rel_drift > max_refinement_rel_drift:
        violations.append(
            f"Mesh-refinement non-invariance: max relative drift across resolutions {list(resolutions)} "
            f"is {max_rel_drift:.4f} > ceiling {max_refinement_rel_drift:.4f} (voxel-unit / staircase blowup trap)"
        )

    noise_floor_err = 0.0
    if noisy_null_input_kwargs is not None:
        noisy_out = _extract_array(_finite_call(target_fn, **noisy_null_input_kwargs))
        exp_null = _finite_array(expected_null_output, dtype=np.float64)
        noise_floor_err = _finite_float(np.max(np.abs(noisy_out - exp_null)))
        if noise_floor_err > noise_floor_tol:
            violations.append(
                f"Infinitesimal noise-floor amplification: ||f(uniform + eps) - null||_inf = {noise_floor_err:.4e} "
                f"> {noise_floor_tol:.2e} (min-max / z-score noise stretching trap)"
            )

    return {
        "status": "PASS" if not violations else "FAIL",
        "resolutions_tested": [int(r) for r in resolutions],
        "max_refinement_rel_drift": round(max_rel_drift, 8),
        "noise_floor_amplification_err": round(noise_floor_err, 12),
        "violations": violations,
    }
