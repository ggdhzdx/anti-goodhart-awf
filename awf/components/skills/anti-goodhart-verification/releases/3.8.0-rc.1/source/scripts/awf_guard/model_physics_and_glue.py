"""AWF Guard: model-physics sensitivity, periodic-unit gauge, feature variance & cross-table bounds."""
from __future__ import annotations

import math
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple
import numpy as np
from awf_guard_numeric_contracts import (
    finite_array as _finite_array,
    finite_call as _finite_call,
    finite_float as _finite_float,
    finite_inputs as _finite_inputs,
)

_DEFAULT_MIN_CV_FLOOR = 0.005
_DEFAULT_MIN_STD_FLOOR = 1e-6
_DEFAULT_MAX_ABS_CORR = 0.98
_MEAN_CV_ACTIVE_FLOOR = 1e-4
_EPS_DENOM = 1e-12
_MAX_ALLOWED_TOLERANCE = 1e-2
_DEFAULT_GAUGE_TOL = 1e-3
_DEFAULT_ASYMPTOTIC_TOL = 5e-3
_DEFAULT_SPIN_MIN_DELTA = 1e-3
_DEFAULT_BOUND_SLACK_MAX = 1e-2
_MONOTONE_SLACK = 1e-9
_MIN_SAMPLE_ROWS = 3
_COORD_DIM = 3
_MIN_CHAIN_LENGTHS = 3
_RIGHT_ANGLE_DEG = 90.0
_HALF_TURN_DEG = 180.0
_DEFAULT_SPIN_ANGLES_DEG: Tuple[float, ...] = (_RIGHT_ANGLE_DEG, _HALF_TURN_DEG)
_DEFAULT_SLIP_FRACTIONS: Tuple[float, ...] = (0.25, 0.5)
_SE3_AXIS = (0.36, 0.48, 0.80)
_SE3_ANGLE_RAD = 0.7
_SE3_SHIFT = (1.75, -2.25, 0.5)
_DEG_HALF_CIRCLE = 180.0


def _rodrigues_matrix(axis: np.ndarray, angle_rad: float) -> np.ndarray:
    u = np.asarray(axis, dtype=np.float64)
    norm_u = float(np.linalg.norm(u))
    if norm_u <= _EPS_DENOM:
        raise ValueError("Rotation axis must be non-zero")
    k_vec = u / norm_u
    kx, ky, kz = float(k_vec[0]), float(k_vec[1]), float(k_vec[2])
    skew = np.array([[0.0, -kz, ky], [kz, 0.0, -kx], [-ky, kx, 0.0]], dtype=np.float64)
    eye = np.eye(_COORD_DIM, dtype=np.float64)
    return eye + math.sin(angle_rad) * skew + (1.0 - math.cos(angle_rad)) * (skew @ skew)


def _orthogonal_pair(vec: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    unit = vec / float(np.linalg.norm(vec))
    basis = np.eye(_COORD_DIM, dtype=np.float64)
    trial = basis[0] if abs(float(unit[0])) < 0.5 else basis[1]
    u1 = np.cross(unit, trial)
    u1 = u1 / float(np.linalg.norm(u1))
    u2 = np.cross(unit, u1)
    u2 = u2 / float(np.linalg.norm(u2))
    return u1, u2


@_finite_inputs
def verify_dynamic_feature_variance_and_noncollinearity(
    feature_matrix: Any,
    feature_names: Sequence[str],
    min_cv_floor: float = _DEFAULT_MIN_CV_FLOOR,
    min_std_floor: float = _DEFAULT_MIN_STD_FLOOR,
    max_abs_corr: float = _DEFAULT_MAX_ABS_CORR,
) -> Dict[str, Any]:
    """
    Gate G4d: Catch frozen/collapsed trajectory columns (std < floor or CV < floor on non-zero-mean inputs)
    and near-collinear duplicate feature columns across an evaluated sample matrix `(N_samples, N_features)`.
    """
    arr = _finite_array(feature_matrix, dtype=np.float64)
    if arr.ndim != 2 or arr.shape[0] < _MIN_SAMPLE_ROWS or arr.shape[1] < 1:
        raise ValueError("feature_matrix must be a 2D array with >= 3 samples and >= 1 feature")
    names = list(feature_names)
    if len(names) != arr.shape[1] or not all(isinstance(n, str) and n for n in names):
        raise ValueError("feature_names must match feature_matrix columns with non-empty strings")
    cv_floor = _finite_float(min_cv_floor)
    std_floor = _finite_float(min_std_floor)
    corr_ceil = _finite_float(max_abs_corr)
    if cv_floor <= 0.0 or cv_floor > _MAX_ALLOWED_TOLERANCE * 10.0 or std_floor <= 0.0 or not (0.0 < corr_ceil < 1.0):
        raise ValueError("Variance floors must be positive and max_abs_corr in (0, 1)")

    n_samples, n_features = int(arr.shape[0]), int(arr.shape[1])
    means = np.mean(arr, axis=0)
    stds = np.std(arr, axis=0, ddof=1)
    frozen_features: List[Dict[str, Any]] = []
    cv_values: List[float] = []
    for idx, fname in enumerate(names):
        mu = float(means[idx])
        sd = float(stds[idx])
        abs_mu = abs(mu)
        cv = sd / abs_mu if abs_mu >= _MEAN_CV_ACTIVE_FLOOR else sd
        cv_values.append(float(cv))
        if sd < std_floor or (abs_mu >= _MEAN_CV_ACTIVE_FLOOR and cv < cv_floor):
            frozen_features.append({"feature": fname, "mean": mu, "std": sd, "cv": float(cv)})

    collinear_pairs: List[Dict[str, Any]] = []
    max_pair_corr = 0.0
    for i in range(n_features):
        if stds[i] <= _EPS_DENOM:
            continue
        xi = (arr[:, i] - means[i]) / float(stds[i])
        for j in range(i + 1, n_features):
            if stds[j] <= _EPS_DENOM:
                continue
            xj = (arr[:, j] - means[j]) / float(stds[j])
            corr = abs(float(np.dot(xi, xj) / float(n_samples - 1)))
            if corr > max_pair_corr:
                max_pair_corr = corr
            if corr > corr_ceil:
                collinear_pairs.append({"left": names[i], "right": names[j], "abs_corr": float(corr)})

    violations: List[str] = []
    if frozen_features:
        bad_cols = ", ".join(item["feature"] for item in frozen_features)
        violations.append(f"frozen/collapsed dynamic feature column(s): {bad_cols}")
    if collinear_pairs:
        bad_pairs = ", ".join(f"{p['left']}~{p['right']}" for p in collinear_pairs)
        violations.append(f"collinear/redundant dynamic feature pair(s): {bad_pairs}")
    return {
        "status": "FAIL" if violations else "PASS",
        "evaluated_sample_count": n_samples,
        "evaluated_feature_count": n_features,
        "min_observed_cv": float(min(cv_values)),
        "max_pairwise_abs_corr": float(max_pair_corr),
        "min_cv_floor": float(cv_floor),
        "max_abs_corr": float(corr_ceil),
        "frozen_features": frozen_features,
        "collinear_pairs": collinear_pairs,
        "violations": violations,
    }


@_finite_inputs
def verify_subfragment_spin_and_siteslip_sensitivity(
    pair_energy_fn: Callable[[np.ndarray, np.ndarray], float],
    frag_a_coords: Any,
    frag_b_coords: Any,
    spin_angles_deg: Sequence[float] = _DEFAULT_SPIN_ANGLES_DEG,
    slip_fractions: Sequence[float] = _DEFAULT_SLIP_FRACTIONS,
    global_se3_tol: float = _DEFAULT_GAUGE_TOL,
    min_spin_delta: float = _DEFAULT_SPIN_MIN_DELTA,
    min_slip_delta: float = _DEFAULT_SPIN_MIN_DELTA,
) -> Dict[str, Any]:
    """
    Gate G3m: Verify pair operator preserves global SE(3) invariance while breaking invariance under
    fixed-centroid sub-fragment rigid spin AND constant-centroid-distance tangential site slip.
    Catches zeroed intra-pair multipoles and center-of-mass-distance-only shortcuts.
    """
    coords_a = _finite_array(frag_a_coords, dtype=np.float64)
    coords_b = _finite_array(frag_b_coords, dtype=np.float64)
    if coords_a.ndim != 2 or coords_b.ndim != 2 or coords_a.shape[1] != _COORD_DIM or coords_b.shape[1] != _COORD_DIM:
        raise ValueError("frag_a_coords and frag_b_coords must be (N, 3) arrays")
    if coords_a.shape[0] < 2 or coords_b.shape[0] < 2:
        raise ValueError("Sub-fragments must have at least 2 atoms each")
    tol = _finite_float(global_se3_tol)
    spin_floor = _finite_float(min_spin_delta)
    slip_floor = _finite_float(min_slip_delta)
    if tol <= 0.0 or tol > _MAX_ALLOWED_TOLERANCE or spin_floor <= 0.0 or slip_floor <= 0.0:
        raise ValueError("Tolerances and sensitivity floors must be positive and bounded")

    ca = np.mean(coords_a, axis=0)
    cb = np.mean(coords_b, axis=0)
    sep_vec = cb - ca
    sep_norm = float(np.linalg.norm(sep_vec))
    if sep_norm <= _EPS_DENOM:
        raise ValueError("Sub-fragment centroids must be non-coincident")

    e0 = _finite_float(_finite_call(pair_energy_fn, coords_a, coords_b))
    rot_global = _rodrigues_matrix(np.array(_SE3_AXIS, dtype=np.float64), _SE3_ANGLE_RAD)
    shift_global = np.array(_SE3_SHIFT, dtype=np.float64)
    e_se3 = _finite_float(_finite_call(pair_energy_fn, coords_a @ rot_global.T + shift_global, coords_b @ rot_global.T + shift_global))
    se3_err = abs(e_se3 - e0)
    probes = 1

    u1, u2 = _orthogonal_pair(sep_vec)
    b_rel = coords_b - cb
    max_spin_delta = 0.0
    for deg in spin_angles_deg:
        rad = _finite_float(deg) * math.pi / _DEG_HALF_CIRCLE
        for axis in (u1, u2):
            rot_spin = _rodrigues_matrix(axis, rad)
            e_spin = _finite_float(_finite_call(pair_energy_fn, coords_a, cb + b_rel @ rot_spin.T))
            probes += 1
            max_spin_delta = max(max_spin_delta, abs(e_spin - e0))

    max_slip_delta = 0.0
    for frac in slip_fractions:
        step = _finite_float(frac) * sep_norm
        for axis in (u1, u2):
            new_dir = sep_vec + step * axis
            cb_slip = ca + sep_norm * (new_dir / float(np.linalg.norm(new_dir)))
            e_slip = _finite_float(_finite_call(pair_energy_fn, coords_a, b_rel + cb_slip))
            probes += 1
            max_slip_delta = max(max_slip_delta, abs(e_slip - e0))

    violations: List[str] = []
    if se3_err > tol:
        violations.append(f"global SE(3) invariance violated: |dE|={se3_err:.3e} > tol={tol:.3e}")
    if max_spin_delta < spin_floor:
        violations.append(f"sub-fragment rigid spin blindness: max|dE|={max_spin_delta:.3e} < floor={spin_floor:.3e}")
    if max_slip_delta < slip_floor:
        violations.append(f"constant-centroid-distance site-slip blindness: max|dE|={max_slip_delta:.3e} < floor={slip_floor:.3e}")
    return {
        "status": "FAIL" if violations else "PASS",
        "global_se3_err": float(se3_err),
        "max_spin_delta": float(max_spin_delta),
        "max_slip_delta": float(max_slip_delta),
        "executed_probe_count": probes,
        "probe_tolerance": float(tol),
        "violations": violations,
    }


@_finite_inputs
def verify_unitcell_cyclic_shift_and_chain_convergence(
    window_observable_fn: Callable[[Any], Any],
    cyclic_unit_windows: Sequence[Any],
    reversed_unit_windows: Sequence[Any],
    chain_sizes: Sequence[float],
    chain_observables: Sequence[Any],
    gauge_tol: float = _DEFAULT_GAUGE_TOL,
    asymptotic_tol: float = _DEFAULT_ASYMPTOTIC_TOL,
) -> Dict[str, Any]:
    """
    Gate G1f: Verify 1D/periodic unit-cell representation invariance across cyclic window shifts
    and head-tail reversals, alongside monotonic asymptotic contraction across growing chain lengths.
    """
    if len(cyclic_unit_windows) < 2 or len(reversed_unit_windows) < 1:
        raise ValueError("Need >= 2 cyclic_unit_windows and >= 1 reversed_unit_windows")
    sizes = [_finite_float(s) for s in chain_sizes]
    if len(sizes) < _MIN_CHAIN_LENGTHS or len(chain_observables) != len(sizes):
        raise ValueError("chain_sizes and chain_observables must align with >= 3 increasing sizes")
    if any(sizes[k] <= 0.0 or (k > 0 and sizes[k] <= sizes[k - 1]) for k in range(len(sizes))):
        raise ValueError("chain_sizes must be strictly increasing positive values")
    g_tol = _finite_float(gauge_tol)
    a_tol = _finite_float(asymptotic_tol)
    if g_tol <= 0.0 or g_tol > _MAX_ALLOWED_TOLERANCE or a_tol <= 0.0 or a_tol > _MAX_ALLOWED_TOLERANCE:
        raise ValueError("gauge_tol and asymptotic_tol must be in (0, 1e-2]")

    ref_val = _finite_array(_finite_call(window_observable_fn, cyclic_unit_windows[0]), dtype=np.float64).ravel()
    cyclic_err = 0.0
    for win in cyclic_unit_windows[1:]:
        cur = _finite_array(_finite_call(window_observable_fn, win), dtype=np.float64).ravel()
        cyclic_err = max(cyclic_err, float(np.linalg.norm(cur - ref_val, ord=np.inf)))
    rev_err = 0.0
    for win in reversed_unit_windows:
        cur = _finite_array(_finite_call(window_observable_fn, win), dtype=np.float64).ravel()
        rev_err = max(rev_err, float(np.linalg.norm(cur - ref_val, ord=np.inf)))

    chain_vecs = [_finite_array(val, dtype=np.float64).ravel() for val in chain_observables]
    step_deltas = [
        float(np.linalg.norm(chain_vecs[idx + 1] - chain_vecs[idx], ord=np.inf))
        for idx in range(len(chain_vecs) - 1)
    ]
    non_monotone = any(step_deltas[idx + 1] > step_deltas[idx] + _MONOTONE_SLACK for idx in range(len(step_deltas) - 1))

    violations: List[str] = []
    if cyclic_err > g_tol:
        violations.append(f"cyclic unit-cell shift gauge drift: err={cyclic_err:.3e} > tol={g_tol:.3e}")
    if rev_err > g_tol:
        violations.append(f"chain head-tail reversal asymmetry: err={rev_err:.3e} > tol={g_tol:.3e}")
    if non_monotone or step_deltas[-1] > a_tol:
        violations.append(
            f"non-convergent oligomer/unit-cell size truncation: deltas={step_deltas}, tol={a_tol:.3e}"
        )
    return {
        "status": "FAIL" if violations else "PASS",
        "cyclic_shift_max_err": float(cyclic_err),
        "reversal_max_err": float(rev_err),
        "chain_step_deltas": step_deltas,
        "final_chain_delta": float(step_deltas[-1]),
        "gauge_tolerance": float(g_tol),
        "asymptotic_tolerance": float(a_tol),
        "executed_window_count": len(cyclic_unit_windows) + len(reversed_unit_windows),
        "violations": violations,
    }


@_finite_inputs
def verify_crosstable_physical_inequality_bounds(
    observables: Dict[str, Any],
    inequality_specs: Sequence[Dict[str, Any]],
    max_allowed_slack: float = _DEFAULT_BOUND_SLACK_MAX,
) -> Dict[str, Any]:
    """
    Gate G5u: Enforce explicit cross-table physical and thermodynamic inequality bounds
    (e.g. detailed-balance free-energy vs Voc ceilings) across upstream/downstream tables.
    """
    if not isinstance(observables, dict) or not observables:
        raise ValueError("observables must be a non-empty dict")
    specs = list(inequality_specs)
    if not specs:
        raise ValueError("inequality_specs must contain at least one bound")
    slack_cap = _finite_float(max_allowed_slack)
    if slack_cap < 0.0 or slack_cap > _MAX_ALLOWED_TOLERANCE:
        raise ValueError("max_allowed_slack must be in [0, 1e-2]")
    clean_obs = {str(k): _finite_float(v) for k, v in observables.items()}

    violations: List[str] = []
    margins: Dict[str, float] = {}
    min_margin: Optional[float] = None
    for spec in specs:
        if not isinstance(spec, dict) or not isinstance(spec.get("bound_id"), str) or not spec["bound_id"]:
            raise ValueError("Each inequality spec requires a non-empty bound_id")
        bid = spec["bound_id"]
        rel = spec.get("relation")
        if rel not in (">=", "<="):
            raise ValueError(f"Bound `{bid}` relation must be `>=` or `<=`")
        slack = _finite_float(spec["slack_tol"]) if "slack_tol" in spec else 0.0
        if slack < 0.0 or slack > slack_cap:
            violations.append(f"loose tolerance inflation in bound `{bid}`: slack={slack:.3e} > cap={slack_cap:.3e}")
            continue
        lhs_terms = spec.get("lhs_terms")
        rhs_terms = spec.get("rhs_terms")
        if not isinstance(lhs_terms, dict) or not lhs_terms or not isinstance(rhs_terms, dict) or not rhs_terms:
            raise ValueError(f"Bound `{bid}` requires non-empty lhs_terms and rhs_terms")
        missing = [k for k in (*lhs_terms.keys(), *rhs_terms.keys()) if k not in clean_obs]
        if missing:
            violations.append(f"missing observable key(s) in bound `{bid}`: {sorted(missing)}")
            continue
        lhs_val = sum(_finite_float(coef) * clean_obs[key] for key, coef in lhs_terms.items())
        rhs_val = sum(_finite_float(coef) * clean_obs[key] for key, coef in rhs_terms.items())
        signed_margin = (lhs_val - rhs_val + slack) if rel == ">=" else (rhs_val - lhs_val + slack)
        margins[bid] = float(signed_margin)
        if min_margin is None or signed_margin < min_margin:
            min_margin = float(signed_margin)
        if signed_margin < 0.0:
            violations.append(
                f"physical/thermodynamic inequality violated `{bid}`: lhs={lhs_val:.6f} {rel} rhs={rhs_val:.6f} (slack={slack:.3e})"
            )

    if min_margin is None:
        min_margin = -1.0
    return {
        "status": "FAIL" if violations else "PASS",
        "checked_bound_count": len(specs),
        "max_allowed_slack": float(slack_cap),
        "min_signed_margin": float(min_margin),
        "bound_margins": margins,
        "violations": violations,
    }
