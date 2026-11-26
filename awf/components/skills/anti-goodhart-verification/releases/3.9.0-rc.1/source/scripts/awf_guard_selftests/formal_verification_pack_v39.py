"""AWF Guard selftests: v3.9.0-rc.1 Formal & Certified Verification Pack (G3o, G5v, G1g, G3n, G2c, G5w)."""
from __future__ import annotations

from typing import Any, Dict
import numpy as np

from awf_universal_anti_goodhart_gates import (
    AtomicContractViolationError,
    GLOBAL_ATOM_REGISTRY,
    QuantityTensor,
    TensorSpec,
    scientific_atom,
    verify_arb_ball_enclosure_and_conditioning,
    verify_hypothesis_lie_group_and_boundary_shrinking,
    verify_keymaerax_ode_invariants,
    verify_lean4_symbolic_proof_and_inhabitation,
    verify_pint_dimensional_homogeneity,
    verify_stoichiometry_spin_and_wegscheider_smt,
)


def _spd_linear_solver(a_mat: np.ndarray, b_vec: np.ndarray) -> np.ndarray:
    return np.linalg.solve(a_mat, b_vec)


def _shifted_boltzmann_free_energy_and_probs(energies: np.ndarray, beta: float) -> np.ndarray:
    e_flat = np.asarray(energies, dtype=np.float64).reshape(-1)
    e_min = float(np.min(e_flat))
    weights = np.exp(-float(beta) * (e_flat - e_min))
    z_sum = float(np.sum(weights))
    f_val = e_min - float(np.log(z_sum)) / float(beta)
    probs = weights / z_sum
    return np.concatenate(([f_val], probs))


def _morse_cluster_energy(coords: np.ndarray) -> float:
    pos = np.asarray(coords, dtype=np.float64)
    diff = pos[:, None, :] - pos[None, :, :]
    n_atoms = pos.shape[0]
    iu = np.triu_indices(n_atoms, k=1)
    dists = np.linalg.norm(diff[iu], axis=-1)
    u_pair = np.exp(-2.0 * (dists - 1.5)) - 2.0 * np.exp(-(dists - 1.5))
    return float(np.sum(u_pair))


def _gibbs_reaction_energy(dH: float, T: float, dS: float) -> float:
    return float(dH) - float(T) * float(dS)


def _verify_formal_verification_pack_v39_selftests() -> Dict[str, Any]:
    """Verify all 6 formal & certified verification capabilities (Pint, Z3+RDKit+SymPy, Arb, Hypothesis, Lean 4, KeYmaera X)."""
    # 1. G3o: Pint dimensional homogeneity + QuantityTensor scale-factor conversion guard
    atom_id = "ATOM-SELFTEST-PINT-BOLTZMANN-01"
    try:
        @scientific_atom(
            atom_id=atom_id,
            tutor_station="Station_Pint_Dimensional_Contract",
            math_contract="w = exp(-dE / eV_ref)",
            dimensional_law="exp(-dE / eV_ref)",
            inputs={
                "dE": TensorSpec(shape=(), unit="eV", auto_convert_unit=True),
                "eV_ref": TensorSpec(shape=(), unit="eV"),
            },
            outputs={"w": TensorSpec(shape=(), unit="dimensionless")},
        )
        def _boltzmann_factor_atom(dE: float, eV_ref: float) -> float:
            return float(np.exp(-dE / eV_ref))

        converted_out = _boltzmann_factor_atom(
            QuantityTensor(0.1, unit="hartree"),
            QuantityTensor(2.7211386245988, unit="eV"),
        )
        assert abs(float(converted_out) - float(np.exp(-1.0))) < 1e-6

        scale_blocked = False
        try:
            _boltzmann_factor_atom(
                QuantityTensor(0.1, unit="eV"),
                QuantityTensor(0.1, unit="hartree"),
            )
        except AtomicContractViolationError:
            scale_blocked = True
        assert scale_blocked
    finally:
        GLOBAL_ATOM_REGISTRY.pop(atom_id, None)

    g3o_spec = {
        "variable_units": {"dG": "kcal / mol", "T": "kelvin"},
        "dimensional_law": "exp(-dG / (R * T))",
        "expected_output_unit": "dimensionless",
        "unit_conversion_probes": [
            ("hartree", "eV", 27.211386245988),
            ("bohr", "angstrom", 0.529177210903),
        ],
        "rel_tol": 1e-6,
    }
    assert verify_pint_dimensional_homogeneity(**g3o_spec)["status"] == "PASS"

    # 2. G5v: Z3 + SymPy + RDKit stoichiometry, spin parity, Wegscheider cycle closure & Feinberg CRNT (delta=0)
    g5v_spec = {
        "species_defs": {
            "acetone": {"smiles": "CC(=O)C", "charge": 0, "spin_multiplicity": 1},
            "propanal": {"smiles": "CCC=O", "charge": 0, "spin_multiplicity": 1},
            "allyl_alcohol": {"smiles": "C=CCO", "charge": 0, "spin_multiplicity": 1},
        },
        "reactions": [
            {"id": "R1", "stoich": {"acetone": -1, "propanal": 1}},
            {"id": "R2", "stoich": {"propanal": -1, "allyl_alcohol": 1}},
            {"id": "R3", "stoich": {"allyl_alcohol": -1, "acetone": 1}},
        ],
        "reaction_dg0": [6.8, 7.4, -14.2],
        "reaction_barriers_fwd": [24.0, 28.5, 19.0],
        "claims_oscillation_or_bistability": False,
        "is_weakly_reversible": True,
        "wegscheider_tol": 1e-4,
    }
    g5v_res = verify_stoichiometry_spin_and_wegscheider_smt(**g5v_spec)
    assert g5v_res["status"] == "PASS" and g5v_res["crnt_deficiency"] == 0 and g5v_res["cycle_basis_count"] == 1

    # 3. G1g: Python-FLINT Arb 128-bit ball arithmetic (extreme Boltzmann shift & SPD linear solve)
    boltz_res = verify_arb_ball_enclosure_and_conditioning(
        target_fn=_shifted_boltzmann_free_energy_and_probs,
        sample_input_kwargs={"energies": np.array([900.0, 900.25, 901.0], dtype=np.float64), "beta": 2.0},
        arb_mode="logsumexp_boltzmann",
        precision_bits=128,
        max_ball_rel_radius=1e-14,
        float64_tol=1e-10,
    )
    assert boltz_res["status"] == "PASS"

    a_spd = np.array(
        [
            [4.2, -0.8, 0.3, 0.1],
            [-0.8, 3.9, -0.5, 0.2],
            [0.3, -0.5, 4.5, -0.4],
            [0.1, 0.2, -0.4, 3.7],
        ],
        dtype=np.float64,
    )
    b_rhs = np.array([1.5, -2.1, 0.9, 2.4], dtype=np.float64)
    g1g_spec = {
        "target_fn": _spd_linear_solver,
        "sample_input_kwargs": {"a_mat": a_spd, "b_vec": b_rhs},
        "arb_mode": "linear_solve",
        "precision_bits": 128,
        "max_ball_rel_radius": 1e-14,
        "float64_tol": 1e-10,
    }
    assert verify_arb_ball_enclosure_and_conditioning(**g1g_spec)["status"] == "PASS"

    # 4. G3n: Hypothesis deterministic Lie-group SE(3) x S_N & singular-angle (0, pi/2, pi) shrinking
    cluster_coords = np.array(
        [[0.0, 0.0, 0.0], [1.45, 0.15, -0.10], [0.65, 1.35, 0.25], [-0.40, 0.75, 1.20]],
        dtype=np.float64,
    )
    g3n_spec = {
        "target_fn": _morse_cluster_energy,
        "base_coords": cluster_coords,
        "coord_kwarg": "coords",
        "output_tensor_rank": 0,
        "max_examples": 20,
        "tol": 1e-8,
    }
    assert verify_hypothesis_lie_group_and_boundary_shrinking(**g3n_spec)["status"] == "PASS"

    # 5. G2c: Lean 4 kernel theorem + axiom whitelist + non-vacuous existential inhabitation witness + SymPy oracle
    lean_code = (
        "theorem wegscheider_three_step_cycle (gA gB gC : Int)\n"
        "    (hAB : gB - gA <= 100) (hBC : gC - gB <= 100) :\n"
        "    (gB - gA) + (gC - gB) + (gA - gC) = 0 := by\n"
        "  omega\n\n"
        "theorem wegscheider_three_step_inhabited :\n"
        "    ∃ (gA gB gC : Int), (gB - gA <= 100) ∧ (gC - gB <= 100) := by\n"
        "  exact ⟨0, 10, 25, by decide, by decide⟩\n"
    )
    g2c_spec = {
        "lean_source_code": lean_code,
        "theorem_name": "wegscheider_three_step_cycle",
        "expected_theorem_signature": "(gB - gA) + (gC - gB) + (gA - gC) = 0",
        "inhabitation_witness_name": "wegscheider_three_step_inhabited",
        "sympy_expr_str": "dH - T * dS",
        "target_fn": _gibbs_reaction_energy,
        "sample_points": [
            {"dH": -12.5, "T": 298.15, "dS": -0.025},
            {"dH": 8.4, "T": 450.0, "dS": 0.031},
        ],
        "oracle_tol": 1e-10,
    }
    assert verify_lean4_symbolic_proof_and_inhabitation(**g2c_spec)["status"] == "PASS"

    # 6. G5w: KeYmaera X differential dynamic logic (dL) ODE mass conservation + Z3 precondition SAT
    kyx_code = (
        'Theorem "First-Order Reaction Mass Conservation"\n'
        "Definitions\n"
        "  Real k;\n"
        "  Real c0;\n"
        "End.\n"
        "ProgramVariables\n"
        "  Real cA;\n"
        "  Real cB;\n"
        "End.\n"
        "Problem\n"
        "  k > 0 & c0 > 0 & cA = c0 & cB = 0\n"
        "  ->\n"
        "  [{cA' = -k*cA, cB' = k*cA & cA >= 0}] (cA + cB = c0)\n"
        "End.\n"
        'Tactic "Differential Invariant Proof"\n'
        "  implyR(1); dI(1)\n"
        "End.\n"
        "End.\n"
    )
    g5w_spec = {
        "kyx_model_code": kyx_code,
        "precondition_variables": {"k": "Real", "c0": "Real", "cA": "Real", "cB": "Real"},
        "precondition_smt2_assertions": ["(> k 0.0)", "(> c0 0.0)", "(= cA c0)", "(= cB 0.0)"],
        "expected_postcondition_fragment": "cA + cB = c0",
    }
    assert verify_keymaerax_ode_invariants(**g5w_spec)["status"] == "PASS"

    return {
        "pint_dimensional_homogeneity_spec": g3o_spec,
        "formal_chemistry_smt_spec": g5v_spec,
        "arb_ball_enclosure_spec": g1g_spec,
        "hypothesis_lie_shrinking_spec": g3n_spec,
        "lean4_symbolic_proof_spec": g2c_spec,
        "keymaerax_ode_safety_spec": g5w_spec,
    }
