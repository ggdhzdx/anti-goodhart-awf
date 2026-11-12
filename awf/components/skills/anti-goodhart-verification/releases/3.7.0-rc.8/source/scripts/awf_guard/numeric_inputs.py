"""AWF Guard: numeric inputs."""
from __future__ import annotations

import dis
import inspect
from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional
from awf_guard_numeric_contracts import finite_array as _finite_array
from awf_guard_numeric_contracts import require_finite as _require_finite
import numpy as np
from .tensor_contracts import QuantityTensor

_MIN_MATERIAL_KWARG_DIFF = 1e-12


def _coerce_leaf_array(value: Any) -> np.ndarray:
    target_dtype = np.complex128 if np.iscomplexobj(value) else np.float64
    return _finite_array(value, dtype=target_dtype)


def _extract_array(output: Any) -> np.ndarray:
    _require_finite(output, "operator output")
    if isinstance(output, QuantityTensor):
        return _coerce_leaf_array(output.data)
    if isinstance(output, np.ndarray):
        return _coerce_leaf_array(output)
    if isinstance(output, (tuple, list)):
        if len(output) == 0:
            raise ValueError("Empty sequence operator output cannot be verified")
        if len(output) == 1:
            return _extract_array(output[0])
        leaves: List[np.ndarray] = [_extract_array(item) for item in output]
        first_shape = leaves[0].shape
        if all(leaf.shape == first_shape for leaf in leaves):
            stacked = np.stack(leaves, axis=0)
            return stacked.reshape(-1) if first_shape == () else stacked
        return np.concatenate([leaf.reshape(-1) for leaf in leaves])
    if isinstance(output, dict):
        if len(output) == 0:
            raise ValueError("Empty mapping operator output cannot be verified")
        ordered_keys = sorted(output.keys(), key=str)
        if len(ordered_keys) == 1:
            return _extract_array(output[ordered_keys[0]])
        return np.concatenate([_extract_array(output[k]).reshape(-1) for k in ordered_keys])
    return _coerce_leaf_array(output)


def _code_loads_varname(code_obj: Any, varname: str) -> bool:
    for instr in dis.get_instructions(code_obj):
        if instr.opname.startswith("LOAD_") and instr.argval == varname:
            return True
    for const in getattr(code_obj, "co_consts", ()):
        if hasattr(const, "co_code") and _code_loads_varname(const, varname):
            return True
    return False


def _kwargs_materially_differ(
    kw_a: Dict[str, Any],
    kw_b: Dict[str, Any],
    target_fn: Optional[Callable[..., Any]] = None,
) -> bool:
    """True when two probe kwarg dicts differ materially in accepted parameters (rejecting 1-ULP & unused-varkw spoofing)."""
    if not isinstance(kw_a, dict) or not isinstance(kw_b, dict):
        return False
    if target_fn is not None and callable(target_fn):
        try:
            sig = inspect.signature(target_fn)
            varkw_params = [p.name for p in sig.parameters.values() if p.kind == inspect.Parameter.VAR_KEYWORD]
            explicit_params = {
                name
                for name, p in sig.parameters.items()
                if p.kind in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY)
            }
            if varkw_params:
                unwrapped = inspect.unwrap(target_fn)
                code_obj = getattr(unwrapped, "__code__", None)
                varkw_used = True if code_obj is None else _code_loads_varname(code_obj, varkw_params[0])
                allowed_keys = (explicit_params | (set(kw_a) & set(kw_b))) if varkw_used else explicit_params
                kw_a = {k: v for k, v in kw_a.items() if k in allowed_keys}
                kw_b = {k: v for k, v in kw_b.items() if k in allowed_keys}
        except (TypeError, ValueError):
            sig = None
    if set(kw_a) != set(kw_b):
        return True
    for key in kw_a:
        va, vb = kw_a[key], kw_b[key]
        if type(va) is bool or type(vb) is bool:
            if va != vb:
                return True
            continue
        if callable(va) or callable(vb):
            if va is not vb:
                return True
            continue
        raw_a = va.data if isinstance(va, QuantityTensor) else va
        raw_b = vb.data if isinstance(vb, QuantityTensor) else vb
        if isinstance(va, QuantityTensor) and isinstance(vb, QuantityTensor) and va.unit != vb.unit:
            return True
        try:
            a_arr, b_arr = _coerce_leaf_array(raw_a), _coerce_leaf_array(raw_b)
            if a_arr.shape != b_arr.shape:
                return True
            if a_arr.size == 0:
                continue
            scale = max(float(np.max(np.abs(a_arr))), float(np.max(np.abs(b_arr))), 1.0)
            max_diff = float(np.max(np.abs(a_arr - b_arr)))
            same = max_diff <= _MIN_MATERIAL_KWARG_DIFF * scale
        except (ValueError, TypeError):
            same = repr(va) == repr(vb)
        if not same:
            return True
    return False
