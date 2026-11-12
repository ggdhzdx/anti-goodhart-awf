"""Counterexamples for the rc.3 contract changes; no optimization-dependent asserts."""
import json
from pathlib import Path
import numpy as np
import awf_universal_anti_goodhart_gates as gate
from awf_guard_selftests.geometry_fixtures import sphere_clearance_exact, sphere_clearance_specs

def require(condition, label):
    if not condition:
        raise AssertionError(label)

def rejects(function, *args, **kwargs):
    try:
        value = function(*args, **kwargs)
    except (ValueError, gate.AntiGoodhartGateError) as error:
        value = {'status': 'FAIL', 'error': str(error)}
    return isinstance(value, dict) and (value.get('status') == 'FAIL' or bool(value.get('violations')))

def ignores_radius(points, centers, radii, c_min):
    distances = np.min(np.linalg.norm(points[:, None] - centers[None, :], axis=2), axis=1)
    void = 100 * np.mean(distances > c_min)
    return np.array([100 - void, void, void, void])

def test_radius_contract():
    data = sphere_clearance_specs()
    function = gate.verify_filtration_monotonicity_and_heterogeneous_radius_clearance
    require(function(sphere_clearance_exact, data['base'], data['probe'])['status'] == 'PASS', 'real radius operator')
    misleading = {**data['probe'], 'c_min': 100}
    require(rejects(function, ignores_radius, data['base'], misleading), 'radius-blind distinct probe')
    scaled_blind = lambda **kwargs: ignores_radius(**kwargs) * 1e-12
    require(rejects(function, scaled_blind, data['base'], misleading, partition_total=1e-10, tol=0.001), 'radius tolerance exceeds normalization scale')
    scaled_exact = lambda **kwargs: sphere_clearance_exact(**kwargs) * 1e-12
    require(function(scaled_exact, data['base'], data['probe'], partition_total=1e-10, tol=1e-15)['status'] == 'PASS', 'small normalized exact operator')
    require(rejects(function, ignores_radius, {'x': 1}, {'x': 2}), 'unknown geometry contract')
    for bad in (np.nan, np.inf, -np.inf):
        require(rejects(function, sphere_clearance_exact, data['base'], data['probe'], tol=bad), 'nonfinite G5r tolerance')
    return 8

def test_small_branches_and_magic():
    old = 'def f(x):\n    if x < 0:\n        return -x\n    return x\n'
    new = 'def f(x):\n    return x\n'
    require(bool(gate.audit_ast_pair_diff(old, new)['violations']), 'small branch deletion')
    require(not gate.audit_ast_pair_diff(old, old)['violations'], 'unchanged function')
    require(bool(gate.audit_ast_pair_diff(old, '')['violations']), 'removed small function')
    source = 'def f(x):\n    return x * 1.23456789\n'
    require(rejects(gate.scan_source_for_todo_placeholders_and_magic_numbers, source), 'default magic scan')
    result = gate.scan_source_for_todo_placeholders_and_magic_numbers(source, check_magic_numbers=False)
    require(result['status'] == 'PASS', 'explicit legacy magic opt-out')
    return 5

def test_nonfinite_extraction():
    for bad in (np.nan, np.inf, -np.inf):
        require(rejects(gate._extract_array, np.array([1, bad])), 'nonfinite operator array')
        require(rejects(gate._extract_array, {'result': [1], 'hidden': bad}), 'nonfinite hidden field')
        require(rejects(gate._finite_float, bad), 'nonfinite scalar')
    return 9

def scanner_diagnostics():
    output = {}
    for path in Path(__file__).parent.rglob('*.py'):
        from awf_guard.fixture_policy import reviewed_fixture_numbers
        result = gate.scan_source_for_todo_placeholders_and_magic_numbers(path.read_text(), allowed_numeric_literals=reviewed_fixture_numbers(path, Path(__file__).parent))
        if result['findings']:
            output[path.name] = result['findings']
        benchmark = gate.audit_benchmark_hackability({path.name: path.read_text()})
        if benchmark['finding_count']:
            output[path.name + ':benchmark'] = benchmark
    return output

def run_contract_checks():
    counts = {'radius': test_radius_contract(), 'small_and_magic': test_small_branches_and_magic(), 'nonfinite': test_nonfinite_extraction()}
    return {'status': 'PASS', 'checks': counts, 'total': sum(counts.values())}
if __name__ == '__main__':
    print(json.dumps({'regressions': run_contract_checks(), 'scanner': scanner_diagnostics()}, indent=2))
