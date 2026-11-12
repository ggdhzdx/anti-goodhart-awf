"""Validate runtime, adversarial cases, targeted mutations and real browser evidence."""
import datetime
import subprocess
import sys
from release_hashes import file_hash, read, write
from stack_release_config import ROOT, REPORT, SOURCES, GUARD, VERIFIER, ENGINEERING, fingerprints


def validate():
    before = fingerprints()
    design = SOURCES['design-anti-goodhart']
    html = SOURCES['html-ppt']
    engine = design / 'scripts/awf_design_anti_goodhart_gates.py'
    cases = design / 'design_tests/test_evidence.py'
    commands = {
        'guard-selftest': [GUARD / 'scripts/awf_universal_anti_goodhart_gates.py', '--self-test'],
        'design-audit': [engine, '--audit-self'], 'design-selftest': [engine, '--self-test'],
        'evidence': [cases], 'mutant-d17': [cases, 'mutant-d17'], 'mutant-d18': [cases, 'mutant-d18'],
        'public-route': [ENGINEERING / 'test_public_route.py'],
        'html-selftest': [html / 'scripts/audit_single_slide_step.py', '--self-test'],
        'concrete-title': [html / 'tests/test_concrete_title_language.py'],
        'concrete-semantics': [html / 'tests/test_concrete_system_semantics.py'],
    }
    steps, checks = {}, {}
    for name, arguments in commands.items():
        stdout, stderr = REPORT / f'final-{name}.stdout.txt', REPORT / f'final-{name}.stderr.txt'
        with stdout.open('w') as out, stderr.open('w') as err:
            proc = subprocess.run([sys.executable, '-B', *map(str, arguments)], cwd=ROOT, stdout=out, stderr=err, timeout=600, check=False)
        steps[name] = {'returncode': proc.returncode, 'command': [str(arg) for arg in arguments],
                       'stdout': str(stdout.relative_to(ROOT)), 'stdout_sha256': file_hash(stdout),
                       'stderr': str(stderr.relative_to(ROOT)), 'stderr_sha256': file_hash(stderr)}
        if name.startswith('mutant-'):
            error = stderr.read_text()
            checks[name] = proc.returncode != 0 and 'AssertionError' in error and 'Traceback' in error and 'TypeError' not in error
        else:
            checks[name] = proc.returncode == 0
        print(f'{name}: rc={proc.returncode}, expected_result={checks[name]}', flush=True)
    sys.path.insert(0, str(VERIFIER))
    from guard_receipt_contract import validate_guard_receipt
    def receipt(name):
        return read(ROOT / steps[name]['stdout']) if steps[name]['returncode'] == 0 else {}
    checks['independent_guard_receipt'] = not validate_guard_receipt(receipt('guard-selftest'))
    audit = receipt('design-audit')
    checks['strict_G6n'] = audit.get('status') == 'PASS' and audit.get('declared_waivers') == [] and audit.get('magic_number_exempt_test_role_files') == [] and len(audit.get('files_audited', [])) == 10
    checks['18_design_gates'] = receipt('design-selftest').get('gates_passed_count') == 18
    checks['adversarial_coverage'] = receipt('evidence').get('negative_cases', 0) >= 60
    checks['public_route_coverage'] = len(receipt('public-route').get('checks_passed', [])) == 8
    checks['12_html_scenarios'] = len(receipt('html-selftest').get('checks_passed', [])) == 12
    browser = read(REPORT / 'browser-smoke/receipt.json')
    checks['actual_browser_capture'] = browser['status'] == 'PASS' and browser['actual_browser_capture'] is True and browser['production_review'] is False
    checks['browser_source_freshness'] = all(file_hash(ROOT / path) == digest for path, digest in browser['source_hashes'].items())
    evidence = browser['acceptance_under_test_authorities']['evidence']['artifacts']['slide-01']
    checks['browser_html_bytes'] = file_hash(REPORT / 'browser-smoke/slide.html') == evidence['html_sha256']
    checks['browser_png_bytes'] = file_hash(REPORT / 'browser-smoke/slide.png') == evidence['png_sha256']
    checks['sources_unchanged'] = before == fingerprints()
    result = {'passed': all(checks.values()), 'checks': checks, 'sources': before, 'steps': steps,
              'observed_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'execution': 'node01 Linux / zc; actual Chrome capture on Windows with ephemeral test authorities',
              'browser_receipt_sha256': file_hash(REPORT / 'browser-smoke/receipt.json')}
    write(REPORT / 'validation.json', result)
    print({'passed': result['passed'], 'failed': [name for name, ok in checks.items() if not ok]}, flush=True)
    return result['passed']
