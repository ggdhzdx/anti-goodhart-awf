"""Record actual predecessor false positives before implementing fixes."""
from pathlib import Path
import sys
from release_hashes import write
ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'registry.yaml').is_file())
sys.path.insert(0, str(ROOT / 'components/skills/design-anti-goodhart/releases/1.0.0-rc.12/source/scripts'))
import awf_design_anti_goodhart_gates as dag
rows = {
    'missing_five_dimensions': dag.score_supermolecule_5dim_rubric({}),
    'zero_threshold_empty_rubric': dag.score_presentation_dual_rubric({'min_passing_score': 0}),
    'fabricated_screenshot_path': dag.evaluate_visual_red_blue_adversarial_audit(99, ['/definitely/does-not-exist.png'], []),
    'inflated_weight': dag.score_optoelectronic_rubric_v3({'category_a_knowledge_items': [{'id': 'invented', 'weight': 10000, 'clarity': 'S', 'visual_level': 'V3', 'required_visual_level': 'V3'}]}),
}
write(ROOT / 'reports/designag-evidence-hardening-20261110/baseline.json', rows)
for name, result in rows.items():
    print(name, {key: result[key] for key in ('passed', 'final_score', 'blue_effective_reward') if key in result})
