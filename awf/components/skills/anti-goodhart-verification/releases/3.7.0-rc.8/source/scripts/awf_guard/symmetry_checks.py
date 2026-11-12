"""AWF Guard: symmetry checks."""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Literal, Optional, Sequence
import numpy as np

from awf_guard_numeric_contracts import finite_array as _finite_array
from awf_guard_numeric_contracts import finite_call as _finite_call
from awf_guard_numeric_contracts import finite_float as _finite_float
from awf_guard_numeric_contracts import finite_inputs as _finite_inputs
from .numeric_inputs import _extract_array, _kwargs_materially_differ

_MAX_SYMMETRY_TOL = 1e-3
_SIGNAL_PERTURB_STEP = 0.35


def _eval_permuted(
    target_fn: Callable[..., Any],
    kw_base: Dict[str, Any],
    pos: np.ndarray,
    base_out: np.ndarray,
    perm: np.ndarray,
    coord_kwarg: str,
    cell_kwarg: str,
    output_tensor_rank: int,
) -> float:
    n_atoms = pos.shape[0]
    kw_perm = dict(kw_base)
    kw_perm[coord_kwarg] = pos[perm]
    for k, v in list(kw_perm.items()):
        if k not in (coord_kwarg, cell_kwarg) and isinstance(v, np.ndarray) and v.ndim >= 1 and v.shape[0] == n_atoms:
            kw_perm[k] = v[perm]
    out_perm = _extract_array(_finite_call(target_fn, **kw_perm))
    expected_perm = (
        base_out[perm]
        if (output_tensor_rank == 1 or (base_out.ndim >= 1 and base_out.shape[0] == n_atoms))
        else base_out
    )
    return _finite_float(np.max(np.abs(out_perm - expected_perm)))


@_finite_inputs
def verify_se3_pbc_and_permutation_equivariance(
    target_fn: Callable[..., Any],
    coords: np.ndarray,
    cell: Optional[np.ndarray] = None,
    extra_kwargs: Optional[Dict[str, Any]] = None,
    coord_kwarg: str = "coords",
    cell_kwarg: str = "cell",
    output_tensor_rank: Literal[0, 1] = 0,
    tol: float = 1e-7,
    seed: int = 202611,
) -> Dict[str, Any]:
    """
    Verify 3D atomistic/molecular/crystal operator symmetry invariants (`G3i`):
    SE(3) rotation+translation, triclinic PBC lattice shifts, full S_N generators (cyclic + adjacent swap),
    and non-degenerate spatial sensitivity (blocking constant-zero and scale-underflow cheats).
    """
    tol_f = _finite_float(tol)
    if not (0.0 < tol_f <= _MAX_SYMMETRY_TOL):
        raise ValueError(f"G3i tol must be in (0, {_MAX_SYMMETRY_TOL}], got {tol_f}")
    pos = _finite_array(coords, dtype=np.float64)
    if pos.ndim != 2 or pos.shape[1] != 3 or pos.shape[0] < 1:
        raise ValueError(f"coords must have shape (N >= 1, 3), got {pos.shape}")
    n_atoms = pos.shape[0]
    kw_base = dict(extra_kwargs) if extra_kwargs is not None else {}
    kw_base[coord_kwarg] = pos.copy()
    if cell is not None:
        cell_arr = _finite_array(cell, dtype=np.float64)
        kw_base[cell_kwarg] = cell_arr.copy()
    else:
        cell_arr = None

    base_out = _extract_array(_finite_call(target_fn, **kw_base))

    pos_pert = pos.copy()
    pos_pert[0, 0] += _SIGNAL_PERTURB_STEP
    kw_pert = dict(kw_base)
    kw_pert[coord_kwarg] = pos_pert
    pert_out = _extract_array(_finite_call(target_fn, **kw_pert))
    pert_delta = _finite_float(np.max(np.abs(pert_out - base_out))) if n_atoms >= 2 else max(
        _finite_float(np.max(np.abs(pert_out - base_out))), _finite_float(np.max(np.abs(base_out)))
    )
    signal_scale = max(pert_delta, 1e-30)

    rng = np.random.default_rng(seed)
    q_mat, r_mat = np.linalg.qr(rng.normal(size=(3, 3)))
    rot = q_mat @ np.diag(np.sign(np.diag(r_mat)))
    if np.linalg.det(rot) < 0:
        rot[:, 0] = -rot[:, 0]
    trans = rng.uniform(-1.5, 1.5, size=(1, 3))

    kw_rot = dict(kw_base)
    kw_rot[coord_kwarg] = pos @ rot.T + trans
    if cell_arr is not None:
        kw_rot[cell_kwarg] = cell_arr @ rot.T
    out_rot = _extract_array(_finite_call(target_fn, **kw_rot))
    expected_rot = base_out @ rot.T if output_tensor_rank == 1 else base_out
    se3_err = _finite_float(np.max(np.abs(out_rot - expected_rot)))

    pbc_err = 0.0
    if cell_arr is not None and n_atoms >= 1:
        kw_pbc = dict(kw_base)
        pos_pbc = pos.copy()
        pos_pbc[0] = pos_pbc[0] + np.array([1.0, -1.0, 1.0], dtype=np.float64) @ cell_arr
        kw_pbc[coord_kwarg] = pos_pbc
        pbc_err = _finite_float(np.max(np.abs(_extract_array(_finite_call(target_fn, **kw_pbc)) - base_out)))
        if n_atoms >= 2:
            pos_pbc2 = pos.copy()
            pos_pbc2[-1] = pos_pbc2[-1] + np.array([-1.0, 2.0, 0.0], dtype=np.float64) @ cell_arr
            kw_pbc[coord_kwarg] = pos_pbc2
            pbc_err = max(pbc_err, _finite_float(np.max(np.abs(_extract_array(_finite_call(target_fn, **kw_pbc)) - base_out))))

    perm_err = 0.0
    if n_atoms >= 2:
        cyc_perm = np.roll(np.arange(n_atoms), 1)
        swap_perm = np.arange(n_atoms)
        swap_perm[0], swap_perm[1] = 1, 0
        perm_err = max(
            _eval_permuted(target_fn, kw_base, pos, base_out, cyc_perm, coord_kwarg, cell_kwarg, output_tensor_rank),
            _eval_permuted(target_fn, kw_base, pos, base_out, swap_perm, coord_kwarg, cell_kwarg, output_tensor_rank),
        )

    rel_cap = max(tol_f, 1e-5)
    non_trivial = pert_delta > tol_f
    scale_consistent = max(se3_err, pbc_err, perm_err) / signal_scale <= rel_cap
    passed = bool(non_trivial and scale_consistent and se3_err <= tol_f and pbc_err <= tol_f and perm_err <= tol_f)
    return {
        "status": "PASS" if passed else "FAIL",
        "se3_rotation_translation_err": round(se3_err, 12),
        "pbc_lattice_shift_err": round(pbc_err, 12),
        "permutation_equivariance_err": round(perm_err, 12),
        "perturbation_signal": round(pert_delta, 12),
        "tol": tol_f,
    }


@_finite_inputs
def verify_pairwise_no_self_interaction_and_symmetry(
    pairwise_fn: Callable[[Any, Any], Any],
    sample_a: Any,
    sample_b: Any,
    grouped_aggregator_fn: Optional[Callable[[Sequence[Any], Sequence[int]], float]] = None,
    tol: float = 1e-9,
) -> Dict[str, Any]:
    """
    Domain-Agnostic Pairwise Kernel Exchange Symmetry & Zero Intra-Group/Self-Interaction Gate (`G5o`).
    """
    tol_f = _finite_float(tol)
    if not (0.0 < tol_f <= _MAX_SYMMETRY_TOL):
        raise ValueError(f"G5o tol must be in (0, {_MAX_SYMMETRY_TOL}], got {tol_f}")
    violations: List[str] = []
    if not _kwargs_materially_differ({"s": sample_a}, {"s": sample_b}):
        violations.append("Vacuous pairwise probe: sample_a and sample_b are identical.")

    out_ab = _extract_array(_finite_call(pairwise_fn, sample_a, sample_b))
    out_ba = _extract_array(_finite_call(pairwise_fn, sample_b, sample_a))
    sym_err = _finite_float(np.max(np.abs(out_ab - out_ba)))
    same_group_leakage = 0.0
    distinct_group_signal = _finite_float(np.max(np.abs(out_ab)))

    if sym_err > tol_f:
        violations.append(f"Pairwise exchange symmetry violation: ||K(A,B) - K(B,A)||_inf = {sym_err:.3e} > {tol_f:.3e}")
    if distinct_group_signal <= tol_f:
        violations.append(f"Pairwise kernel collapsed to zero on distinct entities: ||K(A,B)||_inf = {distinct_group_signal:.3e}")

    if grouped_aggregator_fn is not None:
        leak2 = abs(_finite_float(_finite_call(grouped_aggregator_fn, [sample_a, sample_b], [0, 0])))
        leak3 = abs(_finite_float(_finite_call(grouped_aggregator_fn, [sample_a, sample_b, sample_a], [0, 0, 0])))
        same_group_leakage = max(leak2, leak3)
        distinct_group_signal = abs(_finite_float(_finite_call(grouped_aggregator_fn, [sample_a, sample_b], [0, 1])))
        if same_group_leakage > tol_f:
            violations.append(
                f"Intra-group self-interaction leakage: grouped_aggregator same-group = {same_group_leakage:.4e} != 0"
            )
        if distinct_group_signal <= tol_f:
            violations.append("Distinct-group interaction collapsed to zero on [0, 1]")

    return {
        "status": "PASS" if not violations else "FAIL",
        "exchange_symmetry_err": round(sym_err, 12),
        "same_group_self_interaction_leakage": round(same_group_leakage, 12),
        "distinct_group_signal": round(distinct_group_signal, 8),
        "violations": violations,
    }


@_finite_inputs
def verify_scale_homogeneity_and_rank1_null_calibration(
    target_fn: Callable[[Any], Any],
    base_input: Any,
    homogeneity_degree: float = 0.0,
    scale_factors: Sequence[float] = (0.01, 0.37, 2.5, 100.0),
    rank1_null_input_builder_fn: Optional[Callable[[float], Any]] = None,
    null_metric_extractor_fn: Optional[Callable[[Any], float]] = None,
    asymmetric_marginals: Sequence[float] = (0.10, 0.20, 0.35, 0.50, 0.65, 0.80, 0.90),
    tol: float = 1e-9,
) -> Dict[str, Any]:
    """
    Domain-Agnostic Euler Scale Homogeneity `f(lambda * x) = lambda^k * f(x)` &
    Asymmetric Rank-1 Product Null-Model Zero-Point Calibration Gate (`G3j`).
    """
    tol_f = _finite_float(tol)
    if not (0.0 < tol_f <= _MAX_SYMMETRY_TOL) or len(scale_factors) < 2:
        raise ValueError(f"Invalid G3j tol={tol_f} or scale_factors={scale_factors}")
    x_arr = _finite_array(base_input, dtype=np.float64)
    base_out = _extract_array(_finite_call(target_fn, x_arr.copy()))
    max_homog_err = 0.0
    violations: List[str] = []

    if _finite_float(np.max(np.abs(base_out))) <= tol_f:
        violations.append("Euler scale-homogeneity base output collapsed to zero on base_input.")

    for lam in scale_factors:
        lam_f = _finite_float(lam)
        if lam_f <= 0.0:
            raise ValueError(f"Scale factor must be strictly positive, got {lam_f}")
        scaled_out = _extract_array(_finite_call(target_fn, (lam_f * x_arr).copy()))
        expected_out = (lam_f ** _finite_float(homogeneity_degree)) * base_out
        err = _finite_float(np.max(np.abs(scaled_out - expected_out)))
        if err > max_homog_err:
            max_homog_err = err
    if max_homog_err > tol_f:
        violations.append(
            f"Euler scale-homogeneity violation (degree k={homogeneity_degree}): max ||f(lam*x) - lam^k f(x)||_inf = {max_homog_err:.3e} > {tol_f:.3e}"
        )

    if (rank1_null_input_builder_fn is None) != (null_metric_extractor_fn is None):
        violations.append("Both rank1_null_input_builder_fn and null_metric_extractor_fn must be provided together.")

    max_null_err = 0.0
    if rank1_null_input_builder_fn is not None and null_metric_extractor_fn is not None:
        if not asymmetric_marginals:
            violations.append("asymmetric_marginals cannot be empty when rank-1 null calibration is requested.")
        for p_val in asymmetric_marginals:
            null_in = _finite_call(rank1_null_input_builder_fn, _finite_float(p_val))
            null_val = abs(_finite_float(_finite_call(null_metric_extractor_fn, _finite_call(target_fn, null_in))))
            if null_val > max_null_err:
                max_null_err = null_val
        if max_null_err > tol_f:
            violations.append(
                f"Asymmetric rank-1 independence null-model zero-point violation: max |metric(p*p^T)| = {max_null_err:.4e} > {tol_f:.3e}"
            )

    return {
        "status": "PASS" if not violations else "FAIL",
        "homogeneity_degree": _finite_float(homogeneity_degree),
        "max_scale_homogeneity_err": round(max_homog_err, 12),
        "max_rank1_null_calibration_err": round(max_null_err, 12),
        "violations": violations,
    }
