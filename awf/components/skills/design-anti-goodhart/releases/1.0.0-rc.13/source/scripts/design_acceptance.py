"""D17/D18 acceptance binds fixed rubric arithmetic to actual authorized evidence."""
from pathlib import Path
from cryptography.exceptions import InvalidSignature
from design_contract import number, require
from design_evidence import ReviewRequired, verify_review
from design_scores import calculate_scores
from design_capture_profile import UnsupportedCaptureProfile

ERRORS = (ValueError, KeyError, TypeError, OSError, InvalidSignature)


def _failure(gate, error):
    return {'gate': gate, 'passed': False, 'status': 'REVIEW_REQUIRED' if isinstance(error, (ReviewRequired, UnsupportedCaptureProfile)) else 'FAIL', 'reason': str(error) or type(error).__name__}


def score_presentation_dual_rubric(eval_payload, *, evidence_context=None):
    gate = 'D17_DualRubric_Quantitative_Scorer'
    try:
        scores = calculate_scores(eval_payload)
        evidence = verify_review(evidence_context, eval_payload)
        passed = scores['scores_passed']
        return {'gate': gate, 'passed': passed, 'status': 'PASS' if passed else 'FAIL', **scores, 'evidence': evidence}
    except ERRORS as error:
        return _failure(gate, error)


def evaluate_visual_red_blue_adversarial_audit(blue_claimed_score, rendered_png_paths, red_critic_findings, *, evidence_context=None, score_payload=None):
    gate = 'D18_RedBlue_Visual_Adversarial_Critic_Protocol'
    try:
        claimed = number(blue_claimed_score)
        scores = calculate_scores(score_payload)
        evidence = verify_review(evidence_context, score_payload)
        require(isinstance(rendered_png_paths, (list, tuple)) and bool(rendered_png_paths), 'Explicit rendered screenshot paths required')
        actual = [str(Path(p).resolve()) for p in rendered_png_paths]
        require(len(actual) == len(set(actual)) and set(actual) == set(evidence['png_paths']), 'Screenshot list does not match the signed review')
        require(isinstance(red_critic_findings, list) and not red_critic_findings, 'Unresolved or unassessed critic findings')
        confirmed = min(scores['optoelectronic_v3_result']['final_score'], scores['supermolecule_5dim_result']['final_score'])
        require(claimed <= confirmed, 'Claimed score exceeds the reviewed calculation')
        require(scores['scores_passed'], 'Reviewed rubric does not meet the acceptance threshold or has redlines')
        return {'gate': gate, 'passed': True, 'status': 'PASS', 'rendered_png_count': len(actual), 'confirmed_defect_count': 0,
                'blue_effective_reward': confirmed, 'red_auditor_bounty': 0.0, 'evidence': evidence}
    except ERRORS as error:
        return {**_failure(gate, error), 'blue_effective_reward': 0.0, 'red_auditor_bounty': 0.0}
