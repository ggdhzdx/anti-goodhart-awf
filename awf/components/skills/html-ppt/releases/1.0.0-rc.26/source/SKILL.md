---
name: html-ppt
description: Build, audit, and evolve 16:9 scientific interactive HTML presentations (AWF HTML-PPT / SciSlide) under a Two-Level Macro-to-Micro Tri-Mode Architecture with 2x Large-Typography & <=260 Visible-Char Low-Density Budget (inline SVG & visible HTML >=32px, 1920x1080 card body >=42px, slide title >=56px, 1 paragraph per card), Universal 5-Scale Physical-Entity Visual Fidelity (RDKit ACS vector / 2.5D shading / 4-Axis Orthogonal Image Exploration + Critique-Guided Gen-1+ Evolution), Two-Stage Text-Masked Blind Object Recognition (`D5` & `D18`), Lossless Multi-Slide Split (`SPLIT_SLIDE` + `.topo-breadcrumb`) & Clickable Detail Popovers (`CLICKABLE_POPOVER` + `.detail-trigger[data-detail-id]` backed by verified `<template>` modals, audited via `lossless_split_and_popover_ledger`), Mandatory Beyond-PDF 4-Rung Domain Background Synthesis (`domain_background_bridge` + HTML-level Pre-Background Paper-Recipe Leak Guard & Opening Rung-1 Macro-Stakes Grounding in `D13`), Unread-PDF AI Value-vs-Routine Triage (`ai_value_triage`) + Reader-Intent / `JIT_DURING_GRILL` Dynamic Emphasis, Zero Slide-Count MCQ Law, Intra-Slide Semantic Coherence & De-Ballasting (`intra_slide_semantic_tree`), Anti-Collusion Zero-Context Blind Reader & Outsider Macro-Onboarding Verification (`D18` + `--verify-blind-reader`), Zero AI Self-Scaffolding Slide Meta-Labels, strictly 1-Slide-Per-Step (`max_slides_generated_per_step == 1`), and 1-Hop Slide Topological Lock (`slide_manifest.json`), gated by `skill.design-anti-goodhart@1.0.0-rc.24` (AWF DesignAG) and `skill.anti-goodhart-verification@3.7.0-rc.7` (AWF Guard). Use whenever creating, revising, or auditing HTML slide decks, scientific paper walkthroughs, or teaching presentations.
---

# AWF HTML-PPT V3 (`skill.html-ppt@1.0.0-rc.26` — 5-Scale Physical-Entity Visual Fidelity + 4-Axis Orthogonal Image Exploration & Gen-1+ Evolution + Two-Stage Text-Masked Blind Object Recognition + 2x Large Typography (>=32px SVG/HTML, >=42px HD Body, >=56px Title) & <=260-Char Low-Density Canvas + Lossless Multi-Slide Split (`SPLIT_SLIDE` + `.topo-breadcrumb`) & Clickable Detail Popovers (`CLICKABLE_POPOVER` + `.detail-trigger`) + Pre-Background Recipe Leak & Rung-1 HTML Grounding (`D13`) + Outsider Blind-Reader Onboarding (`D18`) + Two-Level Macro-to-Micro Tri-Mode Engine, Strictly 1-Slide-Per-Step & `AWF DesignAG` 18-Gate Enforcement)

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
   - **Role 3 (`OmniArtifactHub`, `output_artifact_targets`)**: Drives `HTML_PPT` (`skill.html-ppt@1.0.0-rc.24`), `SCI_WORD` (`skill.edit-scientific-article@1.0.0-rc.10` + `skill.build-scientific-docx@1.0.0-rc.12`), and `FIG_PPTX` (`skill.build-editable-figure-pptx@1.0.0-rc.2`) from one shared cognitive tree.

### Mode 1: `TDD` — Tutor-Driven Design（以教代建模式，`tdd_mode: true`）
- **Workflow**: `1 Tutor Station == 1 TDD Cognitive Capsule == 1 Slide`.
- **Canvas-vs-Dialogue Decoupling Law (`投屏极简 ≠ 课堂降智`)**: Never bleed the slide canvas `<=260`-char density cap backward into the Tutor dialogue! In conversation, deliver full 3-step **Wittgenstein's Ladder (`Bridge -> Deconstruct [explicitly tear down macroscopic analogy illusions] -> Replace [exact equation/operator]`)**, 7-element methodological anatomy, visual cloze `[ ? ]`, and rigorous `Teach-on-Miss + Isomorphic Re-Grill` (`design_tutor_pedagogy_guard.py`), while compressing the visible slide canvas cleanly via split breadcrumbs + clickable `<template>` popovers.
- **Foundation-First Onboarding Rule**: On opening background stations (`is_background_slide: true` / `is_background_station: true`), proactively teach the baseline device/system working principle and plain-language analogies first (followed immediately by microscopic deconstruction and exact physical framing), recording `beyond_pdf_background_synthesis` in `tdd_station_capsule` (enforced by Gate `D16`). **Never** quiz the user on paper-specific recipe pairs (`BCP/Ag vs SnO2/Bi`, `PDISNN vs PDI2SNN`) before establishing how the standard system works!
- At each station `Station_1.k`, run the Socratic/Wittgenstein dialogue, record `tdd_station_capsule` via `--record-tdd-capsule` (`core_blindspot_or_conflict`, structured 3-step `wittgenstein_ladder`, optional/required `seven_element_anatomy`, `teach_on_miss_and_regrill_closure` when uncertain, `human_orthogonal_insight`, `visual_modality` $\in \{\text{V2}, \text{V3}\}$, `hidden_teleprompter_qa`), and build + audit `slides/slide_{k:02d}.html`.

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
   - Each slide lives in its own isolated module (`slides/slide_01.html`, `slides/slide_02.html`, ...) and is individually audited via [`scripts/audit_single_slide_step.py`](scripts/audit_single_slide_step.py) against `skill.design-anti-goodhart@1.0.0-rc.24` (`AWF DesignAG`).
2. **1-Hop Slide Topological Lock (`unverified_slide_hop_distance == 1`)**:
   - Tracked in `slide_manifest.json`. At initialization, only `slide_01` (`Station_1.1`) is `"UNLOCKED"`; `slide_02..N` are `"LOCKED"`.
   - `slide_{k+1}` is unlocked **if and only if** `slide_k` has passed all per-slide DesignAG gates (`D1`–`D12`, `D15`, `D16`) with zero Redlines (`R1`–`R7`) and its SHA-256 receipt is recorded as `"status": "PASS"` in `slide_manifest.json`.
3. **Human-in-the-Loop Sign-off Gate (`require_human_approval: true`)**:
   - Optional in Mode 1 (`TDD`) and Mode 2 (`GRILL`); disabled (`false`) during Phase A of Mode 3 (`AUTONOMOUS_DUAL_EVOLVE`).
4. **Multiplicative Visual Modality Cap ($A_i = w_i \times C_{\text{clarity}} \times V_{\text{visual}}$)**:
   - Pure text (`V0 = 0.30`) is mathematically capped at 30% of the score. Mechanism, background, and data slides must use clean cropped paper figures / accurate custom inline SVG diagrams (`V2 = 0.80`) or physics-coupled interactive widgets / multi-step SVG animations (`V3 = 1.00`).
5. **Beyond-PDF 4-Rung Background Runway, Pre-Background Recipe Leak Guard, Opening Rung-1 HTML Grounding, Zero Framework Meta-Jargon Leak & Zero AI Self-Scaffolding Slide Labels (`D13`, `D16`, `D3`)**:
   - Full-paper decks ($\ge 10$ slides) without `domain_background_bridge` or with $< 3$ `V2/V3` opening background slides fail `--init-storyboard` and `--assemble-deck`.
   - **HTML-Level Pre-Background Recipe Leak & Opening Rung-1 Grounding (`audit_slide_html_background_onboarding_fidelity`, Gate `D13`)**: Pre-background cover slides (`pos < min(bg_indices)`) and `Rung 1–2` background slides are deterministically scanned against `extract_paper_specific_recipe_tokens(domain_background_bridge, universal_io_bus_capsule)` (`3-PMPCl`, `4-PMPCl`, `PDISNN`, etc.) and premature substituent ring anatomy (`3-N吡啶`, `哌嗪环`, `ΔG = ΔH`). Furthermore, the opening `background_rung == 1` slide MUST ground `four_rung_funnel.rung1_macro_industry_stakes` in visible HTML ($\ge 1$ shared substantive domain anchor) and MUST NOT jump prematurely into $\ge 2$ narrow sub-domain band/quantum formalism terms (`间接带隙`, `直接带隙`, `S–Q 极限`) before establishing real-world industry & manufacturing stakes!
   - Background `TDD` stations without `beyond_pdf_background_synthesis`, background `GRILL` stations without `background_briefing_anchor`, and user/slide copy leaking internal AWF codewords (`V0–V3`, `Stage k.2`, `UNBOUNDED_FLOW_DRIVEN`, `JIT_DURING_QA`) fail automatically.
   - **严禁在可见页面印制「AI 给自己/评分器看的自注提纲标签」(`Zero AI Self-Scaffolding Slide Labels`, Gate `D3` `AI_SELF_SCAFFOLDING_SLIDE_PATTERNS`)**: NEVER print rubric/workflow meta-labels such as *“背景导读第 1 阶 · 宏观产业痛点与传统单晶衍射天花板”*, *“领域背景铺垫 (1/4)”*, *“背景知识补齐（论文外...）· Rung 1”*, *“基础工作机理示意图 · 领域通用物理模型”*, *“伏笔：...”*, *“伏笔回收 (I)”*, *“回收第 07 页伏笔”*, *“交互实验 #3”*, or *“具体系统目标权衡与下游实验决策”* in `<header>`, `.kicker`, `.tag-pill`, `<footer>`, or body text! Write 100% calm, natural academic expressions meant for a human audience, keeping 4-rung staging and narrative foreshadowing implicit in the science or inside hidden `<aside class="notes" hidden>`.
6. **Ultra-Clean $\le 260$-Char Canvas Budget, 2x Large Typography (`>=32px` Floor / `>=42px` HD Card Body / `56–64px` Title), Lossless Clickable Detail Popovers & Topological Multi-Slide Split (`D4`, `D6`, `D8`, `D16` Guards)**:
   - **内联 `<svg>` 与全部可见 HTML 元素翻倍字号门槛 (`MIN_INLINE_SVG_FONT_PX = 32.0`, `MIN_VISIBLE_HTML_FONT_PX = 32.0`)**: Every `<text>` / `<tspan>` inside `<svg>` AND every visible HTML CSS rule / inline `style="font-size:..."` (including topological breadcrumbs, badges, buttons, captions, footers, and table cells) MUST be **$\ge 32.0\text{ px}$** (sub-`32px` visible text fails Gate `D6`).
   - **`1920×1080` 大字版卡片正文 $\ge 42\text{ px}$ 与单行精炼主标题 `56–64 px` (`MIN_HD_CARD_BODY_FONT_PX = 42.0`, `MIN_HD_SLIDE_TITLE_FONT_PX = 56.0`)**: On `1920×1080` HD canvases, body/card paragraphs `<p>` and list items `<li>` MUST be **$\ge 42.0\text{ px}$** ($\ge 36.0\text{ px}$ on `1600×900`), and `.slide-title` / `h1` MUST be **$\ge 56.0\text{ px}$** (`56–64 px` recommended). Each visible card may contain at most **1** concise `<p>` statement (`MAX_VISIBLE_PARAGRAPHS_PER_CARD = 1`), and `justify-content: space-between` on pure-text cards remains strictly forbidden.
   - **单页可见字符硬砍 60% 至 $\le 260$ 字 + 零信息损失双通道分流 (`MAX_VISIBLE_CHARS_PER_SLIDE = 260`, `MAX_INLINE_SVG_SUBSTANTIVE_LABELS = 10` / `14` total, `lossless_split_and_popover_ledger`)**:
     - **严禁靠删减关键数据/对照实验来凑低字数！** Every quantitative condition, supplementary control proof (`Suppl. Fig.`), formula derivation, and full acronym definition MUST be preserved losslessly via two coordinated channels audited by `design_lossless_popover_and_split.py`:
       1. **主干多子图/多步骤强制拆页 + 顶部拓扑面包屑 (`SPLIT_SLIDE` + `.topo-breadcrumb` / `topo_node_id`)**: Whenever an argument spans $\ge 2$ sub-figures (e.g., `Fig. 1a` vs `Fig. 1b`, `Fig. 1c` vs `Fig. 1d`, `Fig. 3d` vs `Fig. 3e`, `Fig. 4b` vs `Fig. 4c`) or $\ge 2$ causal hops, split them into sequential single-focus slides (`1 图 1 跃迁 1 页`) with a persistent visible `.topo-breadcrumb` (`主线③ 动力学铁证 ▸ 3.2 皮秒瞬态吸收`) so logical topology stays 100% transparent across 28–40+ slides;
       2. **细节参数与审稿铁证进可点击详情弹窗 (`CLICKABLE_POPOVER` + `.detail-trigger[data-detail-id]` + `<template data-detail-id>`)**: Keep only the core causal claim and breakthrough numbers on the `42px` main canvas, while placing experimental recipes, control-experiment rebuttals, derivations, and full acronym definitions (`defined_terms_popover`) behind prominent `>= 32px` clickable `.detail-trigger` / `.term-chip` buttons backed by verified `<template data-detail-id="...">` or modal payloads (`>= 20` chars; dangling triggers and `DROPPED`/`NOTES_ONLY` ledger items fail `D6`/`D16`!).
   - Every fixed-pixel slide (`1600×900` or `1920×1080`) **must** embed standalone centered viewport auto-fit (`html, body { margin: 0; width: 100%; height: 100%; overflow: hidden; }` + `position: fixed; left: 50%; top: 50%; transform: translate(-50%, -50%) scale(...)` scaled via `Math.min(window.innerWidth / W, window.innerHeight / H)`) so opening any `slide_XX.html` or `deck.html` on 125%/150% DPI laptop screens fits 100% inside the viewport with zero scrollbars (`Fixed_Canvas_Viewport_AutoFit_Guard`).
7. **Intra-Slide Semantic Coherence, Zero Bottom-Ballast Strips & Anti-Collusion Blind Reader Reconstruction (`D3`, `D4`, `D6`, `D8`, `D16`, `D18` + `--verify-blind-reader`)**:
   - **单层全高主视觉优先 & 严打「页底三小格配重砖 / 迷你名词栏」(`De-Ballasting Law`)**: Prefer single-tier full-height visuals (`height: 740–820px` full-canvas schematics or full-height left-right deep-coupled splits) that naturally satisfy `D8` center-of-mass without bolting filler boxes underneath. **NEVER** dump 3 bare noun-label cards at the bottom of a slide (`电子密度 Q 峰` / `热振动椭球 ADP` / `精修残差因子 R1`) to game `D4`/`D8`! Two-tier `top-visual + bottom-grid` slides are capped at **$\le 30\%$** of the deck (`MAX_TWO_TIER_BOTTOM_GRID_RATIO = 0.30`), and any secondary block MUST declare its `intra_slide_semantic_tree` (`parent_anchor_target`, `relation_type`, `on_canvas_bridge_marker`), render an explicit `.semantic-bridge` / step-callout badge (`④-1`), and use **verb-driven causal/action card headers** (`D3`/`D4`/`D6`/`D16`). Unrelated or loosely related points MUST be split into a dedicated next slide or removed.
   - **反买通共谋「零上下文盲读复述与门外汉宏观背景审稿」(`Anti-Collusion Zero-Context Blind Reader & Outsider Onboarding`, Gate `D18` + `--verify-blind-reader`)**: Rendered `1920×1080` PNGs must be audited by a read-only Blind Reader subagent (`reviewer_isolation_mode: "READONLY_PNG_BLIND_SUBAGENT"`, `saw_source_pdf: false`, `saw_storyboard_json: false`, `saw_speaker_notes: false`) using a neutral zero-hint prompt (`blind_prompt_sent` is deterministically scanned against coaching/pleading phrases and leaked `core_claim`/`parent_anchor_target` answers, while slide HTML is scanned against reviewer-bribery tokens). Instead of rubber-stamping `"PASS"`, the Blind Reader must extract `reconstructed_claim`, `reconstructed_block_links` (`visible_bridge_evidence != "UNANCHORED_GUESS"`), `ambiguous_or_dangling_elements == []`, and—on background-bridged decks—explicitly attest `opening_macro_background_established: true` + `outsider_onboarding_gaps: []` on opening slides with zero premature paper-recipe tokens (`3-PMPCl`, etc.) reconstructed on pre-background / Rung 1–2 slides!

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

## D17/D18 evidence hardening contract (2026-11-23)

Resolved composition: Tutor Skill/Workflow `1.0.0-rc.37`, DesignAG Skill/Workflow
`1.0.0-rc.24`, HTML-PPT Skill `1.0.0-rc.26` / Workflow `1.0.0-rc.23`,
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
`workflows/design-anti-goodhart/releases/1.0.0-rc.24/source/`; include that directory
and locked component trees when packaging. Current releases remain immutable.
CLI also exposes `--verify-image-tournament <ledger.json> --check-disk-pixels` and
`--verify-blind-object-recognition <obj_audit.json>`.
