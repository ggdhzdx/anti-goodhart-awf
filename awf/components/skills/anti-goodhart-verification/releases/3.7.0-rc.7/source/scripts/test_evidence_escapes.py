"""Regression cases for vacuous evidence and name-based trust, with honest controls."""
import functools
import json
from pathlib import Path
import tempfile
from awf_guard import api as ag


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def correct(x):
    return x + 1


def reference(x):
    return 1 + x


def wrong(x):
    return x - 1


def rejected(action):
    caught = False
    result = None
    try:
        result = action()
    except (ValueError, ag.AntiGoodhartGateError):
        caught = True
    return caught or isinstance(result, dict) and result.get('status') != 'PASS'


def test_nonempty_comparisons():
    source = 'def transform(x):\n    return x + 1\n'
    base = dict(target_fn=correct, reference_or_invariant_fn=reference, solver_source_code=source)
    require(rejected(lambda: ag.evaluate_red_blue_adversarial_audit(**base, adversarial_probe_inputs=[])), 'empty red-blue probes accepted')
    good = ag.evaluate_red_blue_adversarial_audit(**base, adversarial_probe_inputs=[{'x': 2}])
    require(good['status'] == 'PASS' and good['executed_probe_count'] == 1, 'honest red-blue control')
    repair = dict(pre_fix_source=source, post_fix_source=source, reference_oracle_fn=reference)
    require(rejected(lambda: ag.verify_remediation_closed_loop_and_pareto_candidates(**repair, candidate_implementations={'bad': wrong}, evaluation_inputs=[])), 'empty remediation accepted')
    good = ag.verify_remediation_closed_loop_and_pareto_candidates(**repair, candidate_implementations={'good': correct, 'bad': wrong}, evaluation_inputs=[{'x': 2}])
    require(good['status'] == 'PASS' and good['selected_pareto_candidate'] == 'good', 'honest candidate was not selected')
    require(all(r['executed_evaluation_count'] == 1 for r in good['candidate_leaderboard']), 'missing per-candidate evidence')


def test_missing_source():
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / 'absent.py'
        require(rejected(lambda: ag.audit_engine_self_hosting_integrity(path)), 'missing source accepted')
        path.write_text('def transform(x):\n    return x + 1\n')
        good = ag.audit_engine_self_hosting_integrity(path)
        require(good['status'] == 'PASS' and good['files_audited'] == ['absent.py'], 'real source rejected')


def test_unreachable_assertions():
    bodies = ['if False:\n        assert value == 2', 'return\n    assert value == 2',
              'def hidden():\n        assert value == 2', 'while False:\n        assert value == 2']
    for body in bodies:
        result = ag.audit_test_suite_falsegreen_and_mock_abuse('def test_case(value):\n    ' + body + '\n')
        require(result['status'] == 'FAIL', 'unexecuted assertion counted')
    fake = 'def assert_equal(a, b):\n    return (a, b)\ndef test_case(value):\n    assert_equal(value, 2)\n'
    require(ag.audit_test_suite_falsegreen_and_mock_abuse(fake)['status'] == 'FAIL', 'shadowed assertion trusted')
    tautological = 'def assert_equal(a, b):\n    assert True\ndef test_case(value):\n    assert_equal(value, 2)\n'
    require(ag.audit_test_suite_falsegreen_and_mock_abuse(tautological)['status'] == 'FAIL', 'tautological assertion helper trusted')
    for source in ['def test_case(value):\n    assert value == 2\n',
                   'def test_case(value):\n    if True:\n        assert value == 2\n',
                   'from numpy.testing import assert_equal\ndef test_case(value):\n    assert_equal(value, 2)\n']:
        require(ag.audit_test_suite_falsegreen_and_mock_abuse(source)['status'] == 'PASS', 'honest assertion rejected')


def test_role_names():
    source = 'def transform(x):\n    return x * 1.23456789\n'
    require(ag.scan_source_for_todo_placeholders_and_magic_numbers(source.replace('transform', 'test_transform'))['status'] == 'FAIL', 'function name exemption')
    with tempfile.TemporaryDirectory() as directory:
        entry = Path(directory) / 'entry.py'
        entry.write_text('def transform(x):\n    return x + 1\n')
        candidate = Path(directory) / 'test_rc3_contracts.py'
        candidate.write_text(source)
        require(ag.audit_engine_self_hosting_integrity(entry)['status'] == 'FAIL', 'filename exemption')
    require(ag.scan_source_for_todo_placeholders_and_magic_numbers(source, allowed_numeric_literals=[1.23456789])['status'] == 'PASS', 'explicit justified numeric contract rejected')


def test_upstream_receipts():
    correct._atom_metadata = {'upstream_atoms': ['upstream']}
    receipt = {'atom_id': 'upstream', 'verdict_zone': 'PASS', 'tier': 1, 'gates_passed': ['verified_contract']}
    kwargs = dict(mca_condition_number=1, invariant_anchor_count=2)
    try:
        for status in ('PASS_BUT_FAILED', 'VERIFIED_FALSE', 'FAIL', 'REGISTERED'):
            manifest = {'upstream': {'gate_status': status, 'last_verification_receipt': receipt}}
            require(ag.verify_microstep_granularity_and_topological_anchor(correct, atom_manifest=manifest, **kwargs)['status'] == 'FAIL', 'status prefix accepted')
        require(ag.verify_microstep_granularity_and_topological_anchor(correct, atom_manifest={'upstream': {'gate_status': 'PASS'}}, **kwargs)['status'] == 'FAIL', 'unbacked upstream accepted')
        manifest = {'upstream': {'gate_status': 'PASS', 'last_verification_receipt': receipt}}
        require(ag.verify_microstep_granularity_and_topological_anchor(correct, atom_manifest=manifest, **kwargs)['status'] == 'PASS', 'valid upstream receipt rejected')
    finally:
        del correct._atom_metadata
    require(ag.verify_microstep_granularity_and_topological_anchor(correct)['status'] == 'FAIL', 'default numbers presented as evidence')


def test_independent_reference():
    base = dict(target_fn=correct, adversarial_probe_inputs=[{'x': 2}], solver_source_code='def transform(x):\n    return x + 1\n')
    for fake in (correct, functools.partial(correct), functools.wraps(correct)(lambda x: correct(x))):
        require(rejected(lambda: ag.evaluate_red_blue_adversarial_audit(**base, reference_or_invariant_fn=fake)), 'same-origin reference accepted')
    require(ag.evaluate_red_blue_adversarial_audit(**base, reference_or_invariant_fn=reference)['status'] == 'PASS', 'separate reference rejected')


CASES = (test_nonempty_comparisons, test_missing_source, test_unreachable_assertions,
         test_role_names, test_upstream_receipts, test_independent_reference)


def run_escape_regressions():
    rows = []
    for check in CASES:
        try:
            check()
        except Exception as error:
            rows.append({'case': check.__name__, 'status': 'FAIL', 'error': str(error)})
        else:
            rows.append({'case': check.__name__, 'status': 'PASS'})
    return {'status': 'PASS' if all(r['status'] == 'PASS' for r in rows) else 'FAIL', 'groups': rows}


if __name__ == '__main__':
    report = run_escape_regressions()
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report['status'] == 'PASS' else 1)
