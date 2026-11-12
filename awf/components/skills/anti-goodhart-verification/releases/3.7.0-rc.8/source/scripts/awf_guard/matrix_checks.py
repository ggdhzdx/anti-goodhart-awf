"""AWF Guard: matrix checks."""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple
import numpy as np

from awf_guard_numeric_contracts import finite_array as _finite_array
from awf_guard_numeric_contracts import finite_call as _finite_call
from awf_guard_numeric_contracts import finite_float as _finite_float
from awf_guard_numeric_contracts import finite_inputs as _finite_inputs
from .atoms import GLOBAL_ATOM_REGISTRY
from .numeric_inputs import _extract_array, _kwargs_materially_differ

_MAX_MATRIX_TOL = 1e-3
_PENCIL_PERTURB_DELTA = 0.25
_MIN_BROKEN_GAUGE_FLOOR = 1e-4


def _coerce_real_or_complex_matrix(matrix: Any) -> np.ndarray:
    raw = np.asarray(matrix)
    if raw.dtype == object or not np.all(np.isfinite(raw)):
        raise ValueError("Expected numeric matrix with only finite entries")
    target_dtype = np.complex128 if np.iscomplexobj(raw) else np.float64
    return np.asarray(raw, dtype=target_dtype)


@_finite_inputs
def verify_physical_matrix_invariants_and_unit_homogeneity(
    matrix: Optional[np.ndarray] = None,
    require_hermitian: bool = True,
    require_psd: bool = False,
    min_eigenvalue: float = -1e-9,
    require_rate_conservation: bool = False,
    equilibrium_populations: Optional[np.ndarray] = None,
    atom_registry: Optional[Dict[str, Dict[str, Any]]] = None,
    tol: float = 1e-7,
) -> Dict[str, Any]:
    """
    Verify physical operator matrix invariants (Hamiltonian Hermiticity over R or C, Overlap/Kernel
    Positive-Definiteness, Master-Equation probability conservation, non-negative off-diagonal transition
    rates & Detailed Balance) AND cross-atom physical unit homogeneity (`G5m`).
    """
    tol_f = _finite_float(tol)
    if not (0.0 < tol_f <= _MAX_MATRIX_TOL):
        raise ValueError(f"G5m tol must be in (0, {_MAX_MATRIX_TOL}], got {tol_f}")
    hermitian_err = 0.0
    min_eig = 0.0
    rate_col_sum_err = 0.0
    detailed_balance_err = 0.0
    matrix_violations: List[str] = []
    reg = atom_registry if atom_registry is not None else GLOBAL_ATOM_REGISTRY

    if matrix is None and not reg:
        matrix_violations.append("Neither `matrix` nor non-empty `atom_registry` was supplied to G5m.")

    if matrix is not None:
        mat = _coerce_real_or_complex_matrix(matrix)
        if mat.ndim != 2 or mat.shape[0] != mat.shape[1] or mat.shape[0] < 1:
            matrix_violations.append(f"Expected non-empty square 2D matrix, got shape {mat.shape}")
        else:
            hermitian_err = _finite_float(np.max(np.abs(mat - mat.conj().T)))
            if require_hermitian and hermitian_err > tol_f:
                matrix_violations.append(f"Hermiticity violation: ||M - M^H||_inf = {hermitian_err:.3e} > {tol_f:.3e}")
            if require_psd:
                if np.iscomplexobj(mat) and hermitian_err > tol_f:
                    matrix_violations.append(f"Complex PSD violation: non-Hermitian matrix ||M - M^H||_inf = {hermitian_err:.3e}")
                sym_part = 0.5 * (mat + mat.conj().T)
                min_eig = _finite_float(np.min(np.linalg.eigvalsh(sym_part)))
                if min_eig < _finite_float(min_eigenvalue):
                    matrix_violations.append(
                        f"Positive-definiteness violation: lambda_min = {min_eig:.4e} < {_finite_float(min_eigenvalue):.4e}"
                    )
            if require_rate_conservation:
                if np.iscomplexobj(mat) and _finite_float(np.max(np.abs(np.imag(mat)))) > tol_f:
                    matrix_violations.append("Rate matrix must be real-valued.")
                mat_real = np.real(mat)
                if _finite_float(np.max(np.abs(mat_real))) <= tol_f:
                    matrix_violations.append("Rate matrix collapsed to all-zero matrix.")
                off_diag = mat_real - np.diag(np.diag(mat_real))
                if _finite_float(np.min(off_diag)) < -tol_f:
                    matrix_violations.append("Rate matrix has negative off-diagonal transition rate(s).")
                rate_col_sum_err = _finite_float(np.max(np.abs(np.sum(mat_real, axis=0))))
                if rate_col_sum_err > tol_f:
                    matrix_violations.append(
                        f"Rate matrix column-sum conservation violation: max(|sum_i K_ij|) = {rate_col_sum_err:.3e}"
                    )
                if equilibrium_populations is not None:
                    p_eq = _finite_array(equilibrium_populations, dtype=np.float64).reshape(-1)
                    if len(p_eq) != mat_real.shape[0] or np.any(p_eq <= tol_f) or abs(_finite_float(np.sum(p_eq)) - 1.0) > _MAX_MATRIX_TOL:
                        matrix_violations.append("Equilibrium populations must be strictly positive, length N, and sum to 1.")
                    else:
                        flux_mat = mat_real * p_eq[None, :]
                        detailed_balance_err = _finite_float(np.max(np.abs(flux_mat - flux_mat.T)))
                        if detailed_balance_err > tol_f:
                            matrix_violations.append(
                                f"Detailed balance violation: max(|K_ij p_j - K_ji p_i|) = {detailed_balance_err:.3e}"
                            )

    unit_mismatches: List[Dict[str, str]] = []
    for aid, info in reg.items():
        in_specs = info.get("inputs", {})
        for up_id in info.get("upstream_atoms", []):
            if up_id in reg:
                up_outs = reg[up_id].get("outputs", {})
                for shared_param in set(in_specs.keys()) & set(up_outs.keys()):
                    u_out = str(up_outs[shared_param].get("unit", "dimensionless"))
                    u_in = str(in_specs[shared_param].get("unit", "dimensionless"))
                    if u_out != u_in:
                        unit_mismatches.append({
                            "upstream_atom": up_id,
                            "downstream_atom": aid,
                            "parameter": shared_param,
                            "upstream_unit": u_out,
                            "downstream_unit": u_in,
                        })

    passed = (not matrix_violations) and (not unit_mismatches)
    return {
        "status": "PASS" if passed else "FAIL",
        "hermitian_err": round(hermitian_err, 12),
        "min_eigenvalue": round(min_eig, 10),
        "rate_col_sum_err": round(rate_col_sum_err, 12),
        "detailed_balance_err": round(detailed_balance_err, 12),
        "matrix_violations": matrix_violations,
        "unit_mismatches": unit_mismatches,
    }


@_finite_inputs
def verify_nonorthogonal_pencil_gauge_and_spectral_parity(
    diabat_fn: Callable[..., Any],
    base_input_kwargs: Dict[str, Any],
    operator_metric_pairs: Sequence[Tuple[str, str]],
    energy_shifts: Sequence[float] = (-2.0, 2.5),
    subspace_dominance_pairs: Sequence[Tuple[int, int]] = ((0, 1), (2, 3)),
    bipolar_coupling_arg: Optional[str] = None,
    pure_dipolar_base_kwargs: Optional[Dict[str, Any]] = None,
    signed_coupling_index: int = 4,
    spectral_shift_index: int = 5,
    tol: float = 1e-7,
) -> Dict[str, Any]:
    """
    Domain-Agnostic Non-Orthogonal Operator Pencil Metric-Shift Gauge Invariance (`F -> F + dE*S`),
    Subspace Frobenius-Norm Dominance & Bipolar Spectral Parity Gate (`G5t`).
    """
    tol_f = _finite_float(tol)
    if not (0.0 < tol_f <= _MAX_MATRIX_TOL) or not operator_metric_pairs or not energy_shifts:
        raise ValueError(f"Invalid G5t parameters: tol={tol_f}, pairs={operator_metric_pairs}")
    violations: List[str] = []
    out_base = _extract_array(_finite_call(diabat_fn, **base_input_kwargs)).reshape(-1)
    max_pencil_shift_err = 0.0

    op0_arg = operator_metric_pairs[0][0]
    op0_mat = _finite_array(base_input_kwargs[op0_arg], dtype=np.float64).copy()
    if op0_mat.ndim == 2 and op0_mat.shape[0] >= 2:
        kw_offdiag = dict(base_input_kwargs)
        op_pert = op0_mat.copy()
        op_pert[0, -1] += _PENCIL_PERTURB_DELTA
        op_pert[-1, 0] += _PENCIL_PERTURB_DELTA
        kw_offdiag[op0_arg] = op_pert
        out_offdiag = _extract_array(_finite_call(diabat_fn, **kw_offdiag)).reshape(-1)
        if _finite_float(np.max(np.abs(out_offdiag - out_base))) <= tol_f:
            violations.append(f"Operator `{op0_arg}` sensitivity collapse: perturbing off-diagonal coupling left output unchanged.")

    for d_e in energy_shifts:
        kw_shift = dict(base_input_kwargs)
        for op_arg, met_arg in operator_metric_pairs:
            op_mat = _finite_array(base_input_kwargs[op_arg], dtype=np.float64)
            met_mat = _finite_array(base_input_kwargs[met_arg], dtype=np.float64)
            kw_shift[op_arg] = op_mat + _finite_float(d_e) * met_mat
        out_shift = _extract_array(_finite_call(diabat_fn, **kw_shift)).reshape(-1)
        err = _finite_float(np.max(np.abs(out_shift - out_base)))
        if err > max_pencil_shift_err:
            max_pencil_shift_err = err
    if max_pencil_shift_err > tol_f:
        violations.append(
            f"Non-orthogonal pencil metric-shift gauge violation (F -> F + dE*S): "
            f"max |f(F+dE*S, S) - f(F, S)| = {max_pencil_shift_err:.4e} > {tol_f:.2e} "
            f"(missing S^(-1/2) Lowdin orthogonalization)"
        )

    for i_single, i_sub in subspace_dominance_pairs:
        if _finite_float(out_base[i_sub]) <= _finite_float(out_base[i_single]) + tol_f:
            violations.append(
                f"Subspace norm dominance violation: out[{i_sub}]={_finite_float(out_base[i_sub]):.4f} "
                f"<= out[{i_single}]={_finite_float(out_base[i_single]):.4f}"
            )

    parity_anti_err = 0.0
    if bipolar_coupling_arg is not None and pure_dipolar_base_kwargs is not None:
        out_neg = _extract_array(_finite_call(diabat_fn, **pure_dipolar_base_kwargs)).reshape(-1)
        kw_pos = dict(pure_dipolar_base_kwargs)
        kw_pos[bipolar_coupling_arg] = -_finite_array(pure_dipolar_base_kwargs[bipolar_coupling_arg], dtype=np.float64)
        out_pos = _extract_array(_finite_call(diabat_fn, **kw_pos)).reshape(-1)
        j_neg, j_pos = _finite_float(out_neg[signed_coupling_index]), _finite_float(out_pos[signed_coupling_index])
        de_neg, de_pos = _finite_float(out_neg[spectral_shift_index]), _finite_float(out_pos[spectral_shift_index])
        parity_anti_err = abs(j_neg + j_pos)
        if not (j_neg < -tol_f and j_pos > tol_f and parity_anti_err <= tol_f):
            violations.append(
                f"Bipolar coupling sign-parity violation under V -> -V: J_neg={j_neg:.4f}, J_pos={j_pos:.4f}"
            )
        if not (de_neg > tol_f and de_pos < -tol_f):
            violations.append(
                f"Spectral redshift/blueshift reversal violation under V -> -V: dE_neg={de_neg:.4f}, dE_pos={de_pos:.4f}"
            )

    return {
        "status": "PASS" if not violations else "FAIL",
        "max_pencil_metric_shift_err": round(max_pencil_shift_err, 12),
        "bipolar_parity_antisymmetry_err": round(parity_anti_err, 12),
        "violations": violations,
    }


@_finite_inputs
def verify_coupled_basis_sign_gauge_and_locality_bounds(
    operator_fn: Callable[..., Any],
    base_input_kwargs: Dict[str, Any],
    matrix_arg: str = "h_ex_ev",
    vector_arg: str = "mu_vecs_debye",
    separated_cluster_shifted_kwargs: Optional[Dict[str, Any]] = None,
    max_cluster_size: int = 3,
    pr_indices: Sequence[int] = (0, 1),
    coherence_raw_vs_eff_indices: Tuple[int, int] = (2, 3),
    rg_index: int = 5,
    min_broken_gauge_drop: float = 0.05,
    tol: float = 1e-7,
) -> Dict[str, Any]:
    """
    Domain-Agnostic Coupled Operator-Vector Local Sign-Gauge Invariance (`H -> S H S, V -> S V`),
    Spatially Separated Quasi-Degenerate Cluster Locality & Cauchy-Schwarz Collective Bounds Gate (`G3l`).
    """
    tol_f = _finite_float(tol)
    drop_f = _finite_float(min_broken_gauge_drop)
    if not (0.0 < tol_f <= _MAX_MATRIX_TOL) or drop_f < _MIN_BROKEN_GAUGE_FLOOR:
        raise ValueError(f"Invalid G3l bounds: tol={tol_f}, min_broken_gauge_drop={drop_f}")
    violations: List[str] = []
    out_base = _extract_array(_finite_call(operator_fn, **base_input_kwargs)).reshape(-1)
    h_mat = _finite_array(base_input_kwargs[matrix_arg], dtype=np.float64)
    v_mat = _finite_array(base_input_kwargs[vector_arg], dtype=np.float64)
    n_sites = h_mat.shape[0]

    alt_signs = np.array([1.0 if (i % 2 == 0) else -1.0 for i in range(n_sites)], dtype=np.float64)
    single_signs = np.ones(n_sites, dtype=np.float64)
    single_signs[0] = -1.0
    joint_gauge_err = 0.0
    for signs in (alt_signs, single_signs):
        s_diag = np.diag(signs)
        kw_joint = dict(base_input_kwargs)
        kw_joint[matrix_arg] = s_diag @ h_mat @ s_diag
        kw_joint[vector_arg] = signs[:, None] * v_mat if v_mat.ndim == 2 else signs * v_mat
        out_joint = _extract_array(_finite_call(operator_fn, **kw_joint)).reshape(-1)
        joint_gauge_err = max(joint_gauge_err, _finite_float(np.max(np.abs(out_joint - out_base))))
    if joint_gauge_err > tol_f:
        violations.append(f"Coupled sign-gauge violation (H->SHS, V->SV): max_err={joint_gauge_err:.4e} > {tol_f:.2e}")

    kw_broken = dict(base_input_kwargs)
    kw_broken[vector_arg] = alt_signs[:, None] * v_mat if v_mat.ndim == 2 else alt_signs * v_mat
    out_broken = _extract_array(_finite_call(operator_fn, **kw_broken)).reshape(-1)
    broken_gauge_shift = _finite_float(np.max(np.abs(out_broken - out_base)))
    if broken_gauge_shift < drop_f:
        violations.append(f"Insensitive to unpaired sign flip (V->SV with fixed H): shift={broken_gauge_shift:.4e}")

    locality_err = 0.0
    if separated_cluster_shifted_kwargs is not None:
        if not _kwargs_materially_differ(separated_cluster_shifted_kwargs, base_input_kwargs, target_fn=operator_fn):
            violations.append("Vacuous probe: `separated_cluster_shifted_kwargs` is identical to `base_input_kwargs`.")
        out_sep = _extract_array(_finite_call(operator_fn, **separated_cluster_shifted_kwargs)).reshape(-1)
        locality_err = _finite_float(np.max(np.abs(out_sep - out_base)))
        if locality_err > tol_f:
            violations.append(f"Separated-cluster ghost delocalization: shift_err={locality_err:.4e} > {tol_f:.2e}")

    n_lim = _finite_float(max_cluster_size) + tol_f
    for idx in pr_indices:
        if not (1.0 - tol_f <= _finite_float(out_base[idx]) <= n_lim):
            violations.append(f"Participation ratio out[{idx}]={_finite_float(out_base[idx]):.4f} outside [1, {max_cluster_size}]")
    i_raw, i_eff = coherence_raw_vs_eff_indices
    if not (0.0 <= _finite_float(out_base[i_eff]) <= _finite_float(out_base[i_raw]) + tol_f <= n_lim + tol_f):
        violations.append(f"Cauchy-Schwarz coherence bound violation: eff={_finite_float(out_base[i_eff]):.4f}, raw={_finite_float(out_base[i_raw]):.4f}")
    if _finite_float(out_base[rg_index]) < -tol_f:
        violations.append(f"Negative spatial spread Rg={_finite_float(out_base[rg_index]):.4f}")
    if pr_indices and _finite_float(out_base[pr_indices[0]]) > 1.0 + _MAX_MATRIX_TOL and separated_cluster_shifted_kwargs is not None:
        if _finite_float(out_base[rg_index]) <= tol_f:
            violations.append("Delocalized state (PR > 1) reported collapsed spatial spread Rg == 0.")

    return {
        "status": "PASS" if not violations else "FAIL",
        "joint_sign_gauge_err": round(joint_gauge_err, 12),
        "broken_sign_gauge_shift": round(broken_gauge_shift, 12),
        "separated_cluster_locality_err": round(locality_err, 12),
        "violations": violations,
    }
