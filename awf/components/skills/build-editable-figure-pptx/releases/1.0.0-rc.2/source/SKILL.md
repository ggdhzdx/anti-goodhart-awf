---
name: build-editable-figure-pptx
description: Decompose scientific composite figures, Matplotlib/DFT plots, and experimental 2D/3D panels into widescreen editable PowerPoint (.pptx) decks (AWF FigPPT / SciFig / 拆图) where each slide holds one complete sub-panel on a clean text-free base graphic and 100% of panel labels, axis titles, tick numbers, bar/orbital values, rounded-rectangle badges, legends, and molecular/scheme annotations are native, freely draggable PowerPoint shapes/textboxes with OpenXML subscripts/superscripts.
---

# Build Editable Scientific Figure PowerPoint Decks (`AWF FigPPT` / `拆图`)

Convert multi-panel scientific figures (both script-generated computational/DFT plots and existing experimental composite figures/slides) into **native editable PowerPoint (`.pptx`) decks** where:
1. **One Sub-Panel Per Slide**: Every slide (`13.333 × 7.500 in` 16:9 widescreen) holds one complete sub-panel `(a), (b), (c)...` at high resolution, plus an optional single-slide composite overview where all sub-panels and their labels remain individually draggable.
2. **Zero Baked-In Text Overlap**: Underlying plot graphics and 3D molecular renders have overlapping raster text stripped, while **panel labels `(a)–(k)`, axis titles, tick numbers, data values, rounded-rectangle callout badges, legends, and chemical/scheme labels are 100% native PowerPoint textboxes and shapes** that users can click, drag, resize, and reformat in PowerPoint.

Read [references/figure-pptx-decomposition-guide.md](references/figure-pptx-decomposition-guide.md) before decomposing figures or building editable PowerPoint decks.

## Required Workflow & Five Core Engineering Guardrails

1. **Palette PNG Transparency Stripping (`load_clean_rgb` — Anti-Hollow-Text Gate)**:
   - Slides or figures exported from LibreOffice, Origin, or PowerPoint are frequently saved as 8-bit palette PNGs (`mode="P"`) with a `transparency` index in `im.info`.
   - **Never call `.convert("RGB")` directly on a palette PNG before cropping**, because Pillow translates the palette transparency index into `im.info["transparency"] = (0, 0, 0)` in saved crops, causing PowerPoint to render all pure-black `(0, 0, 0)` axis spines and text interiors as transparent (producing invisible plot borders and hollow outlined text).
   - Always composite through `RGBA` onto a fresh `Image.new("RGB", im.size, (255, 255, 255))` canvas using `load_clean_rgb()` from `scripts/editable_figure_pptx_kit.py` and verify via `audit_pptx_editable_shapes()` that zero embedded PNGs carry a `tRNS` transparency chunk on opaque panels.

2. **Computational / Script-Generated Plots (`DataToPptBridge`)**:
   - Render the Matplotlib figure with **all text removed** (`ax.set_xticklabels([])`, `ax.set_yticklabels([])`, `ax.set_xlabel("")`, `ax.set_ylabel("")`, no `ax.text`, no `ax.legend`) and save at `300 DPI` with `transparent=True`.
   - Use `DataToPptBridge(fig, ax, img_left, img_top, fig_w, fig_h)` from `scripts/editable_figure_pptx_kit.py` to transform Matplotlib data coordinates `(x, y)` via `ax.transData` into exact PowerPoint slide coordinates (`Inches`), placing native draggable PowerPoint textboxes, rounded-rectangle badges (`add_ppt_badge`), and legends (`add_ppt_legend`).
   - When rendering a multi-panel composite overview slide (`scale < 1.0`), scale tick lengths and spine widths proportionally (`length=5.8 * scale`, `width=1.6 * scale`) so ticks never collide with miniature draggable tick numbers.

3. **Experimental 2D Plots (`scan_plot_box_and_ink_gaps` — Dual-Mode Decomposition)**:
   - Detect the 4-spine plot frame `(bx0, by0, bx1, by1)` and run `scan_plot_box_and_ink_gaps(im, frame)` to measure the exact pixel whitespace gaps between outer tick marks (`4–8 px`), tick numbers (`14–68 px`), and outer axis titles (`70–130 px`).
   - **Mode A (`place_relabelled_2d_plot_on_slide` — Full Native Relabeling)**: Crop only `frame ± 7 px` (retaining the 4-spine box and tick marks while stripping all raster tick numbers and titles), white out any distorted internal raster legends, and place 100% native draggable PPT tick numbers, axis titles, sample badges, and legends.
   - **Mode B (`place_plot_with_draggable_titles` — Keep Tick Numbers, Strip Outer Titles)**: Crop to the exact whitespace gap between tick numbers and axis titles (`pad_ticks=(pl, pt, pr, pb)`). For spectra without Y-axis tick numbers (e.g., UV-vis, FTIR, XPS), explicitly erase the rotated Y-axis title strip `(bx0 - 65, by0, bx0 - 8, by1)` on the source canvas and keep `pl >= 30` so the leftmost X-axis tick number (e.g., `1800`, `1.0`, `542`) is never horizontally clipped.

4. **Native OpenXML Subscripts, Superscripts & 4-Slot Uniform Font Enforcement (`latin` / `ea` / `cs` / `sym` + Theme XML)**:
   - Never leave raw `_` or `^` characters (such as `W_v`, `λ_reorg`, `D_Na+`) in PowerPoint text runs.
   - Use `populate_paragraph_with_scripts()` / `add_ppt_text()` in `scripts/editable_figure_pptx_kit.py`, which parses `_` and `^` tokens and sets `<a:rPr baseline="-25000">` (subscript) or `<a:rPr baseline="30000">` (superscript) in OpenXML so formulas remain 100% native and editable in PowerPoint.
   - **Anti-Font-Fallback Gate (zh-CN PowerPoint)**: `run.font.name = "Arial"` in `python-pptx` only writes `<a:latin typeface="Arial"/>`. On Chinese Windows PowerPoint (`zh-CN`), Greek letters (`π, θ, φ, γ, β, μ, σ, λ, Δ`), degree signs (`°`), en-dashes (`–`), and arrows (`→`) are classified as East Asian Ambiguous Width characters and fall back to `Calibri` / `等线` / `宋体` unless `<a:ea>`, `<a:cs>`, `<a:sym>`, `<a:endParaRPr>`, and `ppt/theme/*.xml` are ALL set to `"Arial"`. Always call `set_rpr_all_font_slots()` and save with `save_presentation_with_uniform_font(prs, out_path, font_name="Arial")`.
   - **Vector Legend Markers (`add_ppt_vector_legend`)**: Never use Unicode geometric symbols (`●`, `■`) or space-padded strings inside legends; use `add_ppt_vector_legend()` to draw native PowerPoint vector shapes (`MSO_SHAPE.OVAL` / `MSO_SHAPE.RECTANGLE`) paired with independent `Arial` textboxes.
   - **Colorbar Axis Limits (`cbar.ax.get_ylim()`)**: For `contourf` plots with colorbars, always pass `cbar_ylim = cbar.ax.get_ylim()` (the actual contour bin boundaries after `fig.canvas.draw()`) rather than raw array `(vmin, vmax)` so colorbar tick numbers align to the exact pixel of the colorbar tick marks.

5. **Automated Package Audit & PowerPoint COM Visual Readback**:
   - Run `python scripts/editable_figure_pptx_kit.py audit OUTPUT.pptx --require-font Arial` to verify slide dimensions, native draggable textbox counts per slide, 100% single-font purity (`all_xml_typefaces == ["Arial"]`), zero literal `_` tokens, and zero corrupted PNG `transparency=(0, 0, 0)` chunks.
   - On Windows with Microsoft PowerPoint installed, run `python scripts/editable_figure_pptx_kit.py export-png OUTPUT.pptx --out-dir QA_DIR` to export `1920 × 1080` slide PNGs via PowerPoint COM and visually inspect the rendered slides.
