"""AWF Guard: statistical checks."""
from __future__ import annotations

from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional
from typing import Sequence
from typing import Tuple
from awf_guard_numeric_contracts import finite_array as _finite_array
from awf_guard_numeric_contracts import finite_call as _finite_call
from awf_guard_numeric_contracts import finite_float as _finite_float
from awf_guard_numeric_contracts import finite_inputs as _finite_inputs
import math
import numpy as np
from .numeric_inputs import _extract_array


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
    Domain-Agnostic Bipolar Regime Reachability & Multi-Source Delta-Method Variance Gate (`G5p`):
    1. Bipolar Sign Reachability (`f(x_neg) < -margin` and `f(x_pos) > +margin`):
       - Catches non-negative quadratic/norm surrogates (e.g. `(d1 - d2)^2 >= 0` or `|x| >= 0`)
         that are mathematically incapable of representing negative (favorable/exothermic/anti-correlated) regimes.
    2. Multi-Source Delta-Method Variance Propagation (`Var_total = Var_obs + grad(g)^T Sigma_ref grad(g) > Var_obs`):
       - Verifies that uncertainty propagation for excess quantities `z = g(theta_ref) - y_obs` incorporates
         reference baseline covariance via the Jacobian `grad(g)` rather than underestimating error bars with 1-source `Var_obs`.
    """
    val_neg = _finite_float(_finite_call(signed_metric_fn, negative_regime_input))
    val_pos = _finite_float(_finite_call(signed_metric_fn, positive_regime_input))
    violations: List[str] = []

    if not (val_neg < -min_sign_margin):
        violations.append(
            f"Bipolar negative-regime unreachability: f(x_neg) = {val_neg:.6e} >= -{min_sign_margin:.2e} (non-negative surrogate trap)"
        )
    if not (val_pos > min_sign_margin):
        violations.append(
            f"Bipolar positive-regime unreachability: f(x_pos) = {val_pos:.6e} <= +{min_sign_margin:.2e}"
        )

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
        expected_var = _finite_float(sample_obs_var) + _finite_float(np.sum((grad ** 2) * v_ref))
        reported_var = _finite_float(_finite_call(variance_propagator_fn, _finite_float(sample_obs_var), sample_baseline_means, sample_baseline_vars))
        var_err = abs(reported_var - expected_var)
        if reported_var <= _finite_float(sample_obs_var) + 1e-12 and np.any(v_ref > 0):
            violations.append(
                f"Single-source variance underestimation: reported_var ({reported_var:.6f}) <= obs_var ({sample_obs_var:.6f}), omitting baseline uncertainty!"
            )
        if var_err > var_tol:
            violations.append(
                f"Delta-method multi-source variance mismatch: |reported ({reported_var:.6f}) - expected ({expected_var:.6f})| = {var_err:.3e} > {var_tol:.2e}"
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
    Kish-Invariance & Window-Debiasing Conservation Gate (`G5s`):
    1. Mixed-Degree Coordinate-Scaling Homogeneity: Under uniform rescaling `x -> lam * x` (`lam > 0`)
       of the primary observable `scaled_arg_name`, each output component `j` must scale as `lam ** d_j`
       (e.g., first moment and standard deviation scale with degree `1.0`, while relative fluctuation /
       coefficient of variation / paracrystallinity `g = sigma / mu` scales with degree `0.0`).
    2. Zero-Weight Outlier Padding Invariance (Kish Effective Sample Size `N_eff` Exactness):
       Appending extreme outlier observations with zero kernel weight (`w_outlier = 0`) in
       `zero_weight_padded_kwargs` must leave the entire output vector strictly invariant
       (`||f(padded) - f(base)||_inf <= tol`), proving both continuous kernel outlier suppression
       and exact Kish `N_eff = 1 / sum(w_norm^2)` Bessel correction (catching naive `N / (N - 1)` bias).
    3. Window-Debiasing Ratio Identity: Verifies `out[i_raw] > 0` and
       `|out[i_raw] / out[i_deb] - expected_debias_ratio| <= tol`, preventing double-division by `sqrt(2*pi)`.
    """
    violations: List[str] = []
    out_base = _extract_array(_finite_call(dispersion_fn, **base_input_kwargs)).reshape(-1)
    max_scale_err = 0.0

    for lam in scale_factors:
        kw_lam = dict(base_input_kwargs)
        kw_lam[scaled_arg_name] = _finite_array(base_input_kwargs[scaled_arg_name], dtype=np.float64) * _finite_float(lam)
        out_lam = _extract_array(_finite_call(dispersion_fn, **kw_lam)).reshape(-1)
        for j, deg in enumerate(output_homogeneity_degrees):
            expected_j = (_finite_float(lam) ** _finite_float(deg)) * _finite_float(out_base[j])
            err_j = abs(_finite_float(out_lam[j]) - expected_j)
            if err_j > max_scale_err:
                max_scale_err = err_j
    if max_scale_err > tol:
        violations.append(
            f"Mixed-degree coordinate-scaling homogeneity violation on `{scaled_arg_name}`: "
            f"max |f_j(lam*x) - lam^d_j f_j(x)| = {max_scale_err:.4e} > {tol:.2e}"
        )

    zero_weight_pad_err = 0.0
    if zero_weight_padded_kwargs is not None:
        out_pad = _extract_array(_finite_call(dispersion_fn, **zero_weight_padded_kwargs)).reshape(-1)
        zero_weight_pad_err = _finite_float(np.max(np.abs(out_pad - out_base)))
        if zero_weight_pad_err > tol:
            violations.append(
                f"Zero-weight outlier padding / Kish N_eff invariance violation: "
                f"max |f(padded) - f(base)| = {zero_weight_pad_err:.4e} > {tol:.2e} "
                f"(naive N/(N-1) Bessel correction or missing kernel gating)"
            )

    debias_ratio_err = 0.0
    if raw_to_debiased_indices is not None:
        i_raw, i_deb = raw_to_debiased_indices
        v_raw, v_deb = _finite_float(out_base[i_raw]), _finite_float(out_base[i_deb])
        if v_raw <= 0.0 or v_deb <= 0.0:
            violations.append(f"Degenerate non-positive dispersion in base sample: raw={v_raw}, debiased={v_deb}")
        else:
            debias_ratio_err = abs((v_raw / v_deb) - _finite_float(expected_debias_ratio))
            if debias_ratio_err > tol:
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
    Domain-Agnostic Out-of-Sample LOOCV Generalization & Train/Eval Feature-Pipeline Parity Gate (`G7h`):
    1. Computes exact Leave-One-Out Cross-Validation (LOOCV) R^2 via hat-matrix leverage
       `e_i^{(-i)} = (y_i - y_hat_i) / (1 - h_ii)` and blocks small-sample memorization where
       in-sample R^2 is high but `loocv_r2 < min_loocv_r2` or `in_sample_r2 - loocv_r2 > max_generalization_gap`.
    2. Verifies zero Train/Eval Skew (`||calibrate_feature_fn(x) - eval_feature_fn(x)||_inf <= tol`)
       so calibration cutoffs/kernels never diverge from evaluation cutoffs/kernels.
    """
    x_mat = _finite_array(design_matrix, dtype=np.float64)
    y_vec = _finite_array(targets, dtype=np.float64).reshape(-1)
    violations: List[str] = []

    beta, _, _, _ = np.linalg.lstsq(x_mat, y_vec, rcond=None)
    y_pred = x_mat @ beta
    ss_tot = _finite_float(np.sum((y_vec - np.mean(y_vec)) ** 2)) + 1e-15
    in_sample_r2 = 1.0 - _finite_float(np.sum((y_vec - y_pred) ** 2)) / ss_tot

    u_mat, s_vals, _ = np.linalg.svd(x_mat, full_matrices=False)
    pos_mask = s_vals > 1e-12
    u_eff = u_mat[:, pos_mask]
    h_diag = np.sum(u_eff ** 2, axis=1)
    denom = np.maximum(1.0 - h_diag, 1e-6)
    loo_resid = (y_vec - y_pred) / denom
    loocv_r2 = 1.0 - _finite_float(np.sum(loo_resid ** 2)) / ss_tot
    gen_gap = in_sample_r2 - loocv_r2

    if loocv_r2 < min_loocv_r2:
        violations.append(f"LOOCV R^2 = {loocv_r2:.4f} < min_loocv_r2 {min_loocv_r2:.4f}")
    if gen_gap > max_generalization_gap:
        violations.append(f"Generalization gap (R^2_train - R^2_LOOCV) = {gen_gap:.4f} > {max_generalization_gap:.4f}")

    max_skew = 0.0
    if calibrate_feature_fn is not None and eval_feature_fn is not None and parity_test_inputs:
        for inp in parity_test_inputs:
            f_cal = _extract_array(_finite_call(calibrate_feature_fn, inp))
            f_evl = _extract_array(_finite_call(eval_feature_fn, inp))
            skew = _finite_float(np.max(np.abs(f_cal - f_evl)))
            if skew > max_skew:
                max_skew = skew
        if max_skew > tol:
            violations.append(f"Train/Eval feature-pipeline skew: max ||f_cal(x) - f_eval(x)||_inf = {max_skew:.4e} > {tol:.3e}")

    return {
        "status": "PASS" if not violations else "FAIL",
        "in_sample_r2": round(in_sample_r2, 6),
        "loocv_r2": round(loocv_r2, 6),
        "generalization_gap": round(gen_gap, 6),
        "max_train_eval_skew": round(max_skew, 12),
        "violations": violations,
    }
