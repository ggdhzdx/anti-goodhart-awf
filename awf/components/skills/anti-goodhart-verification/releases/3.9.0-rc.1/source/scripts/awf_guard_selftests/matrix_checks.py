"""Positive scenarios grouped by functional responsibility."""
from __future__ import annotations
from typing import Any
from typing import Dict
import numpy as np
from awf_universal_anti_goodhart_gates import verify_nonorthogonal_pencil_gauge_and_spectral_parity

def _verify_matrix_checks() -> Dict[str, Any]:

    def _toy_diabat_fn(s_mat: np.ndarray, f_mat: np.ndarray, j_coul: np.ndarray) -> np.ndarray:
        ev, u = np.linalg.eigh(s_mat)
        s_ih = u / np.sqrt(ev) @ u.T
        f_eff = s_ih @ f_mat @ s_ih
        t_sub = f_eff[0:2, 2:4]
        j_val = float(j_coul[0, 0]) * 1000.0
        return np.array([abs(float(t_sub[1, 1])), float(np.linalg.norm(t_sub)), 0.1, 0.25, j_val, -j_val], dtype=np.float64)
    s_toy = np.array([[1.0, 0.0, 0.05, -0.02], [0.0, 1.0, 0.03, 0.04], [0.05, 0.03, 1.0, 0.0], [-0.02, 0.04, 0.0, 1.0]])
    f_toy = np.array([[-8.0, 0.0, 0.12, -0.08], [0.0, -7.5, 0.09, 0.15], [0.12, 0.09, -8.0, 0.0], [-0.08, 0.15, 0.0, -7.5]])
    j_toy = np.array([[-0.02, 0.0], [0.0, -0.01]])
    g5t_spec = {'diabat_fn': _toy_diabat_fn, 'base_input_kwargs': {'s_mat': s_toy, 'f_mat': f_toy, 'j_coul': j_toy}, 'operator_metric_pairs': (('f_mat', 's_mat'),), 'bipolar_coupling_arg': 'j_coul', 'pure_dipolar_base_kwargs': {'s_mat': np.eye(4), 'f_mat': np.diag([-8.0, -7.5, -8.0, -7.5]), 'j_coul': j_toy}}
    assert verify_nonorthogonal_pencil_gauge_and_spectral_parity(**g5t_spec)['status'] == 'PASS'
    return {'nonorthogonal_pencil_gauge_spec': g5t_spec}
