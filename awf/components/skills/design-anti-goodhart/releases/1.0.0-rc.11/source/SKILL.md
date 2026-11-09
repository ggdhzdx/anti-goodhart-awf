---
name: design-anti-goodhart
description: Visual, Pedagogical & Slide-Deck Anti-Goodhart Verification and Dual-Rubric Scoring Engine (AWF DesignAG / DesignGuard / 设计门禁 / PPT防偷懒) with 18 Automated Design Gates (D1-D18), 7 Redline Circuit-Breakers (R1-R7), Multiplicative Clarity-by-Visual-Modality Scoring (capping V0 pure-text slides at 30%), DOM/Bounding-Box Zero-Overlap & Zero-Clipping Probes, Aspect-Ratio & Sub-Panel Crop Purity Guards, Anti-AI-MetaTone Copywriting Scanners, Acronym First-Use Visible Definition & Popover Guards, Interactive Physics Linkage Auditors, and Multimodal Red-Blue Visual Adversarial Review. Use whenever building, auditing, scoring, or reviewing HTML presentations (HTML-PPT), editable scientific PowerPoint decks (PPTX), or visual teaching slides.
---

# AWF DesignAG: Visual, Pedagogical & Presentation Anti-Goodhart Engine (`skill.design-anti-goodhart@1.0.0-rc.11`)

## 1. Canonical Locations & Co-Located Rubric Authorities

- **AWF Authoritative Source (`1.0.0-rc.11`)**:
  - Skill Spec: `Z:\agent_workflows\components\skills\design-anti-goodhart\releases\1.0.0-rc.11\source\SKILL.md`
  - Automated 18-Gate & Dual-Rubric Engine: `Z:\agent_workflows\components\skills\design-anti-goodhart\releases\1.0.0-rc.11\source\scripts\awf_design_anti_goodhart_gates.py`
  - 18-Gate Positive/Negative Self-Test Suite: `Z:\agent_workflows\components\skills\design-anti-goodhart\releases\1.0.0-rc.11\source\scripts\awf_design_ag_selftest_suite.py`
- **Co-Located Authoritative Rubric References**:
  1. **Rubric Mode 1 — Deep Scientific Literature / Optoelectronic HTML-PPT Rubric v3 (`100 pts + R1..R7 up to -15 pts`)**:
     [`references/01_optoelectronic_scoring_criteria_v3.md`](references/01_optoelectronic_scoring_criteria_v3.md) (5 Categories `A–E`, 17 Scoring Items, 15 Domain Knowledge Anchors with $A_i = \text{Weight}_i \times \text{Clarity} \times \text{VisualCoeff}$, derived from 39 real user feedback items across 13 models).
  2. **Rubric Mode 2 — Pedagogical / Popular-Science / Supramolecular 5-Dimension Rubric (`100 pts`)**:
     [`references/02_supermolecule_SCORING_CRITERIA_5dim.md`](references/02_supermolecule_SCORING_CRITERIA_5dim.md) (5 Core Dimensions: Readability & Layout `25`, Narrative Logic & Foreshadowing `20`, Content Richness & Scientific Accuracy `20`, Visual Structure & Diagram Fidelity `20`, Interactive & Dynamic Physics Design `15`).
- **Two-Layer Collaboration with `AWF Guard` (`skill.anti-goodhart-verification@3.7.0-rc.1`)**:
  - **Layer 1 (Shared Core Foundation)**: Reuses `AWF Guard` for general AST anti-shortcut checks, cryptographic SHA256 harness locks (`G6e`), command-receipt freshness (`G6c`), micro-step topological locking (`G6o`), and Red-Blue adversarial payoff decoupling (`G7h`).
  - **Layer 2 (`DesignAG` Domain Capsule)**: Enforces the **18 Presentation, Visual, Geometric, Optical & Pedagogical Anti-Goodhart Gates (`D1`–`D18`)** and **7 Redlines (`R1`–`R7`)** specific to HTML-PPT, PowerPoint (`.pptx`), and scientific visual communication.

---

## 2. Why Presentation & Design Tasks Suffer from Severe Goodhart Collapse

When an LLM is given a textual "PPT / Design Standard", it naturally exploits six low-effort shortcuts (optimizing the surface proxy while destroying visual and cognitive quality):
1. **Pure-Text Card / Arrow-Box Substitution ($V_0$ Shortcut)**: Explaining physical or chemical mechanisms (e.g., TPA/TTA, PEP anticrossing, 18-crown-6 coordination) using only text boxes or `Step 1 -> Step 2` text arrows instead of cropped original paper figures or accurate structural diagrams.
2. **Unrendered LaTeX Source Leakage & Broken DOM Nesting (`R1` / `R2`)**: Writing raw `$S_0$`, `\frac{k_r}{k_{r,0}}`, `$\text{Ba}^{2+}$` in HTML without loading KaTeX/MathJax, or closing a `<div>` with `</p></div>` so a 3-column grid collapses into nested Russian-doll cards.
3. **AI Marketing Clichés, Corner-Quote Abuse & Preachy Meta-Instructional Tone (`C1` / `R5`)**: Using self-media titles (*“五个问题，看懂这篇工作”*), overusing `「抽走」「烧坏」「焊在一起」`, or printing prompt instructions/disclaimers directly on slides (*“先说比较对象，再说提升倍数”*, *“本汇报复述原论文结果…”*, *“13页实验原理”*).
4. **Composite Multi-Panel Figure Dumping vs. Blind PDF Slicing (`B2` / `D1`)**: Either dumping an unsplit 12-panel *Nature* figure onto a half-slide where labels are microscopic (`hy-4`), or blindly slicing PDF rectangles that chop axis titles in half, leave 20%–40% blank margins, or bleed neighboring figure text into the corner (`qwen-3.8`), or stuffing a `2.5:1` wide banner figure into a narrow vertical column.
5. **Hidden Definitions in Speaker Notes & Standalone Glossary Walls (`C2` / `R6`)**: Hiding definitions of `TPA`, `TTA`, `LT90`, `SPP`, `PF` inside hidden `<aside class="notes">` and dropping the raw acronym onto visible slides later; or inserting a jarring 12-grid glossary wall slide mid-deck instead of inline click/hover popovers; or leaving `#teleprompter-panel` permanently expanded on screen (`R6`).
6. **Hollow Animations, Fake Progress Bars & Cartoon Emoji Pollution (`B4` / `D2` / `E1`)**: Defining `@keyframes` in `<style>` without attaching them to elements (`gemini-3.8flash`), drawing fabricated `100% / 78% / 56%` progress bars instead of real experimental dispersion/lifetime curves (`deepseek`), drawing 1D lines without Y-axes (`R3`), or placing cartoon Emojis (`🐢, 🪞, 🗂️, 🧱, 🌀`) on academic slides (`doubao`).

---

## 3. The 18 Automated DesignAG Gates (`D1`–`D18`) Across 4 Pillars

### Pillar I: Static HTML/DOM/CSS, Copywriting & Acronym $-\infty$ Circuit-Breakers (`D1`–`D6`)

| Gate ID | Gate Name | Target Defect & Rubric Mapping | Enforcement Mechanism |
| :--- | :--- | :--- | :--- |
| **`D1`** | `D1_Zero_Unrendered_LaTeX_Source_Leak` | **Redline `R1`** ($-5$ pts / hard fail): Raw `$...$`, `\frac`, `\tau`, `\text{`, `\propto`, `\Omega` visible on screen | Scans visible DOM text for LaTeX tokens (`\frac`, `\text{`, `\mu`, `\tau`, `\propto`, unescaped `$...$`) and verifies that MathJax/KaTeX scripts + auto-render hooks are present if LaTeX syntax is used; prefers native `<sub>`/`<sup>` + Unicode math symbols. |
| **`D2`** | `D2_HTML_Tag_Balance_And_Grid_Orphan_Guard` | **Redline `R2`** ($-2$/slide) & Supermolecule `1️⃣`: Mismatched `<div>...</p></div>` card collapse & `3+1` grid orphan rows | Parses slide HTML with a strict stack-based tag balancer to catch cross-tag closing errors and audits CSS Grid/Flex card counts against column templates (blocking 4 cards in a 3-column grid producing a `3+1` orphan row). |
| **`D3`** | `D3_Natural_Academic_Copywriting_No_AI_MetaTone` | **`C1` (6 pts) & Redline `R5` ($-2$/hit)**: Marketing clichés, `「...」` abuse, meta-preachy tone, prompt leakage | Scans titles/subtitles/body for: (1) corner-quote metaphor abuse ($\ge 3$ `「...」` on action verbs), (2) WeChat cliché patterns (*“X个问题看懂”*, *“破局思路”*, *“寿命杀手”*), (3) AI meta-instructional/disclaimer tone (*“先说…再说…”*, *“本汇报复述原论文结果”*, *“属于作者发表时的结果”*), (4) subjectless number titles, and (5) raw prompt page-number leakage (*“13页实验原理”*, *“高中生也能看懂的第9页”*). |
| **`D4`** | `D4_Acronym_FirstUse_Visible_Definition_And_Popover_Guard` | **`C2` (5 pts)**: Acronyms hidden in `<aside class="notes">`, undefined symbols (`m > 1`), or disruptive glossary walls | Tracks first slide index where each domain acronym/symbol (`PHOLED`, `TPA`, `TTA`, `LT90`, `PF`, `ODoS`, `SPP`, `PEP`, `EQE`, `CIE`, `SHG`, etc.) appears in **visible** text vs. first visible definition (`全称 / 定义 / =`), penalizes definitions hidden only in `.notes`, penalizes standalone glossary-wall slides in the main flow, and rewards inline click/hover popovers (`data-popover`, `tooltip`, `<details>`). |
| **`D5`** | `D5_Anti_Emoji_FakeProgressBar_And_AIWatermark_Guard` | **`D2` (3 pts), `B4` (4 pts) & Redline `R4`**: Cartoon Emojis (`🐢🪞🗂️🧱`), fake subjective progress bars, AI sci-fi wallpaper | Scans for blacklisted cartoon Emojis in scientific decks, detects subjective percentage bars (`100% 最强 / 78% 强`) masquerading as experimental data without axis ticks, and flags decorative AI sci-fi background images (`R4`) or residual AI watermarks. |
| **`D6`** | `D6_Teleprompter_Hidden_And_Slide_Density_Cadence_Guard` | **Redline `R6` ($-2$) & `C3` (5 pts)**: Always-on teleprompter, `.slide { overflow-y: auto }` text walls, $<16\text{px}$ font, or $>25\%$ filler slides | Verifies that `#teleprompter-panel` / `.notes` are `display: none` or collapsed by default (`R6`), `.slide` does not rely on vertical scrollbars to hold walls of text, body font size $\ge 16\text{px}$, total slide count for full-paper decks is $18\sim 28$ (preventing 12-slide extreme compression), and title/TOC/divider filler slides are $\le 20\%$. |

---

### Pillar II: Geometric, Optical, Aspect-Ratio & Sub-Panel Cropping Invariant Probes (`D7`–`D12`)

| Gate ID | Gate Name | Target Defect & Rubric Mapping | Enforcement Mechanism |
| :--- | :--- | :--- | :--- |
| **`D7`** | `D7_BoundingBox_ZeroOverlap_And_ZeroClipping_Probe` | **Redline `R2` ($-2$/slide)** & Supermolecule `1️⃣`: Sibling card/text overlap & bottom/axis-title clipping (`kimi-k3` slide 13) | Given rendered element bounding boxes `(x, y, w, h)` on the `1920×1080` slide canvas, asserts pairwise sibling intersection-over-union $\text{IoU}(B_i, B_j) = 0$ and strict canvas containment ($x \ge 0, y \ge 0, x+w \le 1920, y+h \le 1080$) with zero clipped child text. |
| **`D8`** | `D8_Canvas_Whitespace_And_Vertical_CenterOfMass_Balance` | **Supermolecule `1️⃣` (25 pts)**: Top-heavy layout with huge empty lower canvas (`grok-4.7`) or overcrowded slides | Computes total active bounding-box coverage ratio $\rho_{\text{area}} \in [0.38, 0.78]$ and area-weighted vertical center of mass $Y_{\text{cm}} = \frac{\sum A_i y_{c,i}}{\sum A_i \cdot H} \in [0.36, 0.64]$, rejecting top-cramped/bottom-empty slides. |
| **`D9`** | `D9_Image_AspectRatio_Layout_Compatibility_Guard` | **`D1` (5 pts)**: Wide banner figure (`AR > 2.0`) stuffed into narrow side-by-side split column (`qwen-3.8` slides 8, 11) | Compares natural image aspect ratio $\text{AR}_{\text{img}} = W_{\text{img}}/H_{\text{img}}$ against container aspect ratio $\text{AR}_{\text{box}}$: requires full-width top/bottom layout for wide figures ($\text{AR}_{\text{img}} \ge 1.85$) and enforces effective image area utilization $\ge 55\%$ of its layout slot (with minimum rendered height $\ge 480\text{px}$ for multi-row figures). |
| **`D10`** | `D10_Subpanel_Crop_Purity_No_Margin_Or_SlicedText_Probe` | **`B2` (5 pts)**: Unsplit 12-panel composite figure (`hy-4`) OR blind PDF crop with $>20\%$ white margin, black border lines, sliced axis labels, or neighbor-figure bleed (`qwen-3.8`) | Audits cropped figure images/specs: (1) limits sub-panel count per slide to $\le 2$ coupled panels (`One Sub-Panel Per Slide` rule), (2) scans outer strips for $>15\%$ blank PDF margin whitespace or stray black margin rules, and (3) checks the `2px` perimeter border for non-background ink density $>2\%$ (catching sliced-in-half titles/axis labels or neighbor figure text remnants). |
| **`D11`** | `D11_Figure_Text_Explicit_Referencing_Coupling_Guard` | **`B1` (4 pts) & `B3` (7 pts)**: Zero paper figures (`grok-4.7`) OR text-figure disconnect / missing sub-panel crop (`hy-4`, `qwen-3.8`) | Verifies that original paper figures (`Fig. 1–5`, `ED Fig.`) are present (`B1`), that the cropped sub-panel ID matches the sub-panel discussed in text (`B3`), and that the slide text contains explicit directional reading anchors (*“左图/右图/上排/下排/第一列/第三列/横轴/纵轴/实线/虚线/星形/读图顺序”*). |
| **`D12`** | `D12_WCAG_Contrast_And_Visual_Restraint_Probe` | **`D2` (3 pts)**: Illegible low-contrast text, garish cyberpunk neon glow (`deepseek`), or font fallback | Computes WCAG 2.1 relative luminance contrast ratio $(L_{\max}+0.05)/(L_{\min}+0.05) \ge 4.5$ for body text ($\ge 3.0$ for large titles) and flags excessive neon text-shadow/box-shadow glow in academic presentations. |

---

### Pillar III: Pedagogical Causal Chain, Interactive Physics Fidelity & Micro-Step Storyboard Anchor (`D13`–`D16`)

| Gate ID | Gate Name | Target Defect & Rubric Mapping | Enforcement Mechanism |
| :--- | :--- | :--- | :--- |
| **`D13`** | `D13_Narrative_Arc_Background_PriorArt_And_Foreshadowing_Guard` | **`A1` (8 pts), `A2` (4 pts) & Supermolecule `2️⃣` (20 pts)**: Missing macro background (`opus-5.5` skipping what PHOLED is), missing Prior Art, or clue-free blind guessing (`kimi-k3.1`) | Verifies the mandatory 4-stage pedagogical arc: (1) Macro Industry/Daily Context & Fundamental Concept Definition (e.g., PHOLED 25%:75% spin statistics, $100\%$ IQE, why blue is short-lived), (2) Degradation/Bottleneck Mechanism (TPA/TTA), (3) Prior Art Routes & Shared Ceiling (`A2`), (4) Core Innovation + Foreshadowing/Callback hooks; blocks clue-free blind numerical guessing on early slides. |
| **`D14`** | `D14_Causal_Why_Chain_And_Control_Pair_Tradeoff_Guard` | **`A3` (14 pts), `A4` (7 pts), `A5` (8 pts), `A6` (5 pts) & Redline `R7`**: Bare arrow conclusions without explaining *Why*, missing molecular structures, or conflated baselines | Audits whether mechanism slides explicitly answer the underlying physical/mathematical **Why** questions (e.g., why ETL & SPP resonate, why anticrossing $\sqrt{(\Delta E/2)^2+g^2}>0$ instead of crossing, why flattened dispersion $\text{ODoS} \propto |dE/dk_x|^{-1}$ accelerates EML decay, why low-$Q$ cavity prevents viewing-angle color shift), verifies presence of molecular structures (`A4`), and checks controlled-variable pairing (`2.5x / 4.4x / 2.2x` vs `5.3x` vs `10-14x` normalized) + `Lifetime-Color-Efficiency` trade-off analysis (`A6`). |
| **`D15`** | `D15_Interactive_Widget_Physics_Linkage_And_Anti_Hollow_Animation_Guard` | **`E1` (7 pts), `E2` (3 pts) & Supermolecule `5️⃣` (15 pts)**: Defined-but-unused `@keyframes` (`gemini-3.8flash`), static fake sliders, reversed physics (`kimiK3` SHG), or missing Quiz | Cross-checks all `@keyframes <name>` declarations in `<style>` against `animation` / `animation-name` bindings in DOM/JS (blocking unmounted hollow animations), verifies interactive sliders/buttons compute coupled physical state updates (`level ∝ 1/PF`, `TTA ∝ 1/PF²`, anticrossing `E_±(g)`), checks physical propagation direction, and checks for end-of-deck interactive Quiz (`E2`) with per-option feedback. |
| **`D16`** | `D16_Slide_Storyboard_MicroStep_And_Layout_Diversity_Anchor` | **Design-Layer `G6o` + Tri-Mode Execution Anchor (`TDD` / `Dual-Stage GDD` / `Auto+Dual-Evolve`)**: One-shot or multi-slide batch generation decay, monotonous 3-card template cloning, rubber-stamp re-grilling (`"听懂了吗"`), or skipping `Slide Design MCQ` | Requires a pre-generation `SlideStoryboardManifest` specifying each slide's claim title, layout archetype, visual modality ($V_2/V_3$), and target knowledge anchor; strictly enforces **1-Slide-Per-Step micro-step generation (`max_slides_generated_per_step == 1`)**, **1-Hop Slide Topological Lock (`unverified_slide_hop_distance == 1`)**, **Tri-Mode verification (`verify_tdd_station_capsule_completeness` for Mode 1 `TDD`, `verify_grill_station_capsule_completeness` for Mode 2 `Dual-Stage Grill-Driven Design` [3-Part Mechanism Grill + Anti-Rubber-Stamp Re-Grill + Bottleneck-to-Slide Mapping + Slide Design MCQ], and `verify_dual_evolution_feedback_receipt` for Mode 3 `Autonomous Draft + Dual-Evolution`)**, and rejects $>2$ consecutive slides sharing the exact same layout archetype. |

---

### Pillar IV: Dual-Rubric Quantitative Scoring & Red-Blue Visual Adversarial Audit (`D17`–`D18`)

1. **`D17_DualRubric_Quantitative_Scorer`**:
   - **Mode 1 (`optoelectronic_v3`)**:
     - Computes **Category A (`46 pts` across 15 knowledge anchors)** using the exact multiplicative anti-Goodhart law from [`01_optoelectronic_scoring_criteria_v3.md`](references/01_optoelectronic_scoring_criteria_v3.md):
       $$\text{Score}(A) = \sum_{k=1}^{15} w_k \times C_{\text{clarity}}(k) \times \min\left(1.0,\ \frac{V_{\text{observed}}(k)}{V_{\text{required}}(k)}\right)$$
       where $C_{\text{clarity}} \in \{S:1.0,\ A:0.75,\ B:0.5,\ C:0.25,\ D:0.0\}$ and $V_{\text{visual}} \in \{V_0\text{ pure text / AI deco}:0.3,\ V_1\text{ crude CSS/Emoji/fake bar}:0.5,\ V_2\text{ clean cropped paper fig / accurate diagram}:0.8,\ V_3\text{ figure + interactive/stepwise physics animation}:1.0\}$.
       - **Note**: Under this multiplicative law, a slide that explains a $V_3$-required concept using only pure text ($V_0 = 0.3$) is mathematically capped at **$30\%$ of the points**, making pure-text laziness unprofitable!
     - Computes **Category B (`20 pts`: `B1=4, B2=5, B3=7, B4=4`)**, **Category C (`16 pts`: `C1=6, C2=5, C3=5`)**, **Category D (`8 pts`: `D1=5, D2=3`)**, **Category E (`10 pts`: `E1=7, E2=3`)**, and deducts **Redlines `R1`–`R7` (capped at `-15 pts`)** with strict de-duplication (each defect penalized once according to Section IV of `01_optoelectronic_scoring_criteria_v3.md`).
   - **Mode 2 (`supermolecule_5dim`)**:
     - Computes the 5-Dimension score (`100 pts` total) from [`02_supermolecule_SCORING_CRITERIA_5dim.md`](references/02_supermolecule_SCORING_CRITERIA_5dim.md):
       1. `dim1_readability_layout` (`25 pts`)
       2. `dim2_narrative_logic` (`20 pts`)
       3. `dim3_richness_accuracy` (`20 pts`)
       4. `dim4_visual_structure_fidelity` (`20 pts`)
       5. `dim5_interactive_dynamic_design` (`15 pts`)
2. **`D18_RedBlue_Visual_Adversarial_Critic_Protocol`**:
   - Enforces decoupled Red-Blue multimodal verification: every slide must be rendered to a `1920×1080` PNG screenshot + DOM bounding-box JSON receipt and audited by an independent read-only Red Visual Critic rewarded solely for catching `R1`–`R7` redlines, visual clipping, sliced crops, or hollow interactions.

---

## 4. CLI Usage

```bash
# 1. Run the 18-Gate + Dual-Rubric Positive/Negative Self-Test Suite
python /home/zc/agent_workflows/components/skills/design-anti-goodhart/releases/1.0.0-rc.11/source/scripts/awf_design_anti_goodhart_gates.py --self-test

# 2. Run Self-Hosting Dogfood Integrity Audit on DesignAG scripts (via AWF Guard)
python /home/zc/agent_workflows/components/skills/design-anti-goodhart/releases/1.0.0-rc.11/source/scripts/awf_design_anti_goodhart_gates.py --audit-self

# 3. Audit an HTML presentation file directly against D1-D6, D15 static/DOM gates
python /home/zc/agent_workflows/components/skills/design-anti-goodhart/releases/1.0.0-rc.11/source/scripts/awf_design_anti_goodhart_gates.py --audit-html path/to/deck.html
```
