"""Verify the real facade and HTML-PPT CLI cannot bypass D17/D18."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from release_hashes import write
ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'registry.yaml').is_file())
DESIGN = ROOT / 'components/skills/design-anti-goodhart/releases/1.0.0-rc.13/source'
HTML = ROOT / 'components/skills/html-ppt/releases/1.0.0-rc.15/source/scripts'
sys.path[:0] = [str(DESIGN / 'scripts'), str(DESIGN), str(HTML)]
import awf_design_anti_goodhart_gates as dag
from awf_design_ag_selftest_suite import _build_gold_standard_positive_bundle
from design_tests.evidence_fixtures import EvidenceFixture
from design_review_adapter import verify_deck_evidence


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def run():
    checks = []
    with tempfile.TemporaryDirectory() as directory:
        folder = Path(directory)
        original = _build_gold_standard_positive_bundle()
        fixture = EvidenceFixture(folder, html_text=original['html_text'])
        from design_contract import digest
        fixture.scores['min_passing_score'] = 85.0
        fixture.review['score_payload_sha256'] = digest(fixture.scores)
        fixture.write()
        bundle = fixture.attach(original)
        result = dag.run_all_18_design_gates(bundle, evidence_context=fixture.context)
        require(result['verdict_zone'] == 'PASS' and result['gates_passed_count'] == 18, 'full-engine positive')
        checks.append('full_engine_signed_positive')
        result = dag.run_all_18_design_gates(bundle)
        require(result['verdict_zone'] == 'FAIL' and len(result['gates_failed']) == 2, 'full-engine unsigned acceptance')
        checks.append('full_engine_missing_context_rejected')
        bad = copy.deepcopy(bundle)
        bad['dual_rubric_eval']['min_passing_score'] = 0
        result = dag.run_all_18_design_gates(bad, evidence_context=fixture.context)
        require(result['verdict_zone'] == 'FAIL', 'zero score threshold escaped the facade')
        checks.append('full_engine_zero_threshold_rejected')
        mismatched = copy.deepcopy(bundle)
        mismatched['html_text'] = '<html><body>another document</body></html>'
        require(dag.run_all_18_design_gates(mismatched, evidence_context=fixture.context)['verdict_zone'] == 'FAIL', 'different source HTML accepted')
        checks.append('full_engine_other_HTML_rejected')
        # JSON CLI fixtures use explicit crop metadata rather than an in-memory NumPy image.
        bundle['crop_specs'] = [{'id': 'fig1ab', 'subpanel_count': 2, 'blank_margin_ratio': 0.0, 'border_sliced_ink_ratio': 0.0}]
        bundle_path, targets_path = folder / 'bundle.json', folder / 'targets.json'
        write(bundle_path, bundle)
        write(targets_path, fixture.context['expected_artifacts'])
        result = verify_deck_evidence(dag, fixture.html, bundle_path, fixture.context)
        require(result['status'] == 'PASS', 'adapter positive')
        checks.append('html_adapter_positive')
        command = [sys.executable, '-B', str(HTML / 'audit_single_slide_step.py'), '--verify-deck-evidence', str(fixture.html),
                   '--review-bundle', str(bundle_path), '--evidence-manifest', fixture.context['manifest_path'],
                   '--trust-policy', fixture.context['trust_policy_path'], '--review-run-id', fixture.context['run_id'], '--review-targets', str(targets_path)]
        proc = subprocess.run(command, capture_output=True, text=True, check=False)
        require(proc.returncode == 0 and json.loads(proc.stdout)['presentation_acceptance'] == 'PASS', proc.stderr or proc.stdout)
        checks.append('html_CLI_signed_positive')
        fixture.html.write_text('<html><body>modified after review</body></html>', encoding='utf-8')
        proc = subprocess.run(command, capture_output=True, text=True, check=False)
        require(proc.returncode != 0 and json.loads(proc.stdout)['status'] == 'FAIL', 'CLI accepted changed deck')
        checks.append('html_CLI_changed_deck_rejected')
        # Even with high user scores and all other old gates satisfied, a stale screenshot cannot pass.
        fixture.html.write_text(bundle['html_text'], encoding='utf-8')
        fixture.png.write_bytes(fixture.png.read_bytes() + b'tamper')
        require(dag.run_all_18_design_gates(bundle, evidence_context=fixture.context)['verdict_zone'] == 'FAIL', 'full-engine changed screenshot accepted')
        checks.append('full_engine_changed_screenshot_rejected')
    print(json.dumps({'status': 'PASS', 'checks_passed': checks, 'scope': 'Real APIs/CLI with synthetic authorities'}, indent=2))


if __name__ == '__main__':
    run()
