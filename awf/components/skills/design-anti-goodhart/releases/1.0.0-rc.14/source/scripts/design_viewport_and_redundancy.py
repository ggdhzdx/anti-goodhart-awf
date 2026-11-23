"""
HTML-Level Slide Redundancy, Information Density & Fixed-Canvas Viewport Auto-Fit Guards
(`skill.design-anti-goodhart@1.0.0-rc.14`).

Enforces two structural anti-Goodhart invariants directly on raw slide HTML (`html_text`):
1. `SVG_SideCard_Redundant_Echo_Guard`: Blocks slides where a self-labeled `<svg>` diagram
   already carries dense text/metrics yet the author also stacks >=3 verbose `<article>`
   side-cards repeating the same tiers, numbers, and CJK phrases ("信息太密，右边卡片完全没必要").
2. `Fixed_Canvas_Viewport_AutoFit_Guard`: Blocks slides that hardcode desktop pixel canvases
   (`width >= 1200px` or `height >= 700px`, e.g., `1600x900` or `1920x1080`) without standalone
   dual-axis viewport scaling (`innerWidth` + `innerHeight` / `100vw` + `100vh` `scale(...)`),
   `overflow: hidden` scrollbar containment, and `left: 50%; top: 50%; translate(-50%, -50%)`
   viewport centering ("页面超出屏幕，需要手动缩放才能完整显示").
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Set

MIN_FIXED_CANVAS_WIDTH_PX = 1200
MIN_FIXED_CANVAS_HEIGHT_PX = 700
MIN_SUBSTANTIVE_SVG_LABEL_CHARS = 3
MIN_SELF_LABELED_SVG_TEXTS = 12
MAX_DENSE_SVG_TEXTS_WITH_CARDS = 24
MIN_REDUNDANT_CARD_COUNT = 3
MIN_VERBOSE_SIDECARD_CHARS = 160
MAX_SVG_CARD_REPEATED_NUMS = 4
MAX_SVG_CARD_SHARED_TRIGRAMS = 7
CJK_TRIGRAM_LEN = 3

AXIS_TICK_ONLY_RE = re.compile(r"^[+-]?\d+(?:\.\d+)?%?$")
QUANT_TOKEN_RE = re.compile(
    r"\d+(?:\.\d+)?\s*(?:%|µm|μm|nm|mm|cm|meV|eV|mV|V|mA|h|ps|ns|µs|μs|°C|K|Å|倍)"
)
CJK_RUN_RE = re.compile(r"[\u4e00-\u9fff]+")


def _strip_non_canvas_blocks(html_text: str) -> str:
    cleaned = re.sub(r"<script\b[^>]*>.*?</script>", " ", html_text, flags=re.DOTALL | re.IGNORECASE)
    cleaned = re.sub(r"<style\b[^>]*>.*?</style>", " ", cleaned, flags=re.DOTALL | re.IGNORECASE)
    cleaned = re.sub(
        r"<aside\b[^>]*class=[\"'][^\"']*notes[^\"']*[\"'][^>]*>.*?</aside>",
        " ",
        cleaned,
        flags=re.DOTALL | re.IGNORECASE,
    )
    return cleaned


def _plain_text(fragment: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", fragment)).strip()


def _extract_quant_tokens(text: str) -> Set[str]:
    normalized = text.replace("μ", "µ")
    return {re.sub(r"\s+", "", m.group(0)) for m in QUANT_TOKEN_RE.finditer(normalized)}


def _extract_cjk_trigrams(text: str) -> Set[str]:
    grams: Set[str] = set()
    for run in CJK_RUN_RE.findall(text):
        if len(run) >= CJK_TRIGRAM_LEN:
            for idx in range(len(run) - CJK_TRIGRAM_LEN + 1):
                grams.add(run[idx : idx + CJK_TRIGRAM_LEN])
    return grams


def audit_svg_sidecard_echo_and_density(html_text: str) -> Dict[str, Any]:
    """
    Detect redundant `<article>` side-cards echoing an already self-labeled `<svg>` chart/diagram.
    """
    visible_dom = _strip_non_canvas_blocks(html_text)
    svg_blocks = re.findall(r"<svg\b[^>]*>(.*?)</svg>", visible_dom, flags=re.DOTALL | re.IGNORECASE)
    dom_without_svg = re.sub(r"<svg\b[^>]*>.*?</svg>", " ", visible_dom, flags=re.DOTALL | re.IGNORECASE)

    svg_labels: List[str] = []
    for svg_body in svg_blocks:
        for raw_label in re.findall(r"<text\b[^>]*>(.*?)</text>", svg_body, flags=re.DOTALL | re.IGNORECASE):
            lbl = _plain_text(raw_label)
            if len(lbl) >= MIN_SUBSTANTIVE_SVG_LABEL_CHARS and not AXIS_TICK_ONLY_RE.match(lbl):
                svg_labels.append(lbl)

    svg_joined = " ".join(svg_labels)
    svg_nums = _extract_quant_tokens(svg_joined)
    svg_trigrams = _extract_cjk_trigrams(svg_joined)

    article_blocks = re.findall(
        r"<article\b[^>]*>(.*?)</article>", dom_without_svg, flags=re.DOTALL | re.IGNORECASE
    )
    card_texts = [_plain_text(blk) for blk in article_blocks if _plain_text(blk)]
    article_count = len(card_texts)
    article_chars = sum(len(t) for t in card_texts)
    cards_joined = " ".join(card_texts)
    card_nums = _extract_quant_tokens(cards_joined)
    card_trigrams = _extract_cjk_trigrams(cards_joined)

    repeated_nums = sorted(svg_nums & card_nums)
    shared_trigrams = sorted(svg_trigrams & card_trigrams)

    issues: List[str] = []
    if (
        len(svg_labels) >= MIN_SELF_LABELED_SVG_TEXTS
        and article_count >= MIN_REDUNDANT_CARD_COUNT
        and article_chars >= MIN_VERBOSE_SIDECARD_CHARS
    ):
        if len(repeated_nums) > MAX_SVG_CARD_REPEATED_NUMS:
            issues.append(
                f"Redundant SVG-to-card quantitative echo: <svg> already has {len(svg_labels)} labels, "
                f"yet {article_count} <article> cards ({article_chars} chars) repeat {len(repeated_nums)} "
                f"numbers {repeated_nums[:6]} — remove redundant side-cards and let the chart breathe"
            )
        if len(shared_trigrams) > MAX_SVG_CARD_SHARED_TRIGRAMS:
            issues.append(
                f"Redundant SVG-to-card text echo: {article_count} <article> cards repeat {len(shared_trigrams)} "
                f"CJK phrases {shared_trigrams[:6]} already printed inside <svg>"
            )
        if len(svg_labels) >= MAX_DENSE_SVG_TEXTS_WITH_CARDS:
            issues.append(
                f"Single-slide density overload: dense <svg> ({len(svg_labels)} text labels >= "
                f"{MAX_DENSE_SVG_TEXTS_WITH_CARDS}) combined with {article_count} verbose <article> cards "
                f"({article_chars} chars) crowds the slide; split into separate slides or drop side-cards"
            )

    return {
        "passed": len(issues) == 0,
        "svg_substantive_label_count": len(svg_labels),
        "article_card_count": article_count,
        "article_visible_chars": article_chars,
        "repeated_quant_tokens": repeated_nums,
        "shared_cjk_trigram_count": len(shared_trigrams),
        "issues": issues,
    }


def _detect_fixed_pixel_canvas(style_css: str) -> bool:
    widths = [
        int(m)
        for m in re.findall(
            r"(?:--canvas-w(?:idth)?|(?<![a-zA-Z-])width)\s*:\s*(\d{3,4})px",
            style_css,
            flags=re.IGNORECASE,
        )
    ]
    heights = [
        int(m)
        for m in re.findall(
            r"(?:--canvas-h(?:eight)?|(?<![a-zA-Z-])height)\s*:\s*(\d{3,4})px",
            style_css,
            flags=re.IGNORECASE,
        )
    ]
    return any(w >= MIN_FIXED_CANVAS_WIDTH_PX for w in widths) and any(
        h >= MIN_FIXED_CANVAS_HEIGHT_PX for h in heights
    )


def audit_fixed_canvas_viewport_autofit(html_text: str) -> Dict[str, Any]:
    """
    Verify that any slide declaring a fixed large pixel canvas (e.g. 1600x900 or 1920x1080)
    includes self-contained dual-axis viewport auto-fit scaling and centered positioning so it
    never overflows laptop screens (125%/150% DPI) or requires manual browser zooming.
    """
    style_css = " ".join(
        re.findall(r"<style\b[^>]*>(.*?)</style>", html_text, flags=re.DOTALL | re.IGNORECASE)
    )
    script_js = " ".join(
        re.findall(r"<script\b[^>]*>(.*?)</script>", html_text, flags=re.DOTALL | re.IGNORECASE)
    )
    combined_code = f"{style_css}\n{script_js}"

    has_fixed_canvas = _detect_fixed_pixel_canvas(style_css)
    if not has_fixed_canvas:
        return {
            "passed": True,
            "has_fixed_pixel_canvas": False,
            "issues": [],
        }

    has_doc_overflow_hidden = bool(
        re.search(
            r"(?:html|body)[^{]*\{[^}]*overflow\s*:\s*hidden",
            style_css,
            flags=re.DOTALL | re.IGNORECASE,
        )
        or re.search(
            r"(?:documentElement|body)\.style(?:\.overflow\s*=\s*[\"']hidden|\.cssText[^;]*overflow\s*:\s*hidden)",
            script_js,
            flags=re.DOTALL | re.IGNORECASE,
        )
    )
    has_js_dual_axis_scale = (
        bool(re.search(r"innerWidth|clientWidth", script_js))
        and bool(re.search(r"innerHeight|clientHeight", script_js))
        and bool(re.search(r"scale\s*\(", combined_code))
    )
    has_css_dual_axis_scale = (
        "100vw" in style_css and "100vh" in style_css and bool(re.search(r"scale\s*\(", style_css))
    )
    has_dual_axis_scale = has_js_dual_axis_scale or has_css_dual_axis_scale

    has_centered_anchor = (
        bool(re.search(r"left\s*[:=]\s*[\"']?50%", combined_code, flags=re.IGNORECASE))
        and bool(re.search(r"top\s*[:=]\s*[\"']?50%", combined_code, flags=re.IGNORECASE))
        and bool(
            re.search(
                r"translate(?:3d)?\s*\(\s*-50%\s*,\s*-50%",
                combined_code,
                flags=re.IGNORECASE,
            )
        )
    )

    issues: List[str] = []
    if not has_dual_axis_scale:
        issues.append(
            "Fixed-pixel canvas (>=1200x700px) missing standalone dual-axis viewport auto-fit scale "
            "(Math.min(innerWidth/W, innerHeight/H) -> scale(...) or CSS 100vw/100vh scale); "
            "slide overflows laptop screens at 125%/150% DPI and forces manual zooming"
        )
    if not has_doc_overflow_hidden:
        issues.append(
            "Fixed-pixel canvas (>=1200x700px) missing html/body overflow:hidden viewport containment; "
            "unscaled layout box triggers browser scrollbars"
        )
    if not has_centered_anchor:
        issues.append(
            "Fixed-pixel canvas (>=1200x700px) missing centered viewport anchor "
            "(left: 50%; top: 50%; transform: translate(-50%, -50%) scale(...)); "
            "grid/flex centering clips left/top edges when viewport < canvas size"
        )

    return {
        "passed": len(issues) == 0,
        "has_fixed_pixel_canvas": True,
        "has_dual_axis_scale": has_dual_axis_scale,
        "has_doc_overflow_hidden": has_doc_overflow_hidden,
        "has_centered_anchor": has_centered_anchor,
        "issues": issues,
    }


def audit_slide_html_density_and_viewport(html_text: str) -> Dict[str, Any]:
    """Combined HTML-level check for redundant SVG-to-card echo and viewport auto-fit."""
    echo_rep = audit_svg_sidecard_echo_and_density(html_text)
    vp_rep = audit_fixed_canvas_viewport_autofit(html_text)
    issues = list(echo_rep["issues"]) + list(vp_rep["issues"])
    return {
        "passed": len(issues) == 0,
        "svg_sidecard_echo": echo_rep,
        "viewport_autofit": vp_rep,
        "issues": issues,
    }
