---
name: edit-scientific-article
description: Edit, reorganize, or review scientific manuscripts, grant proposals, and technical reports for clear definitions, causal logic, evidence-calibrated claims, measured objective scholarly tone (free of exaggerated/absolute modifiers, grandiose slogans, AI clichés, bullet-point work logs, and internal task codes), lossy-compression semantic preservation, 4-way figure/caption/text/table visual synchronization, reproducible methods, and multi-role iterative peer-review convergence. Use for scientific prose in Markdown, HTML, LaTeX, or Word; use build-scientific-docx as well when the deliverable is a DOCX file.
---

# Edit scientific articles and grant proposals

Start from the latest authoritative manuscript. If the user has manually edited a
document, treat that version as the source of truth and preserve its changes. Do
not regenerate it from an older Markdown, HTML, or DOCX source without first
reconciling the differences.

Before editing, read [references/writing-principles-zh.md](references/writing-principles-zh.md).
When learning from user revisions or turning examples into reusable rules, also
read [references/revision-learning.md](references/revision-learning.md).

## Editing workflow

1. Identify the article's audience, purpose, authoritative source, and requested
   output. Preserve the user's scientific terminology unless it is ambiguous or
   factually inconsistent.
2. Build the reader's understanding in dependency order: object and context,
   plain-language meaning, technical definition, method or equation, result,
   interpretation, and consequence.
3. Check every mechanism paragraph for a complete chain: changed cause or
   structure, affected process, observed result, and downstream consequence.
   Label measured results, interpretations, hypotheses, and speculation with
   matching evidence strength.
4. Introduce each metric before its first result. Explain in ordinary language
   what physical, chemical, biological, or statistical process it measures and how
   to read an increase or decrease (generalist onboarding), then give symbols,
   equations, parameters, and methodological details. When reporting core
   performance or yield metrics, state the relevant theoretical limit or
   stoichiometric baseline, reference state origin, and background/substrate
   subtraction protocol where applicable.
5. **Enforce 4-way visual panel-by-panel readback and cross-modal precision synchronization**:
   - Never write or revise figure captions or figure-discussion paragraphs from
     memory or older drafts. Visually inspect every final figure file and build a
     panel-by-panel `(a), (b), (c)...` inventory checking:
     (i) exact panel count and left-to-right/top-to-bottom order (never merge two
     separate panels into one label or swap panel letters);
     (ii) exact axis ranges, bounds, units, and legends;
     (iii) exact numbers, slopes, peak positions, and callout labels annotated
     directly inside the graphic (e.g., bar-chart top labels that may be rounded
     relative to raw supplementary tables);
     (iv) exact scale bar values drawn on microscopy/optical photos (distinguishing
     outer vs. inset scale bars; never hallucinate a scale bar that is absent from
     the image);
     (v) exact ordering of comma-separated multi-item table entries (e.g., modes,
     phases, or regimes) so they match the panel/mode sequence in the corresponding figure.
   - Maintain uniform decimal precision for any given physical quantity across all
     sections of the main text, captions, and tables.
   - When figures are updated to a new calculation or experimental batch,
     simultaneously synchronize all numerical values and descriptions across the
     Abstract, Main Text, Figure Captions, and Supporting Information Tables.
6. **Maintain pure continuous journal prose and zero internal work codes**:
   - Write all journal manuscript sections (Abstract, Introduction, Results &
     Discussion, Conclusion, Experimental & Computational Methods, Supporting
     Information text) as continuous scholarly paragraphs. Never use bullet-point
     lists or numbered work-report lists to present results, mechanism factors,
     or methods.
   - Strip all internal project, slide, or task codes (`Slide 15`, `PPT 第 X 页`,
     `P0 / P1 / P2-A / P2-B / P3`, `Route 1–4`, `Step 1–4`) and mixed draft tags
     from headings, tables, captions, and prose.
7. Make methods independently reproducible from the stated inputs, versions,
   parameters, sampling rules, analysis definitions, and statistics. Move paths,
   hashes, and internal switches to supplementary or provenance material unless
   they are scientifically meaningful.
8. Cite software and methods at first substantive mention using official
   recommended citations, original method papers, or versioned documentation.
   Never invent a citation for a local script.
9. Report what changed and why. Separate writing improvements from scientific
   corrections or unresolved factual questions.

## Positive interpretation and evidence calibration

1. Prioritize direct positive explanations of objects, parameters, trends, and
   physical significance. State plainly what a parameter measures, what the data
   establish, and how to understand the result.
2. Conclude the sentence once meaning is clear. Do not routinely append defensive
   exclusion lists (e.g., avoid habitual strings like "does not represent...",
   "is not claimed as...", "cannot...").
3. Rewrite exclusionary patterns: convert "X does not represent Y; Z is not W"
   into positive statements: "X describes ...; Z provides ...; investigating Y
   or W requires ... evidence".
4. Retain limiting conditions only when they materially alter conclusions, scope
   of applicability, or scientific judgment, stating them naturally and compactly.
5. Scientific accuracy remains paramount: never remove substantive qualifications
   or evidence boundaries merely to eliminate negative phrasing. When evidence is
   bounded, positively articulate the covered scope and what further data would
   be required for subsequent verification.
6. Preserve real secondary effects: when one contribution dominates but another
   also changes, write "mainly due to A, accompanied by a smaller B" rather than
   erasing B.

## Natural scholarly voice, de-exaggeration, and grant proposal readability

1. **Eliminate exaggerated, overly absolute, and grandiose framing (去夸张化与去绝对化表述)**:
   - Never use hyperbolic, absolute, or pompous wording in academic manuscripts or
     Supporting Information:
     - Replace `"从根本上解释了 / 从根本上克服了 / 从根本上消除了"` with `"解释了 / 改善了 / 缓解了"`;
     - Replace grandiose architectural slogans like `"三支柱动力学微观机理 / 三大动力学支柱"`
       and `"第一/第二/第三动力学支柱 (支柱一/二/三)"` with measured phrases such as
       `"动力学微观机理 / 三个方面的因素"` and `"第一个有利因素 / 第二个因素 / 第三个因素"`;
     - Replace absolute verbs/adverbs like `"彻底打通 / 彻底消除 / 彻底截断 / 彻底失活"`,
       `"完全囚禁 / 完全锁定 / 完全恢复 / 完全不同"`, and `"严格处于 / 直接证明 / 本质区别"`
       with evidence-calibrated phrasing (`"改善了连通性 / 缓解了 / 受阻 / 抑制了持续扩展"`,
       `"主要局域于 / 恢复至接近初始水平 / 明显不同"`, `"分布在…区间 / 表明（支持了） / 差异"`);
     - Replace `"100% 暴露 / 100% 开放 / zero steady-state current"` with exact finite-sample statistics
       or rigorous physical scope (e.g., `"所采样的 N 种构象均保持开放（N/N）"`, `"do not contribute to long-range percolating current"`);
     - Replace promotional adjectives like `"全面超越 / 全面降低 / 超长循环 / 极具应用前景"`
       with objective descriptions (`"优于 / 在所测条件下均有所降低 / 长周期稳定 / 具有较好的应用潜力"`).
2. **Eliminate AI clichés and fabricated colloquial metaphors**:
   - Never invent flashy metaphors or commercial buzzwords in scientific prose or
     grant proposals (such as “实时对账”, “死弹簧”, “瘦身铠甲”, “防弹衣”, “全链条闭环”,
     “理论闭环”, “从源头上”, “无缝衔接”, “底层逻辑”, “精准赋能”, “深耕”, or repetitive
     four-part hyphenated quotation slogans like “A—B—C—D”).
   - Express mechanisms using concrete, unadorned physical, chemical, or
     algorithmic actions.
3. **Balance specialist rigor with generalist accessibility in grant proposals**:
   - Translate engineering background into concrete physical and economic trade-offs
     (space, thickness, temperature, energy density, or cost) without slang.
   - Immediately before or after any core governing equation, explain in 1–2
     plain sentences what each term represents and how the variables interact.
   - When an applicant's prior publications are in an adjacent system, explicitly
     articulate the underlying methodological and structural homology rather than
     leaving reviewers to guess.

Project-specific molecule names, symbols, thresholds, and physical hypotheses
are examples, not global writing rules. Verify scientific claims independently;
good prose does not turn a plausible mechanism into evidence.

## Artifact-First Ground-Truth Provenance & ESI Rigor (rc.7)

1. **Parse Disk Artifacts Before Writing Methods or ESI (`Artifact-First, Never Template-First`)**:
   - When authoring or revising Computational/Experimental Methods, Supplementary Notes, or Supplementary Tables, never write protocols (temperatures, pressures, barostats, thermostats, cutoffs, time steps, trajectory lengths, system sizes, atom counts, or fitting errors) from LLM literature conventions or static high-level READMEs.
   - Always inspect and programmatically parse the actual solver/instrument input and output files on disk first, and verify that every number in prose, tables, and figure panels is 100% traceable to disk artifacts.
   - Never use synthetic/schematic random functions (`rng.normal`, `rng.uniform`, `np.cos`, `np.piecewise`) to fake validation parity plots, scans, or convergence trajectories; plot the exact arrays parsed from disk.
2. **Standalone Unpacked ESI Notes, Split Display Equations & 100% English Tables**:
   - Every Supplementary Note (`Note S#1`, `Note S#2`, ...) must be a standalone section with its own heading, full mathematical equations (strictly ONE equation per centered display line, never merging two equations with `\qquad` or commas), symbol-by-symbol physical definitions immediately following each equation, and its own dedicated 100% English Supplementary Table (`Table S#1`, `Table S#2`, ...) when writing English manuscripts/ESIs.

## Universal Scientific Rigor & Referee Defense Gates (Generalized in rc.10)

Whenever authoring, editing, or auditing a scientific manuscript or Electronic Supporting Information (ESI) across any discipline, enforce all 8 domain-agnostic rigor gates before delivery:
1. **Single-Source-of-Truth Metric Concordance**: Every core physical, chemical, or statistical quantity must be 100% identical in value, unit, and definition across the Abstract, Main Text, Figure Panels, Figure Captions, Supplementary Notes, and Supplementary Tables. Never mix distinct theoretical definitions of a similarly named quantity without explicit qualification.
2. **Zero Synthetic Validation Data & Complete Model Parameterization Disclosure**: All parity plots, calibration curves, and distributions must plot 100% real data arrays from disk (zero synthetic `np.random.normal` scatter), and any parameterized model or force field must disclose all fitted degrees of freedom, boundary/capping rules, and validation errors.
3. **Formula Plug-In Arithmetic Closure ($\le 0.1$ Unit Tolerance)**: Every formula accompanied by numerical inputs and a stated output must be verified by direct arithmetic plug-in so the formula left-hand side equals the reported right-hand side and figure values within rounding precision.
4. **Multi-Factor Causal Decomposition Synchronization**: When figure panels or analyses decompose a property change into multiple contributing factors (e.g., structural population reweighting vs. intrinsic state change, or thermodynamic vs. kinetic contributions), the accompanying prose, numbered equation, and table must present the exact same decomposition dimensions.
5. **Multi-Replica Uncertainty & Statistical Synchronization**: All ensemble means $\pm$ SD, hypothesis-test $p$-values, and effect sizes across main text, figures, Notes, and Tables must be read from a single authoritative statistical summary ledger, never mixing single-configuration extrema with ensemble averages.
6. **Static Reference vs. Dynamic Ensemble Separation**: Strictly distinguish single-structure/0 K static reference geometries (e.g., crystal CIF coordinates or minimum-energy conformers) from finite-temperature dynamic ensemble distributions. Define specialized structural notation (e.g., crystallographic $Z'$, space groups, or cluster labels) at first mention so no ambiguity arises across sections.
7. **Normalization & Continuum Definition Consistency**: Use standard physical and statistical definitions (avoiding duplicate normalization when probability weights already sum to unity, and explicitly distinguishing local core-level distributions from bulk apparent averages).
8. **Lossless Semantic Compression & Pre-emptive Referee Defense (New in rc.10)**:
   - **Lossy-Compression 3-Point Audit**: When condensing detailed technical reports or Supporting Information into compact main-text paragraphs (~10:1 compression), verify:
     (i) *No Qualifier Stripping*: Retain the minimum defining qualifiers on specialized metrics so they do not degenerate into generic umbrella terms whose default units or meanings conflict with the reported units or earlier sections;
     (ii) *No Sign–Adjective Polarity Inversion*: Verify that qualitative adjectives (`exothermic/endothermic`, `favorable/unfavorable`, `cooperative/competitive`) strictly match the mathematical sign convention of the accompanying parenthetical parameter;
     (iii) *No Single-Panel Causal Contamination*: Keep the discussion of each specific figure panel focused strictly on the variables plotted on that panel's axes/legend, stripping parenthetical side-quantities or trailing tangential clauses that belong to other panels or SI notes.
   - **Pre-emptive Novelty & Control Defense**: Frame subtle structural/process variations as clean mechanistic probes that uncover a counterintuitive structure–property relationship; when a multi-component system lacks a symmetric negative control, proactively highlight baseline comparisons from existing data to prove intrinsic component superiority; and phrase close simulation–experiment agreement using measured scholarly conventions (`quantitatively reproducing the experimental enhancement trends`, `in close agreement with`).

## Multi-Role Iterative Peer-Review Closed-Loop Protocol (Generalized in rc.10)

When executing an iterative review-and-revision closed loop on a manuscript (`RevRound1` $\to$ `RevRound2` $\to$ `RevRound3`), evaluate and revise sequentially across 4 complementary referee roles until full convergence:
1. **Role 1 (Domain Senior Referee — Big Picture, Novelty & Counterintuitive Framing)**: Audit whether the core hypothesis, mechanistic probe framing, and counterintuitive insights meet top-journal standards; pre-emptively defend against "incremental modification" or "passive diluent / missing control" critiques using existing ground-truth data.
2. **Role 2 (Theoretical & Mechanistic Referee — Physical Rigor & Lossless Compression)**: Audit all equations, thermodynamic signs, descriptor definitions, static-vs-ensemble distinctions, and multi-scale causal chains; eliminate qualifier stripping, sign inversions, and post-hoc fitting phrasing.
3. **Role 3 (Experimental & Cross-Check Auditor — 4-Way Numerical & Visual Concordance)**: Verify 100% numerical identity across prose, tables, figure callout labels, and SI; ensure complete reporting of experimental validation benchmarks (e.g., integrated checks, lifetimes, defect densities, excitation wavelengths, and database deposition numbers).
4. **Role 4 (Associate Editor — Structure, Typography, Word-Count Convergence & Track-Changes Delivery)**: Merge redundant section-closing summary paragraphs, unify template typography (font sizes, line spacing, bold caption lead-ins, native OMML symbols, and Unicode minus signs), complete front/back-matter items (affiliations, keywords, Table of Contents entry), converge cleanly to the target word-count budget, and deliver both clean versioned `.docx` files and a Word native **Track Changes + Right-Margin Rationale Comments** document.
