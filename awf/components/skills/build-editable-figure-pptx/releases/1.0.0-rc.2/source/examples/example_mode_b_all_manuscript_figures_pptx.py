#!/usr/bin/env python3
"""
Build the Comprehensive Editable PowerPoint (.pptx) for ALL 12 Figures in Manuscript v9
(Main Figures 1-6 + Supporting Figures S1-S6):
`TPA_PQ_All_Manuscript_Figures_Editable_Subpanels_v9.pptx`

Every slide holds ONE COMPLETE SUB-PANEL at large widescreen resolution (13.333 x 7.500 in),
with native, freely draggable PowerPoint textboxes/shapes for panel labels (a)-(k), axis titles,
normalized tick numbers, in-box sample badges, legends, and molecular/schematic annotations.
"""

from __future__ import annotations

import shutil
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

from build_editable_dft_pptx_v9 import (
    RGB_PQ1,
    RGB_PQ2,
    RGB_TEXT,
    RGB_MUTED,
    RGB_WHITE,
    add_ppt_text,
    add_ppt_badge,
    add_ppt_legend,
    add_slide_header,
    build_panel_5a,
    build_panel_5b,
    build_panel_5c,
    build_panel_5d,
    build_panel_5e,
    build_panel_5f,
)

ROOT = Path("/home/zc/mmdata/zln/20260701/paper_upgrade_p0_p3_20261021")
SLIDES_DIR = ROOT / "pptx_extracted_20261021" / "slides_png"
MS_SLIDES_DIR = ROOT / "pptx_extracted_20261021" / "ms_slides_png"
MS_DIR = ROOT / "manuscript_20261021"
INT_DIR = ROOT / "figures_integrated_manuscript_20261021"
ASSET_DIR = ROOT / "pptx_editable_assets_v9" / "exp_crops"
ASSET_DIR.mkdir(parents=True, exist_ok=True)

RGB_BLUE_AXIS = RGBColor(0x5D, 0xAD, 0xE2)
RGB_YELLOW_CHG = RGBColor(0xF4, 0xE0, 0xAA)


def load_slide(idx: int) -> Image.Image:
    """
    Composite palette/RGBA slide onto a clean RGB white canvas so no PNG `transparency=(0,0,0)`
    chunk is ever inherited when saving cropped sub-panels!
    """
    im = Image.open(SLIDES_DIR / f"slide_{idx:02d}.png").convert("RGBA")
    bg = Image.new("RGB", im.size, (255, 255, 255))
    bg.paste(im, mask=im.split()[3])
    return bg


def load_ms_slide(idx: int) -> Image.Image:
    im = Image.open(MS_SLIDES_DIR / f"ms_slide_{idx:02d}.png").convert("RGBA")
    bg = Image.new("RGB", im.size, (255, 255, 255))
    bg.paste(im, mask=im.split()[3])
    return bg


def place_relabelled_2d_plot_on_slide(
    slide,
    src_im: Image.Image,
    src_frame: tuple[int, int, int, int],
    crop_name: str,
    panel_letter: str,
    xticks: list[tuple[float, str]],
    xlabel: str,
    yticks: list[tuple[float, str]],
    ylabel: str,
    rticks: list[tuple[float, str]] | None = None,
    rlabel: str | None = None,
    rcolor: RGBColor = RGB_BLUE_AXIS,
    badge_text: str | None = None,
    badge_color: RGBColor = RGB_PQ1,
    badge_rel_xy: tuple[float, float] = (0.04, 0.08),
    box_l: float = 3.20,
    box_t: float = 1.15,
    box_w: float = 6.80,
    box_h: float = 4.95,
):
    """
    Crop only the 4-spine plot frame (plus 7 px for tick marks, stripping all baked outer tick numbers
    and axis titles) and place 100% native draggable PPT tick labels, axis titles, panel label, and badge!
    """
    bx0, by0, bx1, by1 = src_frame
    pad = 7
    W_s, H_s = src_im.size
    cx0, cy0 = max(0, bx0 - pad), max(0, by0 - pad)
    cx1, cy1 = min(W_s, bx1 + pad), min(H_s, by1 + pad)

    crop = src_im.crop((cx0, cy0, cx1, cy1))
    crop_path = ASSET_DIR / f"{crop_name}.png"
    crop.save(crop_path)

    bw = float(bx1 - bx0)
    bh = float(by1 - by0)
    sx = box_w / bw
    sy = box_h / bh

    img_w = crop.width * sx
    img_h = crop.height * sy
    img_l = box_l - (bx0 - cx0) * sx
    img_t = box_t - (by0 - cy0) * sy

    slide.shapes.add_picture(str(crop_path), Inches(img_l), Inches(img_t), width=Inches(img_w), height=Inches(img_h))

    # Panel letter
    add_ppt_text(
        slide, box_l - 0.90, box_t - 0.05, f"({panel_letter})",
        font_pt=20.0, color=RGB_TEXT, bold=True, ha="left", va="top", w_in=0.70, h_in=0.40
    )

    # X ticks
    for frac_x, lbl in xticks:
        tx = box_l + frac_x * box_w
        add_ppt_text(slide, tx, box_t + box_h + 0.10, lbl, font_pt=12.5, color=RGB_TEXT, bold=True, ha="center", va="top")

    # X label
    add_ppt_text(
        slide, box_l + box_w / 2.0, box_t + box_h + 0.48, xlabel,
        font_pt=14.5, color=RGB_TEXT, bold=True, ha="center", va="top", w_in=5.5, h_in=0.38
    )

    # Left Y ticks
    for frac_y, lbl in yticks:
        ty = box_t + (1.0 - frac_y) * box_h
        add_ppt_text(slide, box_l - 0.12, ty, lbl, font_pt=12.5, color=RGB_TEXT, bold=True, ha="right", va="center")

    # Left Y label
    add_ppt_text(
        slide, box_l - 0.78, box_t + box_h / 2.0, ylabel,
        font_pt=14.5, color=RGB_TEXT, bold=True, ha="center", va="center", w_in=4.5, h_in=0.42, rotation=-90.0
    )

    # Right Y ticks & label if dual-axis
    if rticks is not None:
        for frac_y, lbl in rticks:
            ty = box_t + (1.0 - frac_y) * box_h
            add_ppt_text(slide, box_l + box_w + 0.12, ty, lbl, font_pt=12.5, color=rcolor, bold=True, ha="left", va="center")
        if rlabel:
            add_ppt_text(
                slide, box_l + box_w + 0.78, box_t + box_h / 2.0, rlabel,
                font_pt=14.5, color=rcolor, bold=True, ha="center", va="center", w_in=4.5, h_in=0.42, rotation=-90.0
            )

    if badge_text:
        bx = box_l + badge_rel_xy[0] * box_w
        by = box_t + badge_rel_xy[1] * box_h
        add_ppt_badge(
            slide, bx, by, badge_text,
            font_pt=12.0, text_color=badge_color, fill_color=RGB_WHITE, border_color=badge_color,
            ha="left", va="top"
        )


def place_plot_with_draggable_titles(
    slide,
    src_im: Image.Image,
    src_frame: tuple[int, int, int, int],
    crop_name: str,
    panel_letter: str,
    xlabel: str,
    ylabel: str,
    rlabel: str | None = None,
    rcolor: RGBColor = RGB_TEXT,
    pad_ticks: tuple[int, int, int, int] = (60, 18, 25, 45),
    badge_text: str | None = None,
    badge_color: RGBColor = RGB_PQ1,
    badge_rel_xy: tuple[float, float] = (0.68, 0.06),
    box_l: float = 3.20,
    box_t: float = 1.15,
    box_w: float = 6.50,
    box_h: float = 4.95,
):
    """
    Keep the plot box + tick numbers (pad_ticks) while stripping the outer raster axis titles,
    and replace the X/Y/Right axis titles, panel label (a)-(h), and sample badges with native
    draggable PowerPoint textboxes!
    """
    bx0, by0, bx1, by1 = src_frame
    pl, pt, pr, pb = pad_ticks
    W_s, H_s = src_im.size
    cx0, cy0 = max(0, bx0 - pl), max(0, by0 - pt)
    cx1, cy1 = min(W_s, bx1 + pr), min(H_s, by1 + pb)

    crop = src_im.crop((cx0, cy0, cx1, cy1))
    crop_path = ASSET_DIR / f"{crop_name}.png"
    crop.save(crop_path)

    bw = float(bx1 - bx0)
    bh = float(by1 - by0)
    sx = box_w / bw
    sy = box_h / bh

    img_w = crop.width * sx
    img_h = crop.height * sy
    img_l = box_l - (bx0 - cx0) * sx
    img_t = box_t - (by0 - cy0) * sy

    slide.shapes.add_picture(str(crop_path), Inches(img_l), Inches(img_t), width=Inches(img_w), height=Inches(img_h))

    add_ppt_text(
        slide, box_l - max(0.90, (pl * sx) + 0.45), box_t - 0.05, f"({panel_letter})",
        font_pt=20.0, color=RGB_TEXT, bold=True, ha="left", va="top", w_in=0.70, h_in=0.40
    )

    if xlabel:
        add_ppt_text(
            slide, box_l + box_w / 2.0, box_t + box_h + (pb * sy) + 0.05, xlabel,
            font_pt=14.5, color=RGB_TEXT, bold=True, ha="center", va="top", w_in=5.8, h_in=0.38
        )
    if ylabel:
        add_ppt_text(
            slide, box_l - (pl * sx) - 0.24, box_t + box_h / 2.0, ylabel,
            font_pt=14.5, color=RGB_TEXT, bold=True, ha="center", va="center", w_in=4.6, h_in=0.42, rotation=-90.0
        )
    if rlabel:
        add_ppt_text(
            slide, box_l + box_w + (pr * sx) + 0.24, box_t + box_h / 2.0, rlabel,
            font_pt=14.5, color=rcolor, bold=True, ha="center", va="center", w_in=4.6, h_in=0.42, rotation=-90.0
        )
    if badge_text:
        bx = box_l + badge_rel_xy[0] * box_w
        by = box_t + badge_rel_xy[1] * box_h
        add_ppt_badge(
            slide, bx, by, badge_text,
            font_pt=12.0, text_color=badge_color, fill_color=RGB_WHITE, border_color=badge_color,
            ha="left", va="top"
        )


def add_General_box_slide(
    slide,
    src_im: Image.Image,
    src_box: tuple[int, int, int, int],
    crop_name: str,
    panel_letter: str,
    bottom_caption: str | None = None,
    badge_text: str | None = None,
    badge_color: RGBColor = RGB_PQ1,
    max_w: float = 8.4,
    max_h: float = 5.4,
):
    crop = src_im.crop(src_box)
    crop_path = ASSET_DIR / f"{crop_name}.png"
    crop.save(crop_path)
    pw, ph = crop.size
    sc = min(max_w / pw, max_h / ph)
    dw, dh = pw * sc, ph * sc
    dl = (13.333 - dw) / 2.0
    dt = 1.05 + (max_h - dh) / 2.0
    slide.shapes.add_picture(str(crop_path), Inches(dl), Inches(dt), width=Inches(dw), height=Inches(dh))
    add_ppt_text(
        slide, dl - 0.75, dt - 0.05, f"({panel_letter})",
        font_pt=20.0, color=RGB_TEXT, bold=True, ha="left", va="bottom", w_in=0.70, h_in=0.40
    )
    if badge_text:
        add_ppt_badge(
            slide, dl + 0.15, dt + 0.12, badge_text,
            font_pt=12.5, text_color=badge_color, fill_color=RGB_WHITE, border_color=badge_color,
            ha="left", va="top"
        )
    if bottom_caption:
        add_ppt_text(
            slide, 13.333 / 2.0, dt + dh + 0.15, bottom_caption,
            font_pt=14.5, color=RGB_TEXT, bold=True, ha="center", va="top", w_in=8.0, h_in=0.40
        )


def build_all_figures_pptx():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.500)
    blank = prs.slide_layouts[6]

    # ==========================================================================
    # FIGURE 1 (Panels a - h)
    # ==========================================================================
    s17 = load_slide(17)
    d17 = ImageDraw.Draw(s17)
    d17.rectangle((0, 0, 2400, 175), fill=(255, 255, 255))
    # Erase baked CV X-axis titles & reaction scheme labels on Slide 17 without touching carbonyl oxygens!
    d17.rectangle((440, 750, 820, 810), fill=(255, 255, 255))   # baked 'Potential (V vs. Ag/Ag+)' left
    d17.rectangle((1700, 750, 2050, 805), fill=(255, 255, 255)) # baked 'Potential (V vs. Ag/Ag+)' right
    d17.rectangle((335, 840, 760, 915), fill=(255, 255, 255))   # 'electropolymerization' left
    d17.rectangle((70, 1020, 260, 1095), fill=(255, 255, 255))   # 'TPA-PQ1' left
    d17.rectangle((880, 1260, 1090, 1340), fill=(255, 255, 255)) # 'pTPA-PQ1' left
    d17.rectangle((1640, 810, 2038, 875), fill=(255, 255, 255))  # 'electropolymerization' right
    d17.rectangle((1415, 1035, 1630, 1105), fill=(255, 255, 255))# 'TPA-PQ2' right
    d17.rectangle((2030, 1285, 2230, 1348), fill=(255, 255, 255))# 'pTPA-PQ2' right
    d17.rectangle((2165, 1262, 2212, 1295), fill=(255, 255, 255))# slide number '17' right

    # Fig 1(a) — pl=85 keeps full -0.05..0.20 tick numbers while excluding baked 'Current (mA)'
    sl = prs.slides.add_slide(blank)
    add_slide_header(sl, "Figure 1(a) — In-Situ Electropolymerization CV & Scheme of TPA-PQ1 → pTPA-PQ1", "论文图 1(a) 独立可编辑小图：电聚合 CV 图、反应式及 TPA-PQ1 / electropolymerization / pTPA-PQ1 可拖动文本框")
    sch1 = s17.crop((75, 760, 1085, 1335))
    sch1_p = ASSET_DIR / "fig1a_scheme.png"
    sch1.save(sch1_p)
    sl.shapes.add_picture(str(sch1_p), Inches(3.10), Inches(4.85), width=Inches(6.20), height=Inches(2.45))
    place_plot_with_draggable_titles(
        sl, s17, (338, 244, 903, 697), "fig1a_cv", "a",
        xlabel="Potential (V vs. Ag/Ag⁺)", ylabel="Current (mA)",
        pad_ticks=(85, 20, 25, 48), box_l=3.65, box_t=0.90, box_w=5.10, box_h=3.15
    )
    add_ppt_text(sl, 3.65, 6.22, "TPA-PQ1", font_pt=13.5, color=RGB_PQ1, bold=True)
    add_ppt_text(sl, 5.95, 5.20, "electropolymerization", font_pt=12.5, color=RGB_TEXT, bold=True)
    add_ppt_text(sl, 8.65, 6.98, "pTPA-PQ1", font_pt=13.5, color=RGB_PQ1, bold=True)

    # Fig 1(b)
    sl = prs.slides.add_slide(blank)
    add_slide_header(sl, "Figure 1(b) — In-Situ Electropolymerization CV & Scheme of TPA-PQ2 → pTPA-PQ2", "论文图 1(b) 独立可编辑小图：电聚合 CV 图、反应式及 TPA-PQ2 / electropolymerization / pTPA-PQ2 可拖动文本框")
    sch2 = s17.crop((1365, 755, 2345, 1335))
    sch2_p = ASSET_DIR / "fig1b_scheme.png"
    sch2.save(sch2_p)
    sl.shapes.add_picture(str(sch2_p), Inches(3.10), Inches(4.85), width=Inches(6.20), height=Inches(2.45))
    place_plot_with_draggable_titles(
        sl, s17, (1600, 244, 2165, 697), "fig1b_cv", "b",
        xlabel="Potential (V vs. Ag/Ag⁺)", ylabel="Current (mA)",
        pad_ticks=(85, 20, 25, 48), box_l=3.65, box_t=0.90, box_w=5.10, box_h=3.15
    )
    add_ppt_text(sl, 4.05, 6.22, "TPA-PQ2", font_pt=13.5, color=RGB_PQ2, bold=True)
    add_ppt_text(sl, 6.00, 5.12, "electropolymerization", font_pt=12.5, color=RGB_TEXT, bold=True)
    add_ppt_text(sl, 7.65, 7.02, "pTPA-PQ2", font_pt=13.5, color=RGB_PQ2, bold=True)

    # Fig 1(c, d, e, f) from Slide 3 — erase rotated 'Intensity (a.u.)' strip so pl=32 keeps leftmost X tick unclipped!
    s3 = load_slide(3)
    d3 = ImageDraw.Draw(s3)
    for bx0, by0, bx1, by1 in [(805, 86, 1370, 542), (1587, 95, 2152, 551), (758, 735, 1402, 1211), (1578, 735, 2222, 1210)]:
        d3.rectangle((bx0 - 65, by0, bx0 - 8, by1), fill=(255, 255, 255))
    for ltr, s_box, cname, title_en, title_cn, xl, yl, pb_val in [
        ("c", (805, 86, 1370, 542), "fig1c_uv1", "Figure 1(c) — UV-vis Absorption Spectra of TPA-PQ1 & pTPA-PQ1 in NMP", "论文图 1(c) 独立可编辑小图：紫外-可见吸收光谱与可拖动坐标轴标题", "Wavelength (nm)", "Absorbance (a.u.)", 40),
        ("d", (1587, 95, 2152, 551), "fig1d_uv2", "Figure 1(d) — UV-vis Absorption Spectra of TPA-PQ2 & pTPA-PQ2 in NMP", "论文图 1(d) 独立可编辑小图：紫外-可见吸收光谱与可拖动坐标轴标题", "Wavelength (nm)", "Absorbance (a.u.)", 40),
        ("e", (758, 735, 1402, 1211), "fig1e_ftir1", "Figure 1(e) — FTIR Full Spectra of Monomers & Polymers", "论文图 1(e) 独立可编辑小图：傅里叶变换红外全谱与可拖动坐标轴标题", "Wavenumber (cm⁻¹)", "Transmittance (a.u.)", 48),
        ("f", (1578, 735, 2222, 1210), "fig1f_ftir2", "Figure 1(f) — Magnified C=O Stretching Region of FTIR Spectra", "论文图 1(f) 独立可编辑小图：红外光谱局部放大图与可拖动坐标轴标题", "Wavenumber (cm⁻¹)", "Transmittance (a.u.)", 48),
    ]:
        sl = prs.slides.add_slide(blank)
        add_slide_header(sl, title_en, title_cn)
        place_plot_with_draggable_titles(sl, s3, s_box, cname, ltr, xlabel=xl, ylabel=yl, pad_ticks=(32, 15, 25, pb_val))

    # Fig 1(g, h) SEM panels from Slides 4 & 5
    s4, s5 = load_slide(4), load_slide(5)
    for ltr, s_im, b1, b2, l1, l2, col_rgb, t_en, t_cn in [
        ("g", s4, (501, 240, 1124, 664), (1297, 240, 1921, 664), "TPA-PQ1", "pTPA-PQ1", RGB_PQ1, "Figure 1(g) — SEM Micrographs of Monomer TPA-PQ1 and Polymer pTPA-PQ1", "论文图 1(g) 独立可编辑小图：两张 SEM 电镜图与底部样品标签均为独立可拖动对象"),
        ("h", s5, (518, 278, 1142, 699), (1407, 278, 2020, 696), "TPA-PQ2", "pTPA-PQ2", RGB_PQ2, "Figure 1(h) — SEM Micrographs of Monomer TPA-PQ2 and Polymer pTPA-PQ2", "论文图 1(h) 独立可编辑小图：两张 SEM 电镜图与底部样品标签均为独立可拖动对象"),
    ]:
        sl = prs.slides.add_slide(blank)
        add_slide_header(sl, t_en, t_cn)
        add_ppt_text(sl, 1.15, 1.45, f"({ltr})", font_pt=20.0, color=RGB_TEXT, bold=True, ha="left", va="bottom")
        for idx_s, (sbox, slbl, lx) in enumerate([(b1, l1, 1.65), (b2, l2, 7.05)]):
            cp = ASSET_DIR / f"fig1{ltr}_{idx_s}.png"
            s_im.crop(sbox).save(cp)
            sl.shapes.add_picture(str(cp), Inches(lx), Inches(1.55), width=Inches(4.65), height=Inches(3.25))
            add_ppt_text(sl, lx + 2.325, 5.05, slbl, font_pt=16.0, color=col_rgb, bold=True, ha="center", va="top")

    # ==========================================================================
    # FIGURE 2 (Bipolar Mechanism, Ex-Situ FTIR & Ex-Situ XPS — 6 slides)
    # ==========================================================================
    s12 = load_slide(12)
    d12 = ImageDraw.Draw(s12)
    # Erase rotated 'Intensity (a.u.)' strips so pl=32 keeps leftmost X tick numbers unclipped!
    for bx0, by0, bx1, by1 in [(1600, 51, 2301, 559), (115, 685, 753, 1243), (890, 682, 1528, 1237), (1666, 682, 2304, 1242)]:
        d12.rectangle((bx0 - 65, by0, bx0 - 8, by1), fill=(255, 255, 255))

    sl = prs.slides.add_slide(blank)
    add_slide_header(sl, "Figure 2(a) — Bipolar Three-Electron Redox Mechanism of pTPA-PQ1", "论文图 2(a) 独立可编辑小图：双极性三电子氧化还原机理示意图与可拖动标签")
    add_General_box_slide(sl, s12, (107, 23, 1054, 644), "fig2a_scheme", "a", bottom_caption="Bipolar Redox Mechanism (p-Type PF₆⁻ & n-Type 2 Na⁺ Storage)")

    sl = prs.slides.add_slide(blank)
    add_slide_header(sl, "Figure 2(b-1) — In-Situ / Ex-Situ GCD Voltage Profile with Marked Charge/Discharge States", "论文图 2(b) 左图独立可编辑版：充放电状态取样点曲线与可拖动坐标轴标题")
    place_plot_with_draggable_titles(
        sl, s12, (1165, 56, 1497, 563), "fig2b_gcd", "b",
        xlabel="Potential (V vs. Na⁺/Na)", ylabel="",
        pad_ticks=(28, 12, 18, 44), box_l=4.60, box_t=1.10, box_w=3.80, box_h=5.00
    )

    sl = prs.slides.add_slide(blank)
    add_slide_header(sl, "Figure 2(b-2) — Ex-Situ FTIR Evolution During Charge & Discharge", "论文图 2(b) 右图独立可编辑版：非原位红外光谱演化与可拖动坐标轴标题")
    place_plot_with_draggable_titles(
        sl, s12, (1600, 51, 2301, 559), "fig2b_ftir", "b",
        xlabel="Wavenumber (cm⁻¹)", ylabel="Transmittance (a.u.)",
        pad_ticks=(34, 12, 32, 44), box_l=3.20, box_t=1.10, box_w=6.60, box_h=5.00
    )

    for idx_x, (s_box, elem_lbl) in enumerate([
        ((115, 685, 753, 1243), "Ex-Situ O 1s XPS"),
        ((890, 682, 1528, 1237), "Ex-Situ N 1s XPS"),
        ((1666, 682, 2304, 1242), "Ex-Situ F 1s XPS"),
    ], 1):
        sl = prs.slides.add_slide(blank)
        add_slide_header(sl, f"Figure 2(c-{idx_x}) — {elem_lbl} Core-Level Spectra at Pristine, 4.3 V, and 1.3 V", f"论文图 2(c-{idx_x}) 独立可编辑小图：{elem_lbl} 精细谱与可拖动标签/坐标轴标题")
        place_plot_with_draggable_titles(
            sl, s12, s_box, f"fig2c_xps_{idx_x}", "c",
            xlabel="Binding Energy (eV)", ylabel="Intensity (a.u.)",
            pad_ticks=(30, 14, 30, 45), badge_text=elem_lbl, badge_color=RGB_PQ1, badge_rel_xy=(0.35, 0.03)
        )

    # ==========================================================================
    # FIGURE 3 (Half-Cell & All-Climate Performance — 11 slides: a - k)
    # ==========================================================================
    s6 = load_slide(6)
    d6 = ImageDraw.Draw(s6)
    d6.rectangle((0, 0, 230, 120), fill=(255, 255, 255))
    d6.rectangle((1500, 790, 1770, 862), fill=(255, 255, 255))
    d6.rectangle((1875, 1075, 2225, 1116), fill=(255, 255, 255))

    s7 = load_slide(7)
    d7 = ImageDraw.Draw(s7)
    # Erase baked legend text inside both s7 plots so we can place native draggable PPT textboxes!
    for bx0, by0, bx1, by1 in [(268, 403, 996, 991), (1469, 403, 2197, 991)]:
        d7.rectangle((bx0 + 576, by0 + 142, bx0 + 720, by0 + 448), fill=(255, 255, 255))

    s15 = load_slide(15)
    d15 = ImageDraw.Draw(s15)
    for (bx0, by0, _, _), (rx0, ry0, rx1, ry1) in [
        ((577, 71, 1188, 552), (225, 342, 520, 478)),
        ((1470, 62, 2227, 538), (275, 308, 585, 464)),
        ((588, 756, 1199, 1237), (225, 342, 520, 478)),
        ((1477, 765, 2220, 1233), (275, 308, 585, 464)),
    ]:
        d15.rectangle((bx0 + rx0, by0 + ry0, bx0 + rx1, by0 + ry1), fill=(255, 255, 255))

    s16 = load_slide(16)
    d16 = ImageDraw.Draw(s16)
    for (bx0, by0, _, _), (rx0, ry0, rx1, ry1) in [
        ((611, 78, 1221, 559), (225, 325, 515, 468)),
        ((1492, 77, 2239, 547), (265, 150, 578, 295)),
        ((611, 762, 1221, 1243), (225, 325, 515, 468)),
        ((1492, 764, 2239, 1233), (265, 150, 578, 295)),
    ]:
        d16.rectangle((bx0 + rx0, by0 + ry0, bx0 + rx1, by0 + ry1), fill=(255, 255, 255))

    for ltr, s_box, cname, t_en, xl, yl, rl, pticks in [
        ("a", (319, 83, 821, 484), "fig3a_cv", "Figure 3(a) — Half-Cell CV Curves of pTPA-PQ1 and pTPA-PQ2 (1.2–4.1 V)", "Potential (V vs. Na⁺/Na)", "Current (mA)", None, (60, 18, 25, 45)),
        ("b", (978, 80, 1497, 498), "fig3b_rate", "Figure 3(b) — Rate Capability from 0.1 to 10.0 A g⁻¹", "Cycle number", "Specific capacity (mAh g⁻¹)", "Coulombic efficiency (%)", (64, 18, 65, 45)),
        ("c", (1713, 98, 2247, 488), "fig3c_700cyc", "Figure 3(c) — Cycling Performance at 0.2 A g⁻¹ over 700 Cycles", "Cycle number", "Specific capacity (mAh g⁻¹)", "Coulombic efficiency (%)", (59, 18, 59, 45)),
        ("d", (327, 688, 861, 1118), "fig3d_gcd", "Figure 3(d) — Galvanostatic Charge/Discharge (GCD) Profiles (1st–50th Cycle)", "Specific capacity (mAh g⁻¹)", "Potential (V vs. Na⁺/Na)", None, (55, 18, 25, 45)),
    ]:
        sl = prs.slides.add_slide(blank)
        add_slide_header(sl, t_en, f"论文图 3({ltr}) 独立可编辑小图：坐标轴标题与标签均为可拖动 PPT 原生文本框")
        place_plot_with_draggable_titles(
            sl, s6, s_box, cname, ltr, xlabel=xl, ylabel=yl, rlabel=rl,
            pad_ticks=pticks, rcolor=RGB_BLUE_AXIS if rl else RGB_TEXT
        )

    # Fig 3(e, f) — 100% native PPT tick numbers + axis titles + badge + draggable rate legend labels!
    s7_xticks = [(0.004 + i * 0.1578, str(i * 30)) for i in range(7)]
    s7_yticks = [(i * 0.1327, f"{1.0 + i * 0.5:.1f}") for i in range(8)]
    s7_rates = [
        (0.290, "0.2 A g⁻¹"),
        (0.375, "0.5 A g⁻¹"),
        (0.460, "1 A g⁻¹"),
        (0.545, "2 A g⁻¹"),
        (0.630, "5 A g⁻¹"),
        (0.715, "10 A g⁻¹"),
    ]
    for ltr, s_box, b_txt, b_col, t_en in [
        ("e", (1469, 403, 2197, 991), "pTPA-PQ1", RGB_PQ1, "Figure 3(e) — Rate GCD Voltage Profiles of pTPA-PQ1 (0.2 to 10 A g⁻¹)"),
        ("f", (268, 403, 996, 991), "pTPA-PQ2", RGB_PQ2, "Figure 3(f) — Rate GCD Voltage Profiles of pTPA-PQ2 (0.2 to 10 A g⁻¹)"),
    ]:
        sl = prs.slides.add_slide(blank)
        add_slide_header(sl, t_en, f"论文图 3({ltr}) 独立可编辑小图：所有横纵坐标刻度数字、坐标轴标题、样品框及右侧 6 档倍率文字均为 PPT 原生可拖动文本框")
        place_relabelled_2d_plot_on_slide(
            sl, s7, s_box, f"fig3{ltr}_rategcd", ltr,
            xticks=s7_xticks, xlabel="Specific capacity (mAh g⁻¹)",
            yticks=s7_yticks, ylabel="Potential (V vs. Na⁺/Na)",
            badge_text=b_txt, badge_color=b_col, badge_rel_xy=(0.04, 0.05),
            box_l=3.20, box_t=1.15, box_w=6.80, box_h=4.95,
        )
        for ry_frac, r_lbl in s7_rates:
            add_ppt_text(
                sl, 3.20 + 0.795 * 6.80, 1.15 + ry_frac * 4.95, r_lbl,
                font_pt=12.0, color=RGB_TEXT, bold=True, ha="left", va="center", w_in=1.35, h_in=0.28
            )

    # Fig 3(g) — 5000 cycles wide plot (100% native PPT tick numbers, axis titles, legend, current density!)
    sl = prs.slides.add_slide(blank)
    add_slide_header(sl, "Figure 3(g) — Ultra-Long 5000-Cycle Stability at High Rate of 5.0 A g⁻¹", "论文图 3(g) 独立可编辑小图：所有刻度数字、左右双 Y 轴标题、图例与电流密度标注均为可拖动 PPT 原生文本框")
    place_relabelled_2d_plot_on_slide(
        sl, s6, (1123, 710, 2233, 1124), "fig3g_5000cyc", "g",
        xticks=[(i / 5.0, str(i * 1000)) for i in range(6)],
        xlabel="Cycle number",
        yticks=[(i / 5.0, str(i * 50)) for i in range(6)],
        ylabel="Specific capacity (mAh g⁻¹)",
        rticks=[(i * 20.0 / 105.0, str(i * 20)) for i in range(6)],
        rlabel="Coulombic efficiency (%)",
        rcolor=RGB_TEXT,
        box_l=2.20, box_t=1.35, box_w=8.80, box_h=4.60,
    )
    add_ppt_legend(sl, 6.20, 2.25, [("pTPA-PQ1", RGB_PQ1, "bar"), ("pTPA-PQ2", RGB_PQ2, "bar")], font_pt=12.0, w_in=2.10)
    add_ppt_text(sl, 9.40, 5.55, "Current density: 5.0 A g⁻¹", font_pt=12.5, color=RGB_TEXT, bold=True)

    # Fig 3(h, i, j, k) — All-climate panels (100% native PPT tick numbers, axis titles, badges & legends!)
    rticks_ce = [(i * 20.0 / 105.0, str(i * 20)) for i in range(6)]
    yticks_250 = [(i / 5.0, str(i * 50)) for i in range(6)]
    xticks_1600 = [(i / 8.0, str(i * 200)) for i in range(9)]
    xticks_500 = [(i / 5.0, str(i * 100)) for i in range(6)]
    for ltr, s_im, s_box, xt, b_txt, b_col, leg_y, t_en in [
        ("h", s15, (1470, 62, 2227, 538), xticks_1600, "pTPA-PQ1 (50 °C, 5 A g⁻¹)", RGB_PQ1, 4.35, "Figure 3(h) — High-Temperature (50 °C) Cycling of pTPA-PQ1 at 5.0 A g⁻¹"),
        ("i", s15, (1477, 765, 2220, 1233), xticks_1600, "pTPA-PQ2 (50 °C, 5 A g⁻¹)", RGB_PQ2, 4.35, "Figure 3(i) — High-Temperature (50 °C) Cycling of pTPA-PQ2 at 5.0 A g⁻¹"),
        ("j", s16, (1492, 77, 2239, 547), xticks_500, "pTPA-PQ1 (-10 °C, 1 A g⁻¹)", RGB_PQ1, 2.65, "Figure 3(j) — Low-Temperature (-10 °C) Cycling of pTPA-PQ1 at 1.0 A g⁻¹"),
        ("k", s16, (1492, 764, 2239, 1233), xticks_500, "pTPA-PQ2 (-10 °C, 1 A g⁻¹)", RGB_PQ2, 2.65, "Figure 3(k) — Low-Temperature (-10 °C) Cycling of pTPA-PQ2 at 1.0 A g⁻¹"),
    ]:
        sl = prs.slides.add_slide(blank)
        add_slide_header(sl, t_en, f"论文图 3({ltr}) 独立可编辑小图：所有刻度数字、双 Y 轴标题、温度/倍率标签框与图例框均为 PPT 原生可拖动对象")
        place_relabelled_2d_plot_on_slide(
            sl, s_im, s_box, f"fig3{ltr}_climate", ltr,
            xticks=xt, xlabel="Cycle number",
            yticks=yticks_250, ylabel="Specific capacity (mAh g⁻¹)",
            rticks=rticks_ce, rlabel="Coulombic efficiency (%)",
            rcolor=RGB_BLUE_AXIS, badge_text=b_txt, badge_color=b_col, badge_rel_xy=(0.04, 0.11)
        )
        add_ppt_legend(
            sl, 5.75, leg_y,
            [("Charge", RGB_YELLOW_CHG, "bar"), ("Discharge", b_col, "bar"), ("Coulombic efficiency", RGB_BLUE_AXIS, "bar")],
            font_pt=11.0, w_in=2.45
        )

    # ==========================================================================
    # FIGURE 4 (Kinetics: CV, b-Values, Capacitive Ratio, GITT, DRT & EIS — 10 slides)
    # ==========================================================================
    s8 = load_slide(8)
    s10 = load_slide(10)
    s11 = load_slide(11)
    ImageDraw.Draw(s8).rectangle((0, 0, 750, 110), fill=(255, 255, 255))
    ImageDraw.Draw(s10).rectangle((0, 0, 2400, 118), fill=(255, 255, 255))
    ImageDraw.Draw(s11).rectangle((0, 0, 2400, 125), fill=(255, 255, 255))
    ImageDraw.Draw(s11).rectangle((0, 125, 390, 1350), fill=(255, 255, 255))

    for ltr, s_box, cname, t_en, xl, yl, rl, pticks in [
        ("a", (234, 140, 737, 542), "fig4a_cv", "Figure 4(a) — Multi-Scan-Rate CV Curves of pTPA-PQ1 (0.2–1.2 mV s⁻¹)", "Potential (V vs. Na⁺/Na)", "Current (mA)", None, (59, 18, 25, 45)),
        ("b", (989, 137, 1492, 542), "fig4b_bval", "Figure 4(b) — Power-Law log(i) vs. log(v) Plots & b-Value Fitting of pTPA-PQ1", "log (v / mV s⁻¹)", "log (|i| / mA)", None, (59, 18, 25, 45)),
        ("c", (1756, 151, 2259, 556), "fig4c_capbar", "Figure 4(c) — Capacitive vs. Diffusion-Controlled Contribution Ratios of pTPA-PQ1", "Scan rate (mV s⁻¹)", "Contribution ratio (%)", None, (57, 18, 25, 45)),
        ("d", (236, 721, 739, 1123), "fig4d_capcv", "Figure 4(d) — Capacitive Contribution Shaded CV Profile at 1.2 mV s⁻¹", "Potential (V vs. Na⁺/Na)", "Current (mA)", None, (59, 18, 25, 45)),
        ("e", (990, 718, 1487, 1123), "fig4e_gitt", "Figure 4(e) — GITT Potential Response & Na⁺ Diffusion Coefficient D_Na⁺", "Time (h)", "Potential (V vs. Na⁺/Na)", "log (D_Na⁺ / cm² s⁻¹)", (54, 18, 62, 45)),
    ]:
        sl = prs.slides.add_slide(blank)
        add_slide_header(sl, t_en, f"论文图 4({ltr}) 独立可编辑小图：坐标轴标题与编号标签均为可拖动 PPT 原生文本框")
        place_plot_with_draggable_titles(
            sl, s8, s_box, cname, ltr, xlabel=xl, ylabel=yl, rlabel=rl,
            pad_ticks=pticks, rcolor=RGB_BLUE_AXIS if rl else RGB_TEXT
        )

    # Fig 4(f) 1st-cycle 3D EIS
    sl = prs.slides.add_slide(blank)
    add_slide_header(sl, "Figure 4(f) — First-Cycle In-Situ 3D Nyquist EIS Waterfall of pTPA-PQ1", "论文图 4(f) 独立可编辑小图：首圈原位三维阻抗瀑布图与可拖动标签")
    add_General_box_slide(sl, s8, (1595, 745, 2398, 1155), "fig4f_3deis", "f", badge_text="pTPA-PQ1 (1st-Cycle In-Situ EIS)", badge_color=RGB_PQ1)

    # Fig 4(g-1, g-2) 1st-cycle DRT (pTPA-PQ1 & pTPA-PQ2) — pl=36 excludes baked 'Potential (V)'!
    for idx_g, (box_3d, box_2d, iso_lbl, col_rgb) in enumerate([
        ((185, 118, 955, 746), (309, 784, 752, 1239), "pTPA-PQ1 (1st-Cycle DRT)", RGB_PQ1),
        ((1415, 118, 2185, 746), (1624, 800, 2063, 1255), "pTPA-PQ2 (1st-Cycle DRT)", RGB_PQ2),
    ], 1):
        sl = prs.slides.add_slide(blank)
        add_slide_header(sl, f"Figure 4(g-{idx_g}) — 3D & 2D Distribution of Relaxation Times (DRT): {iso_lbl}", f"论文图 4(g-{idx_g}) 独立可编辑小图：左 3D 曲面图、右 2D 等高线图及所有文字标签均可独立拖动")
        c3d = ASSET_DIR / f"fig4g_{idx_g}_3d.png"
        s10.crop(box_3d).save(c3d)
        sl.shapes.add_picture(str(c3d), Inches(0.85), Inches(1.35), width=Inches(5.30), height=Inches(4.35))
        add_ppt_badge(sl, 1.15, 1.05, iso_lbl, font_pt=12.5, text_color=col_rgb, fill_color=RGB_WHITE, border_color=col_rgb, ha="left", va="top")
        place_plot_with_draggable_titles(
            sl, s10, box_2d, f"fig4g_{idx_g}_2d", "g",
            xlabel="log [τ (s)]", ylabel="Potential (V vs. Na⁺/Na)",
            pad_ticks=(36, 30, 152, 44), box_l=7.15, box_t=1.35, box_w=3.95, box_h=4.35
        )

    # Fig 4(h-1, h-2) Nyquist evolution & 100th-cycle 3D EIS — pl=67 keeps full Y tick numbers!
    for idx_h, (box_nyq, box_3d, iso_lbl, col_rgb) in enumerate([
        ((573, 165, 1138, 624), (395, 818, 1320, 1285), "pTPA-PQ1", RGB_PQ1),
        ((1650, 165, 2215, 624), (1475, 810, 2385, 1277), "pTPA-PQ2", RGB_PQ2),
    ], 1):
        sl = prs.slides.add_slide(blank)
        add_slide_header(sl, f"Figure 4(h-{idx_h}) — Nyquist Evolution (Pristine–1000th) & 100th-Cycle 3D EIS ({iso_lbl})", f"论文图 4(h-{idx_h}) 独立可编辑小图：阻抗演化图、100 圈三维阻抗图与标签框均可独立拖动")
        place_plot_with_draggable_titles(
            sl, s11, box_nyq, f"fig4h_{idx_h}_nyq", "h",
            xlabel="Z' (Ω)", ylabel="-Z'' (Ω)",
            pad_ticks=(67, 18, 30, 46), badge_text=iso_lbl, badge_color=col_rgb, badge_rel_xy=(0.68, 0.05),
            box_l=1.45, box_t=1.35, box_w=4.70, box_h=4.30
        )
        c3d = ASSET_DIR / f"fig4h_{idx_h}_3d.png"
        s11.crop(box_3d).save(c3d)
        sl.shapes.add_picture(str(c3d), Inches(6.85), Inches(1.45), width=Inches(5.80), height=Inches(3.60))
        add_ppt_text(sl, 9.75, 5.20, f"{iso_lbl} (100th-Cycle In-Situ 3D EIS)", font_pt=13.5, color=col_rgb, bold=True)

    # ==========================================================================
    # FIGURE 5 (Unified DFT Computational Mechanisms — 6 slides: a - f)
    # ==========================================================================
    img_left, img_top, fig_w, fig_h = 2.30, 0.86, 8.60, 6.05
    for ltr, title_en, title_cn, builder_fn, has_tag in [
        ("a", "Figure 5(a) — Anodic Oxidation Thresholds (Monomer VIP/AIP & Dimer AIP)", "论文图 5(a) 独立可编辑小图：所有文字标签、数值、差值圆角框、坐标轴与图例均为 PPT 原生可拖动文本框", build_panel_5a, True),
        ("b", "Figure 5(b) — Radical Cation Spin Density Isosurfaces (0.004 a.u.) & Hole Reorganization", "论文图 5(b) 独立可编辑小图：两个 3D 分子等值面图、外框及所有文字说明均为独立可拖动 PPT 对象", build_panel_5b, False),
        ("c", "Figure 5(c) — Oligomer Frontier Orbital Evolution (n = 1 → 2 → 3) & Valence Bandwidth W_v", "论文图 5(c) 独立可编辑小图：所有轨道能级数值、价带宽度圆角框、坐标轴刻度与标题均为可拖动 PPT 原生文本框", build_panel_5c, True),
        ("d", "Figure 5(d) — Bipolar Four-State Internal Reorganization Energies λ_reorg", "论文图 5(d) 独立可编辑小图：所有柱顶数值、百分比降幅圆角框、四态标签、坐标轴与图例均为可拖动 PPT 原生文本框", build_panel_5d, True),
        ("e", "Figure 5(e) — Trimer (n = 3) 32-Rotamer Pocket Distance Distribution & 4O–Na⁺ Trap", "论文图 5(e) 独立可编辑小图：开放单口袋标注、四氧夹心钠陷阱圆角框 (-22.8 kcal mol⁻¹)、图例与坐标轴均为可拖动 PPT 文本框", build_panel_5e, True),
        ("f", "Figure 5(f) — Relaxed 3D Trimer (n = 3) Conformations (Open Rod vs. Folded 4O–Na⁺ Trap)", "论文图 5(f) 独立可编辑小图：上下两个 3D 三聚体分子构象图、外框及所有文字标签均为独立可拖动 PPT 对象", build_panel_5f, False),
    ]:
        sl = prs.slides.add_slide(blank)
        add_slide_header(sl, title_en, title_cn)
        if has_tag:
            builder_fn(sl, img_left, img_top, fig_w, fig_h, scale=1.0, tag="allms")
        else:
            builder_fn(sl, img_left, img_top, fig_w, fig_h, scale=1.0)

    # ==========================================================================
    # FIGURE 6 (pTPA-PQ1 || Hard Carbon Full-Cell Performance — 5 slides: a - e)
    # ==========================================================================
    s13 = load_slide(13)
    s14 = load_slide(14)
    # Clean 'PQ-TPA1' on red disk of Slide 13 so we can place a draggable 'pTPA-PQ1' PPT textbox!
    s13_arr = np.array(s13)
    strip = s13_arr[463:493, 756:762].mean(axis=1, keepdims=True).astype(np.uint8)
    s13_arr[463:493, 766:895] = np.repeat(strip, 895 - 766, axis=1)
    s13 = Image.fromarray(s13_arr)
    ImageDraw.Draw(s13).rectangle((1030, 1015, 1560, 1195), fill=(255, 255, 255))
    # Clean 'PQ-TPA||Graphite' and CV legend text on Slide 14 so we can place draggable PPT textboxes!
    d14 = ImageDraw.Draw(s14)
    d14.rectangle((1546, 912, 1775, 949), fill=(255, 255, 255))
    d14.rectangle((446 + 84, 496 + 8, 446 + 148, 496 + 116), fill=(255, 255, 255))

    # Fig 6(a) Full-Cell Schematic
    sl = prs.slides.add_slide(blank)
    add_slide_header(sl, "Figure 6(a) — Schematic Illustration of the pTPA-PQ1 || Hard Carbon (HC) Full Cell", "论文图 6(a) 独立可编辑小图：全电池结构示意图与可拖动正极标签 pTPA-PQ1")
    add_General_box_slide(sl, s13, (614, 28, 1072, 608), "fig6a_fullcell_scheme", "a", bottom_caption="pTPA-PQ1 Cathode || Hard Carbon (HC) Anode Full Cell")
    add_ppt_text(sl, 6.80, 5.10, "pTPA-PQ1", font_pt=12.5, color=RGB_TEXT, bold=True)

    # Fig 6(b) Full-Cell CV (100% native PPT tick numbers + axis titles + 1st/2nd/3rd legend labels!)
    sl = prs.slides.add_slide(blank)
    add_slide_header(sl, "Figure 6(b) — Full-Cell CV Curve of pTPA-PQ1 || HC", "论文图 6(b) 独立可编辑小图：所有横纵坐标刻度数字、标题与 1st/2nd/3rd 图例均为可拖动 PPT 原生文本框")
    place_relabelled_2d_plot_on_slide(
        sl, s14, (446, 496, 1011, 952), "fig6b_fullcell_cv", "b",
        xticks=[(0.046 + i * 0.2133, str(i)) for i in range(5)],
        xlabel="Potential (V)",
        yticks=[(0.075, "-0.4"), (0.382, "0.0"), (0.691, "0.4"), (0.998, "0.8")],
        ylabel="Current (mA)",
        box_l=3.20, box_t=1.15, box_w=6.80, box_h=4.95,
    )
    for ry_frac, cyc_lbl in [(0.049, "1st"), (0.133, "2nd"), (0.216, "3rd")]:
        add_ppt_text(
            sl, 3.20 + 0.154 * 6.80, 1.15 + ry_frac * 4.95, cyc_lbl,
            font_pt=12.5, color=RGB_TEXT, bold=True, ha="left", va="center", w_in=0.80, h_in=0.28
        )

    # Fig 6(c) Full-Cell Rate Capability — pad_ticks=(68, 18, 70, 48)
    sl = prs.slides.add_slide(blank)
    add_slide_header(sl, "Figure 6(c) — Rate Capability of the pTPA-PQ1 || HC Full Cell (0.1–2.0 A g⁻¹)", "论文图 6(c) 独立可编辑小图：包含可拖动 pTPA-PQ1 || HC 图例标签与坐标轴标题")
    place_plot_with_draggable_titles(
        sl, s14, (1543, 499, 2109, 953), "fig6c_fullcell_rate", "c",
        xlabel="Cycle number", ylabel="Specific capacity (mAh g⁻¹)", rlabel="Coulombic efficiency (%)",
        pad_ticks=(68, 18, 70, 48), rcolor=RGB_BLUE_AXIS
    )
    add_ppt_text(sl, 3.30, 5.86, "pTPA-PQ1 || HC", font_pt=12.0, color=RGB_TEXT, bold=True, ha="left", va="center")

    # Fig 6(d) Full-Cell 0.2 A g^-1 Cycling (250 cycles) — pad_ticks=(82, 18, 78, 52)
    sl = prs.slides.add_slide(blank)
    add_slide_header(sl, "Figure 6(d) — Full-Cell Cycling Performance at 0.2 A g⁻¹ over 250 Cycles", "论文图 6(d) 独立可编辑小图：包含可拖动左右双 Y 轴与底部坐标轴标题")
    place_plot_with_draggable_titles(
        sl, s13, (1330, 54, 1975, 565), "fig6d_fullcell_250cyc", "d",
        xlabel="Cycle number", ylabel="Specific capacity (mAh g⁻¹)", rlabel="Coulombic efficiency (%)",
        pad_ticks=(82, 18, 78, 52), rcolor=RGB_BLUE_AXIS
    )

    # Fig 6(e) Full-Cell 2.0 A g^-1 Long-Term Cycling (2000 cycles, 100% native PPT ticks, axes, legend!)
    sl = prs.slides.add_slide(blank)
    add_slide_header(sl, "Figure 6(e) — Full-Cell Long-Term Cycling at 2.0 A g⁻¹ over 2000 Cycles", "论文图 6(e) 独立可编辑小图：所有刻度数字、双 Y 轴标题与图例框均为 PPT 原生可拖动对象")
    place_relabelled_2d_plot_on_slide(
        sl, s13, (580, 684, 1999, 1204), "fig6e_fullcell_2000cyc", "e",
        xticks=[(i / 4.0, str(i * 500)) for i in range(5)],
        xlabel="Cycle number",
        yticks=[(i / 4.0, str(i * 50)) for i in range(5)],
        ylabel="Specific capacity (mAh g⁻¹)",
        rticks=[(i * 20.0 / 105.0, str(i * 20)) for i in range(6)],
        rlabel="Coulombic efficiency (%)",
        rcolor=RGB_BLUE_AXIS,
        box_l=2.20, box_t=1.35, box_w=8.80, box_h=4.60,
    )
    add_ppt_legend(
        sl, 5.40, 4.15,
        [
            ("Charge (2.0 A g⁻¹)", RGB_YELLOW_CHG, "bar"),
            ("Discharge (2.0 A g⁻¹)", RGB_PQ1, "bar"),
            ("Coulombic efficiency", RGB_BLUE_AXIS, "bar"),
        ],
        font_pt=11.5, w_in=2.75
    )

    # ==========================================================================
    # SUPPORTING INFORMATION FIGURES S1 - S6
    # ==========================================================================
    # Fig S1 & S2: NMR and HRMS (4 slides)
    for fig_s_num, s_idx, ms_idx, iso_name, mz_obs, ms_frame, col_rgb in [
        ("S1", 1, 1, "TPA-PQ1", "452.1646", (488, 419, 1995, 1259), RGB_PQ1),
        ("S2", 2, 2, "TPA-PQ2", "452.1648", (509, 400, 2016, 1234), RGB_PQ2),
    ]:
        s_nmr = load_slide(s_idx)
        ImageDraw.Draw(s_nmr).rectangle((165, 350, 420, 585), fill=(255, 255, 255))
        sl_a = prs.slides.add_slide(blank)
        add_slide_header(sl_a, f"Figure {fig_s_num}(a) — ¹H NMR Spectrum of Monomer {iso_name} (400 MHz, CDCl₃)", f"附图 {fig_s_num}(a) 独立可编辑小图：核磁共振氢谱、外框、底部化学位移标题与标签框均可独立拖动")
        add_General_box_slide(
            sl_a, s_nmr, (18, 340, 1135, 1325), f"fig{fig_s_num}a_nmr", "a",
            bottom_caption="Chemical Shift δ (ppm)", badge_text=f"{iso_name} (¹H NMR, 400 MHz, CDCl₃)", badge_color=col_rgb
        )

        ms_im = load_ms_slide(ms_idx)
        mx0, my0, mx1, my1 = ms_frame
        ImageDraw.Draw(ms_im).rectangle((mx0 - 10, my0 - 15, mx0 + 540, my0 + 42), fill=(255, 255, 255))
        sl_b = prs.slides.add_slide(blank)
        add_slide_header(sl_b, f"Figure {fig_s_num}(b) — HR-APCI-FTMS Mass Spectrum of Monomer {iso_name}", f"附图 {fig_s_num}(b) 独立可编辑小图：所有刻度数字、坐标轴标题与质谱峰标注框均为 PPT 原生可拖动文本框")
        place_relabelled_2d_plot_on_slide(
            sl_b, ms_im, ms_frame, f"fig{fig_s_num}b_hrms", "b",
            xticks=[((m - 345.0) / (530.0 - 345.0), str(m)) for m in [350, 380, 410, 440, 470, 500, 520]],
            xlabel="m/z",
            yticks=[(v / 100.0, str(v)) for v in [0, 20, 40, 60, 80, 100]],
            ylabel="Relative Abundance (%)",
            badge_text=f"{iso_name} HR-APCI-FTMS\n[M + H]⁺ = {mz_obs}\nCalcd for C₃₂H₂₂NO₂⁺: 452.1645",
            badge_color=col_rgb, badge_rel_xy=(0.04, 0.06),
        )

    # Fig S3: Ex-Situ SEM (2 slides: S3a pTPA-PQ1 & S3b pTPA-PQ2, each with 4 draggable SEM images + headers)
    s4_boxes = [(10, 948, 534, 1301), (600, 948, 1124, 1301), (1224, 948, 1744, 1301), (1824, 948, 2347, 1301)]
    s5_boxes = [(5, 945, 528, 1298), (623, 945, 1142, 1298), (1228, 945, 1752, 1298), (1841, 945, 2360, 1298)]
    sem_headers = ["Pristine", "200 Cycles", "500 Cycles", "1000 Cycles"]
    for ltr, s_im, boxes, iso_lbl, col_rgb in [
        ("a", s4, s4_boxes, "pTPA-PQ1", RGB_PQ1),
        ("b", s5, s5_boxes, "pTPA-PQ2", RGB_PQ2),
    ]:
        sl = prs.slides.add_slide(blank)
        add_slide_header(sl, f"Figure S3({ltr}) — Ex-Situ SEM Morphology Evolution of {iso_lbl} (Pristine to 1000 Cycles)", f"附图 S3({ltr}) 独立可编辑小图：4 张非原位 SEM 图及顶部循环圈数标题、底部样品名均可独立拖动")
        add_ppt_text(sl, 0.55, 1.85, f"({ltr})", font_pt=20.0, color=RGB_TEXT, bold=True, ha="left", va="bottom")
        for idx_c, (sbox, h_txt) in enumerate(zip(boxes, sem_headers)):
            lx = 0.85 + idx_c * 2.95
            cp = ASSET_DIR / f"figS3{ltr}_{idx_c}.png"
            s_im.crop(sbox).save(cp)
            add_ppt_text(sl, lx + 1.38, 1.95, h_txt, font_pt=14.5, color=RGB_TEXT, bold=True, ha="center", va="bottom")
            sl.shapes.add_picture(str(cp), Inches(lx), Inches(2.10), width=Inches(2.76), height=Inches(1.90))
        add_ppt_text(sl, 13.333 / 2.0, 4.30, iso_lbl, font_pt=16.5, color=col_rgb, bold=True, ha="center", va="top")

    # Fig S4: Control Isomer pTPA-PQ2 Full Kinetics (6 slides: S4a - S4f)
    s9 = load_slide(9)
    arr9 = np.array(s9)
    sub9 = arr9[200:620, 1650:2350]
    red_mask = (sub9[:, :, 0] > 200) & (sub9[:, :, 1] < 140) & (sub9[:, :, 2] < 140)
    xs9 = np.where(red_mask.sum(axis=0) > 40)[0] + 1650
    splits9 = np.where(np.diff(xs9) > 5)[0] + 1
    groups9 = [g for g in np.split(xs9, splits9) if len(g) >= 15]
    d9 = ImageDraw.Draw(s9)
    d9.rectangle((0, 0, 800, 125), fill=(255, 255, 255))
    s9_bar_centers = []
    for g in groups9[:6]:
        x0_b, x1_b = int(g[0]), int(g[-1])
        col_slice = arr9[200:620, x0_b : x1_b + 1]
        col_red = (col_slice[:, :, 0] > 200) & (col_slice[:, :, 1] < 140)
        ys_b = np.where(col_red.sum(axis=1) > (x1_b - x0_b) // 2)[0] + 200
        y0_b, y1_b = int(ys_b[0]), int(ys_b[-1])
        pure_red_pixels = col_slice[(col_slice[:, :, 0] > 220) & (col_slice[:, :, 1] < 120)]
        bar_rgb = tuple(int(v) for v in np.median(pure_red_pixels, axis=0))
        d9.rectangle((x0_b + 2, y0_b + 15, x1_b - 2, y1_b - 8), fill=bar_rgb)
        s9_bar_centers.append(((x0_b + x1_b) / 2.0, y1_b - 35.0))

    for ltr, s_box, cname, t_en, xl, yl, rl, pticks in [
        ("a", (238, 213, 740, 615), "figS4a_cv", "Figure S4(a) — Multi-Scan-Rate CV Curves of pTPA-PQ2 (0.2–1.2 mV s⁻¹)", "Potential (V vs. Na⁺/Na)", "Current (mA)", None, (59, 18, 25, 45)),
        ("b", (997, 221, 1500, 626), "figS4b_bval", "Figure S4(b) — Power-Law log(i) vs. log(v) Fitting of pTPA-PQ2", "log (v / mV s⁻¹)", "log (|i| / mA)", None, (59, 18, 25, 45)),
        ("c", (1768, 221, 2271, 626), "figS4c_capbar", "Figure S4(c) — Capacitive Contribution Ratios of pTPA-PQ2 (63%–82%)", "Scan rate (mV s⁻¹)", "Contribution ratio (%)", None, (57, 18, 25, 45)),
        ("d", (238, 818, 740, 1220), "figS4d_capcv", "Figure S4(d) — Capacitive Shaded CV Profile of pTPA-PQ2 at 1.2 mV s⁻¹", "Potential (V vs. Na⁺/Na)", "Current (mA)", None, (59, 18, 25, 45)),
        ("e", (961, 815, 1458, 1220), "figS4e_gitt", "Figure S4(e) — GITT Potential Response & D_Na⁺ of pTPA-PQ2", "Time (h)", "Potential (V vs. Na⁺/Na)", "log (D_Na⁺ / cm² s⁻¹)", (54, 18, 62, 45)),
    ]:
        sl = prs.slides.add_slide(blank)
        add_slide_header(sl, t_en, f"附图 S4({ltr}) 独立可编辑小图：坐标轴标题与标签均为可拖动 PPT 原生文本框")
        place_plot_with_draggable_titles(
            sl, s9, s_box, cname, ltr, xlabel=xl, ylabel=yl, rlabel=rl,
            pad_ticks=pticks, rcolor=RGB_BLUE_AXIS if rl else RGB_TEXT
        )
        if ltr == "c":
            bx0, by0, bx1, by1 = s_box
            for (bcx, bcy), blbl in zip(s9_bar_centers, ["63%", "72%", "76%", "79%", "81%", "82%"]):
                px = 3.20 + (bcx - bx0) / float(bx1 - bx0) * 6.50
                py = 1.15 + (bcy - by0) / float(by1 - by0) * 4.95
                add_ppt_text(sl, px, py, blbl, font_pt=12.0, color=RGB_WHITE, bold=True, ha="center", va="center")

    sl = prs.slides.add_slide(blank)
    add_slide_header(sl, "Figure S4(f) — First-Cycle In-Situ 3D Nyquist EIS Waterfall of pTPA-PQ2", "附图 S4(f) 独立可编辑小图：首圈原位三维阻抗瀑布图与可拖动标签")
    add_General_box_slide(sl, s9, (1625, 845, 2345, 1205), "figS4f_3deis", "f", badge_text="pTPA-PQ2 (1st-Cycle In-Situ EIS)", badge_color=RGB_PQ2)

    # Fig S5 (50 °C All 4 Panels) & Fig S6 (-10 °C All 4 Panels) — 8 slides, 100% native PPT ticks, axes, badges & legends!
    yticks_400 = [(i / 8.0, str(i * 50)) for i in range(9)]
    xticks_400 = [(i / 4.0, str(i * 100)) for i in range(5)]
    xticks_300 = [(i / 3.0, str(i * 100)) for i in range(4)]

    for fig_s_tag, s_im, temp_str, rate_r, s_boxes, xt_list, yt_list, leg_ys in [
        (
            "S5", s15, "50 °C", "5.0 A g⁻¹",
            [(577, 71, 1188, 552), (1470, 62, 2227, 538), (588, 756, 1199, 1237), (1477, 765, 2220, 1233)],
            [xticks_400, xticks_1600, xticks_400, xticks_1600],
            [yticks_400, yticks_250, yticks_400, yticks_250],
            [4.55, 4.35, 4.55, 4.35],
        ),
        (
            "S6", s16, "-10 °C", "1.0 A g⁻¹",
            [(611, 78, 1221, 559), (1492, 77, 2239, 547), (611, 762, 1221, 1243), (1492, 764, 2239, 1233)],
            [xticks_300, xticks_500, xticks_300, xticks_500],
            [yticks_250, yticks_250, yticks_250, yticks_250],
            [4.45, 2.65, 4.45, 2.65],
        ),
    ]:
        badges = [
            (f"pTPA-PQ1 ({temp_str}, 0.2 A g⁻¹)", RGB_PQ1),
            (f"pTPA-PQ1 ({temp_str}, {rate_r})", RGB_PQ1),
            (f"pTPA-PQ2 ({temp_str}, 0.2 A g⁻¹)", RGB_PQ2),
            (f"pTPA-PQ2 ({temp_str}, {rate_r})", RGB_PQ2),
        ]
        for ltr, s_box, (b_txt, b_col), xt, yt, leg_y in zip(["a", "b", "c", "d"], s_boxes, badges, xt_list, yt_list, leg_ys):
            sl = prs.slides.add_slide(blank)
            add_slide_header(sl, f"Figure {fig_s_tag}({ltr}) — All-Climate Cycling Performance: {b_txt}", f"附图 {fig_s_tag}({ltr}) 独立可编辑小图：所有刻度数字、双 Y 轴标题、标注框与图例均为 PPT 原生可拖动对象")
            place_relabelled_2d_plot_on_slide(
                sl, s_im, s_box, f"fig{fig_s_tag}{ltr}", ltr,
                xticks=xt, xlabel="Cycle number",
                yticks=yt, ylabel="Specific capacity (mAh g⁻¹)",
                rticks=rticks_ce, rlabel="Coulombic efficiency (%)",
                rcolor=RGB_BLUE_AXIS, badge_text=b_txt, badge_color=b_col, badge_rel_xy=(0.04, 0.11)
            )
            add_ppt_legend(
                sl, 5.75, leg_y,
                [("Charge", RGB_YELLOW_CHG, "bar"), ("Discharge", b_col, "bar"), ("Coulombic efficiency", RGB_BLUE_AXIS, "bar")],
                font_pt=11.0, w_in=2.45
            )

    out_ms = MS_DIR / "TPA_PQ_All_Manuscript_Figures_Editable_Subpanels_v9.pptx"
    out_int = INT_DIR / "TPA_PQ_All_Manuscript_Figures_Editable_Subpanels_v9.pptx"
    prs.save(str(out_ms))
    shutil.copy2(out_ms, out_int)
    print(f"Saved All-Manuscript Editable PPTX ({len(prs.slides)} slides): {out_ms}")


if __name__ == "__main__":
    build_all_figures_pptx()
