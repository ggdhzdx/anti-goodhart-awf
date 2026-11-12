"""AWF Guard: numerical stability."""
from __future__ import annotations

import ast
import copy
import time
from typing import Any, Callable, Dict, List, Set, Union
import numpy as np

from awf_guard_numeric_contracts import finite_call as _finite_call
from awf_guard_numeric_contracts import finite_float as _finite_float
from awf_guard_numeric_contracts import finite_inputs as _finite_inputs
from .ast_utils import text_dedent
from .numeric_inputs import _extract_array
from .tensor_contracts import QuantityTensor

_MS_PER_SECOND = 1000.0
_DEFAULT_MCA_MAX_CONDITION_NUMBER = 1e4
_MAX_MCA_NOISE_SIGMA = 1e-3
_MAX_MCA_DRIFT_CEILING = 0.1
_MAX_MCA_COND_CEILING = 1e6


def _is_call_named(node: ast.AST, names: Set[str]) -> bool:
    if not isinstance(node, ast.Call):
        return False
    fn_name = getattr(node.func, "id", None) or getattr(node.func, "attr", None) or ""
    return fn_name in names


def _is_inv_expr(node: ast.AST, inv_vars: Set[str]) -> bool:
    return _is_call_named(node, {"inv", "pinv"}) or (isinstance(node, ast.Name) and node.id in inv_vars)


def _is_exp_sum_expr(node: ast.AST) -> bool:
    if _is_call_named(node, {"sum", "nansum"}) and isinstance(node, ast.Call):
        if node.args and _is_call_named(node.args[0], {"exp"}):
            return True
        if isinstance(node.func, ast.Attribute) and _is_call_named(node.func.value, {"exp"}):
            return True
    return False


@_finite_inputs
def scan_ast_for_floating_point_pitfalls(source_code: Union[ast.AST, str]) -> List[Dict[str, Any]]:
    """
    Static AST scanner for IEEE-754 floating-point numerical anti-patterns (`gmarkall/PitfallsFP`):
    1. `ExplicitMatrixInverseMultiply`: `inv(A) @ b`, `dot(inv(A), b)`, or two-step `inv_a = inv(A); inv_a @ b`.
    2. `UnstableNaiveLogSumExp`: `log(sum(exp(x)))` or `log(exp(x).sum())`.
    3. `NaiveLogOnePlusCancellation`: `log(1 + x)` instead of `log1p(x)`.
    4. `NaiveExpMinusOneCancellation`: `exp(x) - 1.0` instead of `expm1(x)`.
    """
    if isinstance(source_code, str):
        if not source_code.strip():
            return []
        tree: ast.AST = ast.parse(text_dedent(source_code))
    else:
        tree = source_code
    findings: List[Dict[str, Any]] = []

    inv_vars: Set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and _is_call_named(node.value, {"inv", "pinv"}):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name):
                    inv_vars.add(tgt.id)
        elif isinstance(node, ast.AnnAssign) and node.value is not None and _is_call_named(node.value, {"inv", "pinv"}):
            if isinstance(node.target, ast.Name):
                inv_vars.add(node.target.id)

    def _is_one_constant(node: ast.AST) -> bool:
        return isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(
            node.value, bool
        ) and _finite_float(node.value) == 1.0

    for node in ast.walk(tree):
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.MatMult, ast.Mult)):
            if _is_inv_expr(node.left, inv_vars) or _is_inv_expr(node.right, inv_vars):
                findings.append({
                    "kind": "ExplicitMatrixInverseMultiply",
                    "line": getattr(node, "lineno", 0),
                    "detail": (
                        f"Explicit `inv(A) @ b` at line {getattr(node, 'lineno', 0)} degrades numerical "
                        f"conditioning; use `np.linalg.solve(A, b)` instead."
                    ),
                })
        elif _is_call_named(node, {"dot", "matmul"}):
            assert isinstance(node, ast.Call)
            if any(_is_inv_expr(a, inv_vars) for a in node.args):
                findings.append({
                    "kind": "ExplicitMatrixInverseMultiply",
                    "line": getattr(node, "lineno", 0),
                    "detail": (
                        f"`dot(inv(A), b)` at line {getattr(node, 'lineno', 0)} degrades numerical "
                        f"conditioning; use `np.linalg.solve(A, b)` instead."
                    ),
                })

        if _is_call_named(node, {"log"}):
            assert isinstance(node, ast.Call)
            if node.args:
                arg0 = node.args[0]
                if _is_exp_sum_expr(arg0):
                    findings.append({
                        "kind": "UnstableNaiveLogSumExp",
                        "line": getattr(node, "lineno", 0),
                        "detail": (
                            f"Unstabilized `log(sum(exp(x)))` at line {getattr(node, 'lineno', 0)} overflows "
                            f"for |x| > 710; subtract `np.max(x)` or use `scipy.special.logsumexp`."
                        ),
                    })
                elif isinstance(arg0, ast.BinOp) and isinstance(arg0.op, ast.Add):
                    if _is_one_constant(arg0.left) or _is_one_constant(arg0.right):
                        findings.append({
                            "kind": "NaiveLogOnePlusCancellation",
                            "line": getattr(node, "lineno", 0),
                            "detail": (
                                f"Catastrophic cancellation risk `log(1 + x)` at line {getattr(node, 'lineno', 0)}; "
                                f"use `np.log1p(x)` / `math.log1p(x)`."
                            ),
                        })

        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Sub):
            if _is_call_named(node.left, {"exp"}) and _is_one_constant(node.right):
                findings.append({
                    "kind": "NaiveExpMinusOneCancellation",
                    "line": getattr(node, "lineno", 0),
                    "detail": (
                        f"Catastrophic cancellation risk `exp(x) - 1` at line {getattr(node, 'lineno', 0)}; "
                        f"use `np.expm1(x)` / `math.expm1(x)`."
                    ),
                })

    return findings


def _downgrade_value_f32(val: Any) -> Any:
    if isinstance(val, QuantityTensor):
        return QuantityTensor(data=_downgrade_value_f32(val.data), unit=val.unit)
    if isinstance(val, np.ndarray) and np.issubdtype(val.dtype, np.floating):
        return val.astype(np.float32).astype(np.float64)
    if isinstance(val, float):
        return float(np.float32(val))
    if isinstance(val, list) and val and all(isinstance(x, float) for x in val):
        return [float(np.float32(x)) for x in val]
    if isinstance(val, tuple) and val and all(isinstance(x, float) for x in val):
        return tuple(float(np.float32(x)) for x in val)
    return val


def _perturb_value_mca(val: Any, rng: np.random.Generator, sigma: float, domain: Any) -> Any:
    if isinstance(val, QuantityTensor):
        return QuantityTensor(data=_perturb_value_mca(val.data, rng, sigma, domain), unit=val.unit)
    if isinstance(val, np.ndarray) and np.issubdtype(val.dtype, np.floating):
        xi = rng.normal(0.0, sigma, size=val.shape)
        cand_v = np.where(val == 0.0, 1e-16 * xi / max(sigma, 1e-16), val * (1.0 + xi))
        if domain is not None:
            low_b, high_b = domain
            cand_v = np.where(cand_v > high_b, val * (1.0 - np.abs(xi)), cand_v)
            cand_v = np.where(cand_v < low_b, val * (1.0 + np.abs(xi)), cand_v)
            cand_v = np.clip(cand_v, low_b, high_b)
        return cand_v
    if isinstance(val, float):
        xi_f = float(rng.normal(0.0, sigma))
        cand_f = (1e-16 * xi_f / max(sigma, 1e-16)) if val == 0.0 else val * (1.0 + xi_f)
        if domain is not None:
            cand_f = float(np.clip(cand_f, domain[0], domain[1]))
        return cand_f
    if isinstance(val, list) and val and all(isinstance(x, float) for x in val):
        return [_perturb_value_mca(x, rng, sigma, domain) for x in val]
    if isinstance(val, tuple) and val and all(isinstance(x, float) for x in val):
        return tuple(_perturb_value_mca(x, rng, sigma, domain) for x in val)
    return val


@_finite_inputs
def evaluate_mca_and_precision_downgrade_stability(
    target_fn: Callable[..., Any],
    sample_input_kwargs: Dict[str, Any],
    source_code: str = "",
    n_mca_trials: int = 8,
    relative_noise_sigma: float = 1e-7,
    max_allowed_rel_drift: float = 1e-4,
    max_condition_number: float = 1e4,
    seed: int = 202611,
) -> Dict[str, Any]:
    """
    Monte Carlo Arithmetic (MCA) & Float64->Float32 Precision-Downgrade Conditioning Auditor (`G5l` & `G1c`).
    """
    sigma_f = _finite_float(relative_noise_sigma)
    drift_f = _finite_float(max_allowed_rel_drift)
    cond_f = _finite_float(max_condition_number)
    if int(n_mca_trials) < 2 or not (0.0 < sigma_f <= _MAX_MCA_NOISE_SIGMA) or not (0.0 < drift_f <= _MAX_MCA_DRIFT_CEILING) or not (0.0 < cond_f <= _MAX_MCA_COND_CEILING):
        raise ValueError("Invalid MCA trial count, sigma, drift, or condition number bounds")

    ast_pitfalls = scan_ast_for_floating_point_pitfalls(source_code)
    base_out = _extract_array(_finite_call(target_fn, **sample_input_kwargs))
    base_norm = _finite_float(np.max(np.abs(base_out))) + 1e-12

    f32_kwargs = {k: _downgrade_value_f32(v) for k, v in sample_input_kwargs.items()}
    f32_out = _extract_array(_finite_call(target_fn, **f32_kwargs))
    f32_rel_drift = _finite_float(np.max(np.abs(f32_out - base_out))) / base_norm

    rng = np.random.default_rng(seed)
    mca_drifts: List[float] = []
    atom_inputs = (getattr(target_fn, "_atom_metadata", None) or {}).get("inputs", {})
    for _ in range(int(n_mca_trials)):
        mca_kw = {
            k: _perturb_value_mca(v, rng, sigma_f, (atom_inputs.get(k) or {}).get("domain"))
            for k, v in sample_input_kwargs.items()
        }
        mca_out = _extract_array(_finite_call(target_fn, **mca_kw))
        if not np.all(np.isfinite(mca_out)):
            mca_drifts.append(float("inf"))
        else:
            mca_drifts.append(_finite_float(np.max(np.abs(mca_out - base_out))) / base_norm)

    max_mca_rel_drift = max(mca_drifts) if mca_drifts else 0.0
    empirical_cond = max_mca_rel_drift / max(sigma_f, 1e-15)

    passed = (
        (not ast_pitfalls)
        and np.isfinite(f32_rel_drift)
        and np.isfinite(max_mca_rel_drift)
        and (f32_rel_drift <= drift_f)
        and (max_mca_rel_drift <= drift_f)
        and (empirical_cond <= cond_f)
    )
    return {
        "status": "PASS" if passed else "FAIL",
        "ast_pitfalls": ast_pitfalls,
        "f32_rel_drift": round(f32_rel_drift, 10),
        "max_mca_rel_drift": round(max_mca_rel_drift, 10),
        "empirical_condition_number": round(empirical_cond, 4),
        "max_allowed_rel_drift": drift_f,
        "max_condition_number": cond_f,
    }


@_finite_inputs
def evaluate_adaptive_runtime_budget(
    target_fn: Callable[..., Any],
    sample_input_kwargs: Dict[str, Any],
    max_total_budget_sec: float = 2.0,
) -> Dict[str, Any]:
    """
    Measure single-call latency of a scientific operator and compute an adaptive verification sampling budget.
    """
    kw_copy = {k: (v.copy() if isinstance(v, np.ndarray) else copy.deepcopy(v)) for k, v in sample_input_kwargs.items()}
    t0 = time.perf_counter()
    _ = _finite_call(target_fn, **kw_copy)
    elapsed_sec = max(time.perf_counter() - t0, 1e-7)
    single_call_ms = elapsed_sec * _MS_PER_SECOND
    max_calls = max(int(max_total_budget_sec / elapsed_sec), 4)

    if single_call_ms < 5.0:
        tier_label = "fast_in_memory"
        mca_trials, max_mutants, fuzz_cases = 8, 12, 3
    elif single_call_ms < 100.0:
        tier_label = "moderate_kernel"
        mca_trials = min(4, max(2, max_calls // 4))
        max_mutants = min(5, max(2, max_calls // 3))
        fuzz_cases = 2
    else:
        tier_label = "heavy_solver_wrapper"
        mca_trials, max_mutants, fuzz_cases = 2, 2, 1

    return {
        "single_call_ms": round(single_call_ms, 4),
        "budget_tier": tier_label,
        "max_estimated_calls": max_calls,
        "recommended_mca_trials": mca_trials,
        "recommended_max_mutants": max_mutants,
        "recommended_fuzz_cases": fuzz_cases,
    }
