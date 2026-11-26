"""AWF Guard: geometry."""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple
import numpy as np

from awf_guard_numeric_contracts import finite_array as _finite_array
from awf_guard_numeric_contracts import finite_call as _finite_call
from awf_guard_numeric_contracts import finite_float as _finite_float
from awf_guard_numeric_contracts import finite_inputs as _finite_inputs
from awf_guard_radius_probes import radius_probe_violations as _radius_probe_violations
from .numeric_inputs import _extract_array, _kwargs_materially_differ


_G5R_MAX_TOLERANCE = 1e-3
_MAX_GEOMETRY_TOL = 1e-3


def _infer_voxel_grid_arg(kwargs: Dict[str, Any]) -> Optional[str]:
    for key, val in kwargs.items():
        if isinstance(val, np.ndarray) and val.ndim == 3:
            return key
    return None


def _build_canonical_voxel_fixtures(side: int, pad: int) -> Dict[str, np.ndarray]:
    """
    Gate-owned thickness-1 cubic shells, corner-punctured shells, straight 1-D curve,
     PLUS odd-sum sealed shell (`sealed_tab_odd`) and even-sum punctured shell (`punct_tab_even`,
    which shares the exact grid shape AND exact foreground voxel count of `sealed` while having
    punctured homology `(1, 0, 0, 1)`, defeating all voxel-sum / parity lookup cheats).
    """
    n_tot = side + 2 * pad
    lo, hi = pad, pad + side
    sealed = np.zeros((n_tot, n_tot, n_tot), dtype=np.float64)
    sealed[lo:hi, lo:hi, lo:hi] = 1.0
    sealed[lo + 1:hi - 1, lo + 1:hi - 1, lo + 1:hi - 1] = 0.0
    punct = sealed.copy()
    punct[lo, lo, lo] = 0.0
    sealed_tab_odd = sealed.copy()
    sealed_tab_odd[lo + 1, lo + 1, hi] = 1.0
    punct_tab_even = sealed_tab_odd.copy()
    punct_tab_even[lo, lo, lo] = 0.0
    curve = np.zeros_like(sealed)
    curve[lo:hi, lo + side // 2, lo + side // 2] = 1.0
    return {
        "sealed": sealed,
        "punct": punct,
        "sealed_tab_odd": sealed_tab_odd,
        "punct_tab_even": punct_tab_even,
        "curve": curve,
    }


_G5Q_EXPECTED_BETTI_CHI: Dict[str, Tuple[float, ...]] = {
    "sealed": (1.0, 0.0, 1.0, 2.0),
    "punct": (1.0, 0.0, 0.0, 1.0),
    "sealed_tab_odd": (1.0, 0.0, 1.0, 2.0),
    "punct_tab_even": (1.0, 0.0, 0.0, 1.0),
    "curve": (1.0, 0.0, 0.0, 1.0),
}


_G5Q_GENERATED_SIDE_PAD: Tuple[Tuple[int, int], ...] = ((3, 2), (5, 2))


def _g5q_gate_generated_fixture_violations(
    homology_fn: Callable[..., Any],
    base_kwargs: Dict[str, Any],
    grid_arg: str,
    tol: float,
) -> Tuple[List[str], int]:
    """Re-run `homology_fn` on gate-generated translated, rescaled, and parity-flipped shells."""
    violations: List[str] = []
    checked = 0
    user_dtype = _finite_array(base_kwargs[grid_arg]).dtype
    for side, pad in _G5Q_GENERATED_SIDE_PAD:
        fixtures = _build_canonical_voxel_fixtures(side, pad)
        for key, exp_vec in _G5Q_EXPECTED_BETTI_CHI.items():
            kw = dict(base_kwargs)
            kw[grid_arg] = fixtures[key].astype(user_dtype)
            out = _extract_array(_finite_call(homology_fn, **kw)).reshape(-1)
            checked += 1
            if len(out) < 4 or not np.all(np.isfinite(out[:4])) or _finite_float(np.max(np.abs(out[:4] - _finite_array(exp_vec)))) > tol:
                violations.append(
                    f"Gate-generated `{key}` fixture (side={side}, pad={pad}) gave {out[:4].tolist()} != {list(exp_vec)} "
                    f"(homology must follow geometry, not memorized inputs or voxel-count parity)"
                )
    return violations, checked


@_finite_inputs
def verify_euler_poincare_and_digital_duality(
    homology_fn: Callable[..., Any],
    sealed_shell_kwargs: Dict[str, Any],
    corner_punctured_shell_kwargs: Dict[str, Any],
    contractible_path_kwargs: Optional[Dict[str, Any]] = None,
    tol: float = 1e-9,
) -> Dict[str, Any]:
    """
    Domain-Agnostic Euler-Poincare Homological Identity, Digital Jordan-Brouwer Dual-Adjacency
    (6-Foreground vs 26-Background) & 1D Supercover Homotopy Gate (`G5q`).
    """
    tol_f = _finite_float(tol)
    if not (0.0 < tol_f <= _MAX_GEOMETRY_TOL):
        raise ValueError(f"G5q tol must be in (0, {_MAX_GEOMETRY_TOL}], got {tol_f}")
    violations: List[str] = []
    out_sealed = _extract_array(_finite_call(homology_fn, **sealed_shell_kwargs)).reshape(-1)
    out_punct = _extract_array(_finite_call(homology_fn, **corner_punctured_shell_kwargs)).reshape(-1)
    if not _kwargs_materially_differ(sealed_shell_kwargs, corner_punctured_shell_kwargs, target_fn=homology_fn):
        violations.append("Vacuous probe: `corner_punctured_shell_kwargs` is identical to `sealed_shell_kwargs`.")
    grid_arg = _infer_voxel_grid_arg(sealed_shell_kwargs)
    generated_checked = 0
    if grid_arg is None:
        violations.append(
            "G5q requires a 3-D ndarray voxel-grid argument so the gate can generate its own canonical shells; "
            "caller-supplied labels or non-grid inputs cannot be geometry-validated."
        )
    else:
        gen_violations, generated_checked = _g5q_gate_generated_fixture_violations(
            homology_fn, sealed_shell_kwargs, grid_arg, tol_f
        )
        violations.extend(gen_violations)

    for label, vec, exp_vec in (
        ("sealed_shell_S2", out_sealed, np.array([1.0, 0.0, 1.0, 2.0])),
        ("corner_punctured_shell", out_punct, np.array([1.0, 0.0, 0.0, 1.0])),
    ):
        if len(vec) < 4:
            violations.append(f"`{label}` output must have 4 components [beta_0, beta_1, beta_2, chi], got {vec.tolist()}")
            continue
        b0, b1, b2, chi = _finite_float(vec[0]), _finite_float(vec[1]), _finite_float(vec[2]), _finite_float(vec[3])
        ep_err = abs((b0 - b1 + b2) - chi)
        if ep_err > tol_f:
            violations.append(f"Euler-Poincare violation on `{label}`: b0 - b1 + b2 = {b0 - b1 + b2} != chi = {chi}")
        if _finite_float(np.max(np.abs(vec[:4] - exp_vec))) > tol_f:
            violations.append(
                f"Digital duality / homology mismatch on `{label}`: got {vec[:4].tolist()} != expected {exp_vec.tolist()} "
                f"(6-vs-26 adjacency paradox or cell-count error)"
            )

    path_vec_list: List[float] = []
    if contractible_path_kwargs is not None:
        out_path = _extract_array(_finite_call(homology_fn, **contractible_path_kwargs)).reshape(-1)
        path_vec_list = [_finite_float(x) for x in out_path[:4]]
        exp_path = np.array([1.0, 0.0, 0.0, 1.0])
        if len(out_path) < 4 or _finite_float(np.max(np.abs(out_path[:4] - exp_path))) > tol_f:
            violations.append(
                f"1D contractible curve homotopy violation (voxel pinch-off / micro-loop): "
                f"got {path_vec_list} != expected [1.0, 0.0, 0.0, 1.0]"
            )

    return {
        "status": "PASS" if not violations else "FAIL",
        "sealed_shell_betti_chi": [_finite_float(x) for x in out_sealed[:4]],
        "corner_punctured_betti_chi": [_finite_float(x) for x in out_punct[:4]],
        "contractible_path_betti_chi": path_vec_list,
        "gate_generated_fixtures_checked": generated_checked,
        "violations": violations,
    }


@_finite_inputs
def verify_filtration_monotonicity_and_heterogeneous_radius_clearance(
    clearance_fn: Callable[..., Any],
    base_input_kwargs: Dict[str, Any],
    heterogeneous_radius_probe_kwargs: Dict[str, Any],
    expected_heterogeneous_void_max: float = 0.0,
    partition_total: float = 100.0,
    complement_index: int = 0,
    filtration_indices: Sequence[int] = (1, 2, 3),
    tol: float = 1e-9,
    geometry_argument_names: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Domain-Agnostic Cumulative Filtration Monotonicity, Partition-of-Unity Conservation
    & Heterogeneous-Radius Surface Dominance Gate (`G5r`).
    """
    violations: List[str] = []
    tol_f = _finite_float(tol)
    part_tot = _finite_float(partition_total)
    if part_tot <= 0.0 or not (0.0 < tol_f <= _G5R_MAX_TOLERANCE * min(1.0, part_tot)) or not filtration_indices:
        raise ValueError("G5r requires positive partition_total and 0 < tol <= 1e-3 * min(1, partition_total)")
    violations.extend(_radius_probe_violations(clearance_fn, base_input_kwargs, geometry_argument_names, _extract_array, filtration_indices[0], part_tot, tol_f))
    if violations:
        return {"status": "FAIL", "violations": violations}
    out_base = _extract_array(_finite_call(clearance_fn, **base_input_kwargs)).reshape(-1)
    comp_val = _finite_float(out_base[complement_index])
    filt_vals = [_finite_float(out_base[idx]) for idx in filtration_indices]

    part_err = abs((comp_val + filt_vals[0]) - part_tot)
    if part_err > tol_f:
        violations.append(
            f"Partition-of-unity violation: out[{complement_index}] ({comp_val:.6f}) + "
            f"out[{filtration_indices[0]}] ({filt_vals[0]:.6f}) != {part_tot:.6f}"
        )

    for k_i in range(len(filt_vals) - 1):
        if filt_vals[k_i + 1] > filt_vals[k_i] + tol_f:
            violations.append(
                f"Filtration monotonicity violation: f(tau_{k_i+1})={filt_vals[k_i+1]:.6f} > f(tau_{k_i})={filt_vals[k_i]:.6f}"
            )
    if any(v < -tol_f or v > part_tot + tol_f for v in filt_vals):
        violations.append(f"Filtration values out of bounds [0, {part_tot}]: {filt_vals}")

    if not _kwargs_materially_differ(base_input_kwargs, heterogeneous_radius_probe_kwargs, target_fn=clearance_fn):
        violations.append("Vacuous probe: `heterogeneous_radius_probe_kwargs` is identical to `base_input_kwargs`.")
    out_het = _extract_array(_finite_call(clearance_fn, **heterogeneous_radius_probe_kwargs)).reshape(-1)
    het_void0 = _finite_float(out_het[filtration_indices[0]])
    if het_void0 > _finite_float(expected_heterogeneous_void_max) + tol_f:
        violations.append(
            f"Heterogeneous-radius surface clearance failure (k=1 center-distance trap): "
            f"got void={het_void0:.6f} > {_finite_float(expected_heterogeneous_void_max):.6f} when point is inside large sphere!"
        )

    return {
        "status": "PASS" if not violations else "FAIL",
        "partition_unity_err": round(part_err, 12),
        "filtration_spectrum": [round(v, 6) for v in filt_vals],
        "heterogeneous_probe_void": round(het_void0, 8),
        "violations": violations,
    }


@_finite_inputs
def verify_rp2_director_gauge_and_reciprocal_conjugacy(
    diffraction_fn: Callable[..., Any],
    base_input_kwargs: Dict[str, Any],
    director_arg_name: str = "sub_normals",
    slipped_stack_kwargs: Optional[Dict[str, Any]] = None,
    short_stack_kwargs: Optional[Dict[str, Any]] = None,
    spacing_index: int = 0,
    wavevector_index: int = 1,
    persistence_index: int = 2,
    coherence_index: int = 3,
    tol: float = 1e-8,
) -> Dict[str, Any]:
    """
    Domain-Agnostic RP^2 Headless-Director Sign-Gauge Invariance (`n_i -> s_i * n_i`),
    Normal-Projection Lateral-Slip Decoupling, Reciprocal Conjugacy (`d * q == 2*pi`)
    & Finite-Stack Coherence Scaling Gate (`G3k`).
    """
    tol_f = _finite_float(tol)
    if not (0.0 < tol_f <= _MAX_GEOMETRY_TOL):
        raise ValueError(f"G3k tol must be in (0, {_MAX_GEOMETRY_TOL}], got {tol_f}")
    violations: List[str] = []
    out_base = _extract_array(_finite_call(diffraction_fn, **base_input_kwargs)).reshape(-1)
    d0 = _finite_float(out_base[spacing_index])
    q0 = _finite_float(out_base[wavevector_index])
    recip_err = abs(d0 * q0 - 2.0 * _finite_float(np.pi))
    if recip_err > 1e-6:
        violations.append(f"Reciprocal-space conjugacy violation: d0 * q0 = {d0 * q0:.8f} != 2*pi")

    for probe_name, probe_kw in (("slipped_stack_kwargs", slipped_stack_kwargs), ("short_stack_kwargs", short_stack_kwargs)):
        if probe_kw is None:
            violations.append(f"Required probe `{probe_name}` missing (G3k probes are mandatory, not skippable).")
        elif not _kwargs_materially_differ(probe_kw, base_input_kwargs, target_fn=diffraction_fn):
            violations.append(f"Vacuous probe: `{probe_name}` is identical to `base_input_kwargs`.")
    if slipped_stack_kwargs is not None and short_stack_kwargs is not None:
        if not _kwargs_materially_differ(slipped_stack_kwargs, short_stack_kwargs, target_fn=diffraction_fn):
            violations.append("Vacuous probe: `slipped_stack_kwargs` and `short_stack_kwargs` are identical.")

    dirs = _finite_array(base_input_kwargs[director_arg_name], dtype=np.float64).copy()
    if len(dirs) < 2:
        violations.append("RP^2 gauge probe needs >= 2 directors (alternating sign flip is the identity for one).")
    alt_signs = np.where((np.arange(len(dirs)) % 2) == 0, 1.0, -1.0)[:, None]
    single_signs = np.ones((len(dirs), 1), dtype=np.float64)
    single_signs[0, 0] = -1.0
    gauge_err = 0.0
    for signs in (alt_signs, single_signs):
        gauge_kw = dict(base_input_kwargs)
        gauge_kw[director_arg_name] = dirs * signs
        out_gauge = _extract_array(_finite_call(diffraction_fn, **gauge_kw)).reshape(-1)
        gauge_err = max(gauge_err, _finite_float(np.max(np.abs(out_gauge - out_base))))
    if gauge_err > tol_f:
        violations.append(
            f"RP^2 headless-director sign-gauge violation: max |f(R, S*n) - f(R, n)| = {gauge_err:.4e} > {tol_f:.2e}"
        )

    slip_spacing_err = 0.0
    if slipped_stack_kwargs is not None:
        out_slip = _extract_array(_finite_call(diffraction_fn, **slipped_stack_kwargs)).reshape(-1)
        slip_spacing_err = abs(_finite_float(out_slip[spacing_index]) - d0)
        if slip_spacing_err > tol_f:
            violations.append(
                f"Lateral-slip spacing inflation trap: d_perp(slipped)={_finite_float(out_slip[spacing_index]):.6f} "
                f"!= d_perp(aligned)={d0:.6f} (center-to-center distance bug)"
            )

    if short_stack_kwargs is not None:
        out_short = _extract_array(_finite_call(diffraction_fn, **short_stack_kwargs)).reshape(-1)
        if _finite_float(out_base[persistence_index]) <= _finite_float(out_short[persistence_index]) + tol_f:
            violations.append(
                f"Real-space column persistence failed to grow with stack size: "
                f"L(long)={_finite_float(out_base[persistence_index]):.4f} <= L(short)={_finite_float(out_short[persistence_index]):.4f}"
            )
        if _finite_float(out_base[coherence_index]) <= _finite_float(out_short[coherence_index]) + tol_f:
            violations.append(
                f"Reciprocal Scherrer coherence length failed to grow with stack size: "
                f"CCL(long)={_finite_float(out_base[coherence_index]):.4f} <= CCL(short)={_finite_float(out_short[coherence_index]):.4f}"
            )

    return {
        "status": "PASS" if not violations else "FAIL",
        "reciprocal_product_err": round(recip_err, 12),
        "rp2_director_gauge_err": round(gauge_err, 12),
        "lateral_slip_spacing_err": round(slip_spacing_err, 12),
        "violations": violations,
    }
