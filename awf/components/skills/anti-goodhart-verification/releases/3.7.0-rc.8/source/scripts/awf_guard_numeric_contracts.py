"""Finite numerical boundaries, without replacing or tracing user callbacks."""
from dataclasses import fields, is_dataclass
from functools import wraps
import inspect
import math
import numbers

import numpy as np


def require_finite(value, label="value", seen=None, allow_infinity=False):
    """Reject nonfinite numeric leaves; infinite TensorSpec bounds are deliberate."""
    if isinstance(value, (str, bytes, type)) or callable(value) or value is None:
        return
    if isinstance(value, numbers.Number):
        valid = not np.isnan(value) if allow_infinity else np.isfinite(value)
        if not valid:
            raise ValueError(f"Nonfinite numeric value at {label}")
        return
    if isinstance(value, np.ndarray) and value.dtype.kind in "biufc":
        valid = ~np.isnan(value) if allow_infinity else np.isfinite(value)
        if not np.all(valid):
            raise ValueError(f"Nonfinite numeric array at {label}")
        return
    visited = set() if seen is None else seen
    if id(value) in visited:
        return
    visited.add(id(value))
    if isinstance(value, dict):
        children = value.items()
    elif isinstance(value, (list, tuple, set, np.ndarray)):
        children = enumerate(value)
    elif hasattr(value, "data") and hasattr(value, "unit"):
        require_finite(getattr(value, "data"), f"{label}.data", visited, allow_infinity)
        return
    elif is_dataclass(value):
        for field in fields(value):
            bounds = type(value).__name__ == "TensorSpec" and field.name == "domain"
            require_finite(getattr(value, field.name), f"{label}.{field.name}", visited, bounds)
        return
    else:
        return
    for key, item in children:
        require_finite(item, f"{label}[{key}]", visited, allow_infinity)


def finite_array(*args, **kwargs):
    result = np.asarray(*args, **kwargs)
    require_finite(result, "array")
    return result


def finite_float(value=0):
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("Nonfinite scalar from numerical evaluation")
    return result


def finite_call(function, *args, **kwargs):
    result = function(*args, **kwargs)
    require_finite(result, "callback output")
    return result


def finite_inputs(function):
    signature = inspect.signature(function)

    @wraps(function)
    def checked(*args, **kwargs):
        bound = signature.bind(*args, **kwargs)
        bound.apply_defaults()
        require_finite(bound.arguments, function.__name__)
        return function(*args, **kwargs)

    return checked
