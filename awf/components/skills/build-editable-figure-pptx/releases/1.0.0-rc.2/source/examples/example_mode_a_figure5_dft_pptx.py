#!/usr/bin/env python3
"""
Build the Fully Editable PowerPoint (.pptx) for the Manuscript Computational Figures (v9):
1. `TPA_PQ_Figure5_DFT_Editable_Subpanels_v9.pptx`:
   - Slides 1 to 6: Panels (a) through (f) of Manuscript Figure 5, ONE COMPLETE SUB-PANEL PER SLIDE.
     Every single text label, axis title, tick number, bar value, callout badge, legend, and 3D molecular
     caption is a NATIVE, INDIVIDUALLY DRAGGABLE & EDITABLE PowerPoint shape/textbox (with native subscripts).
     The underlying Matplotlib plot base images contain ZERO baked-in text.
   - Slide 7: Complete 6-Panel Composite Overview of Figure 5 ((a)-(f) on one slide), where all text
     labels, axis titles, tick labels, badges, and legends are also native draggable PPT shapes.
   - Slides 8 to 17: 10 additional DFT sub-panels (Bond Orders, Dihedral Torsional Scan, Dimer Stacking
     & Coupling, Dimer MESP Surfaces, Active-Pocket Nucleophilicity, Interfacial Desolvation Ladder,
     Monomer HOMO/LUMO, Dimer HOMO/LUMO, Interfacial Solvated Complexes, 8-Axis Radar Chart), each on
     its own slide with 100% native draggable textboxes.
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize
from PIL import Image

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

ROOT = Path("/home/zc/mmdata/zln/20260701")
BASE = ROOT / "paper_upgrade_p0_p3_20261021"
FIG_DIR = BASE / "figures_publication_20261021"
INT_DIR = BASE / "figures_integrated_manuscript_20261021"
MS_DIR = BASE / "manuscript_20261021"
VMD_DIR = FIG_DIR / "vmd_renders"
TMP_ASSET_DIR = BASE / "pptx_editable_assets_v9"
TMP_ASSET_DIR.mkdir(parents=True, exist_ok=True)

# Unified Top-Journal Color Palette
HEX_PQ1 = "#B03A2E"
HEX_PQ1_LIGHT = "#EC7063"
HEX_PQ1_BG = "#FDEDEC"
HEX_PQ2 = "#1B4F72"
HEX_PQ2_LIGHT = "#5499C7"
HEX_PQ2_BG = "#EBF5FB"
HEX_ACCENT = "#117A65"
HEX_ACCENT_BG = "#E8F8F5"
HEX_TEXT = "#0F172A"
HEX_GRID = "#CBD5E1"
HEX_TRAP = "#D35400"

RGB_PQ1 = RGBColor(0xB0, 0x3A, 0x2E)
RGB_PQ1_LIGHT = RGBColor(0xEC, 0x70, 0x63)
RGB_PQ1_BG = RGBColor(0xFD, 0xED, 0xEC)
RGB_PQ2 = RGBColor(0x1B, 0x4F, 0x72)
RGB_PQ2_LIGHT = RGBColor(0x54, 0x99, 0xC7)
RGB_PQ2_BG = RGBColor(0xEB, 0xF5, 0xFB)
RGB_ACCENT = RGBColor(0x11, 0x7A, 0x65)
RGB_ACCENT_BG = RGBColor(0xE8, 0xF8, 0xF5)
RGB_TEXT = RGBColor(0x0F, 0x17, 0x2A)
RGB_MUTED = RGBColor(0x47, 0x55, 0x69)
RGB_WHITE = RGBColor(0xFF, 0xFF, 0xFF)
RGB_BLACK = RGBColor(0x00, 0x00, 0x00)
RGB_TRAP = RGBColor(0xD3, 0x54, 0x00)

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"],
    "axes.linewidth": 1.8,
    "xtick.major.width": 1.6,
    "ytick.major.width": 1.6,
    "xtick.major.size": 6.0,
    "ytick.major.size": 6.0,
})


def save_cropped_rgba(src_path: Path, out_path: Path) -> tuple[int, int]:
    """Crop whitespace/transparent margins around a VMD render and save as RGBA PNG."""
    img = Image.open(src_path).convert("RGBA")
    arr = np.array(img)
    alpha = arr[:, :, 3]
    non_white = np.max(255 - arr[:, :, :3], axis=-1) > 8
    mask = (alpha > 10) & non_white
    ys, xs = np.where(mask)
    if len(xs) > 0 and len(ys) > 0:
        pad = 8
        x0, x1 = max(0, int(np.min(xs)) - pad), min(arr.shape[1], int(np.max(xs)) + pad)
        y0, y1 = max(0, int(np.min(ys)) - pad), min(arr.shape[0], int(np.max(ys)) + pad)
        arr = arr[y0:y1, x0:x1]
    out_img = Image.fromarray(arr)
    out_img.save(out_path)
    return out_img.size


def style_clean_axes(ax, full_box: bool = True, grid_axis: str = "y", scale: float = 1.0):
    """Style axes with clean spines and gridlines, stripping all Matplotlib text labels."""
    ax.set_facecolor("white")
    for side in ["top", "right", "left", "bottom"]:
        ax.spines[side].set_visible(full_box if side in ("top", "right") else True)
        ax.spines[side].set_color(HEX_TEXT)
        ax.spines[side].set_linewidth(1.8 * scale)
    if grid_axis in ("x", "y", "both"):
        ax.grid(axis=grid_axis, linestyle="--", linewidth=0.85 * scale, color=HEX_GRID, alpha=0.65)
    else:
        ax.grid(False)
    ax.set_axisbelow(True)
    ax.tick_params(
        length=5.8 * scale,
        width=1.6 * scale,
        labelbottom=False,
        labelleft=False,
        labelright=False,
        labeltop=False,
    )


class CoordinateMapper:
    """Exact coordinate mapper from a Matplotlib Axes to PowerPoint slide inches."""

    def __init__(self, fig, ax, img_left_in: float, img_top_in: float, fig_w_in: float, fig_h_in: float):
        self.fig = fig
        self.ax = ax
        self.img_left_in = img_left_in
        self.img_top_in = img_top_in
        self.fig_w_in = fig_w_in
        self.fig_h_in = fig_h_in

    def data_to_ppt(self, x_data: float, y_data: float) -> tuple[float, float]:
        px, py = self.ax.transData.transform((x_data, y_data))
        fx_in = px / self.fig.dpi
        fy_in = py / self.fig.dpi
        return self.img_left_in + fx_in, self.img_top_in + (self.fig_h_in - fy_in)

    def axes_to_ppt(self, x_frac: float, y_frac: float) -> tuple[float, float]:
        px, py = self.ax.transAxes.transform((x_frac, y_frac))
        fx_in = px / self.fig.dpi
        fy_in = py / self.fig.dpi
        return self.img_left_in + fx_in, self.img_top_in + (self.fig_h_in - fy_in)


def set_run_font(run, font_pt: float, color: RGBColor, bold: bool = True, italic: bool = False, font_name: str = "Arial"):
    run.font.name = font_name
    run.font.size = Pt(font_pt)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color


def populate_paragraph_with_subscripts(
    p,
    line: str,
    font_pt: float,
    color: RGBColor,
    bold: bool = True,
    italic: bool = False,
    font_name: str = "Arial",
):
    """
    Parse scientific tokens like `W_v`, `λ_reorg`, `λ_h`, `d_min`, `θ_eq`, `V_min`, `ΔE_Na`, `ΔE_exch`, `|J_h|`, `C_PQ`
    into native PowerPoint subscript runs (`run._r.get_or_add_rPr().set('baseline', '-25000')`).
    """
    parts = re.split(r"(_(?:reorg|exch|min|eq|PQ|Na|h|v))", line)
    for part in parts:
        if not part:
            continue
        if part.startswith("_") and len(part) > 1:
            r = p.add_run()
            r.text = part[1:]
            set_run_font(r, font_pt=font_pt, color=color, bold=bold, italic=italic, font_name=font_name)
            r._r.get_or_add_rPr().set("baseline", "-25000")
        else:
            r = p.add_run()
            r.text = part
            set_run_font(r, font_pt=font_pt, color=color, bold=bold, italic=italic, font_name=font_name)


def add_ppt_text(
    slide,
    x_in: float,
    y_in: float,
    text: str,
    font_pt: float = 13.0,
    color: RGBColor = RGB_TEXT,
    bold: bool = True,
    italic: bool = False,
    ha: str = "center",
    va: str = "center",
    w_in: float | None = None,
    h_in: float | None = None,
    rotation: float = 0.0,
    font_name: str = "Arial",
):
    """
    Add a freely draggable, native PowerPoint textbox anchored at (x_in, y_in)
    following Matplotlib (ha, va) semantics.
    """
    lines = text.split("\n")
    max_len = max(len(line) for line in lines) if lines else 1
    if w_in is None:
        w_in = max(0.65, max_len * (font_pt / 72.0) * 0.68 + 0.28)
    if h_in is None:
        h_in = max(0.28, len(lines) * (font_pt / 72.0) * 1.35 + 0.10)

    if rotation != 0.0:
        left = x_in - w_in / 2.0
        top = y_in - h_in / 2.0
    else:
        if ha == "center":
            left = x_in - w_in / 2.0
        elif ha == "left":
            left = x_in
        elif ha == "right":
            left = x_in - w_in
        else:
            left = x_in - w_in / 2.0

        if va == "center":
            top = y_in - h_in / 2.0
        elif va == "bottom":
            top = y_in - h_in
        elif va == "top":
            top = y_in
        else:
            top = y_in - h_in / 2.0

    tb = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(w_in), Inches(h_in))
    if rotation != 0.0:
        tb.rotation = rotation

    tf = tb.text_frame
    tf.word_wrap = False
    tf.margin_left = Pt(2)
    tf.margin_right = Pt(2)
    tf.margin_top = Pt(1)
    tf.margin_bottom = Pt(1)

    if rotation != 0.0 or va == "center":
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    elif va == "bottom":
        tf.vertical_anchor = MSO_ANCHOR.BOTTOM
    elif va == "top":
        tf.vertical_anchor = MSO_ANCHOR.TOP

    align_map = {
        "center": PP_ALIGN.CENTER,
        "left": PP_ALIGN.LEFT,
        "right": PP_ALIGN.RIGHT,
    }
    p_align = align_map.get(ha, PP_ALIGN.CENTER) if rotation == 0.0 else PP_ALIGN.CENTER

    for idx, line in enumerate(lines):
        p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
        p.alignment = p_align
        populate_paragraph_with_subscripts(p, line, font_pt=font_pt, color=color, bold=bold, italic=italic, font_name=font_name)

    return tb


def add_ppt_badge(
    slide,
    x_in: float,
    y_in: float,
    text: str,
    font_pt: float = 12.0,
    text_color: RGBColor = RGB_ACCENT,
    fill_color: RGBColor = RGB_ACCENT_BG,
    border_color: RGBColor = RGB_ACCENT,
    ha: str = "center",
    va: str = "bottom",
    w_in: float | None = None,
    h_in: float | None = None,
    border_pt: float = 1.2,
):
    """
    Add a draggable native PowerPoint rounded-rectangle badge with editable text inside.
    """
    lines = text.split("\n")
    max_len = max(len(line) for line in lines) if lines else 1
    if w_in is None:
        w_in = max(0.72, max_len * (font_pt / 72.0) * 0.62 + 0.24)
    if h_in is None:
        h_in = max(0.30, len(lines) * (font_pt / 72.0) * 1.32 + 0.12)

    if ha == "center":
        left = x_in - w_in / 2.0
    elif ha == "left":
        left = x_in
    elif ha == "right":
        left = x_in - w_in
    else:
        left = x_in - w_in / 2.0

    if va == "center":
        top = y_in - h_in / 2.0
    elif va == "bottom":
        top = y_in - h_in
    elif va == "top":
        top = y_in
    else:
        top = y_in - h_in / 2.0

    shp = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        Inches(left), Inches(top), Inches(w_in), Inches(h_in)
    )
    if len(shp.adjustments) > 0:
        shp.adjustments[0] = 0.18
    shp.fill.solid()
    shp.fill.fore_color.rgb = fill_color
    shp.line.color.rgb = border_color
    shp.line.width = Pt(border_pt)

    tf = shp.text_frame
    tf.word_wrap = False
    tf.margin_left = Pt(3)
    tf.margin_right = Pt(3)
    tf.margin_top = Pt(2)
    tf.margin_bottom = Pt(2)
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE

    for idx, line in enumerate(lines):
        p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
        p.alignment = PP_ALIGN.CENTER
        populate_paragraph_with_subscripts(p, line, font_pt=font_pt, color=text_color, bold=True)

    return shp


def add_ppt_legend(
    slide,
    left_in: float,
    top_in: float,
    items: list[tuple[str, RGBColor, str]],
    font_pt: float = 12.0,
    w_in: float = 2.15,
    row_h_in: float = 0.28,
    scale: float = 1.0,
):
    """
    Add a native PowerPoint legend composed of a draggable background box,
    draggable colored swatches, and draggable text labels.
    """
    pad_v = 0.12 * scale
    h_in = len(items) * row_h_in + pad_v
    bg = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        Inches(left_in), Inches(top_in), Inches(w_in), Inches(h_in)
    )
    if len(bg.adjustments) > 0:
        bg.adjustments[0] = 0.08
    bg.fill.solid()
    bg.fill.fore_color.rgb = RGB_WHITE
    bg.line.color.rgb = RGBColor(0xCB, 0xD5, 0xE1)
    bg.line.width = Pt(1.0 * scale)

    for idx, (lbl, col_rgb, stype) in enumerate(items):
        cy = top_in + 0.5 * pad_v + (idx + 0.5) * row_h_in
        sx = left_in + 0.11 * scale
        if stype == "bar":
            sw = slide.shapes.add_shape(
                MSO_SHAPE.RECTANGLE,
                Inches(sx), Inches(cy - 0.065 * scale), Inches(0.26 * scale), Inches(0.13 * scale)
            )
            sw.fill.solid()
            sw.fill.fore_color.rgb = col_rgb
            sw.line.color.rgb = RGB_BLACK
            sw.line.width = Pt(0.8 * scale)
        elif stype == "line":
            sw = slide.shapes.add_shape(
                MSO_SHAPE.RECTANGLE,
                Inches(sx), Inches(cy - 0.025 * scale), Inches(0.26 * scale), Inches(0.05 * scale)
            )
            sw.fill.solid()
            sw.fill.fore_color.rgb = col_rgb
            sw.line.color.rgb = col_rgb
        elif stype == "star":
            sw = slide.shapes.add_shape(
                MSO_SHAPE.STAR_5_POINT,
                Inches(sx + 0.03 * scale), Inches(cy - 0.085 * scale), Inches(0.17 * scale), Inches(0.17 * scale)
            )
            sw.fill.solid()
            sw.fill.fore_color.rgb = col_rgb
            sw.line.color.rgb = col_rgb
        add_ppt_text(
            slide, sx + 0.32 * scale, cy, lbl,
            font_pt=font_pt, color=RGB_TEXT, bold=True, ha="left", va="center",
            w_in=w_in - 0.44 * scale, h_in=row_h_in
        )


def add_slide_header(slide, title_str: str, subtitle_str: str):
    """Add an editable slide header banner at the top of each single-panel slide."""
    add_ppt_text(
        slide, 0.55, 0.18, title_str,
        font_pt=16.0, color=RGB_TEXT, bold=True, ha="left", va="top", w_in=12.2, h_in=0.34
    )
    add_ppt_text(
        slide, 0.55, 0.50, subtitle_str,
        font_pt=11.5, color=RGB_MUTED, bold=False, ha="left", va="top", w_in=12.2, h_in=0.28,
        font_name="Microsoft YaHei"
    )


def add_standard_axes_labels(
    slide,
    mapper: CoordinateMapper,
    panel_letter: str,
    xticks: list[tuple[float, str]],
    yticks: list[tuple[float, str]],
    xlabel: str | None = None,
    ylabel: str | None = None,
    scale: float = 1.0,
    x_tick_dy_in: float = 0.09,
    y_tick_dx_in: float = 0.11,
    ylabel_dx_in: float = 0.72,
    xlabel_dy_in: float = 0.52,
):
    """Add panel label (a)-(f), X/Y tick labels, and X/Y axis titles as native draggable PPT textboxes."""
    px0, py0 = mapper.axes_to_ppt(0.0, 1.0)
    add_ppt_text(
        slide, px0 - 0.68 * scale, py0 - 0.06 * scale, f"({panel_letter})",
        font_pt=20.0 * scale, color=RGB_TEXT, bold=True, ha="left", va="bottom",
        w_in=0.65 * scale, h_in=0.40 * scale
    )

    _, y_bot_in = mapper.axes_to_ppt(0.0, 0.0)
    for xv, xlbl in xticks:
        xt_in, _ = mapper.data_to_ppt(xv, 0.0)
        add_ppt_text(
            slide, xt_in, y_bot_in + x_tick_dy_in * scale, xlbl,
            font_pt=12.5 * scale, color=RGB_TEXT, bold=True, ha="center", va="top"
        )

    x_left_in, _ = mapper.axes_to_ppt(0.0, 0.0)
    for yv, ylbl in yticks:
        _, yt_in = mapper.data_to_ppt(0.0, yv)
        add_ppt_text(
            slide, x_left_in - y_tick_dx_in * scale, yt_in, ylbl,
            font_pt=12.5 * scale, color=RGB_TEXT, bold=True, ha="right", va="center"
        )

    if xlabel:
        xc_in, _ = mapper.axes_to_ppt(0.5, 0.0)
        add_ppt_text(
            slide, xc_in, y_bot_in + xlabel_dy_in * scale, xlabel,
            font_pt=14.5 * scale, color=RGB_TEXT, bold=True, ha="center", va="top",
            w_in=5.5 * scale, h_in=0.38 * scale
        )

    if ylabel:
        _, yc_in = mapper.axes_to_ppt(0.0, 0.5)
        add_ppt_text(
            slide, x_left_in - ylabel_dx_in * scale, yc_in, ylabel,
            font_pt=14.5 * scale, color=RGB_TEXT, bold=True, ha="center", va="center",
            w_in=4.5 * scale, h_in=0.42 * scale, rotation=-90.0
        )


# ==============================================================================
# SLIDE 1 — Figure 5(a): Anodic Oxidation Thresholds (Monomer VIP/AIP & Dimer AIP)
# ==============================================================================
def build_panel_5a(slide, img_left: float, img_top: float, fig_w: float, fig_h: float, scale: float = 1.0, tag: str = "single"):
    fig = plt.figure(figsize=(fig_w, fig_h), dpi=300)
    fig.patch.set_alpha(0.0)
    ax = fig.add_axes([0.16, 0.18, 0.79, 0.74])
    style_clean_axes(ax, full_box=True, grid_axis="y", scale=scale)

    metrics_ox = ["Mono VIP\n(M⁰ → M⁺•)", "Mono AIP\n(M⁰ → M⁺•)", "Dimer AIP\n(D⁰ → D⁺•)"]
    pq1_ox = [5.224, 5.111, 4.720]
    pq2_ox = [5.287, 5.166, 4.765]
    x_ox = np.arange(len(metrics_ox))
    w = 0.35

    b_ox1 = ax.bar(x_ox - w/2, pq1_ox, width=w, color=HEX_PQ1, edgecolor="black", lw=1.1 * scale)
    b_ox2 = ax.bar(x_ox + w/2, pq2_ox, width=w, color=HEX_PQ2_LIGHT, edgecolor="black", lw=1.1 * scale)
    ax.set_xticks(x_ox)
    ax.set_ylim(4.45, 5.55)
    yticks = [4.6, 4.8, 5.0, 5.2, 5.4]
    ax.set_yticks(yticks)

    mapper = CoordinateMapper(fig, ax, img_left, img_top, fig_w, fig_h)
    png_path = TMP_ASSET_DIR / f"fig5a_base_{tag}.png"
    fig.savefig(png_path, dpi=300, transparent=True)
    plt.close(fig)

    slide.shapes.add_picture(str(png_path), Inches(img_left), Inches(img_top), width=Inches(fig_w), height=Inches(fig_h))

    add_standard_axes_labels(
        slide, mapper, "a",
        xticks=[(float(i), lbl) for i, lbl in enumerate(metrics_ox)],
        yticks=[(yv, f"{yv:.1f}") for yv in yticks],
        ylabel="Oxidation Potential (eV)",
        scale=scale,
        ylabel_dx_in=0.72,
    )

    for i, (r1, r2) in enumerate(zip(b_ox1, b_ox2)):
        v1, v2 = r1.get_height(), r2.get_height()
        diff_mev = (v1 - v2) * 1000.0
        x1_in, y1_in = mapper.data_to_ppt(r1.get_x() + r1.get_width()/2 - 0.02, v1 + 0.015)
        x2_in, y2_in = mapper.data_to_ppt(r2.get_x() + r2.get_width()/2 + 0.02, v2 + 0.015)
        xb_in, yb_in = mapper.data_to_ppt(float(x_ox[i]), max(v1, v2) + 0.095)

        add_ppt_text(slide, x1_in, y1_in, f"{v1:.2f}", font_pt=11.5 * scale, color=RGB_PQ1, bold=True, ha="center", va="bottom")
        add_ppt_text(slide, x2_in, y2_in, f"{v2:.2f}", font_pt=11.5 * scale, color=RGB_PQ2, bold=True, ha="center", va="bottom")
        add_ppt_badge(
            slide, xb_in, yb_in, f"{diff_mev:.0f} meV",
            font_pt=11.5 * scale, text_color=RGB_ACCENT, fill_color=RGB_ACCENT_BG, border_color=RGB_ACCENT,
            ha="center", va="bottom", w_in=0.92 * scale, h_in=0.30 * scale, border_pt=1.2 * scale
        )

    leg_x, leg_y = mapper.axes_to_ppt(0.56, 0.96)
    add_ppt_legend(
        slide, leg_x, leg_y,
        [("TPA-PQ1 (para)", RGB_PQ1, "bar"), ("TPA-PQ2 (meta)", RGB_PQ2_LIGHT, "bar")],
        font_pt=11.5 * scale, w_in=2.10 * scale, row_h_in=0.27 * scale, scale=scale
    )


# ==============================================================================
# SLIDE 2 — Figure 5(b): Radical Cation Spin Density Isosurfaces (0.004 a.u.)
# ==============================================================================
def build_panel_5b(slide, img_left: float, img_top: float, fig_w: float, fig_h: float, scale: float = 1.0):
    box_l = img_left + 0.16 * fig_w
    box_t = img_top + (1.0 - 0.18 - 0.74) * fig_h
    box_w = 0.79 * fig_w
    box_h = 0.74 * fig_h

    frame = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(box_l), Inches(box_t), Inches(box_w), Inches(box_h)
    )
    frame.fill.solid()
    frame.fill.fore_color.rgb = RGB_WHITE
    frame.line.color.rgb = RGB_TEXT
    frame.line.width = Pt(1.8 * scale)

    add_ppt_text(
        slide, box_l - 0.65 * scale, box_t - 0.06 * scale, "(b)",
        font_pt=20.0 * scale, color=RGB_TEXT, bold=True, ha="left", va="bottom",
        w_in=0.65 * scale, h_in=0.40 * scale
    )

    p1_crop = TMP_ASSET_DIR / "pq1_rad_spin_crop.png"
    p2_crop = TMP_ASSET_DIR / "pq2_rad_spin_crop.png"
    w1, h1 = save_cropped_rgba(VMD_DIR / "pq1_rad_spin.png", p1_crop)
    w2, h2 = save_cropped_rgba(VMD_DIR / "pq2_rad_spin.png", p2_crop)

    for p_img, pw, ph, y_rel_top, y_rel_lbl, lbl_txt, col_rgb in [
        (p1_crop, w1, h1, 0.04, 0.47, "TPA-PQ1⁺• (λ_h = 228.9 meV, Delocalized)", RGB_PQ1),
        (p2_crop, w2, h2, 0.52, 0.93, "TPA-PQ2⁺• (λ_h = 242.7 meV, Meta-Blocked)", RGB_PQ2),
    ]:
        avail_w = box_w * 0.88
        avail_h = box_h * 0.40
        sc = min(avail_w / pw, avail_h / ph)
        disp_w, disp_h = pw * sc, ph * sc
        mx = box_l + (box_w - disp_w) / 2.0
        my = box_t + y_rel_top * box_h + (avail_h - disp_h) / 2.0
        slide.shapes.add_picture(str(p_img), Inches(mx), Inches(my), width=Inches(disp_w), height=Inches(disp_h))
        add_ppt_text(
            slide, box_l + box_w / 2.0, box_t + y_rel_lbl * box_h, lbl_txt,
            font_pt=11.5 * scale, color=col_rgb, bold=True, ha="center", va="top",
            w_in=box_w * 0.96, h_in=0.30 * scale
        )

    add_ppt_text(
        slide, box_l + box_w / 2.0, box_t + box_h + 0.14 * scale,
        "Spin Density Isosurface (0.004 a.u.)",
        font_pt=14.5 * scale, color=RGB_TEXT, bold=True, ha="center", va="top",
        w_in=box_w, h_in=0.38 * scale
    )


# ==============================================================================
# SLIDE 3 — Figure 5(c): Oligomer Frontier Orbital Evolution (n = 1 -> 2 -> 3) & W_v
# ==============================================================================
def build_panel_5c(slide, img_left: float, img_top: float, fig_w: float, fig_h: float, scale: float = 1.0, tag: str = "single"):
    fig = plt.figure(figsize=(fig_w, fig_h), dpi=300)
    fig.patch.set_alpha(0.0)
    ax = fig.add_axes([0.16, 0.18, 0.79, 0.74])
    style_clean_axes(ax, full_box=True, grid_axis="y", scale=scale)

    x_cols = [0.8, 1.8, 2.8, 4.2, 5.2, 6.2]
    col_labels = ["PQ1\nn=1", "PQ1\nn=2", "PQ1\nn=3", "PQ2\nn=1", "PQ2\nn=2", "PQ2\nn=3"]
    orb_data = [
        ([-5.6692], [-2.9576], 2.71, HEX_PQ1, RGB_PQ1),
        ([-5.5147, -5.8964], [-3.0050, -2.9995], 2.51, HEX_PQ1, RGB_PQ1),
        ([-5.4989, -5.7397, -6.0099], [-3.0558, -3.0324, -3.0308], 2.44, HEX_PQ1, RGB_PQ1),
        ([-5.6643], [-3.0115], 2.65, HEX_PQ2, RGB_PQ2),
        ([-5.5577, -5.9775], [-3.0450, -3.0450], 2.51, HEX_PQ2, RGB_PQ2),
        ([-5.5857, -5.7413, -5.9587], [-3.2501, -3.1394, -2.9282], 2.34, HEX_PQ2, RGB_PQ2),
    ]
    for x, (homos, lumos, gap, col_hex, _) in zip(x_cols, orb_data):
        if len(homos) > 1:
            rect = Rectangle((x - 0.28, min(homos)), 0.56, max(homos) - min(homos),
                             facecolor=col_hex, alpha=0.18, edgecolor=col_hex, lw=1.0 * scale)
            ax.add_patch(rect)
        for idx_h, h_val in enumerate(homos):
            ax.plot([x - 0.26, x + 0.26], [h_val, h_val], color=col_hex, lw=(3.0 if idx_h == 0 else 1.6) * scale)
        for idx_l, l_val in enumerate(lumos):
            ax.plot([x - 0.26, x + 0.26], [l_val, l_val], color=col_hex, lw=(3.0 if idx_l == 0 else 1.6) * scale)

    ax.plot(x_cols[:3], [-5.6692, -5.5147, -5.4989], color=HEX_PQ1, ls="--", lw=1.8 * scale, marker="o", ms=6 * scale)
    ax.plot(x_cols[3:], [-5.6643, -5.5577, -5.5857], color=HEX_PQ2, ls="--", lw=1.8 * scale, marker="s", ms=6 * scale)
    ax.axvline(3.5, color="#94A3B8", ls="-.", lw=1.4 * scale)
    ax.set_xticks(x_cols)
    ax.set_ylim(-6.30, -2.55)
    ax.set_xlim(0.10, 6.90)
    yticks = [-6.0, -5.5, -5.0, -4.5, -4.0, -3.5, -3.0]
    ax.set_yticks(yticks)

    mapper = CoordinateMapper(fig, ax, img_left, img_top, fig_w, fig_h)
    png_path = TMP_ASSET_DIR / f"fig5c_base_{tag}.png"
    fig.savefig(png_path, dpi=300, transparent=True)
    plt.close(fig)

    slide.shapes.add_picture(str(png_path), Inches(img_left), Inches(img_top), width=Inches(fig_w), height=Inches(fig_h))

    add_standard_axes_labels(
        slide, mapper, "c",
        xticks=list(zip(x_cols, col_labels)),
        yticks=[(yv, f"{yv:.1f}") for yv in yticks],
        ylabel="Orbital Energy (eV)",
        scale=scale,
        ylabel_dx_in=0.72,
    )

    for x, (homos, lumos, gap, _, col_rgb) in zip(x_cols, orb_data):
        xh_in, yh_in = mapper.data_to_ppt(x, homos[0] + 0.06)
        xl_in, yl_in = mapper.data_to_ppt(x, lumos[0] - 0.07)
        add_ppt_text(slide, xh_in, yh_in, f"{homos[0]:.2f}", font_pt=10.8 * scale, color=col_rgb, bold=True, ha="center", va="bottom")
        add_ppt_text(slide, xl_in, yl_in, f"{lumos[0]:.2f}", font_pt=10.8 * scale, color=col_rgb, bold=True, ha="center", va="top")

    b1_x, b1_y = mapper.data_to_ppt(1.78, -4.25)
    b2_x, b2_y = mapper.data_to_ppt(5.22, -4.25)
    add_ppt_badge(
        slide, b1_x, b1_y, "PQ1: W_v = 511 meV\n(ΔHOMO = +170 meV)",
        font_pt=10.5 * scale, text_color=RGB_PQ1, fill_color=RGB_PQ1_BG, border_color=RGB_PQ1,
        ha="center", va="center", w_in=2.15 * scale, h_in=0.52 * scale, border_pt=1.2 * scale
    )
    add_ppt_badge(
        slide, b2_x, b2_y, "PQ2: W_v = 373 meV\n(ΔHOMO = +79 meV)",
        font_pt=10.5 * scale, text_color=RGB_PQ2, fill_color=RGB_PQ2_BG, border_color=RGB_PQ2,
        ha="center", va="center", w_in=2.15 * scale, h_in=0.52 * scale, border_pt=1.2 * scale
    )


# ==============================================================================
# SLIDE 4 — Figure 5(d): Bipolar Four-State Reorganization Energies lambda_reorg
# ==============================================================================
def build_panel_5d(slide, img_left: float, img_top: float, fig_w: float, fig_h: float, scale: float = 1.0, tag: str = "single"):
    fig = plt.figure(figsize=(fig_w, fig_h), dpi=300)
    fig.patch.set_alpha(0.0)
    ax = fig.add_axes([0.16, 0.18, 0.79, 0.74])
    style_clean_axes(ax, full_box=True, grid_axis="y", scale=scale)

    regimes = ["p-Bare\n(D⁰↔D⁺)", "p-PF₆⁻\n(D⁺·PF₆⁻)", "n-1Na⁺\n(0↔1Na)", "n-2Na⁺\n(1↔2Na)"]
    lam_pq1 = [6.856, 5.756, 11.495, 13.720]
    lam_pq2 = [7.419, 6.874, 12.465, 14.958]
    x_lam = np.arange(len(regimes))
    w = 0.35

    b_l1 = ax.bar(x_lam - w/2, lam_pq1, width=w, color=HEX_PQ1, edgecolor="black", lw=1.1 * scale)
    b_l2 = ax.bar(x_lam + w/2, lam_pq2, width=w, color=HEX_PQ2_LIGHT, edgecolor="black", lw=1.1 * scale)
    ax.set_xticks(x_lam)
    ax.set_ylim(0, 18.2)
    yticks = [0, 3, 6, 9, 12, 15, 18]
    ax.set_yticks(yticks)

    mapper = CoordinateMapper(fig, ax, img_left, img_top, fig_w, fig_h)
    png_path = TMP_ASSET_DIR / f"fig5d_base_{tag}.png"
    fig.savefig(png_path, dpi=300, transparent=True)
    plt.close(fig)

    slide.shapes.add_picture(str(png_path), Inches(img_left), Inches(img_top), width=Inches(fig_w), height=Inches(fig_h))

    add_standard_axes_labels(
        slide, mapper, "d",
        xticks=[(float(i), lbl) for i, lbl in enumerate(regimes)],
        yticks=[(float(yv), str(yv)) for yv in yticks],
        ylabel="λ_reorg (kcal mol⁻¹)",
        scale=scale,
        ylabel_dx_in=0.72,
    )

    for i, (r1, r2) in enumerate(zip(b_l1, b_l2)):
        v1, v2 = r1.get_height(), r2.get_height()
        pct = (v1 - v2) / v2 * 100.0
        x1_in, y1_in = mapper.data_to_ppt(r1.get_x() + r1.get_width()/2 - 0.03, v1 + 0.25)
        x2_in, y2_in = mapper.data_to_ppt(r2.get_x() + r2.get_width()/2 + 0.03, v2 + 0.25)
        xb_in, yb_in = mapper.data_to_ppt(float(x_lam[i]), max(v1, v2) + 1.45)

        add_ppt_text(slide, x1_in, y1_in, f"{v1:.2f}", font_pt=11.0 * scale, color=RGB_PQ1, bold=True, ha="center", va="bottom")
        add_ppt_text(slide, x2_in, y2_in, f"{v2:.2f}", font_pt=11.0 * scale, color=RGB_PQ2, bold=True, ha="center", va="bottom")
        add_ppt_badge(
            slide, xb_in, yb_in, f"{pct:.1f}%",
            font_pt=11.2 * scale, text_color=RGB_ACCENT, fill_color=RGB_ACCENT_BG, border_color=RGB_ACCENT,
            ha="center", va="bottom", w_in=0.78 * scale, h_in=0.28 * scale, border_pt=1.2 * scale
        )

    leg_x, leg_y = mapper.axes_to_ppt(0.03, 0.96)
    add_ppt_legend(
        slide, leg_x, leg_y,
        [("TPA-PQ1 (para)", RGB_PQ1, "bar"), ("TPA-PQ2 (meta)", RGB_PQ2_LIGHT, "bar")],
        font_pt=11.5 * scale, w_in=2.10 * scale, row_h_in=0.27 * scale, scale=scale
    )


# ==============================================================================
# SLIDE 5 — Figure 5(e): 32-Rotamer Ensemble Pocket Distance & 4O-Na+ Trap
# ==============================================================================
def build_panel_5e(slide, img_left: float, img_top: float, fig_w: float, fig_h: float, scale: float = 1.0, tag: str = "single"):
    fig = plt.figure(figsize=(fig_w, fig_h), dpi=300)
    fig.patch.set_alpha(0.0)
    ax = fig.add_axes([0.16, 0.18, 0.79, 0.74])
    style_clean_axes(ax, full_box=True, grid_axis="y", scale=scale)

    pq1_linker_dmin = [23.40, 23.58, 23.40, 23.58, 23.55, 23.74, 23.55, 23.74]
    pq2_linker_dmin = [8.35, 21.40, 20.96, 21.93, 8.35, 18.41, 19.76, 19.43]
    pq1_32 = np.array([21.42, 21.65, 21.88, 22.10, 22.35, 22.60, 22.85, 23.10, 23.40, 23.55, 23.58, 23.74])
    pq2_32 = np.array([7.96, 8.15, 8.35, 8.35, 11.20, 14.50, 18.41, 19.43, 19.76, 20.96, 21.40, 21.93])

    parts = ax.violinplot([pq1_32, pq2_32], positions=[0, 1], widths=0.48, showmeans=True, showextrema=True)
    for idx_pc, pc in enumerate(parts["bodies"]):
        pc.set_facecolor(HEX_PQ1 if idx_pc == 0 else HEX_PQ2_LIGHT)
        pc.set_edgecolor("black")
        pc.set_alpha(0.45)
    for k in ("cmeans", "cbars", "cmins", "cmaxes"):
        parts[k].set_color("black")

    jitter = np.linspace(-0.12, 0.12, len(pq1_linker_dmin))
    ax.scatter(np.zeros_like(pq1_linker_dmin) + jitter, pq1_linker_dmin, color=HEX_PQ1, edgecolor="white", s=65 * scale, zorder=5)
    ax.scatter(np.ones_like(pq2_linker_dmin) + jitter, pq2_linker_dmin, color=HEX_PQ2, edgecolor="white", s=65 * scale, zorder=5)
    ax.scatter([1.0], [3.12], color=HEX_TRAP, marker="*", s=200 * scale, zorder=6)
    ax.axhspan(21.42, 23.74, color=HEX_PQ1, alpha=0.10)

    ax.set_xticks([0, 1])
    ax.set_ylim(1.5, 27.5)
    ax.set_xlim(-0.45, 1.48)
    yticks = [5, 10, 15, 20, 25]
    ax.set_yticks(yticks)

    mapper = CoordinateMapper(fig, ax, img_left, img_top, fig_w, fig_h)
    png_path = TMP_ASSET_DIR / f"fig5e_base_{tag}.png"
    fig.savefig(png_path, dpi=300, transparent=True)
    plt.close(fig)

    slide.shapes.add_picture(str(png_path), Inches(img_left), Inches(img_top), width=Inches(fig_w), height=Inches(fig_h))

    add_standard_axes_labels(
        slide, mapper, "e",
        xticks=[(0.0, "TPA-PQ1 (n=3)"), (1.0, "TPA-PQ2 (n=3)")],
        yticks=[(float(yv), str(yv)) for yv in yticks],
        ylabel="Pocket Distance d_min (Å)",
        scale=scale,
        ylabel_dx_in=0.72,
    )

    tx1_in, ty1_in = mapper.data_to_ppt(0.0, 24.3)
    add_ppt_text(
        slide, tx1_in, ty1_in, "32/32 Open 2O–Na⁺ (21.4–23.7 Å)",
        font_pt=11.0 * scale, color=RGB_PQ1, bold=True, ha="center", va="bottom",
        w_in=3.4 * scale, h_in=0.32 * scale
    )

    bx_in, by_in = mapper.data_to_ppt(0.72, 4.3)
    add_ppt_badge(
        slide, bx_in, by_in, "4O–Na⁺ Sandwich Trap\n(3.12 Å, ΔΔE = -22.8 kcal mol⁻¹)",
        font_pt=10.5 * scale, text_color=RGB_PQ2, fill_color=RGB_PQ2_BG, border_color=RGB_PQ2,
        ha="center", va="bottom", w_in=2.75 * scale, h_in=0.52 * scale, border_pt=1.2 * scale
    )

    leg_x, leg_y = mapper.axes_to_ppt(0.03, 0.54)
    add_ppt_legend(
        slide, leg_x, leg_y,
        [("PQ2 4O–Na⁺ Trap (3.12 Å)", RGB_TRAP, "star")],
        font_pt=10.8 * scale, w_in=2.55 * scale, row_h_in=0.30 * scale, scale=scale
    )


# ==============================================================================
# SLIDE 6 — Figure 5(f): Relaxed 3D Trimer Conformations (Open Rod vs Folded Trap)
# ==============================================================================
def build_panel_5f(slide, img_left: float, img_top: float, fig_w: float, fig_h: float, scale: float = 1.0):
    box_l = img_left + 0.16 * fig_w
    box_t = img_top + (1.0 - 0.18 - 0.74) * fig_h
    box_w = 0.79 * fig_w
    box_h = 0.74 * fig_h

    frame = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(box_l), Inches(box_t), Inches(box_w), Inches(box_h)
    )
    frame.fill.solid()
    frame.fill.fore_color.rgb = RGB_WHITE
    frame.line.color.rgb = RGB_TEXT
    frame.line.width = Pt(1.8 * scale)

    add_ppt_text(
        slide, box_l - 0.65 * scale, box_t - 0.06 * scale, "(f)",
        font_pt=20.0 * scale, color=RGB_TEXT, bold=True, ha="left", va="bottom",
        w_in=0.65 * scale, h_in=0.40 * scale
    )

    t1_crop = TMP_ASSET_DIR / "pq1_trimer_open_crop.png"
    t2_crop = TMP_ASSET_DIR / "pq2_trimer_folded_crop.png"
    w1, h1 = save_cropped_rgba(VMD_DIR / "pq1_trimer_open.png", t1_crop)
    w2, h2 = save_cropped_rgba(VMD_DIR / "pq2_trimer_folded.png", t2_crop)

    for p_img, pw, ph, y_rel_top, y_rel_lbl, lbl_txt, col_rgb in [
        (t1_crop, w1, h1, 0.04, 0.47, "TPA-PQ1 (n=3): Open Rod (2O–Na⁺, 11.5 Å)", RGB_PQ1),
        (t2_crop, w2, h2, 0.52, 0.93, "TPA-PQ2 (n=3): Folded 4O–Na⁺ Trap (10.6 Å)", RGB_PQ2),
    ]:
        avail_w = box_w * 0.88
        avail_h = box_h * 0.40
        sc = min(avail_w / pw, avail_h / ph)
        disp_w, disp_h = pw * sc, ph * sc
        mx = box_l + (box_w - disp_w) / 2.0
        my = box_t + y_rel_top * box_h + (avail_h - disp_h) / 2.0
        slide.shapes.add_picture(str(p_img), Inches(mx), Inches(my), width=Inches(disp_w), height=Inches(disp_h))
        add_ppt_text(
            slide, box_l + box_w / 2.0, box_t + y_rel_lbl * box_h, lbl_txt,
            font_pt=11.2 * scale, color=col_rgb, bold=True, ha="center", va="top",
            w_in=box_w * 0.96, h_in=0.30 * scale
        )

    add_ppt_text(
        slide, box_l + box_w / 2.0, box_t + box_h + 0.14 * scale,
        "Relaxed Trimer (n = 3)",
        font_pt=14.5 * scale, color=RGB_TEXT, bold=True, ha="center", va="top",
        w_in=box_w, h_in=0.38 * scale
    )


# ==============================================================================
# ADDITIONAL DFT SUB-PANELS (Slides 8 - 17)
# ==============================================================================
def build_extra_bond_orders(slide, img_left: float, img_top: float, fig_w: float, fig_h: float, scale: float = 1.0):
    fig = plt.figure(figsize=(fig_w, fig_h), dpi=300)
    fig.patch.set_alpha(0.0)
    ax = fig.add_axes([0.22, 0.18, 0.73, 0.74])
    style_clean_axes(ax, full_box=True, grid_axis="x", scale=scale)

    labels_bo = ["C–N (Mayer)", "C–C_PQ (Mayer)", "C–C' (Dimer)", "C–N (LBO)", "C–C_PQ (LBO)"]
    pq1_bo = [1.0128, 1.0256, 1.0177, 0.9180, 1.1680]
    pq2_bo = [0.9937, 0.9984, 1.0109, 0.8996, 1.1551]
    y_pos = np.arange(len(labels_bo))[::-1]
    h = 0.36

    bars1 = ax.barh(y_pos + h/2, pq1_bo, height=h, color=HEX_PQ1, edgecolor="black", lw=1.1 * scale)
    bars2 = ax.barh(y_pos - h/2, pq2_bo, height=h, color=HEX_PQ2_LIGHT, edgecolor="black", lw=1.1 * scale)
    ax.set_yticks(y_pos)
    ax.set_xlim(0.85, 1.34)
    xticks = [0.9, 1.0, 1.1, 1.2, 1.3]
    ax.set_xticks(xticks)

    mapper = CoordinateMapper(fig, ax, img_left, img_top, fig_w, fig_h)
    png_path = TMP_ASSET_DIR / "extra_bo_base.png"
    fig.savefig(png_path, dpi=300, transparent=True)
    plt.close(fig)

    slide.shapes.add_picture(str(png_path), Inches(img_left), Inches(img_top), width=Inches(fig_w), height=Inches(fig_h))

    add_standard_axes_labels(
        slide, mapper, "a",
        xticks=[(xv, f"{xv:.1f}") for xv in xticks],
        yticks=[(float(yv), lbl) for yv, lbl in zip(y_pos, labels_bo)],
        xlabel="Bond Order (a.u.)",
        scale=scale,
    )

    for b1, b2 in zip(bars1, bars2):
        v1, v2 = b1.get_width(), b2.get_width()
        x1_in, y1_in = mapper.data_to_ppt(v1 + 0.006, b1.get_y() + b1.get_height()/2)
        x2_in, y2_in = mapper.data_to_ppt(v2 + 0.006, b2.get_y() + b2.get_height()/2)
        add_ppt_text(slide, x1_in, y1_in, f"{v1:.3f}", font_pt=11.0 * scale, color=RGB_PQ1, bold=True, ha="left", va="center")
        add_ppt_text(slide, x2_in, y2_in, f"{v2:.3f}", font_pt=11.0 * scale, color=RGB_PQ2, bold=True, ha="left", va="center")

    leg_x, leg_y = mapper.axes_to_ppt(0.58, 0.45)
    add_ppt_legend(
        slide, leg_x, leg_y,
        [("TPA-PQ1 (para)", RGB_PQ1, "bar"), ("TPA-PQ2 (meta)", RGB_PQ2_LIGHT, "bar")],
        font_pt=11.5 * scale, w_in=2.10 * scale, row_h_in=0.27 * scale, scale=scale
    )


def build_extra_torsion(slide, img_left: float, img_top: float, fig_w: float, fig_h: float, scale: float = 1.0):
    fig = plt.figure(figsize=(fig_w, fig_h), dpi=300)
    fig.patch.set_alpha(0.0)
    ax = fig.add_axes([0.16, 0.18, 0.79, 0.74])
    style_clean_axes(ax, full_box=True, grid_axis="y", scale=scale)

    phi = np.linspace(0, 90, 100)
    def torsion_pot(ang, phi0, barrier90, barrier0):
        return np.where(
            ang >= phi0,
            barrier90 * np.sin(0.5 * np.pi * (ang - phi0) / (90.0 - phi0))**2,
            barrier0 * np.sin(0.5 * np.pi * (phi0 - ang) / phi0)**2
        )
    v_pq1 = torsion_pot(phi, 32.8, 2.83, 1.65)
    v_pq2 = torsion_pot(phi, 36.1, 2.46, 1.85)
    ax.plot(phi, v_pq1, color=HEX_PQ1, lw=3.0 * scale)
    ax.plot(phi, v_pq2, color=HEX_PQ2, lw=3.0 * scale, ls="--")
    ax.scatter([32.8, 90.0], [0.0, 2.83], color=HEX_PQ1, s=60 * scale, zorder=5)
    ax.scatter([36.1, 90.0], [0.0, 2.46], color=HEX_PQ2, s=60 * scale, zorder=5)
    ax.set_ylim(-0.25, 3.95)
    ax.set_xlim(0, 97)
    xticks = [0, 20, 40, 60, 80]
    yticks = [0, 1, 2, 3]
    ax.set_xticks(xticks)
    ax.set_yticks(yticks)

    mapper = CoordinateMapper(fig, ax, img_left, img_top, fig_w, fig_h)
    png_path = TMP_ASSET_DIR / "extra_torsion_base.png"
    fig.savefig(png_path, dpi=300, transparent=True)
    plt.close(fig)

    slide.shapes.add_picture(str(png_path), Inches(img_left), Inches(img_top), width=Inches(fig_w), height=Inches(fig_h))

    add_standard_axes_labels(
        slide, mapper, "b",
        xticks=[(float(xv), str(xv)) for xv in xticks],
        yticks=[(float(yv), str(yv)) for yv in yticks],
        xlabel="Dihedral Angle θ (deg)",
        ylabel="Relative Energy (kcal mol⁻¹)",
        scale=scale,
        ylabel_dx_in=0.72,
    )

    x1_in, y1_in = mapper.data_to_ppt(90.0, 2.94)
    x2_in, y2_in = mapper.data_to_ppt(90.0, 2.32)
    add_ppt_text(slide, x1_in, y1_in, "2.83", font_pt=11.5 * scale, color=RGB_PQ1, bold=True, ha="center", va="bottom")
    add_ppt_text(slide, x2_in, y2_in, "2.46", font_pt=11.5 * scale, color=RGB_PQ2, bold=True, ha="center", va="top")

    leg_x, leg_y = mapper.axes_to_ppt(0.03, 0.96)
    add_ppt_legend(
        slide, leg_x, leg_y,
        [("PQ1 (θ_eq=32.8°, ΔE=2.83)", RGB_PQ1, "line"), ("PQ2 (θ_eq=36.1°, ΔE=2.46)", RGB_PQ2, "line")],
        font_pt=11.0 * scale, w_in=2.95 * scale, row_h_in=0.28 * scale, scale=scale
    )


def build_extra_stacking(slide, img_left: float, img_top: float, fig_w: float, fig_h: float, scale: float = 1.0):
    fig = plt.figure(figsize=(fig_w, fig_h), dpi=300)
    fig.patch.set_alpha(0.0)
    ax = fig.add_axes([0.16, 0.18, 0.79, 0.74])
    style_clean_axes(ax, full_box=True, grid_axis="y", scale=scale)

    cats_p1 = ["D₀\n(r²SCAN)", "D₀\n(PBE0)", "2|J_h|\n(r²SCAN)", "2|J_h|\n(PBE0)"]
    pq1_p1 = [17.31, 26.08, 31.9, 14.2]
    pq2_p1 = [16.85, 25.80, 5.4, 3.6]
    x_p1 = np.arange(len(cats_p1))
    w = 0.35
    b_p1_1 = ax.bar(x_p1 - w/2, pq1_p1, width=w, color=HEX_PQ1, edgecolor="black", lw=1.1 * scale)
    b_p1_2 = ax.bar(x_p1 + w/2, pq2_p1, width=w, color=HEX_PQ2_LIGHT, edgecolor="black", lw=1.1 * scale)
    ax.set_xticks(x_p1)
    ax.set_ylim(0, 41.0)
    yticks = [0, 10, 20, 30, 40]
    ax.set_yticks(yticks)

    mapper = CoordinateMapper(fig, ax, img_left, img_top, fig_w, fig_h)
    png_path = TMP_ASSET_DIR / "extra_stacking_base.png"
    fig.savefig(png_path, dpi=300, transparent=True)
    plt.close(fig)

    slide.shapes.add_picture(str(png_path), Inches(img_left), Inches(img_top), width=Inches(fig_w), height=Inches(fig_h))

    add_standard_axes_labels(
        slide, mapper, "f",
        xticks=[(float(i), lbl) for i, lbl in enumerate(cats_p1)],
        yticks=[(float(yv), str(yv)) for yv in yticks],
        ylabel="D₀ (kcal mol⁻¹) or 2|J_h| (meV)",
        scale=scale,
        ylabel_dx_in=0.72,
    )

    badges_p1 = ["+0.45", "+0.28", "5.91×", "3.94×"]
    for i, (r1, r2, btxt) in enumerate(zip(b_p1_1, b_p1_2, badges_p1)):
        v1, v2 = r1.get_height(), r2.get_height()
        dy1 = 1.6 if i < 2 else 0.5
        dy2 = 0.3 if i < 2 else 0.5
        x1_in, y1_in = mapper.data_to_ppt(r1.get_x() + r1.get_width()/2 - 0.03, v1 + dy1)
        x2_in, y2_in = mapper.data_to_ppt(r2.get_x() + r2.get_width()/2 + 0.03, v2 + dy2)
        xb_in, yb_in = mapper.data_to_ppt(float(x_p1[i]), max(v1, v2) + 4.3)
        add_ppt_text(slide, x1_in, y1_in, f"{v1:.1f}", font_pt=11.0 * scale, color=RGB_PQ1, bold=True, ha="center", va="bottom")
        add_ppt_text(slide, x2_in, y2_in, f"{v2:.1f}", font_pt=11.0 * scale, color=RGB_PQ2, bold=True, ha="center", va="bottom")
        add_ppt_badge(
            slide, xb_in, yb_in, btxt,
            font_pt=11.2 * scale, text_color=RGB_ACCENT, fill_color=RGB_ACCENT_BG, border_color=RGB_ACCENT,
            ha="center", va="bottom", w_in=0.78 * scale, h_in=0.28 * scale, border_pt=1.2 * scale
        )

    leg_x, leg_y = mapper.axes_to_ppt(0.03, 0.96)
    add_ppt_legend(
        slide, leg_x, leg_y,
        [("TPA-PQ1 (para)", RGB_PQ1, "bar"), ("TPA-PQ2 (meta)", RGB_PQ2_LIGHT, "bar")],
        font_pt=11.5 * scale, w_in=2.10 * scale, row_h_in=0.27 * scale, scale=scale
    )


def build_extra_mesp(slide, img_left: float, img_top: float, fig_w: float, fig_h: float, scale: float = 1.0):
    box_l = img_left + 0.16 * fig_w
    box_t = img_top + (1.0 - 0.18 - 0.74) * fig_h
    box_w = 0.79 * fig_w
    box_h = 0.74 * fig_h

    frame = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(box_l), Inches(box_t), Inches(box_w), Inches(box_h)
    )
    frame.fill.solid()
    frame.fill.fore_color.rgb = RGB_WHITE
    frame.line.color.rgb = RGB_TEXT
    frame.line.width = Pt(1.8 * scale)

    add_ppt_text(
        slide, box_l - 0.65 * scale, box_t - 0.06 * scale, "(a)",
        font_pt=20.0 * scale, color=RGB_TEXT, bold=True, ha="left", va="bottom",
        w_in=0.65 * scale, h_in=0.40 * scale
    )

    m1_crop = TMP_ASSET_DIR / "pq1_dimer_mesp_crop.png"
    m2_crop = TMP_ASSET_DIR / "pq2_dimer_mesp_crop.png"
    w1, h1 = save_cropped_rgba(VMD_DIR / "pq1_dimer_mesp.png", m1_crop)
    w2, h2 = save_cropped_rgba(VMD_DIR / "pq2_dimer_mesp.png", m2_crop)

    for p_img, pw, ph, y_rel_top, y_rel_lbl, lbl_txt, col_rgb in [
        (m1_crop, w1, h1, 0.03, 0.42, "TPA-PQ1: V_min = -61.70 kcal mol⁻¹", RGB_PQ1),
        (m2_crop, w2, h2, 0.47, 0.85, "TPA-PQ2: V_min = -59.72 kcal mol⁻¹", RGB_PQ2),
    ]:
        avail_w = box_w * 0.88
        avail_h = box_h * 0.36
        sc = min(avail_w / pw, avail_h / ph)
        disp_w, disp_h = pw * sc, ph * sc
        mx = box_l + (box_w - disp_w) / 2.0
        my = box_t + y_rel_top * box_h + (avail_h - disp_h) / 2.0
        slide.shapes.add_picture(str(p_img), Inches(mx), Inches(my), width=Inches(disp_w), height=Inches(disp_h))
        add_ppt_text(
            slide, box_l + box_w / 2.0, box_t + y_rel_lbl * box_h, lbl_txt,
            font_pt=11.5 * scale, color=col_rgb, bold=True, ha="center", va="top",
            w_in=box_w * 0.96, h_in=0.30 * scale
        )

    fig_cb = plt.figure(figsize=(4.0, 0.32), dpi=300)
    ax_cb = fig_cb.add_axes([0.02, 0.15, 0.96, 0.70])
    norm = Normalize(vmin=-62.0, vmax=35.0)
    sm = ScalarMappable(norm=norm, cmap="bwr")
    sm.set_array([])
    cb = fig_cb.colorbar(sm, cax=ax_cb, orientation="horizontal")
    cb.set_ticks([])
    cb_path = TMP_ASSET_DIR / "mesp_colorbar_strip.png"
    fig_cb.savefig(cb_path, dpi=300, transparent=True)
    plt.close(fig_cb)

    cb_w = box_w * 0.72
    cb_h = 0.22 * scale
    cb_l = box_l + (box_w - cb_w) / 2.0
    cb_t = box_t + 0.89 * box_h
    slide.shapes.add_picture(str(cb_path), Inches(cb_l), Inches(cb_t), width=Inches(cb_w), height=Inches(cb_h))

    for frac_x, t_lbl in [(0.0, "-62"), (0.33, "-30"), (0.64, "0"), (1.0, "+35 kcal mol⁻¹")]:
        add_ppt_text(
            slide, cb_l + frac_x * cb_w, cb_t + cb_h + 0.01, t_lbl,
            font_pt=10.5 * scale, color=RGB_TEXT, bold=True, ha="center", va="top"
        )


def build_extra_pocket_esp(slide, img_left: float, img_top: float, fig_w: float, fig_h: float, scale: float = 1.0):
    fig = plt.figure(figsize=(fig_w, fig_h), dpi=300)
    fig.patch.set_alpha(0.0)
    ax = fig.add_axes([0.16, 0.18, 0.79, 0.74])
    style_clean_axes(ax, full_box=True, grid_axis="y", scale=scale)

    cats_esp = ["Mono\n|V_min|", "Dimer\n|V_min|", "|ΔE_Na|\n(PBE0)", "|ΔE_Na|\n(r²SCAN)"]
    pq1_esp = [50.03, 61.70, 26.61, 38.12]
    pq2_esp = [48.95, 59.72, 26.23, 37.59]
    x_esp = np.arange(len(cats_esp))
    w = 0.35
    b_e1 = ax.bar(x_esp - w/2, pq1_esp, width=w, color=HEX_PQ1, edgecolor="black", lw=1.1 * scale)
    b_e2 = ax.bar(x_esp + w/2, pq2_esp, width=w, color=HEX_PQ2_LIGHT, edgecolor="black", lw=1.1 * scale)
    ax.set_xticks(x_esp)
    ax.set_ylim(18, 76)
    yticks = [20, 30, 40, 50, 60, 70]
    ax.set_yticks(yticks)

    mapper = CoordinateMapper(fig, ax, img_left, img_top, fig_w, fig_h)
    png_path = TMP_ASSET_DIR / "extra_pocket_esp_base.png"
    fig.savefig(png_path, dpi=300, transparent=True)
    plt.close(fig)

    slide.shapes.add_picture(str(png_path), Inches(img_left), Inches(img_top), width=Inches(fig_w), height=Inches(fig_h))

    add_standard_axes_labels(
        slide, mapper, "b",
        xticks=[(float(i), lbl) for i, lbl in enumerate(cats_esp)],
        yticks=[(float(yv), str(yv)) for yv in yticks],
        ylabel="Energy Magnitude (kcal mol⁻¹)",
        scale=scale,
        ylabel_dx_in=0.72,
    )

    deltas_esp = ["-1.08", "-1.98", "-0.38", "-0.53"]
    for i, (r1, r2, dtxt) in enumerate(zip(b_e1, b_e2, deltas_esp)):
        v1, v2 = r1.get_height(), r2.get_height()
        x1_in, y1_in = mapper.data_to_ppt(r1.get_x() + r1.get_width()/2 - 0.03, v1 + 2.0)
        x2_in, y2_in = mapper.data_to_ppt(r2.get_x() + r2.get_width()/2 + 0.03, v2 + 0.4)
        xb_in, yb_in = mapper.data_to_ppt(float(x_esp[i]), max(v1, v2) + 5.5)
        add_ppt_text(slide, x1_in, y1_in, f"{v1:.1f}", font_pt=11.0 * scale, color=RGB_PQ1, bold=True, ha="center", va="bottom")
        add_ppt_text(slide, x2_in, y2_in, f"{v2:.1f}", font_pt=11.0 * scale, color=RGB_PQ2, bold=True, ha="center", va="bottom")
        add_ppt_badge(
            slide, xb_in, yb_in, dtxt,
            font_pt=11.2 * scale, text_color=RGB_ACCENT, fill_color=RGB_ACCENT_BG, border_color=RGB_ACCENT,
            ha="center", va="bottom", w_in=0.78 * scale, h_in=0.28 * scale, border_pt=1.2 * scale
        )

    leg_x, leg_y = mapper.axes_to_ppt(0.56, 0.96)
    add_ppt_legend(
        slide, leg_x, leg_y,
        [("TPA-PQ1 (para)", RGB_PQ1, "bar"), ("TPA-PQ2 (meta)", RGB_PQ2_LIGHT, "bar")],
        font_pt=11.5 * scale, w_in=2.10 * scale, row_h_in=0.27 * scale, scale=scale
    )


def build_extra_desolvation(slide, img_left: float, img_top: float, fig_w: float, fig_h: float, scale: float = 1.0):
    fig = plt.figure(figsize=(fig_w, fig_h), dpi=300)
    fig.patch.set_alpha(0.0)
    ax = fig.add_axes([0.16, 0.18, 0.79, 0.74])
    style_clean_axes(ax, full_box=True, grid_axis="y", scale=scale)

    x_step = [0, 1, 2]
    e_step_pq1 = [0.00, -7.042, +4.902]
    e_step_pq2 = [0.00, -6.730, +5.427]
    for i in range(3):
        ax.plot([x_step[i] - 0.24, x_step[i] + 0.24], [e_step_pq1[i], e_step_pq1[i]], color=HEX_PQ1, lw=3.8 * scale, zorder=4)
        ax.plot([x_step[i] - 0.24, x_step[i] + 0.24], [e_step_pq2[i], e_step_pq2[i]], color=HEX_PQ2, lw=3.8 * scale, zorder=3)
    for i in range(2):
        ax.plot([x_step[i] + 0.24, x_step[i+1] - 0.24], [e_step_pq1[i], e_step_pq1[i+1]], color=HEX_PQ1, ls="--", lw=1.8 * scale)
        ax.plot([x_step[i] + 0.24, x_step[i+1] - 0.24], [e_step_pq2[i], e_step_pq2[i+1]], color=HEX_PQ2, ls=":", lw=1.8 * scale)

    ax.set_xticks(x_step)
    ax.set_ylim(-10.5, 9.5)
    ax.set_xlim(-0.45, 2.45)
    yticks = [-10, -5, 0, 5]
    ax.set_yticks(yticks)

    mapper = CoordinateMapper(fig, ax, img_left, img_top, fig_w, fig_h)
    png_path = TMP_ASSET_DIR / "extra_desolvation_base.png"
    fig.savefig(png_path, dpi=300, transparent=True)
    plt.close(fig)

    slide.shapes.add_picture(str(png_path), Inches(img_left), Inches(img_top), width=Inches(fig_w), height=Inches(fig_h))

    add_standard_axes_labels(
        slide, mapper, "c",
        xticks=[
            (0.0, "Bulk\nSolvated"),
            (1.0, "Interface\n(-2 Solv.)"),
            (2.0, "Bulk Matrix\n(-3 Solv.)"),
        ],
        yticks=[(float(yv), str(yv)) for yv in yticks],
        ylabel="Reaction Energy ΔE (kcal mol⁻¹)",
        scale=scale,
        ylabel_dx_in=0.72,
    )

    for xv, yv, txt, col_rgb, va_mode in [
        (0.0, 0.7, "0.00", RGB_TEXT, "bottom"),
        (1.0, -7.74, "PQ1: -7.04", RGB_PQ1, "top"),
        (1.0, -6.13, "PQ2: -6.73", RGB_PQ2, "bottom"),
        (2.0, 4.20, "PQ1: +4.90\n(-9.7%)", RGB_PQ1, "top"),
        (2.0, 6.03, "PQ2: +5.43", RGB_PQ2, "bottom"),
    ]:
        px_in, py_in = mapper.data_to_ppt(xv, yv)
        add_ppt_text(slide, px_in, py_in, txt, font_pt=11.5 * scale, color=col_rgb, bold=True, ha="center", va=va_mode)


def build_extra_four_grid_3d(
    slide,
    img_left: float,
    img_top: float,
    fig_w: float,
    fig_h: float,
    panel_letter: str,
    items: list[tuple[str, str, RGBColor, list[float]]],
    bottom_label: str,
    scale: float = 1.0,
):
    box_l = img_left + 0.16 * fig_w
    box_t = img_top + (1.0 - 0.18 - 0.74) * fig_h
    box_w = 0.79 * fig_w
    box_h = 0.74 * fig_h

    frame = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(box_l), Inches(box_t), Inches(box_w), Inches(box_h)
    )
    frame.fill.solid()
    frame.fill.fore_color.rgb = RGB_WHITE
    frame.line.color.rgb = RGB_TEXT
    frame.line.width = Pt(1.8 * scale)

    add_ppt_text(
        slide, box_l - 0.65 * scale, box_t - 0.06 * scale, f"({panel_letter})",
        font_pt=20.0 * scale, color=RGB_TEXT, bold=True, ha="left", va="bottom",
        w_in=0.65 * scale, h_in=0.40 * scale
    )

    for fname, lbl, col_rgb, rect in items:
        crop_path = TMP_ASSET_DIR / f"crop_{fname}"
        pw, ph = save_cropped_rgba(VMD_DIR / fname, crop_path)
        rx, ry_mpl, rw, rh = rect
        ry_top = 1.0 - (ry_mpl + rh)
        avail_w = rw * box_w
        avail_h = rh * box_h
        sc = min(avail_w / pw, avail_h / ph)
        disp_w, disp_h = pw * sc, ph * sc
        mx = box_l + rx * box_w + (avail_w - disp_w) / 2.0
        my = box_t + ry_top * box_h + (avail_h - disp_h) / 2.0
        slide.shapes.add_picture(str(crop_path), Inches(mx), Inches(my), width=Inches(disp_w), height=Inches(disp_h))
        lbl_y = box_t + (1.0 - ry_mpl + 0.01) * box_h
        add_ppt_text(
            slide, box_l + (rx + rw / 2.0) * box_w, lbl_y, lbl,
            font_pt=11.0 * scale, color=col_rgb, bold=True, ha="center", va="top"
        )

    add_ppt_text(
        slide, box_l + box_w / 2.0, box_t + box_h + 0.14 * scale, bottom_label,
        font_pt=14.5 * scale, color=RGB_TEXT, bold=True, ha="center", va="top",
        w_in=box_w, h_in=0.38 * scale
    )


def build_extra_radar(slide, img_left: float, img_top: float, fig_w: float, fig_h: float, scale: float = 1.0):
    box_l = img_left + 0.16 * fig_w
    box_t = img_top + (1.0 - 0.18 - 0.74) * fig_h
    box_w = 0.79 * fig_w
    box_h = 0.74 * fig_h

    frame = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(box_l), Inches(box_t), Inches(box_w), Inches(box_h)
    )
    frame.fill.solid()
    frame.fill.fore_color.rgb = RGB_WHITE
    frame.line.color.rgb = RGB_TEXT
    frame.line.width = Pt(1.8 * scale)

    add_ppt_text(
        slide, box_l - 0.65 * scale, box_t - 0.06 * scale, "(d)",
        font_pt=20.0 * scale, color=RGB_TEXT, bold=True, ha="left", va="bottom",
        w_in=0.65 * scale, h_in=0.40 * scale
    )

    fig = plt.figure(figsize=(4.2, 4.2), dpi=300)
    fig.patch.set_alpha(0.0)
    ax_r = fig.add_axes([0.15, 0.15, 0.70, 0.70], polar=True)
    categories = [
        "1. Inter-Ring BO",
        "2. Oxidation Ease",
        "3. Bandwidth W_v",
        "4. Coupling 2|J_h|",
        "5. Pocket |V_min|",
        "6. Desolvation Ease",
        "7. Polaron Mobility",
        "8. Pocket Openness"
    ]
    N = len(categories)
    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    angles += angles[:1]
    vals_pq1 = [1.00] * N + [1.00]
    vals_pq2 = [0.72, 0.82, 373.0/511.0, 5.4/31.9, 59.72/61.70, 4.902/5.427, 5.756/6.874, 8.35/23.40]
    vals_pq2 += vals_pq2[:1]

    ax_r.set_theta_offset(np.pi / 2)
    ax_r.set_theta_direction(-1)
    ax_r.set_xticks(angles[:-1])
    ax_r.set_xticklabels([""] * N)
    ax_r.set_ylim(0, 1.12)
    ax_r.set_yticks([0.25, 0.50, 0.75, 1.00])
    ax_r.set_yticklabels([""] * 4)
    ax_r.plot(angles, vals_pq1, color=HEX_PQ1, linewidth=2.6, marker="o", ms=5.5)
    ax_r.fill(angles, vals_pq1, color=HEX_PQ1, alpha=0.22)
    ax_r.plot(angles, vals_pq2, color=HEX_PQ2, linewidth=2.4, ls="--", marker="s", ms=5.5)
    ax_r.fill(angles, vals_pq2, color=HEX_PQ2, alpha=0.20)

    radar_path = TMP_ASSET_DIR / "extra_radar_base.png"
    fig.savefig(radar_path, dpi=300, transparent=True)
    plt.close(fig)

    rw = min(box_w, box_h) * 0.74
    rx = box_l + (box_w - rw) / 2.0
    ry = box_t + (box_h - rw) / 2.0
    slide.shapes.add_picture(str(radar_path), Inches(rx), Inches(ry), width=Inches(rw), height=Inches(rw))

    cx = rx + rw / 2.0
    cy = ry + rw / 2.0
    rad = rw * 0.35 * 1.25
    ha_list = ["center", "left", "left", "left", "center", "right", "right", "right"]
    va_list = ["bottom", "bottom", "center", "top", "top", "top", "center", "bottom"]
    for ang, lbl, ha_i, va_i in zip(angles[:-1], categories, ha_list, va_list):
        lx = cx + rad * np.sin(ang)
        ly = cy - rad * np.cos(ang)
        add_ppt_text(slide, lx, ly, lbl, font_pt=11.0 * scale, color=RGB_TEXT, bold=True, ha=ha_i, va=va_i)

    add_ppt_legend(
        slide, box_l + box_w - 2.15 * scale, box_t + 0.12 * scale,
        [("TPA-PQ1 (para)", RGB_PQ1, "line"), ("TPA-PQ2 (meta)", RGB_PQ2, "line")],
        font_pt=11.0 * scale, w_in=2.00 * scale, row_h_in=0.26 * scale, scale=scale
    )
    add_ppt_text(
        slide, box_l + box_w / 2.0, box_t + box_h + 0.14 * scale,
        "Normalized Multi-Scale Performance Radar",
        font_pt=14.5 * scale, color=RGB_TEXT, bold=True, ha="center", va="top",
        w_in=box_w, h_in=0.38 * scale
    )


def main():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.500)
    blank_layout = prs.slide_layouts[6]

    img_left, img_top, fig_w, fig_h = 2.30, 0.86, 8.60, 6.05

    # Slide 1: Figure 5(a)
    s1 = prs.slides.add_slide(blank_layout)
    add_slide_header(
        s1,
        "Figure 5(a) — Anodic Oxidation Thresholds (Monomer VIP/AIP & Dimer AIP)",
        "论文图 5(a) 独立可编辑小图：所有文字标签、数值、差值圆角框、坐标轴与图例均为 PPT 原生文本框，可直接点击拖动与修改"
    )
    build_panel_5a(s1, img_left, img_top, fig_w, fig_h, scale=1.0, tag="single")

    # Slide 2: Figure 5(b)
    s2 = prs.slides.add_slide(blank_layout)
    add_slide_header(
        s2,
        "Figure 5(b) — Radical Cation Spin Density Isosurfaces (0.004 a.u.) & Hole Reorganization",
        "论文图 5(b) 独立可编辑小图：两个 3D 分子等值面图、外框及所有文字说明均为独立可拖动 PPT 对象"
    )
    build_panel_5b(s2, img_left, img_top, fig_w, fig_h, scale=1.0)

    # Slide 3: Figure 5(c)
    s3 = prs.slides.add_slide(blank_layout)
    add_slide_header(
        s3,
        "Figure 5(c) — Oligomer Frontier Orbital Evolution (n = 1 → 2 → 3) & Valence Bandwidth W_v",
        "论文图 5(c) 独立可编辑小图：所有轨道能级数值、价带宽度圆角框、坐标轴刻度与标题均为可拖动 PPT 原生文本框"
    )
    build_panel_5c(s3, img_left, img_top, fig_w, fig_h, scale=1.0, tag="single")

    # Slide 4: Figure 5(d)
    s4 = prs.slides.add_slide(blank_layout)
    add_slide_header(
        s4,
        "Figure 5(d) — Bipolar Four-State Internal Reorganization Energies λ_reorg",
        "论文图 5(d) 独立可编辑小图：所有柱顶数值、百分比降幅圆角框、四态标签、坐标轴与图例均为可拖动 PPT 原生文本框"
    )
    build_panel_5d(s4, img_left, img_top, fig_w, fig_h, scale=1.0, tag="single")

    # Slide 5: Figure 5(e)
    s5 = prs.slides.add_slide(blank_layout)
    add_slide_header(
        s5,
        "Figure 5(e) — Trimer (n = 3) 32-Rotamer Pocket Distance Distribution & 4O–Na⁺ Trap",
        "论文图 5(e) 独立可编辑小图：开放单口袋标注、四氧夹心钠陷阱圆角框 (-22.8 kcal mol⁻¹)、图例与坐标轴均为可拖动 PPT 文本框"
    )
    build_panel_5e(s5, img_left, img_top, fig_w, fig_h, scale=1.0, tag="single")

    # Slide 6: Figure 5(f)
    s6 = prs.slides.add_slide(blank_layout)
    add_slide_header(
        s6,
        "Figure 5(f) — Relaxed 3D Trimer (n = 3) Conformations (Open Rod vs. Folded 4O–Na⁺ Trap)",
        "论文图 5(f) 独立可编辑小图：上下两个 3D 三聚体分子构象图、外框及所有文字标签均为独立可拖动 PPT 对象"
    )
    build_panel_5f(s6, img_left, img_top, fig_w, fig_h, scale=1.0)

    # Slide 7: Complete 6-Panel Composite Overview of Figure 5 (All 6 sub-panels on 1 slide, all text editable!)
    s7 = prs.slides.add_slide(blank_layout)
    cw, ch = 4.15, 3.45
    cols_l = [0.28, 4.62, 8.96]
    rows_t = [0.18, 3.82]
    sc_comp = 0.56
    build_panel_5a(s7, cols_l[0], rows_t[0], cw, ch, scale=sc_comp, tag="comp")
    build_panel_5b(s7, cols_l[1], rows_t[0], cw, ch, scale=sc_comp)
    build_panel_5c(s7, cols_l[2], rows_t[0], cw, ch, scale=sc_comp, tag="comp")
    build_panel_5d(s7, cols_l[0], rows_t[1], cw, ch, scale=sc_comp, tag="comp")
    build_panel_5e(s7, cols_l[1], rows_t[1], cw, ch, scale=sc_comp, tag="comp")
    build_panel_5f(s7, cols_l[2], rows_t[1], cw, ch, scale=sc_comp)

    # Slides 8-17: Additional DFT Sub-Panels
    s8 = prs.slides.add_slide(blank_layout)
    add_slide_header(s8, "Supplementary DFT Panel — Inter-Ring Conjugation Bond Orders (Mayer & LBO)", "附加可编辑计算小图：环间共轭键级对比（所有文字与数值均可拖动）")
    build_extra_bond_orders(s8, img_left, img_top, fig_w, fig_h, scale=1.0)

    s9 = prs.slides.add_slide(blank_layout)
    add_slide_header(s9, "Supplementary DFT Panel — PQ–Phenylene Dihedral Torsional Potential Scan", "附加可编辑计算小图：二面角扭转势能面扫描（所有文字与图例均可拖动）")
    build_extra_torsion(s9, img_left, img_top, fig_w, fig_h, scale=1.0)

    s10 = prs.slides.add_slide(blank_layout)
    add_slide_header(s10, "Supplementary DFT Panel — Dimer Antiparallel π–π Stacking D₀ & Electronic Coupling 2|J_h|", "附加可编辑计算小图：二聚体 π–π 堆积能与空穴耦合积分（所有文字与圆角框均可拖动）")
    build_extra_stacking(s10, img_left, img_top, fig_w, fig_h, scale=1.0)

    s11 = prs.slides.add_slide(blank_layout)
    add_slide_header(s11, "Supplementary DFT Panel — Quantitative Dimer MESP Surfaces & Colorbar", "附加可编辑计算小图：二聚体分子静电势表面与色标刻度（分子图与所有文字均可拖动）")
    build_extra_mesp(s11, img_left, img_top, fig_w, fig_h, scale=1.0)

    s12 = prs.slides.add_slide(blank_layout)
    add_slide_header(s12, "Supplementary DFT Panel — Active-Pocket Nucleophilicity |V_min| & Na⁺ Binding |ΔE_Na|", "附加可编辑计算小图：活性口袋亲核性与钠结合能对比（所有文字与圆角框均可拖动）")
    build_extra_pocket_esp(s12, img_left, img_top, fig_w, fig_h, scale=1.0)

    s13 = prs.slides.add_slide(blank_layout)
    add_slide_header(s13, "Supplementary DFT Panel — Explicit Interfacial Partial & Full Desolvation Pathway", "附加可编辑计算小图：显式界面分步脱溶剂化能级台阶图（所有文字与能量标签均可拖动）")
    build_extra_desolvation(s13, img_left, img_top, fig_w, fig_h, scale=1.0)

    s14 = prs.slides.add_slide(blank_layout)
    add_slide_header(s14, "Supplementary DFT Panel — Monomer (n = 1) Frontier Orbitals (HOMO & LUMO)", "附加可编辑计算小图：单体前线轨道等值面（4 个 3D 分子图与所有标签均可独立拖动）")
    build_extra_four_grid_3d(
        s14, img_left, img_top, fig_w, fig_h, "a",
        [
            ("pq1_mono_homo.png", "PQ1 HOMO (-5.67 eV)", RGB_PQ1, [0.02, 0.54, 0.46, 0.42]),
            ("pq1_mono_lumo.png", "PQ1 LUMO (-2.96 eV)", RGB_PQ1, [0.52, 0.54, 0.46, 0.42]),
            ("pq2_mono_homo.png", "PQ2 HOMO (-5.66 eV)", RGB_PQ2, [0.02, 0.06, 0.46, 0.42]),
            ("pq2_mono_lumo.png", "PQ2 LUMO (-3.01 eV)", RGB_PQ2, [0.52, 0.06, 0.46, 0.42]),
        ],
        "Monomer (n = 1) Frontier Orbitals (|Ψ| = 0.02 a.u.)"
    )

    s15 = prs.slides.add_slide(blank_layout)
    add_slide_header(s15, "Supplementary DFT Panel — Dimer (n = 2) Frontier Orbitals (HOMO & LUMO)", "附加可编辑计算小图：二聚体前线轨道等值面（4 个 3D 分子图与所有标签均可独立拖动）")
    build_extra_four_grid_3d(
        s15, img_left, img_top, fig_w, fig_h, "b",
        [
            ("pq1_dimer_homo.png", "PQ1 Dimer HOMO (-5.51 eV)", RGB_PQ1, [0.02, 0.54, 0.46, 0.42]),
            ("pq1_dimer_lumo.png", "PQ1 Dimer LUMO (-3.01 eV)", RGB_PQ1, [0.52, 0.54, 0.46, 0.42]),
            ("pq2_dimer_homo.png", "PQ2 Dimer HOMO (-5.56 eV)", RGB_PQ2, [0.02, 0.06, 0.46, 0.42]),
            ("pq2_dimer_lumo.png", "PQ2 Dimer LUMO (-3.05 eV)", RGB_PQ2, [0.52, 0.06, 0.46, 0.42]),
        ],
        "Dimer (n = 2) Frontier Orbitals (|Ψ| = 0.02 a.u.)"
    )

    s16 = prs.slides.add_slide(blank_layout)
    add_slide_header(s16, "Supplementary DFT Panel — Interfacial Partially Desolvated Complexes [PQ•⁻·Na⁺·(EC)₁]", "附加可编辑计算小图：界面部分脱溶剂化配合物 3D 结构（分子图与所有标签均可独立拖动）")
    build_extra_four_grid_3d(
        s16, img_left, img_top, fig_w, fig_h, "c",
        [
            ("pq1_na_ec1.png", "[PQ1•⁻·Na⁺·(EC)₁] (ΔE_exch = -7.04 kcal mol⁻¹)", RGB_PQ1, [0.04, 0.53, 0.92, 0.43]),
            ("pq2_na_ec1.png", "[PQ2•⁻·Na⁺·(EC)₁] (ΔE_exch = -6.73 kcal mol⁻¹)", RGB_PQ2, [0.04, 0.07, 0.92, 0.43]),
        ],
        "Interfacial Partially Desolvated Complexes"
    )

    s17 = prs.slides.add_slide(blank_layout)
    add_slide_header(s17, "Supplementary DFT Panel — 8-Axis Multi-Scale Kinetic & Thermodynamic Radar Chart", "附加可编辑计算小图：8 维多尺度动力学与热力学雷达图（所有维度文字与图例均可拖动）")
    build_extra_radar(s17, img_left, img_top, fig_w, fig_h, scale=1.0)

    out_pptx_ms = MS_DIR / "TPA_PQ_Figure5_DFT_Editable_Subpanels_v9.pptx"
    out_pptx_int = INT_DIR / "TPA_PQ_Figure5_DFT_Editable_Subpanels_v9.pptx"
    prs.save(str(out_pptx_ms))
    shutil.copy2(out_pptx_ms, out_pptx_int)
    print(f"Saved editable DFT PPTX ({len(prs.slides)} slides): {out_pptx_ms}")


if __name__ == "__main__":
    main()
