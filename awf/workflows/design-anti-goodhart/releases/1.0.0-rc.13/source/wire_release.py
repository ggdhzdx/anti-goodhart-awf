"""Wire strict D17/D18 implementations into the facade and legacy self-tests."""
from pathlib import Path
ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'registry.yaml').is_file())
SCRIPTS = ROOT / 'components/skills/design-anti-goodhart/releases/1.0.0-rc.13/source/scripts'
path = SCRIPTS / 'awf_design_anti_goodhart_gates.py'
text = path.read_text(encoding='utf-8')
start = text.index('def score_optoelectronic_rubric_v3(')
end = text.index('def run_all_18_design_gates(', start)
text = text[:start] + 'from design_scores import score_optoelectronic_rubric_v3, score_supermolecule_5dim_rubric\nfrom design_acceptance import score_presentation_dual_rubric, evaluate_visual_red_blue_adversarial_audit\n\n\n' + text[end:]
text = text.replace('def run_all_18_design_gates(bundle: Dict[str, Any])', 'def run_all_18_design_gates(bundle: Dict[str, Any], *, evidence_context=None)')
text = text.replace('score_presentation_dual_rubric(bundle.get("dual_rubric_eval", {}))', 'score_presentation_dual_rubric(bundle.get("dual_rubric_eval", {}), evidence_context=evidence_context)')
text = text.replace('_num_or(bundle, "blue_claimed_score", LEGACY_BLUE_CLAIM_DEFAULT)', 'bundle.get("blue_claimed_score")')
text = text.replace('bundle.get("rendered_png_paths", ["slide_01.png"])', 'bundle.get("rendered_png_paths", [])')
text = text.replace('bundle.get("red_critic_findings", []),\n        ),', 'bundle.get("red_critic_findings"),\n            evidence_context=evidence_context, score_payload=bundle.get("dual_rubric_eval"),\n        ),')
text = text.replace('skill.design-anti-goodhart@1.0.0-rc.12', 'skill.design-anti-goodhart@1.0.0-rc.13')
path.write_text(text, encoding='utf-8')
text = text.replace('res_d18_neg["blue_effective_reward"] != float("-inf")', 'res_d18_neg["status"] != "FAIL" or res_d18_neg["blue_effective_reward"] != 0.0')
path.write_text(text, encoding='utf-8')
path = SCRIPTS / 'awf_design_ag_selftest_suite.py'
text = path.read_text(encoding='utf-8')
start = text.index('    # D17 Exact Calibration Check')
end = text.index('    # D18 Negative:', start)
text = text[:start] + '''    from pathlib import Path
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from design_tests.evidence_fixtures import complete_scores
    payload = complete_scores()["optoelectronic_v3"]
    payload["category_a_knowledge_items"][1]["clarity"] = "B"
    payload["category_a_knowledge_items"][1]["visual_level"] = "V0"
    payload["redlines"]["R1_latex_leak"] = True
    payload["redlines"]["R2_broken_layout_pages"] = 6
    cal_res = dag.score_optoelectronic_rubric_v3(payload)
    if abs(cal_res["a_item_breakdown"]["A2_all"] - EXPECTED_TEXT_MODALITY_SCORE / 2) > 1e-6:
        raise AssertionError("D17 partial clarity times text-modality calibration failed")
    if cal_res["redline_deduction_capped_15"] != -EXPECTED_REDLINE_DEDUCTION_CAP:
        raise AssertionError("D17 redline deduction cap failed")

''' + text[end:]
text = text.replace('    receipt = dag.run_all_18_design_gates(pos_bundle)', '''    import tempfile
    from pathlib import Path
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from design_tests.evidence_fixtures import EvidenceFixture
    with tempfile.TemporaryDirectory() as directory:
        fixture = EvidenceFixture(directory, html_text=pos_bundle["html_text"])
        receipt = dag.run_all_18_design_gates(fixture.attach(pos_bundle), evidence_context=fixture.context)''')
path.write_text(text, encoding='utf-8')
