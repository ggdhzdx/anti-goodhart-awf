---
name: build-scientific-docx
description: Create, revise, or audit scientific Microsoft Word DOCX files while preserving user edits, using editable native OMML equations instead of formula images, enforcing 1:1 print-scale figure typography, multi-panel plot-box 0.0 px alignment, 4-way visual caption/text/table readback, Markdown table pipe safety, measured objective scholarly tone, zero residual LaTeX/Markdown/work-code/template-placeholder tokens, DOM-safe in-place manuscript editing, and Word native Track Changes (<w:ins>/<w:del>) with right-margin rationale comments (<w:comment>). Use whenever a scientific deliverable is a DOCX or Word equation/figure/review behavior matters; do not use for prose-only work with no Word output.
---

# Build scientific DOCX files

Treat the newest user-edited DOCX as authoritative. Never rebuild it from an
older Markdown, HTML, or DOCX source without reconciling the user's changes.
Write a new version by default; do not overwrite the authoritative input.

Read [references/docx-equations-and-preservation.md](references/docx-equations-and-preservation.md)
before generating or modifying a DOCX with equations or figures.

## Required workflow

1. Identify the authoritative input, intended output, and whether the task is a
   new build or a surgical edit of an existing DOCX.
2. Preserve user text, styles, tables, figures, captions, references, section
   settings, and relationships unless the requested change requires otherwise.
   Maintain pure continuous scholarly paragraphs in journal manuscripts (never use
   bullet-point work logs or leave internal slide/project codes such as `Slide 15`,
   `PPT 第 X 页`, or `P0–P3`).
3. Insert equations as native Office Math Markup Language (OMML), so Word's
   equation editor can edit them. Never silently rasterize an unsupported
   equation. Report the exact unsupported expression and stop or request a
   scientifically equivalent rewrite.
4. For deterministic placeholder conversion, use
   `scripts/native_math.py render INPUT.docx OUTPUT.docx`.
   - Display equations: A paragraph containing only `{{OMML: LATEX}}` is converted
     into a centered `m:oMathPara` block, and any inherited first-line indentation
     (`w:ind`) or fixed line-spacing (`w:lineRule="exact"`, e.g. 28 pt in Chinese
     grant templates) is automatically stripped so fractions, integrals, and sums
     are never vertically clipped.
   - Inline equations: `{{OMML_INLINE: LATEX}}` inside a mixed-text paragraph or
     table cell is converted in place into an inline `m:oMath` object while
     preserving surrounding text runs and paragraph formatting.
   - **Markdown Table Pipe Safety (`re.split(r"\s+\|\s+"`)**: When building DOCX
     tables from Markdown sources, never split table rows with bare `.split("|")`
     because vertical bars inside inline math (such as absolute values or transfer
     integrals `$2|J_h|$`, `$|V_{\min}|$`, `$|y_i - \hat{y}_i|$`) will split a
     single formula across adjacent cells and leave broken `$` tokens. Always split
     table cells using whitespace-bounded pipes `re.split(r"\s+\|\s+", line.strip().strip("|"))`
     or convert inline math placeholders before splitting.
   - Supported strict LaTeX subset:
     - N-ary operators (`\sum`, `\prod`, `\int`) -> `m:nary` with `m:naryPr/m:chr`,
       explicit `m:sub`, `m:sup`, and `m:e` (never `m:sSubSup` fallback);
     - Delimiter pairs (`\left ... \right`) and balanced raw `|...|` -> `m:d` with
       `m:dPr/m:begChr`, `m:dPr/m:endChr`, and `m:e` (supporting `()`, `[]`,
       `\{\}`, `\langle\rangle`, `| |`, `\vert`, `\Vert`, `\lvert`, `\rvert`,
       `\lVert`, `\rVert`, and invisible `.`);
     - Functions: Named functions (`\ln`, `\exp`, `\log`, `\sin`, `\cos`, `\tan`,
       `\min`, `\max`, `\det`) and `\operatorname{name}` followed by one group or
       atom argument -> `m:func` with roman `m:fName` and argument `m:e`;
     - Accents and bars: `\hat{...}` (`^`), `\tilde{...}` (`~`), `\vec{...}` (`→`),
       `\dot{...}` (`˙`), and `\ddot{...}` (`¨`) -> `m:acc` with `m:accPr/m:chr`
       and `m:e`, while `\bar{...}` and `\overline{...}` remain `m:bar` with
       `m:barPr/m:pos="top"`;
     - Expanded physics/chemistry symbols: `\gg` (`≫`), `\ll` (`≪`), `\to` (`→`),
       `\gets` (`←`), `\rightleftharpoons` (`⇌`), `\hbar` (`ℏ`), `\AA` (`Å`),
       `\circ` (`∘`), `\bullet` (`•`), `\dots`/`\ldots` (`…`), `\cdots` (`⋯`),
       plus Greek letters and standard relations;
     - Fractions (`\frac` -> `m:f`), radicals (`\sqrt` -> `m:rad`), scripts
       (`_` -> `m:sSub`, `^` -> `m:sSup`, both -> `m:sSubSup`), roman/bold
       (`\mathrm`, `\text` -> roman `p`, `\mathbf` -> bold `b`).
   Syntax outside this subset fails closed with `LatexSyntaxError`; never claim full TeX coverage.
5. 当正文的研究方法、模型、参数、数据范围、结论、命名或版本改变时，交付 DOCX 前必须识别全部受影响图片并检查是否同步更新；逐一核对图内文字、面板顺序、模型名称、公式、颜色条和坐标范围、数值、图注、正文引用，防止旧合成图、旧缓存图和旧媒体对象被继承。
   - **4-Way Visual Panel-by-Panel Readback**: Visually inspect every final embedded
     figure and verify that the panel count/order `(a), (b), (c)...`, axis ranges,
     cycle numbers, peak values, and microscopy scale bars match the Figure
     Captions, Main Text, and Supporting Information Tables with zero discrepancy.
6. **1:1 Print-Scale Figure Typography, Multi-Panel Plot-Box `0.0 px` Alignment & Header Band Rule**:
   - Design the figure canvas width near 1:1 print scale (`figsize` width
     $6.5\text{–}7.5\text{ in}$ or unified high-resolution canvas width $W = 2400\text{ px}$
     placed at $6.0\text{–}6.2\text{ in}$ in Word without lossy downsampling).
     Never draw schematics on oversized $13\text{–}16\text{ in}$ canvases that
     shrink text to illegible $3\text{–}4\text{ pt}$ micro-print in Word.
   - Use $9.5\text{–}12.8\text{ pt}$ fonts on the $6.5\text{–}7.5\text{ in}$ canvas
     so rendered figure text in Word is $\ge 8\text{ pt}$, harmonious with Word's
     $12\text{–}14\text{ pt}$ (小四/四号) body text.
   - **Plot-Box Spine Alignment (`0.0 px` Error) & Uniform Font Scale**: When
     assembling multi-panel composite figures, detect each subplot's inner axis/plot-box
     rectangle (`plot_box = [x0, y0, x1, y1]`) rather than aligning by outer
     whitespace margins. Scale and position subplots so plot-box top and bottom
     edges across every row have **`0.0 px` misalignment**, aligned grid columns
     have **`0.0 px` left/right misalignment**, and 2-panel rows share the exact
     same target plot-box height and font scale as 3-panel rows.
   - **Reserved Top Header Band & Edge Sanitization**: Place panel tags `(a), (b), (c)...`
     inside a dedicated blank header band above the plot-box top spine so they
     never collide with titles, legends, colorbars, or axis ticks; sanitize crop
     borders to remove any residual ghost text from adjacent slide/figure elements.
   - Keep text inside figure boxes to concise 2–3 line keyword phrases ($\le 15$
     Chinese characters per line); leave full sentence explanations to the caption
     and main text.
   - In Matplotlib with Chinese fonts (`SimHei` / `Microsoft YaHei`), always render
     chemical formulas and subscripts via STIX math (`r"$\mathrm{W_2B_5}$"` with
     `mathtext.fontset = "stix"`), never raw Unicode subscript characters (`₂`, `₅`),
     which render as missing-glyph boxes (`□`).
   - Always set single line spacing (`line_spacing = 1.0`) on figure paragraphs so
     fixed 28 pt body line spacing does not clip the image vertically.
7. Audit every final file with `scripts/audit_docx.py`. The audit verifies ZIP
   integrity, XML/python-docx parseability, equation counts, media deltas, zero
   unrendered `{{OMML` placeholders, zero residual raw LaTeX/Markdown tokens
   (`no_residual_latex_tokens`), zero internal work codes (`no_residual_work_codes`),
   zero exaggerated or overly absolute claims (`no_exaggerated_claims`, catching
   phrases like `从根本上`, `三支柱`, `第一动力学支柱`, `彻底消除`, `完全囚禁`, `全面超越`,
   `超长循环`, `极具应用前景`), and zero display equations or drawings trapped inside
   fixed-line-spacing (`w:lineRule="exact"`) paragraphs.
8. Report the new file path, equation count, media delta, and any validation that
   could not be performed.

Run `python scripts/self_test.py` after changing these scripts. The tool refuses
same-path input/output and existing outputs by default. Keep that no-overwrite
behavior unless the user explicitly requests and approves replacement.

Use `edit-scientific-article` as well when the task includes substantive writing
or scientific reasoning rather than document mechanics alone.

## 9. Mandatory Artifact-First Ground-Truth Provenance, Single-Line Equations & Zero Raw `_`/`^` Gate (rc.9)

- **Artifact-First Ground-Truth Provenance (`--provenance-dir`)**: Never write computational methods, Supporting Information (ESI) protocols, or table parameters from LLM memory, generic literature priors, or high-level summary templates. Before writing a single word or plotting a validation figure, parse the actual executed input/output files on disk (`.mdp`, `.gro`, `.top`, `.frcmod`, `.inp`, `.gjf`, `.log`, `*_summary.json`, `*_qc.json`). Never use `rng.normal`, `rng.uniform`, or `np.cos` synthetic curves in force-field or MD validation figures. Run `python scripts/audit_docx.py OUTPUT.docx --provenance-dir <CAMPAIGN_DIR>` to enforce `disk_provenance_concordance: true`.
- **Strictly One Equation Per Display Line (`no_merged_display_equations`)**: Every display equation (`{{OMML: ...}}`) must occupy its own standalone paragraph with a single equation number (`(S1a)`, `(S1b)`, etc.). Never merge two equations or append a parenthetical equation (`\qquad (r_0 = r_{\mathrm{DFT}})`) on the same display line.
- **Zero Raw `_`, `^`, `{`, `}`, `\` in Prose and Table Runs (`no_raw_sub_superscript_ascii_in_runs`)**: Every mathematical symbol with a subscript or superscript in prose, headings, figure captions, or table cells must use `{{OMML_INLINE: ...}}`. `audit_docx.py` scans every `<w:r>` run and fails if any raw `_`, `^`, `{`, `}`, or `\` remains outside `<m:oMath>`.

## 10. Computational Chemistry Referee Gates: `\ddagger`/`\dagger` Support, Zero Synthetic Figure Scripts & Work-Jargon Filter (rc.10)

- **Transition-State & Thermodynamic LaTeX Symbols (`\ddagger`, `\dagger`, `\permil`, `\perp`, `\parallel`)**: `native_math.py` natively converts `\ddagger` (`‡`), `\dagger` (`†`), `\permil` (`‰`), `\models` (`⊨`), `\perp` (`⊥`), `\parallel` (`∥`), `\forall` (`∀`), and `\exists` (`∃`) into editable OMML runs so transition-state barriers (`\Delta G^\ddagger`) never require ASCII fallbacks.
- **Figure-Script Static Source Gate (`--figure-scripts`)**: Run `python scripts/audit_docx.py OUTPUT.docx --provenance-dir <DIR> --figure-scripts <FIG_SCRIPT_1.py> <FIG_SCRIPT_2.py>` to statically scan figure-generation scripts and block unauthorized `np.random.normal` / `np.random.randn` / `random.gauss` synthetic noise in validation or parity figures (`no_synthetic_random_in_figure_scripts: true`).
- **Expanded Internal Debugging Jargon Filter (`no_residual_work_codes`)**: Automatically blocks informal engineering debugging phrases (`完全拉平起点`, `拉平起点`, `completely leveled starting point`, `补跑了`, `重跑了`, `临时脚本`, `TODO`, `FIXME`) from appearing in manuscripts or Supporting Information.

## 11. Inline OMML Font-Size/Bold/Color Inheritance, Greek Token-Delimiter Space Absorption, Table Split Protection & Word COM Visual QA (rc.11)

- **Inline `<m:oMath>` Style Inheritance (`_replace_inline_in_paragraph`)**: Automatically copies `<w:sz>`, `<w:szCs>`, `<w:b>`, `<w:bCs>`, and `<w:color>` from the enclosing paragraph's `first_rPr` onto every `<m:r>` inside inline `<m:oMath>` elements so table cells (`8.4 pt`), figure captions (`9.5 pt`), and section headings (`13 pt` bold navy) render inline mathematical symbols at the exact surrounding font size and weight instead of reverting to Word's default `10.5 pt`.
- **LaTeX Greek/Prefix Space Absorption (`GREEK_AND_PREFIX_COMMANDS`)**: `LatexParser.parse_command` automatically consumes LaTeX command-delimiter spaces after `\Delta`, `\alpha`–`\omega`, `\Gamma`–`\Omega`, `\partial`, `\nabla`, `\hbar`, `\langle`, `\lvert`, and `\lVert` so expressions like `\Delta E`, `\langle\Delta E\rangle`, `\pi r`, and `\beta d` render tightly (`ΔE`, `⟨ΔE⟩`, `πr`, `βd`) without spurious blanks.
- **Table Column-Width Assertions & Row-Split Protection**: Table builders must assert `len(table_data[0]) == len(col_widths)`, set `<w:cantSplit/>` on every table row, set `<w:tblHeader/>` on row 0, and set `keep_with_next = True` on table title paragraphs. `audit_docx.py` enforces `no_truncated_table_columns: true`.
- **Headless Word COM $\to$ PDF $\to$ PNG Visual Inspection Gate**: After `audit_docx.py` passes XML checks, export the `.docx` to PDF via an isolated Microsoft Word COM instance (`ExportAsFixedFormat`), render pages at 150 DPI via `pdftoppm -png`, and visually inspect table headers, display equations, and page breaks.

## 12. DOM-Preserving In-Place Manuscript Editing, Publisher Template Placeholder Gate & Word Native Track Changes + Rationale Comments (rc.12)

- **DOM-Safe `<w:drawing>` Detection (Never Substring `'graphic'`)**: When surgically updating paragraphs in an existing `.docx` while protecting embedded figures, always test for XML drawing nodes (`len(p._p.findall(".//" + qn("w:drawing"))) > 0`). Never check `'graphic' in p._p.xml` because English words like `crystallographic` or `topographic` inside `<w:t>` text runs contain the substring `'graphic'` and will cause the paragraph update to be silently skipped.
- **Dynamic Template Font & Spacing Inheritance**: When rewriting a paragraph in place, inspect the paragraph's existing `first_rPr` and `pPr` before clearing children so the new runs inherit the template's exact font family, font size (`<w:sz>`), alignment, and line spacing instead of hardcoding a single profile.
- **Zero Residual Publisher Template Placeholders (`no_residual_template_placeholders`)**: `audit_docx.py` scans all paragraphs and table cells and fails if any unfilled publisher template placeholder remains (`Deposition numbers xxxxxx`, `Insert text for Table of Contents here`, `((Maximum 450 characters`, `[Insert ... here]`, `Author 1,* Author 2`).
- **Word Native Track Changes (`<w:ins>`/`<w:del>`) + Right-Margin Rationale Comments (`<w:comment>`) (`scripts/build_track_changes_docx.py`)**:
  - When delivering a revised manuscript or multi-round peer-review revision, generate both the clean revised `.docx` and a companion `_TrackChanges.docx` using:
    ```bash
    python scripts/build_track_changes_docx.py ORIGINAL.docx REVISED.docx OUTPUT_TrackChanges.docx \
      --author "SciWord Peer-Review" --initials "PR" --comments-json COMMENTS.json
    ```
  - `build_track_changes_docx.py` invokes an isolated background Word COM instance (`win32com.client.DispatchEx("Word.Application")`) to run `CompareDocuments(Granularity=1, CompareFormatting=False)` (word-level `<w:ins>`/`<w:del>` markup), anchors each revision rationale as a native right-margin comment balloon (`doc.Comments.Add`), and automatically verifies via `AcceptAllRevisions() + DeleteAllComments()` that accepting all changes yields **0 paragraph text differences** and 100% `<m:oMath>` / `<w:drawing>` parity with `REVISED.docx`.
