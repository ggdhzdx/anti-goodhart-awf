#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reusable toolkit and CLI for decomposing composite scientific figures into
one-subpanel-per-slide PowerPoint (.pptx) decks with draggable native textboxes.

Component: skill.build-editable-figure-pptx@1.0.0-rc.2
Workflow:  editable-figure-pptx (aliases: FigPPT, figppt, AWF FigPPT, SciFig)
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
import zipfile
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple, Union

import numpy as np
from PIL import Image, ImageDraw
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.oxml.xmlchemy import OxmlElement
from pptx.util import Inches, Pt


ColorTuple = Tuple[int, int, int]
BBoxPx = Tuple[int, int, int, int]


# ---------------------------------------------------------------------------
# 1. Clean RGB Image Loading (Fixes Palette PNG transparency=(0, 0, 0) Bug)
# ---------------------------------------------------------------------------

def load_clean_rgb(path: Union[str, Path], bg_color: ColorTuple = (255, 255, 255)) -> Image.Image:
    """
    Load any PNG/JPEG/TIFF image and composite it onto a fresh opaque RGB canvas
    with an empty ``im.info`` dictionary.

    Why this is critical:
      8-bit paletted PNGs (mode="P") often carry ``im.info['transparency'] = idx``.
      Calling ``.convert("RGB")`` directly in Pillow converts that into
      ``im.info['transparency'] = (0, 0, 0)`` and writes a PNG ``tRNS`` chunk on save,
      causing PowerPoint to render pure black ``(0, 0, 0)`` axis spines and glyph
      cores as transparent ("hollow text / missing black axes").
    """
    im_rgba = Image.open(path).convert("RGBA")
    canvas = Image.new("RGB", im_rgba.size, bg_color)
    canvas.paste(im_rgba, mask=im_rgba.split()[3])
    return canvas


def erase_rects(
    im: Image.Image,
    rects: Sequence[BBoxPx],
    fill: ColorTuple = (255, 255, 255),
) -> Image.Image:
    """Return a copy of ``im`` with all ``(x0, y0, x1, y1)`` rectangles filled."""
    out = im.copy()
    draw = ImageDraw.Draw(out)
    w, h = out.size
    for x0, y0, x1, y1 in rects:
        cx0 = max(0, min(w, int(x0)))
        cy0 = max(0, min(h, int(y0)))
        cx1 = max(0, min(w, int(x1)))
        cy1 = max(0, min(h, int(y1)))
        if cx1 > cx0 and cy1 > cy0:
            draw.rectangle([cx0, cy0, cx1, cy1], fill=fill)
    return out


# ---------------------------------------------------------------------------
# 2. Plot Box & Ink-Margin Scanner (Separates Tick Numbers from Axis Titles)
# ---------------------------------------------------------------------------

@dataclass
class PlotInkMargins:
    plot_box: BBoxPx
    left_tick_pad_px: int
    top_tick_pad_px: int
    right_tick_pad_px: int
    bottom_tick_pad_px: int
    left_title_erase_rect: Optional[BBoxPx]
    bottom_title_erase_rect: Optional[BBoxPx]

    def to_dict(self) -> dict:
        return asdict(self)


def _find_first_white_gap(profile: np.ndarray, min_run_px: int = 4, start_offset: int = 4) -> Optional[int]:
    """
    Given a 1D boolean array ``profile`` where True means ink is present at distance
    ``d`` outward from the plot spine, find the distance ``d`` where the tick-number
    band ends and a white gap of at least ``min_run_px`` begins.
    """
    n = len(profile)
    seen_ink = False
    white_run = 0
    for d in range(start_offset, n):
        if profile[d]:
            seen_ink = True
            white_run = 0
        else:
            if seen_ink:
                white_run += 1
                if white_run >= min_run_px:
                    return d - white_run + 2
    return None


def scan_plot_box_and_ink_gaps(
    im: Image.Image,
    approx_box: BBoxPx,
    max_search_left: int = 160,
    max_search_bottom: int = 120,
    ink_threshold: int = 240,
) -> PlotInkMargins:
    """
    Inspect the outward pixel bands around a 2D plot box ``(bx0, by0, bx1, by1)``
    to find the clean white gap separating tick numbers from the outer axis titles.
    """
    arr = np.asarray(im.convert("L"))
    h, w = arr.shape
    bx0, by0, bx1, by1 = [int(v) for v in approx_box]

    # Left of Y-axis spine (scanning leftward from bx0)
    x_min = max(0, bx0 - max_search_left)
    left_strip = arr[max(0, by0 - 10):min(h, by1 + 15), x_min:bx0]
    # left_profile[d] = True if there is ink at distance d left of bx0
    left_profile = (left_strip < ink_threshold).any(axis=0)[::-1]
    left_gap = _find_first_white_gap(left_profile, min_run_px=5, start_offset=4)
    pl = int(left_gap) if left_gap is not None else 55

    # Below X-axis spine (scanning downward from by1)
    y_max = min(h, by1 + max_search_bottom)
    bot_strip = arr[by1:y_max, max(0, bx0 - 25):min(w, bx1 + 25)]
    bot_profile = (bot_strip < ink_threshold).any(axis=1)
    bot_gap = _find_first_white_gap(bot_profile, min_run_px=4, start_offset=4)
    pb = int(bot_gap) if bot_gap is not None else 36

    left_erase = (x_min, max(0, by0 - 15), max(0, bx0 - pl), min(h, by1 + 20))
    bot_erase = (max(0, bx0 - 30), min(h, by1 + pb), min(w, bx1 + 30), y_max)

    return PlotInkMargins(
        plot_box=(bx0, by0, bx1, by1),
        left_tick_pad_px=pl,
        top_tick_pad_px=14,
        right_tick_pad_px=18,
        bottom_tick_pad_px=pb,
        left_title_erase_rect=left_erase,
        bottom_title_erase_rect=bot_erase,
    )


# ---------------------------------------------------------------------------
# 3. Pixel & Data -> PowerPoint Coordinate Bridge
# ---------------------------------------------------------------------------

@dataclass
class DataToPptBridge:
    """
    Exact affine coordinate bridge mapping source image pixels ``(px, py)`` and
    scientific plot data values ``(x_val, y_val)`` to PowerPoint slide coordinates
    in inches.
    """
    crop_x0: int
    crop_y0: int
    crop_w: int
    crop_h: int
    pic_left_in: float
    pic_top_in: float
    pic_w_in: float
    pic_h_in: float
    plot_box_px: Optional[BBoxPx] = None
    x_range: Optional[Tuple[float, float]] = None
    y_range: Optional[Tuple[float, float]] = None

    @classmethod
    def from_crop_in_box(
        cls,
        crop_rect: BBoxPx,
        target_box_in: Tuple[float, float, float, float],
        plot_box_px: Optional[BBoxPx] = None,
        x_range: Optional[Tuple[float, float]] = None,
        y_range: Optional[Tuple[float, float]] = None,
    ) -> "DataToPptBridge":
        cx0, cy0, cx1, cy1 = [int(v) for v in crop_rect]
        cw = max(1, cx1 - cx0)
        ch = max(1, cy1 - cy0)
        left_in, top_in, max_w_in, max_h_in = target_box_in
        scale = min(max_w_in / cw, max_h_in / ch)
        pw = cw * scale
        ph = ch * scale
        pl = left_in + (max_w_in - pw) / 2.0
        pt = top_in + (max_h_in - ph) / 2.0
        return cls(
            crop_x0=cx0,
            crop_y0=cy0,
            crop_w=cw,
            crop_h=ch,
            pic_left_in=pl,
            pic_top_in=pt,
            pic_w_in=pw,
            pic_h_in=ph,
            plot_box_px=plot_box_px,
            x_range=x_range,
            y_range=y_range,
        )

    def px_to_ppt(self, px: float, py: float) -> Tuple[float, float]:
        """Map source image pixel ``(px, py)`` to ``(slide_x_in, slide_y_in)``."""
        sx = self.pic_left_in + ((px - self.crop_x0) / self.crop_w) * self.pic_w_in
        sy = self.pic_top_in + ((py - self.crop_y0) / self.crop_h) * self.pic_h_in
        return sx, sy

    def plot_edges_in(self) -> Tuple[float, float, float, float]:
        """Return ``(bx0_in, by0_in, bx1_in, by1_in)`` of the plot box on the slide."""
        if self.plot_box_px is None:
            return (
                self.pic_left_in,
                self.pic_top_in,
                self.pic_left_in + self.pic_w_in,
                self.pic_top_in + self.pic_h_in,
            )
        bx0, by0, bx1, by1 = self.plot_box_px
        x0_in, y0_in = self.px_to_ppt(bx0, by0)
        x1_in, y1_in = self.px_to_ppt(bx1, by1)
        return x0_in, y0_in, x1_in, y1_in

    def x_to_ppt(self, x_val: float) -> float:
        """Map data coordinate ``x_val`` along X-axis to slide X coordinate in inches."""
        if self.plot_box_px is None or self.x_range is None:
            raise ValueError("plot_box_px and x_range are required for x_to_ppt()")
        bx0, _, bx1, _ = self.plot_box_px
        xmin, xmax = self.x_range
        frac = (x_val - xmin) / (xmax - xmin) if xmax != xmin else 0.0
        px = bx0 + frac * (bx1 - bx0)
        return self.px_to_ppt(px, 0.0)[0]

    def y_to_ppt(self, y_val: float) -> float:
        """Map data coordinate ``y_val`` along Y-axis to slide Y coordinate in inches."""
        if self.plot_box_px is None or self.y_range is None:
            raise ValueError("plot_box_px and y_range are required for y_to_ppt()")
        _, by0, _, by1 = self.plot_box_px
        ymin, ymax = self.y_range
        frac = (y_val - ymin) / (ymax - ymin) if ymax != ymin else 0.0
        # Note: y_min is at bottom spine by1, y_max is at top spine by0
        py = by1 - frac * (by1 - by0)
        return self.px_to_ppt(0.0, py)[1]


# ---------------------------------------------------------------------------
# 4. Native PowerPoint Typography with OpenXML Subscripts & Superscripts
# ---------------------------------------------------------------------------

_SCRIPT_TOKEN_RE = re.compile(r"(\^\{[^}]+\}|_\{[^}]+\})")


def set_rpr_all_font_slots(rPr, font_name: str = "Arial") -> None:
    """
    Explicitly set ``<a:latin>``, ``<a:ea>``, ``<a:cs>``, and ``<a:sym>`` typefaces on
    an OpenXML ``<a:rPr>`` or ``<a:endParaRPr>`` element.

    Why this is critical on Chinese Windows PowerPoint (zh-CN):
      ``run.font.name = 'Arial'`` in ``python-pptx`` only writes ``<a:latin typeface='Arial'/>``.
      Greek letters (π, θ, φ, γ, β, μ, σ, λ, Δ), degree signs (°), en-dashes (–), and arrows (→)
      are classified as East Asian Ambiguous Width characters in zh-CN locales, causing PowerPoint
      to fall back to the East Asian theme font (Calibri / 等线 / 宋体) unless ``<a:ea>``,
      ``<a:cs>``, and ``<a:sym>`` are also explicitly set to ``font_name``.
    """
    for tag_name in ("a:latin", "a:ea", "a:cs", "a:sym"):
        old = rPr.find(qn(tag_name))
        if old is not None:
            rPr.remove(old)
        el = OxmlElement(tag_name)
        el.set("typeface", font_name)
        rPr.append(el)


def populate_paragraph_with_scripts(
    p,
    markup_text: str,
    font_size: float = 11.0,
    bold: bool = False,
    italic: bool = False,
    color: ColorTuple = (20, 20, 20),
    font_name: str = "Arial",
) -> None:
    """
    Populate a ``python-pptx`` paragraph using inline ``_{sub}`` and ``^{sup}``
    markup converted into native OpenXML runs with ``baseline="-25000"`` or
    ``baseline="30000"``, and enforce all four OpenXML font slots (latin/ea/cs/sym).
    """
    tokens = _SCRIPT_TOKEN_RE.split(markup_text)
    for tok in tokens:
        if not tok:
            continue
        run = p.add_run()
        rPr = run._r.get_or_add_rPr()
        if tok.startswith("^{") and tok.endswith("}"):
            run.text = tok[2:-1]
            rPr.set("baseline", "30000")
        elif tok.startswith("_{") and tok.endswith("}"):
            run.text = tok[2:-1]
            rPr.set("baseline", "-25000")
        else:
            run.text = tok
        run.font.name = font_name
        run.font.size = Pt(font_size)
        run.font.bold = bold
        run.font.italic = italic
        run.font.color.rgb = RGBColor(*color)
        set_rpr_all_font_slots(rPr, font_name=font_name)
    end_rpr = p._p.find(qn("a:endParaRPr"))
    if end_rpr is not None:
        set_rpr_all_font_slots(end_rpr, font_name=font_name)


def save_presentation_with_uniform_font(
    prs: Presentation,
    out_path: Union[str, Path],
    font_name: str = "Arial",
) -> Path:
    """
    Save ``prs`` to ``out_path`` while enforcing ``font_name`` across:
      1. Every ``<a:rPr>`` and ``<a:endParaRPr>`` in every slide shape (`latin`, `ea`, `cs`, `sym`).
      2. Every ``typeface="..."`` attribute in ``ppt/theme/*.xml``, ``ppt/slideMasters/*.xml``,
         ``ppt/slideLayouts/*.xml``, ``ppt/slides/*.xml``, and ``ppt/presentation.xml``.
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    for slide in prs.slides:
        for shp in slide.shapes:
            if getattr(shp, "has_text_frame", False):
                for p in shp.text_frame.paragraphs:
                    for r in p.runs:
                        r.font.name = font_name
                        set_rpr_all_font_slots(r._r.get_or_add_rPr(), font_name=font_name)
                    end_rpr = p._p.find(qn("a:endParaRPr"))
                    if end_rpr is not None:
                        set_rpr_all_font_slots(end_rpr, font_name=font_name)

    with tempfile.NamedTemporaryFile(suffix=".pptx", delete=False) as tf:
        tmp_path = Path(tf.name)
    try:
        prs.save(str(tmp_path))
        with zipfile.ZipFile(tmp_path, "r") as zin, zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename.endswith(".xml") and (
                    item.filename.startswith("ppt/theme/")
                    or item.filename.startswith("ppt/slideMasters/")
                    or item.filename.startswith("ppt/slideLayouts/")
                    or item.filename.startswith("ppt/slides/")
                    or item.filename == "ppt/presentation.xml"
                ):
                    txt = data.decode("utf-8")
                    txt = re.sub(r'typeface="[^"]*"', f'typeface="{font_name}"', txt)
                    data = txt.encode("utf-8")
                zout.writestr(item, data)
    finally:
        tmp_path.unlink(missing_ok=True)
    return out_path


def add_ppt_vector_legend(
    slide,
    left_in: float,
    top_in: float,
    w_in: float,
    h_in: float,
    items: Sequence[Tuple[str, ColorTuple]],
    marker_kind: str = "circle",
    layout: str = "vertical",
    font_size: float = 9.0,
    font_name: str = "Arial",
    bg_color: ColorTuple = (255, 255, 255),
    border_color: ColorTuple = (203, 213, 225),
):
    """
    Add a native PowerPoint legend box using true vector marker shapes (``circle``,
    ``square``, or ``line``) and independent native textboxes instead of Unicode
    geometric characters (``●``, ``■``), preventing symbol-font fallback and
    space-padding alignment drift.
    """
    box = slide.shapes.add_textbox(Inches(left_in), Inches(top_in), Inches(w_in), Inches(h_in))
    box.fill.solid()
    box.fill.fore_color.rgb = RGBColor(*bg_color)
    box.line.color.rgb = RGBColor(*border_color)
    box.line.width = Pt(0.75)

    n = max(1, len(items))
    if layout == "horizontal":
        slot_w = w_in / n
        for idx, (label, col) in enumerate(items):
            x0 = left_in + idx * slot_w
            yc = top_in + 0.5 * h_in
            if marker_kind == "circle":
                mk = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x0 + 0.06), Inches(yc - 0.045), Inches(0.09), Inches(0.09))
            elif marker_kind == "line":
                mk = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x0 + 0.05), Inches(yc - 0.012), Inches(0.16), Inches(0.024))
            else:
                mk = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x0 + 0.06), Inches(yc - 0.045), Inches(0.09), Inches(0.09))
            mk.fill.solid()
            mk.fill.fore_color.rgb = RGBColor(*col)
            mk.line.fill.background()
            add_ppt_text(
                slide, x0 + 0.18, top_in + 0.01, slot_w - 0.20, h_in - 0.02,
                label, font_size=font_size, bold=True, color=col, font_name=font_name,
            )
    else:
        slot_h = h_in / n
        for idx, (label, col) in enumerate(items):
            y0 = top_in + idx * slot_h
            yc = y0 + 0.5 * slot_h
            if marker_kind == "circle":
                mk = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(left_in + 0.06), Inches(yc - 0.045), Inches(0.09), Inches(0.09))
            elif marker_kind == "line":
                mk = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(left_in + 0.05), Inches(yc - 0.012), Inches(0.16), Inches(0.024))
            else:
                mk = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(left_in + 0.06), Inches(yc - 0.045), Inches(0.09), Inches(0.09))
            mk.fill.solid()
            mk.fill.fore_color.rgb = RGBColor(*col)
            mk.line.fill.background()
            add_ppt_text(
                slide, left_in + 0.22, y0, w_in - 0.24, slot_h,
                label, font_size=font_size, bold=True, color=col, font_name=font_name,
            )
    return box


def add_ppt_text(
    slide,
    left_in: float,
    top_in: float,
    w_in: float,
    h_in: float,
    text: str,
    font_size: float = 11.0,
    bold: bool = False,
    italic: bool = False,
    color: ColorTuple = (20, 20, 20),
    align=PP_ALIGN.LEFT,
    font_name: str = "Arial",
    bg_color: Optional[ColorTuple] = None,
    border_color: Optional[ColorTuple] = None,
    border_pt: float = 0.75,
    word_wrap: bool = False,
    rotation: float = 0.0,
    margin_in: float = 0.02,
):
    """Add a compact, draggable native PowerPoint textbox supporting ``_{sub}`` and ``^{sup}``."""
    tb = slide.shapes.add_textbox(Inches(left_in), Inches(top_in), Inches(w_in), Inches(h_in))
    if rotation != 0.0:
        tb.rotation = rotation
    tf = tb.text_frame
    tf.word_wrap = word_wrap
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = Inches(margin_in)
    tf.margin_right = Inches(margin_in)
    tf.margin_top = Inches(margin_in / 2.0)
    tf.margin_bottom = Inches(margin_in / 2.0)

    if bg_color is not None:
        tb.fill.solid()
        tb.fill.fore_color.rgb = RGBColor(*bg_color)
    else:
        tb.fill.background()

    if border_color is not None:
        tb.line.color.rgb = RGBColor(*border_color)
        tb.line.width = Pt(border_pt)
    else:
        tb.line.fill.background()

    lines = str(text).split("\n")
    for idx, line in enumerate(lines):
        p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
        p.alignment = align
        populate_paragraph_with_scripts(
            p,
            line,
            font_size=font_size,
            bold=bold,
            italic=italic,
            color=color,
            font_name=font_name,
        )
    return tb


def add_ppt_badge(
    slide,
    left_in: float,
    top_in: float,
    w_in: float,
    h_in: float,
    text: str,
    bg_color: ColorTuple = (30, 41, 59),
    text_color: ColorTuple = (255, 255, 255),
    font_size: float = 12.0,
    bold: bool = True,
):
    """Add a rounded-rectangle badge shape with centered native text."""
    shp = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        Inches(left_in),
        Inches(top_in),
        Inches(w_in),
        Inches(h_in),
    )
    shp.fill.solid()
    shp.fill.fore_color.rgb = RGBColor(*bg_color)
    shp.line.fill.background()
    tf = shp.text_frame
    tf.word_wrap = False
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = Inches(0.03)
    tf.margin_right = Inches(0.03)
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    populate_paragraph_with_scripts(
        p,
        text,
        font_size=font_size,
        bold=bold,
        color=text_color,
    )
    return shp


# ---------------------------------------------------------------------------
# 5. High-Level 2D Plot Placement Helpers (Mode A & Mode B)
# ---------------------------------------------------------------------------

def place_plot_with_draggable_titles(
    slide,
    src_im: Image.Image,
    plot_box: BBoxPx,
    target_box_in: Tuple[float, float, float, float],
    crop_out_path: Union[str, Path],
    xlabel: str = "",
    ylabel: str = "",
    title: str = "",
    pad_ticks: Tuple[int, int, int, int] = (55, 14, 18, 36),
    extra_erase_rects: Optional[Sequence[BBoxPx]] = None,
    title_font_pt: float = 12.5,
    axis_font_pt: float = 11.5,
) -> DataToPptBridge:
    """
    Mode B (Preserve Original Tick Numbers):
      Erase only the outer X/Y axis titles and internal legend/annotations specified in
      ``extra_erase_rects``, crop around ``plot_box`` with ``pad_ticks=(pl, pt, pr, pb)``
      so original tick marks and tick numbers remain 100% intact, insert the cropped PNG,
      and add draggable native PowerPoint textboxes for ``xlabel``, rotated ``ylabel``,
      and ``title``.
    """
    bx0, by0, bx1, by1 = [int(v) for v in plot_box]
    pl, pt, pr, pb = [int(v) for v in pad_ticks]
    w, h = src_im.size

    # Automatically erase outside the tick padding window so outer titles cannot bleed in
    cx0 = max(0, bx0 - pl)
    cy0 = max(0, by0 - pt)
    cx1 = min(w, bx1 + pr)
    cy1 = min(h, by1 + pb)

    work = src_im.copy()
    if extra_erase_rects:
        work = erase_rects(work, extra_erase_rects)

    crop_im = work.crop((cx0, cy0, cx1, cy1))
    crop_out_path = Path(crop_out_path)
    crop_out_path.parent.mkdir(parents=True, exist_ok=True)
    crop_im.save(crop_out_path)

    bridge = DataToPptBridge.from_crop_in_box(
        crop_rect=(cx0, cy0, cx1, cy1),
        target_box_in=target_box_in,
        plot_box_px=(bx0, by0, bx1, by1),
    )

    slide.shapes.add_picture(
        str(crop_out_path),
        Inches(bridge.pic_left_in),
        Inches(bridge.pic_top_in),
        Inches(bridge.pic_w_in),
        Inches(bridge.pic_h_in),
    )

    bx0_in, by0_in, bx1_in, by1_in = bridge.plot_edges_in()
    plot_w_in = bx1_in - bx0_in
    plot_h_in = by1_in - by0_in

    if title:
        add_ppt_text(
            slide,
            bx0_in - 0.2,
            bridge.pic_top_in - 0.34,
            plot_w_in + 0.4,
            0.30,
            title,
            font_size=title_font_pt,
            bold=True,
            align=PP_ALIGN.CENTER,
        )

    if xlabel:
        add_ppt_text(
            slide,
            bx0_in - 0.2,
            bridge.pic_top_in + bridge.pic_h_in + 0.02,
            plot_w_in + 0.4,
            0.32,
            xlabel,
            font_size=axis_font_pt,
            bold=True,
            align=PP_ALIGN.CENTER,
        )

    if ylabel:
        # Place rotated Y-axis label just left of the cropped tick-number margin
        yc = 0.5 * (by0_in + by1_in)
        span = max(1.8, plot_h_in)
        rx = bridge.pic_left_in - 0.26
        add_ppt_text(
            slide,
            rx - span / 2.0,
            yc - 0.16,
            span,
            0.32,
            ylabel,
            font_size=axis_font_pt,
            bold=True,
            align=PP_ALIGN.CENTER,
            rotation=-90.0,
        )

    return bridge


def place_relabelled_2d_plot_on_slide(
    slide,
    src_im: Image.Image,
    plot_box: BBoxPx,
    target_box_in: Tuple[float, float, float, float],
    crop_out_path: Union[str, Path],
    x_range: Tuple[float, float],
    y_range: Tuple[float, float],
    xticks: Sequence[Tuple[float, str]],
    yticks: Sequence[Tuple[float, str]],
    xlabel: str = "",
    ylabel: str = "",
    title: str = "",
    spine_pad_px: int = 5,
    extra_erase_rects: Optional[Sequence[BBoxPx]] = None,
    tick_font_pt: float = 9.5,
    axis_font_pt: float = 11.5,
    title_font_pt: float = 12.5,
) -> DataToPptBridge:
    """
    Mode A (Full Tick & Axis Replacement):
      Crop tightly to ``(bx0 - spine_pad_px, by0 - spine_pad_px, bx1 + spine_pad_px, by1 + spine_pad_px)``
      so outward tick marks are preserved while all original tick numbers and axis titles
      stay outside the crop. Then place native PowerPoint tick labels at exact coordinates
      computed via ``bridge.x_to_ppt(val)`` and ``bridge.y_to_ppt(val)``.
    """
    bx0, by0, bx1, by1 = [int(v) for v in plot_box]
    w, h = src_im.size
    cx0 = max(0, bx0 - spine_pad_px)
    cy0 = max(0, by0 - spine_pad_px)
    cx1 = min(w, bx1 + spine_pad_px)
    cy1 = min(h, by1 + spine_pad_px)

    work = src_im.copy()
    if extra_erase_rects:
        work = erase_rects(work, extra_erase_rects)

    crop_im = work.crop((cx0, cy0, cx1, cy1))
    crop_out_path = Path(crop_out_path)
    crop_out_path.parent.mkdir(parents=True, exist_ok=True)
    crop_im.save(crop_out_path)

    bridge = DataToPptBridge.from_crop_in_box(
        crop_rect=(cx0, cy0, cx1, cy1),
        target_box_in=target_box_in,
        plot_box_px=(bx0, by0, bx1, by1),
        x_range=x_range,
        y_range=y_range,
    )

    slide.shapes.add_picture(
        str(crop_out_path),
        Inches(bridge.pic_left_in),
        Inches(bridge.pic_top_in),
        Inches(bridge.pic_w_in),
        Inches(bridge.pic_h_in),
    )

    bx0_in, by0_in, bx1_in, by1_in = bridge.plot_edges_in()
    plot_w_in = bx1_in - bx0_in
    plot_h_in = by1_in - by0_in

    for x_val, x_str in xticks:
        tx_in = bridge.x_to_ppt(x_val)
        add_ppt_text(
            slide,
            tx_in - 0.35,
            by1_in + 0.04,
            0.70,
            0.22,
            x_str,
            font_size=tick_font_pt,
            align=PP_ALIGN.CENTER,
        )

    for y_val, y_str in yticks:
        ty_in = bridge.y_to_ppt(y_val)
        add_ppt_text(
            slide,
            bx0_in - 0.68,
            ty_in - 0.11,
            0.62,
            0.22,
            y_str,
            font_size=tick_font_pt,
            align=PP_ALIGN.RIGHT,
        )

    if title:
        add_ppt_text(
            slide,
            bx0_in - 0.2,
            by0_in - 0.36,
            plot_w_in + 0.4,
            0.30,
            title,
            font_size=title_font_pt,
            bold=True,
            align=PP_ALIGN.CENTER,
        )

    if xlabel:
        add_ppt_text(
            slide,
            bx0_in - 0.2,
            by1_in + 0.28,
            plot_w_in + 0.4,
            0.30,
            xlabel,
            font_size=axis_font_pt,
            bold=True,
            align=PP_ALIGN.CENTER,
        )

    if ylabel:
        yc = 0.5 * (by0_in + by1_in)
        span = max(1.8, plot_h_in)
        rx = bx0_in - 0.82
        add_ppt_text(
            slide,
            rx - span / 2.0,
            yc - 0.16,
            span,
            0.32,
            ylabel,
            font_size=axis_font_pt,
            bold=True,
            align=PP_ALIGN.CENTER,
            rotation=-90.0,
        )

    return bridge


# ---------------------------------------------------------------------------
# 6. Automated PPTX Editability & Collision Auditor
# ---------------------------------------------------------------------------

def audit_pptx_editable_shapes(
    pptx_path: Union[str, Path],
    min_text_shapes_per_slide: int = 2,
    require_font: Optional[str] = None,
) -> Dict[str, object]:
    """
    Audit a generated ``.pptx`` file to verify:
      1. Every slide contains at least one picture and at least ``min_text_shapes_per_slide``
         native editable text shapes.
      2. None of the embedded PNG images contain a paletted or RGB ``tRNS`` chunk marking
         pure black ``(0, 0, 0)`` as transparent.
      3. Inspect all XML files in the package for ``typeface="..."`` declarations and, if
         ``require_font`` is specified (e.g., ``"Arial"``), verify that 100% of typefaces
         equal ``require_font``.
      4. Report total slides, total pictures, total editable text shapes, and any warnings.
    """
    prs = Presentation(str(pptx_path))
    slide_reports = []
    total_pictures = 0
    total_text_shapes = 0
    trns_black_violations = []
    sparse_text_slides = []

    for idx, slide in enumerate(prs.slides, start=1):
        pics = 0
        txt_shapes = 0
        sample_texts = []
        for shp in slide.shapes:
            if shp.shape_type == 13:  # PICTURE
                pics += 1
                blob = shp.image.blob
                # Check if PNG has transparency=(0, 0, 0)
                try:
                    import io
                    im = Image.open(io.BytesIO(blob))
                    trns = im.info.get("transparency")
                    if trns == (0, 0, 0) or (im.mode == "P" and trns is not None):
                        trns_black_violations.append(
                            {"slide": idx, "shape_name": shp.name, "mode": im.mode, "transparency": str(trns)}
                        )
                except Exception:
                    pass
            if getattr(shp, "has_text_frame", False):
                t = shp.text_frame.text.strip()
                if t:
                    txt_shapes += 1
                    if len(sample_texts) < 4:
                        sample_texts.append(t.replace("\n", " / "))

        total_pictures += pics
        total_text_shapes += txt_shapes
        if txt_shapes < min_text_shapes_per_slide:
            sparse_text_slides.append(idx)

        slide_reports.append(
            {
                "slide": idx,
                "pictures": pics,
                "editable_text_shapes": txt_shapes,
                "sample_texts": sample_texts,
            }
        )

    all_xml_typefaces: set[str] = set()
    with zipfile.ZipFile(str(pptx_path), "r") as zf:
        for name in zf.namelist():
            if name.endswith(".xml"):
                txt = zf.read(name).decode("utf-8", errors="ignore")
                all_xml_typefaces.update(re.findall(r'typeface="([^"]*)"', txt))

    font_violations: List[str] = []
    if require_font is not None:
        font_violations = sorted(tf for tf in all_xml_typefaces if tf != require_font)

    passed = (
        len(prs.slides) > 0
        and len(trns_black_violations) == 0
        and len(sparse_text_slides) == 0
        and len(font_violations) == 0
    )

    return {
        "pptx_path": str(pptx_path),
        "passed": passed,
        "slide_count": len(prs.slides),
        "total_pictures": total_pictures,
        "total_editable_text_shapes": total_text_shapes,
        "all_xml_typefaces": sorted(all_xml_typefaces),
        "font_violations": font_violations,
        "trns_black_violations": trns_black_violations,
        "sparse_text_slides": sparse_text_slides,
        "slides": slide_reports,
    }


# ---------------------------------------------------------------------------
# 7. Windows PowerPoint COM Slide Exporter for Visual QA
# ---------------------------------------------------------------------------

def export_pptx_slides_via_com(
    pptx_path: Union[str, Path],
    out_dir: Union[str, Path],
    width_px: int = 1920,
    height_px: int = 1080,
) -> List[Path]:
    """
    Export all slides of ``pptx_path`` to PNG images in ``out_dir`` using Windows
    PowerPoint COM automation.
    """
    pptx_abs = str(Path(pptx_path).resolve())
    out_path = Path(out_dir).resolve()
    out_path.mkdir(parents=True, exist_ok=True)

    ps_script = f"""
$ErrorActionPreference = 'Stop'
$ppt = New-Object -ComObject PowerPoint.Application
$pres = $ppt.Presentations.Open('{pptx_abs}', $true, $false, $false)
try {{
    $i = 1
    foreach ($slide in $pres.Slides) {{
        $outPng = Join-Path '{str(out_path)}' ("slide_{{0:D2}}.png" -f $i)
        $slide.Export($outPng, 'PNG', {int(width_px)}, {int(height_px)})
        $i++
    }}
}} finally {{
    $pres.Close()
}}
"""
    subprocess.run(
        ["powershell", "-NoProfile", "-Command", ps_script],
        check=True,
    )
    return sorted(out_path.glob("slide_*.png"))


# ---------------------------------------------------------------------------
# 8. Command-Line Interface
# ---------------------------------------------------------------------------

def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="AWF FigPPT toolkit: build, scan, export, and audit editable scientific figure PPTX decks."
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_audit = sub.add_parser("audit", help="Audit a .pptx file for native text editability and PNG transparency bugs.")
    p_audit.add_argument("pptx", help="Path to .pptx file")
    p_audit.add_argument("--min-text-shapes", type=int, default=2, help="Minimum editable text shapes per slide")
    p_audit.add_argument("--require-font", type=str, default=None, help="Require 100% of XML typeface attributes to match this font (e.g. Arial)")

    p_scan = sub.add_parser("scan-margins", help="Scan outward ink margins around a 2D plot box.")
    p_scan.add_argument("image", help="Path to source figure PNG")
    p_scan.add_argument("--box", nargs=4, type=int, required=True, metavar=("BX0", "BY0", "BX1", "BY1"))

    p_export = sub.add_parser("export-png", help="Export slides of a .pptx to PNG via Windows PowerPoint COM.")
    p_export.add_argument("pptx", help="Path to .pptx file")
    p_export.add_argument("--out-dir", required=True, help="Output directory for slide_XX.png files")
    p_export.add_argument("--width", type=int, default=1920)
    p_export.add_argument("--height", type=int, default=1080)

    args = parser.parse_args(argv)

    if args.cmd == "audit":
        report = audit_pptx_editable_shapes(
            args.pptx,
            min_text_shapes_per_slide=args.min_text_shapes,
            require_font=args.require_font,
        )
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0 if report["passed"] else 1

    if args.cmd == "scan-margins":
        im = load_clean_rgb(args.image)
        res = scan_plot_box_and_ink_gaps(im, tuple(args.box))
        print(json.dumps(res.to_dict(), indent=2))
        return 0

    if args.cmd == "export-png":
        exported = export_pptx_slides_via_com(args.pptx, args.out_dir, width_px=args.width, height_px=args.height)
        print(json.dumps({"exported_count": len(exported), "files": [str(p) for p in exported]}, indent=2))
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
