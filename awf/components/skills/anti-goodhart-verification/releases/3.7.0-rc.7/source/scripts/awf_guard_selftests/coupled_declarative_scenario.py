"""Positive scenarios grouped by functional responsibility."""
from __future__ import annotations
from typing import Any
from typing import Dict
from awf_universal_anti_goodhart_gates import evaluate_universal_declarative_slots
import numpy as np
from awf_universal_anti_goodhart_gates import verify_coupled_basis_sign_gauge_and_locality_bounds

def _verify_coupled_declarative_scenario() -> Dict[str, Any]:

    def _toy_sr_fn(h_ex_ev: np.ndarray, mu_vecs_debye: np.ndarray, coords_ang: np.ndarray) -> np.ndarray:
        _, evecs = np.linalg.eigh(h_ex_ev[0:2, 0:2])
        c0 = evecs[:, 0]
        p0 = c0 ** 2
        pr0 = 1.0 / float(np.sum(p0 ** 2))
        m_sq = float(np.sum((c0 @ mu_vecs_debye[0:2]) ** 2))
        incoh = float(p0 @ np.sum(mu_vecs_debye[0:2] ** 2, axis=1))
        eta = m_sq / max(incoh, 1e-12)
        r_mean = p0 @ coords_ang[0:2]
        rg = float(np.sqrt(max(float(p0 @ np.sum((coords_ang[0:2] - r_mean) ** 2, axis=1)), 0.0)))
        return np.array([pr0, pr0, eta, 0.85 * eta, eta, rg], dtype=np.float64)
    h_sr = np.array([[1.8, -0.04, 1e-05, 0.0], [-0.04, 1.8, 0.0, 1e-05], [1e-05, 0.0, 1.8, -0.04], [0.0, 1e-05, -0.04, 1.8]])
    mu_sr = np.array([[10.0, 0.0, 0.0], [10.0, 0.0, 0.0], [10.0, 0.0, 0.0], [10.0, 0.0, 0.0]])
    c_sr1 = np.array([[0.0, 0.0, 0.0], [4.0, 0.0, 0.0], [40.0, 0.0, 0.0], [44.0, 0.0, 0.0]])
    c_sr2 = np.array([[0.0, 0.0, 0.0], [4.0, 0.0, 0.0], [90.0, 0.0, 0.0], [94.0, 0.0, 0.0]])
    g3l_spec = {'operator_fn': _toy_sr_fn, 'base_input_kwargs': {'h_ex_ev': h_sr, 'mu_vecs_debye': mu_sr, 'coords_ang': c_sr1}, 'separated_cluster_shifted_kwargs': {'h_ex_ev': h_sr, 'mu_vecs_debye': mu_sr, 'coords_ang': c_sr2}, 'max_cluster_size': 2}
    assert verify_coupled_basis_sign_gauge_and_locality_bounds(**g3l_spec)['status'] == 'PASS'
    univ_spec = {'operator_fn': _toy_sr_fn, 'base_input_kwargs': {'h_ex_ev': h_sr, 'mu_vecs_debye': mu_sr, 'coords_ang': c_sr1}, 'slot_laws': {'s1_1_regime_probes': [{'name': 'SeparatedClusterLocality', 'input_kwargs': {'h_ex_ev': h_sr, 'mu_vecs_debye': mu_sr, 'coords_ang': c_sr2}, 'predicate_fn': lambda out: bool(abs(float(out[5]) - 2.0) < 1e-06)}], 's3_1_equivariance_laws': [{'name': 'DipoleSignFlipGauge', 'transformed_kwargs': {'h_ex_ev': h_sr, 'mu_vecs_debye': -mu_sr, 'coords_ang': c_sr1}, 'mode': 'invariance', 'tol': 1e-10}], 's5_1_manifold_laws': [{'name': 'CauchySchwarzSuperRadianceBound', 'residual_fn': lambda out: float(np.maximum(0.0, out[2] - 2.0)), 'tol': 1e-09}]}}
    assert evaluate_universal_declarative_slots(**univ_spec)['status'] == 'PASS'
    return {'coupled_basis_sign_gauge_spec': g3l_spec, 'universal_slot_laws_spec': univ_spec}
