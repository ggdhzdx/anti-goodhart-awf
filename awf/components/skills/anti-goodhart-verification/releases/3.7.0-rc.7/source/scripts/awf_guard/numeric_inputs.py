"""AWF Guard: numeric inputs."""
from __future__ import annotations

from typing import Any
from typing import Dict
from awf_guard_numeric_contracts import finite_array as _finite_array
from awf_guard_numeric_contracts import require_finite as _require_finite
import numpy as np
from .tensor_contracts import QuantityTensor


def _extract_array(output: Any) -> np.ndarray:
    _require_finite(output, "operator output")
    if isinstance(output, QuantityTensor):
        return _finite_array(output.data, dtype=np.float64)
    if isinstance(output, np.ndarray):
        return output.astype(np.float64)
    if isinstance(output, (tuple, list)) and len(output) > 0:
        return _finite_array(output[0], dtype=np.float64)
    if isinstance(output, dict) and len(output) > 0:
        first_key = next(iter(output))
        return _finite_array(output[first_key], dtype=np.float64)
    return _finite_array(output, dtype=np.float64)


def _kwargs_materially_differ(kw_a: Dict[str, Any], kw_b: Dict[str, Any]) -> bool:
    """True when two probe kwarg dicts differ in keys or in any value (arrays compared element-wise)."""
    if set(kw_a) != set(kw_b):
        return True
    for key in kw_a:
        va, vb = kw_a[key], kw_b[key]
        if callable(va) or callable(vb):
            if va is not vb:
                return True
            continue
        try:
            a_arr, b_arr = _finite_array(va), _finite_array(vb)
            same = a_arr.shape == b_arr.shape and bool(np.array_equal(a_arr, b_arr))
        except (ValueError, TypeError):
            same = repr(va) == repr(vb)
        if not same:
            return True
    return False
