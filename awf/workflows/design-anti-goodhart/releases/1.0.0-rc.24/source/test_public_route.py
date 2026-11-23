"""Verify the real DesignAG 1.0.0-rc.24 facade and HTML-PPT 1.0.0-rc.26 CLI cannot bypass D3/D4/D5/D6/D8/D13/D16/D17/D18."""
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
DESIGN = ROOT / "components/skills/design-anti-goodhart/releases/1.0.0-rc.24/source"
HTML = ROOT / "components/skills/html-ppt/releases/1.0.0-rc.26/source/scripts"
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
        require(result["verdict_zone"] == "PASS" and result["gates_passed_count"] == 18, f"full-engine positive: {result}")
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
        bundle["crop_specs"] = [{"id": "fig1a", "subpanel_count": 1, "blank_margin_ratio": 0.0, "border_sliced_ink_ratio": 0.0}]
        bundle_path, targets_path = folder / "bundle.json", folder / "targets.json"
        write(bundle_path, bundle)
        write(targets_path, fixture.context["expected_artifacts"])
        result = verify_deck_evidence(dag, fixture.html, bundle_path, fixture.context)
        require(result["status"] == "PASS", f"adapter positive: {result}")
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

        # Signed <32px (e.g. 26px) inline SVG deck must fail D6 inside full 18-gate public facade
        tiny_svg_dir = folder / "tiny_svg_case"
        tiny_svg_html = (
            "<!DOCTYPE html><html><head></head><body><div class='slide'>"
            "<h1 style='font-size:58px;'>最大功率因子并不对应最高效率</h1>"
            "<svg viewBox='0 0 1600 500'><text font-size='26'>内联SVG字号26px小于32px红线</text></svg>"
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
            f"full-engine accepted <32px inline SVG: {tiny_res}",
        )
        checks.append("full_engine_signed_lt32px_svg_rejected")

        # Signed >260 visible-char slide must fail D6 even when fonts are >=42px
        dense_dir = folder / "over260_chars_case"
        dense_html = (
            "<!DOCTYPE html><html><head></head><body><div class='slide' id='s01'><style>"
            "html,body{margin:0;width:100%;height:100%;overflow:hidden;}"
            "#s01{position:fixed;left:50%;top:50%;width:1920px;height:1080px;transform:translate(-50%,-50%) scale(100vw,100vh);}"
            "</style>"
            "<h1 style='font-size:58px;'>单页可见文字超过两百六十字符必须拦截</h1>"
            "<div class='card'><h3 style='font-size:46px;'>过密段落一堆满屏幕导致观众无法瞬间抓取主干</h3>"
            "<p style='font-size:42px;'>在两倍大字号规范下如果单页仍然堆砌超过两百六十个可见字符就会严重挤压留白并迫使观众逐字默读丧失幻灯片一页一跃迁的清晰感因此必须拆成连续多页或收进可点击弹窗中按需展开。</p></div>"
            "<div class='card'><h3 style='font-size:46px;'>过密段落二继续叠加实验配方与补充对照细节</h3>"
            "<p style='font-size:42px;'>把旋涂转速退火温度溶剂体积比核磁氢谱归属与紫外光电子能谱二次电子截止边全部直接平铺在主画布上使总字数突破三百字红线触发低密度门禁拦截。此外还把瞬态吸收飞秒泵浦波长时间常数双指数拟合残差外量子效率积分电流以及最大功率点连续追踪三百秒稳态曲线说明一并塞进同一张页面导致单页总字符数超过三百一十个可见字符。</p></div>"
            "</div></body></html>"
        )
        dense_fixture = EvidenceFixture(dense_dir, html_text=dense_html)
        dense_fixture.scores["min_passing_score"] = 85.0
        dense_fixture.review["score_payload_sha256"] = digest(dense_fixture.scores)
        dense_fixture.write()
        dense_bundle = dense_fixture.attach(copy.deepcopy(original))
        dense_res = dag.run_all_18_design_gates(dense_bundle, evidence_context=dense_fixture.context)
        require(
            dense_res["verdict_zone"] == "FAIL"
            and "D6_Teleprompter_Hidden_And_Slide_Density_Cadence_Guard" in dense_res["gates_failed"],
            f"full-engine accepted >260 visible chars slide: {dense_res}",
        )
        checks.append("full_engine_signed_over260_visible_chars_rejected")

        # Signed dangling .detail-trigger without matching <template data-detail-id> must fail D6
        dangling_dir = folder / "dangling_popover_case"
        dangling_html = (
            "<!DOCTYPE html><html><head></head><body><div class='slide' id='s02'><style>"
            "html,body{margin:0;width:100%;height:100%;overflow:hidden;}"
            "#s02{position:fixed;left:50%;top:50%;width:1920px;height:1080px;transform:translate(-50%,-50%) scale(100vw,100vh);}"
            "</style>"
            "<span class='topo-breadcrumb' data-topo-node='T2.1' style='font-size:32px;'>主线二 · 分子取向破局</span>"
            "<h1 style='font-size:58px;'>螺环侧链阻断π堆积释放锚定头基</h1>"
            "<div class='card'><h3 style='font-size:46px;'>立体位阻切断共平面团聚</h3>"
            "<p style='font-size:42px;'>正交螺环撑开邻近咔唑，把游离磷酸锚定比例提升至 89%。</p>"
            "<button class='detail-trigger' data-detail-id='missing_payload' style='font-size:32px;'>+ 查看 XPS 分峰铁证</button>"
            "</div></div></body></html>"
        )
        dangling_fixture = EvidenceFixture(dangling_dir, html_text=dangling_html)
        dangling_fixture.scores["min_passing_score"] = 85.0
        dangling_fixture.review["score_payload_sha256"] = digest(dangling_fixture.scores)
        dangling_fixture.write()
        dangling_bundle = dangling_fixture.attach(copy.deepcopy(original))
        dangling_res = dag.run_all_18_design_gates(dangling_bundle, evidence_context=dangling_fixture.context)
        require(
            dangling_res["verdict_zone"] == "FAIL"
            and "D6_Teleprompter_Hidden_And_Slide_Density_Cadence_Guard" in dangling_res["gates_failed"],
            f"full-engine accepted dangling .detail-trigger button: {dangling_res}",
        )
        checks.append("full_engine_signed_dangling_detail_trigger_rejected")

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

        # CLI public-route check: DROPPED / OMITTED item in lossless_split_and_popover_ledger must fail --init-storyboard
        dropped_sb = folder / "dropped_ledger_sb.json"
        write(dropped_sb, {
            "workflow_mode": "AUTONOMOUS_DUAL_EVOLVE",
            "narrative_spec": {
                "has_macro_background_and_core_def": True,
                "has_degradation_or_bottleneck_mechanism": True,
                "has_prior_art_and_ceiling": True,
                "has_clue_free_blind_guessing": False,
                "has_foreshadowing_and_callback": True,
            },
            "mechanism_spec": {"causal_why_links_explained": {"a": True}},
            "lossless_split_and_popover_ledger": {
                "zero_information_loss_verified": True,
                "preserved_evidence_items": [
                    {
                        "evidence_id": "ev_sfg",
                        "content_summary": "SFG 二阶非线性振动光谱取向角推导细节",
                        "preservation_channel": "DROPPED",
                    }
                ],
            },
            "storyboard_slides": [
                {
                    "station_id": "S_1",
                    "topo_node_id": "T1.1",
                    "title": "螺环位阻释放磷酸锚定头基",
                    "layout_archetype": "top_banner_dual_cards",
                },
                {
                    "station_id": "S_2",
                    "topo_node_id": "T1.2",
                    "title": "面外堆积加速空穴隧穿提取",
                    "layout_archetype": "split_left_fig_right_steps",
                },
            ],
        })
        drop_proc = subprocess.run(
            [sys.executable, "-B", str(HTML / "audit_single_slide_step.py"), "--init-storyboard", str(dropped_sb), "--manifest", str(folder / "drop_manifest.json")],
            capture_output=True, text=True, encoding="utf-8", check=False,
        )
        require(drop_proc.returncode != 0 and json.loads(drop_proc.stdout)["status"] == "FAIL", "CLI accepted DROPPED item in lossless_split_and_popover_ledger")
        checks.append("html_CLI_dropped_lossless_ledger_item_rejected")

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
            "<text font-size='32'>① 预制刚性多孔母晶</text><text font-size='32'>④ 傅里叶电子密度图</text></svg></div>"
            "<div class='grid-3'>"
            "<div class='panel'><span class='panel-title' style='font-size:36px;'>电子密度 Q 峰</span><p style='font-size:42px;'>类比三维山峰图定位骨架。</p></div>"
            "<div class='panel'><span class='panel-title' style='font-size:36px;'>热振动椭球 ADP</span><p style='font-size:42px;'>即原子位移参数反映热晃动。</p></div>"
            "<div class='panel'><span class='panel-title' style='font-size:36px;'>精修残差因子 R1</span><p style='font-size:42px;'>衡量计算与实测振幅相对误差。</p></div>"
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

        # Signed pre-background Slide 01 leaking paper-specific 3-PMPCl + 3-N吡啶 + 哌嗪环 must fail D13 in full 18-gate facade
        leak_dir = folder / "pre_bg_3pmpcl_leak_case"
        leak_html = (
            "<!DOCTYPE html><html><head></head><body><section class='slide'>"
            "<h1 style='font-size:58px;'>熵调控分子锁稳定纯相钙钛矿电池</h1>"
            "<svg viewBox='0 0 1600 600'><text font-size='34'>双端柔性分子锁 3-PMPCl：3-N吡啶锁骨架，哌嗪环放旋转</text></svg>"
            "</section></body></html>"
        )
        leak_fixture = EvidenceFixture(leak_dir, html_text=leak_html)
        leak_fixture.scores["min_passing_score"] = 85.0
        leak_fixture.review["score_payload_sha256"] = digest(leak_fixture.scores)
        leak_fixture.write()
        leak_bundle = leak_fixture.attach(copy.deepcopy(original))
        leak_bundle["narrative_spec"] = copy.deepcopy(original["narrative_spec"])
        leak_bundle["narrative_spec"]["domain_background_bridge"]["background_slide_indices"] = [2, 3, 4]
        leak_bundle["universal_io_bus_capsule"] = {
            "evidence_ingest_ledger": [
                {
                    "claim_id": "Claim_3PMPCl",
                    "quantitative_value": "3-PMPCl 将体相能垒提至 3.07 eV，认证效率 27.6%",
                    "source_artifact_or_figure_ref": "Science 2026 Fig. 1",
                }
            ],
            "devil_reviewer_capsule": {
                "alternative_hypothesis_challenge": "为何间位氮 3-PMPCl 优于对位氮 4-PMPCl？",
                "control_evidence_rebuttal": "573 K 下 3-PMPCl 表面覆盖率与体相能垒均更高。",
            },
            "output_artifact_targets": ["HTML_PPT"],
        }
        leak_res = dag.run_all_18_design_gates(leak_bundle, evidence_context=leak_fixture.context)
        require(
            leak_res["verdict_zone"] == "FAIL"
            and "D13_Narrative_Arc_Background_PriorArt_And_Foreshadowing_Guard" in leak_res["gates_failed"],
            f"full-engine accepted pre-background Slide 01 leaking 3-PMPCl: {leak_res}",
        )
        checks.append("full_engine_signed_prebackground_3pmpcl_recipe_leak_rejected")

        # Signed opening Rung 1 slide jumping into 间接带隙 / 直接带隙 / S–Q 极限 formalism must fail D13 in full 18-gate facade
        rung1_jump_dir = folder / "rung1_band_jump_case"
        rung1_jump_html = (
            "<!DOCTYPE html><html><head></head><body><section class='slide'>"
            "<h1 style='font-size:58px;'>单结晶硅逼近上限，钙钛矿向单结极限推进</h1>"
            "<svg viewBox='0 0 1600 600'><text font-size='34'>间接带隙 1.12 eV · 直接带隙 1.48 eV · S–Q 极限 33.7%</text></svg>"
            "</section></body></html>"
        )
        rung1_fixture = EvidenceFixture(rung1_jump_dir, html_text=rung1_jump_html)
        rung1_fixture.scores["min_passing_score"] = 85.0
        rung1_fixture.review["score_payload_sha256"] = digest(rung1_fixture.scores)
        rung1_fixture.write()
        rung1_bundle = rung1_fixture.attach(copy.deepcopy(original))
        rung1_bundle["storyboard_slides"] = copy.deepcopy(original["storyboard_slides"])
        rung1_bundle["storyboard_slides"][0]["is_background_slide"] = True
        rung1_bundle["storyboard_slides"][0]["background_rung"] = 1
        rung1_bundle["narrative_spec"] = copy.deepcopy(original["narrative_spec"])
        rung1_bundle["narrative_spec"]["domain_background_bridge"]["four_rung_funnel"]["rung1_macro_industry_stakes"] = (
            "晶硅光伏占全球 95% 以上装机但受限于 1400 °C 熔硅高能耗与刚性面积瓶颈，100 °C 溶液涂布钙钛矿卡在湿热寿命"
        )
        rung1_res = dag.run_all_18_design_gates(rung1_bundle, evidence_context=rung1_fixture.context)
        require(
            rung1_res["verdict_zone"] == "FAIL"
            and "D13_Narrative_Arc_Background_PriorArt_And_Foreshadowing_Guard" in rung1_res["gates_failed"],
            f"full-engine accepted opening Rung 1 slide jumping into band formalism: {rung1_res}",
        )
        checks.append("full_engine_signed_rung1_band_formalism_jump_rejected")

        # CLI public-route check: --verify-blind-reader rejects blind-reader receipt reconstructing 3-PMPCl on Slide 01 without macro onboarding
        pv_sb_path = folder / "pv_bg_sb.json"
        pv_manifest_path = folder / "pv_bg_manifest.json"
        pv_blind_path = folder / "pv_escaped_blind.json"
        write(pv_sb_path, {
            "workflow_mode": "AUTONOMOUS_DUAL_EVOLVE",
            "require_beyond_pdf_background": True,
            "domain_background_bridge": {
                "pdf_omitted_background_gaps": [
                    "原始论文默认读者熟知全球晶硅光伏高温熔硅能耗与刚性面积瓶颈，未铺垫涂布式钙钛矿产业定位",
                    "原始论文首段直接切入甲脒铅碘相变能垒与旋转熵，缺少五层三明治发电原理铺垫",
                ],
                "outside_pdf_onboarding_primer": "晶硅太阳能板需千度高温熔硅且单层效率近顶；百摄氏度涂布钙钛矿兼具叠层高效率潜力却怕湿热变黄。",
                "four_rung_funnel": {
                    "rung1_macro_industry_stakes": "晶硅占全球 95% 装机但受限于 1400 °C 熔硅能耗，100 °C 溶液涂布钙钛矿卡在湿热寿命",
                    "rung2_canonical_working_principle": {
                        "summary": "倒置五层钙钛矿器件受光照产生电子与空穴，沿两侧传输层能级台阶分流输出电压",
                        "visual_schematic_plan": "硅基高温产线对比涂布钙钛矿产线双轨 SVG 图 + 五层三明治能级图",
                    },
                    "rung3_core_jargon_translations": [
                        {"term": "立方黑相与六方黄相", "plain_analogy": "三维透气发电笼 vs 坍塌绝缘柱", "physical_meaning": "共顶八面体导电吸光，共面黄相绝缘"},
                        {"term": "准费米能级劈裂", "plain_analogy": "水电站上下游最大水位差", "physical_meaning": "光照下电子与空穴化学势差"},
                    ],
                    "rung4_prior_art_deadlock": "传统外源离子混掺虽稳相却拉偏带隙且局部未掺杂微区触发多米诺坍塌",
                },
                "background_slide_indices": [2, 3, 4],
                "paper_claims_strictly_from_pdf": True,
            },
            "universal_io_bus_capsule": leak_bundle["universal_io_bus_capsule"],
            "narrative_spec": {
                "has_macro_background_and_core_def": True,
                "has_degradation_or_bottleneck_mechanism": True,
                "has_prior_art_and_ceiling": True,
                "has_clue_free_blind_guessing": False,
                "has_foreshadowing_and_callback": True,
            },
            "mechanism_spec": {"causal_why_links_explained": {"a": True}},
            "storyboard_slides": [
                {"station_id": "S_1", "title": "熵调控分子锁稳定纯相钙钛矿太阳能电池", "layout_archetype": "hero_clean_suspense_cover", "is_background_slide": False, "required_visual_level": "V2"},
                {"station_id": "S_2", "title": "晶硅受限于高温熔硅能耗与刚性面积瓶颈", "layout_archetype": "dual_track_industrial_macro_svg", "is_background_slide": True, "background_rung": 1, "required_visual_level": "V2"},
                {"station_id": "S_3", "title": "倒置五层光电三明治靠能级台阶分流载流子", "layout_archetype": "split_left_fig_right_steps", "is_background_slide": True, "background_rung": 2, "required_visual_level": "V2"},
                {"station_id": "S_4", "title": "传统混掺拉宽带隙且未掺杂微区触发多米诺坍塌", "layout_archetype": "interactive_svg_sandbox_split", "is_background_slide": True, "background_rung": 4, "required_visual_level": "V2"},
            ],
        })
        init_pv_proc = subprocess.run(
            [sys.executable, "-B", str(HTML / "audit_single_slide_step.py"), "--init-storyboard", str(pv_sb_path), "--manifest", str(pv_manifest_path)],
            capture_output=True, text=True, encoding="utf-8", check=False,
        )
        require(init_pv_proc.returncode == 0, f"PV manifest init failed: {init_pv_proc.stdout or init_pv_proc.stderr}")
        write(pv_blind_path, {
            "reviewer_isolation_mode": "READONLY_PNG_BLIND_SUBAGENT",
            "saw_source_pdf": False,
            "saw_storyboard_json": False,
            "saw_speaker_notes": False,
            "blind_prompt_sent": "仅根据所给单页渲染截图独立复述唯一核心结论、次级模块连接证据与任何未铺垫概念。",
            "slide_reconstructions": [
                {
                    "slide_id": "slide_01",
                    "reconstructed_claim": "在晶界引入双端分子锁 3-PMPCl，利用刚性 3-N 吡啶与柔性哌嗪环阻断黄相坍塌。",
                    "ambiguous_or_dangling_elements": [],
                    "reconstructed_block_links": [],
                }
            ],
        })
        blind_cli_proc = subprocess.run(
            [sys.executable, "-B", str(HTML / "audit_single_slide_step.py"), "--manifest", str(pv_manifest_path), "--verify-blind-reader", str(pv_blind_path)],
            capture_output=True, text=True, encoding="utf-8", check=False,
        )
        require(blind_cli_proc.returncode != 0 and json.loads(blind_cli_proc.stdout)["status"] == "FAIL", "CLI accepted blind reader receipt leaking 3-PMPCl on Slide 01 without macro onboarding")
        checks.append("html_CLI_blind_reader_premature_3pmpcl_and_missing_macro_onboarding_rejected")

        # rc.23 / rc.25 public-route check: homogeneous Gen-0 prompts + Stage A LOW_AMBIGUOUS_GEOMETRY stick doodle rejected
        homo_ledger_path = folder / "homo_ledger.json"
        write(homo_ledger_path, {
            "slide_id": "slide_01",
            "generations_completed": 1,
            "is_text_free_base": True,
            "has_vector_callout_overlay": True,
            "winner_id": "g0_a",
            "gen0_candidates": [
                {"id": "g0_a", "sha256": "1" * 32, "camera_topology": "ISOMETRIC_3D_CUTAWAY", "rendering_medium": "SUBSURFACE_3D", "prompt": "Pure white cortical brain folds multipolar neurons rigid silicon probe reactive glial scar gold pad", "score": 38.0, "is_text_free": True},
                {"id": "g0_b", "sha256": "2" * 32, "camera_topology": "ISOMETRIC_3D_CUTAWAY", "rendering_medium": "SUBSURFACE_3D", "prompt": "Pure white cortical brain folds multipolar neurons stiff grey silicon probe reactive glial scar gold site", "score": 37.0, "is_text_free": True},
                {"id": "g0_c", "sha256": "3" * 32, "camera_topology": "ISOMETRIC_3D_CUTAWAY", "rendering_medium": "SUBSURFACE_3D", "prompt": "Pure white cortical brain folds multipolar neurons metallic silicon probe dense glial scar gold pad", "score": 36.5, "is_text_free": True},
                {"id": "g0_d", "sha256": "4" * 32, "camera_topology": "ISOMETRIC_3D_CUTAWAY", "rendering_medium": "SUBSURFACE_3D", "prompt": "Pure white cortical brain folds multipolar neurons rigid silicon probe inflamed glial scar gold tip", "score": 36.0, "is_text_free": True},
            ],
            "evolved_candidates": [],
        })
        homo_cli = subprocess.run(
            [sys.executable, "-B", str(HTML / "audit_single_slide_step.py"), "--manifest", str(pv_manifest_path), "--verify-image-tournament", str(homo_ledger_path)],
            capture_output=True, text=True, encoding="utf-8", check=False,
        )
        require(homo_cli.returncode != 0 and json.loads(homo_cli.stdout)["status"] == "FAIL", "CLI accepted homogeneous single-gen Gen-0 prompt clones")
        checks.append("html_CLI_homogeneous_single_gen_image_tournament_rejected")

        masked_bad_path = folder / "masked_bad_obj.json"
        write(masked_bad_path, {
            "reviewer_isolation_mode": "READONLY_PNG_BLIND_SUBAGENT",
            "saw_source_pdf": False,
            "saw_storyboard_json": False,
            "saw_speaker_notes": False,
            "visual_entity_manifest": [{"entity_id": "neuron", "scale_class": "BIO_MACRO_SYSTEM", "render_route": "EVOLUTIONARY_TEXTFREE_ILLUSTRATION_PLUS_SVG_CALLOUTS", "expected_class_keywords": ["neuron", "神经元"]}],
            "stage_a_masked_visual": {
                "stage_a_all_text_hidden": True,
                "text_masked_png_sha256": "a" * 32,
                "stage_a_blind_prompt": "Inspect the pure text-free visual region only and name every drawn physical object.",
                "unrecognizable_crude_glyphs": ["red dots with stick tails"],
                "recognized_objects": [{"visual_description": "Two red dots with two short lines", "blind_guessed_object": "circle stick symbol", "recognition_confidence": "LOW_AMBIGUOUS_GEOMETRY", "craft_tier": "T0_STICK_DOODLE"}],
            },
            "stage_b_full_slide_check": {"full_slide_png_sha256": "b" * 32, "bitmap_pseudo_text_detected": False, "leader_line_misalignment_or_crossing": []},
        })
        masked_cli = subprocess.run(
            [sys.executable, "-B", str(HTML / "audit_single_slide_step.py"), "--manifest", str(pv_manifest_path), "--verify-blind-object-recognition", str(masked_bad_path)],
            capture_output=True, text=True, encoding="utf-8", check=False,
        )
        require(masked_cli_proc_rc := masked_cli.returncode != 0 and json.loads(masked_cli.stdout)["status"] == "FAIL", "CLI accepted Stage A LOW_AMBIGUOUS_GEOMETRY stick doodle")
        checks.append("html_CLI_two_stage_masked_stick_doodle_rejected")

        # rc.24 / rc.26 public-route check: structured 3-step Wittgenstein Ladder, 7-element anatomy & Teach-on-Miss Re-Grill
        hollow_ladder = dag.verify_tdd_station_capsule_completeness({
            "station_id": "Station_1.1",
            "core_blindspot_or_conflict": "热弛豫退火速率决定亚稳态锁仓寿命",
            "wittgenstein_ladder": "就像上紧发条的玩具慢慢松弛回到原位一样",
            "human_orthogonal_insight": "基态释放客体，亚稳态抓取客体",
            "visual_modality": "V2_CUSTOM_VECTOR_DIAGRAM",
            "hidden_teleprompter_qa": "比较热弛豫速率与光子吸收通量的稳态比值",
        })
        require(not hollow_ladder["passed"], "DesignAG accepted hollow single-sentence wittgenstein_ladder")
        checks.append("designag_hollow_single_sentence_ladder_rejected")

        rubber_stamp_miss = dag.verify_tdd_station_capsule_completeness({
            "station_id": "Station_1.1",
            "core_blindspot_or_conflict": "热弛豫退火速率决定亚稳态锁仓寿命",
            "wittgenstein_ladder": {
                "bridge": "类比用单向棘轮把水流抽到高位蓄水池。",
                "deconstruct": "宏观棘轮靠机械卡榫硬锁，但分子尺度布朗热涨落无处不在且无硬卡榫，该类比在热能隙与微观可逆性边界处失效。",
                "replace": "必须用稳态光通量与 Eyring 热回退速率 k_Δ = (k_B T/h) exp(-ΔG‡/RT) 的竞争比值定义锁仓寿命。",
            },
            "human_orthogonal_insight": "基态释放客体，亚稳态抓取客体",
            "visual_modality": "V2_CUSTOM_VECTOR_DIAGRAM",
            "hidden_teleprompter_qa": "比较 k_hv 与 k_Δ 在 288 K 下的稳态分数",
            "user_missed_or_uncertain": True,
            "teach_on_miss_and_regrill_closure": {
                "wittgenstein_teach_explanation": "已补充三步维特根斯坦拆梯与 Eyring 能垒判据。",
                "isomorphic_regrill_question": "这下你听懂了吗？",
            },
        })
        require(not rubber_stamp_miss["passed"], "DesignAG accepted rubber-stamp Teach-on-Miss re-grill prompt")
        checks.append("designag_rubber_stamp_regrill_rejected")

        full_tdd_ok = dag.verify_tdd_station_capsule_completeness({
            "station_id": "Station_1.1",
            "is_background_station": True,
            "beyond_pdf_background_synthesis": "传统化学燃料体系每完成一次抓放循环就不可避免产生化学废物；光驱动耗散自组装则用稳态光子通量维持高能态容器，停光即自发退回基态释放货物。",
            "core_blindspot_or_conflict": "为何室温热能足以翻越过低的激发态/亚稳态回退能垒导致空转",
            "wittgenstein_ladder": {
                "bridge": "就像把球踢上山坡凹槽暂存货物的单坡储物台。",
                "deconstruct": "宏观山坡台阶高度远超环境风吹草动，但分子处于 k_B T 室温热浴持续碰撞中，若坡沿能垒 ΔG‡ 过低，棘轮类比失效并退化为瞬时热漏。",
                "replace": "由稳态分数 f_meta = k_hv / (k_hv + k_Δ) 与 Eyring 速率 k_Δ = (k_B T / h) exp(-ΔG‡ / RT) 共同设定抓放时间窗。",
            },
            "require_seven_element_anatomy": True,
            "seven_element_anatomy": {
                "principle_and_logic": "光泵浦速率压倒热弛豫速率时才能维持高能亚稳态集聚。",
                "physical_picture": "稳态光流持续填充浅势阱容器，停光即按指数速率热泄放。",
                "mathematical_formulation": "f_meta = k_hv / (k_hv + k_Δ); k_Δ = (k_B T / h) exp(-ΔG‡ / RT)",
                "scope_and_boundary": "适用于无副反应的光异构双稳态容器在恒温溶液中的持续辐照稳态。",
                "pros_and_cons": "优势是零化学废物与远程开关控制；代价是需要持续能量输入并存在光照渗透约束。",
                "alternatives_comparison": "相比化学燃料添加-中和循环，省去了副产物积累对宿主构象的毒化。",
                "concrete_evidence_or_implementation": "对比常规 365 nm 短半衰期开关与小时级长半衰期闭环容器的升温/降温稳态响应。",
            },
            "human_orthogonal_insight": "基态释放客体，亚稳态抓取客体",
            "visual_modality": "V2_CUSTOM_VECTOR_DIAGRAM",
            "hidden_teleprompter_qa": "若将浴温从 15 °C 升至 75 °C，k_Δ 指数飙升将怎样压低稳态高能态占比？",
            "user_missed_or_uncertain": True,
            "teach_on_miss_and_regrill_closure": {
                "wittgenstein_teach_explanation": "先以山坡凹槽搭梯，再指出热浴碰撞令低能垒槽秒级漏空从而拆梯，最后用 f_meta 与 Eyring 公式替换定量判定半衰期窗口。",
                "isomorphic_regrill_question": "若LED光强不变而溶液温度从 15 °C 突然升至 75 °C，稳态抓取容器占比会怎么变，为什么？",
            },
        })
        require(full_tdd_ok["passed"], f"DesignAG rejected valid 3-step/7-element/Teach-on-Miss capsule: {full_tdd_ok}")
        checks.append("designag_wittgenstein_3step_7element_teach_on_miss_accepted")

    print(json.dumps({"status": "PASS", "checks_passed": checks, "scope": "Real APIs/CLI with synthetic authorities, Canvas-vs-Dialogue Anti-Dilution Law, Structured 3-Step Wittgenstein Ladder, 7-Element Anatomy & Teach-on-Miss Re-Grill Closure, Universal 5-Scale Physical-Entity Fidelity, 4-Axis Orthogonal Image Exploration + Gen-1+ Evolution, Two-Stage Text-Masked Blind Object Recognition (D5 & D18), Pre-Background Paper-Recipe Leak Guard & Opening Rung-1 Macro-Stakes HTML Grounding (D13), Outsider Blind-Reader Macro-Onboarding Verification, 2x Large Typography (>=32px SVG/HTML, >=42px HD body, >=56px HD title), <=260-Char Low-Density Guard, Clickable Detail Popovers & Lossless Multi-Slide Split Ledger"}, indent=2))


if __name__ == "__main__":
    run()
