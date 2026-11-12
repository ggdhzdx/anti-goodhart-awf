"""AWF Guard: self audit."""
from __future__ import annotations
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from pathlib import Path
from typing import Tuple
from awf_guard_numeric_contracts import finite_inputs as _finite_inputs
import ast
from .source_quality import DEFAULT_MAX_FUNCTION_LINES
from .fixture_policy import reviewed_fixture_numbers
from .agent_security import audit_agent_patterns_and_tool_registry
from .static_audit import audit_ast_path
from .benchmark import audit_benchmark_hackability
from .agent_security import audit_security_and_quality_patterns
from .test_quality import audit_test_suite_falsegreen_and_mock_abuse
from .numerical_stability import scan_ast_for_floating_point_pitfalls
from .ast_mutation import scan_ast_for_loose_tolerance_inflation
from .data_leakage import scan_ast_for_pre_split_preprocessing_leakage
from .canary import scan_ast_for_stateful_call_counter_and_operator_spoof
from .source_quality import scan_source_for_todo_placeholders_and_magic_numbers
_SELF_AUDIT_TEST_ROLE_FILES: Tuple[str, ...] = ('test_modular_integrity.py', 'test_nonfinite_campaign.py', 'test_rc3_contracts.py', 'test_function_line_limit.py', 'awf_anti_goodhart_selftest_suite.py', 'awf_anti_goodhart_negative_controls.py', 'awf_anti_goodhart_mutation_adequacy.py', 'probe_ag_v37.py', 'awf_guard_selftests/__init__.py', 'awf_guard_selftests/ast_and_truth.py', 'awf_guard_selftests/build_selftest_atoms_and_oracle.py', 'awf_guard_selftests/calibrated_morph_and_optics_pack.py', 'awf_guard_selftests/calibrated_scientific_pack_v34.py', 'awf_guard_selftests/gemtest_benchjack_and_goodhart.py', 'awf_guard_selftests/guardrails_aurite_impossible_and_falsegreen.py', 'awf_guard_selftests/mutmut_dbc_splitguard_and_pitfallsfp.py', 'awf_guard_selftests/runner.py', 'awf_guard_selftests/scientific_computing_pack.py', 'awf_guard_selftests/trajectory_and_evilgenie.py', 'awf_guard_selftests/tutor_implementation_goodhart.py', 'test_execution_flow.py', 'awf_guard_selftests/geometry_checks.py', 'awf_guard_selftests/statistical_checks.py', 'awf_guard_selftests/matrix_checks.py', 'awf_guard_selftests/coupled_declarative_scenario.py', 'awf_guard_selftests/geometry_fixtures.py')
_SELF_AUDIT_FALSEGREEN_FILES: Tuple[str, ...] = ('awf_anti_goodhart_selftest_suite.py', 'awf_anti_goodhart_negative_controls.py', 'awf_guard_selftests/__init__.py', 'awf_guard_selftests/ast_and_truth.py', 'awf_guard_selftests/build_selftest_atoms_and_oracle.py', 'awf_guard_selftests/calibrated_morph_and_optics_pack.py', 'awf_guard_selftests/calibrated_scientific_pack_v34.py', 'awf_guard_selftests/gemtest_benchjack_and_goodhart.py', 'awf_guard_selftests/guardrails_aurite_impossible_and_falsegreen.py', 'awf_guard_selftests/mutmut_dbc_splitguard_and_pitfallsfp.py', 'awf_guard_selftests/runner.py', 'awf_guard_selftests/scientific_computing_pack.py', 'awf_guard_selftests/trajectory_and_evilgenie.py', 'awf_guard_selftests/tutor_implementation_goodhart.py', 'test_execution_flow.py', 'awf_guard_selftests/geometry_checks.py', 'awf_guard_selftests/statistical_checks.py', 'awf_guard_selftests/matrix_checks.py', 'awf_guard_selftests/coupled_declarative_scenario.py', 'awf_guard_selftests/geometry_fixtures.py')
_SELF_AUDIT_TEST_SUPPORT_FILES = ('awf_anti_goodhart_selftest_suite.py', 'awf_guard_selftests/__init__.py', 'awf_guard_selftests/build_selftest_atoms_and_oracle.py', 'awf_guard_selftests/runner.py', 'awf_guard_selftests/geometry_fixtures.py', 'awf_guard_selftests/calibrated_morph_and_optics_pack.py')
_SELF_AUDIT_MAX_FILE_LINES = 1000
_SELF_AUDIT_TEST_ROLE_FILES += ('test_evidence_escapes.py',)
_SELF_AUDIT_FALSEGREEN_FILES += ('test_evidence_escapes.py',)
_SELF_AUDIT_DECLARED_FILE_SIZE_WAIVERS: Dict[str, str] = {}

def _self_audit_single_file(py_path: Path, max_fn_lines: Optional[int], audit_root: Path) -> Dict[str, Any]:
    src = py_path.read_text(encoding='utf-8')
    tree = ast.parse(src)
    relative_name = py_path.relative_to(audit_root).as_posix()
    is_test_role = relative_name in _SELF_AUDIT_TEST_ROLE_FILES
    aux_findings = scan_ast_for_stateful_call_counter_and_operator_spoof(tree) + scan_ast_for_floating_point_pitfalls(tree) + scan_ast_for_loose_tolerance_inflation(tree) + scan_ast_for_pre_split_preprocessing_leakage(tree)
    counts = {'ast_violation_count': int(audit_ast_path(py_path, max_atom_lines=max_fn_lines)['violation_count']), 'security_quality_issue_count': int(audit_security_and_quality_patterns(src)['issue_count']), 'agent_pattern_issue_count': int(audit_agent_patterns_and_tool_registry(src)['issue_count']), 'benchjack_finding_count': int(audit_benchmark_hackability({py_path.name: src})['finding_count']), 'auxiliary_scanner_finding_count': len(aux_findings), 'g5n_finding_count': int(scan_source_for_todo_placeholders_and_magic_numbers(src, check_magic_numbers=True, allowed_numeric_literals=reviewed_fixture_numbers(py_path, audit_root))['finding_count']), 'falsegreen_finding_count': 0}
    if relative_name in _SELF_AUDIT_FALSEGREEN_FILES:
        fg = audit_test_suite_falsegreen_and_mock_abuse(src)
        counts['falsegreen_finding_count'] = int(fg['hollow_finding_count']) + int(fg['mock_finding_count']) + (0 if fg['test_count'] > 0 or relative_name in _SELF_AUDIT_TEST_SUPPORT_FILES else 1)
    fn_spans = {f'{py_path.name}:{node.name}@{node.lineno}': getattr(node, 'end_lineno', node.lineno) - node.lineno + 1 for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
    return {'counts': counts, 'fn_spans': fn_spans, 'file_lines': src.count('\n') + 1, 'is_test_role': is_test_role}

@_finite_inputs
def audit_engine_self_hosting_integrity(engine_file_path: Optional[Path]=None, max_fn_lines: Optional[int]=None, include_colocated_scripts: bool=True, max_file_lines: Optional[int]=None) -> Dict[str, Any]:
    """
    Self-Referential Dogfooding Gate (`G6n_SelfHosting_ZeroViolation_Dogfood_Audit`):
    Audits `AWF Guard`'s own source code (and all co-located `.py` scripts in `scripts/` when
    `include_colocated_scripts=True`) against all of its static, `G5n` placeholder/unused-var/stub
    circuit-breaker (magic-number check ON for every non-test-role file), falsegreen `G6k`/`G6l`
    (test-suite files), security, quality, agent-pattern, BenchJack V1-V8, PitfallsFP, Mutmut tolerance,
    DataLeakage and caller-declared size contracts. Length alone is advisory by default.
    Requires strictly 0 unwaived violations; declared file-size waivers are reported, never hidden.
    """
    target_py = (engine_file_path or Path(__file__).resolve().parent.parent / 'awf_universal_anti_goodhart_gates.py').resolve()
    if not target_py.is_file():
        raise ValueError("Audit target must be an existing source file")
    files_to_audit: List[Path] = [target_py]
    if include_colocated_scripts and target_py.parent.is_dir():
        files_to_audit = sorted(target_py.parent.rglob('*.py'))
    if not files_to_audit or target_py not in files_to_audit:
        raise ValueError("Audit must include the requested source file")
    totals: Dict[str, int] = {}
    fn_lengths: Dict[str, int] = {}
    oversized_files: List[Dict[str, Any]] = []
    waived: List[Dict[str, Any]] = []
    size_review_items: List[Dict[str, Any]] = []
    test_role_files: List[str] = []
    for py_path in files_to_audit:
        res = _self_audit_single_file(py_path, max_fn_lines, target_py.parent)
        for key, val in res['counts'].items():
            totals.setdefault(key, 0)
            totals[key] += val
        fn_lengths.update({f'{py_path.relative_to(target_py.parent).as_posix()}::{key}': value for key, value in res['fn_spans'].items()})
        if res['is_test_role']:
            test_role_files.append(py_path.relative_to(target_py.parent).as_posix())
        relative_name = py_path.relative_to(target_py.parent).as_posix()
        if res['file_lines'] > _SELF_AUDIT_MAX_FILE_LINES:
            size_review_items.append({'kind': 'file', 'file': relative_name, 'lines': res['file_lines'], 'threshold': _SELF_AUDIT_MAX_FILE_LINES})
        if max_file_lines is not None and res['file_lines'] > max_file_lines:
            oversized_files.append({'file': relative_name, 'lines': res['file_lines'], 'limit': max_file_lines})
    size_review_items.extend(({'kind': 'function', 'function': key, 'lines': span, 'threshold': DEFAULT_MAX_FUNCTION_LINES} for key, span in fn_lengths.items() if span > DEFAULT_MAX_FUNCTION_LINES))
    oversized_fns = [{'function': key, 'lines': span, 'limit': max_fn_lines} for key, span in fn_lengths.items() if max_fn_lines is not None and span > max_fn_lines]
    passed = all((v == 0 for v in totals.values())) and (not oversized_fns) and (not oversized_files)
    return {'status': 'PASS' if passed else 'FAIL', 'engine_file': str(target_py), 'files_audited': [p.relative_to(target_py.parent).as_posix() for p in files_to_audit], 'magic_number_exempt_test_role_files': [], 'reviewed_numeric_fixture_files': [str(p.relative_to(target_py.parent)) for p in files_to_audit if reviewed_fixture_numbers(p, target_py.parent) is not None], 'total_functions_checked': len(fn_lengths), 'max_observed_function_lines': max(fn_lengths.values()) if fn_lengths else 0, 'max_allowed_function_lines': max_fn_lines, 'oversized_functions': oversized_fns, 'max_allowed_file_lines': max_file_lines, 'oversized_files_unwaived': oversized_files, 'declared_waivers': waived, 'size_policy': 'advisory_by_default_explicit_limits_enforced', 'size_review_items': size_review_items, **totals}
