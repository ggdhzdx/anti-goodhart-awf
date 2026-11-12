"""AWF Guard: provenance stages."""
from __future__ import annotations
from typing import Any
from typing import Callable
from typing import Dict
from awf_guard_numeric_contracts import finite_float as _finite_float
import inspect
from .errors import AntiGoodhartGateError
from .station_spec import MetaBoundsPolicy
from .station_spec import StationVerificationSpec
from .station_spec import _cfg_value
from .benchmark import audit_benchmark_hackability
from .self_audit import audit_engine_self_hosting_integrity
from .data_leakage import audit_splitguard_row_and_group_leakage
from .task_guardrails import audit_task_guardrails_and_scope
from .test_quality import audit_test_suite_falsegreen_and_mock_abuse
from .ast_structure import compute_ncc_test_overlap
from .harness import evaluate_evilgenie_3d_categorical
from .canary import evaluate_impossible_canary_and_anti_sycophancy
from .trajectory import score_trial_orthogonal_fairness
from .command_receipts import verify_command_receipt_freshness

def _run_gate6_provenance_and_harness_checks(spec: StationVerificationSpec, policy: MetaBoundsPolicy, receipt: Dict[str, Any], raw_target: Callable[..., Any]) -> None:
    if spec.test_suite_source_for_ncc is not None:
        code_for_ncc = spec.solver_source_code
        if code_for_ncc is None:
            try:
                code_for_ncc = inspect.getsource(raw_target)
            except OSError:
                code_for_ncc = ''
        ncc_res = compute_ncc_test_overlap(code_for_ncc, spec.test_suite_source_for_ncc, ncc_floor=max(spec.ncc_floor, policy.min_ncc_floor))
        if ncc_res['applicable'] and (not ncc_res['passed']):
            raise AntiGoodhartGateError(f"[Gate 6b NCC Test-Memorization Trap] NCC={ncc_res['ncc_score']} < floor {ncc_res['ncc_floor']}!")
        receipt['gate6b_ncc_test_overlap'] = ncc_res
        receipt['gates_passed'].append('G6b_NCC_Zero_Test_Memorization')
    if spec.command_receipts is not None:
        rec_info = verify_command_receipt_freshness(spec.command_receipts, last_edit_mtime=spec.latest_source_edit_mtime, require_un_narrowed=True)
        receipt['gate6c_command_receipt'] = rec_info
        receipt['gates_passed'].append('G6c_CommandReceipt_Fresh_And_Unnarrowed')
    if spec.trajectory_steps_for_fairness is not None and spec.trajectory_fairness_contract is not None:
        orth_score = score_trial_orthogonal_fairness(static_reward=1.0, trajectory_steps=spec.trajectory_steps_for_fairness, contract=spec.trajectory_fairness_contract, final_code_or_edits=spec.solver_source_code or '')
        if orth_score.fairness == 0:
            raise AntiGoodhartGateError(f'[Gate 6d Trajectory Fairness & Bypass Smuggling Failure] Trial classified as `{orth_score.outcome}` via channels {list(orth_score.bypass_channels_detected)}: {orth_score.evidence}')
        receipt['gate6d_trajectory_fairness'] = orth_score.to_dict()
        receipt['gates_passed'].append('G6d_Trajectory_Fairness_And_No_Bypass_Smuggling')
    if spec.harness_integrity_snapshot is not None:
        eg_3d = evaluate_evilgenie_3d_categorical(visible_passed=True, holdout_passed=True, solver_source_code=spec.solver_source_code or '', harness_snapshot=spec.harness_integrity_snapshot)
        if eg_3d['status'] != 'PASS':
            raise AntiGoodhartGateError(f"[Gate 6e EvilGenie Harness Integrity / 3D Categorical Failure] test_result={eg_3d['test_result']}, classification={eg_3d['code_classification']}, files_modified={eg_3d['files_modified']}")
        receipt['gate6e_evilgenie_3d_categorical'] = {'test_result': eg_3d['test_result'], 'code_classification': eg_3d['code_classification'], 'files_modified': eg_3d['files_modified']}
        receipt['gates_passed'].append('G6e_Harness_SHA256_Immutable_And_3D_Categorical')
    if spec.benchmark_source_files is not None:
        bj_res = audit_benchmark_hackability(spec.benchmark_source_files)
        if bj_res['status'] != 'PASS':
            raise AntiGoodhartGateError(f"[Gate 6f/6g BenchJack Evaluator Hackability Failure] Found {bj_res['finding_count']} vulnerability(ies) ({bj_res['findings_by_class']}): {bj_res['findings'][0]['detail']}")
        receipt['gate6f_6g_benchjack_audit'] = {'files_scanned': bj_res['files_scanned'], 'finding_count': bj_res['finding_count']}
        receipt['gates_passed'].append('G6f_BenchJack_TrustBoundary_No_SharedPath_Or_ConftestHook')
        receipt['gates_passed'].append('G6g_BenchJack_Evaluator_No_LogicGap_Or_WeakMatch')
    if spec.task_guardrail_audit_spec is not None:
        tg_res = audit_task_guardrails_and_scope(**spec.task_guardrail_audit_spec)
        if tg_res['status'] != 'PASS':
            raise AntiGoodhartGateError(f"[Gate 6h/6i Agent-Guardrails Pre-Merge Failure] verdict={tg_res['verdict']}, score={tg_res['score']}, findings={tg_res['findings']}")
        receipt['gate6h_6i_agent_guardrails'] = {'score': tg_res['score'], 'verdict': tg_res['verdict'], 'finding_count': tg_res['finding_count'], 'verity_accepted': tg_res['verity_evidence'] is not None}
        receipt['gates_passed'].append('G6h_AgentGuardrails_TaskScope_And_Continuity_Budget')
        receipt['gates_passed'].append('G6i_Verity_Cryptographic_Receipt_Schema_And_Fingerprint')

def _run_gate6j_to_gate6n_checks(spec: StationVerificationSpec, receipt: Dict[str, Any], raw_target: Callable[..., Any]) -> None:
    if spec.impossiblebench_audit_spec is not None and spec.small_input_kwargs:
        ib_res = evaluate_impossible_canary_and_anti_sycophancy(target_fn=spec.target_fn, sample_input_kwargs=spec.small_input_kwargs, solver_source_code=spec.impossiblebench_audit_spec.get('solver_source_code', spec.solver_source_code or ''), contradictory_delta=_finite_float(_cfg_value(spec.impossiblebench_audit_spec, 'contradictory_delta', 10.0)), tol=spec.oracle_tol, impossible_spec_trials=spec.impossiblebench_audit_spec.get('impossible_spec_trials'))
        if ib_res['status'] != 'PASS':
            raise AntiGoodhartGateError(f"[Gate 6j/7f ImpossibleBench Conflicting Canary / Anti-Sycophancy Failure] ast_cheating={ib_res['ast_cheating_findings']}, referentially_transparent={ib_res['referentially_transparent']}, canary_falsely_passed={ib_res['canary_falsely_passed']}, sycophancy_violations={ib_res['sycophancy_violations']}")
        receipt['gate6j_7f_impossiblebench'] = {'referentially_transparent': ib_res['referentially_transparent'], 'canary_falsely_passed': ib_res['canary_falsely_passed'], 'honest_interventions': ib_res['honest_interventions'], 'sycophancy_violation_count': len(ib_res['sycophancy_violations'])}
        receipt['gates_passed'].append('G6j_ImpossibleBench_ConflictingCanary_And_ReferentialTransparency')
        receipt['gates_passed'].append('G7f_ImpossibleBench_AntiSycophancy_ContradictorySpec_Flag')
    if spec.falsegreen_test_audit_spec is not None:
        fg_res = audit_test_suite_falsegreen_and_mock_abuse(test_source_code=spec.falsegreen_test_audit_spec['test_source_code'], target_fn_names=spec.falsegreen_test_audit_spec.get('target_fn_names', [raw_target.__name__]))
        if fg_res['status'] != 'PASS':
            raise AntiGoodhartGateError(f"[Gate 6k/6l FalseGreen Hollow-Test / Self-Mocking Failure] hollow={fg_res['hollow_findings']}, mock={fg_res['mock_findings']}")
        receipt['gate6k_6l_falsegreen_test_audit'] = {'test_count': fg_res['test_count'], 'hollow_finding_count': fg_res['hollow_finding_count'], 'mock_finding_count': fg_res['mock_finding_count'], 'assertion_analysis': fg_res['assertion_analysis'], 'assurance_scope': fg_res['assurance_scope']}
        receipt['gates_passed'].append('G6k_FalseGreen_No_Hollow_Or_Tautological_Tests')
        receipt['gates_passed'].append('G6l_FalseGreen_Zero_SelfMocking_And_BogusMockAssert')
    if spec.splitguard_leakage_audit_spec is not None:
        sg_res = audit_splitguard_row_and_group_leakage(**spec.splitguard_leakage_audit_spec)
        if sg_res['status'] != 'PASS':
            raise AntiGoodhartGateError(f"[Gate 6m/7g SplitGuard Data-Leakage / Group-Split Failure] ast_leakage={sg_res['ast_leakage_findings']}, runtime_leakage={sg_res['runtime_leakage_events']}")
        receipt['gate6m_7g_splitguard_leakage'] = {'ast_finding_count': len(sg_res['ast_leakage_findings']), 'runtime_leakage_count': len(sg_res['runtime_leakage_events']), 'duplicate_row_overlap': sg_res['duplicate_row_overlap'], 'overlapping_groups': sg_res['overlapping_groups']}
        receipt['gates_passed'].append('G6m_DataLeakage_No_PreSplit_FitTransform')
        receipt['gates_passed'].append('G7g_SplitGuard_Zero_RowTaint_And_GroupSplit_Leakage')
    if spec.self_hosting_dogfood_audit:
        sh_res = audit_engine_self_hosting_integrity()
        if sh_res['status'] != 'PASS':
            raise AntiGoodhartGateError(f'[Gate 6n Self-Hosting Dogfood Integrity Failure] AWF Guard failed its own static/quality/capsule audit: {sh_res}')
        receipt['gate6n_self_hosting_dogfood'] = {'total_functions_checked': sh_res['total_functions_checked'], 'max_observed_function_lines': sh_res['max_observed_function_lines'], 'violation_count': 0, 'files_audited': sh_res['files_audited'], 'target_present': True}
        receipt['gates_passed'].append('G6n_SelfHosting_ZeroViolation_Dogfood_Audit')

class ProvenanceStages:
    """Legacy private stage adapter; the engine uses explicit functions."""
    _run_gate6_provenance_and_harness_checks = staticmethod(_run_gate6_provenance_and_harness_checks)
    _run_gate6j_to_gate6n_checks = staticmethod(_run_gate6j_to_gate6n_checks)
