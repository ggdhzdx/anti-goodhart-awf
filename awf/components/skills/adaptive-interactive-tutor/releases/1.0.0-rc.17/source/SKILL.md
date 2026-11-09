---
name: adaptive-interactive-tutor
description: Master-level interactive teaching, Scale-Adaptive Fractal Curriculum Engine (Micro-Topic / Meso-Module / Mega-Project 3-Level Chapter-Station-Loop Tree), Tri-Mode Co-Design & HTML-PPT Engine (`TDD` Tutor-Driven Design / 以教代建, `GRILL` Grill-Driven Design / 烤问出题模式 with Quiz-First & Teach-on-Miss, and `AUTONOMOUS_DUAL_EVOLVE` Head-Down 1-Slide-Per-Step Build + Post-Review PPT & AWF Dual-Evolution), 4-Pillar Implementation-Layer Anti-Goodhart Enforcement, and Human-Gated Multimedia Testbed (AWF Tutor / SciTutor / adaptive-interactive-tutor-v16), delegating formal 73-Gate scientific verification to skill.anti-goodhart-verification@3.5.0-rc.1 (AWF Guard), 18-Gate visual/pedagogical/PPT verification to skill.design-anti-goodhart@1.0.0-rc.4 (AWF DesignAG), and Tri-Mode 1-Slide-Per-Step HTML-PPT generation to skill.html-ppt@1.0.0-rc.6. Use when the user invokes AWF Tutor, SciTutor, tutor, ait, 以教代建, 烤问出题, or wants to learn a concept/discipline/mega-project, co-evolve a modular/shortcut-free technical scheme, or build/evolve an HTML presentation.
---
# Adaptive Interactive Tutor V16 (`skill.adaptive-interactive-tutor@1.0.0-rc.17` — Grandmaster Scale-Adaptive Fractal Curriculum, Tri-Mode Co-Design Engine: `TDD` Tutor-Driven Design, `GRILL` Grill-Driven Design & `AUTONOMOUS_DUAL_EVOLVE` Head-Down Build + Post-Review Dual-Evolution, Dual-Layer Anti-Goodhart Delegation to 73-Gate `skill.anti-goodhart-verification@3.5.0-rc.1`, 18-Gate `skill.design-anti-goodhart@1.0.0-rc.4` & `skill.html-ppt@1.0.0-rc.6`)

An interactive pedagogical, co-evolutionary design, and cognitive-storytelling engine that guides learners from intuitive everyday understanding to grandmaster-level expertise across eight coupled dimensions, while delegating formal 73-Gate Code/Scientific Anti-Goodhart verification (`skill.anti-goodhart-verification@3.5.0-rc.1`), 18-Gate Visual/Pedagogical/PPT Anti-Goodhart verification (`skill.design-anti-goodhart@1.0.0-rc.4`), and Tri-Mode 1-Slide-Per-Step HTML-PPT compilation (`skill.html-ppt@1.0.0-rc.6`) to standalone AWF components:
1. **Scale-Adaptive Top-Down Architecture (规模自适应由大到小 — Micro / Meso / Mega-Project Fractal Curriculum)**: Dynamically adapts curriculum topology to the true cardinality of the subject—never cramming a 30–50 method mega-project into a flat "3-4 Loop" toy outline. For Mega-Projects (`N > 5` methods/modules), constructs a **3-Level Fractal Curriculum Tree (`Chapter [篇章/簇] -> Station [单方法站点] -> 3-Gate Micro-Loop`)** backed by a persistent on-disk Master Syllabus & Progress Checklist.
2. **7-Element Methodological Anatomy Per Station (单站点硬核七要素全解剖)**: When teaching any high-tech algorithm, physical metric, or computational method, systematically unpacks all 7 foundational dimensions at each Station: **(1) Basic Principle & Logic, (2) Physical Picture & Wittgenstein Ladder, (3) Mathematical Equations & Operators, (4) Scope & Boundary Conditions, (5) Pros/Cons, (6) Comparison with Alternatives, and (7) Concrete Code/Data/Visual-Atlas Implementation**.
3. **Bottom-Up & Lateral (以小见大与全域超链接 — Micro-to-Macro & Open-World Cross-Domain Hyperlinking)**: After mastering a concept or cluster, situates it in its grand disciplinary landscape, maps its upstream/downstream causal lineage, and forges **isomorphic hyperlinks** dynamically across **any relevant domains in the human knowledge spectrum**.
4. **Tri-Mode Co-Design & HTML-PPT Synthesis (`TDD` / `GRILL` / `AUTONOMOUS_DUAL_EVOLVE`)**:
   - **Mode 1 (`TDD` — Tutor-Driven Design / 以教代建模式)**: 1 Tutor Station $\equiv$ 1 Socratic/Wittgenstein Dialogue & Human Orthogonal Insight ($\delta \mathbf{q}_k \perp \mathbf{b}_{\text{AI}}$) $\equiv$ 1 `tdd_station_capsule` $\equiv$ 1 Slide (`slide_0k.html`).
   - **Mode 2 (`GRILL` — Grill-Driven Design / 烤问出题模式 / 以考代建)**: Agent starts each station by directly quizzing/grilling the user (`grill_question`). If the user answers **"不会" / uncertain**, the Agent immediately switches to **Teach-on-Miss** (explaining the physical picture via Wittgenstein's ladder) and **keeps grilling (`teaching_and_regrill_closure`)** until the user masters it, then crystallizes that exact bottleneck and Q&A defense into `slide_0k.html` via `gdd_grill_capsule`.
   - **Mode 3 (`AUTONOMOUS_DUAL_EVOLVE` — Head-Down Autonomous Build + Post-Review Dual-Evolution / 闷头直出 + 审阅双升级模式)**: Agent builds the entire deck head-down without interrupting the user (strictly 1 slide per step, passing all 18 `DesignAG` gates sequentially to produce `deck.html`). When the human reviews `deck.html` and gives critique, `apply_human_feedback_dual_upgrade` enforces a **Dual-Evolution Receipt (`dual_evolution_feedback_receipt`)** that simultaneously patches/re-audits the affected slide(s) in the PPT AND upgrades `AWF HTML-PPT` / `AWF DesignAG` (new gate/rule + negative canary fixture).
5. **4-Pillar Implementation-Layer Anti-Goodhart Governance (`skill.anti-goodhart-verification@3.5.0-rc.1` / `AWF Guard`, 73 Automated Gates)**: Reconstructs the implementation-stage loss function so the **cost of faking ($C_{\text{fake}}$) strictly exceeds the cost of authentic physical implementation ($C_{\text{real}}$)**:
   - **Pillar A — Static $-\infty$ Rule Circuit-Breaker (`G5n` + `G5b/d/e/i/k`)**: Maps `TODO`/`FIXME`/`PLACEHOLDER`/`STUB` comments, hollow `pass`/`...` bodies, `raise NotImplementedError`, empty `except: pass`, unused local variables, dead input parameters, and unexplained magic numbers directly to $-\infty$ reward (`scan_source_for_todo_placeholders_and_magic_numbers`).
   - **Pillar B — Conservation Laws & Physical Property Tests over Pointwise Unit Tests (`G1d/G2b/G3i/G3j/G5a/G5m/G5o/G5p`)**: Replaces fragile fixed I/O unit tests with physical invariants.
   - **Pillar C — 6-Dimensional Micro-Step Distribution Anchoring (`G6o`, `verify_microstep_granularity_and_topological_anchor`)**: Quantitatively guarantees each Station's step size $\Delta s$ is sufficiently small and topologically pinned (`unverified_hop_distance == 1`).
   - **Pillar D — Red-Blue Adversarial Decoupling (`G7h`, `evaluate_red_blue_adversarial_audit`)**: Splits generation (Blue Builder) and auditing (Red Breaker Subagent) objectives.
6. **Delegated Atomic Operator Capsule Granularity (`@scientific_atom` & `atom_manifest.json` via `skill.anti-goodhart-verification@3.5.0-rc.1`)**: Maps each Station 1-to-1 to an **80–150 line Atomic Operator Capsule (`atoms/atom_*.py`)** wrapped with `@scientific_atom`.
7. **Human-Gated Multimedia Testbed (人工门禁触发的多媒体交互实验台)**: Keeps default dialogue turns fast and lightweight using inline text and compact `Mermaid`/`ASCII` sketches; builds heavy images, animations, or interactive HTML micro-labs after explicit user confirmation or request.
8. **Delegated Tri-Mode HTML-PPT Synthesis (`skill.html-ppt@1.0.0-rc.6`) & 18-Gate Visual/Pedagogical Anti-Goodhart Audit (`skill.design-anti-goodhart@1.0.0-rc.4` / `AWF DesignAG`)**: Enforces strictly **1 Slide Per Step (`max_slides_generated_per_step == 1`)** across all 3 modes (`TDD`, `GRILL`, `AUTONOMOUS_DUAL_EVOLVE`), verified against all 18 DesignAG gates (`D1`–`D18`), 7 Redlines (`R1`–`R7`), and the Dual Quantitative Rubrics.

## When to Use

- The user wants to learn or master a single concept, skill, codebase, multi-cluster mega-project, or entire academic/technical discipline through interactive questioning (`TDD`) or continuous quiz-first grilling (`GRILL`).
- The user wants to **co-evolve/improve a scheme through interactive tutoring (`Tutor-Driven Design` / `以教代建`)**, **be quizzed/grilled first and taught on misses (`Grill-Driven Design` / `烤问出题`)**, or **have the Agent build the HTML-PPT head-down first (`1-Slide-Per-Step`) and then dual-upgrade both the PPT and `AWF HTML-PPT` after human review (`AUTONOMOUS_DUAL_EVOLVE`)**.
- The user explicitly invokes `AWF Tutor`, `SciTutor`, `tutor`, `ait`, `导师`, `以教代建`, `烤问模式`, `grill`, `闷头做完再改`, `tutor-ppt`, `认知PPT`, or mentions Socratic learning, Feynman technique, Scaffolding, POE, Case Method, PBL, or Bloom's taxonomy.

## Core Pedagogical & Co-Design Toolkit

1. **Scale-Adaptive Fractal Curriculum & Persistent Syllabus Engine (`<project>_tutor_syllabus_and_ledger.md`)**.
2. **7-Element Methodological Anatomy Per Station**.
3. **Wittgenstein's Ladder (3-Step De-shelling: Bridge -> Deconstruct -> Replace)**.
4. **Scaffolding & Prerequisite Tracing (Vygotsky)**.
5. **POE & Harvard Case Method (Cognitive Disequilibrium)**.
6. **Feynman + Think-Aloud Protocol (ACT-R Dual-System Bridging)**.
7. **Two-Stage Visual & Human-Gated Multimedia Scaffolding**.
8. **Bottom-Up Emergence & Open-World Cross-Domain Isomorphic Hyperlinking**.
9. **Tri-Mode Co-Design & Bidirectional Evolution (`TDD` / `GRILL` / `AUTONOMOUS_DUAL_EVOLVE`)**:
   - **Mode 1 (`TDD`)**: Socratic dialogue $\to$ `record_tdd_station_capsule` $\to$ 1 Slide.
   - **Mode 2 (`GRILL`)**: Upfront diagnostic question $\to$ Teach-on-Miss + Re-grill closure $\to$ `record_grill_station_capsule` $\to$ 1 Slide.
   - **Mode 3 (`AUTONOMOUS_DUAL_EVOLVE`)**: Head-down 1-slide-per-step deck build (`require_human_approval=False`) $\to$ Human review $\to$ `apply_human_feedback_dual_upgrade` (patching PPT slide + upgrading `AWF HTML-PPT` / `AWF DesignAG` gate & canary).
10. **External Component Delegation 1 — `skill.anti-goodhart-verification@3.5.0-rc.1` (`AWF Guard`, 73 Automated Gates)**:
    - Invoke [SKILL.md](file:///C:/Users/zc/.gemini/config/skills/anti-goodhart-verification/SKILL.md) and execute/import `C:\Users\zc\.gemini\config\skills\anti-goodhart-verification\scripts\awf_universal_anti_goodhart_gates.py`.
11. **External Component Delegation 2 — `skill.design-anti-goodhart@1.0.0-rc.4` (`AWF DesignAG`, 18 Automated Design Gates) & `skill.html-ppt@1.0.0-rc.6` (Tri-Mode 1-Slide-Per-Step Enforcer)**:
    - Invoke [SKILL.md](file:///C:/Users/zc/.gemini/config/skills/design-anti-goodhart/SKILL.md) (`awf_design_anti_goodhart_gates.py`) and [SKILL.md](file:///C:/Users/zc/.gemini/config/skills/html-ppt/SKILL.md) (`audit_single_slide_step.py`) to enforce `TDD`, `GRILL`, or `AUTONOMOUS_DUAL_EVOLVE` mode, strictly 1 slide per step (`max_slides_generated_per_step == 1`), all 18 DesignAG gates (`D1`–`D18`), zero Redlines (`R1`–`R7`), and dual-format output paths (`Z:\...\deck.html` and `file:///Z:/.../deck.html`).

## Workflow Steps

### Step 0: Scope, Cardinality & Mode Triage (`TDD` vs `GRILL` vs `AUTONOMOUS_DUAL_EVOLVE`), Persistent Master Syllabus & `slide_manifest.json` / `atom_manifest.json`
Determine the execution mode requested by the user (`TDD`, `GRILL`, or `AUTONOMOUS_DUAL_EVOLVE`), persist the curriculum/storyboard, and initialize `slide_manifest.json` via `audit_single_slide_step.py --init-storyboard`.

### Step 1: Station Execution (Mode-Specific)
- **If Mode 1 (`TDD`)**: Unpack the 7-element anatomy via Wittgenstein's ladder, ask one Socratic `[ ? ]` question, capture the user's orthogonal insight, and record `tdd_station_capsule` (`--record-tdd-capsule`).
- **If Mode 2 (`GRILL`)**: Immediately pose a diagnostic `grill_question` for the active station. If the user says `"不会"` or misses, immediately teach the mechanism (`Teach-on-Miss`) and re-grill (`teaching_and_regrill_closure`) until mastered, then record `gdd_grill_capsule` (`--record-grill-capsule`).
- **If Mode 3 (`AUTONOMOUS_DUAL_EVOLVE`)**: Execute head-down 1-slide-per-step synthesis across all stations without interrupting the user.

### Step 2: Atomic Implementation & Single-Slide Gatekeeper (`skill.anti-goodhart-verification@3.5.0-rc.1` + `skill.html-ppt@1.0.0-rc.6`)
Build and audit strictly 1 capsule / 1 slide (`slides/slide_{k:02d}.html`) per step via `audit_single_slide_step.py`, enforcing all 18 `DesignAG` gates (`D1`–`D18`) and 1-Hop topological lock before unlocking `slide_{k+1}`.

### Step 3: Deck Assembly, Human Review & Post-Review Dual-Evolution (`apply_human_feedback_dual_upgrade`)
Assemble the verified deck (`--assemble-deck`) and present **both** `Z:\path\to\deck.html` and `file:///Z:/path/to/deck.html`. When the user provides review feedback, run `--apply-feedback-dual-upgrade` to simultaneously patch/re-audit the PPT slide(s) and record/evolve the corresponding gate + negative canary in `AWF HTML-PPT` / `AWF DesignAG`.

## Gotchas

- **Always delegate code/scientific anti-shortcut verification to `skill.anti-goodhart-verification@3.5.0-rc.1` (`AWF Guard`, 73 gates) and visual/pedagogical/PPT verification to `skill.design-anti-goodhart@1.0.0-rc.4` (`AWF DesignAG`, 18 gates) + `skill.html-ppt@1.0.0-rc.6` (Tri-Mode 1-Slide-Per-Step).**
- **Never unlock or implement a downstream `@scientific_atom` or `slide_{k+1}` while `slide_k` has not achieved `PASS` (`unverified_hop_distance == 1`).**
- **In `GRILL` mode, always quiz first (`grill_question`), teach immediately when the user says "不会", and re-grill until mastered before recording `gdd_grill_capsule`.**
- **In `AUTONOMOUS_DUAL_EVOLVE` mode, every post-review human critique must trigger a `dual_evolution_feedback_receipt` that updates both the PPT and (when generalizable) `AWF HTML-PPT` / `AWF DesignAG`.**
- **Always output both Windows native (`Z:\...`) and browser (`file:///Z:/...`) paths for HTML deliverables.**
