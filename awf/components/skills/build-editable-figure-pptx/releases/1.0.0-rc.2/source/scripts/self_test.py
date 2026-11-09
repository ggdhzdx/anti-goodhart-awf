#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Automated self-test suite for skill.build-editable-figure-pptx@1.0.0-rc.1.
Tests both positive (clean RGB loading, affine coordinate bridge, OpenXML sub/superscripts,
Mode A & Mode B plot builders) and negative cases (palette PNG tRNS black transparency bug
and sparse text slide detection).
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from pptx import Presentation
from pptx.util import Inches

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from editable_figure_pptx_kit import (
    DataToPptBridge,
    add_ppt_badge,
    add_ppt_text,
    add_ppt_vector_legend,
    audit_pptx_editable_shapes,
    load_clean_rgb,
    place_plot_with_draggable_titles,
    place_relabelled_2d_plot_on_slide,
    save_presentation_with_uniform_font,
    scan_plot_box_and_ink_gaps,
)


def _make_synthetic_paletted_plot(path: Path) -> Path:
    """Create an 8-bit paletted PNG with a plot box, tick bands, outer titles, and transparency index."""
    im = Image.new("RGB", (600, 450), (255, 255, 255))
    draw = ImageDraw.Draw(im)
    # Plot box (120, 60, 520, 340)
    draw.rectangle([120, 60, 520, 340], outline=(0, 0, 0), width=2)
    # Simulated tick numbers left of bx0=120 (x=88..112)
    draw.rectangle([90, 100, 112, 112], fill=(0, 0, 0))
    draw.rectangle([90, 200, 112, 212], fill=(0, 0, 0))
    # White gap x=65..89, then rotated Y-axis title at x=35..58
    draw.rectangle([38, 120, 55, 280], fill=(0, 0, 0))
    # Simulated X-tick numbers below by1=340 (y=346..362)
    draw.rectangle([180, 348, 210, 360], fill=(0, 0, 0))
    draw.rectangle([380, 348, 410, 360], fill=(0, 0, 0))
    # White gap y=361..379, then X-axis title at y=382..402
    draw.rectangle([240, 384, 400, 400], fill=(0, 0, 0))

    p_im = im.convert("P")
    # Attach palette transparency index that maps to (0, 0, 0) when naively converted to RGB
    pal = p_im.getpalette()
    black_idx = 0
    for i in range(256):
        if pal[3 * i : 3 * i + 3] == [0, 0, 0]:
            black_idx = i
            break
    p_im.save(path, transparency=black_idx)
    return path


def run_tests() -> dict:
    results = {}
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        src_png = _make_synthetic_paletted_plot(tmp_dir / "paletted_plot.png")

        # 1. Verify negative case: naive .convert("RGB") retains transparency=(0, 0, 0)
        naive_rgb = Image.open(src_png).convert("RGB")
        naive_crop = tmp_dir / "naive_crop.png"
        naive_rgb.save(naive_crop)
        reloaded_naive = Image.open(naive_crop)
        assert reloaded_naive.info.get("transparency") == (0, 0, 0), (
            f"Expected naive convert('RGB') to carry transparency=(0,0,0), got {reloaded_naive.info}"
        )
        results["negative_naive_rgb_trns_detected"] = True

        # 2. Verify positive case: load_clean_rgb strips transparency completely
        clean_rgb = load_clean_rgb(src_png)
        assert clean_rgb.info.get("transparency") is None, "load_clean_rgb must strip transparency"
        clean_crop = tmp_dir / "clean_crop.png"
        clean_rgb.save(clean_crop)
        reloaded_clean = Image.open(clean_crop)
        assert reloaded_clean.info.get("transparency") is None
        results["positive_load_clean_rgb"] = True

        # 3. Verify scan_plot_box_and_ink_gaps finds the white gap between ticks and outer titles
        margins = scan_plot_box_and_ink_gaps(clean_rgb, (120, 60, 520, 340))
        assert 30 <= margins.left_tick_pad_px <= 55, f"Unexpected left_tick_pad_px: {margins.left_tick_pad_px}"
        assert 20 <= margins.bottom_tick_pad_px <= 40, f"Unexpected bottom_tick_pad_px: {margins.bottom_tick_pad_px}"
        results["scan_plot_box_and_ink_gaps"] = margins.to_dict()

        # 4. Verify DataToPptBridge affine coordinate accuracy
        bridge = DataToPptBridge.from_crop_in_box(
            crop_rect=(60, 40, 540, 380),
            target_box_in=(1.0, 1.0, 9.6, 5.0),
            plot_box_px=(120, 60, 520, 340),
            x_range=(1.0, 4.0),
            y_range=(0.0, 100.0),
        )
        bx0_in, by0_in, bx1_in, by1_in = bridge.plot_edges_in()
        assert abs(bridge.x_to_ppt(1.0) - bx0_in) < 1e-6
        assert abs(bridge.x_to_ppt(4.0) - bx1_in) < 1e-6
        assert abs(bridge.y_to_ppt(0.0) - by1_in) < 1e-6
        assert abs(bridge.y_to_ppt(100.0) - by0_in) < 1e-6
        results["affine_bridge_exact"] = True

        # 5. Build a positive PPTX deck (Mode B + Mode A + OpenXML sub/superscripts) and audit it
        prs = Presentation()
        prs.slide_width = Inches(13.333)
        prs.slide_height = Inches(7.5)
        blank = prs.slide_layouts[6]

        # Slide 1: Mode B
        s1 = prs.slides.add_slide(blank)
        add_ppt_badge(s1, 0.35, 0.22, 0.55, 0.42, "1a")
        add_ppt_text(s1, 1.0, 0.22, 10.0, 0.42, "Mode B: Draggable Titles with Intact Tick Numbers", font_size=16, bold=True)
        place_plot_with_draggable_titles(
            s1,
            clean_rgb,
            plot_box=(120, 60, 520, 340),
            target_box_in=(1.2, 1.1, 10.5, 5.4),
            crop_out_path=tmp_dir / "mode_b_crop.png",
            xlabel="Potential vs. Na^{+}/Na (V)",
            ylabel="Current Density (mA g^{-1})",
            title="Cyclic Voltammetry of Na_{3}TPA-PQ",
            pad_ticks=(margins.left_tick_pad_px, 14, 18, margins.bottom_tick_pad_px),
            extra_erase_rects=[margins.left_title_erase_rect, margins.bottom_title_erase_rect],
        )

        # Slide 2: Mode A
        s2 = prs.slides.add_slide(blank)
        add_ppt_badge(s2, 0.35, 0.22, 0.55, 0.42, "1b")
        add_ppt_text(s2, 1.0, 0.22, 10.0, 0.42, "Mode A: Full Native Tick & Axis Replacement", font_size=16, bold=True)
        place_relabelled_2d_plot_on_slide(
            s2,
            clean_rgb,
            plot_box=(120, 60, 520, 340),
            target_box_in=(1.4, 1.1, 10.2, 5.2),
            crop_out_path=tmp_dir / "mode_a_crop.png",
            x_range=(1.0, 4.0),
            y_range=(0.0, 100.0),
            xticks=[(1.0, "1.0"), (2.0, "2.0"), (3.0, "3.0"), (4.0, "4.0")],
            yticks=[(0.0, "0"), (50.0, "50"), (100.0, "100")],
            xlabel="Voltage (V vs. Na^{+}/Na)",
            ylabel="Capacity (mAh g^{-1})",
            title="Galvanostatic Charge/Discharge",
        )

        add_ppt_vector_legend(
            s2, 8.5, 1.3, 2.2, 0.55,
            items=[("CD-NF (Parallel)", (26, 111, 223)), ("CD-NC (Wedge)", (241, 64, 64))],
            marker_kind="circle",
            layout="vertical",
        )

        good_pptx = tmp_dir / "good_deck.pptx"
        save_presentation_with_uniform_font(prs, good_pptx, font_name="Arial")
        audit_good = audit_pptx_editable_shapes(good_pptx, min_text_shapes_per_slide=4, require_font="Arial")
        assert audit_good["passed"] is True, f"Expected good_deck to pass audit: {audit_good}"
        assert audit_good["all_xml_typefaces"] == ["Arial"], f"Expected only Arial, got {audit_good['all_xml_typefaces']}"
        results["positive_pptx_audit"] = {
            "passed": audit_good["passed"],
            "slide_count": audit_good["slide_count"],
            "total_editable_text_shapes": audit_good["total_editable_text_shapes"],
            "all_xml_typefaces": audit_good["all_xml_typefaces"],
        }

        # 6. Build a negative PPTX deck with naive tRNS black transparency and verify audit catches it
        bad_prs = Presentation()
        bs1 = bad_prs.slides.add_slide(bad_prs.slide_layouts[6])
        bs1.shapes.add_picture(str(naive_crop), Inches(1), Inches(1), Inches(4), Inches(3))
        bad_pptx = tmp_dir / "bad_deck.pptx"
        bad_prs.save(str(bad_pptx))
        audit_bad = audit_pptx_editable_shapes(bad_pptx, min_text_shapes_per_slide=2)
        assert audit_bad["passed"] is False, "Expected bad_deck to fail audit"
        assert len(audit_bad["trns_black_violations"]) == 1, "Expected tRNS black violation to be caught"
        assert audit_bad["sparse_text_slides"] == [1], "Expected sparse text slide to be caught"
        results["negative_pptx_audit_caught"] = True

    return results


if __name__ == "__main__":
    res = run_tests()
    print(json.dumps({"status": "PASS", "tests": res}, indent=2))
