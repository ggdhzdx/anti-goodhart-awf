"""AWF Guard scientific computing pack: cohesive definitions behind the compatibility interface."""
from __future__ import annotations

from typing import Any
from typing import Callable
from typing import Dict
import ast
from awf_universal_anti_goodhart_gates import detect_extensional_enumeration_and_dispatch
from awf_universal_anti_goodhart_gates import evaluate_adaptive_runtime_budget
import numpy as np
from awf_universal_anti_goodhart_gates import verify_analytic_gradient_finite_difference
from awf_universal_anti_goodhart_gates import verify_asymptotic_convergence_order
from awf_universal_anti_goodhart_gates import verify_physical_matrix_invariants_and_unit_homogeneity
from awf_universal_anti_goodhart_gates import verify_se3_pbc_and_permutation_equivariance


def _verify_scientific_computing_pack_selftests(
    r_grid: np.ndarray,
    f_vals: np.ndarray,
    fast_spherical_integral: Callable[..., Any],
) -> Dict[str, Any]:
    # 1. IUPAC Periodic-Table Exemption & Adaptive Runtime Budget
    periodic_src = (
        "COVALENT_RADII = {'H': 0.31, 'C': 0.76, 'N': 0.71, 'O': 0.66, 'Si': 1.11, 'P': 1.07, 'S': 1.05}\n"
        "def get_covalent_radius(symbol):\n"
        "    return COVALENT_RADII[symbol]\n"
    )
    assert len(detect_extensional_enumeration_and_dispatch(ast.parse(periodic_src))) == 0
    budget_res = evaluate_adaptive_runtime_budget(
        fast_spherical_integral,
        {"r": r_grid, "f": f_vals, "use_mask": True},
    )
    assert budget_res["budget_tier"] in ("fast_in_memory", "moderate_kernel")

    # 2. Gate G2b: Analytic Force/Gradient vs 4th-Order Richardson Central Finite Difference
    def anharmonic_energy(coords: np.ndarray) -> float:
        r2 = np.sum(coords ** 2, axis=-1)
        return float(np.sum(0.5 * 2.5 * r2 + 0.25 * 0.8 * (r2 ** 2)))

    def honest_anharmonic_force(coords: np.ndarray) -> np.ndarray:
        r2 = np.sum(coords ** 2, axis=-1, keepdims=True)
        return -(2.5 * coords + 0.8 * r2 * coords)

    def buggy_wrong_sign_force(coords: np.ndarray) -> np.ndarray:
        r2 = np.sum(coords ** 2, axis=-1, keepdims=True)
        return 2.5 * coords + 0.8 * r2 * coords

    sample_pos = np.array([[0.3, -0.4, 0.5], [-0.2, 0.6, -0.1]], dtype=np.float64)
    fd_bad = verify_analytic_gradient_finite_difference(
        energy_fn=anharmonic_energy,
        force_or_grad_fn=buggy_wrong_sign_force,
        sample_input_kwargs={"coords": sample_pos},
        coord_arg="coords",
    )
    assert fd_bad["status"] == "FAIL" and fd_bad["sign_flipped"] is True
    fd_good = verify_analytic_gradient_finite_difference(
        energy_fn=anharmonic_energy,
        force_or_grad_fn=honest_anharmonic_force,
        sample_input_kwargs={"coords": sample_pos},
        coord_arg="coords",
    )
    assert fd_good["status"] == "PASS" and fd_good["max_abs_err"] < 1e-9

    # 3. Gate G1d: Asymptotic Convergence Order O(h^p) Verification
    exact_val = float(1.0 - np.cos(1.0))

    def honest_trapezoid_sin(h: float) -> float:
        n_pts = int(round(1.0 / h))
        xs = np.linspace(0.0, 1.0, n_pts + 1)
        ys = np.sin(xs)
        return float(h * (0.5 * ys[0] + np.sum(ys[1:-1]) + 0.5 * ys[-1]))

    def fake_first_order_euler_sin(h: float) -> float:
        n_pts = int(round(1.0 / h))
        xs = np.linspace(0.0, 1.0 - h, n_pts)
        return float(h * np.sum(np.sin(xs)))

    co_bad = verify_asymptotic_convergence_order(
        solver_fn=fake_first_order_euler_sin,
        exact_or_fine_ref=exact_val,
        resolution_steps=(0.1, 0.05, 0.025),
        step_kwarg="h",
        expected_order=2.0,
    )
    assert co_bad["status"] == "FAIL" and co_bad["empirical_order"] < 1.3
    co_good = verify_asymptotic_convergence_order(
        solver_fn=honest_trapezoid_sin,
        exact_or_fine_ref=exact_val,
        resolution_steps=(0.1, 0.05, 0.025),
        step_kwarg="h",
        expected_order=2.0,
    )
    assert co_good["status"] == "PASS" and co_good["empirical_order"] > 1.95

    # 4. Gate G3i: 3D SE(3) Rotation/Translation + Triclinic PBC Minimum-Image + S_N Permutation
    triclinic_cell = np.array([[4.0, 0.0, 0.0], [0.8, 4.2, 0.0], [0.4, 0.5, 4.5]], dtype=np.float64)
    pbc_coords = np.array([[0.2, 0.3, 0.4], [3.8, 0.4, 0.5], [1.5, 2.1, 1.8]], dtype=np.float64)

    def honest_triclinic_mic_energy(coords: np.ndarray, cell: np.ndarray) -> float:
        diff = coords[:, None, :] - coords[None, :, :]
        frac = np.linalg.solve(cell.T, diff.reshape(-1, 3).T).T.reshape(diff.shape)
        frac = frac - np.round(frac)
        cart = frac @ cell
        dist2 = np.sum(cart ** 2, axis=-1)
        mask = 1.0 - np.eye(coords.shape[0])
        return float(0.5 * np.sum(mask * np.exp(-0.5 * dist2)))

    def broken_non_pbc_energy(coords: np.ndarray, cell: np.ndarray) -> float:
        diff = coords[:, None, :] - coords[None, :, :]
        dist2 = np.sum((diff + 0.0 * cell[0, 0]) ** 2, axis=-1)
        mask = 1.0 - np.eye(coords.shape[0])
        return float(0.5 * np.sum(mask * np.exp(-0.5 * dist2)))

    eq_bad = verify_se3_pbc_and_permutation_equivariance(
        target_fn=broken_non_pbc_energy,
        coords=pbc_coords,
        cell=triclinic_cell,
        output_tensor_rank=0,
    )
    assert eq_bad["status"] == "FAIL" and eq_bad["pbc_lattice_shift_err"] > 1e-2

    # 5. Gate G5m: Physical Matrix Hermiticity / PSD / Detailed Balance & Cross-Atom Unit Homogeneity
    p_eq = np.array([0.5, 0.3, 0.2], dtype=np.float64)
    k_rate = np.array([
        [-0.5, 0.5, 0.5],
        [0.3, -0.9, 0.6],
        [0.2, 0.4, -1.1],
    ], dtype=np.float64)
    mat_bad = verify_physical_matrix_invariants_and_unit_homogeneity(
        matrix=np.array([[1.0, 2.0], [0.5, 1.0]]),
        require_hermitian=True,
    )
    assert mat_bad["status"] == "FAIL" and len(mat_bad["matrix_violations"]) >= 1

    return {
        "gradient_fd_spec": {
            "energy_fn": anharmonic_energy,
            "force_or_grad_fn": honest_anharmonic_force,
            "sample_input_kwargs": {"coords": sample_pos},
            "coord_arg": "coords",
        },
        "convergence_order_spec": {
            "solver_fn": honest_trapezoid_sin,
            "exact_or_fine_ref": exact_val,
            "resolution_steps": (0.1, 0.05, 0.025),
            "step_kwarg": "h",
            "expected_order": 2.0,
        },
        "se3_pbc_perm_spec": {
            "target_fn": honest_triclinic_mic_energy,
            "coords": pbc_coords,
            "cell": triclinic_cell,
            "output_tensor_rank": 0,
        },
        "matrix_and_unit_spec": {
            "matrix": k_rate,
            "require_hermitian": False,
            "require_psd": False,
            "require_rate_conservation": True,
            "equilibrium_populations": p_eq,
        },
    }
