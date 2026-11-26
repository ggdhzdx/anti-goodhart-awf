"""AWF Guard: invariant stages."""
from __future__ import annotations

import ast
from typing import Any, Callable, Dict, Optional, Tuple
import numpy as np

from awf_guard_numeric_contracts import finite_call as _finite_call
from awf_guard_numeric_contracts import finite_float as _finite_float
from .agent_security import audit_agent_patterns_and_tool_registry, audit_security_and_quality_patterns
from .ast_dataflow import detect_extensional_enumeration_and_dispatch
from .ast_mutation import (
    _DEFAULT_MUTATION_MAX_ATOL,
    _DEFAULT_MUTATION_MAX_RTOL,
    _DEFAULT_MUTATION_MIN_KILL_RATE,
    evaluate_ast_mutation_kill_rate,
    scan_ast_for_loose_tolerance_inflation,
)
from .ast_structure import audit_ast_pair_diff, scan_ast_for_harness_tampering
from .errors import AntiGoodhartGateError, SecondOrderCollusionError
from .evidence_contracts import call_without_target_reentry
from .harness import scan_ast_for_test_file_reading_and_heuristic_cutoff
from .input_contracts import verify_pure_input_immutability_and_contracts
from .metamorphic import execute_metamorphic_relation_suite
from .numeric_inputs import _extract_array, _kwargs_materially_differ
from .numerical_stability import _DEFAULT_MCA_MAX_CONDITION_NUMBER, evaluate_mca_and_precision_downgrade_stability
from .optimization_checks import audit_parameter_update_trajectory
from .shape_contracts import check_jaxtyping_shape_contract
from .static_audit import scan_ast_for_hardcoded_short_loops
from .station_spec import MetaBoundsPolicy, StationVerificationSpec, _cfg_value
from .trajectory import scan_b64_obfuscated_literals

_EXTREME_RESIDUAL_PROBE = 1e6


def _verify_gate1_limit_and_evaluator(
    spec: StationVerificationSpec,
    policy: MetaBoundsPolicy,
    receipt: Dict[str, Any],
    check_upper: Callable[[str, float, float], None],
) -> None:
    if spec.analytic_expected_fn is not None:
        if not spec.limit_input_kwargs:
            raise AntiGoodhartGateError('[Gate 1] `analytic_expected_fn` provided without `limit_input_kwargs`!')
        out_lim = _finite_call(spec.target_fn, **spec.limit_input_kwargs)
        arr_lim = _extract_array(out_lim)
        exp_lim = _extract_array(_finite_call(spec.analytic_expected_fn, out_lim))
        if isinstance(out_lim, (np.ndarray, float, int)):
            exp_shifted = _extract_array(_finite_call(spec.analytic_expected_fn, out_lim + 1.0))
            if exp_shifted.shape == exp_lim.shape and _finite_float(np.max(np.abs((exp_shifted - exp_lim) - 1.0))) <= 1e-9:
                raise AntiGoodhartGateError('[Gate 1 Analytic-Limit Tautology] `analytic_expected_fn` echoes candidate output!')
        err_lim = _finite_float(np.max(np.abs(arr_lim - exp_lim)))
        if err_lim > spec.limit_tol:
            raise AntiGoodhartGateError(
                f'[Gate 1 Analytic-Limit Failure] Max deviation {err_lim:.3e} > tol {spec.limit_tol:.3e}. '
                'Check for missing Jacobian/measure factors or wrong normalization!'
            )
        check_upper('G1_Analytic_Limit', err_lim, spec.limit_tol)
        receipt['gate1_analytic_limit_err'] = err_lim
        receipt['gates_passed'].append('G1_Analytic_Limit')
    if spec.evaluator_fn is not None:
        if spec.evaluator_ref_sample is None or spec.evaluator_null_sample is None or spec.evaluator_shifted_sample is None:
            raise AntiGoodhartGateError('[Gate 1 Evaluator] Missing ref, null, or shifted calibration sample!')
        if not _kwargs_materially_differ({'s': spec.evaluator_ref_sample}, {'s': spec.evaluator_null_sample}) or not _kwargs_materially_differ(
            {'s': spec.evaluator_ref_sample}, {'s': spec.evaluator_shifted_sample}
        ):
            raise AntiGoodhartGateError('[Gate 1 Evaluator] Calibration null/shifted samples must differ from reference sample!')
        s_id = _finite_float(_finite_call(spec.evaluator_fn, spec.evaluator_ref_sample, spec.evaluator_ref_sample.copy()))
        s_null = _finite_float(_finite_call(spec.evaluator_fn, spec.evaluator_ref_sample, spec.evaluator_null_sample))
        s_shift = _finite_float(_finite_call(spec.evaluator_fn, spec.evaluator_ref_sample, spec.evaluator_shifted_sample))
        if abs(s_id - 1.0) > 1e-05:
            raise AntiGoodhartGateError(f'[Gate 1 Evaluator Identity Failure] S(ref, ref) = {s_id:.6f} != 1.0.')
        eff_null_ceil = min(spec.null_score_ceiling, policy.max_null_score_ceiling)
        if s_null > eff_null_ceil:
            raise AntiGoodhartGateError(f'[Gate 1 Evaluator Null-Control Trap] Uncorrelated null baseline scored {s_null:.4f} (ceiling <= {eff_null_ceil:.4f}).')
        eff_shift_floor = max(spec.min_shift_drop, policy.min_shift_sensitivity_drop)
        if s_id - s_shift < eff_shift_floor:
            raise AntiGoodhartGateError(f'[Gate 1 Evaluator Shift-Sensitivity Trap] Shifted sample only dropped score by {s_id - s_shift:.4f} (< {eff_shift_floor:.4f}).')
        receipt['gate1_evaluator_calibration'] = {'s_identity': s_id, 's_null': s_null, 's_shifted': s_shift}
        receipt['gates_passed'].append('G1_Null_Shift_Calibration')


def _run_gate1_to_gate3_checks(
    spec: StationVerificationSpec,
    policy: MetaBoundsPolicy,
    receipt: Dict[str, Any],
    check_upper: Callable[[str, float, float], None],
    check_lower: Callable[[str, float, float], None],
) -> Tuple[Optional[np.ndarray], Any]:
    _verify_gate1_limit_and_evaluator(spec, policy, receipt, check_upper)
    arr_fast: Optional[np.ndarray] = None
    out_fast: Any = None
    if spec.small_input_kwargs:
        out_fast = _finite_call(spec.target_fn, **spec.small_input_kwargs)
        arr_fast = _extract_array(out_fast)
    if spec.tier >= 2 or spec.orthogonal_oracle_fn is not None:
        if spec.orthogonal_oracle_fn is None or not spec.small_input_kwargs:
            raise AntiGoodhartGateError('[Gate 2] Missing `orthogonal_oracle_fn` or `small_input_kwargs`.')
        try:
            out_ora = _finite_call(call_without_target_reentry, spec.orthogonal_oracle_fn, spec.target_fn, **spec.small_input_kwargs)
        except ValueError as exc:
            raise SecondOrderCollusionError(f'[Meta-Guard Collusive Oracle] {exc}') from exc
        arr_ora = _extract_array(out_ora)
        assert arr_fast is not None
        err_ora = (
            _finite_float(np.max(np.abs(arr_fast - arr_ora)))
            if spec.mode == 'deterministic'
            else _finite_float(abs(np.mean(arr_fast) - np.mean(arr_ora)) / (np.std(arr_ora) + 1e-08))
        )
        if err_ora > spec.oracle_tol:
            raise AntiGoodhartGateError(f'[Gate 2 Orthogonal-Oracle Mismatch] Fast operator deviated from textbook oracle by {err_ora:.3e} > tol {spec.oracle_tol:.3e}!')
        check_upper('G2_DualPath_Orthogonal_Oracle', err_ora, spec.oracle_tol)
        receipt['gate2_oracle_err'] = err_ora
        receipt['gates_passed'].append('G2_DualPath_Orthogonal_Oracle')
    if spec.symmetry_transform_fn is not None:
        if not spec.small_input_kwargs or arr_fast is None:
            raise AntiGoodhartGateError('[Gate 3a] `symmetry_transform_fn` requires `small_input_kwargs`.')
        sym_kwargs = _finite_call(spec.symmetry_transform_fn, dict(spec.small_input_kwargs))
        if not _kwargs_materially_differ(spec.small_input_kwargs, sym_kwargs, target_fn=spec.target_fn):
            raise AntiGoodhartGateError('[Gate 3a] `symmetry_transform_fn` produced an identity input mapping!')
        out_sym = _extract_array(_finite_call(spec.target_fn, **sym_kwargs))
        exp_sym = _extract_array(_finite_call(spec.equivariant_output_fn, out_fast)) if spec.equivariant_output_fn is not None else arr_fast
        err_sym = _finite_float(np.max(np.abs(out_sym - exp_sym))) if spec.mode == 'deterministic' else _finite_float(abs(np.mean(out_sym) - np.mean(exp_sym)))
        if err_sym > spec.oracle_tol:
            raise AntiGoodhartGateError(f'[Gate 3a Symmetry Violation] Output changed by {err_sym:.3e} under symmetry group action!')
        check_upper('G3a_Symmetry_Invariance', err_sym, spec.oracle_tol)
        receipt['gate3_symmetry_err'] = err_sym
        receipt['gates_passed'].append('G3a_Symmetry_Invariance')
    if spec.perturb_transform_fn is not None:
        if not spec.small_input_kwargs or arr_fast is None:
            raise AntiGoodhartGateError('[Gate 3b] `perturb_transform_fn` requires `small_input_kwargs`.')
        pert_kwargs = _finite_call(spec.perturb_transform_fn, dict(spec.small_input_kwargs))
        if not _kwargs_materially_differ(spec.small_input_kwargs, pert_kwargs, target_fn=spec.target_fn):
            raise AntiGoodhartGateError('[Gate 3b] `perturb_transform_fn` produced an identity input mapping!')
        out_pert = _extract_array(_finite_call(spec.target_fn, **pert_kwargs))
        delta_pert = _finite_float(np.max(np.abs(out_pert - arr_fast)))
        if delta_pert < spec.min_perturbation_delta:
            raise AntiGoodhartGateError(f'[Gate 3b Orthogonal-Perturbation Numbness] Output changed by only {delta_pert:.3e} (< {spec.min_perturbation_delta:.3e})!')
        check_lower('G3b_Perturbation_Sensitivity', delta_pert, spec.min_perturbation_delta)
        receipt['gate3_perturbation_delta'] = delta_pert
        receipt['gates_passed'].append('G3b_Perturbation_Sensitivity')
    return (arr_fast, out_fast)


def _run_gate3c_to_gate4_checks(
    spec: StationVerificationSpec,
    receipt: Dict[str, Any],
    arr_fast: Optional[np.ndarray],
    check_lower: Callable[[str, float, float], None],
) -> None:
    if spec.metamorphic_relations is not None:
        if not spec.metamorphic_relations:
            raise AntiGoodhartGateError('[Gate 3c] `metamorphic_relations` cannot be empty when specified.')
        mr_res = execute_metamorphic_relation_suite(spec.target_fn, spec.metamorphic_relations)
        receipt['gate3c_metamorphic_relations'] = mr_res['reports']
        receipt['gates_passed'].append('G3c_General_MultiSource_Metamorphic_Relation')
    if spec.output_dependent_metamorphic_relations is not None:
        if not spec.output_dependent_metamorphic_relations:
            raise AntiGoodhartGateError('[Gate 3d] `output_dependent_metamorphic_relations` cannot be empty when specified.')
        od_res = execute_metamorphic_relation_suite(spec.target_fn, spec.output_dependent_metamorphic_relations)
        if not all(r.get('source_outputs_accessed') is True for r in od_res['reports']):
            raise AntiGoodhartGateError('[Gate 3d] Output-dependent metamorphic relation never accessed `state.source_outputs`!')
        receipt['gate3d_output_dependent_metamorphic'] = od_res['reports']
        receipt['gates_passed'].append('G3d_OutputDependent_RoundTrip_Metamorphic_Relation')
    if spec.jaxtyping_shape_contract_checks is not None:
        checked_contracts = 0
        for j_chk in spec.jaxtyping_shape_contract_checks:
            s_dims: Dict[str, int] = dict(j_chk.get('initial_symbolic_dims', {}))
            v_dims: Dict[str, Tuple[bool, Tuple[int, ...]]] = {}
            for item_name, arr_shape, raw_spec in j_chk['tensors']:
                check_jaxtyping_shape_contract(
                    name=item_name,
                    arr_shape=tuple(arr_shape),
                    raw_spec_shape=raw_spec,
                    symbolic_dims=s_dims,
                    variadic_dims=v_dims,
                    atom_id=spec.station_id,
                    direction='ContractCheck',
                )
                checked_contracts += 1
        if checked_contracts < 1:
            raise AntiGoodhartGateError('[Gate 3e/3f] `jaxtyping_shape_contract_checks` verified 0 tensor contracts!')
        receipt['gate3ef_jaxtyping_contracts_verified'] = checked_contracts
        receipt['gates_passed'].append('G3e_Jaxtyping_Symbolic_Algebraic_Shape_Contract')
        receipt['gates_passed'].append('G3f_Jaxtyping_Variadic_Batch_And_Broadcast_Contract')
    if spec.design_by_contract_audit_spec is not None:
        if not spec.small_input_kwargs:
            raise AntiGoodhartGateError('[Gate 3g/3h] `design_by_contract_audit_spec` requires `small_input_kwargs`.')
        dbc_res = verify_pure_input_immutability_and_contracts(
            target_fn=spec.target_fn,
            sample_input_kwargs=spec.small_input_kwargs,
            pre_fn=spec.design_by_contract_audit_spec.get('pre_fn'),
            post_fn=spec.design_by_contract_audit_spec.get('post_fn'),
            adversarial_inputs=spec.design_by_contract_audit_spec.get('adversarial_inputs'),
        )
        if dbc_res['status'] != 'PASS' or int(dbc_res['adversarial_cases_tested']) < 1:
            raise AntiGoodhartGateError(
                f"[Gate 3g/3h Design-by-Contract / Input Immutability Failure] mutated_inputs={dbc_res['mutated_inputs']}, "
                f"contract_violations={dbc_res['contract_violations']}, adversarial_cases_tested={dbc_res['adversarial_cases_tested']}"
            )
        receipt['gate3g_3h_design_by_contract'] = {'mutated_inputs': dbc_res['mutated_inputs'], 'adversarial_cases_tested': dbc_res['adversarial_cases_tested']}
        receipt['gates_passed'].append('G3g_DealPure_InputImmutability_And_NoSideEffects')
        receipt['gates_passed'].append('G3h_CrossHair_Adversarial_Boundary_Contract_Fuzzing')
    if spec.constraint_ablation_kwargs is not None:
        if arr_fast is None or not _kwargs_materially_differ(spec.small_input_kwargs, spec.constraint_ablation_kwargs, target_fn=spec.target_fn):
            raise AntiGoodhartGateError('[Gate 4] `constraint_ablation_kwargs` must differ from `small_input_kwargs`!')
        out_abl = _extract_array(_finite_call(spec.target_fn, **spec.constraint_ablation_kwargs))
        shock = _finite_float(np.max(np.abs(out_abl - arr_fast)))
        if shock < spec.min_ablation_shock:
            raise AntiGoodhartGateError(f'[Gate 4 Constraint/Mask Bypass] Ablating boundary/masking constraint produced shock {shock:.3e} < {spec.min_ablation_shock:.3e}!')
        check_lower('G4_Constraint_Ablation_Shock', shock, spec.min_ablation_shock)
        receipt['gate4_ablation_shock'] = shock
        receipt['gates_passed'].append('G4_Constraint_Ablation_Shock')


def _run_gate5_manifold_and_ast_checks(
    spec: StationVerificationSpec,
    policy: MetaBoundsPolicy,
    receipt: Dict[str, Any],
    arr_fast: Optional[np.ndarray],
    out_fast: Any,
    check_upper: Callable[[str, float, float], None],
) -> None:
    if arr_fast is not None:
        if not np.all(np.isfinite(arr_fast)):
            raise AntiGoodhartGateError('[Gate 5 NaN/Inf Trap] Output contains NaN or Inf!')
        if arr_fast.size > 1:
            std_val = _finite_float(np.std(arr_fast))
            if std_val < spec.min_output_std:
                raise AntiGoodhartGateError(f'[Gate 5 Constant Collapse] Output std={std_val:.3e} < {spec.min_output_std:.3e}.')
    if spec.invariant_residual_fn is not None:
        if out_fast is None:
            raise AntiGoodhartGateError('[Gate 5a] `invariant_residual_fn` requires `small_input_kwargs` output!')
        res_val = abs(_finite_float(_finite_call(spec.invariant_residual_fn, out_fast)))
        if isinstance(out_fast, (np.ndarray, float, int)):
            res_hi = abs(_finite_float(_finite_call(spec.invariant_residual_fn, out_fast + _EXTREME_RESIDUAL_PROBE)))
            res_lo = abs(_finite_float(_finite_call(spec.invariant_residual_fn, out_fast - _EXTREME_RESIDUAL_PROBE)))
            if max(res_hi, res_lo) <= spec.residual_tol:
                raise AntiGoodhartGateError('[Gate 5a Tautological Residual] `invariant_residual_fn` stays <= residual_tol under +/-1e6 perturbations!')
        if res_val > spec.residual_tol:
            raise AntiGoodhartGateError(f'[Gate 5 Conservation Identity Violation] Residual {res_val:.3e} > tol {spec.residual_tol:.3e}.')
        check_upper('G5a_Conservation_Identity', res_val, spec.residual_tol)
        receipt['gate5_conservation_residual'] = res_val
        receipt['gates_passed'].append('G5a_Conservation_Identity')
    if spec.solver_source_code is not None:
        if not spec.solver_source_code.strip():
            raise AntiGoodhartGateError('[Gate 5b] `solver_source_code` cannot be empty or whitespace!')
        scan_ast_for_hardcoded_short_loops(spec.solver_source_code, min_allowed_bound=policy.min_allowed_iterative_loop_bound)
        solver_tree = ast.parse(spec.solver_source_code)
        tamper_v = scan_ast_for_harness_tampering(solver_tree)
        if tamper_v:
            raise AntiGoodhartGateError(f"[Gate 5b AST Anti-Tamper Guard] {tamper_v[0]['detail']}")
        enum_v = detect_extensional_enumeration_and_dispatch(solver_tree)
        if enum_v:
            raise AntiGoodhartGateError(f"[Gate 5b AST Anti-Memorization Guard] {enum_v[0]['detail']}")
        receipt['gates_passed'].append('G5b_AST_No_Short_Loops')
        receipt['gates_passed'].append('G5d_AST_AntiTamper_And_No_Enumeration')
        if spec.baseline_source_code is not None:
            if not spec.baseline_source_code.strip():
                raise AntiGoodhartGateError('[Gate 5e] `baseline_source_code` cannot be empty!')
            pair_res = audit_ast_pair_diff(spec.baseline_source_code, spec.solver_source_code)
            if pair_res['status'] != 'PASS':
                raise AntiGoodhartGateError(f"[Gate 5e Pair-Mode Structural Regression] {pair_res['violations'][0]['detail']}")
            receipt['gates_passed'].append('G5e_PairMode_No_Complexity_Collapse')
        if spec.forbidden_b64_literals is not None:
            if not spec.forbidden_b64_literals:
                raise AntiGoodhartGateError('[Gate 5f] `forbidden_b64_literals` cannot be empty when specified!')
            b64_hits = scan_b64_obfuscated_literals(spec.solver_source_code, spec.forbidden_b64_literals)
            if b64_hits:
                raise AntiGoodhartGateError(f"[Gate 5f 3-Alignment Base64 Obfuscation Guard] {b64_hits[0]['detail']}")
            receipt['gates_passed'].append('G5f_Base64_3Alignment_No_Obfuscated_Constants')
        eg_ast_v = scan_ast_for_test_file_reading_and_heuristic_cutoff(solver_tree)
        if eg_ast_v:
            raise AntiGoodhartGateError(f"[Gate 5g EvilGenie Test-File-Read / Heuristic-Cutoff Guard] {eg_ast_v[0]['detail']}")
        receipt['gates_passed'].append('G5g_AST_No_TestFileRead_Or_HeuristicCutoff')
    if spec.parameter_history_matrix is not None or spec.expected_total_dof is not None:
        if spec.parameter_history_matrix is None or spec.expected_total_dof is None:
            raise AntiGoodhartGateError('[Gate 5c] Both `parameter_history_matrix` and `expected_total_dof` are required together!')
        svd_info = audit_parameter_update_trajectory(
            spec.parameter_history_matrix,
            expected_total_dof=spec.expected_total_dof,
            min_active_fraction=spec.min_active_dof_fraction,
            min_effective_rank=spec.min_trajectory_svd_rank,
        )
        receipt['gate5_trajectory_svd'] = svd_info
        receipt['gates_passed'].append('G5c_Trajectory_SVD_FullRank')


def _run_gate5h_to_gate5l_checks(spec: StationVerificationSpec, receipt: Dict[str, Any]) -> None:
    if spec.agent_verifier_audit_spec is not None:
        av_src = spec.agent_verifier_audit_spec.get('source_code', spec.solver_source_code or '')
        if not isinstance(av_src, str) or not av_src.strip():
            raise AntiGoodhartGateError('[Gate 5h/5i] `agent_verifier_audit_spec` requires non-empty `source_code`!')
        av_pat = audit_agent_patterns_and_tool_registry(
            source_code=av_src,
            prompt_text=spec.agent_verifier_audit_spec.get('prompt_text', ''),
            registered_tools_override=spec.agent_verifier_audit_spec.get('registered_tools'),
        )
        if av_pat['status'] != 'PASS':
            raise AntiGoodhartGateError(f"[Gate 5h Agent-Verifier Pattern Failure] {av_pat['issues'][0]['detail']}")
        av_sec = audit_security_and_quality_patterns(
            source_code=av_src,
            requirements_text=spec.agent_verifier_audit_spec.get('requirements_text', ''),
        )
        if av_sec['status'] != 'PASS':
            raise AntiGoodhartGateError(f"[Gate 5i Agent-Verifier Security/Quality Failure] {av_sec['issues'][0]['detail']}")
        receipt['gate5h_5i_agent_verifier'] = {
            'defined_tools': av_pat['defined_tools'],
            'pattern_issues': av_pat['issue_count'],
            'security_quality_issues': av_sec['issue_count'],
        }
        receipt['gates_passed'].append('G5h_AgentVerifier_LoopRetry_ToolRegistry_And_GraphCycle')
        receipt['gates_passed'].append('G5i_AgentVerifier_ZeroSecrets_SwallowedExceptions_And_Quality')
    if spec.mutation_testing_audit_spec is not None:
        tol_src = spec.mutation_testing_audit_spec.get('test_source_code', (spec.falsegreen_test_audit_spec or {}).get('test_source_code', ''))
        if not isinstance(tol_src, str) or not tol_src.strip():
            raise AntiGoodhartGateError('[Gate 5k] `mutation_testing_audit_spec` requires non-empty `test_source_code`!')
        tol_findings = scan_ast_for_loose_tolerance_inflation(
            tol_src,
            max_allowed_atol=_finite_float(_cfg_value(spec.mutation_testing_audit_spec, 'max_allowed_atol', _DEFAULT_MUTATION_MAX_ATOL)),
            max_allowed_rtol=_finite_float(_cfg_value(spec.mutation_testing_audit_spec, 'max_allowed_rtol', _DEFAULT_MUTATION_MAX_RTOL)),
        )
        if tol_findings:
            raise AntiGoodhartGateError(f"[Gate 5k Anti-Loose-Tolerance Failure] {tol_findings[0]['detail']}")
        mut_res = evaluate_ast_mutation_kill_rate(
            fn_or_source=spec.mutation_testing_audit_spec.get('fn_or_source', spec.target_fn),
            assertion_check_fn=spec.mutation_testing_audit_spec['assertion_check_fn'],
            extra_globals=spec.mutation_testing_audit_spec.get('extra_globals'),
            min_kill_rate=_finite_float(_cfg_value(spec.mutation_testing_audit_spec, 'min_kill_rate', _DEFAULT_MUTATION_MIN_KILL_RATE)),
        )
        if mut_res['status'] != 'PASS' or int(mut_res['total_mutants']) < 1:
            raise AntiGoodhartGateError(f"[Gate 5j AST Mutation Kill-Rate Failure] kill_rate={mut_res['kill_rate']}, total_mutants={mut_res['total_mutants']}!")
        receipt['gate5j_5k_mutation_testing'] = {
            'total_mutants': mut_res['total_mutants'],
            'killed_mutants': mut_res['killed_mutants'],
            'kill_rate': mut_res['kill_rate'],
            'loose_tolerance_findings': len(tol_findings),
        }
        receipt['gates_passed'].append('G5j_Mutmut_AST_Mutation_Kill_Rate')
        receipt['gates_passed'].append('G5k_Anti_Loose_Tolerance_Inflation')
    if spec.numerical_stability_audit_spec is not None:
        if not spec.small_input_kwargs:
            raise AntiGoodhartGateError('[Gate 5l/1c] `numerical_stability_audit_spec` requires `small_input_kwargs`.')
        mca_src = spec.numerical_stability_audit_spec.get('source_code', spec.solver_source_code or '')
        if not isinstance(mca_src, str) or not mca_src.strip():
            raise AntiGoodhartGateError('[Gate 5l/1c] `numerical_stability_audit_spec` requires non-empty `source_code`!')
        mca_res = evaluate_mca_and_precision_downgrade_stability(
            target_fn=spec.target_fn,
            sample_input_kwargs=spec.small_input_kwargs,
            source_code=mca_src,
            n_mca_trials=int(_cfg_value(spec.numerical_stability_audit_spec, 'n_mca_trials', 8)),
            relative_noise_sigma=_finite_float(_cfg_value(spec.numerical_stability_audit_spec, 'relative_noise_sigma', 1e-07)),
            max_allowed_rel_drift=_finite_float(_cfg_value(spec.numerical_stability_audit_spec, 'max_allowed_rel_drift', 0.0001)),
            max_condition_number=_finite_float(_cfg_value(spec.numerical_stability_audit_spec, 'max_condition_number', _DEFAULT_MCA_MAX_CONDITION_NUMBER)),
        )
        if mca_res['status'] != 'PASS':
            raise AntiGoodhartGateError(
                f"[Gate 5l/1c PitfallsFP / MCA Conditioning Failure] ast_pitfalls={mca_res['ast_pitfalls']}, "
                f"f32_rel_drift={mca_res['f32_rel_drift']}, max_mca_rel_drift={mca_res['max_mca_rel_drift']}, "
                f"cond={mca_res['empirical_condition_number']}"
            )
        receipt['gate5l_1c_mca_conditioning'] = {
            'f32_rel_drift': mca_res['f32_rel_drift'],
            'max_mca_rel_drift': mca_res['max_mca_rel_drift'],
            'empirical_condition_number': mca_res['empirical_condition_number'],
        }
        receipt['gates_passed'].append('G5l_PitfallsFP_No_NaiveInverse_Or_UnstableLogSumExp')
        receipt['gates_passed'].append('G1c_MCA_StochasticRounding_And_PrecisionDowngrade_Stability')


class InvariantStages:
    """Legacy private stage adapter; the engine uses explicit functions."""
    _run_gate1_to_gate3_checks = staticmethod(_run_gate1_to_gate3_checks)
    _run_gate3c_to_gate4_checks = staticmethod(_run_gate3c_to_gate4_checks)
    _run_gate5_manifold_and_ast_checks = staticmethod(_run_gate5_manifold_and_ast_checks)
    _run_gate5h_to_gate5l_checks = staticmethod(_run_gate5h_to_gate5l_checks)
