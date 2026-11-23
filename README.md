# AWF Anti-Goodhart Universal Input-Onion-Output Suite (`AWF DesignAG` + `AWF Guard` + `AWF HTML-PPT` + `AWF Tutor` + `AWF SciWord` + `AWF FigPPT`)

Public, portable distribution of the **Agent Workflow Foundry (AWF)** 9-Role Universal Input-Background-Understanding-Output Onion Control Bus (`BackgroundSynthesizer + EvidenceIngest` $\to$ `AWF Tutor / Onion Peeling + DevilReviewer` $\to$ `OmniArtifactHub` [driving `AWF HTML-PPT`, `AWF SciWord`, and `AWF FigPPT`] $\to$ `AWF DesignAG` 18-Gate + `AWF Guard` 74-Subcheck Verification):

1. **`AWF DesignAG` (`design-anti-goodhart@1.0.0-rc.24` / `skill.design-anti-goodhart@1.0.0-rc.24`)**:
   - **18 Automated Design & Pedagogical Gates (`D1`–`D18`)** and **7 Redlines (`R1`–`R7`)**, including:
     - **Canvas-vs-Dialogue Anti-Dilution, 3-Step Wittgenstein Ladder, 7-Element Anatomy & `Teach-on-Miss` Re-Grill Closure (`design_tutor_pedagogy_guard.py` across `D16`)**: Blocks hollow 1-sentence analogies (`len >= 10` loophole) by enforcing explicit `Bridge -> Deconstruct (breakdown semantics) -> Replace`, optional/required 7-element methodological anatomy with explicit mathematical operators, and mandatory `user_missed_or_uncertain` -> substantive Wittgenstein `Teach-on-Miss` explanation + deductive isomorphic re-grill prompts (banning *"听懂了吗？"* rubber-stamps);
     - **2x Large Typography & `<=260`-Char Low-Density Budget (`design_viewport_and_redundancy.py` + `design_lossless_popover_and_split.py` across `D4`/`D6`/`D16`)**: Enforces `>=32px` inline `<svg>` & visible HTML floors, `>=42px` `1920x1080` card body copy (`>=36px` on `1600x900`), `>=56px` concise slide titles, `1` visible `<p>` per card, `<=260` visible canvas characters per slide (`>60%` density reduction), and zero information loss via `SPLIT_SLIDE` (`.topo-breadcrumb`) + `CLICKABLE_POPOVER` (`.detail-trigger[data-detail-id]` backed by verified `<template>` payloads and `lossless_split_and_popover_ledger`);
     - **Intra-Slide Semantic Coherence, De-Ballasting & Outsider Anti-Collusion Blind Reader (`design_semantic_coherence.py` across `D3`/`D4`/`D6`/`D8`/`D16`/`D18`)**: Blocks bare verbless noun-label card strips, unanchored bottom 3-card ballast strips, and `>30%` deck-wide bottom-grid cloning; enforces pre-generation `intra_slide_semantic_tree` parent-child anchors, Anti-Collusion Zero-Context Blind Reader topological reconstruction, and explicit outsider macro-onboarding verification (`opening_macro_background_established: true`, `outsider_onboarding_gaps: []`, and zero premature paper-recipe tokens on opening slides);
     - **Beyond-PDF 4-Rung Domain Background Bridge & HTML Onboarding Fidelity (`verify_domain_background_bridge_capsule` + `audit_slide_html_background_onboarding_fidelity` in `D13` & `D16`)**: Enforces Role 0 (`BackgroundSynthesizer & AudienceTranslator`), >=3 `V2/V3` custom-SVG/interactive opening background slides on full-paper decks, HTML-level pre-background paper-recipe leak prevention (`3-PMPCl`, `3-N吡啶`, `哌嗪环`), opening `Rung 1` macro-stakes HTML grounding (blocking premature sub-domain band/quantum formalism jumps), plain-language jargon analogies, Briefing-First `FOUNDATION_INTUITION_BUILD` grills, and zero leaked framework meta-jargon (`D3` / `D13` / `D16`);
     - **Unread-PDF AI Value-vs-Routine Triage & Intent/JIT Emphasis Guard (`verify_ai_value_triage` + `verify_unread_pdf_emphasis_alignment` in `D16`)**: Blocks forcing unread-PDF users to blindly guess unfamiliar paper module names (`"以下哪些模块需要作为重头戏展开讲"`), requiring upfront value/routine disclosure plus Reader-Intent lenses or `JIT_DURING_GRILL` dynamic discovery;
     - **Unconditional Zero Slide-Count MCQ Law (`verify_logic_driven_slide_count_policy` in `D16`)**: Unconditionally eliminates `total_slides_mcq` ("页数怎么选") and preset fixed page totals (`planned_total_slides` / `elastic_slide_range`)—total slides emerge purely from logical closure and cognitive need (`UNBOUNDED_FLOW_DRIVEN`);
     - **Hierarchical Onion Peeling (`verify_onion_peeling_capsule`)**: Layer 0 Coarse Trunks $\to$ Layer 1..K Trunk Sub-Framework (with `trunk_context_preview`) $\to$ Leaf Slide / Section / Figure Panel;
     - **Universal I/O Onion Control Bus (`verify_universal_io_onion_bus_capsule`)**: Enforces Role 0 (`domain_background_ledger`), Role 1 (`EvidenceIngest` / `evidence_ingest_ledger`), Role 2 (`DevilReviewer` / `devil_reviewer_capsule`), and Role 3 (`OmniArtifactHub` / `output_artifact_targets` $\subseteq \{\text{HTML\_PPT}, \text{SCI\_WORD}, \text{FIG\_PPTX}\}$);
     - **Tri-Mode Execution in `D16` (`TDD`, `GRILL`, `AUTONOMOUS_DUAL_EVOLVE`)** + **Strict 1-Unit-Per-Step & 1-Hop Topological Lock**.
2. **`AWF HTML-PPT V3` (`html-ppt@1.0.0-rc.23` / `skill.html-ppt@1.0.0-rc.26`)**:
   - **2x Large Typography + `<=260`-Char Low-Density + Lossless Multi-Slide Split (`SPLIT_SLIDE` + `.topo-breadcrumb`) & Clickable Detail Popovers (`CLICKABLE_POPOVER` + `.detail-trigger`) + Pre-Background Recipe Leak & Rung-1 HTML Grounding (`D13`) + Outsider Anti-Collusion Blind Reader (`--verify-blind-reader`) + Tri-Mode 1-Slide-Per-Step Enforcer (`audit_single_slide_step.py`, 23 checks)**: Ships [`references/background-synthesis-and-onboarding.md`](awf/components/skills/html-ppt/releases/1.0.0-rc.26/source/references/background-synthesis-and-onboarding.md) and [`assets/slide-template.html`](awf/components/skills/html-ppt/releases/1.0.0-rc.26/source/assets/slide-template.html).
3. **`AWF SciWord` (`scientific-report-authoring@1.0.0-rc.13` / `skill.edit-scientific-article@1.0.0-rc.10` + `skill.build-scientific-docx@1.0.0-rc.12`)**:
   - **Scientific Paper & Report Authoring (`SCI_WORD` Output Channel)**: Driven by the same Onion Peeling tree and `EvidenceIngest` ledger to generate/revise scientific manuscripts and native-OMML Word (`.docx`) documents 1 section per step.
4. **`AWF FigPPT / SciFig` (`editable-figure-pptx@1.0.0-rc.2` / `skill.build-editable-figure-pptx@1.0.0-rc.2`)**:
   - **Editable Scientific Composite Figure Deck (`FIG_PPTX` Output Channel)**: Decomposes and builds publication-grade widescreen editable PowerPoint (`.pptx`) figures where 100% of labels, ticks, legends, and badges are native OpenXML shapes.
5. **`AWF Guard` (`anti-goodhart-verification@3.7.0-rc.8` / `skill.anti-goodhart-verification@3.7.0-rc.8`)**:
   - **14 Orthogonal Universal Slots $\times$ 74 Automated Code & Scientific Computing Anti-Goodhart Sub-Checks (`G1`–`G7`) + Recursive Co-Located Self-Hosting Dogfood Audit (`--audit-self`)**.
6. **`AWF Tutor V16` (`adaptive-interactive-tutor@1.0.0-rc.37` / `skill.adaptive-interactive-tutor@1.0.0-rc.37`)**:
   - Canvas-vs-Dialogue Anti-Dilution Law + Restored `Core Pedagogical & Co-Design Toolkit` (`Bridge -> Deconstruct -> Replace` 3-Step Wittgenstein Ladder, `Teach-on-Miss` + Isomorphic Re-Grill, Active Visual Cloze `[ ? ]`, POE, Vygotsky ZPD), 2x Large Typography & Lossless Split/Popover Presentation Co-Design, Pre-Background Recipe Leak & Rung-1 HTML Grounding, Intra-Slide Semantic Coherence & Outsider Anti-Collusion Blind Reader, Beyond-PDF 4-Rung Domain Background Onboarding, Unread-PDF Value Triage & Reader-Intent / JIT Grill Emphasis, Unconditional Zero Slide-Count MCQ, Scale-Adaptive Fractal Curriculum (`Chapter -> Station -> 3-Gate Micro-Loop`), 7-Element Methodological Anatomy, Hierarchical Onion Peeling, and Foundation-First / Briefing-First Tri-Mode Co-Design (`TDD`, `GRILL`, `AUTONOMOUS_DUAL_EVOLVE`).

## Included Locked Closure

- `skill.design-anti-goodhart@1.0.0-rc.24` (`awf/components/skills/design-anti-goodhart/releases/1.0.0-rc.24/source/`, plus immutable `1.0.0-rc.13`–`1.0.0-rc.23`)
- `skill.html-ppt@1.0.0-rc.26` (`awf/components/skills/html-ppt/releases/1.0.0-rc.26/source/`, plus immutable `1.0.0-rc.15`–`1.0.0-rc.25`)
- `skill.edit-scientific-article@1.0.0-rc.10` (`awf/components/skills/edit-scientific-article/releases/1.0.0-rc.10/source/`)
- `skill.build-scientific-docx@1.0.0-rc.12` (`awf/components/skills/build-scientific-docx/releases/1.0.0-rc.12/source/`)
- `skill.build-editable-figure-pptx@1.0.0-rc.2` (`awf/components/skills/build-editable-figure-pptx/releases/1.0.0-rc.2/source/`)
- `skill.anti-goodhart-verification@3.7.0-rc.8` (`awf/components/skills/anti-goodhart-verification/releases/3.7.0-rc.8/source/`)
- `skill.anti-goodhart-verification@3.7.0-rc.7` (also shipped; DesignAG, Tutor, and HTML-PPT workflow locks pin this release)
- `skill.adaptive-interactive-tutor@1.0.0-rc.37` (`awf/components/skills/adaptive-interactive-tutor/releases/1.0.0-rc.37/source/`, plus immutable `1.0.0-rc.26`–`1.0.0-rc.36`)
- Workflow descriptors & exact `versions.lock` files under `awf/workflows/`
- Mergeable registry fragment at `awf/registry.fragment.json`

## Quick Verification

```bash
# 1. Verify full repository manifest, hashes, locks, AST syntax, and run all 74 + 18 + 23-Check self-tests & self-audits
python verify.py

# 2. Run AWF DesignAG 18-gate positive/negative self-test & self-hosting audit directly
python -B awf/components/skills/design-anti-goodhart/releases/1.0.0-rc.24/source/scripts/awf_design_anti_goodhart_gates.py --self-test
python -B awf/components/skills/design-anti-goodhart/releases/1.0.0-rc.24/source/scripts/awf_design_anti_goodhart_gates.py --audit-self

# 3. Run AWF HTML-PPT V3 2x Typography, Lossless Split/Popover, Macro-Onboarding Fidelity & Tri-Mode (23 checks) self-test directly
python -B awf/components/skills/html-ppt/releases/1.0.0-rc.26/source/scripts/audit_single_slide_step.py --self-test

# 4. Run AWF Guard 14-Slot x 74-Subcheck self-test & recursive self-hosting audit directly
python -B awf/components/skills/anti-goodhart-verification/releases/3.7.0-rc.8/source/scripts/awf_universal_anti_goodhart_gates.py --self-test
python -B awf/components/skills/anti-goodhart-verification/releases/3.7.0-rc.8/source/scripts/awf_universal_anti_goodhart_gates.py --audit-self
```
