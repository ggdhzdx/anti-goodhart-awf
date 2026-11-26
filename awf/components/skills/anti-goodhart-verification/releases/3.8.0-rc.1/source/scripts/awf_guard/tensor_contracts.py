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

_VALID_MONOTONIC_MODES = ("strictly_increasing", "non_decreasing", "strictly_decreasing")
_SYMMETRY_ATOL = 1e-10


def _validate_tensor_against_spec(
    name: str,
    val: Any,
    spec: TensorSpec,
    symbolic_dims: Dict[str, int],
    atom_id: str,
    direction: str,
    variadic_dims: Optional[Dict[str, Tuple[bool, Tuple[int, ...]]]] = None,
) -> np.ndarray:
    """Validate unit, jaxtyping symbolic/algebraic/variadic shape, NaN/Inf, symmetry/Hermiticity, domain bounds, and monotonicity."""
    if isinstance(val, QuantityTensor):
        if val.unit != spec.unit:
            raise AtomicContractViolationError(
                f"[{atom_id} {direction} Unit Mismatch] Parameter `{name}` expected unit "
                f"`{spec.unit}`, but received QuantityTensor with unit `{val.unit}`!"
            )
        raw_payload = val.data
    else:
        if spec.unit != "dimensionless" and not spec.allow_untagged_array:
            raise AtomicContractViolationError(
                f"[{atom_id} {direction} Untagged Physical Unit] Parameter `{name}` declares physical unit "
                f"`{spec.unit}` and requires `QuantityTensor(data, unit='{spec.unit}')`, not bare `{type(val).__name__}`!"
            )
        raw_payload = val

    use_complex = np.iscomplexobj(raw_payload)
    if not spec.allow_nan:
        arr = _finite_array(raw_payload, dtype=np.complex128 if use_complex else np.float64)
    else:
        arr = np.asarray(raw_payload, dtype=np.complex128 if use_complex else np.float64)
        if not spec.allow_inf and np.any(np.isinf(arr)):
            raise AtomicContractViolationError(
                f"[{atom_id} {direction} Inf Guard] `{name}` contains infinite values!"
            )

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

    if spec.symmetric:
        if arr.ndim < 2 or arr.shape[-1] != arr.shape[-2] or not np.allclose(arr, np.swapaxes(arr, -1, -2), atol=_SYMMETRY_ATOL):
            raise AtomicContractViolationError(
                f"[{atom_id} {direction} Symmetry Violation] `{name}` must be symmetric (A == A^T)!"
            )

    if spec.hermitian:
        if arr.ndim < 2 or arr.shape[-1] != arr.shape[-2] or not np.allclose(arr, np.swapaxes(arr.conj(), -1, -2), atol=_SYMMETRY_ATOL):
            raise AtomicContractViolationError(
                f"[{atom_id} {direction} Hermiticity Violation] `{name}` must be Hermitian (H == H^dagger)!"
            )

    if arr.size > 0 and not np.iscomplexobj(arr):
        finite_vals = arr[np.isfinite(arr)]
        if finite_vals.size > 0:
            min_v, max_v = _finite_float(np.min(finite_vals)), _finite_float(np.max(finite_vals))
            if spec.non_negative and min_v < -1e-12:
                raise AtomicContractViolationError(
                    f"[{atom_id} {direction} Non-Negativity Violation] `{name}` has negative minimum {min_v:.4g}!"
                )
            low_b, high_b = spec.domain
            if min_v < low_b - 1e-12 or max_v > high_b + 1e-12:
                raise AtomicContractViolationError(
                    f"[{atom_id} {direction} Domain Violation] `{name}` range [{min_v:.4g}, {max_v:.4g}] "
                    f"violates physical domain [{low_b}, {high_b}] (unit: {spec.unit})!"
                )

    if spec.monotonic is not None:
        if np.iscomplexobj(arr) or arr.ndim < 1 or arr.shape[-1] < 2:
            raise AtomicContractViolationError(
                f"[{atom_id} {direction} Monotonicity Violation] `{name}` requires a real 1D+ array of length >= 2 for `{spec.monotonic}`!"
            )
        diffs = np.diff(arr, axis=-1)
        if spec.monotonic == "strictly_increasing" and not np.all(diffs > 0):
            raise AtomicContractViolationError(
                f"[{atom_id} {direction} Monotonicity Violation] `{name}` must be strictly increasing along its last axis!"
            )
        elif spec.monotonic == "non_decreasing" and not np.all(diffs >= -1e-15):
            raise AtomicContractViolationError(
                f"[{atom_id} {direction} Monotonicity Violation] `{name}` must be non-decreasing along its last axis!"
            )
        elif spec.monotonic == "strictly_decreasing" and not np.all(diffs < 0):
            raise AtomicContractViolationError(
                f"[{atom_id} {direction} Monotonicity Violation] `{name}` must be strictly decreasing along its last axis!"
            )

    return arr


@dataclass(frozen=True)
class TensorSpec:
    """
    Formal boundary contract for an input or output parameter of an Atomic Operator Capsule.
    """
    shape: Union[str, Tuple[Union[str, int], ...]] = ()
    unit: str = "dimensionless"
    domain: Tuple[float, float] = (-np.inf, np.inf)
    monotonic: Optional[Literal["strictly_increasing", "non_decreasing", "strictly_decreasing"]] = None
    allow_nan: bool = False
    allow_inf: bool = False
    symmetric: bool = False
    hermitian: bool = False
    non_negative: bool = False
    allow_untagged_array: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "shape", parse_jaxtyping_shape_spec(self.shape))
        if self.monotonic is not None and self.monotonic not in _VALID_MONOTONIC_MODES:
            raise ValueError(f"Unsupported TensorSpec monotonic mode: {self.monotonic!r}")


class QuantityTensor:
    """Lightweight unit-tagged numerical payload for zero-trust cross-module unit checking."""
    def __init__(self, data: Union[np.ndarray, float, int, complex], unit: str = "dimensionless") -> None:
        if isinstance(data, np.ndarray):
            _ = _finite_array(data)
            self.data = data
        else:
            dtype = np.complex128 if np.iscomplexobj(data) else np.float64
            self.data = _finite_array(data, dtype=dtype)
        self.unit = unit

    def __array__(self, dtype=None) -> np.ndarray:
        return _finite_array(self.data, dtype=dtype)
