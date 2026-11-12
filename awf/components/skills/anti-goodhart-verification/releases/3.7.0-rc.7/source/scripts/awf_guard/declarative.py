"""AWF Guard: declarative."""
from __future__ import annotations

from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import Literal
from typing import Optional
from typing import Sequence
from awf_guard_numeric_contracts import finite_array as _finite_array
from awf_guard_numeric_contracts import finite_call as _finite_call
from awf_guard_numeric_contracts import finite_float as _finite_float
from awf_guard_numeric_contracts import finite_inputs as _finite_inputs
import numpy as np
from .numeric_inputs import _extract_array
from .numeric_inputs import _kwargs_materially_differ


_DECLARATIVE_MAX_LAW_TOL: Dict[str, float] = {"deterministic": 1e-3, "stochastic": 0.15}


_DECLARATIVE_MIN_SENSITIVITY_FLOOR = 1e-5


def _declarative_tol_violation(kind: str, name: str, tol_val: float, mode: str, is_sensitivity: bool) -> Optional[str]:
    if is_sensitivity:
        if not (tol_val >= _DECLARATIVE_MIN_SENSITIVITY_FLOOR):
            return f"[{kind} `{name}`] Sensitivity floor {tol_val:.3e} < hard minimum {_DECLARATIVE_MIN_SENSITIVITY_FLOOR:.1e} (vacuous law)"
        return None
    ceiling = _DECLARATIVE_MAX_LAW_TOL[mode]
    if not (tol_val <= ceiling):
        return f"[{kind} `{name}`] Tolerance {tol_val:.3e} exceeds hard ceiling {ceiling:.1e} for mode `{mode}` (threshold dilution)"
    return None


def _eval_declarative_regime_probes(operator_fn: Callable[..., Any], base_kw: Dict[str, Any], probes: Sequence[Dict[str, Any]]) -> List[str]:
    violations: List[str] = []
    for idx, probe in enumerate(probes):
        p_name = str(probe.get("name", f"probe_{idx + 1}"))
        if not _kwargs_materially_differ(probe["input_kwargs"], base_kw):
            violations.append(f"[S1.1 RegimeProbe `{p_name}`] Probe input is identical to the base input (vacuous regime).")
        p_out = _extract_array(_finite_call(operator_fn, **probe["input_kwargs"])).reshape(-1)
        if not bool(_finite_call(probe["predicate_fn"], p_out)):
            violations.append(f"[S1.1 RegimeProbe `{p_name}`] Predicate failed on output={p_out.tolist()}")
        if bool(probe["predicate_fn"](np.full_like(p_out, np.nan, dtype=np.float64))):
            violations.append(f"[S1.1 RegimeProbe `{p_name}`] Predicate accepts an all-NaN output (tautological predicate).")
    return violations


def _eval_declarative_equivariance_laws(
    operator_fn: Callable[..., Any], base_kw: Dict[str, Any], out_base: np.ndarray,
    laws: Sequence[Dict[str, Any]], default_tol: float, mode: str,
) -> List[str]:
    violations: List[str] = []
    for idx, law in enumerate(laws):
        l_name = str(law.get("name", f"equiv_{idx + 1}"))
        src_kw = law.get("input_kwargs")
        ref_kw = base_kw if src_kw is None else src_kw
        if not _kwargs_materially_differ(law["transformed_kwargs"], ref_kw):
            violations.append(f"[S3.1 Law `{l_name}`] `transformed_kwargs` is identical to its reference input (identity transform).")
        ref_out = out_base if src_kw is None else _extract_array(_finite_call(operator_fn, **src_kw)).reshape(-1)
        trans_out = _extract_array(_finite_call(operator_fn, **law["transformed_kwargs"])).reshape(-1)
        exp_fn = law.get("expected_out_fn")
        target_out = ref_out if exp_fn is None else _finite_array(_finite_call(exp_fn, ref_out), dtype=np.float64).reshape(-1)
        diff = _finite_float(np.max(np.abs(trans_out - target_out)))
        tol_val = _finite_float(law.get("tol", default_tol))
        is_sens = law.get("mode", "invariance") == "sensitivity"
        tol_issue = _declarative_tol_violation("S3.1 Law", l_name, tol_val, mode, is_sens)
        if tol_issue:
            violations.append(tol_issue)
        if not np.isfinite(diff):
            violations.append(f"[S3.1 Law `{l_name}`] Non-finite output difference ({diff}).")
        elif is_sens and diff < tol_val:
            violations.append(f"[S3.1 SensitivityLaw `{l_name}`] Shift {diff:.4e} < required floor {tol_val:.4e}")
        elif not is_sens and diff > tol_val:
            violations.append(f"[S3.1 EquivarianceLaw `{l_name}`] Error {diff:.4e} > tol {tol_val:.4e}")
    return violations


def _eval_declarative_manifold_laws(
    operator_fn: Callable[..., Any], out_base: np.ndarray, laws: Sequence[Dict[str, Any]], default_tol: float, mode: str,
) -> List[str]:
    violations: List[str] = []
    for idx, m_law in enumerate(laws):
        m_name = str(m_law.get("name", f"manifold_{idx + 1}"))
        m_kw = m_law.get("input_kwargs")
        m_out = out_base if m_kw is None else _extract_array(_finite_call(operator_fn, **m_kw)).reshape(-1)
        res_val = abs(_finite_float(_finite_call(m_law["residual_fn"], m_out)))
        tol_val = _finite_float(m_law.get("tol", default_tol))
        tol_issue = _declarative_tol_violation("S5.1 ManifoldLaw", m_name, tol_val, mode, False)
        if tol_issue:
            violations.append(tol_issue)
        if not (res_val <= tol_val):
            violations.append(f"[S5.1 ManifoldLaw `{m_name}`] Residual {res_val:.4e} > tol {tol_val:.4e}")
        nan_res = abs(float(m_law["residual_fn"](np.full_like(m_out, np.nan, dtype=np.float64))))
        if nan_res <= tol_val:
            violations.append(f"[S5.1 ManifoldLaw `{m_name}`] Residual is {nan_res:.3e} on an all-NaN output (tautological residual).")
    return violations


@_finite_inputs
def evaluate_universal_declarative_slots(
    operator_fn: Callable[..., Any],
    base_input_kwargs: Dict[str, Any],
    slot_laws: Dict[str, Any],
    default_tol: float = 1e-7,
    mode: Literal["deterministic", "stochastic"] = "deterministic",
    min_total_laws: int = 1,
) -> Dict[str, Any]:
    """
    Open-Ended Parameterized Universal Slot Evaluator (`S1_1`, `S3_1`, `S5_1`):
    Allows any new mathematical symmetry, gauge invariance, scaling law, manifold conservation
    identity, or contrastive regime probe to be verified declaratively without adding new gate
    functions to the engine:
    - `s1_1_regime_probes`: list of `{"name": str, "input_kwargs": dict, "predicate_fn": Callable[[np.ndarray], bool]}`
    - `s3_1_equivariance_laws`: list of `{"name": str, "input_kwargs": Optional[dict], "transformed_kwargs": dict,
      "expected_out_fn": Optional[Callable[[np.ndarray], np.ndarray]], "mode": "invariance"|"sensitivity", "tol": float}`
    - `s5_1_manifold_laws`: list of `{"name": str, "input_kwargs": Optional[dict],
      "residual_fn": Callable[[np.ndarray], float], "tol": float}`
    v3.7.0-rc.3 anti-vacuity guards: at least `min_total_laws` (>= 1) laws; invariance/manifold tolerances capped at
    `1e-3` (deterministic) / `0.15` (stochastic) and sensitivity floors >= `1e-5` (not caller-overridable);
    identity transforms, base-identical regime probes, NaN-accepting predicates / residuals and non-finite
    differences are rejected.
    """
    if mode not in _DECLARATIVE_MAX_LAW_TOL:
        raise ValueError(f"Unknown declarative mode `{mode}`")
    out_base = _extract_array(_finite_call(operator_fn, **base_input_kwargs)).reshape(-1)
    probes = list(slot_laws.get("s1_1_regime_probes", []))
    eq_laws = list(slot_laws.get("s3_1_equivariance_laws", []))
    mf_laws = list(slot_laws.get("s5_1_manifold_laws", []))
    violations: List[str] = []
    total = len(probes) + len(eq_laws) + len(mf_laws)
    if total < max(int(min_total_laws), 1):
        violations.append(f"Only {total} declarative law(s) supplied (< {max(int(min_total_laws), 1)}): nothing was verified.")
    violations += _eval_declarative_regime_probes(operator_fn, base_input_kwargs, probes)
    violations += _eval_declarative_equivariance_laws(operator_fn, base_input_kwargs, out_base, eq_laws, default_tol, mode)
    violations += _eval_declarative_manifold_laws(operator_fn, out_base, mf_laws, default_tol, mode)
    return {
        "status": "PASS" if not violations else "FAIL",
        "s1_1_probes_checked": len(probes),
        "s3_1_equivariance_laws_checked": len(eq_laws),
        "s5_1_manifold_laws_checked": len(mf_laws),
        "violations": violations,
    }
