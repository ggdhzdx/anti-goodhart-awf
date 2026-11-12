"""AWF Guard: runtime."""
from __future__ import annotations
from typing import Any
from typing import Dict
from awf_guard_numeric_contracts import finite_call as _finite_call
import os
import sys
import tempfile
from .errors import AntiGoodhartGateError
from .errors import BorderlineThresholdHuggingError
from .atoms import GLOBAL_ATOM_REGISTRY
from .station_spec import MetaBoundsPolicy
from .station_spec import StationVerificationSpec
from .slot_receipts import _consolidate_to_14_universal_slots
from .ast_utils import _unwrap_target_fn
from .spec_integrity import audit_spec_integrity
from .information import generate_abstract_retry_feedback
from .execution_flow import execute_stage
from .invariant_stages import _run_gate1_to_gate3_checks
from .invariant_stages import _run_gate3c_to_gate4_checks
from .invariant_stages import _run_gate5_manifold_and_ast_checks
from .invariant_stages import _run_gate5h_to_gate5l_checks
from .provenance_stages import _run_gate6_provenance_and_harness_checks
from .provenance_stages import _run_gate6j_to_gate6n_checks
from .scientific_stages import _run_scientific_computing_pack_checks
from .scientific_stages import _run_calibrated_scientific_invariant_checks
from .scientific_stages import _run_calibrated_diffraction_quantum_and_slot_checks
from .holdout_stages import _run_gate7_holdout_and_claim_checks

class UniversalAntiGoodhartEngine:

    @classmethod
    def run_station_gates(cls, spec: StationVerificationSpec, policy: MetaBoundsPolicy=MetaBoundsPolicy()) -> Dict[str, Any]:
        receipt: Dict[str, Any] = {'station_id': spec.station_id, 'station_name': spec.station_name, 'tier': spec.tier, 'mode': spec.mode, 'verdict_zone': 'PASS', 'requires_human_approval': False, 'borderline_warnings': [], 'gates_passed': []}
        if spec.tier == 0:
            if not spec.socratic_premortem_question or not spec.socratic_premortem_analytic_trap:
                raise AntiGoodhartGateError('[Tier-0 Socratic Gate] Station must define `socratic_premortem_question` and `socratic_premortem_analytic_trap`.')
            receipt['gates_passed'].append('Tier0_Socratic_PreMortem')
            return receipt
        audit_spec_integrity(spec, policy)
        receipt['gates_passed'].append('MetaGuard_AntiCollusion')
        atom_meta = getattr(spec.target_fn, '_atom_metadata', None)
        if atom_meta is not None:
            receipt['atom_id'] = atom_meta['atom_id']
            receipt['gates_passed'].append('AtomCapsule_ContractBus')
            if 'ast_called_symbols' in atom_meta:
                receipt['ast_called_symbols'] = atom_meta['ast_called_symbols']
                receipt['gates_passed'].append('AST_DependencyGraph_CrossCheck')
            if atom_meta.get('parameter_taint_flow'):
                receipt['parameter_taint_flow'] = atom_meta['parameter_taint_flow']
                receipt['gates_passed'].append('AST_ParameterTaint_Dataflow')
                receipt['gates_passed'].append('AST_Intent_Structure_Alignment')
        if spec.sealed_holdout_capsule is not None:
            receipt['sealed_holdout_commitment'] = spec.sealed_holdout_capsule.commitment_sha256
            receipt['gates_passed'].append('BoundarySeal_InformationAsymmetry')
        call_counter = {'count': 0}
        raw_target = _finite_call(_unwrap_target_fn, spec.target_fn)
        target_code = getattr(raw_target, '__code__', None)

        def _trace_calls(frame: Any, event: str, _arg: Any) -> Any:
            if event == 'call' and target_code is not None and (frame.f_code is target_code):
                call_counter['count'] += 1
            return _trace_calls

        def _check_borderline_upper(gate_label: str, err_val: float, tol_val: float) -> None:
            if tol_val > 0 and err_val / tol_val >= policy.borderline_margin_ratio:
                receipt['borderline_warnings'].append(f'[{gate_label} Borderline Threshold-Hugging] error={err_val:.3e} is at {err_val / tol_val * 100:.1f}% of tolerance ceiling ({tol_val:.3e}).')

        def _check_borderline_lower(gate_label: str, val: float, floor_val: float) -> None:
            if floor_val > 0:
                raw_ceil = floor_val / max(policy.borderline_margin_ratio, 1e-06)
                if floor_val < 1.0 and val <= 1.0 and (raw_ceil >= 1.0):
                    eff_ceil = floor_val + (1.0 - floor_val) * (1.0 - policy.borderline_margin_ratio)
                else:
                    eff_ceil = raw_ceil
                if val <= eff_ceil:
                    receipt['borderline_warnings'].append(f'[{gate_label} Borderline Floor-Hugging] value={val:.4g} barely cleared floor={floor_val:.4g}.')
        orig_cwd = os.getcwd()
        temp_ctx = tempfile.TemporaryDirectory(prefix='ag_cleanroom_') if spec.cleanroom_chdir else None
        sys.settrace(_trace_calls)
        try:
            if temp_ctx is not None:
                os.chdir(temp_ctx.name)
                receipt['gates_passed'].append('CleanRoom_Tempdir_Sandbox')
            arr_fast, out_fast = execute_stage(_run_gate1_to_gate3_checks, receipt, spec=spec, policy=policy, check_upper=_check_borderline_upper, check_lower=_check_borderline_lower)
            execute_stage(_run_gate3c_to_gate4_checks, receipt, spec=spec, arr_fast=arr_fast, check_lower=_check_borderline_lower)
            execute_stage(_run_gate5_manifold_and_ast_checks, receipt, spec=spec, policy=policy, arr_fast=arr_fast, out_fast=out_fast, check_upper=_check_borderline_upper)
            execute_stage(_run_gate5h_to_gate5l_checks, receipt, spec=spec)
            execute_stage(_run_gate6_provenance_and_harness_checks, receipt, spec=spec, policy=policy, raw_target=raw_target)
            execute_stage(_run_gate6j_to_gate6n_checks, receipt, spec=spec, raw_target=raw_target)
            execute_stage(_run_scientific_computing_pack_checks, receipt, spec=spec)
            execute_stage(_run_gate7_holdout_and_claim_checks, receipt, spec=spec, policy=policy, check_upper=_check_borderline_upper, check_lower=_check_borderline_lower)
        finally:
            sys.settrace(None)
            os.chdir(orig_cwd)
            if temp_ctx is not None:
                temp_ctx.cleanup()
        if target_code is not None and call_counter['count'] < 1:
            raise AntiGoodhartGateError('[Gate 6 Phantom Dead-Code Trap] `target_fn` was never actually invoked during verification!')
        receipt['gate6_dynamic_calls'] = call_counter['count']
        receipt['gates_passed'].append('G6_Dynamic_Execution_Lineage')
        if receipt['borderline_warnings']:
            receipt['verdict_zone'] = 'BORDERLINE_NEEDS_HUMAN_REVIEW'
            receipt['requires_human_approval'] = True
            receipt['abstract_remediation_feedback'] = generate_abstract_retry_feedback(receipt)
            if policy.strict_reject_borderline:
                raise BorderlineThresholdHuggingError(f"[Tri-State Borderline Rejection] Operator landed in the marginal threshold-hugging zone ({len(receipt['borderline_warnings'])} warning(s)): {' | '.join(receipt['borderline_warnings'])}")
        receipt['gates_passed'].append('TriState_Verdict_Audit')
        _consolidate_to_14_universal_slots(receipt)
        if atom_meta is not None and atom_meta['atom_id'] in GLOBAL_ATOM_REGISTRY:
            GLOBAL_ATOM_REGISTRY[atom_meta['atom_id']]['gate_status'] = f"{receipt['verdict_zone']} ({len(receipt['gates_passed'])} universal slots / {receipt['subchecks_verified_count']} subchecks)"
        return receipt
