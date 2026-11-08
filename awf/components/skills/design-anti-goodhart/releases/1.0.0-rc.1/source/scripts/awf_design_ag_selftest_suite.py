#!/usr/bin/env python3
"""
Co-located Positive & Negative Self-Test Suite for AWF DesignAG
(`skill.design-anti-goodhart@1.0.0-rc.1`).

Verifies all 18 Design Anti-Goodhart Gates (D1-D18) and the Dual-Rubric Scorer
against real-world failure cases from `01_optoelectronic_scoring_criteria_v3.md`
and `02_supermolecule_SCORING_CRITERIA_5dim.md`.
"""

from __future__ import annotations

from typing import Any, Dict, List

import numpy as np

import awf_design_anti_goodhart_gates as dag


def _verify_pillar1_static_and_copywriting_gates() -> None:
    # D1 Negative: gemini-3.8flash raw LaTeX source leak without MathJax/KaTeX
    bad_html_d1 = "<div class='slide'><p>PF = \\frac{k_r \\text{ (微腔)}}{k_{r,0}}, $S_0$ to $\\tau$</p></div>"
    res_d1_neg = dag.scan_html_for_unrendered_latex_leak(bad_html_d1)
    if res_d1_neg["passed"] or not res_d1_neg["redline_r1_triggered"]:
        raise AssertionError("D1 failed to catch unrendered raw LaTeX source leak")

    # D1 Positive: clean native HTML sub/sup + Unicode math
    good_html_d1 = "<div class='slide'><p>PF = k<sub>r</sub> / k<sub>r,0</sub>, τ<sub>0</sub> ≈ 1.5 μs</p></div>"
    res_d1_pos = dag.scan_html_for_unrendered_latex_leak(good_html_d1)
    if not res_d1_pos["passed"]:
        raise AssertionError(f"D1 false positive on clean HTML: {res_d1_pos}")

    # D2 Negative: kimi-k3 slide 5 `<div class="big-num">因</p></div>` + doubao 3+1 orphan grid
    bad_html_d2 = "<div class='grid g3'><div class='card'><div class='big-num'>因</p></div></div>"
    res_d2_neg = dag.audit_html_tag_balance_and_grid_orphans(
        bad_html_d2, [{"slide": 5, "columns": 3, "item_count": 4}]
    )
    if res_d2_neg["passed"] or len(res_d2_neg["tag_mismatches"]) == 0 or len(res_d2_neg["orphan_grids"]) == 0:
        raise AssertionError("D2 failed to catch mismatched closing tag or 3+1 orphan grid")

    # D3 Negative: deepseek corner quotes + sol-6.1 AI meta-tone + astra-6 subjectless title + prompt residue
    bad_slides_d3 = [
        {
            "title": "五个问题，看懂这篇工作",
            "subtitle": "先说比较对象，再说提升倍数",
            "body": "把 SPP 和激子「焊」在一起，「快速抽走」三线态，防止把分子「烧坏」或「打架」。本汇报复述原论文结果。",
        },
        {
            "title": "140 小时与 10–14 倍，来自归一化比较",
            "subtitle": "13页实验原理",
            "body": "属于作者发表时的结果。",
        },
    ]
    res_d3_neg = dag.audit_copywriting_naturalness_and_ai_tone(bad_slides_d3)
    if (
        res_d3_neg["passed"]
        or not res_d3_neg["excessive_corner_quotes"]
        or not res_d3_neg["cliche_hits"]
        or not res_d3_neg["meta_tone_hits"]
        or not res_d3_neg["prompt_residue_hits"]
        or not res_d3_neg["subjectless_titles"]
    ):
        raise AssertionError(f"D3 failed to catch AI copywriting anti-patterns: {res_d3_neg}")

    # D4 Negative: TPA/TTA hidden in notes on slide 1, used bare on slide 2 + glossary wall on slide 3
    bad_slides_d4 = [
        {
            "visible_text": "蓝光为什么容易老化：三重态发生相互作用",
            "notes_text": "TPA（三重态-极化子湮灭）与 TTA（三重态-三重态湮灭）",
            "defined_terms_notes": ["TPA", "TTA"],
        },
        {
            "visible_text": "TTA 缺陷生成率与 TPA 缺陷生成率随 LT90 变化",
            "notes_text": "",
        },
        {
            "visible_text": "关键术语速查字典墙",
            "is_glossary_wall": True,
        },
    ]
    res_d4_neg = dag.audit_acronym_definitions_and_popovers(bad_slides_d4, ("TPA", "TTA", "LT90"))
    if res_d4_neg["passed"] or not res_d4_neg["missing_visible_defs"] or not res_d4_neg["glossary_wall_slides"]:
        raise AssertionError(f"D4 failed to catch hidden acronym definitions or glossary wall: {res_d4_neg}")

    # D5 Negative: doubao cartoon Emojis + deepseek fake progress bars + AI decorative mechanism fake
    bad_html_d5 = "<div>🐢 三重态堆积 🪞 Ag阴极 🗂️ DBR 100% 最强 78% 强 豆包AI生成</div>"
    res_d5_neg = dag.audit_emojis_fake_bars_and_watermarks(
        bad_html_d5,
        [{"src": "plasmon_wave_4x3.png", "is_ai_decorative_wallpaper": True, "claimed_as_mechanism_diagram": True}],
    )
    if res_d5_neg["passed"] or res_d5_neg["redline_r4_count"] != 1:
        raise AssertionError(f"D5 failed to catch cartoon Emojis, fake progress bars, or AI deco fake: {res_d5_neg}")

    # D6 Negative: gemini-4 visible teleprompter + gemini-3.8flash scrollbar + glm-5.3 filler slides
    res_d6_neg = dag.audit_teleprompter_and_slide_density({
        "teleprompter_default_visible": True,
        "slides_with_vertical_scrollbar": 3,
        "min_body_font_px": 12.5,
        "total_slides": 12,
        "filler_transition_slides": 5,
        "is_full_paper_deck": True,
    })
    if res_d6_neg["passed"] or not res_d6_neg["redline_r6_triggered"]:
        raise AssertionError(f"D6 failed to catch teleprompter/density violations: {res_d6_neg}")


def _verify_pillar2_geometric_optical_and_cropping_gates() -> None:
    # D7 Negative: sibling card overlap + bottom canvas overflow clipping (kimi-k3 slide 13)
    bad_boxes_d7 = [
        {"id": "card1", "parent_id": "colR", "x": 1000, "y": 150, "w": 800, "h": 350},
        {"id": "card2", "parent_id": "colR", "x": 1000, "y": 450, "w": 800, "h": 350},
        {"id": "card3", "parent_id": "colR", "x": 1000, "y": 780, "w": 800, "h": 360, "scroll_h": 410, "client_h": 360},
    ]
    res_d7_neg = dag.verify_bounding_boxes_zero_overlap_and_clipping(bad_boxes_d7)
    if res_d7_neg["passed"] or not res_d7_neg["overlaps"] or not res_d7_neg["clipped_elements"]:
        raise AssertionError(f"D7 failed to catch sibling overlap or bottom clipping: {res_d7_neg}")

    # D8 Negative: grok-4.7 top-heavy layout (all boxes cramped in top 18% of canvas)
    bad_boxes_d8 = [
        {"id": "top_strip", "x": 100, "y": 40, "w": 1700, "h": 160},
    ]
    res_d8_neg = dag.verify_canvas_whitespace_and_center_of_mass(bad_boxes_d8)
    if res_d8_neg["passed"] or res_d8_neg["center_of_mass_ok"]:
        raise AssertionError(f"D8 failed to catch top-heavy center-of-mass imbalance: {res_d8_neg}")

    # D9 Negative: qwen-3.8 wide banner (2.55:1) stuffed into narrow vertical column (920x936)
    res_d9_neg = dag.verify_image_aspect_ratio_and_slot_utilization([
        {"id": "fig1_banner", "img_w": 2550, "img_h": 1000, "slot_w": 920, "slot_h": 936, "panel_rows": 1},
        {"id": "fig2_multirow", "img_w": 1600, "img_h": 1200, "slot_w": 1600, "slot_h": 420, "panel_rows": 3},
    ])
    if res_d9_neg["passed"] or len(res_d9_neg["violations"]) < 2:
        raise AssertionError(f"D9 failed to catch aspect-ratio mismatch or crushed multi-row figure: {res_d9_neg}")

    # D10 Negative: hy-4 12-panel composite dump + qwen-3.8 blind PDF crop with 28% left margin & sliced border text
    synth_crop = np.full((200, 300), 255.0, dtype=np.float64)
    synth_crop[10:190, 90:290] = 200.0  # 30% blank left margin (cols 0..89)
    synth_crop[0, 100:180] = 10.0  # dark sliced title text right on top cut boundary
    res_d10_neg = dag.verify_subpanel_crop_purity([
        {"id": "fig2_unsplit", "subpanel_count": 12},
        {"id": "fig5ab_blind_crop", "subpanel_count": 2, "image_array": synth_crop, "has_neighbor_bleed": True},
    ])
    if res_d10_neg["passed"] or len(res_d10_neg["violations"]) < 3:
        raise AssertionError(f"D10 failed to catch unsplit figure or blind PDF crop defects: {res_d10_neg}")

    # D11 Negative: qwen-3.8 slide 8 discussing 1b while only cropping 1a + deepseek slide 18 1D chart
    res_d11_neg = dag.verify_figure_text_explicit_coupling(
        [
            {
                "cropped_subpanels": ["1a"],
                "discussed_subpanels": ["1a", "1b"],
                "visible_text": "SPP与ETL激子强耦合形成PEP",
                "chart_audit": {"has_x_axis": True, "has_y_axis": False, "coordinates_misplaced": True},
            }
        ],
        total_paper_figures_cited=0,
    )
    if res_d11_neg["passed"] or res_d11_neg["redline_r3_count"] < 2:
        raise AssertionError(f"D11 failed to catch subpanel mismatch or R3 broken chart: {res_d11_neg}")

    # D12 Negative: low contrast light-gray text on white + cyberpunk neon glow
    res_d12_neg = dag.verify_wcag_contrast_and_visual_restraint(
        [{"id": "low_contrast_body", "fg_rgb": (190, 195, 200), "bg_rgb": (255, 255, 255), "is_large_title": False}],
        has_cyberpunk_neon_glow=True,
        pptx_font_slots_uniform=False,
    )
    if res_d12_neg["passed"]:
        raise AssertionError("D12 failed to catch low WCAG contrast or cyberpunk neon glow")


def _verify_pillar3_and_pillar4_pedagogical_and_scoring_gates() -> None:
    # D13 Negative: missing PHOLED macro background + clue-free blind guessing
    res_d13_neg = dag.verify_narrative_arc_and_foreshadowing({
        "has_macro_background_and_core_def": False,
        "has_degradation_or_bottleneck_mechanism": True,
        "has_prior_art_and_ceiling": False,
        "has_clue_free_blind_guessing": True,
    })
    if res_d13_neg["passed"] or len(res_d13_neg["issues"]) < 3:
        raise AssertionError(f"D13 failed to catch narrative arc defects: {res_d13_neg}")

    # D14 Negative: unexplained anticrossing Why + 6-oxygen crown ether factual error (R7)
    res_d14_neg = dag.verify_causal_why_chain_and_tradeoffs({
        "causal_why_links_explained": {
            "why_etl_spp_resonate": False,
            "why_anticrossing_not_crossing": False,
            "why_flat_dispersion_accelerates_eml": True,
        },
        "has_real_molecular_chemical_structures": False,
        "scientific_or_structural_errors": ["18-crown-6 drawn as 6 oxygen atoms without 12 carbons"],
    })
    if res_d14_neg["passed"] or res_d14_neg["redline_r7_count"] != 1:
        raise AssertionError(f"D14 failed to catch unexplained causal Why chain or R7 error: {res_d14_neg}")

    # D15 Negative: gemini-3.8flash unmounted `@keyframes collide` + reversed SHG physics
    bad_anim_html = "<style>@keyframes collide { 0% { opacity: 1; } 100% { opacity: 0; } }</style><div>Static</div>"
    res_d15_neg = dag.verify_interactive_physics_and_animations(
        bad_anim_html,
        {
            "has_coupled_physics_formula_widget": False,
            "has_reversed_or_broken_physics_animation": True,
            "has_interactive_quiz_with_explanation": False,
        },
    )
    if res_d15_neg["passed"] or "collide" not in res_d15_neg["unmounted_keyframes"]:
        raise AssertionError(f"D15 failed to catch unmounted @keyframes collide: {res_d15_neg}")

    # D16 Negative: one-shot 15 slides per step + 4 consecutive identical 3-card layouts
    res_d16_neg = dag.verify_storyboard_microstep_and_layout_diversity(
        [{"layout_archetype": "three_column_cards"} for _ in range(6)],
        max_slides_generated_per_step=15,
    )
    if res_d16_neg["passed"]:
        raise AssertionError("D16 failed to catch one-shot batching and monotonous layout cloning")

    # D17 Exact Calibration Check against Section II of `01_optoelectronic_scoring_criteria_v3.md`:
    # "为什么是反交叉" (weight = 4, required = V3):
    # - opus-5.5: clarity B (0.5), visual V3 (1.0) -> 4 * 0.5 * 1.0 = 2.0
    # - gemini-3.8flash: clarity B (0.5), visual V2 (0.8) -> 4 * 0.5 * 0.8 = 1.6
    # - pure text S (1.0), V0 (0.3) -> 4 * 1.0 * 0.3 = 1.2
    cal_res = dag.score_optoelectronic_rubric_v3({
        "category_a_knowledge_items": [
            {"id": "opus_anticross", "weight": 4.0, "clarity": "B", "visual_level": "V3", "required_visual_level": "V3"},
            {"id": "g38_anticross", "weight": 4.0, "clarity": "B", "visual_level": "V2", "required_visual_level": "V3"},
            {"id": "v0_pure_text", "weight": 4.0, "clarity": "S", "visual_level": "V0", "required_visual_level": "V3"},
        ],
        "b_to_e_grades": {},
        "redlines": {"R1_latex_leak": True, "R2_broken_layout_pages": 6},
    })
    bd = cal_res["a_item_breakdown"]
    if abs(bd["opus_anticross"] - 2.0) > 1e-6 or abs(bd["g38_anticross"] - 1.6) > 1e-6 or abs(bd["v0_pure_text"] - 1.2) > 1e-6:
        raise AssertionError(f"D17 multiplicative formula mismatch vs rubric spec: {bd}")
    if abs(cal_res["redline_deduction_capped_15"] - (-15.0)) > 1e-6:
        raise AssertionError(f"D17 redline cap -15 failed: {cal_res}")

    # D18 Negative: Red Critic confirms visual clipping & R1 redline on rendered PNG
    res_d18_neg = dag.evaluate_visual_red_blue_adversarial_audit(
        95.0,
        ["slide_05.png"],
        [{"slide": 5, "defect": "Card 3 bottom clipped", "verified_on_rendered_png": True, "is_redline": True}],
    )
    if res_d18_neg["passed"] or res_d18_neg["blue_effective_reward"] != float("-inf"):
        raise AssertionError(f"D18 failed to zero/neg-inf Blue reward on confirmed Redline: {res_d18_neg}")


def _build_gold_standard_positive_bundle() -> Dict[str, Any]:
    good_html = (
        "<!DOCTYPE html><html><head><script src='katex.min.js'></script>"
        "<style>@keyframes pulse_wave { 0% { opacity: 0.4; } 100% { opacity: 1.0; } }"
        ".wave { animation: pulse_wave 2s infinite; }</style></head>"
        "<body><div class='slide'><h2>PF 最大的器件，并不是 EQE 最高的器件</h2>"
        "<p class='wave'>在上排第一列 Ag/BPyTP2 色散图中，下支 LP 落入 400–500 nm 蓝光发射带。</p>"
        "</div></body></html>"
    )
    slides = [
        {
            "title": "电激发下 75% 三重态自旋统计决定了显示产业必须发展磷光 PHOLED",
            "subtitle": "重原子旋轨耦合实现 100% 内量子效率，但高能蓝光三重态受困于微秒级长寿命",
            "body": "先看左图 1a 的自旋统计比例，再看右图 1b 的能级寿命对比。",
            "visible_text": (
                "PHOLED（磷光有机发光二极管）与 TPA（三重态-极化子湮灭）、TTA（三重态-三重态湮灭）、"
                "LT90（亮度衰减至初始亮度 90% 的工作寿命，防 10% 烧屏残影）、PF（Purcell 因子）、"
                "ODoS（光学态密度）、SPP（表面等离激元）、PEP（等离激元-激子极化激元）。"
                "左图 1a 展示传统器件，右图 1b 展示极化激元增强器件。"
            ),
            "notes_text": "",
            "defined_terms_visible": ["PHOLED", "TPA", "TTA", "LT90", "PF", "ODoS", "SPP", "PEP"],
            "inline_popover_count": 8,
            "cropped_subpanels": ["1a", "1b"],
            "discussed_subpanels": ["1a", "1b"],
            "chart_audit": {"has_x_axis": True, "has_y_axis": True, "coordinates_misplaced": False},
        }
    ]
    boxes = [
        {"id": "header", "parent_id": "root", "x": 80, "y": 50, "w": 1760, "h": 110},
        {"id": "left_panel", "parent_id": "root", "x": 80, "y": 200, "w": 850, "h": 760},
        {"id": "right_panel", "parent_id": "root", "x": 990, "y": 200, "w": 850, "h": 760},
    ]
    clean_crop = np.full((240, 320), 255.0, dtype=np.float64)
    clean_crop[15:225, 18:302] = 180.0

    a_items: List[Dict[str, Any]] = [
        {"id": "A1_all", "weight": 8.0, "clarity": "S", "visual_level": "V3", "required_visual_level": "V3"},
        {"id": "A2_all", "weight": 4.0, "clarity": "S", "visual_level": "V2", "required_visual_level": "V2"},
        {"id": "A3_all", "weight": 14.0, "clarity": "S", "visual_level": "V3", "required_visual_level": "V3"},
        {"id": "A4_all", "weight": 7.0, "clarity": "S", "visual_level": "V3", "required_visual_level": "V3"},
        {"id": "A5_all", "weight": 8.0, "clarity": "S", "visual_level": "V2", "required_visual_level": "V2"},
        {"id": "A6_all", "weight": 5.0, "clarity": "S", "visual_level": "V2", "required_visual_level": "V2"},
    ]
    storyboard = [
        {"layout_archetype": "top_banner_bottom_dual_cards"},
        {"layout_archetype": "split_left_fig_right_guided_steps"},
        {"layout_archetype": "interactive_svg_sandbox_split"},
        {"layout_archetype": "three_column_device_stack_comparison"},
        {"layout_archetype": "paired_bar_chart_and_tradeoff_matrix"},
        {"layout_archetype": "interactive_quiz_and_takeaway"},
    ]
    return {
        "html_text": good_html,
        "grid_specs": [{"slide": 1, "columns": 3, "item_count": 3}],
        "slides": slides,
        "figure_metadata": [{"src": "fig1ab.png", "is_ai_decorative_wallpaper": False}],
        "deck_spec": {
            "teleprompter_default_visible": False,
            "slides_with_vertical_scrollbar": 0,
            "min_body_font_px": 20.0,
            "total_slides": 22,
            "filler_transition_slides": 2,
            "is_full_paper_deck": True,
        },
        "boxes": boxes,
        "placements": [
            {"id": "fig1ab_wide", "img_w": 2000, "img_h": 900, "slot_w": 1760, "slot_h": 720, "panel_rows": 1},
            {"id": "fig2ab_grid", "img_w": 1200, "img_h": 900, "slot_w": 850, "slot_h": 640, "panel_rows": 2},
        ],
        "crop_specs": [{"id": "fig1ab", "subpanel_count": 2, "image_array": clean_crop}],
        "total_paper_figures_cited": 12,
        "color_pairs": [{"id": "body", "fg_rgb": (20, 28, 45), "bg_rgb": (248, 250, 252), "is_large_title": False}],
        "has_cyberpunk_neon_glow": False,
        "pptx_font_slots_uniform": True,
        "narrative_spec": {
            "has_macro_background_and_core_def": True,
            "has_degradation_or_bottleneck_mechanism": True,
            "has_prior_art_and_ceiling": True,
            "has_clue_free_blind_guessing": False,
            "has_foreshadowing_and_callback": True,
        },
        "mechanism_spec": {
            "causal_why_links_explained": {
                "why_etl_spp_resonate": True,
                "why_anticrossing_not_crossing": True,
                "why_flat_dispersion_accelerates_eml": True,
            },
            "has_dedicated_device_or_assembly_slide": True,
            "has_real_molecular_chemical_structures": True,
            "has_controlled_pair_comparison_and_baseline_note": True,
            "has_multi_objective_tradeoff_explanation": True,
            "scientific_or_structural_errors": [],
        },
        "interaction_spec": {
            "has_coupled_physics_formula_widget": True,
            "has_reversed_or_broken_physics_animation": False,
            "has_interactive_quiz_with_explanation": True,
        },
        "storyboard_slides": storyboard,
        "max_slides_generated_per_step": 2,
        "dual_rubric_eval": {
            "min_passing_score": 90.0,
            "optoelectronic_v3": {
                "category_a_knowledge_items": a_items,
                "b_to_e_grades": {k: "S" for k in ("B1", "B2", "B3", "B4", "C1", "C2", "C3", "D1", "D2", "E1", "E2")},
                "redlines": {},
            },
            "supermolecule_5dim": {
                "dim1_readability_base_25": 24.5,
                "dim1_penalties": {},
                "dim2_logic_score_20": 19.5,
                "dim3_richness_accuracy_20": 19.5,
                "dim4_visual_fidelity_20": 19.0,
                "dim5_interaction_15": 14.5,
            },
        },
        "blue_claimed_score": 97.0,
        "rendered_png_paths": ["slide_01.png", "slide_02.png"],
        "red_critic_findings": [],
    }


def run_design_ag_selftest_suite() -> Dict[str, Any]:
    """Run all negative adversarial assertions and the 18-gate positive gold-standard bundle."""
    _verify_pillar1_static_and_copywriting_gates()
    _verify_pillar2_geometric_optical_and_cropping_gates()
    _verify_pillar3_and_pillar4_pedagogical_and_scoring_gates()

    pos_bundle = _build_gold_standard_positive_bundle()
    receipt = dag.run_all_18_design_gates(pos_bundle)
    if receipt["verdict_zone"] != "PASS" or receipt["gates_passed_count"] != 18:
        raise AssertionError(f"Expected all 18 DesignAG gates to PASS, got: {receipt}")
    return receipt


if __name__ == "__main__":
    import json
    print(json.dumps(run_design_ag_selftest_suite(), indent=2, ensure_ascii=False))
