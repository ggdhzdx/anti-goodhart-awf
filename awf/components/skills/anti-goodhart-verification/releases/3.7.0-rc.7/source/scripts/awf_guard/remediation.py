"""AWF Guard: remediation."""
from __future__ import annotations

from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional
from typing import Sequence
from typing import Tuple
from awf_guard_numeric_contracts import finite_call as _finite_call
from awf_guard_numeric_contracts import finite_float as _finite_float
from awf_guard_numeric_contracts import finite_inputs as _finite_inputs
import ast
import copy
import inspect
import numpy as np
from .source_quality import DEFAULT_MAX_FUNCTION_LINES
from .atoms import GLOBAL_ATOM_REGISTRY
from .ast_structure import _calculate_mccabe
from .numeric_inputs import _extract_array
from .ast_utils import _unwrap_target_fn
from .ast_structure import audit_ast_pair_diff
from .source_quality import scan_source_for_todo_placeholders_and_magic_numbers
from .ast_utils import text_dedent
from .evidence_contracts import concrete_cases, require_distinct_reference, valid_upstream_receipt


@_finite_inputs
def verify_microstep_granularity_and_topological_anchor(
    target_fn: Callable[..., Any],
    atom_manifest: Optional[Dict[str, Dict[str, Any]]] = None,
    min_lines: Optional[int] = None,
    max_lines: Optional[int] = None,
    max_cyclomatic_complexity: int = 10,
    max_inputs: int = 6,
    max_outputs: int = 3,
    mca_condition_number: Optional[float] = None,
    max_condition_number: float = 1e4,
    invariant_anchor_count: Optional[int] = None,
    min_invariant_anchors: int = 2,
) -> Dict[str, Any]:
    """
    6-Dimensional Micro-Step Sufficiency & Topological Distribution Anchor Verifier (`G6o`):
    Determines quantitatively whether a decomposed step size `Delta s` is sufficiently small
    (within the LLM's single-step reasoning trust region) and topologically pinned:
    1. Code Line Granularity: `min_lines <= L <= max_lines` (only explicitly supplied bounds are enforced);
    2. Control-Flow Entropy: McCabe cyclomatic complexity `1 <= V(G) <= max_cyclomatic_complexity` (default <= 10);
    3. I/O Tensor Arity: `1 <= N_in <= max_inputs`, `1 <= N_out <= max_outputs`;
    4. Topological 1-Hop Frontier Lock: all direct `upstream_atoms` in `atom_manifest` must already hold a `PASS` receipt;
    5. Local Jacobian / MCA Conditioning: `mca_condition_number <= max_condition_number`;
    6. Physical Invariant Pinning Count: `invariant_anchor_count >= min_invariant_anchors` (>= 2 orthogonal properties).
    """
    raw_fn = _finite_call(_unwrap_target_fn, target_fn)
    source_available = True
    try:
        lines, _ = inspect.getsourcelines(raw_fn)
        src = "".join(lines)
        n_lines = len(lines)
        tree = ast.parse(text_dedent(src))
        fn_nodes = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        cc_val = _calculate_mccabe(fn_nodes[0]) if fn_nodes else 1
    except (OSError, SyntaxError):
        source_available = False
        n_lines = 0
        cc_val = 0

    atom_meta = getattr(target_fn, "_atom_metadata", None) or {}
    in_map = atom_meta.get("inputs", {})
    out_map = atom_meta.get("outputs", {})
    sig = inspect.signature(raw_fn)
    n_in = len(in_map) if in_map else len(sig.parameters)
    n_out = len(out_map) if out_map else 1

    reg = atom_manifest if atom_manifest is not None else GLOBAL_ATOM_REGISTRY
    upstreams = list(atom_meta.get("upstream_atoms", []))
    unverified_upstreams: List[str] = []
    for up_id in upstreams:
        up_info = reg.get(up_id)
        if up_info is None:
            unverified_upstreams.append(f"{up_id} (MISSING)")
        else:
            st = str(up_info.get("gate_status", "REGISTERED"))
            if st not in {"PASS", "VERIFIED"} or not valid_upstream_receipt(up_id, up_info.get("last_verification_receipt")):
                unverified_upstreams.append(f"{up_id} ({st})")

    violations: List[str] = []
    if not source_available:
        violations.append("Target source is unavailable; structure was not inspected")
    if (min_lines is not None and n_lines < min_lines) or (max_lines is not None and n_lines > max_lines):
        violations.append(f"Line count {n_lines} outside micro-step window [{min_lines}, {max_lines}]")
    if cc_val > max_cyclomatic_complexity:
        violations.append(f"McCabe cyclomatic complexity {cc_val} > max {max_cyclomatic_complexity} (step too coarse)")
    if not (1 <= n_in <= max_inputs and 1 <= n_out <= max_outputs):
        violations.append(f"I/O arity (in={n_in}, out={n_out}) exceeds micro-step cap ({max_inputs}, {max_outputs})")
    if unverified_upstreams:
        violations.append(f"Topological leap violation: upstream atom(s) not yet PASS: {unverified_upstreams}")
    if mca_condition_number is None:
        violations.append("Condition number must be explicitly declared")
    elif mca_condition_number > max_condition_number:
        violations.append(f"Local condition number {mca_condition_number:.2e} > {max_condition_number:.2e}")
    if invariant_anchor_count is None:
        violations.append("Invariant anchors must be explicitly declared")
    elif invariant_anchor_count < min_invariant_anchors:
        violations.append(
            f"Insufficient physical invariant anchors ({invariant_anchor_count} < {min_invariant_anchors})"
        )

    passed = len(violations) == 0
    return {
        "status": "PASS" if passed else "FAIL",
        "source_lines": n_lines,
        "cyclomatic_complexity": cc_val,
        "input_arity": n_in,
        "output_arity": n_out,
        "upstream_atoms": upstreams,
        "unverified_upstream_atoms": unverified_upstreams,
        "unverified_hop_distance": 1 + len(unverified_upstreams),
        "mca_condition_number": round(_finite_float(mca_condition_number), 4) if mca_condition_number is not None else None,
        "invariant_anchor_count": int(invariant_anchor_count) if invariant_anchor_count is not None else None,
        "anchor_condition_evidence": "caller_declared_not_independently_measured",
        "source_inspected": source_available,
        "violations": violations,
    }


@_finite_inputs
def evaluate_red_blue_adversarial_audit(
    target_fn: Callable[..., Any],
    reference_or_invariant_fn: Callable[..., Any],
    adversarial_probe_inputs: Sequence[Dict[str, Any]],
    solver_source_code: str = "",
    red_auditor_claimed_pass: bool = True,
    probe_tol: float = 1e-5,
) -> Dict[str, Any]:
    """
    Red-Team Breaker vs. Blue-Team Builder Adversarial Decoupled Game (`G7h`):
    Splits generation and auditing objectives:
    - Blue Builder only gets +1.0 when `defects_found == 0` (else `-inf`);
    - Red Auditor gets `+10.0 * defects_found` for catching simplified assumptions, fake data,
      placeholder stubs, or adversarial counterexamples (`||f_blue(x*) - f_ref(x*)|| > probe_tol`),
      and gets `-inf` (`rubber_stamp_collusion = True`) if it rubber-stamps defective Blue code!
    """
    concrete_cases(adversarial_probe_inputs, "Red-blue audit")
    require_distinct_reference(target_fn, reference_or_invariant_fn)
    executed_probes = 0
    cb_res = scan_source_for_todo_placeholders_and_magic_numbers(
        solver_source_code,
        check_magic_numbers=True,
    )
    failed_probes: List[Dict[str, Any]] = []
    for idx, probe_kw in enumerate(adversarial_probe_inputs):
        kw_b = {k: (v.copy() if isinstance(v, np.ndarray) else copy.deepcopy(v)) for k, v in probe_kw.items()}
        kw_r = {k: (v.copy() if isinstance(v, np.ndarray) else copy.deepcopy(v)) for k, v in probe_kw.items()}
        out_b = _extract_array(_finite_call(target_fn, **kw_b))
        out_r = _extract_array(_finite_call(reference_or_invariant_fn, **kw_r))
        err = _finite_float(np.max(np.abs(out_b - out_r))) if out_b.shape == out_r.shape else float("inf")
        executed_probes += 1
        if err > probe_tol:
            failed_probes.append({"probe_index": idx, "max_abs_err": round(err, 10)})

    defects_found = cb_res["finding_count"] + len(failed_probes)
    rubber_stamp_collusion = bool(defects_found > 0 and red_auditor_claimed_pass)
    blue_reward = 1.0 if defects_found == 0 else -float("inf")
    if defects_found > 0:
        red_reward = -float("inf") if red_auditor_claimed_pass else _finite_float(defects_found) * 10.0
    else:
        red_reward = 1.0 if red_auditor_claimed_pass else -1.0

    passed = (defects_found == 0) and (not rubber_stamp_collusion)
    return {
        "status": "PASS" if passed else "FAIL",
        "defects_found": defects_found,
        "circuit_breaker_findings": cb_res["findings"],
        "failed_adversarial_probes": failed_probes,
        "executed_probe_count": executed_probes,
        "requested_probe_count": len(adversarial_probe_inputs),
        "reference_origin_distinct": True,
        "rubber_stamp_collusion": rubber_stamp_collusion,
        "blue_builder_reward": blue_reward,
        "red_auditor_reward": red_reward,
    }


@_finite_inputs
def verify_remediation_closed_loop_and_pareto_candidates(
    pre_fix_source: str,
    post_fix_source: str,
    candidate_implementations: Dict[str, Callable[..., Any]],
    reference_oracle_fn: Callable[..., Any],
    evaluation_inputs: Sequence[Dict[str, Any]],
    tol: float = 1e-8,
    scientific_model_changed: bool = False,
    tolerance_loosened: bool = False,
    consecutive_failed_attempts: int = 0,
    max_autonomous_attempts: int = 3,
) -> Dict[str, Any]:
    """
    Domain-Agnostic Autonomous Remediation Closed-Loop, Differential Pair-Audit &
    Multi-Candidate Pareto Selector (`G6p_Remediation_ClosedLoop_PairDiff_And_Pareto_Selection`):
    1. Autonomous vs. Human-in-the-Loop Escalation Boundary:
       - Immediately escalates (`status = "ESCALATE_TO_HUMAN"`, `requires_human_escalation = True`)
         if fixing the failure requires altering the agreed scientific model (`scientific_model_changed=True`),
         loosening acceptance tolerances (`tolerance_loosened=True`), or exceeds `max_autonomous_attempts`.
    2. Differential Anti-Watering-Down Pair Audit (`pre_fix_source` -> `post_fix_source`):
       - Verifies that the repair did not collapse AST complexity, shrink loop bounds, or inject stubs/magic numbers.
    3. Multi-Candidate Pareto Selection & Mandatory Post-Fix Re-Verification:
       - Evaluates all candidate fixes `{name: fn}` on `evaluation_inputs` against `reference_oracle_fn`
         and ranks passing candidates by `(max_oracle_err, float32_precision_drift)`.
    """
    concrete_cases(evaluation_inputs, "Remediation verification")
    if not candidate_implementations:
        raise ValueError("Remediation requires at least one candidate")
    for candidate in candidate_implementations.values():
        require_distinct_reference(candidate, reference_oracle_fn)
    escalation_reasons: List[str] = []
    if scientific_model_changed:
        escalation_reasons.append("Scientific hypothesis/model structure changed -> requires human approval")
    if tolerance_loosened:
        escalation_reasons.append("Acceptance tolerance loosened -> forbidden autonomous watering-down")
    if consecutive_failed_attempts >= max_autonomous_attempts:
        escalation_reasons.append(
            f"Consecutive autonomous repair attempts ({consecutive_failed_attempts}) >= cap ({max_autonomous_attempts})"
        )

    pair_violations = (
        audit_ast_pair_diff(pre_fix_source, post_fix_source)["violations"]
        if pre_fix_source.strip()
        else []
    )
    cb_post = scan_source_for_todo_placeholders_and_magic_numbers(post_fix_source, check_magic_numbers=True)

    candidate_Leaderboard: List[Dict[str, Any]] = []
    valid_candidates: List[Tuple[float, float, str]] = []
    for cand_name, cand_fn in candidate_implementations.items():
        max_err = 0.0
        f32_drift = 0.0
        executed_evaluations = 0
        for kw in evaluation_inputs:
            kw_c = {k: (v.copy() if isinstance(v, np.ndarray) else copy.deepcopy(v)) for k, v in kw.items()}
            kw_r = {k: (v.copy() if isinstance(v, np.ndarray) else copy.deepcopy(v)) for k, v in kw.items()}
            out_c = _extract_array(_finite_call(cand_fn, **kw_c))
            out_r = _extract_array(_finite_call(reference_oracle_fn, **kw_r))
            err = _finite_float(np.max(np.abs(out_c - out_r))) if out_c.shape == out_r.shape else float("inf")
            if err > max_err:
                max_err = err
            kw_f32 = {
                k: (v.astype(np.float32).astype(np.float64) if isinstance(v, np.ndarray) and np.issubdtype(v.dtype, np.floating) else v)
                for k, v in kw.items()
            }
            out_f32 = _extract_array(_finite_call(cand_fn, **kw_f32))
            drift = _finite_float(np.max(np.abs(out_f32 - out_c))) / (_finite_float(np.max(np.abs(out_c))) + 1e-15)
            executed_evaluations += 1
            if drift > f32_drift:
                f32_drift = drift
        cand_passed = max_err <= tol
        candidate_Leaderboard.append({
            "candidate": cand_name,
            "passed_oracle": cand_passed,
            "executed_evaluation_count": executed_evaluations,
            "max_oracle_err": round(max_err, 12),
            "f32_rel_drift": round(f32_drift, 10),
        })
        if cand_passed:
            valid_candidates.append((max_err, f32_drift, cand_name))

    valid_candidates.sort(key=lambda item: (item[0], item[1]))
    selected_candidate = valid_candidates[0][2] if valid_candidates else None
    if selected_candidate is None:
        escalation_reasons.append("Zero candidate implementations satisfied post-fix oracle re-verification")

    requires_human = len(escalation_reasons) > 0
    structural_violations = list(pair_violations) + list(cb_post["findings"])
    passed = (not requires_human) and (len(structural_violations) == 0) and (selected_candidate is not None)
    status = "PASS" if passed else ("ESCALATE_TO_HUMAN" if requires_human else "FAIL")
    return {
        "status": status,
        "autonomous_resolution": passed,
        "requires_human_escalation": requires_human,
        "escalation_reasons": escalation_reasons,
        "selected_pareto_candidate": selected_candidate,
        "candidate_leaderboard": candidate_Leaderboard,
        "requested_evaluation_count": len(evaluation_inputs),
        "oracle_tolerance": tol,
        "reference_origin_distinct": True,
        "pair_regression_violations": pair_violations,
        "post_fix_circuit_breaker_findings": cb_post["findings"],
    }
