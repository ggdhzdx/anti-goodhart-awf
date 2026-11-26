"""AWF Guard: tensor contracts and Pint physical-unit / dimensional-homogeneity verification."""
from __future__ import annotations

import ast
import functools
from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional, Sequence, Tuple, Union
import numpy as np
import pint

from awf_guard_numeric_contracts import finite_array as _finite_array
from awf_guard_numeric_contracts import finite_float as _finite_float
from awf_guard_numeric_contracts import finite_inputs as _finite_inputs
from .errors import AtomicContractViolationError
from .shape_contracts import check_jaxtyping_shape_contract, parse_jaxtyping_shape_spec

_VALID_MONOTONIC_MODES = ("strictly_increasing", "non_decreasing", "strictly_decreasing")
_SYMMETRY_ATOL = 1e-10
_DOMAIN_BOUND_EPS = 1e-12
_MONOTONIC_NONDEC_EPS = -1e-15
_UNIT_SCALE_ATOL = 1e-9
_MAX_UNIT_REL_TOL = 1e-3

_CUSTOM_ATOMIC_UNIT_DEFS = (
    "hartree = 4.3597447222071e-18 * joule = Eh = Ha",
    "rydberg = 0.5 * hartree = Ry",
    "bohr = 5.29177210903e-11 * meter = a0",
    "debye = 3.3356409519815204e-30 * coulomb * meter = D",
    "wavenumber = 1 / centimeter = cm_inv",
)


@functools.lru_cache(maxsize=1)
def _get_pint_ureg() -> pint.UnitRegistry:
    ureg: pint.UnitRegistry = pint.UnitRegistry(autoconvert_offset_to_baseunit=True)
    for definition in _CUSTOM_ATOMIC_UNIT_DEFS:
        ureg.define(definition)
    return ureg


def _normalize_unit_expr(unit_str: str) -> str:
    cleaned = unit_str.strip()
    if not cleaned or cleaned == "1":
        return "dimensionless"
    return cleaned.replace("^", "**")


def _parse_pint_unit_quantity(unit_str: str) -> Any:
    ureg = _get_pint_ureg()
    norm = _normalize_unit_expr(unit_str)
    if norm == "dimensionless":
        return ureg.Quantity(1.0, ureg.dimensionless)
    parsed = ureg.parse_expression(norm)
    if isinstance(parsed, ureg.Quantity):
        return parsed.astype(float)
    return ureg.Quantity(1.0, parsed)


def _check_or_convert_quantity_unit(
    val_data: Any,
    actual_unit: str,
    expected_unit: str,
    auto_convert: bool,
    atom_id: str,
    direction: str,
    param_name: str,
) -> Any:
    if actual_unit == expected_unit:
        return val_data
    try:
        q_actual = _parse_pint_unit_quantity(actual_unit)
        q_expected = _parse_pint_unit_quantity(expected_unit)
    except Exception as exc:
        raise AtomicContractViolationError(
            f"[{atom_id} {direction} Unit Mismatch] Parameter `{param_name}` expected unit "
            f"`{expected_unit}`, received `{actual_unit}` (unparseable unit expression: {exc})!"
        ) from exc

    if q_actual.dimensionality != q_expected.dimensionality:
        raise AtomicContractViolationError(
            f"[{atom_id} {direction} Unit Mismatch] Parameter `{param_name}` expected unit "
            f"`{expected_unit}` ({q_expected.dimensionality}), but received QuantityTensor with "
            f"incompatible dimensionality `{actual_unit}` ({q_actual.dimensionality})!"
        )

    scale_factor = _finite_float(q_actual.to(q_expected.units).magnitude)
    if abs(scale_factor - 1.0) <= _UNIT_SCALE_ATOL:
        return val_data
    if not auto_convert:
        raise AtomicContractViolationError(
            f"[{atom_id} {direction} Unit Scale Mismatch] Parameter `{param_name}` expected `{expected_unit}`, "
            f"received `{actual_unit}` (conversion factor = {scale_factor:.8g} != 1.0; set auto_convert_unit=True "
            f"or convert explicitly)!"
        )
    return np.asarray(val_data) * scale_factor


def _eval_dimensional_ast(node: ast.AST, env: Dict[str, Any], ureg: pint.UnitRegistry) -> Any:
    if isinstance(node, ast.Expression):
        return _eval_dimensional_ast(node.body, env, ureg)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
        return ureg.Quantity(_finite_float(node.value), ureg.dimensionless)
    if isinstance(node, ast.Name):
        if node.id not in env:
            raise KeyError(f"Unknown variable `{node.id}` in dimensional_law")
        return env[node.id]
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        sub = _eval_dimensional_ast(node.operand, env, ureg)
        return sub if isinstance(node.op, ast.UAdd) else (-sub)
    if isinstance(node, ast.BinOp):
        left = _eval_dimensional_ast(node.left, env, ureg)
        right = _eval_dimensional_ast(node.right, env, ureg)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            return left / right
        if isinstance(node.op, ast.Pow):
            if not right.dimensionless:
                raise pint.DimensionalityError(right.units, ureg.dimensionless, extra_msg="exponent must be dimensionless")
            exp_val = _finite_float(right.to(ureg.dimensionless).magnitude)
            return left ** exp_val
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and len(node.args) == 1 and not node.keywords:
        arg_q = _eval_dimensional_ast(node.args[0], env, ureg)
        fn_id = node.func.id
        if fn_id == "sqrt":
            return arg_q ** 0.5
        if fn_id in ("exp", "log", "ln", "sin", "cos", "tan", "tanh"):
            if not arg_q.dimensionless:
                raise pint.DimensionalityError(
                    arg_q.units,
                    ureg.dimensionless,
                    extra_msg=f"argument to `{fn_id}(...)` must be dimensionless",
                )
            return ureg.Quantity(1.0, ureg.dimensionless)
    raise ValueError(f"Unsupported syntax `{ast.dump(node)}` in dimensional_law")


@_finite_inputs
def verify_pint_dimensional_homogeneity(
    variable_units: Dict[str, str],
    dimensional_law: str,
    expected_output_unit: str = "dimensionless",
    unit_conversion_probes: Optional[Sequence[Tuple[str, str, float]]] = None,
    rel_tol: float = 1e-6,
) -> Dict[str, Any]:
    """
    Buckingham-Pi Dimensional Homogeneity & Atomic/SI Scale-Factor Verification Gate (`G3o`).
    Verifies algebraic/transcendental physical formulas via `pint` (catching missing R, k_B, hbar, nF
    inside exponentials/sums and unacknowledged Hartree/eV/kcal-mol^-1 scale mismatches).
    """
    tol_f = _finite_float(rel_tol)
    if not (0.0 < tol_f <= _MAX_UNIT_REL_TOL):
        raise ValueError(f"G3o rel_tol must be in (0, {_MAX_UNIT_REL_TOL}], got {tol_f}")
    if not variable_units or not dimensional_law or not dimensional_law.strip():
        raise ValueError("G3o requires non-empty `variable_units` and `dimensional_law`")

    ureg = _get_pint_ureg()
    violations: List[str] = []
    env: Dict[str, Any] = {
        "R": _parse_pint_unit_quantity("joule / (mol * kelvin)"),
        "k_B": _parse_pint_unit_quantity("joule / kelvin"),
        "hbar": _parse_pint_unit_quantity("joule * second"),
        "F_const": _parse_pint_unit_quantity("coulomb / mol"),
        "e_charge": _parse_pint_unit_quantity("elementary_charge"),
    }
    for var_name, unit_text in variable_units.items():
        try:
            env[str(var_name)] = _parse_pint_unit_quantity(str(unit_text))
        except Exception as exc:
            violations.append(f"Invalid Pint unit `{unit_text}` for variable `{var_name}`: {exc}")

    try:
        expected_q = _parse_pint_unit_quantity(expected_output_unit)
    except Exception as exc:
        violations.append(f"Invalid expected_output_unit `{expected_output_unit}`: {exc}")
        expected_q = ureg.Quantity(1.0, ureg.dimensionless)

    inferred_dim = "invalid"
    if not violations:
        try:
            expr_tree = ast.parse(dimensional_law.strip(), mode="eval")
            referenced_vars = {n.id for n in ast.walk(expr_tree) if isinstance(n, ast.Name)}
            if not (referenced_vars & set(variable_units.keys())):
                violations.append("Vacuous dimensional_law: expression references zero declared `variable_units`.")
            result_q = _eval_dimensional_ast(expr_tree, env, ureg)
            inferred_dim = str(result_q.dimensionality)
            if result_q.dimensionality != expected_q.dimensionality:
                violations.append(
                    f"Dimensionality mismatch: law `{dimensional_law}` has dimensionality "
                    f"{result_q.dimensionality}, expected {expected_q.dimensionality} (`{expected_output_unit}`)"
                )
        except Exception as exc:
            violations.append(f"Dimensional homogeneity failure in `{dimensional_law}`: {exc}")

    checked_probes = 0
    max_scale_rel_err = 0.0
    if unit_conversion_probes is not None:
        if len(unit_conversion_probes) == 0:
            violations.append("unit_conversion_probes cannot be empty when supplied.")
        for src_u, dst_u, claimed_factor in unit_conversion_probes:
            checked_probes += 1
            claimed_f = _finite_float(claimed_factor)
            try:
                q_src = _parse_pint_unit_quantity(src_u)
                q_dst = _parse_pint_unit_quantity(dst_u)
                exact_factor = _finite_float(q_src.to(q_dst.units).magnitude)
                rel_err = abs(claimed_f - exact_factor) / max(abs(exact_factor), _DOMAIN_BOUND_EPS)
                if rel_err > max_scale_rel_err:
                    max_scale_rel_err = rel_err
                if rel_err > tol_f:
                    violations.append(
                        f"Unit scale factor mismatch for `{src_u} -> {dst_u}`: claimed={claimed_f:.8g}, "
                        f"exact={exact_factor:.8g} (rel_err={rel_err:.3e} > {tol_f:.3e})"
                    )
            except Exception as exc:
                violations.append(f"Incompatible conversion probe `{src_u} -> {dst_u}`: {exc}")

    return {
        "status": "PASS" if not violations else "FAIL",
        "evaluated_variable_count": len(variable_units),
        "checked_conversion_probes": checked_probes,
        "inferred_dimensionality": inferred_dim,
        "expected_dimensionality": str(expected_q.dimensionality),
        "max_conversion_rel_err": round(max_scale_rel_err, 12),
        "rel_tolerance": tol_f,
        "violations": violations,
    }


def _validate_tensor_against_spec(
    name: str,
    val: Any,
    spec: TensorSpec,
    symbolic_dims: Dict[str, int],
    atom_id: str,
    direction: str,
    variadic_dims: Optional[Dict[str, Tuple[bool, Tuple[int, ...]]]] = None,
) -> np.ndarray:
    """Validate Pint unit/scale, jaxtyping symbolic shape, NaN/Inf, symmetry/Hermiticity, domain, and monotonicity."""
    if isinstance(val, QuantityTensor):
        raw_payload = _check_or_convert_quantity_unit(
            val_data=val.data,
            actual_unit=val.unit,
            expected_unit=spec.unit,
            auto_convert=spec.auto_convert_unit,
            atom_id=atom_id,
            direction=direction,
            param_name=name,
        )
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
            if spec.non_negative and min_v < -_DOMAIN_BOUND_EPS:
                raise AtomicContractViolationError(
                    f"[{atom_id} {direction} Non-Negativity Violation] `{name}` has negative minimum {min_v:.4g}!"
                )
            low_b, high_b = spec.domain
            if min_v < low_b - _DOMAIN_BOUND_EPS or max_v > high_b + _DOMAIN_BOUND_EPS:
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
        elif spec.monotonic == "non_decreasing" and not np.all(diffs >= _MONOTONIC_NONDEC_EPS):
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
    auto_convert_unit: bool = False

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

    def __array__(self, dtype: Any = None) -> np.ndarray:
        return _finite_array(self.data, dtype=dtype)
