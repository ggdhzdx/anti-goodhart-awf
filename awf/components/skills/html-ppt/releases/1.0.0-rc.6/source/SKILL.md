---
name: html-ppt
description: Build, audit, and evolve 16:9 scientific interactive HTML presentations (AWF HTML-PPT / SciSlide) under a Tri-Mode Execution Architecture (`TDD` Tutor-Driven Design, `GRILL` Grill-Driven Design with Quiz-First & Teach-on-Miss, and `AUTONOMOUS_DUAL_EVOLVE` Head-Down 1-Slide-Per-Step Build + Post-Review PPT & AWF Dual-Evolution), strictly enforcing 1-Slide-Per-Step (`max_slides_generated_per_step == 1`), 1-Hop Slide Topological Lock (`slide_manifest.json`), and optional Human-in-the-Loop Sign-off Gate, gated by `skill.design-anti-goodhart@1.0.0-rc.4` (AWF DesignAG, 18 Automated Design Gates D1-D18 + 7 Redlines R1-R7 + Dual Quantitative Rubrics) and `skill.anti-goodhart-verification@3.5.0-rc.1` (AWF Guard). Use whenever creating, revising, or auditing HTML slide decks, scientific paper walkthroughs, or teaching presentations.
---

# AWF HTML-PPT V3 (`skill.html-ppt@1.0.0-rc.6` — Tri-Mode Execution Engine: `TDD` Tutor-Driven Design, `GRILL` Grill-Driven Design & `AUTONOMOUS_DUAL_EVOLVE` Head-Down Build + Post-Review Dual-Evolution, Strictly 1-Slide-Per-Step, 1-Hop Topological Lock & `AWF DesignAG` 18-Gate Enforcement)

An anti-Goodhart, self-evolving scientific HTML presentation authoring and verification engine. To prevent mid-deck attention collapse, template cloning, unrendered LaTeX leaks, overlapping/clipped DOM boxes, and pure-text laziness (`V0 = 0.30` cap), **AWF HTML-PPT V3 strictly forbids generating multiple slides in a single step** and supports a **Tri-Mode Execution Architecture** (`workflow_mode: "TDD" | "GRILL" | "AUTONOMOUS_DUAL_EVOLVE"`). Regardless of mode, every slide (`slides/slide_XX.html`) is generated, rendered, and audited **one slide per step** before unlocking the next slide in `slide_manifest.json`.

---

## 1. Tri-Mode Execution Architecture (`TDD` / `GRILL` / `AUTONOMOUS_DUAL_EVOLVE`)

### Mode 1: `TDD` — Tutor-Driven Design（以教代建模式，`tdd_mode: true`）
- **Workflow**: `1 Tutor Station == 1 TDD Cognitive Capsule == 1 Slide`.
- At each station `Station_1.k`, the Agent runs a Socratic/Wittgenstein teaching dialogue with the human, records `tdd_station_capsule` via `--record-tdd-capsule` (`core_blindspot_or_conflict`, `wittgenstein_ladder`, `human_orthogonal_insight`, `visual_modality` $\in \{\text{V2}, \text{V3}\}$, `hidden_teleprompter_qa`), and then builds + audits `slides/slide_{k:02d}.html`.

### Mode 2: `GRILL` — Grill-Driven Design（烤问出题模式 / 以考代建，`grill_mode: true`）
- **Workflow**: **Quiz-First $\to$ Teach-on-Miss $\to$ Re-Grill Closure $\to$ 1 Slide**.
- At each station `Station_1.k`, the Agent **immediately challenges the user with a diagnostic question (`grill_question`)**:
  - If the user answers **"不会" / uncertain / incomplete**, the Agent immediately switches to **Teach-on-Miss** (`taught_on_miss: true`), explains the physical picture using a Wittgenstein ladder, and **keeps grilling (`teaching_and_regrill_closure`)** until the user masters the mechanism.
  - Once closed, the Agent records `gdd_grill_capsule` via `--record-grill-capsule` and crystallizes that exact exam question, physical picture, and follow-up defense into `slides/slide_{k:02d}.html`.

### Mode 3: `AUTONOMOUS_DUAL_EVOLVE` — Head-Down Autonomous Draft + Post-Review Dual-Evolution（闷头直出 + 审阅双升级模式，`autonomous_dual_evolve_mode: true`）
- **Phase A (Head-Down Autonomous 1-Slide-Per-Step Build)**:
  - With `require_human_approval: false`, the Agent does **not** interrupt the user during construction. Instead, it autonomously loops $k = 1 \dots N$, generating and verifying **strictly 1 slide per step** through all 18 `DesignAG` gates (`D1`–`D18`) and assembling the complete `deck.html` (`Z:\...\deck.html` + `file:///Z:/.../deck.html`).
- **Phase B (Human Review $\to$ Dual-Evolution of PPT + `AWF HTML-PPT` / `DesignAG`)**:
  - After reviewing `deck.html`, the human gives critique/feedback.
  - Running `--apply-feedback-dual-upgrade feedback_payload.json` enforces `verify_dual_evolution_feedback_receipt`:
    1. **Upgrades the PPT itself**: Patches the target `slides/slide_{k:02d}.html`, re-runs the 18-gate `DesignAG` audit, and updates `slide_manifest.json` + `deck.html`.
    2. **Simultaneously upgrades `AWF HTML-PPT` / `AWF DesignAG`** (when `generalizable_to_awf: true`): Records `awf_upgrade_target`, `new_or_updated_gate_rule`, and `negative_canary_added` so the workflow permanently learns from the user's critique.

---

## 2. Non-Negotiable Anti-Goodhart Laws

1. **Strictly 1 Slide Per Step (`max_slides_generated_per_step == 1`)**:
   - Never generate a monolithic multi-slide HTML file in one shot, and never batch 2 or more slides in a single step.
   - Each slide lives in its own isolated module (`slides/slide_01.html`, `slides/slide_02.html`, ...) and is individually audited via [`scripts/audit_single_slide_step.py`](scripts/audit_single_slide_step.py) against `skill.design-anti-goodhart@1.0.0-rc.4` (`AWF DesignAG`).
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
# Run Tri-Mode self-test (verifies all 8 invariants across TDD, GRILL, and AUTONOMOUS_DUAL_EVOLVE)
python scripts/audit_single_slide_step.py --self-test

# Initialize storyboard manifest (workflow_mode: "TDD" | "GRILL" | "AUTONOMOUS_DUAL_EVOLVE")
python scripts/audit_single_slide_step.py --init-storyboard storyboard.json --manifest slide_manifest.json

# Mode 1 (TDD): Record Tutor Station cognitive capsule for slide K
python scripts/audit_single_slide_step.py --record-tdd-capsule tdd_capsule_01.json --slide-index 1 --manifest slide_manifest.json

# Mode 2 (GRILL): Record Grill-First + Teach-on-Miss + Re-Grill capsule for slide K
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
