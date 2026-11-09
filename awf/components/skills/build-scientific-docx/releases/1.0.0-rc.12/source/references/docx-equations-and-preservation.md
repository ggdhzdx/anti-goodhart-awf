# Scientific DOCX equations, figures, and preservation

## Source-of-truth rule

When the user has edited a Word document, that DOCX is the authoritative source.
Do not regenerate it from an older Markdown or HTML file. First compare the
candidate input with the latest user-edited file and preserve user additions,
deletions, paragraph merges, terminology, figures, tables, and references.

Produce a new versioned filename. Never overwrite the authoritative input by
default. Keep a verified backup before any explicitly approved in-place change.

## Native Word equations & Markdown table pipe safety

Editable Word equations are represented by Office Math Markup Language (OMML):
- `m:oMathPara` containing `m:oMath` for centered display equations;
- `m:oMath` directly inside a paragraph (`w:p`) for inline equations.
A PNG, SVG, or EMF picture that visually resembles a formula is not an editable Word equation.

The bundled `scripts/native_math.py` converts:
1. Display equation paragraphs containing only:
   ```text
   {{OMML: S_{cov}=cov_{IC-IC}-cov_{IC-core}}}
   ```
   into centered `m:oMathPara` equations, while automatically removing inherited
   `w:ind` (first-line indent) and `w:spacing[@w:lineRule='exact']` (fixed line
   spacing such as 28 pt in Chinese grant templates) from `w:pPr` so tall
   fractions and integrals are never vertically clipped.
2. Inline equation placeholders inside mixed-text paragraphs and table cells:
   ```text
   电子热容 {{OMML_INLINE: C_e(T_e)}} 与电声耦合系数 {{OMML_INLINE: G(T_e)}}
   ```
   into inline `m:oMath` elements in place, preserving surrounding text runs and
   paragraph formatting.
3. **Markdown Table Pipe Safety (`re.split(r"\s+\|\s+"`)**:
   When converting Markdown tables into Word tables, never split rows using bare
   `line.split("|")`. Formulas containing vertical bars such as absolute values
   or transfer-integral couplings (`$2|J_h|$`, `$|V_{\min}|$`, `$|y_i - \hat{y}_i|$`)
   will be split across columns, leaving broken raw `$` tokens in adjacent cells.
   Always split Markdown table rows on whitespace-bounded column separators
   `re.split(r"\s+\|\s+", line.strip().strip("|"))` or convert `$...$` to
   `{{OMML_INLINE: ...}}` before splitting on column boundaries.

Conversion is transactional: all expressions are parsed before the output is
written. Unsupported commands cause a clear failure and are never converted to
images.

Supported constructs and their semantic OMML representation:

- **N-ary operators** (`\sum`, `\prod`, `\int`): rendered as semantic `m:nary`
  with `m:naryPr/m:chr`, explicit `m:sub`, `m:sup`, and body `m:e`. Sub-only
  (`\sum_i`), sup-only (`\prod^N`), both (`\sum_{i=1}^n`), and neither
  (`\int x`) are supported with appropriate `m:subHide` / `m:supHide` flags;
  operators never fall back to `m:sSubSup` around Unicode glyphs. An explicit
  n-ary body is required (e.g. `\sum` without following body raises `LatexSyntaxError`).
- **Paired delimiters and absolute values** (`\left ... \right`, `|...|`): rendered as an `m:d` structure
  with `m:dPr/m:begChr`, `m:dPr/m:endChr`, and body `m:e`. Delimiters are not
  emitted as plain runs. Supported delimiter characters include `()`, `[]`,
  `\{\}` (`\lbrace\rbrace`), `\langle\rangle`, `| |` (`\vert`, `\lvert`, `\rvert`),
  `\Vert` (`\|`, `\lVert`, `\rVert`), and invisible `.` (`\left.` or `\right.`).
  Balanced raw `|...|` pairs in a sequence become `m:d` with `begChr` and `endChr`
  set to `'|'`, supporting nesting with groups and delimiters. Unmatched or
  misordered delimiters and unmatched raw `|` fail closed. `\left|...\right|`
  remains fully supported.
- **Functions** (`\ln`, `\exp`, `\log`, `\sin`, `\cos`, `\tan`, `\min`,
  `\max`, `\det`, `\operatorname{name}`): rendered as `m:func` with function name in `m:fName`
  (styled with `m:rPr/m:sty[@m:val='p']`) and argument in `m:e`. Named operators
  and `\operatorname{name}` consume exactly one following atom or bracketed group.
  Scripts on arguments (such as `\ln x^2` or `\operatorname{median} x^2`) stay
  inside `m:e`. Missing arguments fail closed.
- **Accents and overbars**:
  - `\hat{...}` (`^`), `\tilde{...}` (`~`), `\vec{...}` (`→`), `\dot{...}` (`˙`),
    `\ddot{...}` (`¨`): rendered as semantic accent `m:acc` with `m:accPr/m:chr`
    and base `m:e`.
  - `\bar{...}`, `\overline{...}`: preserved as `m:bar` with
    `m:barPr/m:pos[@m:val='top']` and base `m:e`.
- **Fractions and radicals**: `\frac{num}{den}` rendered as `m:f` (`m:num`,
  `m:den`); `\sqrt{arg}` rendered as `m:rad` (`m:radPr/m:degHide`, `m:deg`,
  `m:e`). Optional radical degrees (e.g. `\sqrt[3]{x}`) are unsupported and fail closed.
- **Subscripts and superscripts**: `x_i` (`m:sSub`), `x^2` (`m:sSup`), and
  `x_i^2` (`m:sSubSup`). Duplicate subscripts or superscripts (e.g. `x_1_2`)
  fail closed.
- **Font styles**: `\mathrm`, `\text` (plain roman run `p`), `\mathbf` (bold run `b`).
- **Symbols**: Greek letters, binary operators, relations (`\gg`, `\ll`, `\le`, `\ge`, `\neq`, `\approx`, `\sim`, `\propto`, `\equiv`), arrows (`\to`, `\gets`, `\rightarrow`, `\leftarrow`, `\leftrightarrow`, `\Rightarrow`, `\Leftarrow`, `\rightleftharpoons`, `\leftrightharpoons`), physics/chemistry symbols (`\hbar`, `\AA`, `\circ`, `\bullet`, `\partial`, `\nabla`, `\infty`, `\oplus`, `\ominus`), and ellipses (`\dots`, `\ldots`, `\cdots`) listed by `python scripts/native_math.py supported`.

### Bounded scope and fail-closed constraints

This tool implements a deliberately strict, bounded LaTeX subset, not a full TeX
engine. The following boundaries apply:

- No macro expansion or user-defined commands;
- No LaTeX environments (`\begin{equation}`, `\begin{align}`, `\matrix`, etc.);
- No arbitrary delimiter sizing commands (`\Big`, `\bigg`);
- No optional radical degrees (`\sqrt[n]{x}`);
- Strict validation: missing n-ary bodies, missing function arguments,
  unmatched left/right delimiters, unclosed raw absolute values, duplicate scripts,
  and unknown commands fail transactionally with `LatexSyntaxError`.
- No image rasterization fallback: all equations must be represented as valid
  editable OMML or the build fails.

## Figure and media synchronization, multi-panel plot-box alignment & 1:1 print-scale typography rules

1. **Content Synchronization & 4-Way Visual Readback**:
   当正文的研究方法、模型、参数、数据范围、结论、命名或版本改变时，交付 DOCX 前必须识别全部受影响图片并检查是否同步更新；逐一核对图内文字、面板顺序、模型名称、公式、颜色条和坐标范围、数值、图注、正文引用，防止旧合成图、旧缓存图和旧媒体对象被继承。
   - Open every final embedded image file and perform a visual panel-by-panel
     readback (`(a), (b), (c)...`), verifying that panel count, panel order,
     axis ranges, cycle bounds, peak positions, slopes, and microscopy scale bars
     match the Figure Captions, Main Text, and Supporting Information Tables.
2. **Multi-Panel Composite Figure Plot-Box `0.0 px` Alignment & Header Band Gate**:
   - **Unified Canvas Width & Lossless Resolution**: Use a uniform canvas width
     across all manuscript and SI figures (e.g., $W = 2400\text{ px}$ placed at
     $6.0\text{–}6.2\text{ in}$ in Word, $\sim 387\text{ DPI}$) without lossy
     downsampling of high-resolution source renders.
   - **Plot-Box Spine Alignment (`0.0 px` Error)**: Never align multi-panel
     composites by outer image bounding boxes. Detect each subplot's inner axis
     rectangle (`plot_box = [x0, y0, x1, y1]`) and scale/place each panel so
     plot-box top and bottom edges across every row have **`0.0 px` misalignment**
     and aligned grid columns have **`0.0 px` left/right misalignment**.
   - **Uniform Font Size Across Rows**: Lock a uniform target plot-box height and
     source font scale across 2-panel and 3-panel rows so axis labels and tick
     numbers never appear disproportionately enlarged in 2-panel rows.
   - **Reserved Top Header Band & Edge Sanitization**: Place `(a), (b), (c)...`
     labels inside a dedicated blank header band above the plot-box top edge
     (left-aligned with the plot-box spine) so labels never overlap titles,
     legends, colorbars, or ticks; sanitize crop borders to eliminate residual
     ghost text from adjacent slide/figure elements.
3. **1:1 Print-Scale Canvas & Font Sizing**:
   - Standard A4 Word body columns are $\sim 5.8\text{–}6.2\text{ inches}$ wide. Always design Matplotlib figures at `figsize=(6.5..7.5, H)` so the placement scaling ratio into Word is $\ge 0.80$.
   - Use $9.5\text{–}12.8\text{ pt}$ fonts on the $6.5\text{–}7.5\text{ in}$ canvas so text inside embedded Word figures renders at $\ge 8\text{ pt}$ and matches the visual weight of $12\text{–}14\text{ pt}$ (小四/四号) body text.
   - Keep text inside flowchart/schematic cards to concise 2–3 line keyword phrases ($\le 15$ Chinese characters per line); place detailed explanations in the figure caption and body paragraphs.
   - Use STIX math (`r"$\mathrm{W_2B_5}$"` with `mathtext.fontset = "stix"`) for chemical formulas and subscripts instead of raw Unicode subscript characters (`₂`, `₅`), which are missing from `SimHei` and `Microsoft YaHei`.
   - Set single line spacing (`line_spacing = 1.0`, `first_line_indent = Pt(0)`) on the paragraph holding `w:drawing` so fixed 28 pt body line spacing never clips the image.

## Audit rules

Run:

```bash
python scripts/audit_docx.py OUTPUT.docx \
  --baseline INPUT.docx \
  --minimum-equations 1 \
  --max-new-media 0
```

The audit checks ZIP integrity, required package members, XML parseability,
`python-docx` parsing, equation counts (display and inline), zero unrendered
`{{OMML` placeholders, zero residual raw LaTeX/Markdown tokens
(`no_residual_latex_tokens`), zero internal work codes (`no_residual_work_codes`),
zero exaggerated or overly absolute claims (`no_exaggerated_claims`, such as
`从根本上`, `三支柱`, `第一动力学支柱`, `彻底消除`, `完全囚禁`, `全面超越`, `超长循环`,
`极具应用前景`), zero display equations or drawings clipped by `w:lineRule="exact"`,
drawing/media counts, paragraphs, and tables. With a baseline it reports newly
added media by content hash. Set `--max-new-media` to the exact number of
intentionally added figures.

## Preservation checklist

- authoritative user edits retained;
- input and output paths differ;
- output filename is versioned and does not already exist;
- formulas are OMML and remain editable;
- Markdown tables split on whitespace-bounded pipes (`re.split(r"\s+\|\s+"`) so `|...|` inside formulas never splits cells;
- zero residual raw `$` signs, raw LaTeX commands, raw Markdown syntax, internal slide/work codes (`Slide`, `PPT 第 X 页`), or exaggerated/absolute wording (`no_exaggerated_claims`);
- display equations and figures are not clipped by fixed line spacing (`w:lineRule="exact"`);
- unsupported formulas fail visibly;
- no unexplained new media objects;
- 当正文的研究方法、模型、参数、数据范围、结论、命名或版本改变时，交付 DOCX 前必须识别全部受影响图片并检查是否同步更新；逐一核对图内文字、面板顺序、模型名称、公式、颜色条和坐标范围、数值、图注、正文引用，防止旧合成图、旧缓存图和旧媒体对象被继承。
- multi-panel composite figures enforce `0.0 px` plot-box spine alignment, uniform font scale across 2-panel and 3-panel rows, reserved top header bands for `(a), (b), (c)...` labels, and 4-way visual readback consistency;
- embedded figures use 1:1 print-scale canvas width ($6.5\text{–}7.5\text{ in}$), readable font sizes ($\ge 9.5\text{ pt}$), concise keyword labels, and STIX math subscripts;
- paragraph, table, figure, caption, reference, and section counts are plausible;
- final package passes ZIP and parser checks;
- any unavailable Windows/Word visual check is reported honestly.


## 8. Extra-Brace Sanitization, Extended Operators (`\iint`, `\min`), and `--require-english-tables` Gate (rc.7)

- `native_math.clean_omml_braces()` automatically repairs trailing extra closing braces on `{{OMML_INLINE:...}}}` placeholders before regex tokenization so no residual `}` leaks into rendered Word runs.
- `SYMBOLS` now includes `\iint` (`∬`), `\iiint` (`∭`), `\oint` (`∮`), and `\mid` (`|`), and `FUNCTIONS` includes `\min`, `\max`, `\sup`, `\inf`, `\det`, `\dim`, `\lim`, `\arg`, `\arccos`, `\arcsin`, and `\arctan` (allowing subscripted operators like `\min_{A}` and surface integrals `\iint_{S}`).
- `audit_docx.py --require-english-tables` verifies that every table cell in the `.docx` document contains zero Chinese characters (`no_chinese_in_english_tables: true`, `table_cjk_cell_count: 0`).


## 9. DOM-Safe In-Place Editing, Publisher Template Placeholder Gate, and Word Native Track Changes + Comments (rc.12)

- **DOM-Safe `<w:drawing>` Check**: Never test `'graphic' in p._p.xml` when filtering out figure paragraphs during in-place `.docx` editing, because words like `crystallographic` or `topographic` inside `<w:t>` match `'graphic'`. Always query XML elements: `len(p._p.findall(".//" + qn("w:drawing"))) > 0`.
- **Publisher Template Placeholder Gate (`no_residual_template_placeholders`)**: `audit_docx.py` automatically rejects documents containing residual template placeholders such as `xxxxx`, `Insert text for Table of Contents here`, `((Maximum 450 characters`, `[Insert ... here]`, or `Author 1,* Author 2`.
- **Word Native Track Changes (`<w:ins>`/`<w:del>`) + Right-Margin Rationale Comments (`<w:comment>`) (`scripts/build_track_changes_docx.py`)**:
  - Uses an isolated `win32com.client.DispatchEx("Word.Application")` session to run `CompareDocuments(Granularity=1, CompareFormatting=False)` between `ORIGINAL.docx` and `REVISED.docx`, optionally attaches paragraph-anchored rationale comments from `--comments-json`, and verifies via `AcceptAllRevisions() + DeleteAllComments()` that accepting all revisions yields zero text differences and exact equation/drawing parity with `REVISED.docx`.
