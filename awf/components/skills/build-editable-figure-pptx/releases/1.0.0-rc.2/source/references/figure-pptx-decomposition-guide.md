# Scientific Figure Decomposition & Editable PowerPoint Guide (`FigPPT`)

This reference documents the production architecture, failure modes, and pixel-level verification rules for decomposing composite scientific figures into native, editable PowerPoint (`.pptx`) slides.

---

## 1. The Five Failure Modes in Scientific Figure-to-PPTX Decomposition

When decomposing composite manuscript figures (from Word `.docx`, PDF pages, or Matplotlib/VMD composite canvases) into one-panel-per-slide PowerPoint decks, five recurring failure modes degrade publication quality:

### Failure Mode 1: Palette PNG `transparency=(0, 0, 0)` Corruption ("Hollow Text & Missing Black Spines")
- **Symptom**: After cropping a sub-panel from an exported slide or figure PNG and inserting it into PowerPoint, pure black pixels `(0, 0, 0)` become transparent. Black axis spines disappear, and black text/numbers with grey anti-aliased edges turn into hollow outlines.
- **Root Cause**: Many PNG exporters (including PowerPoint slide export and PDF renderers) save 8-bit paletted PNGs (`mode="P"`) with a palette transparency index in `im.info["transparency"]` (e.g., index `71`). Calling `Image.open(path).convert("RGB")` directly in Pillow converts `im.info["transparency"]` into an RGB tuple `(0, 0, 0)` and writes a PNG `tRNS` chunk when `crop.save(path)` is called. PowerPoint respects the `tRNS` chunk and renders all `(0, 0, 0)` pixels as transparent.
- **Mandatory Fix (`load_clean_rgb`)**:
  Always convert through `RGBA` onto a fresh opaque white `RGB` canvas so `im.info` is completely empty (`{}`):
  ```python
  from PIL import Image

  def load_clean_rgb(path):
      im = Image.open(path).convert("RGBA")
      bg = Image.new("RGB", im.size, (255, 255, 255))
      bg.paste(im, mask=im.split()[3])
      return bg
  ```

### Failure Mode 2: Erasing or Clipping Original Tick Numbers on 2D Plots
- **Symptom**: Either (a) outer axis titles are erased with a fixed rectangle that accidentally slices the leftmost X-tick number (e.g., `1.0` or `1800`) or top Y-tick number, or (b) tick numbers are erased and re-typed with an approximate linear pixel range that drifts from the actual tick marks.
- **Root Cause**: In multi-line or wide X-tick labels (`1800`, `1.0`), the leftmost character extends slightly left of the vertical Y-axis spine `bx0`. Meanwhile, rotated Y-axis titles sit further left (`bx0 - 65` to `bx0 - 35`), separated by a clean vertical white gap (`bx0 - 30` to `bx0 - 8`).
- **Mandatory Fix (Two Explicit Modes)**:
  - **Mode B (Preserve Original Tick Numbers — Default for Experimental Plots without Raw Arrays)**:
    Scan horizontal/vertical ink profiles outside the plot box `(bx0, by0, bx1, by1)` to find the exact white gap between the tick numbers and the outer axis titles. Erase *only* the outer title strips (and rotated left title strip up to the white gap) before cropping with `pad_ticks=(pl, pt, pr, pb)` so original tick marks and tick numbers remain 100% intact. Then place native PPTX textboxes for the X-axis title, rotated Y-axis title (`rotation=-90`), legend, and annotations.
  - **Mode A (Full Tick & Axis Replacement — For High-Resolution Plots with Known Axis Limits)**:
    Crop tightly to `(bx0 - pad, by0 - pad, bx1 + pad, by1 + pad)` where `pad` (`4–6 px`) preserves outward tick marks while excluding all original tick text, then place native PPTX tick labels at exact coordinates computed by `DataToPptBridge.x_to_ppt(val)` and `DataToPptBridge.y_to_ppt(val)`.

### Failure Mode 3: Aspect-Ratio Distortion & Coordinate Drift
- **Symptom**: Sub-panels look stretched, or overlaid PPTX callout arrows/labels miss their data peaks.
- **Mandatory Fix (`DataToPptBridge`)**:
  Compute `scale = min(max_w_in / crop_w_px, max_h_in / crop_h_px)` once, set `pic_w_in = crop_w_px * scale` and `pic_h_in = crop_h_px * scale`, and map every pixel `(px, py)` or data coordinate `(x_val, y_val)` through the affine bridge.

### Failure Mode 4: Plain-Text Chemical Formulas, East Asian Ambiguous-Width Font Fallback (`zh-CN`), and Symbol Legend Drift
- **Symptom**:
  1. Chemical formulas (`Na3V2(PO4)3`), scientific units (`mA g⁻¹`, `cm⁻¹`), or state labels (`S₀`, `D₁`) are inserted as unformatted plain text or rely on missing Unicode glyphs.
  2. On Chinese Windows PowerPoint (`zh-CN`), Greek symbols (`π, θ, φ, γ, β, μ, σ, λ, Δ`), degree signs (`°`), and en-dashes (`–`) render in `宋体` / `等线` / `Calibri` even when `run.font.name = "Arial"` was set, and clicking a textbox border displays `Calibri` or a blank font box.
  3. Legends using Unicode geometric symbols (`●`, `■`) trigger `Wingdings` / `Segoe UI Symbol` fallback, or space-padded legend labels (`"■ CD-NF    ■ CD-NC"`) collide with overlaid vector markers.
- **Root Cause**:
  - `python-pptx`'s `run.font.name = "Arial"` only writes `<a:latin typeface="Arial"/>`, leaving `<a:ea>`, `<a:cs>`, `<a:sym>`, `<a:endParaRPr>`, and `ppt/theme/theme1.xml` at default `Calibri` / East Asian fallback.
- **Mandatory Fix (`populate_paragraph_with_scripts`, `save_presentation_with_uniform_font`, `add_ppt_vector_legend`)**:
  1. Use inline markup (`_{...}` for subscript, `^{...}` for superscript) parsed into separate OpenXML `<a:r>` runs with `rPr.set("baseline", "-25000")` (subscript) or `rPr.set("baseline", "30000")` (superscript).
  2. Call `set_rpr_all_font_slots(rPr, "Arial")` on every run and `<a:endParaRPr>`, and save the deck via `save_presentation_with_uniform_font(prs, out_path, font_name="Arial")` so 100% of XML `typeface="..."` attributes in slides, layouts, masters, and themes equal `"Arial"`.
  3. Build legends with `add_ppt_vector_legend()` using native PowerPoint vector shapes (`MSO_SHAPE.OVAL` / `MSO_SHAPE.RECTANGLE`) and independent textboxes.
  4. For `contourf` colorbars, always map colorbar ticks using `cbar.ax.get_ylim()` after `fig.canvas.draw()` rather than raw data `(vmin, vmax)`.

### Failure Mode 5: Unverified Visual Overlaps
- **Symptom**: Native PPTX textboxes overlap with data curves, error bars, or adjacent labels.
- **Mandatory Fix**:
  1. Run `editable_figure_pptx_kit.py audit <file.pptx>` to verify 100% shape editability and check for unplanned textbox bounding-box collisions.
  2. Export every slide to PNG via Windows PowerPoint COM (`editable_figure_pptx_kit.py export-png <file.pptx> --out-dir <qa_dir>`) and visually inspect the rendered slides.

---

## 2. Standard Slide Layout Specification (16:9 Widescreen)

- **Slide Dimensions**: `13.333 in × 7.500 in` (`16:9` widescreen).
- **Top Header Bar**:
  - Panel badge (rounded rectangle, `0.18–0.85 in` wide, `0.42 in` high at `left=0.35 in, top=0.22 in`) with bold panel letter (`a`, `b`, `c`...) or figure code.
  - Slide title (`16–18 pt` Bold Arial, `left=1.05 in, top=0.22 in`) describing the sub-panel and its manuscript mapping (`[Manuscript Fig. Xy]`).
  - Optional subtitle / key metric summary (`11–12 pt` Italic/Regular at `top=0.56 in`).
- **Main Sub-Panel Canvas**:
  - Centered inside `left=0.60..12.70 in, top=0.95..6.85 in` (`max_w ≈ 11.2 in, max_h ≈ 5.6 in`).
  - For 2D plots, leave `0.75 in` on the left for the rotated Y-axis title and `0.55 in` on the bottom for the X-axis title.
- **Editable Metadata / Caption Footer** (optional):
  - `10–11 pt` grey textbox at `top=7.05 in` summarizing experimental conditions or computational level of theory.
