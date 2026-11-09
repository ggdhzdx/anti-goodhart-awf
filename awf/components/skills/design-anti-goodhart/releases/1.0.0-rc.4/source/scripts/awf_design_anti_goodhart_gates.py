#!/usr/bin/env python3
"""
AWF DesignAG: Visual, Pedagogical & Slide-Deck Anti-Goodhart Verification Engine
(`skill.design-anti-goodhart@1.0.0-rc.2`).

Implements 18 Automated Design Anti-Goodhart Gates (D1-D18) across 4 Pillars,
strictly enforcing 1-Slide-Per-Step Micro-Step Anchoring (`MAX_MICROSTEP_BATCH_SLIDES = 1`)
+ 1-Hop Slide Topological Lock (`unverified_slide_hop_distance == 1`), Escape-to-Gate
Darwinian Regression Evolution, and the Dual-Rubric Quantitative Scorer:
  1. Optoelectronic / Scientific Literature HTML-PPT Rubric v3 (100 pts + R1..R7 up to -15 pts)
  2. Supermolecule / Pedagogical 5-Dimension Rubric (100 pts: 25 + 20 + 20 + 20 + 15)
Collaborates with Layer-1 `skill.anti-goodhart-verification@3.4.0-rc.1` (`AWF Guard`).
"""

from __future__ import annotations

import argparse
import html.parser
import json
import math
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np

# Named physical/geometric/optical threshold constants (zero magic numbers for G5n)
CANVAS_DEFAULT_WIDTH = 1920.0
CANVAS_DEFAULT_HEIGHT = 1080.0
MAX_SIBLING_IOU_TOL = 0.005
SCROLL_OVERFLOW_PX_TOL = 2.0
MIN_COVERAGE_RATIO = 0.35
MAX_COVERAGE_RATIO = 0.80
COM_MIN_RATIO = 0.35
COM_MAX_RATIO = 0.65
WIDE_BANNER_AR_THRESHOLD = 1.85
NARROW_SLOT_AR_LIMIT = 1.15
MIN_SLOT_UTILIZATION_RATIO = 0.55
MIN_MULTIROW_SLOT_HEIGHT_PX = 480.0
MAX_SUBPANELS_PER_SLIDE = 2
MAX_BLANK_MARGIN_RATIO = 0.18
MAX_BORDER_SLICED_INK_RATIO = 0.025
WCAG_BODY_CONTRAST_MIN = 4.5
WCAG_TITLE_CONTRAST_MIN = 3.0
MIN_BODY_FONT_PX = 16.0
MAX_FILLER_SLIDE_RATIO = 0.22
MIN_FULL_DECK_SLIDES = 15
MAX_MICROSTEP_BATCH_SLIDES = 1
MAX_CONSECUTIVE_SAME_LAYOUT = 2
MIN_LAYOUT_SHANNON_ENTROPY = 1.4
MAX_REDLINE_DEDUCTION = 15.0

CLARITY_COEFF_MAP: Dict[str, float] = {
    "S": 1.0,
    "A": 0.75,
    "B": 0.50,
    "C": 0.25,
    "D": 0.0,
}

VISUAL_MODALITY_COEFF_MAP: Dict[str, float] = {
    "V0": 0.30,
    "V1": 0.50,
    "V2": 0.80,
    "V3": 1.00,
}

GRADE_TO_RATIO_MAP: Dict[str, float] = {
    "S": 1.0,
    "A": 0.75,
    "B": 0.50,
    "C": 0.25,
    "D": 0.0,
}

VOID_HTML_ELEMENTS = frozenset({
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
})

BANNED_CARTOON_EMOJIS = (
    "🐢", "🪞", "🗂️", "🧱", "🌀", "💠", "🔲", "⬜", "🤡", "💩", "🎉",
)

WECHAT_CLICHE_PATTERNS = (
    r"[一二三四五六七八九十\d]+个问题[，,\s]*看懂",
    r"[一二三四五六七八九十\d]+个要点[，,\s]*带走",
    r"破局思路[：:]",
    r"寿命杀手[：:]",
    r"效率的巅峰[，,].*的短板",
    r"边界与下一步[：:]",
)

AI_META_PREACHY_PATTERNS = (
    r"先说比较对象[，,\s]*再说提升倍数",
    r"先对齐输出负荷与颜色[，,\s]*再判断",
    r"组会追问[：:]\s*先说清参照",
    r"复述这篇论文[，,\s]*只需抓住",
    r"本汇报复述原论文结果",
    r"不将[‘'“\"]?最长寿命[’'”\"]?延伸为",
    r"以下是基于本文提出的讨论方案",
    r"属于作者发表时的结果",
    r"教学计算[，,\s]*不是实验拟合",
)

PROMPT_RESIDUE_PATTERNS = (
    r"\b\d{1,2}\s*页实验原理",
    r"高中生也能看懂的第\s*\d+\s*页",
    r"\b\d{1,2}\s*页的\s*LT\d+",
    r"按照您的要求生成第\s*\d+\s*页",
)

RAW_LATEX_PATTERNS = (
    r"\\frac\s*\{",
    r"\\text\s*\{",
    r"\\tau\b",
    r"\\mu\b",
    r"\\propto\b",
    r"\\Omega\b",
    r"\\sqrt\s*\{",
    r"\\approx\b",
    r"\$[^\$]{1,80}\$",
)


def _num_or(mapping: Dict[str, Any], key: str, fallback: float) -> float:
    """Explicit numeric lookup helper avoiding silent `.get(k, literal)` AST anti-patterns."""
    return float(mapping[key]) if key in mapping and mapping[key] is not None else fallback


def _int_or(mapping: Dict[str, Any], key: str, fallback: int) -> int:
    """Explicit integer lookup helper avoiding silent `.get(k, literal)` AST anti-patterns."""
    return int(mapping[key]) if key in mapping and mapping[key] is not None else fallback


def _strip_invisible_html_blocks(html_text: str) -> str:
    """Remove <script>, <style>, and speaker notes blocks to isolate visible DOM markup."""
    cleaned = re.sub(r"<script\b[^>]*>.*?</script>", " ", html_text, flags=re.DOTALL | re.IGNORECASE)
    cleaned = re.sub(r"<style\b[^>]*>.*?</style>", " ", cleaned, flags=re.DOTALL | re.IGNORECASE)
    cleaned = re.sub(
        r"<(?:aside|div)\b[^>]*class=[\"'][^\"']*\bnotes(?:-source)?\b[^\"']*[\"'][^>]*>.*?</(?:aside|div)>",
        " ",
        cleaned,
        flags=re.DOTALL | re.IGNORECASE,
    )
    return cleaned


def _extract_visible_plain_text(html_text: str) -> str:
    """Extract visible plain text from HTML after stripping scripts, styles, and speaker notes."""
    visible_html = _strip_invisible_html_blocks(html_text)
    plain = re.sub(r"<[^>]+>", " ", visible_html)
    return re.sub(r"\s+", " ", plain).strip()


# ============================================================================
# Pillar I: Static HTML/DOM/CSS, Copywriting & Acronym -inf Circuit-Breakers
# ============================================================================

def scan_html_for_unrendered_latex_leak(html_text: str) -> Dict[str, Any]:
    """
    Gate D1 (Redline R1): Detect unrendered raw LaTeX source code in visible slide content.
    Checks whether raw LaTeX commands (`\\frac`, `\\text{`, `$...$`) appear in visible text
    without a MathJax or KaTeX rendering engine loaded in `<head>`.
    """
    has_math_engine = bool(
        re.search(r"(?:katex|mathjax|auto-render)", html_text, flags=re.IGNORECASE)
    )
    visible_text = _extract_visible_plain_text(html_text)
    leaked_tokens: List[str] = []
    for pat in RAW_LATEX_PATTERNS:
        matches = re.findall(pat, visible_text)
        if matches:
            if not has_math_engine or pat in (r"\\frac\s*\{", r"\\text\s*\{"):
                for m in matches[:5]:
                    leaked_tokens.append(str(m))
    passed = len(leaked_tokens) == 0
    return {
        "gate": "D1_Zero_Unrendered_LaTeX_Source_Leak",
        "passed": passed,
        "has_math_engine": has_math_engine,
        "leaked_token_count": len(leaked_tokens),
        "leaked_samples": leaked_tokens[:8],
        "redline_r1_triggered": not passed,
        "redline_deduction": -5.0 if not passed else 0.0,
        "effective_reward": 1.0 if passed else float("-inf"),
    }


class _StrictTagBalanceParser(html.parser.HTMLParser):
    """Stack-based HTML tag balance checker to catch `<div>...</p></div>` card collapse."""

    def __init__(self) -> None:
        super().__init__()
        self.stack: List[Tuple[str, int]] = []
        self.mismatches: List[str] = []

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        t = tag.lower()
        if t not in VOID_HTML_ELEMENTS:
            lineno, _ = self.getpos()
            self.stack.append((t, lineno))

    def handle_endtag(self, tag: str) -> None:
        t = tag.lower()
        if t in VOID_HTML_ELEMENTS:
            return
        lineno, _ = self.getpos()
        if not self.stack:
            self.mismatches.append(f"Unexpected closing </{t}> at line {lineno} with empty stack")
            return
        top_tag, top_line = self.stack[-1]
        if top_tag == t:
            self.stack.pop()
        else:
            self.mismatches.append(
                f"Mismatched closing </{t}> at line {lineno} for open <{top_tag}> (line {top_line})"
            )
            for idx in range(len(self.stack) - 1, -1, -1):
                if self.stack[idx][0] == t:
                    del self.stack[idx:]
                    break


def audit_html_tag_balance_and_grid_orphans(
    html_text: str,
    grid_specs: Optional[Sequence[Dict[str, int]]] = None,
) -> Dict[str, Any]:
    """
    Gate D2 (Redline R2 & Supermolecule 1): Catch HTML tag closing mismatches (e.g.,
    `<div class="big-num">因</p></div>` in `ppt-kimi-k3` slide 5) and `3+1` grid orphan rows.
    """
    parser = _StrictTagBalanceParser()
    parser.feed(html_text)
    mismatches = list(parser.mismatches)
    for unclosed_tag, line in parser.stack:
        if unclosed_tag not in ("html", "body", "head"):
            mismatches.append(f"Unclosed <{unclosed_tag}> opened at line {line}")

    orphan_grids: List[str] = []
    for spec in grid_specs or []:
        cols = _int_or(spec, "columns", 3)
        items = _int_or(spec, "item_count", 0)
        slide_no = _int_or(spec, "slide", 0)
        if cols >= 3 and items > cols and (items % cols) == 1:
            orphan_grids.append(
                f"Slide {slide_no}: {items} items in {cols}-column grid creates '{cols}+1' orphan row"
            )

    passed = len(mismatches) == 0 and len(orphan_grids) == 0
    return {
        "gate": "D2_HTML_Tag_Balance_And_Grid_Orphan_Guard",
        "passed": passed,
        "tag_mismatches": mismatches,
        "orphan_grids": orphan_grids,
        "redline_r2_triggered": len(mismatches) > 0,
    }


def audit_copywriting_naturalness_and_ai_tone(
    slides: Sequence[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Gate D3 (Rubric C1 & Redline R5): Detect WeChat marketing clichés, overused corner-quote
    metaphors (`「抽走」「烧坏」`), preachy AI meta-instructional/disclaimer tone (`先说比较对象，再说提升倍数`),
    subjectless numeric titles (`140 小时与 10–14 倍，来自归一化比较`), and prompt residue (`13页实验原理`).
    """
    cliche_hits: List[str] = []
    meta_tone_hits: List[str] = []
    prompt_residue_hits: List[str] = []
    subjectless_titles: List[str] = []
    corner_quote_count = 0

    for idx, slide in enumerate(slides, start=1):
        title = str(slide.get("title", "")).strip()
        subtitle = str(slide.get("subtitle", "")).strip()
        body = str(slide.get("body", "")).strip()
        combined = f"{title} {subtitle} {body}"

        corner_quotes = re.findall(r"「[^」]{1,8}」", combined)
        corner_quote_count += len(corner_quotes)

        for pat in WECHAT_CLICHE_PATTERNS:
            if re.search(pat, combined):
                cliche_hits.append(f"Slide {idx}: matches cliché '{pat}' in '{title}'")
        for pat in AI_META_PREACHY_PATTERNS:
            if re.search(pat, combined):
                meta_tone_hits.append(f"Slide {idx}: AI meta/disclaimer tone matching '{pat}'")
        for pat in PROMPT_RESIDUE_PATTERNS:
            if re.search(pat, combined):
                prompt_residue_hits.append(f"Slide {idx}: prompt residue matching '{pat}'")

        if re.match(r"^\d+(?:\.\d+)?\s*(?:小时|h|倍|×|nm|%)\s*(?:与|和|及)\s*\d+", title):
            subjectless_titles.append(f"Slide {idx}: subjectless numeric title '{title}'")

    excessive_quotes = corner_quote_count >= 4
    passed = (
        len(cliche_hits) == 0
        and len(meta_tone_hits) == 0
        and len(prompt_residue_hits) == 0
        and len(subjectless_titles) == 0
        and not excessive_quotes
    )
    return {
        "gate": "D3_Natural_Academic_Copywriting_No_AI_MetaTone",
        "passed": passed,
        "corner_quote_count": corner_quote_count,
        "excessive_corner_quotes": excessive_quotes,
        "cliche_hits": cliche_hits,
        "meta_tone_hits": meta_tone_hits,
        "prompt_residue_hits": prompt_residue_hits,
        "subjectless_titles": subjectless_titles,
        "redline_r5_count": len(prompt_residue_hits),
    }


def audit_acronym_definitions_and_popovers(
    slides: Sequence[Dict[str, Any]],
    required_acronyms: Sequence[str] = ("PHOLED", "TPA", "TTA", "LT90", "PF", "ODoS", "SPP", "PEP"),
) -> Dict[str, Any]:
    """
    Gate D4 (Rubric C2): Enforce 'Define-Before-Use on Visible Canvas' and inline click popovers.
    Catches acronyms hidden in speaker notes (`<aside class="notes">`) that later appear undefined
    on visible slides (`ppt-astra-6` TPA/TTA & `ppt-deepseek` LT90), and flags standalone glossary walls.
    """
    first_visible_use: Dict[str, int] = {}
    first_visible_def: Dict[str, int] = {}
    notes_only_defs: List[str] = []
    glossary_wall_slides: List[int] = []
    inline_popover_count = 0

    for idx, slide in enumerate(slides, start=1):
        vis = str(slide.get("visible_text", ""))
        notes = str(slide.get("notes_text", ""))
        defined_here = set(slide.get("defined_terms_visible", []))
        defined_in_notes = set(slide.get("defined_terms_notes", []))
        inline_popover_count += _int_or(slide, "inline_popover_count", 0)
        if bool(slide.get("is_glossary_wall", False)):
            glossary_wall_slides.append(idx)

        for term in required_acronyms:
            if re.search(rf"\b{re.escape(term)}\b", vis):
                first_visible_use.setdefault(term, idx)
            if term in defined_here or re.search(rf"\b{re.escape(term)}\s*(?:（|\(|=|：|:|即|指)", vis):
                first_visible_def.setdefault(term, idx)
            elif term in defined_in_notes or re.search(rf"\b{re.escape(term)}\s*(?:（|\(|=|：|:|即|指)", notes):
                if term not in first_visible_def:
                    notes_only_defs.append(f"{term} (hidden in Slide {idx} notes)")

    premature_uses: List[str] = []
    missing_visible_defs: List[str] = []
    for term, use_idx in first_visible_use.items():
        def_idx = first_visible_def.get(term)
        if def_idx is None:
            missing_visible_defs.append(f"{term} used on Slide {use_idx} but never defined on visible canvas")
        elif def_idx > use_idx:
            premature_uses.append(f"{term} used on Slide {use_idx} before visible definition on Slide {def_idx}")

    passed = (
        len(missing_visible_defs) == 0
        and len(premature_uses) == 0
        and len(glossary_wall_slides) == 0
    )
    return {
        "gate": "D4_Acronym_FirstUse_Visible_Definition_And_Popover_Guard",
        "passed": passed,
        "missing_visible_defs": missing_visible_defs,
        "premature_uses": premature_uses,
        "notes_only_defs": notes_only_defs,
        "glossary_wall_slides": glossary_wall_slides,
        "inline_popover_count": inline_popover_count,
    }


def audit_emojis_fake_bars_and_watermarks(
    html_text: str,
    figure_metadata: Optional[Sequence[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Gate D5 (Rubric D2, B4 & Redline R4): Block cartoon Emojis (`🐢🪞🗂️🧱`), subjective fake
    percentage progress bars masquerading as experimental data, AI sci-fi decorative wallpapers
    masquerading as mechanism diagrams (`R4`), and residual AI generation watermarks.
    """
    visible_text = _extract_visible_plain_text(html_text)
    found_emojis = [e for e in BANNED_CARTOON_EMOJIS if e in visible_text]
    fake_progress_bars = re.findall(
        r"\b(?:100|78|56|32)%\s*(?:最强|强|中|弱)\b", visible_text
    )
    ai_watermarks = re.findall(r"(?:AI\s*生成|豆包\s*AI|Midjourney|DALL·E)", visible_text, flags=re.IGNORECASE)

    ai_deco_figures: List[str] = []
    for fig in figure_metadata or []:
        if bool(fig.get("is_ai_decorative_wallpaper", False)) and bool(fig.get("claimed_as_mechanism_diagram", False)):
            ai_deco_figures.append(str(fig.get("src", "unknown_ai_fig")))
        if bool(fig.get("has_ai_watermark", False)):
            ai_watermarks.append(str(fig.get("src", "watermarked_fig")))

    passed = (
        len(found_emojis) == 0
        and len(fake_progress_bars) == 0
        and len(ai_deco_figures) == 0
        and len(ai_watermarks) == 0
    )
    return {
        "gate": "D5_Anti_Emoji_FakeProgressBar_And_AIWatermark_Guard",
        "passed": passed,
        "found_cartoon_emojis": found_emojis,
        "fake_progress_bars": fake_progress_bars,
        "ai_decorative_mechanism_fakes": ai_deco_figures,
        "ai_watermarks": ai_watermarks,
        "redline_r4_count": len(ai_deco_figures),
    }


def audit_teleprompter_and_slide_density(
    deck_spec: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Gate D6 (Redline R6 & Rubric C3): Block always-visible teleprompter panels (`#teleprompter-panel`),
    `.slide { overflow-y: auto }` vertical scrollbar text walls, micro-fonts (<16px), extreme 12-slide
    compression, and >22% filler transition slides (`ppt-glm-5.3`).
    """
    teleprompter_visible = bool(deck_spec.get("teleprompter_default_visible", False))
    slide_scrollbars = _int_or(deck_spec, "slides_with_vertical_scrollbar", 0)
    min_body_font_px = _num_or(deck_spec, "min_body_font_px", 18.0)
    total_slides = _int_or(deck_spec, "total_slides", 20)
    filler_slides = _int_or(deck_spec, "filler_transition_slides", 2)
    is_full_paper_deck = bool(deck_spec.get("is_full_paper_deck", True))

    filler_ratio = filler_slides / max(1, total_slides)
    issues: List[str] = []
    if teleprompter_visible:
        issues.append("Redline R6: Teleprompter/speaker-notes panel is visible by default on screen")
    if slide_scrollbars > 0:
        issues.append(f"{slide_scrollbars} slide(s) require vertical scrollbar (overflow-y: auto text wall)")
    if min_body_font_px < MIN_BODY_FONT_PX:
        issues.append(f"Minimum body font size {min_body_font_px:.1f}px < {MIN_BODY_FONT_PX:.1f}px floor")
    if is_full_paper_deck and total_slides < MIN_FULL_DECK_SLIDES:
        issues.append(f"Total slides ({total_slides}) < {MIN_FULL_DECK_SLIDES} causes severe single-slide overload")
    if filler_ratio > MAX_FILLER_SLIDE_RATIO:
        issues.append(f"Filler/divider slide ratio {filler_ratio:.1%} > {MAX_FILLER_SLIDE_RATIO:.1%} cap")

    passed = len(issues) == 0
    return {
        "gate": "D6_Teleprompter_Hidden_And_Slide_Density_Cadence_Guard",
        "passed": passed,
        "teleprompter_default_visible": teleprompter_visible,
        "slide_scrollbars": slide_scrollbars,
        "min_body_font_px": min_body_font_px,
        "total_slides": total_slides,
        "filler_ratio": round(filler_ratio, 4),
        "redline_r6_triggered": teleprompter_visible,
        "issues": issues,
    }


# ============================================================================
# Pillar II: Geometric, Optical, Aspect-Ratio & Sub-Panel Cropping Probes
# ============================================================================

def verify_bounding_boxes_zero_overlap_and_clipping(
    boxes: Sequence[Dict[str, Any]],
    canvas_w: float = CANVAS_DEFAULT_WIDTH,
    canvas_h: float = CANVAS_DEFAULT_HEIGHT,
) -> Dict[str, Any]:
    """
    Gate D7 (Redline R2 & Supermolecule 1): Verify pairwise sibling bounding-box IoU == 0
    and strict containment inside the 1920x1080 canvas with zero internal scroll clipping.
    """
    overlaps: List[str] = []
    clipped: List[str] = []
    n = len(boxes)

    for i in range(n):
        b1 = boxes[i]
        id1 = str(b1.get("id", f"box_{i}"))
        x1, y1 = float(b1["x"]), float(b1["y"])
        w1, h1 = float(b1["w"]), float(b1["h"])
        if x1 < -1.0 or y1 < -1.0 or (x1 + w1) > (canvas_w + 1.0) or (y1 + h1) > (canvas_h + 1.0):
            clipped.append(f"{id1} exceeds canvas ({x1:.1f},{y1:.1f},{w1:.1f},{h1:.1f})")
        scroll_h = float(b1.get("scroll_h", h1))
        client_h = float(b1.get("client_h", h1))
        if scroll_h > client_h + SCROLL_OVERFLOW_PX_TOL:
            clipped.append(f"{id1} internal text clipped (scroll_h={scroll_h:.1f} > client_h={client_h:.1f})")

        for j in range(i + 1, n):
            b2 = boxes[j]
            if b1.get("parent_id") != b2.get("parent_id"):
                continue
            id2 = str(b2.get("id", f"box_{j}"))
            x2, y2 = float(b2["x"]), float(b2["y"])
            w2, h2 = float(b2["w"]), float(b2["h"])
            ix = max(0.0, min(x1 + w1, x2 + w2) - max(x1, x2))
            iy = max(0.0, min(y1 + h1, y2 + h2) - max(y1, y2))
            inter = ix * iy
            union = max(1e-9, w1 * h1 + w2 * h2 - inter)
            iou = inter / union
            if iou > MAX_SIBLING_IOU_TOL:
                overlaps.append(f"{id1} overlaps {id2} (IoU={iou:.4f})")

    passed = len(overlaps) == 0 and len(clipped) == 0
    return {
        "gate": "D7_BoundingBox_ZeroOverlap_And_ZeroClipping_Probe",
        "passed": passed,
        "overlaps": overlaps,
        "clipped_elements": clipped,
        "redline_r2_triggered": not passed,
    }


def verify_canvas_whitespace_and_center_of_mass(
    boxes: Sequence[Dict[str, Any]],
    canvas_w: float = CANVAS_DEFAULT_WIDTH,
    canvas_h: float = CANVAS_DEFAULT_HEIGHT,
) -> Dict[str, Any]:
    """
    Gate D8 (Supermolecule 1): Verify slide active coverage ratio in [0.35, 0.80]
    and vertical center of mass in [0.35, 0.65] (rejecting top-cramped/bottom-empty slides).
    """
    if not boxes:
        return {
            "gate": "D8_Canvas_Whitespace_And_Vertical_CenterOfMass_Balance",
            "passed": False,
            "reason": "Empty slide with zero bounding boxes",
        }
    total_area = 0.0
    weighted_x = 0.0
    weighted_y = 0.0
    for b in boxes:
        x, y = float(b["x"]), float(b["y"])
        w, h = float(b["w"]), float(b["h"])
        area = max(0.0, w * h)
        total_area += area
        weighted_x += area * (x + 0.5 * w)
        weighted_y += area * (y + 0.5 * h)

    canvas_area = max(1.0, canvas_w * canvas_h)
    coverage = total_area / canvas_area
    x_cm_norm = (weighted_x / max(1.0, total_area)) / canvas_w
    y_cm_norm = (weighted_y / max(1.0, total_area)) / canvas_h

    coverage_ok = MIN_COVERAGE_RATIO <= coverage <= MAX_COVERAGE_RATIO
    com_ok = (COM_MIN_RATIO <= x_cm_norm <= COM_MAX_RATIO) and (COM_MIN_RATIO <= y_cm_norm <= COM_MAX_RATIO)
    passed = coverage_ok and com_ok
    return {
        "gate": "D8_Canvas_Whitespace_And_Vertical_CenterOfMass_Balance",
        "passed": passed,
        "coverage_ratio": round(coverage, 4),
        "whitespace_ratio": round(1.0 - coverage, 4),
        "x_cm_norm": round(x_cm_norm, 4),
        "y_cm_norm": round(y_cm_norm, 4),
        "coverage_ok": coverage_ok,
        "center_of_mass_ok": com_ok,
    }


def verify_image_aspect_ratio_and_slot_utilization(
    placements: Sequence[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Gate D9 (Rubric D1): Catch wide banner figures (`AR >= 1.85`, e.g. `fig1.jpg` 2.55:1)
    stuffed into narrow vertical split columns (`qwen-3.8` slides 8 & 11) or multi-row
    figures crushed into short `<480px` slots (`qwen-3.8` slides 9 & 13).
    """
    violations: List[str] = []
    for p in placements:
        fig_id = str(p.get("id", "fig"))
        img_w = float(p["img_w"])
        img_h = float(p["img_h"])
        slot_w = float(p["slot_w"])
        slot_h = float(p["slot_h"])
        panel_rows = _int_or(p, "panel_rows", 1)

        img_ar = img_w / max(1.0, img_h)
        slot_ar = slot_w / max(1.0, slot_h)
        scale = min(slot_w / max(1.0, img_w), slot_h / max(1.0, img_h))
        rendered_w = img_w * scale
        rendered_h = img_h * scale
        utilization = (rendered_w * rendered_h) / max(1.0, slot_w * slot_h)

        if img_ar >= WIDE_BANNER_AR_THRESHOLD and slot_ar < NARROW_SLOT_AR_LIMIT:
            violations.append(
                f"{fig_id}: wide banner (AR={img_ar:.2f}) placed in narrow slot (AR={slot_ar:.2f}), "
                f"utilization={utilization:.1%}"
            )
        elif utilization < MIN_SLOT_UTILIZATION_RATIO:
            violations.append(
                f"{fig_id}: low slot utilization {utilization:.1%} < {MIN_SLOT_UTILIZATION_RATIO:.0%} "
                f"(img AR={img_ar:.2f} vs slot AR={slot_ar:.2f})"
            )
        if panel_rows >= 2 and rendered_h < MIN_MULTIROW_SLOT_HEIGHT_PX:
            violations.append(
                f"{fig_id}: multi-row figure ({panel_rows} rows) crushed to height {rendered_h:.0f}px "
                f"< {MIN_MULTIROW_SLOT_HEIGHT_PX:.0f}px"
            )

    passed = len(violations) == 0
    return {
        "gate": "D9_Image_AspectRatio_Layout_Compatibility_Guard",
        "passed": passed,
        "violations": violations,
    }


def verify_subpanel_crop_purity(
    crop_specs: Sequence[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Gate D10 (Rubric B2): Verify sub-panel decomposition (`<= 2` sub-panels per slide)
    and catch blind PDF cropping (`>18%` blank margin strip, black border rules, sliced
    edge text ink `>2.5%` along crop boundary, or neighbor-figure text bleed).
    """
    violations: List[str] = []
    for spec in crop_specs:
        fig_id = str(spec.get("id", "crop"))
        subpanels = _int_or(spec, "subpanel_count", 1)
        blank_margin_ratio = _num_or(spec, "blank_margin_ratio", 0.0)
        border_ink_ratio = _num_or(spec, "border_sliced_ink_ratio", 0.0)
        has_neighbor_bleed = bool(spec.get("has_neighbor_bleed", False))
        has_black_margin_line = bool(spec.get("has_black_margin_line", False))

        if "image_array" in spec and isinstance(spec["image_array"], np.ndarray):
            arr = np.asarray(spec["image_array"], dtype=np.float64)
            if arr.ndim == 3:
                arr = arr.mean(axis=2)
            is_ink = arr < 235.0
            top_ink = float(np.mean(is_ink[:2, :]))
            bot_ink = float(np.mean(is_ink[-2:, :]))
            right_ink = float(np.mean(is_ink[:, -2:]))
            border_ink_ratio = max(border_ink_ratio, top_ink, bot_ink, right_ink)

            col_has_ink = np.mean(is_ink, axis=0) > 0.01
            nonzero_cols = np.where(col_has_ink)[0]
            if len(nonzero_cols) > 0:
                left_blank = float(nonzero_cols[0]) / float(arr.shape[1])
                blank_margin_ratio = max(blank_margin_ratio, left_blank)

        if subpanels > MAX_SUBPANELS_PER_SLIDE:
            violations.append(
                f"{fig_id}: unsplit composite figure with {subpanels} sub-panels (> {MAX_SUBPANELS_PER_SLIDE})"
            )
        if blank_margin_ratio > MAX_BLANK_MARGIN_RATIO:
            violations.append(
                f"{fig_id}: excessive blank PDF margin strip {blank_margin_ratio:.1%} > {MAX_BLANK_MARGIN_RATIO:.0%}"
            )
        if border_ink_ratio > MAX_BORDER_SLICED_INK_RATIO:
            violations.append(
                f"{fig_id}: sliced title/axis text along crop boundary (ink={border_ink_ratio:.1%})"
            )
        if has_neighbor_bleed:
            violations.append(f"{fig_id}: neighbor figure text remnant bled into crop")
        if has_black_margin_line:
            violations.append(f"{fig_id}: residual black PDF margin line detected")

    passed = len(violations) == 0
    return {
        "gate": "D10_Subpanel_Crop_Purity_No_Margin_Or_SlicedText_Probe",
        "passed": passed,
        "violations": violations,
    }


def verify_figure_text_explicit_coupling(
    slides: Sequence[Dict[str, Any]],
    total_paper_figures_cited: int,
) -> Dict[str, Any]:
    """
    Gate D11 (Rubric B1, B3, B4 & Redline R3): Reject zero-figure decks (`grok-4.7`),
    verify cropped sub-panels match the sub-panels discussed in text (`qwen-3.8` slide 8),
    require explicit directional reading pointers (`astra-6` slide 8 / `sol-6.1`), and
    block fabricated/axis-missing/mispositioned data charts (`deepseek` slide 18).
    """
    issues: List[str] = []
    redline_r3_count = 0
    if total_paper_figures_cited <= 0:
        issues.append("Rubric B1 D-grade: zero original paper figures cited across the entire deck")

    directional_pattern = re.compile(
        r"(?:左图|右图|上图|下图|上排|下排|第一列|第二列|第三列|第四列|横轴|纵轴|实线|虚线|星形|色带|亮带|读图顺序|先看|再看)"
    )

    for idx, slide in enumerate(slides, start=1):
        cropped = set(slide.get("cropped_subpanels", []))
        discussed = set(slide.get("discussed_subpanels", []))
        text = str(slide.get("visible_text", ""))

        if discussed and not DiscussedSubpanelSubset(discussed, cropped):
            missing = sorted(discussed - cropped)
            issues.append(
                f"Slide {idx}: text discusses sub-panel(s) {missing} missing from cropped figure {sorted(cropped)}"
            )
        if cropped and len(cropped - discussed) >= 2:
            unexplained = sorted(cropped - discussed)
            issues.append(
                f"Slide {idx}: figure includes unexplained sub-panel(s) {unexplained} (text-figure disconnect)"
            )
        if cropped and not directional_pattern.search(text):
            issues.append(
                f"Slide {idx}: figure present {sorted(cropped)} but text lacks explicit directional reading cues"
            )

        chart = slide.get("chart_audit")
        if isinstance(chart, dict):
            if not bool(chart.get("has_x_axis", True)) or not bool(chart.get("has_y_axis", True)):
                issues.append(f"Slide {idx} (Redline R3): 2D data chart missing X or Y coordinate axis")
                redline_r3_count += 1
            if bool(chart.get("coordinates_misplaced", False)):
                issues.append(f"Slide {idx} (Redline R3): plotted data points misaligned with axis ticks")
                redline_r3_count += 1
            if bool(chart.get("missing_literature_benchmarks", False)):
                issues.append(f"Slide {idx} (Redline R3): benchmark chart omits literature reference points")
                redline_r3_count += 1

    passed = len(issues) == 0
    return {
        "gate": "D11_Figure_Text_Explicit_Referencing_Coupling_Guard",
        "passed": passed,
        "total_paper_figures_cited": total_paper_figures_cited,
        "redline_r3_count": redline_r3_count,
        "issues": issues,
    }


def DiscussedSubpanelSubset(discussed: set, cropped: set) -> bool:
    """Helper checking whether all discussed sub-panels are present in the cropped image."""
    return discussed.issubset(cropped)


def _relative_luminance(rgb: Tuple[int, int, int]) -> float:
    """Compute WCAG 2.1 relative luminance from 8-bit sRGB tuple."""
    channels = []
    for c in rgb:
        v = max(0.0, min(1.0, float(c) / 255.0))
        channels.append(v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4)
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def verify_wcag_contrast_and_visual_restraint(
    color_pairs: Sequence[Dict[str, Any]],
    has_cyberpunk_neon_glow: bool = False,
    pptx_font_slots_uniform: bool = True,
) -> Dict[str, Any]:
    """
    Gate D12 (Rubric D2): Verify WCAG 2.1 contrast ratio >= 4.5 for body text (>= 3.0 for large
    titles), block garish cyberpunk neon glow abuse (`deepseek`), and verify 4-slot font purity.
    """
    low_contrast: List[str] = []
    for pair in color_pairs:
        label = str(pair.get("id", "text"))
        fg = tuple(pair.get("fg_rgb", (20, 20, 30)))
        bg = tuple(pair.get("bg_rgb", (255, 255, 255)))
        is_large = bool(pair.get("is_large_title", False))
        l1 = _relative_luminance((int(fg[0]), int(fg[1]), int(fg[2])))
        l2 = _relative_luminance((int(bg[0]), int(bg[1]), int(bg[2])))
        ratio = (max(l1, l2) + 0.05) / (min(l1, l2) + 0.05)
        threshold = WCAG_TITLE_CONTRAST_MIN if is_large else WCAG_BODY_CONTRAST_MIN
        if ratio < threshold:
            low_contrast.append(f"{label}: contrast {ratio:.2f}:1 < {threshold:.1f}:1")

    passed = (
        len(low_contrast) == 0
        and not has_cyberpunk_neon_glow
        and pptx_font_slots_uniform
    )
    return {
        "gate": "D12_WCAG_Contrast_And_Visual_Restraint_Probe",
        "passed": passed,
        "low_contrast_items": low_contrast,
        "has_cyberpunk_neon_glow": has_cyberpunk_neon_glow,
        "pptx_font_slots_uniform": pptx_font_slots_uniform,
    }


# ============================================================================
# Pillar III: Pedagogical Causal Chain, Interactive Physics & Storyboard Anchor
# ============================================================================

def verify_narrative_arc_and_foreshadowing(
    narrative_spec: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Gate D13 (Rubric A1, A2 & Supermolecule 2): Verify the 4-stage pedagogical narrative arc:
    (1) Macro industry/daily context & fundamental concept definition (e.g. what PHOLED is),
    (2) Degradation/bottleneck mechanism, (3) Prior Art routes & ceiling, (4) Core solution +
    foreshadowing/callback hooks, and zero clue-free blind guessing on early slides.
    """
    issues: List[str] = []
    if not bool(narrative_spec.get("has_macro_background_and_core_def", False)):
        issues.append("Missing macro background & fundamental concept definition (e.g. what PHOLED is)")
    if not bool(narrative_spec.get("has_degradation_or_bottleneck_mechanism", False)):
        issues.append("Missing physical/chemical bottleneck mechanism before introducing solution")
    if not bool(narrative_spec.get("has_prior_art_and_ceiling", False)):
        issues.append("Missing Prior Art routes and shared ceiling slide (Rubric A2)")
    if bool(narrative_spec.get("has_clue_free_blind_guessing", False)):
        issues.append("Contains abrupt clue-free blind numerical guessing on early slide (Supermolecule 2)")

    has_foreshadowing = bool(narrative_spec.get("has_foreshadowing_and_callback", False))
    passed = len(issues) == 0
    return {
        "gate": "D13_Narrative_Arc_Background_PriorArt_And_Foreshadowing_Guard",
        "passed": passed,
        "has_foreshadowing_and_callback": has_foreshadowing,
        "issues": issues,
    }


def verify_causal_why_chain_and_tradeoffs(
    mechanism_spec: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Gate D14 (Rubric A3, A4, A6 & Redline R7): Verify that core mechanism slides explain the
    complete causal 'Why' chain (not bare conclusion arrows), include dedicated device/molecular
    structures, pair controlled variables with baseline disambiguation, and contain zero
    scientific/structural inaccuracies (`R7`).
    """
    issues: List[str] = []
    why_links = mechanism_spec.get("causal_why_links_explained", {})
    for link_name, explained in why_links.items():
        if not bool(explained):
            issues.append(f"Unexplained causal 'Why' link: {link_name}")

    if not bool(mechanism_spec.get("has_dedicated_device_or_assembly_slide", True)):
        issues.append("Missing dedicated device stack (C/H/F) or supramolecular assembly slide (A4)")
    if not bool(mechanism_spec.get("has_real_molecular_chemical_structures", True)):
        issues.append("Missing real molecular chemical structure diagrams (e.g., BPyTP2/18-crown-6, A4)")
    if not bool(mechanism_spec.get("has_controlled_pair_comparison_and_baseline_note", True)):
        issues.append("Missing controlled-variable pair comparison or baseline disambiguation (A6)")
    if not bool(mechanism_spec.get("has_multi_objective_tradeoff_explanation", True)):
        issues.append("Missing multi-objective trade-off explanation (e.g., why max PF != max EQE, A6)")

    factual_errors = list(mechanism_spec.get("scientific_or_structural_errors", []))
    for err in factual_errors:
        issues.append(f"Redline R7 scientific/structural error: {err}")

    passed = len(issues) == 0
    return {
        "gate": "D14_Causal_Why_Chain_And_Control_Pair_Tradeoff_Guard",
        "passed": passed,
        "redline_r7_count": len(factual_errors),
        "issues": issues,
    }


def verify_interactive_physics_and_animations(
    html_text: str,
    interaction_spec: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Gate D15 (Rubric E1, E2 & Supermolecule 5): Detect hollow `@keyframes` defined in `<style>`
    but never mounted in DOM/CSS (`gemini-3.8flash` slide 4), verify multi-variable physical
    formula coupling in interactive widgets, block reversed physical causality (`kimiK3` SHG),
    and check for interactive Quiz with explanatory feedback.
    """
    style_blocks = " ".join(re.findall(r"<style\b[^>]*>(.*?)</style>", html_text, flags=re.DOTALL | re.IGNORECASE))
    rest_html = re.sub(r"<style\b[^>]*>.*?</style>", " ", html_text, flags=re.DOTALL | re.IGNORECASE)
    declared_keyframes = set(re.findall(r"@keyframes\s+([a-zA-Z0-9_-]+)", style_blocks))

    unmounted_keyframes: List[str] = []
    for kf in sorted(declared_keyframes):
        mounted_in_style = len(re.findall(rf"\b{re.escape(kf)}\b", style_blocks)) >= 2
        mounted_in_dom = bool(re.search(rf"\b{re.escape(kf)}\b", rest_html))
        if not (mounted_in_style or mounted_in_dom):
            unmounted_keyframes.append(kf)

    issues: List[str] = []
    if unmounted_keyframes:
        issues.append(f"Hollow unmounted CSS @keyframes declared but never used: {unmounted_keyframes}")
    if not bool(interaction_spec.get("has_coupled_physics_formula_widget", False)):
        issues.append("Missing interactive widget with coupled physical formula response (E1)")
    if bool(interaction_spec.get("has_reversed_or_broken_physics_animation", False)):
        issues.append("Animation/widget demonstrates reversed or broken physical process (Supermolecule 5)")
    if not bool(interaction_spec.get("has_interactive_quiz_with_explanation", False)):
        issues.append("Missing end-of-deck interactive self-test Quiz with physical explanation (E2)")

    passed = len(issues) == 0
    return {
        "gate": "D15_Interactive_Widget_Physics_Linkage_And_Anti_Hollow_Animation_Guard",
        "passed": passed,
        "declared_keyframes": sorted(declared_keyframes),
        "unmounted_keyframes": unmounted_keyframes,
        "issues": issues,
    }


def verify_tdd_station_capsule_completeness(
    tdd_station_capsule: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Verify Tutor-Driven Design (TDD-Slide) 1-Station-to-1-Slide Cognitive Capsule completeness:
    Ensures the slide was crystallized from an authentic Tutor Station dialogue (`station_id`),
    unpacking `core_blindspot_or_conflict` (POE/Socratic bottleneck), `wittgenstein_ladder`
    (Bridge -> Deconstruct -> Replace), `human_orthogonal_insight` (delta_q orthogonal to b_AI),
    `visual_modality` (strictly V2 or V3, never V0 pure text), and `hidden_teleprompter_qa`.
    """
    issues: List[str] = []
    if not isinstance(tdd_station_capsule, dict) or not tdd_station_capsule:
        return {
            "passed": False,
            "issues": ["Missing tdd_station_capsule (Tutor Station-to-Slide TDD dialogue not recorded)"],
        }

    station_id = str(tdd_station_capsule.get("station_id", "")).strip()
    conflict = str(tdd_station_capsule.get("core_blindspot_or_conflict", "")).strip()
    ladder = str(tdd_station_capsule.get("wittgenstein_ladder", "")).strip()
    human_probe = str(tdd_station_capsule.get("human_orthogonal_insight", "")).strip()
    modality = str(tdd_station_capsule.get("visual_modality", "")).strip().upper()
    teleprompter_qa = str(tdd_station_capsule.get("hidden_teleprompter_qa", "")).strip()

    if len(station_id) < 2:
        issues.append("TDD capsule missing valid station_id (e.g. 'Station_1.1')")
    if len(conflict) < 8:
        issues.append("TDD capsule missing core_blindspot_or_conflict (Socratic/POE bottleneck)")
    if len(ladder) < 10:
        issues.append("TDD capsule missing wittgenstein_ladder (Bridge -> Deconstruct -> Replace)")
    if len(human_probe) < 6:
        issues.append("TDD capsule missing human_orthogonal_insight (delta_q orthogonal probe / direction)")
    if not (modality.startswith("V2") or modality.startswith("V3")):
        issues.append(
            f"TDD capsule visual_modality='{modality}' must be V2 (diagram/paper figure) or V3 (interactive physics widget); V0/V1 forbidden"
        )
    if len(teleprompter_qa) < 8:
        issues.append("TDD capsule missing hidden_teleprompter_qa (distilled speaker notes & Q&A defense)")

    return {
        "passed": len(issues) == 0,
        "station_id": station_id,
        "visual_modality": modality,
        "issues": issues,
    }


def verify_grill_station_capsule_completeness(
    gdd_grill_capsule: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Verify Grill-Driven Design (GDD / 以考代建) 1-Station-to-1-Slide Capsule completeness:
    The Agent starts by quizzing/grilling the user (`grill_question`). If the user answers,
    it deepens/validates; if the user misses or says '不会', it immediately teaches the
    mechanism (`teaching_and_regrill_closure`) and re-grills until mastered, then crystallizes
    the exact bottleneck and Q&A defense into `slide_0k.html` (`V2/V3` + `hidden_teleprompter_qa`).
    """
    issues: List[str] = []
    if not isinstance(gdd_grill_capsule, dict) or not gdd_grill_capsule:
        return {
            "passed": False,
            "issues": ["Missing gdd_grill_capsule (Grill-Driven Design station quiz/re-grill not recorded)"],
        }

    station_id = str(gdd_grill_capsule.get("station_id", "")).strip()
    grill_q = str(gdd_grill_capsule.get("grill_question", "")).strip()
    resp_state = str(gdd_grill_capsule.get("user_response_state", "")).strip().upper()
    closure = str(gdd_grill_capsule.get("teaching_and_regrill_closure", "")).strip()
    modality = str(gdd_grill_capsule.get("visual_modality", "")).strip().upper()
    teleprompter_qa = str(gdd_grill_capsule.get("hidden_teleprompter_qa", "")).strip()

    valid_states = {"ANSWERED_DIRECTLY", "TAUGHT_ON_MISS_AND_REGRILLED"}
    if len(station_id) < 2:
        issues.append("GDD capsule missing valid station_id (e.g. 'Station_1.1')")
    if len(grill_q) < 8:
        issues.append("GDD capsule missing upfront grill_question posed to the learner")
    if resp_state not in valid_states:
        issues.append(
            f"GDD capsule user_response_state='{resp_state}' must be in {sorted(valid_states)}"
        )
    if len(closure) < 10:
        issues.append(
            "GDD capsule missing teaching_and_regrill_closure (teach-on-miss explanation & follow-up re-grill verification)"
        )
    if not (modality.startswith("V2") or modality.startswith("V3")):
        issues.append(
            f"GDD capsule visual_modality='{modality}' must be V2 or V3 (V0/V1 forbidden)"
        )
    if len(teleprompter_qa) < 8:
        issues.append("GDD capsule missing hidden_teleprompter_qa (distilled grill Q&A defense)")

    return {
        "passed": len(issues) == 0,
        "station_id": station_id,
        "user_response_state": resp_state,
        "visual_modality": modality,
        "issues": issues,
    }


def verify_dual_evolution_feedback_receipt(
    feedback_receipt: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Verify Autonomous Draft + Post-Review Dual-Evolution (`AUTONOMOUS_DUAL_EVOLVE`) receipt:
    When the agent builds the deck head-down (`1-Slide-Per-Step`) and the human reviews it
    afterward, any human critique must produce a verified dual-evolution receipt covering:
    (1) patching & re-verifying the affected slide(s) in the PPT itself (`affected_slides_patched`), and
    (2) explicitly auditing/upgrading `AWF HTML-PPT` / `AWF DesignAG` (`is_generalizable_to_awf`,
        `target_gate_or_rule_id`, `negative_canary_fixture`) when the feedback represents a reusable rule.
    """
    issues: List[str] = []
    if not isinstance(feedback_receipt, dict) or not feedback_receipt:
        return {
            "passed": False,
            "issues": ["Missing dual_evolution_feedback_receipt for post-review dual upgrade"],
        }

    summary = str(feedback_receipt.get("human_feedback_summary", "")).strip()
    patched = feedback_receipt.get("affected_slides_patched", [])
    generalizable = feedback_receipt.get("is_generalizable_to_awf")
    gate_id = str(feedback_receipt.get("target_gate_or_rule_id", "")).strip()
    canary = str(feedback_receipt.get("negative_canary_fixture", "")).strip()
    rationale = str(feedback_receipt.get("non_generalizable_rationale", "")).strip()

    if len(summary) < 6:
        issues.append("Dual-evolution receipt missing human_feedback_summary")
    if not isinstance(patched, list) or len(patched) == 0:
        issues.append("Dual-evolution receipt must list >=1 re-audited slide in affected_slides_patched")
    if not isinstance(generalizable, bool):
        issues.append("Dual-evolution receipt must explicitly set boolean is_generalizable_to_awf")
    elif generalizable:
        if len(gate_id) < 2:
            issues.append("Generalizable feedback must specify target_gate_or_rule_id for AWF HTML-PPT / DesignAG upgrade")
        if len(canary) < 6:
            issues.append("Generalizable feedback must record negative_canary_fixture for AWF regression self-test")
    else:
        if len(rationale) < 6:
            issues.append("When is_generalizable_to_awf=False, must provide non_generalizable_rationale")

    return {
        "passed": len(issues) == 0,
        "affected_slides_patched": patched,
        "is_generalizable_to_awf": bool(generalizable),
        "target_gate_or_rule_id": gate_id,
        "issues": issues,
    }


def verify_storyboard_microstep_and_layout_diversity(
    storyboard_slides: Sequence[Dict[str, Any]],
    max_slides_generated_per_step: int = 1,
    unverified_slide_hop_distance: int = 1,
    tdd_mode: bool = False,
    tdd_station_capsule: Optional[Dict[str, Any]] = None,
    grill_mode: bool = False,
    gdd_grill_capsule: Optional[Dict[str, Any]] = None,
    dual_evolution_receipt: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Gate D16 (Design-Layer G6o + Tri-Mode Execution Anchor):
    Enforce pre-generation `SlideStoryboardManifest`, strictly 1-Slide-Per-Step micro-step
    generation (`max_slides_generated_per_step <= 1`), 1-hop topological slide lock
    (`unverified_slide_hop_distance == 1`), and Tri-Mode integrity:
    - Mode 1 (`tdd_mode`): Tutor-Driven Design (`tdd_station_capsule`),
    - Mode 2 (`grill_mode`): Grill-Driven Design (`gdd_grill_capsule`),
    - Mode 3 (`AUTONOMOUS_DUAL_EVOLVE`): Head-down 1-slide-per-step build + post-review
      dual-upgrade (`dual_evolution_receipt` upgrading both the PPT and AWF HTML-PPT/DesignAG),
    plus layout archetype diversity (`<= 2` consecutive identical layouts) & Shannon entropy `>= 1.4` bits.
    """
    issues: List[str] = []
    if not storyboard_slides:
        return {
            "gate": "D16_Slide_Storyboard_MicroStep_And_Layout_Diversity_Anchor",
            "passed": False,
            "issues": ["Missing SlideStoryboardManifest"],
        }
    if max_slides_generated_per_step > MAX_MICROSTEP_BATCH_SLIDES or max_slides_generated_per_step < 1:
        issues.append(
            f"Single-slide micro-step violation: generated {max_slides_generated_per_step} slides in one step "
            f"(strictly <= {MAX_MICROSTEP_BATCH_SLIDES} slide/step allowed)"
        )
    if unverified_slide_hop_distance != 1:
        issues.append(
            f"Topological 1-hop slide lock violation: unverified_slide_hop_distance={unverified_slide_hop_distance} != 1 "
            "(previous slide must hold a PASS receipt in slide_manifest.json before generating next slide)"
        )
    if tdd_mode or tdd_station_capsule is not None:
        tdd_res = verify_tdd_station_capsule_completeness(tdd_station_capsule)
        if not tdd_res["passed"]:
            issues.extend(tdd_res["issues"])
    if grill_mode or gdd_grill_capsule is not None:
        gdd_res = verify_grill_station_capsule_completeness(gdd_grill_capsule)
        if not gdd_res["passed"]:
            issues.extend(gdd_res["issues"])
    if dual_evolution_receipt is not None:
        de_res = verify_dual_evolution_feedback_receipt(dual_evolution_receipt)
        if not de_res["passed"]:
            issues.extend(de_res["issues"])

    layouts = [str(s.get("layout_archetype", "unknown")) for s in storyboard_slides]
    streak = 1
    for i in range(1, len(layouts)):
        if layouts[i] == layouts[i - 1]:
            streak += 1
            if streak > MAX_CONSECUTIVE_SAME_LAYOUT:
                issues.append(
                    f"Slides {i - streak + 2}..{i + 1} repeat identical layout '{layouts[i]}' ({streak}x)"
                )
        else:
            streak = 1

    counts: Dict[str, int] = {}
    for lay in layouts:
        counts[lay] = (counts[lay] if lay in counts else 0) + 1
    total = float(len(layouts))
    entropy = -sum((c / total) * math.log2(c / total) for c in counts.values() if c > 0)
    if len(layouts) >= 6 and entropy < MIN_LAYOUT_SHANNON_ENTROPY:
        issues.append(
            f"Layout diversity Shannon entropy {entropy:.2f} bits < {MIN_LAYOUT_SHANNON_ENTROPY:.2f} bits"
        )

    passed = len(issues) == 0
    return {
        "gate": "D16_Slide_Storyboard_MicroStep_And_Layout_Diversity_Anchor",
        "passed": passed,
        "layout_entropy_bits": round(entropy, 4),
        "max_slides_generated_per_step": max_slides_generated_per_step,
        "unverified_slide_hop_distance": unverified_slide_hop_distance,
        "issues": issues,
    }


# ============================================================================
# Pillar IV: Dual-Rubric Quantitative Scorer & Red-Blue Visual Critic (D17-D18)
# ============================================================================

def score_optoelectronic_rubric_v3(eval_payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute exact deterministic score under Rubric Mode 1:
    `01_optoelectronic_scoring_criteria_v3.md` (A=46, B=20, C=16, D=8, E=10, Redlines R1..R7 up to -15).
    Enforces: A_item = weight * clarity_coeff * min(1.0, visual_coeff / required_visual_coeff).
    """
    a_items = eval_payload.get("category_a_knowledge_items", [])
    a_total = 0.0
    a_breakdown: Dict[str, float] = {}
    v0_capped_items: List[str] = []

    for item in a_items:
        kid = str(item["id"])
        weight = float(item["weight"])
        clarity_key = str(item.get("clarity", "D")).upper()
        clarity = CLARITY_COEFF_MAP[clarity_key] if clarity_key in CLARITY_COEFF_MAP else 0.0
        vis_level = str(item.get("visual_level", "V0")).upper()
        req_level = str(item.get("required_visual_level", "V2")).upper()
        if bool(item.get("is_ai_decorative_image", False)):
            vis_level = "V0"
        vis_c = VISUAL_MODALITY_COEFF_MAP[vis_level] if vis_level in VISUAL_MODALITY_COEFF_MAP else 0.30
        req_c = VISUAL_MODALITY_COEFF_MAP[req_level] if req_level in VISUAL_MODALITY_COEFF_MAP else 0.80
        expr_factor = 1.0 if vis_c >= req_c else vis_c
        if vis_level == "V0" and weight > 0:
            v0_capped_items.append(kid)
        pts = round(weight * clarity * expr_factor, 3)
        a_total += pts
        a_breakdown[kid] = pts

    b_weights = {"B1": 4.0, "B2": 5.0, "B3": 7.0, "B4": 4.0}
    c_weights = {"C1": 6.0, "C2": 5.0, "C3": 5.0}
    d_weights = {"D1": 5.0, "D2": 3.0}
    e_weights = {"E1": 7.0, "E2": 3.0}
    grades = eval_payload.get("b_to_e_grades", {})

    def _sum_group(w_map: Dict[str, float]) -> float:
        total_g = 0.0
        for k, w in w_map.items():
            val = grades.get(k, "D")
            if isinstance(val, (int, float)):
                ratio = float(val)
            else:
                uk = str(val).upper()
                ratio = GRADE_TO_RATIO_MAP[uk] if uk in GRADE_TO_RATIO_MAP else 0.0
            total_g += w * max(0.0, min(1.0, ratio))
        return round(total_g, 3)

    b_score = _sum_group(b_weights)
    c_score = _sum_group(c_weights)
    d_score = _sum_group(d_weights)
    e_score = _sum_group(e_weights)

    red = eval_payload.get("redlines", {})
    raw_deduction = (
        (5.0 if bool(red.get("R1_latex_leak", False)) else 0.0)
        + 2.0 * _int_or(red, "R2_broken_layout_pages", 0)
        + 3.0 * _int_or(red, "R3_fake_or_misplaced_charts", 0)
        + 2.0 * _int_or(red, "R4_ai_deco_mechanism_fakes", 0)
        + 2.0 * _int_or(red, "R5_prompt_residue_hits", 0)
        + (2.0 if bool(red.get("R6_teleprompter_visible", False)) else 0.0)
        + 2.0 * _int_or(red, "R7_scientific_fact_errors", 0)
    )
    capped_deduction = min(MAX_REDLINE_DEDUCTION, raw_deduction)
    gross = round(a_total + b_score + c_score + d_score + e_score, 2)
    final_score = max(0.0, round(gross - capped_deduction, 2))
    return {
        "rubric": "optoelectronic_v3_100_plus_R15",
        "A_scientific_explanation_46": round(a_total, 2),
        "B_figures_and_evidence_20": b_score,
        "C_expression_and_clarity_16": c_score,
        "D_visual_and_engineering_8": d_score,
        "E_interaction_quality_10": e_score,
        "gross_score_100": gross,
        "redline_deduction_capped_15": -capped_deduction,
        "final_score": final_score,
        "v0_pure_text_capped_items": v0_capped_items,
        "a_item_breakdown": a_breakdown,
    }


def score_supermolecule_5dim_rubric(eval_payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute exact deterministic score under Rubric Mode 2:
    `02_supermolecule_SCORING_CRITERIA_5dim.md` (Readability 25 + Logic 20 + Richness/Accuracy 20
    + Visuals 20 + Interaction 15 = 100 pts).
    """
    d1 = _num_or(eval_payload, "dim1_readability_base_25", 24.0)
    d1_penalties = eval_payload.get("dim1_penalties", {})
    if bool(d1_penalties.get("extreme_overload_or_unreadable", False)):
        d1 = min(d1, 2.0)
    else:
        if bool(d1_penalties.get("top_heavy_imbalance", False)):
            d1 -= 6.0
        if bool(d1_penalties.get("bottom_overflow_clipped", False)):
            d1 -= 5.0
        if bool(d1_penalties.get("raw_latex_exposed", False)):
            d1 -= 6.0
        if bool(d1_penalties.get("too_few_slides_overload", False)):
            d1 -= 5.0
        if bool(d1_penalties.get("font_too_small", False)):
            d1 -= 5.0
        if bool(d1_penalties.get("text_overlap", False)):
            d1 -= 3.5
        if bool(d1_penalties.get("grid_3plus1_orphan", False)):
            d1 -= 3.0
    d1 = max(0.0, min(25.0, d1))

    d2 = max(0.0, min(20.0, _num_or(eval_payload, "dim2_logic_score_20", 19.0)))
    d3 = max(0.0, min(20.0, _num_or(eval_payload, "dim3_richness_accuracy_20", 19.0)))
    d4 = max(0.0, min(20.0, _num_or(eval_payload, "dim4_visual_fidelity_20", 18.0)))
    d5 = max(0.0, min(15.0, _num_or(eval_payload, "dim5_interaction_15", 14.0)))

    total = round(d1 + d2 + d3 + d4 + d5, 2)
    return {
        "rubric": "supermolecule_5dim_100",
        "dim1_readability_layout_25": round(d1, 2),
        "dim2_narrative_logic_20": round(d2, 2),
        "dim3_richness_accuracy_20": round(d3, 2),
        "dim4_visual_fidelity_20": round(d4, 2),
        "dim5_interaction_design_15": round(d5, 2),
        "final_score": total,
    }


def score_presentation_dual_rubric(eval_payload: Dict[str, Any]) -> Dict[str, Any]:
    """Gate D17: Run both Optoelectronic v3 and Supermolecule 5-Dim quantitative scorers."""
    opt_res = score_optoelectronic_rubric_v3(eval_payload.get("optoelectronic_v3", {}))
    sup_res = score_supermolecule_5dim_rubric(eval_payload.get("supermolecule_5dim", {}))
    min_pass = _num_or(eval_payload, "min_passing_score", 80.0)
    passed = (opt_res["final_score"] >= min_pass) and (sup_res["final_score"] >= min_pass)
    return {
        "gate": "D17_DualRubric_Quantitative_Scorer",
        "passed": passed,
        "optoelectronic_v3_result": opt_res,
        "supermolecule_5dim_result": sup_res,
    }


def evaluate_visual_red_blue_adversarial_audit(
    blue_claimed_score: float,
    rendered_png_paths: Sequence[str],
    red_critic_findings: Sequence[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Gate D18 (Design-Layer G7h): Decoupled multimodal Red-Blue visual adversarial audit.
    Requires rendered slide PNG evidence (`rendered_png_paths`) and zeroes out Blue Builder
    reward if the independent Red Visual Critic exposes any severe visual/scientific defect.
    """
    if not rendered_png_paths:
        return {
            "gate": "D18_RedBlue_Visual_Adversarial_Critic_Protocol",
            "passed": False,
            "reason": "Missing rendered 1920x1080 PNG screenshots for visual inspection",
            "blue_effective_reward": float("-inf"),
            "red_auditor_bounty": 10.0,
        }
    confirmed_defects = [
        f for f in red_critic_findings if bool(f.get("verified_on_rendered_png", True))
    ]
    has_redline = any(bool(f.get("is_redline", False)) for f in confirmed_defects)
    passed = len(confirmed_defects) == 0
    blue_eff = (
        float(blue_claimed_score)
        if passed
        else (float("-inf") if has_redline else 0.0)
    )
    red_bounty = sum(_num_or(f, "severity_weight", 2.0) for f in confirmed_defects)
    return {
        "gate": "D18_RedBlue_Visual_Adversarial_Critic_Protocol",
        "passed": passed,
        "rendered_png_count": len(rendered_png_paths),
        "confirmed_defect_count": len(confirmed_defects),
        "blue_effective_reward": blue_eff,
        "red_auditor_bounty": round(red_bounty, 2),
    }


def run_all_18_design_gates(bundle: Dict[str, Any]) -> Dict[str, Any]:
    """Execute all 18 DesignAG gates (D1-D18) on a presentation verification bundle."""
    html_text = str(bundle.get("html_text", ""))
    results = [
        scan_html_for_unrendered_latex_leak(html_text),
        audit_html_tag_balance_and_grid_orphans(html_text, bundle.get("grid_specs")),
        audit_copywriting_naturalness_and_ai_tone(bundle.get("slides", [])),
        audit_acronym_definitions_and_popovers(
            bundle.get("slides", []),
            bundle.get("required_acronyms", ("PHOLED", "TPA", "TTA", "LT90", "PF", "ODoS", "SPP", "PEP")),
        ),
        audit_emojis_fake_bars_and_watermarks(html_text, bundle.get("figure_metadata")),
        audit_teleprompter_and_slide_density(bundle.get("deck_spec", {})),
        verify_bounding_boxes_zero_overlap_and_clipping(bundle.get("boxes", [])),
        verify_canvas_whitespace_and_center_of_mass(bundle.get("boxes", [])),
        verify_image_aspect_ratio_and_slot_utilization(bundle.get("placements", [])),
        verify_subpanel_crop_purity(bundle.get("crop_specs", [])),
        verify_figure_text_explicit_coupling(
            bundle.get("slides", []), _int_or(bundle, "total_paper_figures_cited", 5)
        ),
        verify_wcag_contrast_and_visual_restraint(
            bundle.get("color_pairs", []),
            bool(bundle.get("has_cyberpunk_neon_glow", False)),
            bool(bundle.get("pptx_font_slots_uniform", True)),
        ),
        verify_narrative_arc_and_foreshadowing(bundle.get("narrative_spec", {})),
        verify_causal_why_chain_and_tradeoffs(bundle.get("mechanism_spec", {})),
        verify_interactive_physics_and_animations(html_text, bundle.get("interaction_spec", {})),
        verify_storyboard_microstep_and_layout_diversity(
            bundle.get("storyboard_slides", []),
            _int_or(bundle, "max_slides_generated_per_step", 1),
            _int_or(bundle, "unverified_slide_hop_distance", 1),
            bool(bundle.get("tdd_mode", False)),
            bundle.get("tdd_station_capsule"),
            bool(bundle.get("grill_mode", False)),
            bundle.get("gdd_grill_capsule"),
            bundle.get("dual_evolution_receipt"),
        ),
        score_presentation_dual_rubric(bundle.get("dual_rubric_eval", {})),
        evaluate_visual_red_blue_adversarial_audit(
            _num_or(bundle, "blue_claimed_score", 92.0),
            bundle.get("rendered_png_paths", ["slide_01.png"]),
            bundle.get("red_critic_findings", []),
        ),
    ]
    gates_passed = [r["gate"] for r in results if r.get("passed")]
    gates_failed = [r["gate"] for r in results if not r.get("passed")]
    return {
        "verdict_zone": "PASS" if len(gates_failed) == 0 else "FAIL",
        "total_gates": len(results),
        "gates_passed_count": len(gates_passed),
        "gates_passed": gates_passed,
        "gates_failed": gates_failed,
        "gate_details": results,
    }


def _resolve_awf_guard_scripts_dir() -> Path:
    candidates = [
        Path("/home/zc/agent_workflows/components/skills/anti-goodhart-verification/releases/3.5.0-rc.1/source/scripts"),
        Path(r"Z:\agent_workflows\components\skills\anti-goodhart-verification\releases\3.5.0-rc.1\source\scripts"),
        Path("/home/zc/agent_workflows/components/skills/anti-goodhart-verification/releases/3.4.0-rc.1/source/scripts"),
        Path(r"Z:\agent_workflows\components\skills\anti-goodhart-verification\releases\3.4.0-rc.1\source\scripts"),
        Path(__file__).resolve().parents[2] / "anti-goodhart-verification" / "scripts",
    ]
    for c in candidates:
        if c.is_dir():
            return c
    return candidates[0]


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="AWF DesignAG 18-Gate & Dual-Rubric Engine")
    parser.add_argument("--self-test", action="store_true", help="Run 18-gate positive/negative self-test suite")
    parser.add_argument("--audit-self", action="store_true", help="Run AWF Guard G6n self-hosting dogfood audit on DesignAG")
    parser.add_argument("--audit-html", type=str, default="", help="Audit an HTML presentation file")
    args = parser.parse_args(argv)

    if args.audit_self:
        sys.dont_write_bytecode = True
        ag_scripts = _resolve_awf_guard_scripts_dir()
        if str(ag_scripts) not in sys.path:
            sys.path.insert(0, str(ag_scripts))
        import awf_universal_anti_goodhart_gates as ag_core  # type: ignore

        audit_rep = ag_core.audit_engine_self_hosting_integrity(Path(__file__).resolve())
        print(json.dumps(audit_rep, indent=2, ensure_ascii=False))
        return 0 if audit_rep.get("status") == "PASS" else 1

    if args.self_test:
        sys.dont_write_bytecode = True
        scripts_dir = str(Path(__file__).resolve().parent)
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)
        import awf_design_ag_selftest_suite as selftest  # type: ignore

        report = selftest.run_design_ag_selftest_suite()
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0 if report.get("verdict_zone") == "PASS" else 1

    if args.audit_html:
        p = Path(args.audit_html)
        html_content = p.read_text(encoding="utf-8")
        res = {
            "file": str(p),
            "D1": scan_html_for_unrendered_latex_leak(html_content),
            "D2": audit_html_tag_balance_and_grid_orphans(html_content),
            "D5": audit_emojis_fake_bars_and_watermarks(html_content),
        }
        print(json.dumps(res, indent=2, ensure_ascii=False))
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
