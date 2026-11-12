"""AWF Guard calibrated scientific pack v34: cohesive definitions behind the compatibility interface."""
from __future__ import annotations

from typing import Any
from typing import Dict
from typing import List
import numpy as np
from awf_universal_anti_goodhart_gates import verify_bipolar_reachability_and_multisource_variance
from awf_universal_anti_goodhart_gates import verify_loocv_generalization_and_train_eval_parity
from awf_universal_anti_goodhart_gates import verify_mesh_refinement_invariance_and_noise_floor
from awf_universal_anti_goodhart_gates import verify_pairwise_no_self_interaction_and_symmetry
from awf_universal_anti_goodhart_gates import verify_remediation_closed_loop_and_pareto_candidates
from awf_universal_anti_goodhart_gates import verify_scale_homogeneity_and_rank1_null_calibration
from .calibrated_morph_and_optics_pack import _verify_calibrated_morph_and_optics_pack_selftests


def _verify_calibrated_scientific_pack_v34_selftests() -> Dict[str, Any]:
    """Verify v3.4.0-rc.1 Calibrated Scientific Computing Pack (G5o, G7i, G3j, G6p, G5p)."""
    # 1. Gate G5o: Pairwise Exchange Symmetry & Intra-Group Self-Interaction Exclusion
    pts_a = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]])
    pts_b = np.array([[0.0, 0.0, 3.0], [1.0, 0.0, 3.0]])

    def sym_kernel(pa: np.ndarray, pb: np.ndarray) -> float:
        return float(np.exp(-np.linalg.norm(np.mean(pa, axis=0) - np.mean(pb, axis=0))))

    def group_agg(groups: List[np.ndarray], gids: List[int]) -> float:
        tot = 0.0
        for idx_i in range(len(groups)):
            for idx_j in range(idx_i + 1, len(groups)):
                if gids[idx_i] != gids[idx_j]:
                    tot += sym_kernel(groups[idx_i], groups[idx_j])
        return tot

    g5o_spec = {
        "pairwise_fn": sym_kernel,
        "sample_a": pts_a,
        "sample_b": pts_b,
        "grouped_aggregator_fn": group_agg,
    }
    assert verify_pairwise_no_self_interaction_and_symmetry(**g5o_spec)["status"] == "PASS"

    # 2. Gate G7i: Exact Hat-Matrix Leverage LOOCV & Train/Eval Feature-Extractor Parity
    x_feat = np.array([[1.0], [2.0], [3.0], [4.0], [5.0], [6.0]])
    y_targ = np.array([2.1, 3.9, 6.1, 8.0, 9.9, 12.1])
    g7i_spec = {
        "design_matrix": x_feat,
        "targets": y_targ,
        "min_loocv_r2": 0.90,
        "max_generalization_gap": 0.20,
        "calibrate_feature_fn": lambda arr: arr * 2.0,
        "eval_feature_fn": lambda arr: arr * 2.0,
        "parity_test_inputs": [np.array([1.0, 2.0]), np.array([3.0, 4.0])],
    }
    assert verify_loocv_generalization_and_train_eval_parity(**g7i_spec)["status"] == "PASS"

    # 3. Gate G3j: Euler Scale Homogeneity & Asymmetric Rank-1 Null Zero-Point Calibration
    g3j_spec = {
        "target_fn": lambda m: float(
            np.linalg.svd(m - np.outer(np.mean(m, axis=1), np.ones(m.shape[1])), compute_uv=False)[0]
        ),
        "base_input": np.array([[1.0, -1.0], [-1.0, 1.0]]),
        "homogeneity_degree": 1.0,
        "rank1_null_input_builder_fn": lambda p: np.outer(np.full(6, p), np.ones(6)),
        "null_metric_extractor_fn": lambda val: float(val),
    }
    assert verify_scale_homogeneity_and_rank1_null_calibration(**g3j_spec)["status"] == "PASS"

    # 4. Gate G6p: Autonomous Remediation Closed-Loop & Pareto Multi-Candidate Selector
    pre_src = "def f(d, x):\n    if x > 0:\n        return d['a'] * x\n    return -d['a'] * x\n"
    post_src = "def f(d, x):\n    if x > 0:\n        return d['a'] * x * 1.0\n    return -d['a'] * x\n"
    g6p_spec = {
        "pre_fix_source": pre_src,
        "post_fix_source": post_src,
        "candidate_implementations": {
            "cand_bad": lambda x: x + 1.0,
            "cand_best": lambda x: x * 2.0,
        },
        "reference_oracle_fn": lambda x: x * 2.0,
        "evaluation_inputs": [{"x": np.array([1.0, 2.0])}, {"x": np.array([3.0, 4.0])}],
    }
    g6p_res = verify_remediation_closed_loop_and_pareto_candidates(**g6p_spec)
    assert g6p_res["status"] == "PASS" and g6p_res["selected_pareto_candidate"] == "cand_best"

    # 5. Gate G5p: Bipolar Sign Reachability & Multi-Source Delta-Method Variance Propagation
    g5p_spec = {
        "signed_metric_fn": lambda x: float(x),
        "negative_regime_input": -2.5,
        "positive_regime_input": 3.2,
        "variance_propagator_fn": lambda v_obs, means, v_ref: float(v_obs + 0.25 * v_ref[0] + 0.25 * v_ref[1]),
        "baseline_fn": lambda theta: float(0.5 * theta[0] + 0.5 * theta[1]),
    }
    assert verify_bipolar_reachability_and_multisource_variance(**g5p_spec)["status"] == "PASS"

    # 6. Gate G1e: Mesh-Refinement Intensive Invariance & Infinitesimal Noise-Floor Stability
    g1e_spec = {
        "target_fn": lambda grid, h: float(np.sum(grid) * (h ** 2)),
        "resolution_input_builder_fn": lambda n_g: {
            "grid": np.ones((n_g, n_g), dtype=np.float64),
            "h": 4.0 / float(n_g),
        },
        "resolutions": (16, 32),
        "max_refinement_rel_drift": 1e-9,
        "noisy_null_input_kwargs": {"grid": np.full((16, 16), 1e-8, dtype=np.float64), "h": 0.25},
        "expected_null_output": 0.0,
        "noise_floor_tol": 1e-6,
    }
    assert verify_mesh_refinement_invariance_and_noise_floor(**g1e_spec)["status"] == "PASS"

    out = {
        "pairwise_self_interaction_spec": g5o_spec,
        "loocv_and_parity_spec": g7i_spec,
        "scale_homogeneity_and_null_spec": g3j_spec,
        "remediation_closed_loop_spec": g6p_spec,
        "bipolar_and_variance_spec": g5p_spec,
        "mesh_refinement_and_noise_spec": g1e_spec,
    }
    out.update(_verify_calibrated_morph_and_optics_pack_selftests())
    return out
