"""AWF Guard: numerical stability."""
from __future__ import annotations

from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import Set
from typing import Union
from awf_guard_numeric_contracts import finite_call as _finite_call
from awf_guard_numeric_contracts import finite_float as _finite_float
from awf_guard_numeric_contracts import finite_inputs as _finite_inputs
import ast
import copy
import numpy as np
import time
from .numeric_inputs import _extract_array
from .ast_utils import text_dedent


_MS_PER_SECOND = 1000.0


_DEFAULT_MCA_MAX_CONDITION_NUMBER = 1e4


@_finite_inputs
def scan_ast_for_floating_point_pitfalls(source_code: Union[ast.AST, str]) -> List[Dict[str, Any]]:
    """
    Static AST scanner for IEEE-754 floating-point numerical anti-patterns (`gmarkall/PitfallsFP`):
    1. `ExplicitMatrixInverseMultiply`: `np.linalg.inv(A) @ b` or `np.dot(np.linalg.inv(A), b)`
       instead of `np.linalg.solve(A, b)` (amplifies condition number and wastes O(N^3) flops).
    2. `UnstableNaiveLogSumExp`: `np.log(np.sum(np.exp(x)))` without max-subtraction stabilization
       (`scipy.special.logsumexp`), causing overflow/underflow for |x| > 710.
    3. `NaiveLogOnePlusCancellation`: `np.log(1 + x)` or `math.log(1.0 + x)` instead of `log1p(x)`,
       losing up to 16 digits of precision when |x| << 1.
    4. `NaiveExpMinusOneCancellation`: `np.exp(x) - 1.0` instead of `expm1(x)` when |x| << 1.
    """
    if isinstance(source_code, str):
        if not source_code.strip():
            return []
        tree: ast.AST = ast.parse(text_dedent(source_code))
    else:
        tree = source_code
    findings: List[Dict[str, Any]] = []

    def _is_call_named(node: ast.AST, names: Set[str]) -> bool:
        if not isinstance(node, ast.Call):
            return False
        fn_name = getattr(node.func, "id", None) or getattr(node.func, "attr", None) or ""
        return fn_name in names

    def _is_one_constant(node: ast.AST) -> bool:
        return isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(
            node.value, bool
        ) and _finite_float(node.value) == 1.0

    for node in ast.walk(tree):
        # 1. Explicit matrix inverse multiplied by vector/matrix: inv(A) @ b or dot(inv(A), b)
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.MatMult, ast.Mult)):
            if _is_call_named(node.left, {"inv", "pinv"}) or _is_call_named(node.right, {"inv", "pinv"}):
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
            if any(_is_call_named(a, {"inv", "pinv"}) for a in node.args):
                findings.append({
                    "kind": "ExplicitMatrixInverseMultiply",
                    "line": getattr(node, "lineno", 0),
                    "detail": (
                        f"`dot(inv(A), b)` at line {getattr(node, 'lineno', 0)} degrades numerical "
                        f"conditioning; use `np.linalg.solve(A, b)` instead."
                    ),
                })

        # 2 & 3. log(sum(exp(x))) and log(1 + x)
        if _is_call_named(node, {"log"}):
            assert isinstance(node, ast.Call)
            if node.args:
                arg0 = node.args[0]
                if _is_call_named(arg0, {"sum", "nansum"}):
                    assert isinstance(arg0, ast.Call)
                    if arg0.args and _is_call_named(arg0.args[0], {"exp"}):
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

        # 4. exp(x) - 1.0
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
    Monte Carlo Arithmetic (MCA) & Float64->Float32 Precision-Downgrade Conditioning Auditor
    (`gmarkall/PitfallsFP`):
    1. **Static Floating-Point Pitfall Scan (`G5l`)**:
       - Scans `source_code` for `inv(A) @ b`, `log(sum(exp(x)))`, `log(1 + x)`, and `exp(x) - 1`.
    2. **Float64 -> Float32 -> Float64 Precision-Downgrade Drift (`G1c`)**:
       - Round-trips continuous input arrays through IEEE-754 binary32 (`np.float32`) and measures
         relative output drift `f32_rel_drift = ||y_f32 - y_f64||_inf / (||y_f64||_inf + 1e-12)`.
    3. **Monte Carlo Arithmetic (MCA) Stochastic Mantissa Perturbation & Condition Number (`G1c`)**:
       - Injects `n_mca_trials` independent multiplicative mantissa perturbations `x * (1 + xi)`,
         `xi ~ N(0, relative_noise_sigma^2)`, computes `max_mca_rel_drift` and empirical condition
         number `empirical_condition_number = max_rel_output_drift / relative_noise_sigma`.
    """
    ast_pitfalls = scan_ast_for_floating_point_pitfalls(source_code)

    base_out = _extract_array(_finite_call(target_fn, **sample_input_kwargs))
    base_norm = _finite_float(np.max(np.abs(base_out))) + 1e-12

    # 1. Float32 precision downgrade round-trip
    f32_kwargs: Dict[str, Any] = {}
    for k, v in sample_input_kwargs.items():
        if isinstance(v, np.ndarray) and np.issubdtype(v.dtype, np.floating):
            f32_kwargs[k] = v.astype(np.float32).astype(np.float64)
        else:
            f32_kwargs[k] = v
    f32_out = _extract_array(_finite_call(target_fn, **f32_kwargs))
    f32_rel_drift = _finite_float(np.max(np.abs(f32_out - base_out))) / base_norm

    # 2. Monte Carlo Arithmetic (MCA) stochastic mantissa rounding trials
    rng = np.random.default_rng(seed)
    mca_drifts: List[float] = []
    atom_inputs = (getattr(target_fn, "_atom_metadata", None) or {}).get("inputs", {})
    for _ in range(n_mca_trials):
        mca_kw: Dict[str, Any] = {}
        for k, v in sample_input_kwargs.items():
            if isinstance(v, np.ndarray) and np.issubdtype(v.dtype, np.floating):
                xi = rng.normal(0.0, relative_noise_sigma, size=v.shape)
                cand_v = v * (1.0 + xi)
                if k in atom_inputs and atom_inputs[k].get("domain") is not None:
                    low_b, high_b = atom_inputs[k]["domain"]
                    cand_v = np.where(cand_v > high_b, v * (1.0 - np.abs(xi)), cand_v)
                    cand_v = np.where(cand_v < low_b, v * (1.0 + np.abs(xi)), cand_v)
                    cand_v = np.clip(cand_v, low_b, high_b)
                mca_kw[k] = cand_v
            else:
                mca_kw[k] = v
        mca_out = _extract_array(_finite_call(target_fn, **mca_kw))
        if not np.all(np.isfinite(mca_out)):
            mca_drifts.append(float("inf"))
        else:
            mca_drifts.append(_finite_float(np.max(np.abs(mca_out - base_out))) / base_norm)

    max_mca_rel_drift = max(mca_drifts) if mca_drifts else 0.0
    empirical_cond = max_mca_rel_drift / max(relative_noise_sigma, 1e-15)

    passed = (
        (not ast_pitfalls)
        and np.isfinite(f32_rel_drift)
        and np.isfinite(max_mca_rel_drift)
        and (f32_rel_drift <= max_allowed_rel_drift)
        and (max_mca_rel_drift <= max_allowed_rel_drift)
        and (empirical_cond <= max_condition_number)
    )
    return {
        "status": "PASS" if passed else "FAIL",
        "ast_pitfalls": ast_pitfalls,
        "f32_rel_drift": round(f32_rel_drift, 10),
        "max_mca_rel_drift": round(max_mca_rel_drift, 10),
        "empirical_condition_number": round(empirical_cond, 4),
        "max_allowed_rel_drift": max_allowed_rel_drift,
        "max_condition_number": max_condition_number,
    }


@_finite_inputs
def evaluate_adaptive_runtime_budget(
    target_fn: Callable[..., Any],
    sample_input_kwargs: Dict[str, Any],
    max_total_budget_sec: float = 2.0,
) -> Dict[str, Any]:
    """
    Measure single-call latency of a scientific operator and compute an adaptive verification
    sampling budget so heavy kernels (PME electrostatics, 3D grids, MLIP inference) do not stall.
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
