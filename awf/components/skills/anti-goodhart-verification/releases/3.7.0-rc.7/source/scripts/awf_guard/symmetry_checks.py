"""AWF Guard: symmetry checks."""
from __future__ import annotations

from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import Literal
from typing import Optional
from typing import Sequence
from awf_guard_numeric_contracts import finite_array as _finite_array
from awf_guard_numeric_contracts import finite_call as _finite_call
from awf_guard_numeric_contracts import finite_float as _finite_float
from awf_guard_numeric_contracts import finite_inputs as _finite_inputs
import numpy as np
from .numeric_inputs import _extract_array


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
    1. `SE(3)` Proper Rigid Rotation (`R in SO(3)`, `det(R)=+1`) + Translation `t`:
       - Scalar (`output_tensor_rank == 0`): `f(r @ R.T + t, cell @ R.T) == f(r, cell)`
       - Per-atom 3D Vector (`output_tensor_rank == 1`): `F(r @ R.T + t, cell @ R.T) == F(r, cell) @ R.T`
    2. 3D Periodic Boundary Condition (PBC Minimum-Image Convention, including Triclinic Cell):
       - Displaces atom 0 by integer lattice vectors `n @ cell`; catches missing MIC or orthogonal-only wrapping.
    3. `S_N` Atomic Permutation Invariance / Equivariance:
       - Permutes atomic order `r[perm]` and verifies scalar invariance or vector row covarying `F[perm]`.
    """
    pos = _finite_array(coords, dtype=np.float64)
    if pos.ndim != 2 or pos.shape[1] != 3:
        raise ValueError(f"coords must have shape (N, 3), got {pos.shape}")
    n_atoms = pos.shape[0]
    kw_base = dict(extra_kwargs) if extra_kwargs is not None else {}
    kw_base[coord_kwarg] = pos.copy()
    if cell is not None:
        cell_arr = _finite_array(cell, dtype=np.float64)
        kw_base[cell_kwarg] = cell_arr.copy()
    else:
        cell_arr = None

    base_out = _extract_array(_finite_call(target_fn, **kw_base))

    # 1. Generate random proper rotation R in SO(3) (det = +1) and translation t
    rng = np.random.default_rng(seed)
    q_mat, r_mat = np.linalg.qr(rng.normal(size=(3, 3)))
    d_diag = np.diag(np.sign(np.diag(r_mat)))
    rot = q_mat @ d_diag
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

    # 2. 3D Periodic Boundary Condition (PBC) integer lattice shift check
    pbc_err = 0.0
    if cell_arr is not None and n_atoms >= 1:
        kw_pbc = dict(kw_base)
        pos_pbc = pos.copy()
        lattice_shift = np.array([1.0, -1.0, 1.0], dtype=np.float64) @ cell_arr
        pos_pbc[0] = pos_pbc[0] + lattice_shift
        kw_pbc[coord_kwarg] = pos_pbc
        out_pbc = _extract_array(_finite_call(target_fn, **kw_pbc))
        pbc_err = _finite_float(np.max(np.abs(out_pbc - base_out)))

    # 3. S_N Atomic Permutation symmetry / equivariance check
    perm_err = 0.0
    if n_atoms >= 2:
        perm = np.roll(np.arange(n_atoms), 1)
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
        perm_err = _finite_float(np.max(np.abs(out_perm - expected_perm)))

    passed = bool(se3_err <= tol and pbc_err <= tol and perm_err <= tol)
    return {
        "status": "PASS" if passed else "FAIL",
        "se3_rotation_translation_err": round(se3_err, 12),
        "pbc_lattice_shift_err": round(pbc_err, 12),
        "permutation_equivariance_err": round(perm_err, 12),
        "tol": tol,
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
    Domain-Agnostic Pairwise Kernel Exchange Symmetry & Zero Intra-Group/Self-Interaction Gate (`G5n`):
    1. Verifies pairwise exchange symmetry `||K(A, B) - K(B, A)||_inf <= tol`.
    2. When `grouped_aggregator_fn(entities, group_ids)` is provided, verifies that placing all entities
       into the same group (`group_ids = [0, 0]`) yields strictly zero inter-group interaction (`|E_same_group| <= tol`),
       while distinct groups (`group_ids = [0, 1]`) yield non-zero interaction. Catches diagonal `i == j` and
       intra-entity (`group_i == group_j`) self-interaction pollution in N-body, graph, and pairwise potentials.
    """
    out_ab = _extract_array(_finite_call(pairwise_fn, sample_a, sample_b))
    out_ba = _extract_array(_finite_call(pairwise_fn, sample_b, sample_a))
    sym_err = _finite_float(np.max(np.abs(out_ab - out_ba)))
    same_group_leakage = 0.0
    distinct_group_signal = _finite_float(np.max(np.abs(out_ab)))
    violations: List[str] = []

    if sym_err > tol:
        violations.append(f"Pairwise exchange symmetry violation: ||K(A,B) - K(B,A)||_inf = {sym_err:.3e} > {tol:.3e}")

    if grouped_aggregator_fn is not None:
        same_group_leakage = abs(_finite_float(_finite_call(grouped_aggregator_fn, [sample_a, sample_b], [0, 0])))
        distinct_group_signal = abs(_finite_float(_finite_call(grouped_aggregator_fn, [sample_a, sample_b], [0, 1])))
        if same_group_leakage > tol:
            violations.append(
                f"Intra-group self-interaction leakage: grouped_aggregator([A,B], group_ids=[0,0]) = {same_group_leakage:.4e} != 0"
            )
        if distinct_group_signal <= tol:
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
    Asymmetric Rank-1 Product Null-Model Zero-Point Calibration Gate (`G3j`):
    1. Verifies Euler homogeneity of degree `k` across multi-decade positive scale factors `lambda > 0`,
       exposing hardcoded unscaled cutoffs (`x >= c`) or additive biases in dimensionless/homogeneous operators.
    2. When `rank1_null_input_builder_fn(p)` and `null_metric_extractor_fn(out)` are provided, verifies that
       independent rank-1 outer-product distributions `P = p * p^T` yield strictly zero correlation/order
       across ALL asymmetric marginals `p in (0, 1)`, catching hardcoded symmetric `0.50` baselines.
    """
    x_arr = _finite_array(base_input, dtype=np.float64)
    base_out = _extract_array(_finite_call(target_fn, x_arr.copy()))
    max_homog_err = 0.0
    violations: List[str] = []

    for lam in scale_factors:
        scaled_out = _extract_array(_finite_call(target_fn, (_finite_float(lam) * x_arr).copy()))
        expected_out = (_finite_float(lam) ** _finite_float(homogeneity_degree)) * base_out
        err = _finite_float(np.max(np.abs(scaled_out - expected_out)))
        if err > max_homog_err:
            max_homog_err = err
    if max_homog_err > tol:
        violations.append(
            f"Euler scale-homogeneity violation (degree k={homogeneity_degree}): max ||f(lam*x) - lam^k f(x)||_inf = {max_homog_err:.3e} > {tol:.3e}"
        )

    max_null_err = 0.0
    if rank1_null_input_builder_fn is not None and null_metric_extractor_fn is not None:
        for p_val in asymmetric_marginals:
            null_in = _finite_call(rank1_null_input_builder_fn, _finite_float(p_val))
            null_val = abs(_finite_float(_finite_call(null_metric_extractor_fn, _finite_call(target_fn, null_in))))
            if null_val > max_null_err:
                max_null_err = null_val
        if max_null_err > tol:
            violations.append(
                f"Asymmetric rank-1 independence null-model zero-point violation: max |metric(p*p^T)| = {max_null_err:.4e} > {tol:.3e}"
            )

    return {
        "status": "PASS" if not violations else "FAIL",
        "homogeneity_degree": _finite_float(homogeneity_degree),
        "max_scale_homogeneity_err": round(max_homog_err, 12),
        "max_rank1_null_calibration_err": round(max_null_err, 12),
        "violations": violations,
    }
