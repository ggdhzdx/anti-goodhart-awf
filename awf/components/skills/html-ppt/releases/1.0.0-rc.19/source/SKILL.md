---
name: html-ppt
description: Build, audit, and evolve 16:9 scientific interactive HTML presentations (AWF HTML-PPT / SciSlide) under a Two-Level Macro-to-Micro Tri-Mode Architecture with Mandatory Beyond-PDF 4-Rung Domain Background Synthesis (`domain_background_bridge`: proactively synthesizing foundational world knowledge, everyday physical analogies, and >=3 V2/V3 custom-SVG/interactive onboarding slides omitted by raw PDFs across `TDD` Tutor, Briefing-First `GRILL`, and `AUTONOMOUS_DUAL_EVOLVE`), Unread-PDF AI Value-vs-Routine Triage (`ai_value_triage`) + Reader-Intent / `JIT_DURING_GRILL` Dynamic Emphasis (banning blind paper-module catalog quizzes on unread users), Zero Slide-Count MCQ Law (NEVER ask the user how to choose slide counts or preset fixed total pages—slide count grows purely by logic and need), Inline-SVG >=18px Typography & Single-Slide Density Caps, strictly 1-Slide-Per-Step (`max_slides_generated_per_step == 1`), and 1-Hop Slide Topological Lock (`slide_manifest.json`), gated by `skill.design-anti-goodhart@1.0.0-rc.17` (AWF DesignAG) and `skill.anti-goodhart-verification@3.7.0-rc.7` (AWF Guard). Use whenever creating, revising, or auditing HTML slide decks, scientific paper walkthroughs, or teaching presentations.
---

# AWF HTML-PPT V3 (`skill.html-ppt@1.0.0-rc.19` — Beyond-PDF 4-Rung Background Synthesis + Unread-PDF Value Triage & Reader-Intent / JIT Grill Emphasis + Zero Slide-Count MCQ (Pure Logic & Need Driven) + Inline-SVG >=18px & Single-Slide Density Guards + Two-Level Macro-to-Micro Tri-Mode Engine: Stage 0 Global Deck Blueprint + Stage 1..N `TDD` / Briefing-First `GRILL` / `AUTONOMOUS_DUAL_EVOLVE`, Strictly 1-Slide-Per-Step & `AWF DesignAG` 18-Gate Enforcement)

An anti-Goodhart, self-evolving scientific HTML presentation authoring and verification engine. Specialist research PDFs almost always omit foundational background, and **users opening a walkthrough have typically NOT read the PDF yet (`user_has_read_pdf: false` by default)**. Asking an unread user *"以下哪些模块需要作为重头戏展开讲？"* with unfamiliar paper module names forces blind rubber-stamp guessing. To prevent audience/user bewilderment ("一头雾水"), blind Stage 0 module guessing, mid-deck attention collapse, template cloning, unrendered LaTeX leaks, overlapping/clipped DOM boxes, and pure-text laziness (`V0 = 0.30` cap), **AWF HTML-PPT V3 mandates proactive Beyond-PDF 4-Rung Domain Background Synthesis (`domain_background_bridge`), upfront AI Value-vs-Routine Triage (`ai_value_triage`), Reader-Intent or `JIT_DURING_GRILL` emphasis discovery, strictly 1-Slide-Per-Step generation**, and a **Tri-Mode Execution Architecture** (`workflow_mode: "TDD" | "GRILL" | "AUTONOMOUS_DUAL_EVOLVE"`). Regardless of mode, read [`references/background-synthesis-and-onboarding.md`](references/background-synthesis-and-onboarding.md) before starting a paper/project walkthrough, and generate, render, and audit every slide (`slides/slide_XX.html`) **one slide per step** before unlocking the next slide in `slide_manifest.json`.

---

## 1. Two-Level Macro-to-Micro Tri-Mode Architecture (`Step 0.0 Beyond-PDF Background Bridge` + `Stage 0 Global Blueprint` + `TDD / GRILL / AUTONOMOUS_DUAL_EVOLVE`)

### Step 0.0: Beyond-PDF 领域背景主动补齐与零黑话通俗导读（`domain_background_bridge`，所有模式强制前置！）
Raw PDFs write for narrow sub-field insiders and jump straight into obscure molecular/process acronyms (`QFLS`, `PDISNN`, `BCP/Ag`, `SFG`, `Edge-on`, `TTA`). Merely summarizing the PDF leaves users bewildered in `Tutor`, `GRILL`, and the `HTML-PPT` itself. Before any Stage 0 MCQs, Tutor questions, Grill questions, or `storyboard.json` initialization, execute **Role 0 (`BackgroundSynthesizer & AudienceTranslator`)** per [`references/background-synthesis-and-onboarding.md`](references/background-synthesis-and-onboarding.md):
1. **PDF 省略背景缺口诊断 (`pdf_omitted_background_gaps`, $\ge 2$ items)**: Explicitly audit Title + Abstract + Intro ¶1 to identify what foundational device/reaction working principles, physical metrics, and prior-art trade-offs the raw PDF silently omitted.
2. **首轮大白话全景导读 (`outside_pdf_onboarding_primer` — 先给地图，再抛选择题/问题)**:
   - In **Turn 1**, BEFORE asking any blueprint multiple-choice questions or quizzing the user, proactively deliver a 3–5 sentence plain-language world-knowledge primer explaining: (a) what real-world device/system this is and why it matters, (b) how a textbook baseline version works via an intuitive everyday analogy, and (c) where the bottleneck sits that this paper aims to break.
   - **严禁泄露框架内部黑话 (`Zero Internal Framework Codeword Leak`, Gate `D13` & `D16`)**: NEVER utter internal AWF tokens (`V0–V3`, `V3动画`, `Stage k.1/k.2`, `UNBOUNDED_FLOW_DRIVEN`, `JIT_DURING_QA`, `HYBRID_SEED_PLUS_JIT`, `AUTONOMOUS_DUAL_EVOLVE`, `INTENT_MAPPED_AI_RECOMMENDED`, `AI_SEED_PLUS_JIT`, `JIT_DURING_GRILL`, `ai_value_triage`, `gdd_grill_capsule`, `tdd_station_capsule`, `slide_manifest.json`) in user-facing chat, MCQ options, or slide copy! Translate them into natural human expressions (e.g., *"可拖动参数的交互式动态推演图"*, *"不硬限页数，顺着逻辑讲透为止"*, *"先不锁死重头戏，看后面哪块卡壳或感兴趣再当场拆页深挖"*).
   - **首轮「全文干货与水分体检单」剧透 (`ai_value_triage` — AI 先亮底牌，严禁让未读 PDF 的用户盲猜模块)**: Immediately after the 3–5 sentence onboarding primer, give a 3-line plain-language audit so a user who has read **0% of the PDF** instantly knows what is worth their time:
     1. **全篇真王牌（AI 鉴定）** (`core_breakthrough_gem`): Which single counter-intuitive mechanism/design is the paper's true highlight and why;
     2. **前置台阶铺垫** (`foundation_bridge_summary`): What $\ge 3$ outside-PDF background slides we will build first;
     3. **常规套路快进区** (`routine_fast_forward_zone`): Which boilerplate characterization / standard test sections can be compressed into 1 overview slide unless requested otherwise.
3. **4 阶递进背景漏斗与多页视觉铺垫 (`four_rung_funnel` + $\ge 3$ `V2/V3` Opening Slides on Full-Paper Decks)**:
   - **Rung 1 (`rung1_macro_industry_stakes`)**: Macro industry/scientific stakes & incumbent ceiling;
   - **Rung 2 (`rung2_canonical_working_principle` + `visual_schematic_plan`)**: Canonical baseline device/system working principle **before** introducing any paper-specific molecule/recipe, paired with a custom inline `<svg>` cross-section/cycle schematic or interactive model (`V2/V3`, never `V0` bullet walls);
   - **Rung 3 (`rung3_core_jargon_translations`, $\ge 2$ terms)**: Translate every load-bearing jargon term via `{term, plain_analogy, physical_meaning}` (e.g., reservoir water-head drop $\leftrightarrow$ `QFLS`, escalator step mismatch $\leftrightarrow$ electrode `WF`);
   - **Rung 4 (`rung4_prior_art_deadlock`)**: Why mainstream prior-art fixes hit a Whack-a-Mole trade-off deadlock, naturally handing off to the paper's innovation.
   - **双源溯源纪律 (`Dual-Source Provenance`)**: Proactively synthesize world-knowledge tutorial context (`BEYOND_PDF_DOMAIN_KNOWLEDGE`), while keeping all paper-specific experimental numbers and claims strictly anchored to the PDF (`paper_claims_strictly_from_pdf: true`). Full-paper walkthroughs ($\ge 10$ slides) **must** dedicate $\ge 3$ opening `V2/V3` slides (`background_slide_indices`) to Rungs 1–4 instead of cramming background onto a single dense slide.

### Stage 0: Macro-GDD Global Deck Blueprint（全局总纲对焦与自然语言选择题拍板，`global_deck_blueprint`）
After delivering the Step 0.0 plain-language primer, align on the **global architecture** with the human (speaking 100% natural language, zero internal codewords):
1. **Step 0.A — 全篇核心冲突一刀探底 (`macro_thesis_probe`)**:
   - Crystallizes the Bird's-Eye Conflict Formula (`executive_core_conflict`: Bottleneck Ceiling $\to$ Core Physical Knob $\to$ Quantitative Breakthrough) on top of the Step 0.0 primer and aligns with the user's familiarity (`human_baseline_alignment`).
2. **Step 0.B — 全局导演选择题（取消总页数选择题！只问逻辑主线、听讲诉求与动态演示策略，`logical_flow_mcq` + `emphasis_allocation_mcq` + `v3_animation_budget_mcq`）**:
   - **【铁律：彻底取消「页数怎么选」选择题（一律不问、一律不选，严禁固定总页数！）】**:
     - **一律不问、一律不选页数！** 绝对禁止在对话中向用户抛任何关于“总页数怎么选 / 做多少页 / 选紧凑档还是不限档”的选择题（在 `global_deck_blueprint` 中直接省略 `total_slides_mcq`；无论是否读过 PDF，只要提问 `total_slides_mcq`、在选项中偷渡页数选档或预设固定总页数 `planned_total_slides`，Gate `D16` 无条件拦截失败！）。
     - **全篇页数只看逻辑闭环与理解需要**：内部自动采用纯逻辑驱动生长（`slide_count_policy: "UNBOUNDED_FLOW_DRIVEN"`），前置背景该铺 3 页就铺 3 页，核心机理难懂该拆 3 页就拆 3 页（`APPEND_FLOW_SLIDE` / `SPLIT_SLIDE` / `PROMOTE_HEAVY_FOCUS`），常规验证 1 页能讲清就 1 页收工（`COMPRESS_ROUTINE_MODULE`），绝不人为凑页数或硬砍页数！
   - **MCQ 1 (`logical_flow_mcq` — 内容与逻辑演进流程怎么走？首要核心)**: Establishes the ordered causal narrative spine starting with foundational background (`logical_flow_spine`, e.g., `["1. 领域价值与基础器件怎么工作（论文外补齐）", "2. 关键指标通俗拆解与前人方案死结", "3. 本文核心破局旋钮与微观机理", "4. 控制变量实验铁证与边界代价"]`).
   - **MCQ 2 (`emphasis_allocation_mcq` — 重头戏怎么偏重？严禁拿论文陌生模块名考未读 PDF 的用户！)**:
     - **Default Assumption (`user_has_read_pdf: false`)**: Unless the user explicitly says they already read the paper, assume they have **NOT** read the PDF! **NEVER** ask cold catalog questions like *"以下哪些模块需要作为重头戏展开讲？A. [陌生专业模块1] B. [陌生专业模块2]"* (blocked by Gate `D16` `verify_unread_pdf_emphasis_alignment`).
     - Instead, pair `ai_value_triage` with **zero-prerequisite Reader-Intent Lenses or Dynamic JIT Discovery** (recorded internally via `emphasis_policy: "AI_SEED_PLUS_JIT" | "INTENT_MAPPED_AI_RECOMMENDED" | "JIT_DURING_GRILL"`, phrased 100% in plain human language):
       - **A (推荐 · 吃透核心脑洞 + 边问边调)**：AI 主导排戏份——重点把上面鉴定的「核心破局机理」掰碎讲透，常规表征一页带过；推进中哪块卡壳或觉得有意思，当场加页深挖；
       - **B (借鉴实验配方与工艺防坑)**：重点拆解分子/结构怎么设计、对照实验怎么搭、有哪些复现暗坑；
       - **C (组会汇报 / 审稿挑刺视角)**：重点深挖控制变量铁证链、替代解释排除与性能边界代价；
       - **D (完全边走边定)**：现在先不锁死重头戏，顺着主线边聊边看，遇到卡壳或来劲的地方再当场展开。
   - **MCQ 3 (`v3_animation_budget_mcq` — 哪些地方做可交互动态演示？默认推荐边推进边拍板）**: Recorded internally as `"JIT_DURING_QA"` (`min_v3_slides_quota >= 1`), `"HYBRID_SEED_PLUS_JIT"`, or `"UPFRONT_LOCKED"`—always phrased to the user in plain language (*"讲到哪一页觉得静态图不够直观，我们当场加上可拖动参数的动态演示"*).
3. **Step 0.C — 分级洋葱剥皮演进流程 (`onion_peeling_capsule` + `--peel-onion-trunk`)**:
   - **Layer 0 (最外层粗框架 `layer0_macro_frame`)**: Locks the 3–5 coarsest macro trunks (`Trunk_1` = Beyond-PDF Foundation & Bottleneck Onboarding, `Trunk_2..M` start as `"UNPEELED"`).
   - **Layer 1..K (`peel_onion_trunk_subframe` + 先给微缩剧透再剥皮 `trunk_context_preview`)**: When peeling open the active trunk (`--peel-onion-trunk`), **always deliver a plain-language `trunk_context_preview` first** (*"地基打完了！接下来这一块作者干了两件事：①... ②... 你想两块都细盘，还是只抓①、把②浓缩成一页结论？"*) before asking `trunk_subframe_mcq`!
   - **Leaf Layer**: Single-Slide Q&A + Visual Layout MCQ $\to$ 1-Slide HTML generation & 18-gate `DesignAG` audit. Stage 4 assembly verifies zero `"UNPEELED"` trunks remain.
4. **Step 0.D — 全域输入-背景补齐-洋葱理解-跨载体输出统一控制总线 (`universal_io_bus_capsule` + `--record-cross-artifact-unit`)**:
   - **Role 0 (`BackgroundSynthesizer & AudienceTranslator`, `domain_background_bridge` / `domain_background_ledger`)**: Synthesizes outside-PDF world knowledge (`BEYOND_PDF_DOMAIN_KNOWLEDGE`), physical analogies, and custom SVG/interactive visual schematics so non-insiders never get lost.
   - **Role 1 (`EvidenceIngest`, `evidence_ingest_ledger`)**: Anchors paper-specific claims (`claim_id`, `quantitative_value`, `source_artifact_or_figure_ref`) strictly to the PDF/logs (`PDF_PRIMARY_EVIDENCE`).
   - **Role 2 (`DevilReviewer`, `devil_reviewer_capsule`)**: Pairs skeptical alternative hypotheses (`alternative_hypothesis_challenge`) with negative-control rebuttals (`control_evidence_rebuttal`).
   - **Role 3 (`OmniArtifactHub`, `output_artifact_targets`)**: Drives `HTML_PPT` (`skill.html-ppt@1.0.0-rc.19`), `SCI_WORD` (`skill.edit-scientific-article@1.0.0-rc.10` + `skill.build-scientific-docx@1.0.0-rc.12`), and `FIG_PPTX` (`skill.build-editable-figure-pptx@1.0.0-rc.2`) from one shared cognitive tree.

### Mode 1: `TDD` — Tutor-Driven Design（以教代建模式，`tdd_mode: true`）
- **Workflow**: `1 Tutor Station == 1 TDD Cognitive Capsule == 1 Slide`.
- **Foundation-First Onboarding Rule**: On opening background stations (`is_background_slide: true` / `is_background_station: true`), proactively teach the baseline device/system working principle and plain-language analogies first, recording `beyond_pdf_background_synthesis` in `tdd_station_capsule` (enforced by Gate `D16`). **Never** quiz the user on paper-specific recipe pairs (`BCP/Ag vs SnO2/Bi`, `PDISNN vs PDI2SNN`) before establishing how the standard system works!
- At each station `Station_1.k`, run the Socratic/Wittgenstein dialogue, record `tdd_station_capsule` via `--record-tdd-capsule` (`core_blindspot_or_conflict`, `wittgenstein_ladder`, `human_orthogonal_insight`, `visual_modality` $\in \{\text{V2}, \text{V3}\}$, `hidden_teleprompter_qa`), and build + audit `slides/slide_{k:02d}.html`.

### Mode 2: `GRILL` — Dual-Stage Grill-Driven Design（先导读搭梯再烤问 + PPT视觉选择题，`grill_mode: true`）
- **Workflow**: **Briefing Anchor (when needed) + 3-Part Mechanism Grill $\to$ Teach-on-Miss $\to$ Isomorphic Re-Grill $\to$ Bottleneck-to-Slide Mapping + Slide Design MCQ (A/B/C) $\to$ 1 Slide Build & Audit**.
- **Briefing-First Law (严禁真空冷突袭烤问！)**:
  - Because raw PDFs omit background, **never ambush the user cold with unexplained sub-domain acronyms**!
  - On opening foundation/background stations, select `question_archetype: "FOUNDATION_INTUITION_BUILD"` (or `requires_beyond_pdf_background: true`), **first provide a 3–5 sentence self-contained `background_briefing_anchor`** explaining the canonical setup and plain-language terms, and *then* ask a deductive first-principles 3-part question that any attentive reader can reason out from that briefing!
- **Stage 1 — 科学机理三段式烤问与变式复烤（决定本页“讲什么/防什么”）：**
  - Select `question_archetype` $\in$ `{"FOUNDATION_INTUITION_BUILD", "PARADOX_BOTTLENECK", "KNOB_TURNING_PREDICTION", "TRADEOFF_BREAKDOWN", "ISOMORPHIC_REGRILL"}`.
  - Pose `grill_question`: `【给定锚点】 + 【冲突情境】 + 【一刀见血追问】` (zero leaked framework codewords!).
  - On miss/uncertainty, run **Teach-on-Miss** (Wittgenstein ladder) + **Isomorphic Re-Grill** (`teaching_and_regrill_closure`; rubber-stamp *"听懂了吗/明白了吗"* is blocked by Gate `D16`).
  - **Grill 反应实时驱动重头戏伸缩 (`JIT Emphasis Sensor`)**: Treat user responses in `GRILL` as the live focus probe—if a station triggers `Teach-on-Miss` or follow-up curiosity, promote it dynamically via `--mutate-storyboard` (`action: "PROMOTE_HEAVY_FOCUS"`, `trigger_source: "GRILL_MISS_BOTTLENECK"` / `"USER_CURIOSITY_SPIKE"`) to split/add a deep-dive slide; if the user nails a routine section effortlessly, compress it (`action: "COMPRESS_ROUTINE_MODULE"`).
- **Stage 2 — 认知断层映射与 PPT 视觉/排版选择题拍板（决定本页“怎么画/怎么排”）：**
  - Map the grilled insight to the slide's headline assertion & visual centerpiece (`bottleneck_to_slide_mapping`) and `S`-key notes (`hidden_teleprompter_qa`), ask a plain-language **A/B/C Slide Design MCQ** (`slide_design_mcq`), record via `--record-grill-capsule`, and build `slides/slide_{k:02d}.html`.

### Mode 3: `AUTONOMOUS_DUAL_EVOLVE` — Head-Down Autonomous Draft + Post-Review Dual-Evolution（闷头直出 + 审阅双升级模式，`autonomous_dual_evolve_mode: true`）
- **Phase A (Head-Down Autonomous 1-Slide-Per-Step Build)**:
  - Populate `domain_background_bridge` inside `storyboard.json` first (allocating $\ge 3$ custom-SVG / interactive `V2/V3` opening background slides across Rungs 1–4 for full-paper decks), then loop $k = 1 \dots N$ with `require_human_approval: false`, generating and auditing **strictly 1 slide per step** and assembling `deck.html`.
- **Phase B (Human Review $\to$ Dual-Evolution of PPT + `AWF HTML-PPT` / `DesignAG`)**:
  - Running `--apply-feedback-dual-upgrade feedback_payload.json` patches and re-audits the target slide(s) while recording `target_gate_or_rule_id` and `negative_canary_fixture` when `is_generalizable_to_awf: true`.

---

## 2. Non-Negotiable Anti-Goodhart Laws

1. **Strictly 1 Slide Per Step (`max_slides_generated_per_step == 1`)**:
   - Never generate a monolithic multi-slide HTML file in one shot, and never batch 2 or more slides in a single step.
   - Each slide lives in its own isolated module (`slides/slide_01.html`, `slides/slide_02.html`, ...) and is individually audited via [`scripts/audit_single_slide_step.py`](scripts/audit_single_slide_step.py) against `skill.design-anti-goodhart@1.0.0-rc.17` (`AWF DesignAG`).
2. **1-Hop Slide Topological Lock (`unverified_slide_hop_distance == 1`)**:
   - Tracked in `slide_manifest.json`. At initialization, only `slide_01` (`Station_1.1`) is `"UNLOCKED"`; `slide_02..N` are `"LOCKED"`.
   - `slide_{k+1}` is unlocked **if and only if** `slide_k` has passed all per-slide DesignAG gates (`D1`–`D12`, `D15`, `D16`) with zero Redlines (`R1`–`R7`) and its SHA-256 receipt is recorded as `"status": "PASS"` in `slide_manifest.json`.
3. **Human-in-the-Loop Sign-off Gate (`require_human_approval: true`)**:
   - Optional in Mode 1 (`TDD`) and Mode 2 (`GRILL`); disabled (`false`) during Phase A of Mode 3 (`AUTONOMOUS_DUAL_EVOLVE`).
4. **Multiplicative Visual Modality Cap ($A_i = w_i \times C_{\text{clarity}} \times V_{\text{visual}}$)**:
   - Pure text (`V0 = 0.30`) is mathematically capped at 30% of the score. Mechanism, background, and data slides must use clean cropped paper figures / accurate custom inline SVG diagrams (`V2 = 0.80`) or physics-coupled interactive widgets / multi-step SVG animations (`V3 = 1.00`).
5. **Beyond-PDF 4-Rung Background Runway & Zero Framework Meta-Jargon Leak (`D13`, `D16`, `D3`)**:
   - Full-paper decks ($\ge 10$ slides) without `domain_background_bridge` or with $< 3$ `V2/V3` opening background slides fail `--init-storyboard` and `--assemble-deck`.
   - Background `TDD` stations without `beyond_pdf_background_synthesis`, background `GRILL` stations without `background_briefing_anchor`, and user/slide copy leaking internal AWF codewords (`V0–V3`, `Stage k.2`, `UNBOUNDED_FLOW_DRIVEN`, `JIT_DURING_QA`) fail automatically.
6. **Inline `<svg>` Minimum Font Size $\ge 18\text{ px}$, Single-Slide Character Cap ($\le 650$), Zero SVG-to-SideCard Echo & Viewport Auto-Fit (`D6` HTML-Level Guards)**:
   - **内联 `<svg>` 最小字号硬门槛 (`MIN_INLINE_SVG_FONT_PX = 18.0`)**: Every `<text>` / `<tspan>` inside an inline `<svg>` MUST explicitly declare and render at an effective font size $\ge 18.0\text{ px}$ (accounting for `viewBox` coordinate scaling; omitting `font-size` so the browser falls back to `16px` or shrinking `18px` via oversized `viewBox="0 0 3840 ..."` fails Gate `D6`).
   - **单页可见字数与内联 `<svg>` 标签上限 (`MAX_VISIBLE_CHARS_PER_SLIDE = 650`, `MAX_INLINE_SVG_SUBSTANTIVE_LABELS = 22` / `30` total)**: Never cram 1,000+ visible characters or pack 3+ sub-diagrams (`30+` `<text>` labels) into one slide's `<svg>`, and never pair a self-labeled `<svg>` ($\ge 12$ labels) with $>220$ chars of non-SVG body/card prose—split into multiple clean slides via `--mutate-storyboard` (`SPLIT_SLIDE`) instead!
   - Never stack $\ge 3$ verbose `<article>` side-cards repeating numbers or CJK phrases already labeled inside an `<svg>` diagram (`SVG_SideCard_Redundant_Echo_Guard`); expand the diagram cleanly across the canvas instead.
   - Every fixed-pixel slide (`1600×900` or `1920×1080`) **must** embed standalone centered viewport auto-fit (`html, body { margin: 0; width: 100%; height: 100%; overflow: hidden; }` + `position: fixed; left: 50%; top: 50%; transform: translate(-50%, -50%) scale(...)` scaled via `Math.min(window.innerWidth / W, window.innerHeight / H) * 0.96`) so opening any `slide_XX.html` or `deck.html` on 125%/150% DPI laptop screens fits 100% inside the viewport with zero scrollbars and zero manual browser zooming (`Fixed_Canvas_Viewport_AutoFit_Guard`).

---

## 3. CLI Commands (`scripts/audit_single_slide_step.py`)

```bash
# Run Tri-Mode self-test (verifies all 13 invariants including Beyond-PDF 4-Rung Background Bridge)
python scripts/audit_single_slide_step.py --self-test

# Initialize storyboard manifest (requires domain_background_bridge with >=3 V2/V3 background slides on >=10-slide decks)
python scripts/audit_single_slide_step.py --init-storyboard storyboard.json --manifest slide_manifest.json

# Record or update Role 0 Beyond-PDF 4-Rung Domain Background Bridge on an existing manifest
python scripts/audit_single_slide_step.py --record-background-bridge background_bridge.json --manifest slide_manifest.json

# Mode 1 (TDD): Record Tutor Station cognitive capsule for slide K (requires beyond_pdf_background_synthesis on background slides)
python scripts/audit_single_slide_step.py --record-tdd-capsule tdd_capsule_01.json --slide-index 1 --manifest slide_manifest.json

# Mode 2 (GRILL): Record Dual-Stage Grill capsule for slide K (requires background_briefing_anchor on foundation/background slides)
python scripts/audit_single_slide_step.py --record-grill-capsule grill_capsule_01.json --slide-index 1 --manifest slide_manifest.json

# Mode 3 (AUTONOMOUS_DUAL_EVOLVE): Apply human feedback to patch PPT slide AND record AWF upgrade receipt
python scripts/audit_single_slide_step.py --apply-feedback-dual-upgrade dual_upgrade_payload.json --manifest slide_manifest.json

# Assemble all PASS slides into final deck.html
python scripts/audit_single_slide_step.py --assemble-deck --manifest slide_manifest.json --output deck.html
```

---

## 4. Preserved References & Templates

- Beyond-PDF 4-rung background synthesis, visual SVG blueprints & zero-jargon onboarding playbook: [background-synthesis-and-onboarding.md](references/background-synthesis-and-onboarding.md)
- Concrete system semantics & title rules: [content-and-evidence.md](references/content-and-evidence.md)
- Visual & browser interaction checklist: [visual-and-interaction-review.md](references/visual-and-interaction-review.md)
- Base 16:9 slide scaffold: [slide-template.html](assets/slide-template.html)


## Content contract before visual scoring

Use concrete scientific titles: each title names a concrete object, phenomenon, relationship, or question and is natural enough to read aloud. Keep the lesson workflow in presenter notes or controls. Before accepting an algorithm or optimization slide, apply the concrete-system semantics contract in `references/content-and-evidence.md`: identify the physical candidate, inputs, objectives and directions, operation, output, and downstream decision. Verify every illustrated dominance relationship against its coordinates. A layout score cannot substitute for these content checks.

## D17/D18 evidence hardening contract (2026-11-16)

Resolved composition: Tutor Skill/Workflow `1.0.0-rc.30`, DesignAG Skill/Workflow
`1.0.0-rc.17`, HTML-PPT Skill `1.0.0-rc.19` / Workflow `1.0.0-rc.16`,
Guard `3.7.0-rc.7`, repository verifier `1.0.0-rc.2`.

1. D17 no longer invents missing grades. All 15 knowledge criteria, all B-E
   grades, five dimensions, readability penalties and R1-R7 assessments are
   explicit. Weights and required modalities are fixed to the co-located rubric;
   NaN/Inf, booleans as scores, negative counts, duplicate criteria and out-of-range
   values fail. The threshold cannot be below 80; final HTML-PPT requires 85.
   Any redline prevents acceptance even if the numerical score remains high.
2. D17/D18 require separately authorized Ed25519 renderer and reviewer receipts.
   The runner supplies its public-key trust policy, expected artifact paths and
   run ID outside the user bundle. There are NO default trusted production keys.
   Never auto-trust a key embedded in a submission or copy test authorities into
   production. A trusted runner and isolated signer keys are the security boundary.
3. Receipts bind the exact HTML and PNG bytes, capture profile, static slide
   selector/index/state, complete frame coverage, complete rubric payload and
   31 criterion observations. Missing/corrupt/non-PNG/wrong-size images, altered
   source, copied PNGs across frames, stale run IDs, unsigned edits, unknown keys,
   same renderer/reviewer key and partial review coverage do not pass.
4. Supported profile is `offline-static-slide-initial-v1`: normalized explicit
   html/head/body; exact offline CSP from `design_capture_profile.CSP_META` as a
   direct head child before active content; all resources embedded as data/inline
   content; no executable scripts or event handlers. Duplicate attributes and
   non-void self-closing tags are rejected (use explicit SVG closing tags too).
   Static `.slide` elements are
   counted from actual HTML; each initial frame must be captured. Without `.slide`,
   the single `html` frame is used. Identical PNGs across frames require additional
   review. JavaScript-generated views and interaction state coverage are unsupported
   by this profile and remain REVIEW_REQUIRED, not automatically accepted.
5. Structural assembly is a draft milestone. HTML-PPT's per-slide path runs ten
   applicable checks; `assemble_verified_deck` reports `presentation_acceptance:
   REVIEW_REQUIRED`. Final acceptance uses `--verify-deck-evidence` and all 18 gates.
   Direct `run_all_18_design_gates` also rejects bundle HTML that differs from the
   actual reviewed artifact. No alternate public entry point may bypass binding.

### Trust and domain limits

Signatures prove who attested to which bytes; they do not prove a renderer executed
correctly, an auditor truly looked, scientific truth, or independence of judgment.
The renderer must actually capture each declared frame; the reviewer must inspect
the captures and record observations. D1-D16 still accept some caller-supplied
metadata. This release tests force-PASS mutations for D17/D18, not all 18 gates.
The fixed knowledge rubric is the bundled optoelectronic rubric; adapting it to
another domain requires an explicitly reviewed rubric successor, not caller-chosen
weights. Guard scientific validation remains a separate requirement.

### API and CLI

`run_all_18_design_gates(bundle, evidence_context=context)` accepts a context with
`manifest_path`, `trust_policy_path`, `expected_artifacts` (artifact ID to HTML path)
and `run_id`. The signed manifest has `render` and `review` envelopes, each with
`payload` and a base64 Ed25519 `signature` over UTF-8 canonical JSON (sorted keys,
compact separators, ensure_ascii=False, allow_nan=False). The policy schema is
`{"schema_version":1,"renderers":{"ID":"BASE64_RAW_PUBLIC_KEY"},"reviewers":{"ID":"BASE64_RAW_PUBLIC_KEY"}}`.
Keys identify separately authorized roles. Signature generation belongs to the
trusted renderer/reviewer processes, never to the untrusted deck producer.

The renderer payload contains schema_version, run_id, renderer_id, renderer,
capture_profile, and artifacts. Each artifact includes artifact_id, html_path,
html_sha256, png_path, png_sha256, width, height, resources=[], and
frame={selector,index,state}. Reviewer payload contains schema_version, run_id,
reviewer_id, render_payload_sha256, score_payload_sha256, reviewed_artifact_ids,
verdict, findings, and criterion_evidence. Each criterion observation names its
artifact_ids and a nonempty observation. All artifacts must be cited somewhere.

```text
python -B scripts/awf_design_anti_goodhart_gates.py --self-test
python -B scripts/awf_design_anti_goodhart_gates.py --audit-self
python -B design_tests/test_evidence.py
```

For final HTML-PPT acceptance, invoke its pinned script:

```text
python -B scripts/audit_single_slide_step.py --verify-deck-evidence deck.html --review-bundle bundle.json --evidence-manifest evidence.json --trust-policy trusted-public-keys.json --review-run-id RUN_ID --review-targets targets.json
```

The trusted runner must own the last three arguments and target mapping. Passing
attacker-chosen values there invalidates the trust boundary. See DesignAG
`references/evidence-contract.md` and source modules for the exact schema. Synthetic
fixtures create ephemeral in-memory keys and explicitly do not grant production trust.

All engineering scripts for this coordinated release are physically co-located at
`workflows/design-anti-goodhart/releases/1.0.0-rc.17/source/`; include that directory
and locked component trees when packaging. Current releases remain immutable.
