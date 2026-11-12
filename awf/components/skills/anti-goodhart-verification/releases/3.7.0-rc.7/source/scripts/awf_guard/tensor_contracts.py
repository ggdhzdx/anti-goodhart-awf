"""AWF Guard: tensor contracts."""
from __future__ import annotations

from typing import Any
from typing import Dict
from typing import Literal
from typing import Optional
from typing import Tuple
from typing import Union
from awf_guard_numeric_contracts import finite_array as _finite_array
from awf_guard_numeric_contracts import finite_float as _finite_float
from dataclasses import dataclass
import numpy as np
from .errors import AtomicContractViolationError
from .shape_contracts import check_jaxtyping_shape_contract
from .shape_contracts import parse_jaxtyping_shape_spec


def _validate_tensor_against_spec(
    name: str,
    val: Any,
    spec: TensorSpec,
    symbolic_dims: Dict[str, int],
    atom_id: str,
    direction: str,
    variadic_dims: Optional[Dict[str, Tuple[bool, Tuple[int, ...]]]] = None,
) -> np.ndarray:
    """Validate unit, jaxtyping symbolic/algebraic/variadic shape, NaN/Inf, domain bounds, and monotonicity."""
    if isinstance(val, QuantityTensor):
        if val.unit != spec.unit:
            raise AtomicContractViolationError(
                f"[{atom_id} {direction} Unit Mismatch] Parameter `{name}` expected unit "
                f"`{spec.unit}`, but received QuantityTensor with unit `{val.unit}`!"
            )
        arr = _finite_array(val.data, dtype=np.float64)
    else:
        arr = _finite_array(val, dtype=np.float64)

    check_jaxtyping_shape_contract(
        name=name,
        arr_shape=arr.shape,
        raw_spec_shape=spec.shape,
        symbolic_dims=symbolic_dims,
        variadic_dims=variadic_dims,
        atom_id=atom_id,
        direction=direction,
    )

    if not spec.allow_nan and not np.all(np.isfinite(arr)):
        raise AtomicContractViolationError(
            f"[{atom_id} {direction} NaN/Inf Guard] `{name}` contains NaN or Inf values!"
        )

    if arr.size > 0:
        min_v, max_v = _finite_float(np.min(arr)), _finite_float(np.max(arr))
        low_b, high_b = spec.domain
        if min_v < low_b - 1e-12 or max_v > high_b + 1e-12:
            raise AtomicContractViolationError(
                f"[{atom_id} {direction} Domain Violation] `{name}` range [{min_v:.4g}, {max_v:.4g}] "
                f"violates physical domain [{low_b}, {high_b}] (unit: {spec.unit})!"
            )

    if spec.monotonic is not None and arr.ndim == 1 and arr.size > 1:
        diffs = np.diff(arr)
        if spec.monotonic == "strictly_increasing" and not np.all(diffs > 0):
            raise AtomicContractViolationError(
                f"[{atom_id} {direction} Monotonicity Violation] `{name}` must be strictly increasing!"
            )
        elif spec.monotonic == "non_decreasing" and not np.all(diffs >= -1e-15):
            raise AtomicContractViolationError(
                f"[{atom_id} {direction} Monotonicity Violation] `{name}` must be non-decreasing!"
            )
        elif spec.monotonic == "strictly_decreasing" and not np.all(diffs < 0):
            raise AtomicContractViolationError(
                f"[{atom_id} {direction} Monotonicity Violation] `{name}` must be strictly decreasing!"
            )

    return arr


@dataclass(frozen=True)
class TensorSpec:
    """
    Formal boundary contract for an input or output parameter of an Atomic Operator Capsule.
    Supports both tuple (`("N", "N+1")`) and `jaxtyping` space-separated string (`"*batch N N+1"`)
    shape specifications, including symbolic algebra (`N+1`, `N-1`, `2*N`), variadic batch axes
    (`*batch`, `#*batch`, `...`), and broadcastable axes (`#N`).
    """
    shape: Union[str, Tuple[Union[str, int], ...]] = ()
    unit: str = "dimensionless"
    domain: Tuple[float, float] = (-np.inf, np.inf)
    monotonic: Optional[Literal["strictly_increasing", "non_decreasing", "strictly_decreasing"]] = None
    allow_nan: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "shape", parse_jaxtyping_shape_spec(self.shape))


class QuantityTensor:
    """Lightweight unit-tagged numerical payload for zero-trust cross-module unit checking."""
    def __init__(self, data: Union[np.ndarray, float, int], unit: str = "dimensionless") -> None:
        self.data = _finite_array(data, dtype=np.float64) if not isinstance(data, np.ndarray) else data
        self.unit = unit

    def __array__(self, dtype=None) -> np.ndarray:
        return _finite_array(self.data, dtype=dtype)
