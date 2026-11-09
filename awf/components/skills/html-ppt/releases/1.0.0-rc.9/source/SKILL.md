---
name: html-ppt
description: Build, audit, and evolve 16:9 scientific interactive HTML presentations (AWF HTML-PPT / SciSlide) under a Two-Level Macro-to-Micro Tri-Mode Architecture (Stage 0 Global Deck Blueprint MCQs deciding total slides, heavy focus modules, and exact V3 animation slides + Stage 1..N Single-Slide `TDD` / Dual-Stage `GRILL` / `AUTONOMOUS_DUAL_EVOLVE`), strictly enforcing 1-Slide-Per-Step (`max_slides_generated_per_step == 1`) and 1-Hop Slide Topological Lock (`slide_manifest.json`), gated by `skill.design-anti-goodhart@1.0.0-rc.7` (AWF DesignAG) and `skill.anti-goodhart-verification@3.6.0-rc.1` (AWF Guard). Use whenever creating, revising, or auditing HTML slide decks, scientific paper walkthroughs, or teaching presentations.
---

# AWF HTML-PPT V3 (`skill.html-ppt@1.0.0-rc.9` — Two-Level Macro-to-Micro Tri-Mode Engine: Stage 0 Global Deck Blueprint MCQs [Total Slides + Focus Modules + V3 Animation Budget] + Stage 1..N `TDD` / Dual-Stage `GRILL` / `AUTONOMOUS_DUAL_EVOLVE`, Strictly 1-Slide-Per-Step & `AWF DesignAG` 18-Gate Enforcement)

An anti-Goodhart, self-evolving scientific HTML presentation authoring and verification engine. To prevent mid-deck attention collapse, template cloning, unrendered LaTeX leaks, overlapping/clipped DOM boxes, and pure-text laziness (`V0 = 0.30` cap), **AWF HTML-PPT V3 strictly forbids generating multiple slides in a single step** and supports a **Tri-Mode Execution Architecture** (`workflow_mode: "TDD" | "GRILL" | "AUTONOMOUS_DUAL_EVOLVE"`). Regardless of mode, every slide (`slides/slide_XX.html`) is generated, rendered, and audited **one slide per step** before unlocking the next slide in `slide_manifest.json`.

---

## 1. Two-Level Macro-to-Micro Tri-Mode Architecture (`Stage 0 Global Blueprint` + `TDD / GRILL / AUTONOMOUS_DUAL_EVOLVE`)

### Stage 0: Macro-GDD Global Deck Blueprint（全局总纲烤问与三联选择题拍板，`global_deck_blueprint`）
Before generating `storyboard.json` or writing `slide_01.html`, the Agent determines the **global architecture** with the human in two steps:
1. **Step 0.A — 全篇核心冲突一刀探底 (`macro_thesis_probe`)**:
   - Synthesizes the entire paper/topic into a 3-sentence **Bird's-Eye Conflict Formula** (`executive_core_conflict`: Bottleneck Ceiling $\to$ Core Physical Knob $\to$ Quantitative Breakthrough) and probes the user's baseline familiarity (`human_baseline_alignment`; if the user hasn't read the paper yet, provides a 1-minute bird's-eye onboarding map first).
2. **Step 0.B — 全局导演三联选择题（支持弹性区间与问答中动态演进，`total_slides_mcq` + `emphasis_allocation_mcq` + `v3_animation_budget_mcq`）**:
   - **MCQ 1 (`total_slides_mcq` — 一共多少页？固定页数或弹性区间)**: Presents $\ge 2$ pacing tiers and locks EITHER an exact `planned_total_slides` OR an **Elastic Slide Range (`elastic_slide_range: [min_slides, max_slides]`, e.g., `[14, 22]`)**. As Q&A progresses in Stage 1–3, the user or Agent can dynamically add/split slides (`SPLIT_SLIDE` / `INSERT_SLIDE`) when a mechanism needs deeper unpacking, or merge/remove future slides (`MERGE_SLIDES` / `REMOVE_SLIDE`) when the user already knows a section well, via `--mutate-storyboard` (`mutate_storyboard_manifest`).
   - **MCQ 2 (`emphasis_allocation_mcq` — 哪些方面重点讲？)**: Ranks all mechanisms by `Counter-Intuitiveness × Rubric Weight` and presents $\ge 2$ focus-weighting options so the user chooses `heavy_focus_modules` (which get 2–3 consecutive deep-dive slides instead of 1-page summaries).
   - **MCQ 3 (`v3_animation_budget_mcq` — 哪些设计动画/交互讲？先锁定种子页或边问边定 `JIT_DURING_QA`)**: Supports three discovery policies (`v3_discovery_policy`):
     1. `"UPFRONT_LOCKED"`: Lock exact 1-based slide indices (`v3_designated_slide_indices`) at Stage 0;
     2. `"HYBRID_SEED_PLUS_JIT"`: Lock 1–2 obvious core animation seed slides at Stage 0 AND promote additional slides during Stage 1–3 Q&A;
     3. `"JIT_DURING_QA"`: Do **not** force premature slide-number guessing at Stage 0 (`v3_designated_slide_indices: []`); instead, lock a minimum deck animation quota (`min_v3_slides_quota >= 1`, e.g. 3 V3 slides across the deck) and decide **which exact slides get V3 interactive sliders/animations during each slide's Q&A** (`PROMOTE_V3` or `promote_to_v3_animation: true` in the station capsule; Stage 4 `assemble_verified_deck` verifies that total V3 slides $\ge$ `min_v3_slides_quota`).

### Mode 1: `TDD` — Tutor-Driven Design（以教代建模式，`tdd_mode: true`）
- **Workflow**: `1 Tutor Station == 1 TDD Cognitive Capsule == 1 Slide`.
- At each station `Station_1.k`, the Agent runs a Socratic/Wittgenstein teaching dialogue with the human, records `tdd_station_capsule` via `--record-tdd-capsule` (`core_blindspot_or_conflict`, `wittgenstein_ladder`, `human_orthogonal_insight`, `visual_modality` $\in \{\text{V2}, \text{V3}\}$, `hidden_teleprompter_qa`), and then builds + audits `slides/slide_{k:02d}.html`.

### Mode 2: `GRILL` — Dual-Stage Grill-Driven Design（双阶烤问出题模式：机理烤问 + PPT制作选择题，`grill_mode: true`）
- **Workflow**: **Stage $k.1$ (3-Part Mechanism Grill $\to$ Teach-on-Miss $\to$ Isomorphic Re-Grill) $\to$ Stage $k.2$ (Bottleneck-to-Slide Mapping + Slide Design MCQ A/B/C) $\to$ Stage $k.3$ (1 Slide Build & Audit)**.
- **Stage $k.1$ — 科学机理三段式烤问与变式复烤（决定本页“讲什么/防什么”）：**
  - Select `question_archetype` $\in$ `{"PARADOX_BOTTLENECK", "KNOB_TURNING_PREDICTION", "TRADEOFF_BREAKDOWN", "ISOMORPHIC_REGRILL"}`.
  - Pose the **3-Part Grill Question (`grill_question`)**: `【给定锚点 Given Anchor】 + 【反直觉冲突 Paradox/Conflict】 + 【一刀见血追问 Razor Question】` (never ask unanchored trivia or blind guessing).
  - If the user answers **"不会" / uncertain**, immediately run **Teach-on-Miss** (Wittgenstein ladder: `Bridge -> Deconstruct -> Replace`) and verify with an **Isomorphic Re-Grill question** (`teaching_and_regrill_closure`; rubber-stamp questions like *"听懂了吗/明白了吗"* are automatically rejected by Gate `D16`!).
- **Stage $k.2$ — 认知断层映射与 PPT 视觉/排版选择题拍板（决定本页“怎么画/怎么排”）：**
  - **Bottleneck-to-Slide Mapping (`bottleneck_to_slide_mapping`)**: Turn the exact point where the user hesitated or got grilled into the **Headline Assertion and Visual Centerpiece** of `slide_{k:02d}.html`, and store the isomorphic re-grill Q&A inside the `S`-key hidden teleprompter (`hidden_teleprompter_qa`).
  - **Slide Design Multiple-Choice Question (`slide_design_mcq`)**: Directly ask the user a structured **A/B/C multiple-choice question** (with a `(Recommended)` option and cognitive/visual rationale) on how `slide_{k:02d}.html` should present this mechanism (e.g., `Option A (Recommended): Left Fig.1a energy funnel + Right V3 interactive Purcell slider`, `Option B: Top timeline + dual mechanism cards`, `Option C: 3-generation comparison radar`). Once the user selects an option (`selected_option`), record `gdd_grill_capsule` via `--record-grill-capsule` and build `slides/slide_{k:02d}.html`.

### Mode 3: `AUTONOMOUS_DUAL_EVOLVE` — Head-Down Autonomous Draft + Post-Review Dual-Evolution（闷头直出 + 审阅双升级模式，`autonomous_dual_evolve_mode: true`）
- **Phase A (Head-Down Autonomous 1-Slide-Per-Step Build)**:
  - With `require_human_approval: false`, the Agent does **not** interrupt the user during construction. Instead, it autonomously loops $k = 1 \dots N$, generating and verifying **strictly 1 slide per step** through all 18 `DesignAG` gates (`D1`–`D18`) and assembling the complete `deck.html` (`Z:\...\deck.html` + `file:///Z:/.../deck.html`).
- **Phase B (Human Review $\to$ Dual-Evolution of PPT + `AWF HTML-PPT` / `DesignAG`)**:
  - After reviewing `deck.html`, the human gives critique/feedback.
  - Running `--apply-feedback-dual-upgrade feedback_payload.json` enforces `verify_dual_evolution_feedback_receipt`:
    1. **Upgrades the PPT itself**: Patches the target `slides/slide_{k:02d}.html`, re-runs the 18-gate `DesignAG` audit, and updates `slide_manifest.json` + `deck.html`.
    2. **Simultaneously upgrades `AWF HTML-PPT` / `AWF DesignAG`** (when `is_generalizable_to_awf: true`): Records `target_gate_or_rule_id` and `negative_canary_fixture` so the workflow permanently learns from the user's critique.

---

## 2. Non-Negotiable Anti-Goodhart Laws

1. **Strictly 1 Slide Per Step (`max_slides_generated_per_step == 1`)**:
   - Never generate a monolithic multi-slide HTML file in one shot, and never batch 2 or more slides in a single step.
   - Each slide lives in its own isolated module (`slides/slide_01.html`, `slides/slide_02.html`, ...) and is individually audited via [`scripts/audit_single_slide_step.py`](scripts/audit_single_slide_step.py) against `skill.design-anti-goodhart@1.0.0-rc.7` (`AWF DesignAG`).
2. **1-Hop Slide Topological Lock (`unverified_slide_hop_distance == 1`)**:
   - Tracked in `slide_manifest.json`. At initialization, only `slide_01` (`Station_1.1`) is `"UNLOCKED"`; `slide_02..N` are `"LOCKED"`.
   - `slide_{k+1}` is unlocked **if and only if** `slide_k` has passed all per-slide DesignAG gates (`D1`–`D12`, `D15`, `D16`) with zero Redlines (`R1`–`R7`) and its SHA-256 receipt is recorded as `"status": "PASS"` in `slide_manifest.json`.
3. **Human-in-the-Loop Sign-off Gate (`require_human_approval: true`)**:
   - Optional in Mode 1 (`TDD`) and Mode 2 (`GRILL`); disabled (`false`) during Phase A of Mode 3 (`AUTONOMOUS_DUAL_EVOLVE`).
4. **Multiplicative Visual Modality Cap ($A_i = w_i \times C_{\text{clarity}} \times V_{\text{visual}}$)**:
   - Pure text (`V0 = 0.30`) is mathematically capped at 30% of the score. Mechanism and data slides must use clean cropped paper figures / accurate SVG diagrams (`V2 = 0.80`) or physics-coupled interactive widgets / multi-step SVG animations (`V3 = 1.00`).

---

## 3. CLI Commands (`scripts/audit_single_slide_step.py`)

```bash
# Run Tri-Mode self-test (verifies all 8 invariants across TDD, Dual-Stage GRILL, and AUTONOMOUS_DUAL_EVOLVE)
python scripts/audit_single_slide_step.py --self-test

# Initialize storyboard manifest (workflow_mode: "TDD" | "GRILL" | "AUTONOMOUS_DUAL_EVOLVE")
python scripts/audit_single_slide_step.py --init-storyboard storyboard.json --manifest slide_manifest.json

# Mode 1 (TDD): Record Tutor Station cognitive capsule for slide K
python scripts/audit_single_slide_step.py --record-tdd-capsule tdd_capsule_01.json --slide-index 1 --manifest slide_manifest.json

# Mode 2 (GRILL): Record Dual-Stage Grill capsule (3-Part Mechanism Grill + Slide Design MCQ) for slide K
python scripts/audit_single_slide_step.py --record-grill-capsule grill_capsule_01.json --slide-index 1 --manifest slide_manifest.json

# Mode 3 (AUTONOMOUS_DUAL_EVOLVE): Apply human feedback to patch PPT slide AND record AWF upgrade receipt
python scripts/audit_single_slide_step.py --apply-feedback-dual-upgrade dual_upgrade_payload.json --manifest slide_manifest.json

# Assemble all PASS slides into final deck.html
python scripts/audit_single_slide_step.py --assemble-deck --manifest slide_manifest.json --output deck.html
```

---

## 4. Preserved References & Templates

- Concrete system semantics & title rules: [content-and-evidence.md](references/content-and-evidence.md)
- Visual & browser interaction checklist: [visual-and-interaction-review.md](references/visual-and-interaction-review.md)
- Base 16:9 slide scaffold: [slide-template.html](assets/slide-template.html)
