"""AWF Guard: Python-FLINT Arb certified ball-arithmetic enclosure & Hypothesis Lie-group shrinking gates."""
from __future__ import annotations

import math
from typing import Any, Callable, Dict, List, Literal, Optional, Sequence, Tuple
import flint
from hypothesis import example, given, settings, strategies as st
import numpy as np

from awf_guard_numeric_contracts import finite_array as _finite_array
from awf_guard_numeric_contracts import finite_call as _finite_call
from awf_guard_numeric_contracts import finite_float as _finite_float
from awf_guard_numeric_contracts import finite_inputs as _finite_inputs
from .numeric_inputs import _extract_array

_MIN_ARB_PREC_BITS = 64
_MAX_ARB_PREC_BITS = 1024
_MAX_BALL_RADIUS_CEILING = 1e-4
_MAX_F64_ORACLE_TOL = 1e-3
_RAD_DENOM_FLOOR = 1e-30
_PERTURB_COORD_DELTA = 0.35
_HYP_TRANSLATION_BOUND = 5.0
_HYP_MIN_EXAMPLES = 8
_AXIS_NORM_FLOOR = 1e-12


def _arb_linear_solve_enclosure(a_arr: np.ndarray, b_arr: np.ndarray) -> List[Any]:
    if a_arr.ndim != 2 or a_arr.shape[0] != a_arr.shape[1] or a_arr.shape[0] < 1:
        raise ValueError(f"Expected non-empty square matrix for Arb solve, got {a_arr.shape}")
    n_dim = a_arr.shape[0]
    b_vec = b_arr.reshape(n_dim, 1)
    a_rows = [[flint.arb(float(a_arr[i, j])) for j in range(n_dim)] for i in range(n_dim)]
    b_rows = [[flint.arb(float(b_vec[i, 0]))] for i in range(n_dim)]
    x_mat = flint.arb_mat(a_rows).solve(flint.arb_mat(b_rows))
    return [x_mat[i, 0] for i in range(n_dim)]


def _arb_boltzmann_free_energy_enclosure(energies: np.ndarray, beta: float) -> List[Any]:
    e_flat = energies.reshape(-1)
    if e_flat.size < 1 or beta <= 0.0:
        raise ValueError("Boltzmann enclosure requires non-empty energies and beta > 0")
    beta_arb = flint.arb(beta)
    e_min = flint.arb(float(np.min(e_flat)))
    shifted_sum = flint.arb(0.0)
    for val in e_flat:
        shifted_sum = shifted_sum + (-beta_arb * (flint.arb(float(val)) - e_min)).exp()
    free_energy = e_min - shifted_sum.log() / beta_arb
    probs = [((-beta_arb * (flint.arb(float(val)) - e_min)).exp()) / shifted_sum for val in e_flat]
    return [free_energy, *probs]


@_finite_inputs
def verify_arb_ball_enclosure_and_conditioning(
    target_fn: Callable[..., Any],
    sample_input_kwargs: Dict[str, Any],
    arb_mode: Literal["linear_solve", "logsumexp_boltzmann"] = "linear_solve",
    matrix_arg: str = "a_mat",
    rhs_arg: str = "b_vec",
    energies_arg: str = "energies",
    beta_arg: str = "beta",
    precision_bits: int = 128,
    max_ball_rel_radius: float = 1e-12,
    float64_tol: float = 1e-7,
    require_certified_sign: bool = True,
) -> Dict[str, Any]:
    """
    Certified Midpoint-Radius Ball Arithmetic Enclosure & Conditioning Gate (`G1g`) powered by `python-flint` (Arb).
    Verifies both bounded rigorous rounding-error ball radii and `float64` operator accuracy against the Arb ball.
    """
    prec = int(precision_bits)
    max_rad_f = _finite_float(max_ball_rel_radius)
    tol_f = _finite_float(float64_tol)
    if not (_MIN_ARB_PREC_BITS <= prec <= _MAX_ARB_PREC_BITS):
        raise ValueError(f"G1g precision_bits must be in [{_MIN_ARB_PREC_BITS}, {_MAX_ARB_PREC_BITS}], got {prec}")
    if not (0.0 < max_rad_f <= _MAX_BALL_RADIUS_CEILING) or not (0.0 < tol_f <= _MAX_F64_ORACLE_TOL):
        raise ValueError(f"G1g tolerances exceed hard bounds: max_ball_rel_radius={max_rad_f}, float64_tol={tol_f}")

    violations: List[str] = []
    prev_prec = flint.ctx.prec
    flint.ctx.prec = prec
    try:
        if arb_mode == "linear_solve":
            a_arr = _finite_array(sample_input_kwargs[matrix_arg], dtype=np.float64)
            b_arr = _finite_array(sample_input_kwargs[rhs_arg], dtype=np.float64)
            balls = _arb_linear_solve_enclosure(a_arr, b_arr)
        elif arb_mode == "logsumexp_boltzmann":
            e_arr = _finite_array(sample_input_kwargs[energies_arg], dtype=np.float64)
            beta_val = _finite_float(sample_input_kwargs[beta_arg])
            balls = _arb_boltzmann_free_energy_enclosure(e_arr, beta_val)
        else:
            raise ValueError(f"Unsupported arb_mode: {arb_mode!r}")

        mids: List[float] = []
        rads: List[float] = []
        sign_ambiguous = 0
        for idx, b_item in enumerate(balls):
            mid_str = b_item.mid().str(20, radius=False)
            rad_str = b_item.rad().str(20, radius=False)
            mid_f = float(mid_str)
            rad_f = float(rad_str)
            if not (math.isfinite(mid_f) and math.isfinite(rad_f)):
                violations.append(f"Arb enclosure component #{idx} is non-finite (singular/indeterminate ball).")
                mid_f, rad_f = 0.0, float("inf")
            mids.append(mid_f)
            rads.append(rad_f)
            if require_certified_sign and abs(mid_f) > tol_f and bool(b_item.contains(0)):
                sign_ambiguous += 1
    except ZeroDivisionError as exc:
        violations.append(f"Arb ball arithmetic detected exact or numerical singularity: {exc}")
        mids, rads, sign_ambiguous = [], [], 0
    finally:
        flint.ctx.prec = prev_prec

    out_f64 = _extract_array(_finite_call(target_fn, **sample_input_kwargs)).reshape(-1)
    max_rel_rad = 0.0
    max_f64_err = 0.0
    if mids and len(out_f64) != len(mids):
        violations.append(f"Output shape mismatch: target_fn returned {len(out_f64)} scalars, Arb oracle has {len(mids)}")
    elif mids:
        for idx, (m_val, r_val) in enumerate(zip(mids, rads)):
            if not math.isfinite(r_val):
                max_rel_rad = _MAX_BALL_RADIUS_CEILING * 10.0
                continue
            rel_r = r_val / max(abs(m_val), _RAD_DENOM_FLOOR)
            if rel_r > max_rel_rad:
                max_rel_rad = rel_r
            dist_outside_ball = max(0.0, abs(_finite_float(out_f64[idx]) - m_val) - r_val)
            if dist_outside_ball > max_f64_err:
                max_f64_err = dist_outside_ball

        if max_rel_rad > max_rad_f:
            violations.append(
                f"Arb certified ball relative radius {max_rel_rad:.3e} exceeds ceiling {max_rad_f:.3e} "
                f"at {prec}-bit precision (severe ill-conditioning)."
            )
        if sign_ambiguous > 0:
            violations.append(f"Arb ball straddles zero on {sign_ambiguous} non-trivial component(s); sign uncertified.")
        if max_f64_err > tol_f:
            violations.append(
                f"Float64 output deviates from certified Arb ball enclosure by {max_f64_err:.3e} > {tol_f:.3e}."
            )

    safe_rel_rad = round(max_rel_rad, 16) if math.isfinite(max_rel_rad) else 1.0
    return {
        "status": "PASS" if not violations else "FAIL",
        "arb_mode": arb_mode,
        "precision_bits": prec,
        "component_count": len(mids),
        "max_ball_rel_radius": safe_rel_rad,
        "max_float64_enclosure_err": round(max_f64_err, 14),
        "float64_tolerance": tol_f,
        "sign_ambiguous_count": sign_ambiguous,
        "violations": violations,
    }


def _rodrigues_rotation_matrix(axis_raw: Sequence[float], angle_rad: float) -> np.ndarray:
    ax = np.asarray(axis_raw, dtype=np.float64)
    norm = float(np.linalg.norm(ax))
    u_vec = np.array([1.0, 0.0, 0.0], dtype=np.float64) if norm < _AXIS_NORM_FLOOR else (ax / norm)
    ux, uy, uz = float(u_vec[0]), float(u_vec[1]), float(u_vec[2])
    k_mat = np.array([[0.0, -uz, uy], [uz, 0.0, -ux], [-uy, ux, 0.0]], dtype=np.float64)
    c_val = math.cos(angle_rad)
    s_val = math.sin(angle_rad)
    return np.eye(3, dtype=np.float64) + s_val * k_mat + (1.0 - c_val) * (k_mat @ k_mat)


@_finite_inputs
def verify_hypothesis_lie_group_and_boundary_shrinking(
    target_fn: Callable[..., Any],
    base_coords: np.ndarray,
    coord_kwarg: str = "coords",
    extra_kwargs: Optional[Dict[str, Any]] = None,
    output_tensor_rank: Literal[0, 1] = 0,
    max_examples: int = 24,
    tol: float = 1e-6,
) -> Dict[str, Any]:
    """
    Deterministic Property-Based Lie-Group (`SE(3) x S_N`) & Singular-Angle (`0, pi/2, pi`)
    Shrinking Gate (`G3n`) powered by `hypothesis`.
    """
    tol_f = _finite_float(tol)
    n_ex = int(max_examples)
    if not (0.0 < tol_f <= _MAX_F64_ORACLE_TOL) or n_ex < _HYP_MIN_EXAMPLES:
        raise ValueError(f"G3n requires tol in (0, {_MAX_F64_ORACLE_TOL}] and max_examples >= {_HYP_MIN_EXAMPLES}")
    pos = _finite_array(base_coords, dtype=np.float64)
    if pos.ndim != 2 or pos.shape[1] != 3 or pos.shape[0] < 2:
        raise ValueError(f"G3n base_coords must have shape (N >= 2, 3), got {pos.shape}")

    n_atoms = pos.shape[0]
    kw_base = dict(extra_kwargs) if extra_kwargs is not None else {}
    kw_base[coord_kwarg] = pos.copy()
    base_out = _extract_array(_finite_call(target_fn, **kw_base))

    pos_pert = pos.copy()
    pos_pert[0, 0] += _PERTURB_COORD_DELTA
    kw_pert = dict(kw_base)
    kw_pert[coord_kwarg] = pos_pert
    pert_out = _extract_array(_finite_call(target_fn, **kw_pert))
    pert_signal = _finite_float(np.max(np.abs(pert_out - base_out)))
    violations: List[str] = []
    if pert_signal <= tol_f:
        violations.append(f"Internal-geometry sensitivity collapse: pert_signal={pert_signal:.3e} <= {tol_f:.3e}")

    executed_counter = {"count": 0, "max_err": 0.0}
    last_failure: Dict[str, Any] = {}
    id_perm = list(range(n_atoms))
    rev_perm = list(reversed(range(n_atoms)))
    half_pi = 0.5 * math.pi

    @settings(derandomize=True, database=None, max_examples=n_ex, deadline=None)
    @example(axis=(1.0, 0.0, 0.0), angle=0.0, trans=(0.0, 0.0, 0.0), perm=id_perm)
    @example(axis=(1.0, 0.0, 0.0), angle=math.pi, trans=(2.5, -1.5, 0.5), perm=rev_perm)
    @example(axis=(0.0, 1.0, 0.0), angle=half_pi, trans=(-2.0, 1.0, 3.0), perm=id_perm)
    @example(axis=(0.0, 0.0, 1.0), angle=-math.pi, trans=(0.0, 0.0, -4.0), perm=rev_perm)
    @given(
        axis=st.tuples(
            st.floats(-1.0, 1.0, allow_nan=False, allow_infinity=False),
            st.floats(-1.0, 1.0, allow_nan=False, allow_infinity=False),
            st.floats(-1.0, 1.0, allow_nan=False, allow_infinity=False),
        ),
        angle=st.floats(-math.pi, math.pi, allow_nan=False, allow_infinity=False),
        trans=st.tuples(
            st.floats(-_HYP_TRANSLATION_BOUND, _HYP_TRANSLATION_BOUND, allow_nan=False, allow_infinity=False),
            st.floats(-_HYP_TRANSLATION_BOUND, _HYP_TRANSLATION_BOUND, allow_nan=False, allow_infinity=False),
            st.floats(-_HYP_TRANSLATION_BOUND, _HYP_TRANSLATION_BOUND, allow_nan=False, allow_infinity=False),
        ),
        perm=st.permutations(range(n_atoms)),
    )
    def _run_property(
        axis: Tuple[float, float, float],
        angle: float,
        trans: Tuple[float, float, float],
        perm: List[int],
    ) -> None:
        executed_counter["count"] += 1
        rot = _rodrigues_rotation_matrix(axis, angle)
        t_vec = np.asarray(trans, dtype=np.float64).reshape(1, 3)
        perm_arr = np.asarray(perm, dtype=int)
        kw_trial = dict(kw_base)
        kw_trial[coord_kwarg] = (pos[perm_arr] @ rot.T) + t_vec
        out_trial = _extract_array(_finite_call(target_fn, **kw_trial))
        expected = (base_out[perm_arr] @ rot.T) if output_tensor_rank == 1 else base_out
        err = _finite_float(np.max(np.abs(out_trial - expected)))
        if err > executed_counter["max_err"]:
            executed_counter["max_err"] = err
        if err > tol_f:
            last_failure["shrunk"] = {
                "angle_rad": round(angle, 8),
                "axis": [round(float(x), 6) for x in axis],
                "translation": [round(float(x), 6) for x in trans],
                "permutation": [int(i) for i in perm],
                "equivariance_err": round(err, 12),
            }
            raise AssertionError(f"SE(3)xS_N equivariance err={err:.3e} > {tol_f:.3e}")

    try:
        _run_property()
    except AssertionError as exc:
        violations.append(f"Hypothesis shrunk Lie-group counterexample: {last_failure.get('shrunk', str(exc))}")

    return {
        "status": "PASS" if not violations else "FAIL",
        "executed_example_count": executed_counter["count"],
        "max_equivariance_err": round(executed_counter["max_err"], 12),
        "perturbation_signal": round(pert_signal, 12),
        "tolerance": tol_f,
        "shrunk_counterexample": last_failure["shrunk"] if "shrunk" in last_failure else None,
        "violations": violations,
    }
