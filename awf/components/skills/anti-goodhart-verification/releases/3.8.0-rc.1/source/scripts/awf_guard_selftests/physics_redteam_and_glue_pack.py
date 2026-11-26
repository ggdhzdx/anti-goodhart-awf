"""AWF Guard selftests: model-physics sensitivity, periodic unit-cell gauge, feature variance, outer glue & dual-entry red-team."""
from __future__ import annotations

from typing import Any, Dict
import numpy as np
from awf_universal_anti_goodhart_gates import (
    audit_outer_glue_and_single_source_ast,
    extract_stripped_ast_physics_card,
    verify_crosstable_physical_inequality_bounds,
    verify_dual_entry_physics_redteam_audit,
    verify_dynamic_feature_variance_and_noncollinearity,
    verify_subfragment_spin_and_siteslip_sensitivity,
    verify_unitcell_cyclic_shift_and_chain_convergence,
)


def _pair_anisotropic_operator(fa: np.ndarray, fb: np.ndarray) -> float:
    """SE(3)-invariant dipole-dipole + pairwise orientation energy sensitive to spin and site slip."""
    ca = np.mean(fa, axis=0)
    cb = np.mean(fb, axis=0)
    da = fa[1] - fa[0]
    db = fb[1] - fb[0]
    r_vec = cb - ca
    r_norm = float(np.linalg.norm(r_vec))
    u_a = da / max(float(np.linalg.norm(da)), 1e-12)
    u_b = db / max(float(np.linalg.norm(db)), 1e-12)
    r_hat = r_vec / max(r_norm, 1e-12)
    orient = float(np.dot(u_a, u_b)) - 3.0 * float(np.dot(u_a, r_hat)) * float(np.dot(u_b, r_hat))
    d_end = float(np.linalg.norm(fa[-1] - fb[0]))
    return orient / max(r_norm ** 2, 1e-6) + 0.5 / max(d_end, 1e-6)


def _cyclic_unit_observable(window: np.ndarray) -> float:
    """Periodic ring observable invariant under cyclic window shift and head-tail reversal."""
    arr = np.asarray(window, dtype=np.float64)
    nxt = np.roll(arr, -1)
    return float(np.sum(arr * nxt) + 0.25 * np.sum(arr ** 2))


def _verify_physics_redteam_and_glue_selftests() -> Dict[str, Any]:
    """Verify v3.8.0-rc.1 Model-Physics Red-Team & Outer-Glue Closure Pack (G4d, G3m, G1f, G5u, G6q, G7j)."""
    # 1. G4d: Genuine dynamic features with physical variance and non-collinearity
    features = np.array([
        [4.1, 0.22, -0.15],
        [4.8, 0.31, -0.05],
        [5.4, 0.18, 0.14],
        [4.3, 0.27, 0.08],
        [5.9, 0.35, -0.21],
    ], dtype=np.float64)
    g4d_spec = {
        "feature_matrix": features,
        "feature_names": ["r_min_A", "solv_eV", "tilt_cos"],
        "min_cv_floor": 0.005,
        "min_std_floor": 1e-6,
        "max_abs_corr": 0.98,
    }
    assert verify_dynamic_feature_variance_and_noncollinearity(**g4d_spec)["status"] == "PASS"

    # 2. G3m: Global SE(3)-invariant pair operator with genuine spin & tangential slip response
    frag_a = np.array([[0.0, 0.0, 0.0], [1.4, 0.3, 0.0], [2.5, -0.4, 0.2]], dtype=np.float64)
    frag_b = np.array([[4.2, 0.1, 0.5], [5.5, 1.1, 0.8], [6.4, -0.3, 1.2]], dtype=np.float64)
    g3m_spec = {
        "pair_energy_fn": _pair_anisotropic_operator,
        "frag_a_coords": frag_a,
        "frag_b_coords": frag_b,
        "global_se3_tol": 1e-6,
        "min_spin_delta": 1e-3,
        "min_slip_delta": 1e-3,
    }
    assert verify_subfragment_spin_and_siteslip_sensitivity(**g3m_spec)["status"] == "PASS"

    # 3. G1f: Periodic cyclic-shift + reversal invariant window & asymptotically converging chain N -> 2N -> 4N
    base_win = np.array([1.2, 0.7, 1.8, 0.9], dtype=np.float64)
    g1f_spec = {
        "window_observable_fn": _cyclic_unit_observable,
        "cyclic_unit_windows": [base_win, np.roll(base_win, 1), np.roll(base_win, 2)],
        "reversed_unit_windows": [base_win[::-1], np.roll(base_win[::-1], 1)],
        "chain_sizes": [1, 2, 4, 8],
        "chain_observables": [1.500, 1.620, 1.660, 1.662],
        "gauge_tol": 1e-6,
        "asymptotic_tol": 5e-3,
    }
    assert verify_unitcell_cyclic_shift_and_chain_convergence(**g1f_spec)["status"] == "PASS"

    # 4. G5u: Cross-table physical / thermodynamic detailed-balance bound satisfied
    g5u_spec = {
        "observables": {"G_CT_eV": 1.48, "q_Voc_exp_eV": 0.912, "dE1_rad_eV": 0.24, "dE3_nonrad_eV": 0.22},
        "inequality_specs": [{
            "bound_id": "detailed_balance_Voc_ceiling",
            "lhs_terms": {"G_CT_eV": 1.0},
            "rhs_terms": {"q_Voc_exp_eV": 1.0, "dE1_rad_eV": 1.0, "dE3_nonrad_eV": 1.0},
            "relation": ">=",
            "slack_tol": 1e-3,
            "rationale": "CT free energy must exceed qVoc + radiative + nonradiative losses",
        }],
        "max_allowed_slack": 1e-2,
    }
    assert verify_crosstable_physical_inequality_bounds(**g5u_spec)["status"] == "PASS"

    # 5. G6q: Clean @scientific_atom capsule + thin orchestrator importing single-source physics helper
    clean_outer = (
        "from shared_physics import build_joint_descriptor\n\n"
        "@scientific_atom\n"
        "def eval_pair_energy(fa, fb):\n"
        "    vec = build_joint_descriptor(fa, fb)\n"
        "    return vec['energy']\n\n"
        "def run_pipeline(frames):\n"
        "    return [eval_pair_energy(f['a'], f['b']) for f in frames]\n"
    )
    companion = {
        "station_next.py": "from shared_physics import build_joint_descriptor\n\ndef summarize(fa, fb):\n    return build_joint_descriptor(fa, fb)\n"
    }
    g6q_spec = {
        "outer_source_code": clean_outer,
        "companion_sources": companion,
    }
    assert audit_outer_glue_and_single_source_ast(**g6q_spec)["status"] == "PASS"

    # 6. G7j: Dual-entry pre_code & post_hoc_audit (docstring stripped card matches executable AST)
    post_hoc_src = (
        "# outer solver\n"
        "def compute_anisotropic_field(r_sep, q_sub, dip_vec):\n"
        "    \"\"\"Uses distributed q_sub and dip_vec coupling.\"\"\"\n"
        "    field = q_sub / r_sep + dip_vec / (r_sep ** 2)\n"
        "    return field\n"
    )
    card = extract_stripped_ast_physics_card(post_hoc_src)
    assert card["function_count"] == 1 and "q_sub / r_sep" in card["executable_expressions_joined"]
    assert "outer solver" not in card["executable_expressions_joined"]
    g7j_post = verify_dual_entry_physics_redteam_audit({
        "mode": "post_hoc_audit",
        "author_id": "builder_agent",
        "reviewer_id": "independent_physics_redteam",
        "critique_axes_checked": [
            "sub_fragment_symmetry_and_multipole",
            "periodic_boundary_and_size_convergence",
            "functional_environment_and_thermodynamic_bounds",
            "cross_station_shared_observable_lock",
        ],
        "identified_risks_and_remediations": [
            {"axis": "sub_fragment_symmetry_and_multipole", "risk": "zeroed subring charges", "remediation_or_gate": "G3m spin/slip probe", "resolved": True},
            {"axis": "functional_environment_and_thermodynamic_bounds", "risk": "missing Voc bound", "remediation_or_gate": "G5u detailed-balance bound", "resolved": True},
        ],
        "target_source_code": post_hoc_src,
        "claimed_mechanisms": [{"claim_id": "dist_field", "required_ast_tokens": ["q_sub", "dip_vec"], "forbidden_ast_tokens": ["0.12"]}],
        "post_hoc_probe_verdicts": {"G3m": "PASS", "G5u": "PASS"},
    })
    assert g7j_post["status"] == "PASS"

    g7j_spec = {
        "redteam_spec": {
            "mode": "pre_code",
            "author_id": "builder_agent",
            "reviewer_id": "independent_physics_redteam",
            "pre_existing_code_present": False,
            "design_timestamp_epoch": 100.0,
            "implementation_start_epoch": 200.0,
            "critique_axes_checked": [
                "sub_fragment_symmetry_and_multipole",
                "periodic_boundary_and_size_convergence",
                "functional_environment_and_thermodynamic_bounds",
                "cross_station_shared_observable_lock",
            ],
            "approximation_ledger": [
                {"assumption": "distributed sub-ring RESP charges on DFT geometry", "domain": "weak-coupling non-covalent pairs"},
            ],
            "identified_risks_and_remediations": [
                {"axis": "sub_fragment_symmetry_and_multipole", "risk": "center-distance collapse", "remediation_or_gate": "enforce G3m spin+slip probe", "resolved": True},
                {"axis": "periodic_boundary_and_size_convergence", "risk": "unit-cell boundary cut", "remediation_or_gate": "enforce G1f cyclic shift", "resolved": True},
            ],
        }
    }
    assert verify_dual_entry_physics_redteam_audit(**g7j_spec)["status"] == "PASS"

    return {
        "dynamic_feature_variance_spec": g4d_spec,
        "subfragment_spin_and_slip_spec": g3m_spec,
        "unitcell_gauge_and_chain_spec": g1f_spec,
        "crosstable_physical_bounds_spec": g5u_spec,
        "outer_glue_and_single_source_spec": g6q_spec,
        "dual_entry_physics_redteam_spec": g7j_spec,
    }
