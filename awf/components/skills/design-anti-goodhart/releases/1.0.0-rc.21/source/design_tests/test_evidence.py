"""Counterexamples for score fabrication, stale bytes and forged review evidence."""
import copy
import json
from pathlib import Path
import sys
import tempfile
from PIL import Image

SOURCE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SOURCE / 'scripts'))
sys.path.insert(0, str(SOURCE))
import awf_design_anti_goodhart_gates as dag
from design_contract import digest, file_digest, read_json
from design_tests.evidence_fixtures import EvidenceFixture, complete_scores, save_json


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def d17(fixture, scores=None, context=None):
    return dag.score_presentation_dual_rubric(fixture.scores if scores is None else scores, evidence_context=fixture.context if context is None else context)


def d18(fixture, score=100.0, paths=None, findings=None):
    return dag.evaluate_visual_red_blue_adversarial_audit(score, [str(fixture.png)] if paths is None else paths, [] if findings is None else findings,
                                                         evidence_context=fixture.context, score_payload=fixture.scores)


def score_cases(directory):
    fixture = EvidenceFixture(directory)
    require(d17(fixture)['passed'], 'positive D17 control')
    direct = dag.score_optoelectronic_rubric_v3(fixture.scores['optoelectronic_v3'])
    require(direct['A_scientific_explanation_46'] == 46 and direct['final_score'] == 100, 'canonical rubric totals')
    require(direct['a_item_breakdown']['A6_paired_baselines'] == 3 and direct['a_item_breakdown']['A6_tradeoffs'] == 2, 'A6 V2 must receive full credit')
    checks = []
    def reject(name, mutate):
        scores = copy.deepcopy(fixture.scores)
        mutate(scores)
        require(not d17(fixture, scores)['passed'], name)
        checks.append(name)
    reject('missing_dimension', lambda s: s['supermolecule_5dim'].pop('dim2_logic_score_20'))
    reject('empty_dimensions', lambda s: s.update(supermolecule_5dim={}))
    reject('zero_threshold', lambda s: s.update(min_passing_score=0))
    reject('negative_threshold', lambda s: s.update(min_passing_score=-1))
    reject('boolean_score', lambda s: s['supermolecule_5dim'].update(dim2_logic_score_20=True))
    reject('out_of_range_score', lambda s: s['supermolecule_5dim'].update(dim2_logic_score_20=100))
    reject('missing_redline_assessment', lambda s: s['optoelectronic_v3'].update(redlines={}))
    reject('negative_redline_count', lambda s: s['optoelectronic_v3']['redlines'].update(R2_broken_layout_pages=-1))
    reject('string_redline_boolean', lambda s: s['optoelectronic_v3']['redlines'].update(R1_latex_leak='false'))
    reject('inflated_weight', lambda s: s['optoelectronic_v3']['category_a_knowledge_items'][0].update(weight=10000))
    reject('duplicate_criterion', lambda s: s['optoelectronic_v3']['category_a_knowledge_items'].__setitem__(1, copy.deepcopy(s['optoelectronic_v3']['category_a_knowledge_items'][0])))
    reject('unknown_criterion', lambda s: s['optoelectronic_v3']['category_a_knowledge_items'][0].update(id='invented'))
    reject('lowered_visual_requirement', lambda s: s['optoelectronic_v3']['category_a_knowledge_items'][0].update(required_visual_level='V0'))
    reject('missing_grade', lambda s: s['optoelectronic_v3']['b_to_e_grades'].pop('B1'))
    reject('unknown_grade', lambda s: s['optoelectronic_v3']['b_to_e_grades'].update(B1='PERFECT'))
    for value in (float('nan'), float('inf'), -float('inf')):
        reject('nonfinite_' + str(value), lambda s: s['supermolecule_5dim'].update(dim2_logic_score_20=value))
    # Sign the invalid assessment too: schema/rubric rejection must not merely be a stale digest check.
    for name, modify in [('signed_zero_threshold', lambda s: s.update(min_passing_score=0)),
                         ('signed_inflated_weight', lambda s: s['optoelectronic_v3']['category_a_knowledge_items'][0].update(weight=10000)),
                         ('signed_redline_present', lambda s: s['optoelectronic_v3']['redlines'].update(R1_latex_leak=True))]:
        bad = EvidenceFixture(Path(directory) / name)
        modify(bad.scores)
        bad.review['score_payload_sha256'] = digest(bad.scores)
        bad.write()
        require(not d17(bad)['passed'], name)
        checks.append(name)
    require(dag.score_presentation_dual_rubric(fixture.scores)['status'] == 'REVIEW_REQUIRED', 'missing evidence should request review')
    checks.append('unsigned_complete_scores_require_review')
    return checks


def multi_frame_cases(directory):
    fixture = EvidenceFixture(directory, html_text='<html><body><div class="slide">one</div><div class="slide">two</div></body></html>')
    second_path = fixture.png.with_name('second.png')
    second_path.write_bytes(fixture.png.read_bytes())
    row = copy.deepcopy(fixture.render['artifacts'][0])
    row.update(artifact_id='slide-02', png_path=str(second_path), frame={'selector': '.slide', 'index': 1, 'state': 'initial'})
    fixture.render['artifacts'].append(row)
    fixture.context['expected_artifacts']['slide-02'] = str(fixture.html)
    fixture.review['reviewed_artifact_ids'].append('slide-02')
    fixture.review['criterion_evidence']['C3']['artifact_ids'].append('slide-02')
    fixture.write()
    paths = [str(fixture.png), str(second_path)]
    require(not d18(fixture, paths=paths)['passed'], 'copied screenshot accepted as second frame')
    Image.new('RGB', (1920, 1080), 'navy').save(second_path)
    row['png_sha256'] = file_digest(second_path)
    fixture.write()
    require(d18(fixture, paths=paths)['passed'], 'two complete distinct frames rejected')
    row['frame']['index'] = 0
    fixture.write()
    require(not d18(fixture, paths=paths)['passed'], 'same frame relabeled as another slide')
    return ['duplicate_png_across_frames', 'duplicate_frame_under_another_id']


def evidence_cases(directory):
    checks = []
    def reject(name, mutate, resign=False):
        fixture = EvidenceFixture(Path(directory) / name)
        mutate(fixture)
        if resign:
            fixture.write()
        require(not d18(fixture)['passed'], name)
        checks.append(name)
    fixture = EvidenceFixture(Path(directory) / 'positive')
    require(d18(fixture)['passed'], 'positive D18 control')
    require(not dag.evaluate_visual_red_blue_adversarial_audit(99, ['/not/a/screenshot.png'], [])['passed'], 'legacy fake path')
    checks.append('legacy_fake_path')
    reject('missing_png', lambda f: f.png.unlink())
    reject('changed_html', lambda f: f.html.write_text('changed', encoding='utf-8'))
    reject('changed_png', lambda f: f.png.write_bytes(f.png.read_bytes() + b'altered'))
    def replace_png(fixture, size, image_format='PNG'):
        Image.new('RGB', size, 'black').save(fixture.png, format=image_format)
        fixture.render['artifacts'][0]['png_sha256'] = file_digest(fixture.png)
    reject('signed_wrong_dimensions', lambda f: replace_png(f, (800, 600)), True)
    reject('signed_jpeg_named_png', lambda f: replace_png(f, (1920, 1080), 'JPEG'), True)
    def corrupt(fixture):
        fixture.png.write_bytes(b'not-a-png')
        fixture.render['artifacts'][0]['png_sha256'] = file_digest(fixture.png)
    reject('signed_corrupt_png', corrupt, True)
    reject('wrong_run', lambda f: f.context.update(run_id='another-run'))
    reject('missing_target_slide', lambda f: f.context['expected_artifacts'].update(extra=str(f.html)))
    reject('wrong_html_target', lambda f: f.context['expected_artifacts'].update({'slide-01': str(f.html.with_name('other.html'))}))
    reject('signed_duplicate_artifact', lambda f: f.render['artifacts'].append(copy.deepcopy(f.render['artifacts'][0])), True)
    reject('signed_missing_review_coverage', lambda f: f.review.update(reviewed_artifact_ids=[]), True)
    reject('signed_missing_criterion_observation', lambda f: f.review['criterion_evidence'].pop('B1'), True)
    reject('signed_unknown_criterion_artifact', lambda f: f.review['criterion_evidence']['B1'].update(artifact_ids=['other']), True)
    reject('signed_empty_observation', lambda f: f.review['criterion_evidence']['B1'].update(observation=''), True)
    reject('signed_critic_rejection', lambda f: f.review.update(verdict='FAIL'), True)
    reject('signed_unresolved_finding', lambda f: f.review.update(findings=[{'defect': 'clipped', 'verified_on_rendered_png': False}]), True)
    def same_key(fixture):
        fixture.reviewer_key = fixture.renderer_key
        fixture.policy['reviewers']['fixture-reviewer'] = fixture.policy['renderers']['fixture-renderer']
    reject('same_authority_key', same_key, True)
    def tamper_signature(fixture):
        package = read_json(fixture.context['manifest_path'])
        package['review']['payload']['run_id'] = 'tampered'
        save_json(fixture.context['manifest_path'], package)
    reject('unsigned_review_edit', tamper_signature)
    def unknown_authority(fixture):
        fixture.policy['reviewers'] = {}
        save_json(fixture.context['trust_policy_path'], fixture.policy)
    reject('unknown_reviewer_key', unknown_authority)
    reject('changed_score_after_review', lambda f: f.scores.update(min_passing_score=90))
    def signed_html(fixture, html, frame=None):
        fixture.html.write_text(html, encoding='utf-8')
        fixture.render['artifacts'][0]['html_sha256'] = file_digest(fixture.html)
        if frame is not None:
            fixture.render['artifacts'][0]['frame'] = frame
    reject('signed_external_resource_omitted', lambda f: signed_html(f, f.html.read_text().replace('</body>', '<img src="unlisted.png"></body>')), True)
    from design_capture_profile import CSP_META
    reject('signed_missing_offline_CSP', lambda f: signed_html(f, f.html.read_text().replace(CSP_META, '')), True)
    reject('signed_only_first_of_two_slides', lambda f: signed_html(f, f.html.read_text().replace('</body>', '<div class="slide">one</div><div class="slide">two</div></body>'), {'selector': '.slide', 'index': 0, 'state': 'initial'}), True)
    reject('signed_wrong_frame_state', lambda f: f.render['artifacts'][0].update(frame={'selector': 'html', 'index': 0, 'state': 'after-click'}), True)
    reject('signed_duplicate_CSP_attribute', lambda f: signed_html(f, f.html.read_text().replace('content="default-src', 'content="default-src *" content="default-src')), True)
    reject('signed_CSP_in_title', lambda f: signed_html(f, f.html.read_text().replace(CSP_META, '<title>' + CSP_META + '</title>')), True)
    reject('signed_CSP_in_body', lambda f: signed_html(f, f.html.read_text().replace(CSP_META, '').replace('<body>', '<body>' + CSP_META)), True)
    reject('signed_nonvoid_selfclosing_head_escape', lambda f: signed_html(f, f.html.read_text().replace('<head>', '<head><title/><!-- </title> -->')), True)
    reject('signed_duplicate_resource_attribute', lambda f: signed_html(f, f.html.read_text().replace('</body>', '<img src="https://example.invalid/a.png" src="data:image/png;base64,AA=="></body>')), True)
    reject('signed_script_adds_unreviewed_slide', lambda f: signed_html(f, f.html.read_text().replace('</body>', '<script>document.body.innerHTML += "<div class=slide>new</div>"</script></body>')), True)
    reject('signed_event_handler', lambda f: signed_html(f, f.html.read_text().replace('<body>', '<body onload="alert(1)">')), True)
    def changed_resource(fixture):
        asset = fixture.directory / 'asset.css'
        asset.write_text('body{color:black}', encoding='utf-8')
        fixture.render['artifacts'][0]['resources'] = [{'path': str(asset), 'sha256': file_digest(asset)}]
        fixture.write()
        asset.write_text('body{color:white}', encoding='utf-8')
    reject('changed_render_resource', changed_resource)
    for name, args in [('overclaimed_score', {'score': 101}), ('nan_claim', {'score': float('nan')}), ('wrong_path_list', {'paths': ['/absent.png']}), ('unresolved_caller_findings', {'findings': [{'verified_on_rendered_png': False}]})]:
        require(not d18(fixture, **args)['passed'], name)
        checks.append(name)
    return checks


def run():
    if len(sys.argv) > 1:
        def always_pass(*args, **kwargs):
            return {'passed': True, 'status': 'PASS'}
        if sys.argv[1] == 'mutant-d17':
            dag.score_presentation_dual_rubric = always_pass
        elif sys.argv[1] == 'mutant-d18':
            dag.evaluate_visual_red_blue_adversarial_audit = always_pass
        else:
            raise ValueError(sys.argv[1])
    with tempfile.TemporaryDirectory() as directory:
        scores = score_cases(Path(directory) / 'scores')
        evidence = evidence_cases(Path(directory) / 'evidence')
        evidence += multi_frame_cases(Path(directory) / 'multi-frame')
    print(json.dumps({'status': 'PASS', 'negative_cases': len(scores) + len(evidence), 'score_cases': scores, 'evidence_cases': evidence,
                      'positive_controls': ['complete_signed_scores', 'actual_png_bytes_with_distinct_test_authorities'],
                      'scope': 'Synthetic unit authorities; no production trust is provisioned'}, indent=2))


if __name__ == '__main__':
    run()
