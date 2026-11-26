"""Positive scenarios grouped by functional responsibility."""
from __future__ import annotations
from typing import Any
from typing import Dict
import numpy as np
from awf_universal_anti_goodhart_gates import verify_weighted_dispersion_kish_and_scale_invariance

def _verify_statistical_checks() -> Dict[str, Any]:

    def _kish_disp_fn(vals: np.ndarray, weights: np.ndarray) -> np.ndarray:
        wn = weights / float(np.sum(weights))
        mu = float(np.sum(wn * vals))
        eff_n = 1.0 / float(np.sum(wn ** 2))
        var = float(np.sum(wn * (vals - mu) ** 2)) * (eff_n / (eff_n - 1.0))
        sd = float(np.sqrt(var))
        g_raw = sd / mu * 100.0
        return np.array([mu, sd, g_raw, g_raw / float(np.sqrt(2.0 * np.pi))], dtype=np.float64)
    g5s_spec = {'dispersion_fn': _kish_disp_fn, 'base_input_kwargs': {'vals': np.array([3.45, 3.5, 3.55, 3.6], dtype=np.float64), 'weights': np.array([1.0, 1.0, 1.0, 1.0], dtype=np.float64)}, 'scaled_arg_name': 'vals', 'zero_weight_padded_kwargs': {'vals': np.array([3.45, 3.5, 3.55, 3.6, 25.0, 50.0], dtype=np.float64), 'weights': np.array([1.0, 1.0, 1.0, 1.0, 0.0, 0.0], dtype=np.float64)}}
    assert verify_weighted_dispersion_kish_and_scale_invariance(**g5s_spec)['status'] == 'PASS'
    return {'weighted_dispersion_kish_spec': g5s_spec}
