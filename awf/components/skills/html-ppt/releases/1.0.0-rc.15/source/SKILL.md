---
name: html-ppt
description: Build, audit, and evolve 16:9 scientific interactive HTML presentations (AWF HTML-PPT / SciSlide) under a Two-Level Macro-to-Micro Tri-Mode Architecture (Stage 0 Global Deck Blueprint MCQs deciding total slides, heavy focus modules, and exact V3 animation slides + Stage 1..N Single-Slide `TDD` / Dual-Stage `GRILL` / `AUTONOMOUS_DUAL_EVOLVE`), strictly enforcing 1-Slide-Per-Step (`max_slides_generated_per_step == 1`) and 1-Hop Slide Topological Lock (`slide_manifest.json`), gated by `skill.design-anti-goodhart@1.0.0-rc.13` (AWF DesignAG) and `skill.anti-goodhart-verification@3.7.0-rc.7` (AWF Guard). Use whenever creating, revising, or auditing HTML slide decks, scientific paper walkthroughs, or teaching presentations.
---

# AWF HTML-PPT V3 (`skill.html-ppt@1.0.0-rc.15` — Two-Level Macro-to-Micro Tri-Mode Engine: Stage 0 Global Deck Blueprint MCQs [Total Slides + Focus Modules + V3 Animation Budget] + Stage 1..N `TDD` / Dual-Stage `GRILL` / `AUTONOMOUS_DUAL_EVOLVE`, Strictly 1-Slide-Per-Step & `AWF DesignAG` 18-Gate Enforcement)

An anti-Goodhart, self-evolving scientific HTML presentation authoring and verification engine. To prevent mid-deck attention collapse, template cloning, unrendered LaTeX leaks, overlapping/clipped DOM boxes, and pure-text laziness (`V0 = 0.30` cap), **AWF HTML-PPT V3 strictly forbids generating multiple slides in a single step** and supports a **Tri-Mode Execution Architecture** (`workflow_mode: "TDD" | "GRILL" | "AUTONOMOUS_DUAL_EVOLVE"`). Regardless of mode, every slide (`slides/slide_XX.html`) is generated, rendered, and audited **one slide per step** before unlocking the next slide in `slide_manifest.json`.

---

## 1. Two-Level Macro-to-Micro Tri-Mode Architecture (`Stage 0 Global Blueprint` + `TDD / GRILL / AUTONOMOUS_DUAL_EVOLVE`)

### Stage 0: Macro-GDD Global Deck Blueprint（全局总纲烤问与三联选择题拍板，`global_deck_blueprint`）
Before generating `storyboard.json` or writing `slide_01.html`, the Agent determines the **global architecture** with the human in two steps:
1. **Step 0.A — 全篇核心冲突一刀探底 (`macro_thesis_probe`)**:
   - Synthesizes the entire paper/topic into a 3-sentence **Bird's-Eye Conflict Formula** (`executive_core_conflict`: Bottleneck Ceiling $\to$ Core Physical Knob $\to$ Quantitative Breakthrough) and probes the user's baseline familiarity (`human_baseline_alignment`; if the user hasn't read the paper yet, provides a 1-minute bird's-eye onboarding map first).
2. **Step 0.B — 全局导演选择题（以「内容与逻辑演进流程」为核心，支持「页数不限，顺着逻辑自然长出」，`logical_flow_mcq` + `emphasis_allocation_mcq` + `total_slides_mcq` + `v3_animation_budget_mcq`）**:
   - **MCQ 1 (`logical_flow_mcq` — 内容与逻辑演进流程怎么走？首要核心)**: Establishes the ordered causal narrative spine (`logical_flow_spine`, e.g., `["1. 痛点死结", "2. 核心破局旋钮与物理机理", "3. 控制变量实验铁证", "4. 代价与适用边界"]`).
   - **MCQ 2 (`emphasis_allocation_mcq` — 哪些方面重点深挖？)**: Ranks all mechanisms by `Counter-Intuitiveness × Rubric Weight` so the user selects `heavy_focus_modules`.
   - **MCQ 3 (`total_slides_mcq` — 页数策略：默认推荐「不限，顺着逻辑自然确定」)**:
     1. **`A (Recommended)` 页数不限 / 顺着逻辑流程自然生长 (`slide_count_policy: "UNBOUNDED_FLOW_DRIVEN"`, `planned_total_slides: "不限"`)**: Do **not** guess an artificial total slide count upfront! Instead, follow `logical_flow_spine` step by step—each logical module organically takes as many slides as needed (`APPEND_FLOW_SLIDE` / `SPLIT_SLIDE` / `MERGE_SLIDES` via `--mutate-storyboard`) until every module in `logical_flow_spine` is clearly explained.
     2. **`B` 弹性页数区间 (`elastic_slide_range: [min_slides, max_slides]`)** or **`C` 固定时长页数 (`planned_total_slides`)**.
   - **MCQ 4 (`v3_animation_budget_mcq` — 哪些设计动画/交互讲？默认推荐边问边定 `JIT_DURING_QA`)**: Supports `"JIT_DURING_QA"` (decide which exact slides get `V3` interactive sliders/animations during each slide's Q&A along the logical flow, while enforcing `min_v3_slides_quota >= 1` at final deck assembly), `"HYBRID_SEED_PLUS_JIT"`, or `"UPFRONT_LOCKED"`.
3. **Step 0.C — 分级洋葱剥皮演进流程 (`onion_peeling_capsule` + `--peel-onion-trunk`)**:
   - **Layer 0 (最外层粗框架 `layer0_macro_frame`)**: Only locks the 3–5 coarsest macro trunks (`macro_trunks_mcq`: `Trunk_1`, `Trunk_2`, ..., where `Trunk_2..M` start as `"UNPEELED"`).
   - **Layer 1..K (进入某一个主干，确定该主干内的细分框架 `peel_onion_trunk_subframe`)**: When entering `Trunk_m`, the Agent peels open *only* `Trunk_m` (`trunk_subframe_mcq`), deciding which sub-points inside `Trunk_m` become atomic `LEAF_SLIDE` pages (or recursive `SUB_BRANCH` layers), enforced by a 1-Hop Trunk Order Lock (`Trunk_{m+1}` cannot be peeled while `Trunk_m`'s leaf slides are unfinished).
   - **Leaf Layer (最终到单页内容与视觉确定)**: Each `LEAF_SLIDE` undergoes Single-Slide Mechanism Grill / TDD Q&A + Slide Visual/Animation MCQ (`V2` vs `V3`) $\to$ 1-Slide HTML generation & 18-gate `DesignAG` audit. Stage 4 assembly verifies that 100% of `macro_trunks` have been peeled (zero `"UNPEELED"` trunks remaining).

4. **Step 0.D — 全域输入-洋葱理解-跨载体输出统一控制总线 (universal_io_bus_capsule + --record-cross-artifact-unit)**:
   - **Role 1 (EvidenceIngest — 输入证据与文献蒸馏账本官, evidence_ingest_ledger)**: Bridges raw PDF papers (pdf-document-stack / ablesci), calculation outputs, and experimental logs into anchored facts (claim_id, quantitative_value, source_artifact_or_figure_ref) before Onion Layer 0 begins, eliminating hallucinated numbers or misattributed figures.
   - **Role 2 (DevilReviewer — 魔鬼审稿人与答辩评委官, devil_advocate_review)**: Challenges core mechanisms with alternative_hypothesis_challenge (skeptical peer-reviewer alternative hypothesis) and requires control_evidence_rebuttal (negative control / ablation proof), feeding into PPT S-key teleprompter notes, Paper Discussion/Rebuttal (AWF SciWord), and Figure control panels (AWF FigPPT).
   - **Role 3 (OmniArtifactHub — 跨载体同源总调度官, cross_artifact_targets)**: Allows a single shared Onion Peeling & Q&A tree (onion_peeling_capsule) to simultaneously drive AWF HTML-PPT (skill.html-ppt@1.0.0-rc.15), AWF SciWord (workflow.scientific-report-authoring@1.0.0-rc.14 / skill.edit-scientific-article@1.0.0-rc.11 + skill.build-scientific-docx@1.0.0-rc.14), and AWF FigPPT / SciFig (workflow.editable-figure-pptx@1.0.0-rc.2 / skill.build-editable-figure-pptx@1.0.0-rc.2).

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
  - With `require_human_approval: false`, the Agent does **not** interrupt the user during construction. Instead, it autonomously loops $k = 1 \dots N$, generating and verifying **strictly 1 slide per step** through applicable per-slide structural checks (`D1`–`D18`) and assembling the complete `deck.html` (`Z:\...\deck.html` + `file:///Z:/.../deck.html`).
- **Phase B (Human Review $\to$ Dual-Evolution of PPT + `AWF HTML-PPT` / `DesignAG`)**:
  - After reviewing `deck.html`, the human gives critique/feedback.
  - Running `--apply-feedback-dual-upgrade feedback_payload.json` enforces `verify_dual_evolution_feedback_receipt`:
    1. **Upgrades the PPT itself**: Patches the target `slides/slide_{k:02d}.html`, re-runs the 18-gate `DesignAG` audit, and updates `slide_manifest.json` + `deck.html`.
    2. **Simultaneously upgrades `AWF HTML-PPT` / `AWF DesignAG`** (when `is_generalizable_to_awf: true`): Records `target_gate_or_rule_id` and `negative_canary_fixture` so the workflow permanently learns from the user's critique.

---

## 2. Non-Negotiable Anti-Goodhart Laws

1. **Strictly 1 Slide Per Step (`max_slides_generated_per_step == 1`)**:
   - Never generate a monolithic multi-slide HTML file in one shot, and never batch 2 or more slides in a single step.
   - Each slide lives in its own isolated module (`slides/slide_01.html`, `slides/slide_02.html`, ...) and is individually audited via [`scripts/audit_single_slide_step.py`](scripts/audit_single_slide_step.py) against `skill.design-anti-goodhart@1.0.0-rc.13` (`AWF DesignAG`).
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


## Content contract before visual scoring

Use concrete scientific titles: each title names a concrete object, phenomenon, relationship, or question and is natural enough to read aloud. Keep the lesson workflow in presenter notes or controls. Before accepting an algorithm or optimization slide, apply the concrete-system semantics contract in `references/content-and-evidence.md`: identify the physical candidate, inputs, objectives and directions, operation, output, and downstream decision. Verify every illustrated dominance relationship against its coordinates. A layout score cannot substitute for these content checks.

## D17/D18 evidence hardening contract (2026-11-10)

Resolved composition: Tutor Skill/Workflow `1.0.0-rc.26`, DesignAG Skill/Workflow
`1.0.0-rc.13`, HTML-PPT Skill `1.0.0-rc.15` / Workflow `1.0.0-rc.12`,
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
`workflows/design-anti-goodhart/releases/1.0.0-rc.13/source/`; include that directory
and locked component trees when packaging. Current releases remain immutable.
