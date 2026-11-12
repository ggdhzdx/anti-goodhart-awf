"""AWF Guard: statistical checks."""
from __future__ import annotations

import math
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple
import numpy as np

from awf_guard_numeric_contracts import finite_array as _finite_array
from awf_guard_numeric_contracts import finite_call as _finite_call
from awf_guard_numeric_contracts import finite_float as _finite_float
from awf_guard_numeric_contracts import finite_inputs as _finite_inputs
from .numeric_inputs import _extract_array, _kwargs_materially_differ

_MAX_G5P_TOL = 1e-2
_G5P_UNDERESTIMATE_FRAC = 0.10
_G5P_REL_VAR_TOL_FLOOR = 1e-3
_MAX_G5S_TOL = 1e-3
_MAX_G7I_TOL = 1e-3
_MIN_LOOCV_FLOOR = 0.50
_MAX_GEN_GAP_CEILING = 0.50
_LOOCV_DIAG_SENTINEL = 1e9
_KISH_HEAVY_WEIGHT = 4.0
_KISH_SKEW_EXACT_RATIO = math.sqrt(5.0 / 3.0)


@_finite_inputs
def verify_bipolar_reachability_and_multisource_variance(
    signed_metric_fn: Callable[[Any], float],
    negative_regime_input: Any,
    positive_regime_input: Any,
    variance_propagator_fn: Optional[Callable[[float, Sequence[float], Sequence[float]], float]] = None,
    baseline_fn: Optional[Callable[[np.ndarray], float]] = None,
    sample_obs_var: float = 1.0,
    sample_baseline_means: Sequence[float] = (100.0, 100.0),
    sample_baseline_vars: Sequence[float] = (4.0, 9.0),
    min_sign_margin: float = 1e-6,
    var_tol: float = 1e-6,
) -> Dict[str, Any]:
    """
    Domain-Agnostic Bipolar Regime Reachability & Multi-Source Delta-Method Variance Gate (`G5p`).
    """
    margin_f = _finite_float(min_sign_margin)
    vtol_f = _finite_float(var_tol)
    if margin_f < 1e-9 or not (0.0 < vtol_f <= _MAX_G5P_TOL):
        raise ValueError(f"Invalid G5p bounds: min_sign_margin={margin_f}, var_tol={vtol_f}")
    val_neg = _finite_float(_finite_call(signed_metric_fn, negative_regime_input))
    val_pos = _finite_float(_finite_call(signed_metric_fn, positive_regime_input))
    violations: List[str] = []

    if not (val_neg < -margin_f):
        violations.append(
            f"Bipolar negative-regime unreachability: f(x_neg) = {val_neg:.6e} >= -{margin_f:.2e} (non-negative surrogate trap)"
        )
    if not (val_pos > margin_f):
        violations.append(
            f"Bipolar positive-regime unreachability: f(x_pos) = {val_pos:.6e} <= +{margin_f:.2e}"
        )

    if (variance_propagator_fn is None) != (baseline_fn is None):
        violations.append("Both variance_propagator_fn and baseline_fn must be supplied together.")

    var_err = 0.0
    reported_var = _finite_float(sample_obs_var)
    expected_var = _finite_float(sample_obs_var)
    if variance_propagator_fn is not None and baseline_fn is not None:
        theta0 = _finite_array(sample_baseline_means, dtype=np.float64)
        v_ref = _finite_array(sample_baseline_vars, dtype=np.float64)
        grad = np.zeros_like(theta0)
        eps = 1e-6
        for idx in range(len(theta0)):
            step = np.zeros_like(theta0)
            step[idx] = eps * max(abs(_finite_float(theta0[idx])), 1.0)
            grad[idx] = (_finite_float(_finite_call(baseline_fn, theta0 + step)) - _finite_float(_finite_call(baseline_fn, theta0 - step))) / (2.0 * step[idx])
        baseline_contrib = _finite_float(np.sum((grad ** 2) * v_ref))
        expected_var = _finite_float(sample_obs_var) + baseline_contrib
        reported_var = _finite_float(_finite_call(variance_propagator_fn, _finite_float(sample_obs_var), sample_baseline_means, sample_baseline_vars))
        var_err = abs(reported_var - expected_var)
        if reported_var <= _finite_float(sample_obs_var) + min(1e-12, _G5P_UNDERESTIMATE_FRAC * max(baseline_contrib, 0.0)) and baseline_contrib > 0.0:
            violations.append(
                f"Single-source variance underestimation: reported_var ({reported_var:.6e}) <= obs_var ({sample_obs_var:.6e}), omitting baseline uncertainty!"
            )
        rel_err = var_err / max(abs(baseline_contrib), 1e-30) if baseline_contrib > 0.0 else 0.0
        if var_err > vtol_f or (baseline_contrib > 0.0 and rel_err > max(vtol_f * 100.0, _G5P_REL_VAR_TOL_FLOOR)):
            violations.append(
                f"Delta-method multi-source variance mismatch: |reported ({reported_var:.6e}) - expected ({expected_var:.6e})| = {var_err:.3e} > {vtol_f:.2e}"
            )

    return {
        "status": "PASS" if not violations else "FAIL",
        "negative_regime_value": round(val_neg, 8),
        "positive_regime_value": round(val_pos, 8),
        "reported_multisource_var": round(reported_var, 8),
        "expected_multisource_var": round(expected_var, 8),
        "variance_propagation_err": round(var_err, 12),
        "violations": violations,
    }


def _infer_weight_arg_name(base_input_kwargs: Dict[str, Any], scaled_arg_name: str, n_obs: int) -> Optional[str]:
    for key, val in base_input_kwargs.items():
        if key != scaled_arg_name and isinstance(val, np.ndarray) and val.ndim == 1 and len(val) == n_obs:
            return key
    return None


@_finite_inputs
def verify_weighted_dispersion_kish_and_scale_invariance(
    dispersion_fn: Callable[..., Any],
    base_input_kwargs: Dict[str, Any],
    scaled_arg_name: str,
    scale_factors: Sequence[float] = (0.75, 1.25),
    output_homogeneity_degrees: Sequence[float] = (1.0, 1.0, 0.0, 0.0),
    zero_weight_padded_kwargs: Optional[Dict[str, Any]] = None,
    raw_to_debiased_indices: Optional[Tuple[int, int]] = (2, 3),
    expected_debias_ratio: float = math.sqrt(2.0 * math.pi),
    tol: float = 1e-8,
) -> Dict[str, Any]:
    """
    Domain-Agnostic Weighted Moment/Dispersion Mixed-Degree Homogeneity, Zero-Weight Outlier
    Kish-Invariance, Skewed-Weight Exact Kish N_eff Bessel Identity & Window-Debiasing Gate (`G5s`).
    """
    tol_f = _finite_float(tol)
    if not (0.0 < tol_f <= _MAX_G5S_TOL):
        raise ValueError(f"G5s tol must be in (0, {_MAX_G5S_TOL}], got {tol_f}")
    violations: List[str] = []
    vals_base = _finite_array(base_input_kwargs[scaled_arg_name], dtype=np.float64)
    out_base = _extract_array(_finite_call(dispersion_fn, **base_input_kwargs)).reshape(-1)
    max_scale_err = 0.0

    for lam in scale_factors:
        kw_lam = dict(base_input_kwargs)
        kw_lam[scaled_arg_name] = vals_base * _finite_float(lam)
        out_lam = _extract_array(_finite_call(dispersion_fn, **kw_lam)).reshape(-1)
        for j, deg in enumerate(output_homogeneity_degrees):
            expected_j = (_finite_float(lam) ** _finite_float(deg)) * _finite_float(out_base[j])
            err_j = abs(_finite_float(out_lam[j]) - expected_j)
            if err_j > max_scale_err:
                max_scale_err = err_j
    if max_scale_err > tol_f:
        violations.append(
            f"Mixed-degree coordinate-scaling homogeneity violation on `{scaled_arg_name}`: "
            f"max |f_j(lam*x) - lam^d_j f_j(x)| = {max_scale_err:.4e} > {tol_f:.2e}"
        )

    zero_weight_pad_err = 0.0
    if zero_weight_padded_kwargs is None:
        violations.append("Zero-weight outlier padding probe `zero_weight_padded_kwargs` is required for G5s.")
    else:
        if not _kwargs_materially_differ(base_input_kwargs, zero_weight_padded_kwargs, target_fn=dispersion_fn):
            violations.append("Zero-weight outlier padding probe is identical to base_input_kwargs.")
        out_pad = _extract_array(_finite_call(dispersion_fn, **zero_weight_padded_kwargs)).reshape(-1)
        zero_weight_pad_err = _finite_float(np.max(np.abs(out_pad - out_base)))
        if zero_weight_pad_err > tol_f:
            violations.append(
                f"Zero-weight outlier padding / Kish N_eff invariance violation: "
                f"max |f(padded) - f(base)| = {zero_weight_pad_err:.4e} > {tol_f:.2e} "
                f"(naive N/(N-1) Bessel correction or missing kernel gating)"
            )

    weight_key = _infer_weight_arg_name(base_input_kwargs, scaled_arg_name, len(vals_base))
    if weight_key is not None and len(vals_base) >= 2 and len(out_base) >= 2:
        v0, v1 = _finite_float(vals_base[0]), _finite_float(vals_base[-1])
        if abs(v1 - v0) > 1e-12:
            kw_rep = dict(base_input_kwargs)
            kw_rep[scaled_arg_name] = np.array([v0, v0, v1, v1, v1, v1], dtype=np.float64)
            kw_rep[weight_key] = np.ones(6, dtype=np.float64)
            kw_skew = dict(base_input_kwargs)
            kw_skew[scaled_arg_name] = np.array([v0, v0, v1], dtype=np.float64)
            kw_skew[weight_key] = np.array([1.0, 1.0, _KISH_HEAVY_WEIGHT], dtype=np.float64)
            sd_rep = _finite_float(_extract_array(_finite_call(dispersion_fn, **kw_rep)).reshape(-1)[1])
            sd_skew = _finite_float(_extract_array(_finite_call(dispersion_fn, **kw_skew)).reshape(-1)[1])
            kish_ratio = sd_skew / max(abs(sd_rep), 1e-30)
            if abs(kish_ratio - _KISH_SKEW_EXACT_RATIO) > max(tol_f * 10.0, 1e-6):
                violations.append(
                    f"Kish N_eff skewed-weight Bessel correction violation: sd([1,1,4])/sd([1]*6) = {kish_ratio:.6f} "
                    f"!= sqrt(5/3) = {_KISH_SKEW_EXACT_RATIO:.6f} (unweighted ddof=1, biased, or frequency-weight bug)"
                )

    debias_ratio_err = 0.0
    if raw_to_debiased_indices is not None:
        i_raw, i_deb = raw_to_debiased_indices
        v_raw, v_deb = _finite_float(out_base[i_raw]), _finite_float(out_base[i_deb])
        if v_raw <= 0.0 or v_deb <= 0.0:
            violations.append(f"Degenerate non-positive dispersion in base sample: raw={v_raw}, debiased={v_deb}")
        else:
            debias_ratio_err = abs((v_raw / v_deb) - _finite_float(expected_debias_ratio))
            if debias_ratio_err > tol_f:
                violations.append(
                    f"Window-debiasing ratio violation: out[{i_raw}]/out[{i_deb}] = {v_raw / v_deb:.6f} "
                    f"!= expected {_finite_float(expected_debias_ratio):.6f}"
                )

    return {
        "status": "PASS" if not violations else "FAIL",
        "max_mixed_degree_scale_err": round(max_scale_err, 12),
        "zero_weight_outlier_pad_err": round(zero_weight_pad_err, 12),
        "debias_ratio_err": round(debias_ratio_err, 12),
        "violations": violations,
    }


@_finite_inputs
def verify_loocv_generalization_and_train_eval_parity(
    design_matrix: np.ndarray,
    targets: np.ndarray,
    min_loocv_r2: float = 0.75,
    max_generalization_gap: float = 0.20,
    calibrate_feature_fn: Optional[Callable[[Any], Any]] = None,
    eval_feature_fn: Optional[Callable[[Any], Any]] = None,
    parity_test_inputs: Optional[Sequence[Any]] = None,
    tol: float = 1e-9,
) -> Dict[str, Any]:
    """
    Domain-Agnostic Out-of-Sample LOOCV Generalization & Train/Eval Feature-Pipeline Parity Gate (`G7i`).
    """
    tol_f = _finite_float(tol)
    min_r2_f = _finite_float(min_loocv_r2)
    max_gap_f = _finite_float(max_generalization_gap)
    if not (0.0 < tol_f <= _MAX_G7I_TOL) or min_r2_f < _MIN_LOOCV_FLOOR or not (0.0 < max_gap_f <= _MAX_GEN_GAP_CEILING):
        raise ValueError(f"Invalid G7i thresholds: min_loocv_r2={min_r2_f}, max_generalization_gap={max_gap_f}, tol={tol_f}")

    x_mat = _finite_array(design_matrix, dtype=np.float64)
    y_vec = _finite_array(targets, dtype=np.float64).reshape(-1)
    if x_mat.ndim != 2 or x_mat.shape[0] < 3 or x_mat.shape[0] != len(y_vec):
        raise ValueError(f"G7i requires 2D design_matrix (N >= 3, p) matching targets length; got {x_mat.shape}, {y_vec.shape}")
    n_samples = x_mat.shape[0]
    violations: List[str] = []

    row_dists = np.linalg.norm(x_mat[:, None, :] - x_mat[None, :, :], axis=-1) + np.eye(n_samples) * _LOOCV_DIAG_SENTINEL
    if _finite_float(np.min(row_dists)) <= 1e-8:
        violations.append("LOOCV duplicate-row memorization leakage: design_matrix contains identical/near-identical rows.")

    beta, _, _, _ = np.linalg.lstsq(x_mat, y_vec, rcond=None)
    y_pred = x_mat @ beta
    ss_tot = _finite_float(np.sum((y_vec - np.mean(y_vec)) ** 2))
    if ss_tot <= 1e-14:
        violations.append("LOOCV constant target collapse: targets have zero variance.")
        ss_tot = 1e-14
    in_sample_r2 = 1.0 - _finite_float(np.sum((y_vec - y_pred) ** 2)) / ss_tot

    u_mat, s_vals, _ = np.linalg.svd(x_mat, full_matrices=False)
    pos_mask = s_vals > 1e-12
    eff_rank = int(np.sum(pos_mask))
    u_eff = u_mat[:, pos_mask]
    h_diag = np.sum(u_eff ** 2, axis=1)
    max_leverage = _finite_float(np.max(h_diag)) if h_diag.size > 0 else 1.0
    if eff_rank >= n_samples or max_leverage >= 1.0 - 1e-6:
        violations.append(
            f"LOOCV high-leverage singularity (h_ii -> 1): max_leverage={max_leverage:.6f}, rank={eff_rank}, n={n_samples}"
        )
    denom = np.maximum(1.0 - h_diag, 1e-6)
    loo_resid = (y_vec - y_pred) / denom
    loocv_r2 = 1.0 - _finite_float(np.sum(loo_resid ** 2)) / ss_tot
    gen_gap = in_sample_r2 - loocv_r2

    if loocv_r2 < min_r2_f:
        violations.append(f"LOOCV R^2 = {loocv_r2:.4f} < min_loocv_r2 {min_r2_f:.4f}")
    if gen_gap > max_gap_f:
        violations.append(f"Generalization gap (R^2_train - R^2_LOOCV) = {gen_gap:.4f} > {max_gap_f:.4f}")

    max_skew = 0.0
    if calibrate_feature_fn is not None or eval_feature_fn is not None:
        if calibrate_feature_fn is None or eval_feature_fn is None or not parity_test_inputs:
            violations.append("Train/Eval feature-pipeline parity check requires calibrate_feature_fn, eval_feature_fn, and non-empty parity_test_inputs.")
        else:
            for inp in parity_test_inputs:
                f_cal = _extract_array(_finite_call(calibrate_feature_fn, inp))
                f_evl = _extract_array(_finite_call(eval_feature_fn, inp))
                skew = _finite_float(np.max(np.abs(f_cal - f_evl)))
                if skew > max_skew:
                    max_skew = skew
            if max_skew > tol_f:
                violations.append(f"Train/Eval feature-pipeline skew: max ||f_cal(x) - f_eval(x)||_inf = {max_skew:.4e} > {tol_f:.3e}")

    return {
        "status": "PASS" if not violations else "FAIL",
        "in_sample_r2": round(in_sample_r2, 6),
        "loocv_r2": round(loocv_r2, 6),
        "generalization_gap": round(gen_gap, 6),
        "max_train_eval_skew": round(max_skew, 12),
        "violations": violations,
    }
