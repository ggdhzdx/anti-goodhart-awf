"""AWF Guard: holdout stages."""
from __future__ import annotations

from typing import Any, Callable, Dict

from awf_guard_numeric_contracts import finite_float as _finite_float
from .claims import verify_agent_turn_claims
from .errors import AntiGoodhartGateError
from .station_spec import MetaBoundsPolicy, StationVerificationSpec, _cfg_value
from .verifier_safety import compute_verifier_safety_and_bestofk_gap, evaluate_verifier_hardening_regression_gate


def _run_gate7_holdout_and_claim_checks(
    spec: StationVerificationSpec,
    policy: MetaBoundsPolicy,
    receipt: Dict[str, Any],
    check_upper: Callable[[str, float, float], None],
    check_lower: Callable[[str, float, float], None],
) -> None:
    if spec.depooled_slice_scores is not None:
        if not spec.depooled_slice_scores:
            raise AntiGoodhartGateError('[Gate 7a] `depooled_slice_scores` cannot be empty when specified!')
        sorted_slices = sorted(spec.depooled_slice_scores.items(), key=lambda kv: kv[1])
        worst_k = sorted_slices[:min(5, len(sorted_slices))]
        worst_name, worst_val = worst_k[0]
        if worst_val < spec.worst_slice_floor:
            raise AntiGoodhartGateError(f'[Gate 7 L_inf Min-Max Bucket Failure] Worst slice `{worst_name}` scored {worst_val:.4f} < floor {spec.worst_slice_floor:.4f}!')
        check_lower('G7a_DePooled_WorstK_Exposure', worst_val, spec.worst_slice_floor)
        receipt['gate7_worst_5_slices'] = dict(worst_k)
        receipt['gates_passed'].append('G7a_DePooled_WorstK_Exposure')
    if spec.sealed_holdout_capsule is not None and spec.holdout_orthogonal_value is not None:
        blind_res = spec.sealed_holdout_capsule.evaluate_blind(spec.holdout_orthogonal_value, borderline_ratio=policy.borderline_margin_ratio)
        if not blind_res['passed']:
            raise AntiGoodhartGateError(
                f"[Gate 7b Sealed Hold-Out Orthogonal Failure] Metric `{spec.sealed_holdout_capsule.metric_name}` "
                f"failed blind verification ({blind_res['direction']}, severity={blind_res['ratio_to_tol']:.2f}x ceiling; "
                f"exact target REDACTED). Hint: {spec.sealed_holdout_capsule.remediation_hint}"
            )
        if blind_res['is_borderline']:
            receipt['borderline_warnings'].append(
                f"[G7b_HoldOut_Orthogonal_Validation Borderline Threshold-Hugging] Blind holdout metric "
                f"`{spec.sealed_holdout_capsule.metric_name}` is near ceiling (band {blind_res['ratio_to_tol'] * 100:.1f}%)."
            )
        receipt['gate7_holdout_ratio_to_tol'] = blind_res['ratio_to_tol']
        receipt['gates_passed'].append('G7b_HoldOut_Orthogonal_Validation')
    elif spec.holdout_orthogonal_value is not None and spec.holdout_orthogonal_target is not None:
        diff_val = _finite_float(spec.holdout_orthogonal_value) - _finite_float(spec.holdout_orthogonal_target)
        orth_err = abs(diff_val)
        ratio_to_tol = orth_err / max(_finite_float(spec.holdout_orthogonal_tol), 1e-15)
        if orth_err > spec.holdout_orthogonal_tol:
            direction = 'OVER-PREDICTED (+)' if diff_val > 0 else 'UNDER-PREDICTED (-)'
            if spec.sanitize_holdout_feedback:
                raise AntiGoodhartGateError(
                    f'[Gate 7 Hold-Out Orthogonal Failure (Sanitized)] Metric `{spec.holdout_orthogonal_metric_name}` '
                    f'{direction} beyond tolerance ({ratio_to_tol:.2f}x ceiling; exact hold-out target REDACTED).'
                )
            raise AntiGoodhartGateError(f'[Gate 7 Hold-Out Orthogonal Failure] Metric `{spec.holdout_orthogonal_metric_name}` deviated by {orth_err:.4f} > tol {spec.holdout_orthogonal_tol:.4f}!')
        check_upper('G7b_HoldOut_Orthogonal_Validation', orth_err, spec.holdout_orthogonal_tol)
        receipt['gate7_holdout_orthogonal_err'] = orth_err
        receipt['gates_passed'].append('G7b_HoldOut_Orthogonal_Validation')
    if spec.agent_turn_claims is not None:
        claim_report = verify_agent_turn_claims(
            spec.agent_turn_claims,
            repo_root=spec.repo_root_for_claims,
            command_receipts=spec.command_receipts,
            last_edit_mtime=spec.latest_source_edit_mtime,
            extra_source_code=spec.solver_source_code,
            extra_diff_files=spec.diff_files_for_claims,
        )
        if claim_report['status'] != 'PASS' or int(_cfg_value(claim_report['summary'], 'claims_total', 0)) < 1:
            raise AntiGoodhartGateError(f"[Gate 7c Turn-Claim Fact-Check Failure] Agent turn claims failed deterministic fact-check: summary={claim_report['summary']}")
        receipt['gate7c_turn_claim_factcheck'] = claim_report['summary']
        receipt['gates_passed'].append('G7c_TurnClaim_FactCheck_ZeroContradiction')
    if spec.verifier_hardening_spec is not None:
        vh_res = evaluate_verifier_hardening_regression_gate(
            patched_grader_fn=spec.verifier_hardening_spec['patched_grader_fn'],
            breach_samples=spec.verifier_hardening_spec.get('breach_samples', []),
            gold_samples=spec.verifier_hardening_spec.get('gold_samples', []),
        )
        if not vh_res['accepted']:
            raise AntiGoodhartGateError(
                f"[Gate 7d Verifier Hardening Regression Gate Failure] Patch rejected "
                f"(breach_sealed={vh_res['breach_sealed']}, friendly_fire={vh_res['friendly_fire_over_tightened']}, "
                f"breach_count={_cfg_value(vh_res, 'breach_count', 0)}, gold_count={_cfg_value(vh_res, 'gold_count', 0)})!"
            )
        receipt['gate7d_verifier_hardening'] = vh_res
        receipt['gates_passed'].append('G7d_RedGreen_RegressionGate_ZeroFriendlyFire')
    if spec.rollout_seam_records is not None:
        if not spec.rollout_seam_records:
            raise AntiGoodhartGateError('[Gate 7e] `rollout_seam_records` cannot be empty when specified!')
        seam_res = compute_verifier_safety_and_bestofk_gap(spec.rollout_seam_records)
        hard_info = seam_res['hardened']
        gap_val = _finite_float(seam_res['bestofk']['gap'])
        if hard_info['over_tightened'] or _finite_float(hard_info['safety_score']) < spec.min_verifier_safety_score or gap_val <= 0.0:
            raise AntiGoodhartGateError(f"[Gate 7e Verifier Safety / Best-of-K Gap Failure] safety_score={hard_info['safety_score']}, bestofk_gap={gap_val}!")
        receipt['gate7e_verifier_safety_and_gap'] = seam_res
        receipt['gates_passed'].append('G7e_VerifierSafety_And_BestOfK_Gap')


class HoldoutStages:
    """Legacy private stage adapter; the engine uses explicit functions."""
    _run_gate7_holdout_and_claim_checks = staticmethod(_run_gate7_holdout_and_claim_checks)
