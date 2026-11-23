"""Verify the real DesignAG 1.0.0-rc.20 facade and HTML-PPT 1.0.0-rc.22 CLI cannot bypass D3/D4/D6/D8/D13/D16/D17/D18."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from release_hashes import write

ROOT = next(
    p for p in Path(__file__).resolve().parents
    if (p / "registry.yaml").is_file() or (p / "registry.fragment.json").is_file()
)
DESIGN = ROOT / "components/skills/design-anti-goodhart/releases/1.0.0-rc.20/source"
HTML = ROOT / "components/skills/html-ppt/releases/1.0.0-rc.22/source/scripts"
sys.path[:0] = [str(DESIGN / "scripts"), str(DESIGN), str(HTML)]
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
        fixture = EvidenceFixture(folder, html_text=original["html_text"])
        from design_contract import digest
        fixture.scores["min_passing_score"] = 85.0
        fixture.review["score_payload_sha256"] = digest(fixture.scores)
        fixture.write()
        bundle = fixture.attach(original)
        result = dag.run_all_18_design_gates(bundle, evidence_context=fixture.context)
        require(result["verdict_zone"] == "PASS" and result["gates_passed_count"] == 18, "full-engine positive")
        checks.append("full_engine_signed_positive")
        result = dag.run_all_18_design_gates(bundle)
        require(result["verdict_zone"] == "FAIL" and len(result["gates_failed"]) == 2, "full-engine unsigned acceptance")
        checks.append("full_engine_missing_context_rejected")
        bad = copy.deepcopy(bundle)
        bad["dual_rubric_eval"]["min_passing_score"] = 0
        result = dag.run_all_18_design_gates(bad, evidence_context=fixture.context)
        require(result["verdict_zone"] == "FAIL", "zero score threshold escaped the facade")
        checks.append("full_engine_zero_threshold_rejected")
        mismatched = copy.deepcopy(bundle)
        mismatched["html_text"] = "<html><body>another document</body></html>"
        require(dag.run_all_18_design_gates(mismatched, evidence_context=fixture.context)["verdict_zone"] == "FAIL", "different source HTML accepted")
        checks.append("full_engine_other_HTML_rejected")
        bundle["crop_specs"] = [{"id": "fig1ab", "subpanel_count": 2, "blank_margin_ratio": 0.0, "border_sliced_ink_ratio": 0.0}]
        bundle_path, targets_path = folder / "bundle.json", folder / "targets.json"
        write(bundle_path, bundle)
        write(targets_path, fixture.context["expected_artifacts"])
        result = verify_deck_evidence(dag, fixture.html, bundle_path, fixture.context)
        require(result["status"] == "PASS", "adapter positive")
        checks.append("html_adapter_positive")
        command = [
            sys.executable, "-B", str(HTML / "audit_single_slide_step.py"),
            "--verify-deck-evidence", str(fixture.html),
            "--review-bundle", str(bundle_path),
            "--evidence-manifest", fixture.context["manifest_path"],
            "--trust-policy", fixture.context["trust_policy_path"],
            "--review-run-id", fixture.context["run_id"],
            "--review-targets", str(targets_path),
        ]
        proc = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", check=False)
        require(proc.returncode == 0 and json.loads(proc.stdout)["presentation_acceptance"] == "PASS", proc.stderr or proc.stdout)
        checks.append("html_CLI_signed_positive")

        # Signed <18px inline SVG deck must still fail D6 inside full 18-gate public facade
        tiny_svg_dir = folder / "tiny_svg_case"
        tiny_svg_html = (
            "<!DOCTYPE html><html><head></head><body><div class='slide'>"
            "<h2>PF 最大的器件，并不是 EQE 最高的器件</h2>"
            "<svg viewBox='0 0 1600 500'><text font-size='14'>内联SVG字号过小</text></svg>"
            "</div></body></html>"
        )
        tiny_fixture = EvidenceFixture(tiny_svg_dir, html_text=tiny_svg_html)
        tiny_fixture.scores["min_passing_score"] = 85.0
        tiny_fixture.review["score_payload_sha256"] = digest(tiny_fixture.scores)
        tiny_fixture.write()
        tiny_bundle = tiny_fixture.attach(copy.deepcopy(original))
        tiny_bundle["interaction_spec"]["has_coupled_physics_formula_widget"] = True
        tiny_res = dag.run_all_18_design_gates(tiny_bundle, evidence_context=tiny_fixture.context)
        require(
            tiny_res["verdict_zone"] == "FAIL"
            and "D6_Teleprompter_Hidden_And_Slide_Density_Cadence_Guard" in tiny_res["gates_failed"],
            f"full-engine accepted <18px inline SVG: {tiny_res}",
        )
        checks.append("full_engine_signed_lt18px_svg_rejected")

        fixture.html.write_text("<html><body>modified after review</body></html>", encoding="utf-8")
        proc = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", check=False)
        require(proc.returncode != 0 and json.loads(proc.stdout)["status"] == "FAIL", "CLI accepted changed deck")
        checks.append("html_CLI_changed_deck_rejected")
        fixture.html.write_text(bundle["html_text"], encoding="utf-8")
        fixture.png.write_bytes(fixture.png.read_bytes() + b"tamper")
        require(dag.run_all_18_design_gates(bundle, evidence_context=fixture.context)["verdict_zone"] == "FAIL", "full-engine changed screenshot accepted")
        checks.append("full_engine_changed_screenshot_rejected")

        # CLI public-route check for 10-slide full-paper deck missing Beyond-PDF background bridge
        bad_sb = folder / "bad_storyboard.json"
        archetypes = ("top_banner_dual_cards", "split_left_fig_right_steps", "interactive_svg_sandbox_split")
        write(bad_sb, {
            "workflow_mode": "GRILL",
            "narrative_spec": {
                "has_macro_background_and_core_def": True,
                "has_degradation_or_bottleneck_mechanism": True,
                "has_prior_art_and_ceiling": True,
                "has_clue_free_blind_guessing": False,
                "has_foreshadowing_and_callback": True,
            },
            "mechanism_spec": {"causal_why_links_explained": {"a": True}},
            "storyboard_slides": [
                {"station_id": f"S_{i}", "title": f"Slide {i}", "layout_archetype": archetypes[(i - 1) % 3]}
                for i in range(1, 11)
            ],
        })
        bg_cmd = [
            sys.executable, "-B", str(HTML / "audit_single_slide_step.py"),
            "--init-storyboard", str(bad_sb),
            "--manifest", str(folder / "bad_manifest.json"),
        ]
        bg_proc = subprocess.run(bg_cmd, capture_output=True, text=True, encoding="utf-8", check=False)
        require(bg_proc.returncode != 0 and json.loads(bg_proc.stdout)["status"] == "FAIL", "CLI accepted 10-slide deck without domain_background_bridge")
        checks.append("html_CLI_missing_beyond_pdf_background_rejected")

        # CLI public-route check: unread-PDF blind module emphasis quiz rejected, and total_slides_mcq rejected unconditionally
        blind_sb = folder / "unread_blind_sb.json"
        write(blind_sb, {
            "workflow_mode": "GRILL",
            "grill_mode": True,
            "global_deck_blueprint": {
                "macro_thesis_probe": {
                    "executive_core_conflict": "蓝光磷光微秒级寿命引发高亮度 TTA 烧屏，利用极化激元反交叉耦合压缩寿命破局",
                    "human_baseline_alignment": "用户尚未读过 PDF，希望靠问答理解这篇工作",
                    "user_has_read_pdf": False,
                },
                "emphasis_allocation_mcq": {
                    "user_has_read_pdf": False,
                    "question_prompt": "以下哪些模块需要作为重头戏展开讲？",
                    "options": ["A: ETL/SPP 色散反交叉哈密顿量", "B: TTA 双分子动力学与 LT95 测试"],
                    "selected_option": "A: ETL/SPP 色散反交叉哈密顿量",
                    "heavy_focus_modules": ["ETL/SPP 色散反交叉"],
                },
                "v3_animation_budget_mcq": {
                    "options": ["A (Recommended): 讲到抽象难点时当场拍板加动态演示", "B: 仅用静态图"],
                    "selected_option": "A (Recommended): 讲到抽象难点时当场拍板加动态演示",
                    "v3_discovery_policy": "JIT_DURING_QA",
                    "min_v3_slides_quota": 1,
                    "v3_designated_slide_indices": [],
                },
            },
            "narrative_spec": {
                "has_macro_background_and_core_def": True,
                "has_degradation_or_bottleneck_mechanism": True,
                "has_prior_art_and_ceiling": True,
                "has_clue_free_blind_guessing": False,
                "has_foreshadowing_and_callback": True,
            },
            "mechanism_spec": {"causal_why_links_explained": {"a": True}},
            "storyboard_slides": [
                {"station_id": "S_1", "title": "五层电致发光三明治结构分流电子与空穴", "layout_archetype": "top_banner_dual_cards"},
                {"station_id": "S_2", "title": "极化激元反交叉劈裂平缓色散段加速辐射", "layout_archetype": "split_left_fig_right_steps"},
            ],
        })
        blind_proc = subprocess.run(
            [sys.executable, "-B", str(HTML / "audit_single_slide_step.py"), "--init-storyboard", str(blind_sb), "--manifest", str(folder / "blind_manifest.json")],
            capture_output=True, text=True, encoding="utf-8", check=False,
        )
        require(blind_proc.returncode != 0 and json.loads(blind_proc.stdout)["status"] == "FAIL", "CLI accepted unread-PDF cold blind-module emphasis quiz")
        checks.append("html_CLI_unread_pdf_blind_module_quiz_rejected")

        slide_count_sb = folder / "slide_count_mcq_sb.json"
        write(slide_count_sb, {
            "workflow_mode": "GRILL",
            "grill_mode": True,
            "global_deck_blueprint": {
                "macro_thesis_probe": {
                    "executive_core_conflict": "蓝光磷光微秒级寿命引发高亮度 TTA 烧屏，利用极化激元反交叉耦合压缩寿命破局",
                    "human_baseline_alignment": "测试即使有其他正常选项，只要还包含页数选择题 total_slides_mcq 就必须拒绝",
                },
                "total_slides_mcq": {
                    "options": ["A: 页数不限", "B: 10–14页紧凑档"],
                    "selected_option": "A: 页数不限",
                    "slide_count_policy": "UNBOUNDED_FLOW_DRIVEN",
                },
                "emphasis_allocation_mcq": {
                    "options": ["A (Recommended): 吃透核心破局机理", "B: 借鉴实验配方与防坑"],
                    "selected_option": "A (Recommended): 吃透核心破局机理",
                    "heavy_focus_modules": ["极化激元反交叉耦合"],
                },
                "v3_animation_budget_mcq": {
                    "options": ["A (Recommended): 讲到抽象难点时当场拍板加动态演示", "B: 仅用静态图"],
                    "selected_option": "A (Recommended): 讲到抽象难点时当场拍板加动态演示",
                    "v3_discovery_policy": "JIT_DURING_QA",
                    "min_v3_slides_quota": 1,
                    "v3_designated_slide_indices": [],
                },
            },
            "narrative_spec": {
                "has_macro_background_and_core_def": True,
                "has_degradation_or_bottleneck_mechanism": True,
                "has_prior_art_and_ceiling": True,
                "has_clue_free_blind_guessing": False,
                "has_foreshadowing_and_callback": True,
            },
            "mechanism_spec": {"causal_why_links_explained": {"a": True}},
            "storyboard_slides": [
                {"station_id": "S_1", "title": "五层电致发光三明治结构分流电子与空穴", "layout_archetype": "top_banner_dual_cards"},
                {"station_id": "S_2", "title": "极化激元反交叉劈裂平缓色散段加速辐射", "layout_archetype": "split_left_fig_right_steps"},
            ],
        })
        sc_proc = subprocess.run(
            [sys.executable, "-B", str(HTML / "audit_single_slide_step.py"), "--init-storyboard", str(slide_count_sb), "--manifest", str(folder / "sc_manifest.json")],
            capture_output=True, text=True, encoding="utf-8", check=False,
        )
        require(sc_proc.returncode != 0 and json.loads(sc_proc.stdout)["status"] == "FAIL", "CLI accepted deprecated total_slides_mcq")
        checks.append("html_CLI_slide_count_mcq_unconditionally_rejected")

        # Signed 17px AI self-scaffolding kicker & Rung footer must fail D3 and D6 in full 18-gate public facade
        scaf_dir = folder / "ai_scaffolding_case"
        scaf_html = (
            "<!DOCTYPE html><html><head></head><body><div class='slide'>"
            "<style>.kicker{font-size:17px;}</style>"
            "<header><span class='kicker'>背景导读第 1 阶 · 宏观产业痛点与传统单晶衍射天花板</span></header>"
            "<h2>PF 最大的器件，并不是 EQE 最高的器件</h2>"
            "<footer>背景知识补齐（论文外通用晶体学图景）· Rung 1: Macro Stakes</footer>"
            "</div></body></html>"
        )
        scaf_fixture = EvidenceFixture(scaf_dir, html_text=scaf_html)
        scaf_fixture.scores["min_passing_score"] = 85.0
        scaf_fixture.review["score_payload_sha256"] = digest(scaf_fixture.scores)
        scaf_fixture.write()
        scaf_bundle = scaf_fixture.attach(copy.deepcopy(original))
        scaf_res = dag.run_all_18_design_gates(scaf_bundle, evidence_context=scaf_fixture.context)
        require(
            scaf_res["verdict_zone"] == "FAIL"
            and "D3_Natural_Academic_Copywriting_No_AI_MetaTone" in scaf_res["gates_failed"]
            and "D6_Teleprompter_Hidden_And_Slide_Density_Cadence_Guard" in scaf_res["gates_failed"],
            f"full-engine accepted 17px AI self-scaffolding labels: {scaf_res}",
        )
        checks.append("full_engine_signed_ai_scaffolding_and_17px_kicker_rejected")

        # Signed 1920x1080 slide with 20px <p> inside hollow 272px space-between card must fail D6 in full 18-gate facade
        hollow_dir = folder / "hollow_card_20px_case"
        hollow_html = (
            "<!DOCTYPE html><html><head></head><body><div class='slide' id='s03'><style>"
            "html,body{margin:0;width:100%;height:100%;overflow:hidden;}"
            "#s03{position:fixed;left:50%;top:50%;width:1920px;height:1080px;transform:translate(-50%,-50%) scale(100vw,100vh);}"
            ".panel{display:flex;flex-direction:column;justify-content:space-between;}"
            "</style><div class='grid-3' style='height:272px;'><div class='panel'>"
            "<div class='panel-hdr'><span>热振动椭球 ADP</span></div>"
            "<p style='font-size:20px;'>即原子位移参数（Atomic Displacement Parameter），类比拍照时被摄者晃动重影：限域越紧，椭球越圆小锐利。</p>"
            "</div></div></div></body></html>"
        )
        hollow_fixture = EvidenceFixture(hollow_dir, html_text=hollow_html)
        hollow_fixture.scores["min_passing_score"] = 85.0
        hollow_fixture.review["score_payload_sha256"] = digest(hollow_fixture.scores)
        hollow_fixture.write()
        hollow_bundle = hollow_fixture.attach(copy.deepcopy(original))
        hollow_res = dag.run_all_18_design_gates(hollow_bundle, evidence_context=hollow_fixture.context)
        require(
            hollow_res["verdict_zone"] == "FAIL"
            and "D6_Teleprompter_Hidden_And_Slide_Density_Cadence_Guard" in hollow_res["gates_failed"],
            f"full-engine accepted hollow 272px 20px-font card on 1920x1080 slide: {hollow_res}",
        )
        checks.append("full_engine_signed_hollow_20px_hd_card_rejected")

        # Signed Slide 3 orphan bare-noun bottom 3-card strip must fail D3, D4, and D6 in full 18-gate facade
        orphan_dir = folder / "orphan_bottom_strip_case"
        orphan_html = (
            "<!DOCTYPE html><html><head></head><body><section class='slide'>"
            "<div class='panel'><svg viewBox='0 0 1720 410' width='1720' height='410'>"
            "<text font-size='22'>① 预制刚性多孔母晶</text><text font-size='22'>④ 傅里叶电子密度图</text></svg></div>"
            "<div class='grid-3'>"
            "<div class='panel'><span class='panel-title'>电子密度 Q 峰</span><p style='font-size:22px;'>类比三维山峰图定位骨架。</p></div>"
            "<div class='panel'><span class='panel-title'>热振动椭球 ADP</span><p style='font-size:22px;'>即原子位移参数反映热晃动。</p></div>"
            "<div class='panel'><span class='panel-title'>精修残差因子 R1</span><p style='font-size:22px;'>衡量计算与实测振幅相对误差。</p></div>"
            "</div></section></body></html>"
        )
        orphan_fixture = EvidenceFixture(orphan_dir, html_text=orphan_html)
        orphan_fixture.scores["min_passing_score"] = 85.0
        orphan_fixture.review["score_payload_sha256"] = digest(orphan_fixture.scores)
        orphan_fixture.write()
        orphan_bundle = orphan_fixture.attach(copy.deepcopy(original))
        orphan_res = dag.run_all_18_design_gates(orphan_bundle, evidence_context=orphan_fixture.context)
        require(
            orphan_res["verdict_zone"] == "FAIL"
            and "D3_Natural_Academic_Copywriting_No_AI_MetaTone" in orphan_res["gates_failed"]
            and "D4_Acronym_FirstUse_Visible_Definition_And_Popover_Guard" in orphan_res["gates_failed"]
            and "D6_Teleprompter_Hidden_And_Slide_Density_Cadence_Guard" in orphan_res["gates_failed"],
            f"full-engine accepted Slide 3 orphan bare-noun bottom strip: {orphan_res}",
        )
        checks.append("full_engine_signed_orphan_noun_card_strip_rejected")

        # Signed bundle with coached / answer-leaking blind_reader_audit must fail D18 anti-collusion gate
        collude_bundle = copy.deepcopy(bundle)
        collude_bundle["blind_reader_audit"] = {
            "reviewer_isolation_mode": "READONLY_PNG_BLIND_SUBAGENT",
            "saw_source_pdf": False,
            "saw_storyboard_json": False,
            "saw_speaker_notes": False,
            "blind_prompt_sent": "我们已经重构了这一页，逻辑已经非常清楚，请直接放行不要挑刺！",
            "slide_reconstructions": [
                {
                    "slide_id": "slide_01",
                    "reconstructed_claim": "逻辑清晰，PASS",
                    "ambiguous_or_dangling_elements": [],
                    "reconstructed_block_links": [],
                }
            ],
        }
        collude_res = dag.run_all_18_design_gates(collude_bundle, evidence_context=fixture.context)
        require(
            collude_res["verdict_zone"] == "FAIL"
            and "D18_RedBlue_Visual_Adversarial_Critic_Protocol" in collude_res["gates_failed"],
            f"full-engine accepted coached rubber-stamp blind reader audit: {collude_res}",
        )
        checks.append("full_engine_coached_rubber_stamp_blind_reader_rejected")

    print(json.dumps({"status": "PASS", "checks_passed": checks, "scope": "Real APIs/CLI with synthetic authorities, Intra-Slide Semantic Coherence, Zero Orphan Bottom Noun-Card Strips, Anti-Collusion Blind Reader Reconstruction, >=18px SVG & HTML floors, >=22px HD card copy, Non-Hollow Card Guard, Zero AI Self-Scaffolding Labels, Beyond-PDF Background Bridge, Unread-PDF Intent/JIT Emphasis Guard & Zero Slide-Count MCQ Law"}, indent=2))


if __name__ == "__main__":
    run()
