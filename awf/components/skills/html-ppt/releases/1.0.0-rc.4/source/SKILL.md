---
name: html-ppt
description: Build, audit, and evolve 16:9 scientific interactive HTML presentations (AWF HTML-PPT / SciSlide) under a strictly 1-Slide-Per-Step micro-step architecture (`max_slides_generated_per_step == 1`) and 1-Hop Slide Topological Lock (`slide_manifest.json`), gated by `skill.design-anti-goodhart@1.0.0-rc.2` (AWF DesignAG, 18 Automated Design Gates D1-D18 + 7 Redlines R1-R7 + Dual Quantitative Rubrics) and `skill.anti-goodhart-verification@3.4.0-rc.1` (AWF Guard). Use whenever creating, revising, or auditing HTML slide decks, scientific paper walkthroughs, or teaching presentations.
---

# AWF HTML-PPT V2 (`skill.html-ppt@1.0.0-rc.4` — Strictly 1-Slide-Per-Step Atomic Micro-Step Engine, 1-Hop `slide_manifest.json` Topological Lock, `AWF DesignAG` 18-Gate Enforcement & Darwinian Escape-to-Gate Evolution)

An anti-Goodhart, self-evolving scientific HTML presentation authoring and verification engine. To prevent mid-deck attention collapse, template cloning, unrendered LaTeX leaks, overlapping/clipped DOM boxes, and pure-text laziness (`V0 = 0.30` cap), **AWF HTML-PPT V2 strictly forbids generating multiple slides in a single step**. Every presentation is built through a **4-Stage Pipeline** where **Stage 3 generates, renders, and verifies strictly ONE slide (`slides/slide_XX.html`) per micro-step** before unlocking the next slide in `slide_manifest.json`.

---

## 1. Non-Negotiable Anti-Goodhart Laws

1. **Strictly 1 Slide Per Step (`max_slides_generated_per_step == 1`)**:
   - Never generate a monolithic multi-slide HTML file in one shot, and never batch 2 or more slides in a single step.
   - Each slide lives in its own isolated module (`slides/slide_01.html`, `slides/slide_02.html`, ...) and is individually audited via [`scripts/audit_single_slide_step.py`](scripts/audit_single_slide_step.py) against `skill.design-anti-goodhart@1.0.0-rc.2` (`AWF DesignAG`).
2. **1-Hop Slide Topological Lock (`unverified_slide_hop_distance == 1`)**:
   - Tracked in `slide_manifest.json`. At initialization, only `slide_01` is `"UNLOCKED"`; `slide_02..N` are `"LOCKED"`.
   - `slide_{k+1}` is unlocked **if and only if** `slide_k` has passed all per-slide DesignAG gates (`D1`–`D12`, `D15`, `D16`) with zero Redlines (`R1`–`R7`) and its SHA-256 receipt is recorded as `"status": "PASS"` in `slide_manifest.json`.
3. **Multiplicative Visual Modality Cap ($A_i = w_i \times C_{\text{clarity}} \times V_{\text{visual}}$)**:
   - Pure text (`V0 = 0.30`) is mathematically capped at 30% of the score. Mechanism and data slides must use clean cropped paper figures / accurate SVG diagrams (`V2 = 0.80`) or physics-coupled interactive widgets / multi-step SVG animations (`V3 = 1.00`).

---

## 2. Four-Stage Execution Workflow

### Stage 1: Storyboard & Causal-Chain Contract (`storyboard.json` $\to$ Gates `D13, D14, D16`)
Before writing a single line of HTML:
1. Author `storyboard.json` defining all $N$ slides ($N \ge 15$ for full paper walkthroughs):
   - Concrete scientific object/claim title (no meta-instructional titles like *"先把研究对象说清楚"* or prompt tags `P1/L2`);
   - Narrative role (`macro_background` $\to$ `degradation_bottleneck` $\to$ `prior_art_ceiling` $\to$ `foreshadowing` $\to$ `core_mechanism_why_chain` $\to$ `controlled_comparison` $\to$ `tradeoff_and_quiz`);
   - Layout archetype (`layout_archetype`: $\le 2$ consecutive identical layouts, deck Shannon entropy $H \ge 1.4\text{ bits}$);
   - Target visual modality (`V2` or `V3`) and explicit figure/sub-panel IDs (`Fig. 1a`, `Fig. 2b`).
2. Run:
   ```bash
   python scripts/audit_single_slide_step.py --init-storyboard storyboard.json --manifest slide_manifest.json
   ```
   This validates the storyboard through `DesignAG` (`D13`, `D14`, `D16`) and unlocks **only `slide_01`**.

### Stage 2: Paper Figure Sub-Panel Cropping & Visual Asset Pre-Audit (Gates `D5, D9, D10, D11`)
- Crop original paper sub-panels (`<= 2` sub-panels per image card) and verify via `DesignAG` (`D9`, `D10`):
  - Aspect ratio matches target slot ($\le 2\%$ distortion; never stuff wide banner figures into narrow vertical slots);
  - Blank margin ratio $\le 18\%$ and border-sliced ink ratio $\le 2.5\%$ (no sliced half-captions or cut-off axis labels);
  - Zero AI text-to-image decorative mechanism fakes (`R4`) and zero `NotebookLM` / AI watermarks (`D5`).

### Stage 3: Strictly 1-Slide-Per-Step Sandbox Implementation & DOM Bounding-Box Probe (Gates `D1`–`D12, D15, D16`)
For each slide $k = 1, 2, \dots, N$ **one by one**:
1. Verify in `slide_manifest.json` that `slide_k` has `"status": "UNLOCKED"` (and `slide_{k-1}` is `"PASS"`).
2. Write **only** `slides/slide_{k:02d}.html` (16:9 `1920x1080` viewport):
   - Load KaTeX/MathJax; zero raw `$` or `\frac` leaks (`D1`/`R1`);
   - Balanced HTML tags and zero `3+1` / `4+1` orphan grid rows (`D2`/`R2`);
   - Natural academic copywriting: $\le 3$ corner quotes `「」`, zero clichés (*赋能/抓手/闭环*), zero self-praise (*这很深刻*) (`D3`/`R5`);
   - Define every technical acronym visibly on first use and attach inline `popover`/`tooltip` definitions (`D4`);
   - Zero cartoon emojis (`🎯💡🚀`) and zero unanchored fake CSS progress bars (`D5`);
   - Default-hidden speaker notes/teleprompter and body font $\ge 18\text{ px}$ (`D6`/`R6`);
   - Explicit directional reading anchors in body text referencing the exact cropped sub-panel (`D11`/`R3`);
   - If interactive/animated (`V3`), bind all `@keyframes` to active DOM nodes and couple sliders to real physical equations (`D15`).
3. Measure `1920x1080` DOM bounding boxes $(x,y,w,h)$ and run the single-slide gatekeeper:
   ```bash
   python scripts/audit_single_slide_step.py --audit-slide slides/slide_01.html --slide-index 1 --manifest slide_manifest.json
   ```
   - Checks `D7` (zero sibling overlap $\text{IoU} \le 0.005$, zero scroll clipping), `D8` (canvas coverage $\in [35\%, 80\%]$, vertical center-of-mass $Y_{\text{cm}} \in [0.35, 0.65]$), and `D12` (WCAG contrast $\ge 4.5:1$).
   - **If `FAIL`**: Fix `slides/slide_{k:02d}.html` immediately and re-run `--audit-slide`. **Never touch `slide_{k+1}` until `slide_k` prints `PASS`!**
   - **If `PASS`**: `slide_manifest.json` records `slide_k`'s SHA-256 receipt and unlocks `slide_{k+1}`.

### Stage 4: Read-Only Red Subagent Visual Audit, Dual-Rubric Scoring & Final Deck Assembly (Gates `D17, D18`)
Once all $N$ slides hold `"status": "PASS"` in `slide_manifest.json`:
1. Render `1920x1080` PNG screenshots for all slides and invoke a **read-only Red Visual Critic subagent (`research` subagent)** to inspect every rendered PNG against `R1`–`R7` and the 39 historical defect patterns (`D18`).
2. Assemble the verified single-slide modules into the final navigable deck and compute the Dual-Rubric score (`D17` $\ge 85/100$ on both Optoelectronic v3 and Supermolecule 5-Dim rubrics):
   ```bash
   python scripts/audit_single_slide_step.py --assemble-deck --manifest slide_manifest.json --output deck.html
   ```
3. Report **both** Windows native path (`Z:\path\to\deck.html`) and browser URL (`file:///Z:/path/to/deck.html`).

---

## 3. Darwinian Escape-to-Gate Evolution Protocol (越用越强自进化飞轮)

Whenever the user identifies a new visual, layout, or pedagogical flaw $X$ that escaped current gates:
1. **Capture Escape Fixture**: Save the offending slide snippet/metrics as a permanent negative adversarial test case in `awf_design_ag_selftest_suite.py`.
2. **Synthesize New Deterministic Gate**: Add or tighten the mathematical/DOM detector in `awf_design_anti_goodhart_gates.py` (never merely append prose advice to Markdown).
3. **Verify Red-Green Separation**: Confirm `--self-test` catches the new negative fixture (`FAIL`) while passing the gold-standard positive bundle (`PASS`), and confirm `--audit-self` reports `0` AST violations.
4. **Release & Kernel-Lock (`rc.X+1` + `chattr +i`)**: Register the new `skill.design-anti-goodhart@1.0.0-rc.X+1` and `skill.html-ppt@1.0.0-rc.Y+1` releases, run `ssh root@node01 "/usr/local/sbin/awf-immutable-lock"`, and verify via `verify.py`.

---

## 4. Preserved References & Templates

- Concrete system semantics & title rules: [content-and-evidence.md](references/content-and-evidence.md)
- Visual & browser interaction checklist: [visual-and-interaction-review.md](references/visual-and-interaction-review.md)
- Base 16:9 slide scaffold: [slide-template.html](assets/slide-template.html)
