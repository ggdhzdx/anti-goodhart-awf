"""Final deck acceptance is separate from successful structural assembly."""
import json
from pathlib import Path
MIN_HTML_PASS = 85.0


def verify_deck_evidence(design, deck_path, bundle_path, context):
    deck_path = Path(deck_path).resolve()
    expected = context.get('expected_artifacts', {})
    if not expected or any(Path(path).resolve() != deck_path for path in expected.values()):
        return {'status': 'FAIL', 'reason': 'Every reviewed screenshot must target this exact assembled deck'}
    bundle = json.loads(Path(bundle_path).read_text(encoding='utf-8'))
    threshold = bundle.get('dual_rubric_eval', {}).get('min_passing_score')
    if type(threshold) not in (int, float) or not threshold >= MIN_HTML_PASS:
        return {'status': 'FAIL', 'reason': 'HTML-PPT requires a reviewed threshold of at least 85/100'}
    # Static scanning is bound to actual deck bytes, not a caller-supplied HTML string.
    bundle['html_text'] = deck_path.read_text(encoding='utf-8')
    result = design.run_all_18_design_gates(bundle, evidence_context=context)
    return {'status': result['verdict_zone'], 'presentation_acceptance': result['verdict_zone'],
            'assurance_scope': 'design_gates_with_authorized_artifact_bound_review', 'design_receipt': result}
