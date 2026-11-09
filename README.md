# AWF Anti-Goodhart Universal Input-Onion-Output Suite (`AWF DesignAG` + `AWF Guard` + `AWF HTML-PPT` + `AWF Tutor` + `AWF SciWord` + `AWF FigPPT`)

Public, portable distribution of the **Agent Workflow Foundry (AWF)** 8-Role Universal Input-Understanding-Output Onion Control Bus (`EvidenceIngest` $\to$ `AWF Tutor / Onion Peeling + DevilReviewer` $\to$ `OmniArtifactHub` [driving `AWF HTML-PPT`, `AWF SciWord`, and `AWF FigPPT`] $\to$ `AWF DesignAG` 18-Gate + `AWF Guard` 73-Gate Verification):

1. **`AWF DesignAG` (`design-anti-goodhart@1.0.0-rc.11` / `skill.design-anti-goodhart@1.0.0-rc.11`)**:
   - **18 Automated Design & Pedagogical Gates (`D1`–`D18`)** and **7 Redlines (`R1`–`R7`)**, including:
     - **Hierarchical Onion Peeling (`verify_onion_peeling_capsule`)**: Layer 0 Coarse Trunks $\to$ Layer 1..K Trunk Sub-Framework $\to$ Leaf Slide / Section / Figure Panel;
     - **Universal I/O Onion Control Bus (`verify_universal_io_onion_bus_capsule`)**: Enforces Role 1 (`EvidenceIngest` / `evidence_ingest_ledger`), Role 2 (`DevilReviewer` / `devil_advocate_review`), and Role 3 (`OmniArtifactHub` / `cross_artifact_targets` $\subseteq \{\text{HTML\_PPT}, \text{SCI\_WORD}, \text{FIG\_PPTX}\}$);
     - **Tri-Mode Execution in `D16` (`TDD`, `GRILL`, `AUTONOMOUS_DUAL_EVOLVE`)** + **Strict 1-Unit-Per-Step & 1-Hop Topological Lock**.
2. **`AWF HTML-PPT V3` (`html-ppt@1.0.0-rc.10` / `skill.html-ppt@1.0.0-rc.13`)**:
   - **Tri-Mode 1-Slide-Per-Step & Cross-Artifact Enforcer (`audit_single_slide_step.py`)**: Supports `--peel-onion-trunk`, `--mutate-storyboard` (`UNBOUNDED_FLOW_DRIVEN` / `"不限"`), `--record-cross-artifact-unit` (`SCI_WORD` & `FIG_PPTX`), `--record-tdd-capsule`, `--record-grill-capsule`, and `--apply-feedback-dual-upgrade`.
3. **`AWF SciWord` (`scientific-report-authoring@1.0.0-rc.13` / `skill.edit-scientific-article@1.0.0-rc.10` + `skill.build-scientific-docx@1.0.0-rc.12`)**:
   - **Scientific Paper & Report Authoring (`SCI_WORD` Output Channel)**: Driven by the same Onion Peeling tree and `EvidenceIngest` ledger to generate/revise scientific manuscripts and native-OMML Word (`.docx`) documents 1 section per step.
4. **`AWF FigPPT / SciFig` (`editable-figure-pptx@1.0.0-rc.2` / `skill.build-editable-figure-pptx@1.0.0-rc.2`)**:
   - **Editable Scientific Composite Figure Deck (`FIG_PPTX` Output Channel)**: Decomposes and builds publication-grade widescreen editable PowerPoint (`.pptx`) figures where 100% of labels, ticks, legends, and badges are native OpenXML shapes.
5. **`AWF Guard` (`anti-goodhart-verification@3.7.0-rc.1` / `skill.anti-goodhart-verification@3.7.0-rc.1`)**:
   - **14 Orthogonal Universal Slots $\times$ 74 Automated Code & Scientific Computing Anti-Goodhart Sub-Checks (`G1`–`G7`) + Recursive Co-Located Self-Hosting Dogfood Audit (`--audit-self`)**.
6. **`AWF Tutor V16` (`adaptive-interactive-tutor@1.0.0-rc.24` / `skill.adaptive-interactive-tutor@1.0.0-rc.24`)**:
   - Scale-Adaptive Fractal Curriculum (`Chapter -> Station -> 3-Gate Micro-Loop`), 7-Element Methodological Anatomy, Hierarchical Onion Peeling, and Tri-Mode Co-Design (`TDD`, `GRILL`, `AUTONOMOUS_DUAL_EVOLVE`).

## Included Locked Closure

- `skill.design-anti-goodhart@1.0.0-rc.11` (`awf/components/skills/design-anti-goodhart/releases/1.0.0-rc.11/source/`)
- `skill.html-ppt@1.0.0-rc.13` (`awf/components/skills/html-ppt/releases/1.0.0-rc.13/source/`)
- `skill.edit-scientific-article@1.0.0-rc.10` (`awf/components/skills/edit-scientific-article/releases/1.0.0-rc.10/source/`)
- `skill.build-scientific-docx@1.0.0-rc.12` (`awf/components/skills/build-scientific-docx/releases/1.0.0-rc.12/source/`)
- `skill.build-editable-figure-pptx@1.0.0-rc.2` (`awf/components/skills/build-editable-figure-pptx/releases/1.0.0-rc.2/source/`)
- `skill.anti-goodhart-verification@3.7.0-rc.1` (`awf/components/skills/anti-goodhart-verification/releases/3.7.0-rc.1/source/`)
- `skill.adaptive-interactive-tutor@1.0.0-rc.24` (`awf/components/skills/adaptive-interactive-tutor/releases/1.0.0-rc.24/source/`)
- Workflow descriptors & exact `versions.lock` files under `awf/workflows/`
- Mergeable registry fragment at `awf/registry.fragment.json`

## Quick Verification

```bash
# 1. Verify full repository manifest, hashes, locks, AST syntax, and run all 74 + 18 + 12-Check Universal Onion Bus self-tests & self-audits
python verify.py

# 2. Run AWF DesignAG 18-gate positive/negative self-test & self-hosting audit directly
python awf/components/skills/design-anti-goodhart/releases/1.0.0-rc.11/source/scripts/awf_design_anti_goodhart_gates.py --self-test
python awf/components/skills/design-anti-goodhart/releases/1.0.0-rc.11/source/scripts/awf_design_anti_goodhart_gates.py --audit-self

# 3. Run AWF HTML-PPT V3 Universal Onion Bus & Tri-Mode (12 checks) self-test directly
python awf/components/skills/html-ppt/releases/1.0.0-rc.13/source/scripts/audit_single_slide_step.py --self-test

# 4. Run AWF Guard 14-Slot x 74-Subcheck self-test & recursive self-hosting audit directly
python awf/components/skills/anti-goodhart-verification/releases/3.7.0-rc.1/source/scripts/awf_universal_anti_goodhart_gates.py --self-test
python awf/components/skills/anti-goodhart-verification/releases/3.7.0-rc.1/source/scripts/awf_universal_anti_goodhart_gates.py --audit-self
```
