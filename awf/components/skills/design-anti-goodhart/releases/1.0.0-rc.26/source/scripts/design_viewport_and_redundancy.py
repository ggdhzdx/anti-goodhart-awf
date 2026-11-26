"""
HTML-Level Slide Redundancy, Single-Slide Character Budget, Inline-SVG & HTML DOM Typography,
Hollow Text-Card Underfill & Fixed-Canvas Viewport Auto-Fit Guards
(`skill.design-anti-goodhart@1.0.0-rc.18`).

Enforces four structural anti-Goodhart invariants directly on raw slide HTML (`html_text`):
1. `SVG_SideCard_Redundant_Echo_Guard`: Blocks slides where a self-labeled `<svg>` diagram
   already carries dense text/metrics yet the author also stacks verbose `<article>` or
   card/paragraph blocks repeating or crowding the canvas.
2. `Inline_SVG_Typography_And_Slide_Char_Budget_Guard`:
   - Enforces `MIN_INLINE_SVG_FONT_PX = 18.0` across all inline `<svg>` text elements
     (checking `font-size` attributes, inline `style="font-size:..."`, `<style>` rules,
     missing `font-size` browser-16px fallbacks, and `viewBox` coordinate downscaling);
   - Caps single-slide visible characters (`MAX_VISIBLE_CHARS_PER_SLIDE = 650`, excluding
     `<head>`, `<script>`, `<style>`, `<aside class="notes">`, and hidden `.term-popover` tips);
   - Caps inline `<svg>` `<text>` nodes per slide (`MAX_INLINE_SVG_SUBSTANTIVE_LABELS = 22`,
     `MAX_INLINE_SVG_TOTAL_TEXT_NODES = 30`) so authors cannot stuff 3+ sub-diagrams into 1 SVG.
3. `HTML_DOM_Typography_And_Hollow_Card_Underfill_Guard`:
   - Enforces `MIN_VISIBLE_HTML_FONT_PX = 18.0` across all visible HTML `<style>` rules and
     inline `style="font-size:..."` attributes (blocking tiny 15–17px kickers, badges, and footers);
   - Enforces canvas-proportional body/card paragraph & list font floors (`>= 22.0px` on `1920x1080`
     HD canvases, `>= 20.0px` on `1600x900` canvases) so `<p>`/`<li>` copy never shrinks into tiny text;
   - Blocks hollow pure-text cards (`justify-content: space-between` tearing a blank chasm between a
     1-line header and a short paragraph, or explicit `height >= 220px` boxes holding sparse `< 95`-char
     copy with `> 55%` empty box whitespace).
4. `Fixed_Canvas_Viewport_AutoFit_Guard`: Blocks fixed pixel canvases (`>=1200x700px`) lacking
   standalone dual-axis viewport scaling, `overflow: hidden`, and `50%/50%` centered anchoring.
"""

from __future__ import annotations

from html.parser import HTMLParser
import re
from typing import Any, Dict, List, Optional, Set, Tuple

MIN_FIXED_CANVAS_WIDTH_PX = 1200
MIN_FIXED_CANVAS_HEIGHT_PX = 700
MIN_SUBSTANTIVE_SVG_LABEL_CHARS = 3
MIN_SELF_LABELED_SVG_TEXTS = 6
MAX_DENSE_SVG_TEXTS_WITH_CARDS = 12
MIN_REDUNDANT_CARD_COUNT = 3
MIN_VERBOSE_SIDECARD_CHARS = 90
MAX_SVG_CARD_REPEATED_NUMS = 4
MAX_SVG_CARD_SHARED_TRIGRAMS = 7
CJK_TRIGRAM_LEN = 3

MIN_INLINE_SVG_FONT_PX = 32.0
MIN_VISIBLE_HTML_FONT_PX = 32.0
HD_CANVAS_WIDTH_THRESHOLD_PX = 1800.0
MIN_HD_CARD_BODY_FONT_PX = 42.0
MIN_STD_CARD_BODY_FONT_PX = 36.0
MIN_HD_SLIDE_TITLE_FONT_PX = 56.0
HOLLOW_CARD_MIN_HEIGHT_PX = 220.0
HOLLOW_CARD_SPARSE_TEXT_CHARS = 24
HOLLOW_CARD_MAX_DIRECT_BLOCKS = 2
MIN_MULTI_BUTTON_WIDGET_COUNT = 2
BROWSER_DEFAULT_SVG_FONT_PX = 16.0
MAX_VISIBLE_CHARS_PER_SLIDE = 260
MAX_INLINE_SVG_SUBSTANTIVE_LABELS = 10
MAX_INLINE_SVG_TOTAL_TEXT_NODES = 14
MAX_NON_SVG_BODY_CHARS_WITH_DENSE_SVG = 110
DEFAULT_SLIDE_CANVAS_WIDTH_PX = 1920.0
SAMPLE_PREVIEW_LIMIT = 5
LABEL_SNIPPET_MAX_CHARS = 24

HTML_VOID_ELEMENTS = frozenset(
    {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
)

AXIS_TICK_ONLY_RE = re.compile(r"^[+-]?\d+(?:\.\d+)?%?$")
QUANT_TOKEN_RE = re.compile(
    r"\d+(?:\.\d+)?\s*(?:%|µm|μm|nm|mm|cm|meV|eV|mV|V|mA|h|ps|ns|µs|μs|°C|K|Å|倍)"
)
CJK_RUN_RE = re.compile(r"[\u4e00-\u9fff]+")
FONT_SIZE_DECL_RE = re.compile(r"font-size\s*:\s*(\d+(?:\.\d+)?)\s*(?:px)?\b", re.IGNORECASE)
NUMERIC_PX_RE = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*(?:px)?\s*$", re.IGNORECASE)
SIGNED_FLOAT_RE = re.compile(r"^[+-]?\d+(?:\.\d+)?$")


def _strip_non_canvas_blocks(html_text: str) -> str:
    cleaned = re.sub(r"<head\b[^>]*>.*?</head>", " ", html_text, flags=re.DOTALL | re.IGNORECASE)
    cleaned = re.sub(r"<script\b[^>]*>.*?</script>", " ", cleaned, flags=re.DOTALL | re.IGNORECASE)
    cleaned = re.sub(r"<style\b[^>]*>.*?</style>", " ", cleaned, flags=re.DOTALL | re.IGNORECASE)
    cleaned = re.sub(r"<template\b[^>]*>.*?</template>", " ", cleaned, flags=re.DOTALL | re.IGNORECASE)
    cleaned = re.sub(
        r"<(?:aside|div|section)\b[^>]*class=[\"'][^\"']*\b(?:notes|term-popover|detail-popover|evidence-modal|teleprompter)\b[^\"']*[\"'][^>]*>.*?</(?:aside|div|section)>",
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


def _extract_font_px_from_attrs(attr_map: Dict[str, Optional[str]]) -> Optional[float]:
    style_val = attr_map.get("style") or ""
    style_matches = FONT_SIZE_DECL_RE.findall(style_val)
    if style_matches:
        return float(style_matches[-1])
    attr_fs = attr_map.get("font-size")
    if attr_fs is not None:
        m = NUMERIC_PX_RE.match(attr_fs)
        if m:
            return float(m.group(1))
    return None


def _extract_css_svg_text_font_px(html_text: str) -> Tuple[Optional[float], List[float]]:
    style_blocks = re.findall(r"<style\b[^>]*>(.*?)</style>", html_text, flags=re.DOTALL | re.IGNORECASE)
    css_text = "\n".join(style_blocks)
    css_text = re.sub(r"/\*.*?\*/", " ", css_text, flags=re.DOTALL)
    svg_text_sizes: List[float] = []
    undersized_css: List[float] = []
    for selector_raw, body_raw in re.findall(r"([^{}]+)\{([^{}]+)\}", css_text):
        selectors = [s.strip().lower() for s in selector_raw.split(",") if s.strip()]
        targets_svg_text = any(
            ("svg" in sel and "text" in sel) or sel == "text" or sel.endswith(" text")
            for sel in selectors
        )
        if not targets_svg_text:
            continue
        for fs_str in FONT_SIZE_DECL_RE.findall(body_raw):
            val = float(fs_str)
            svg_text_sizes.append(val)
            if val < MIN_INLINE_SVG_FONT_PX:
                undersized_css.append(val)
    fallback_px = min(svg_text_sizes) if svg_text_sizes else None
    return fallback_px, undersized_css


def _compute_svg_coord_scale(attr_map: Dict[str, Optional[str]], canvas_width_px: float) -> float:
    vb_raw = (attr_map.get("viewbox") or "").strip()
    if not vb_raw:
        return 1.0
    parts = [p for p in re.split(r"[\s,]+", vb_raw) if p]
    if len(parts) != 4 or not SIGNED_FLOAT_RE.match(parts[2]):
        return 1.0
    vb_w = float(parts[2])
    if vb_w <= 0.0:
        return 1.0
    explicit_w_raw = (attr_map.get("width") or "").strip()
    m_w = NUMERIC_PX_RE.match(explicit_w_raw) if explicit_w_raw and "%" not in explicit_w_raw else None
    rendered_w = float(m_w.group(1)) if m_w else min(canvas_width_px, vb_w)
    if vb_w > canvas_width_px and m_w is None:
        rendered_w = canvas_width_px
    return min(1.0, rendered_w / vb_w)


def _new_slide_bucket(slide_no: int) -> Dict[str, Any]:
    return {
        "slide_no": slide_no,
        "visible_chunks": [],
        "non_svg_body_chunks": [],
        "svg_total_text_count": 0,
        "svg_substantive_labels": [],
        "min_raw_svg_font_px": None,
        "min_effective_svg_font_px": None,
        "undersized_svg_samples": [],
        "missing_font_svg_samples": [],
    }


class _SlideCanvasDOMInspector(HTMLParser):
    """DOM-aware inspector tracking per-slide visible characters and inline `<svg>` typography."""

    def __init__(self, css_svg_text_px: Optional[float], canvas_width_px: float) -> None:
        super().__init__(convert_charrefs=True)
        self.css_svg_text_px = css_svg_text_px
        self.canvas_width_px = canvas_width_px
        self.slides: List[Dict[str, Any]] = []
        self._active_slide: Optional[Dict[str, Any]] = None
        self._slide_depth = 0
        self._ignored_depth = 0
        self._header_footer_depth = 0
        self._svg_depth = 0
        self._svg_coord_scale = 1.0
        self._svg_font_stack: List[Optional[float]] = []
        self._in_svg_text_depth = 0
        self._current_text_parts: List[str] = []
        self._current_text_min_px: Optional[float] = None
        self._current_text_missing_fs = False
        self._tag_trail: List[Tuple[str, str]] = []

    def _ensure_bucket(self) -> Dict[str, Any]:
        if self._active_slide is None:
            bucket = _new_slide_bucket(len(self.slides) + 1)
            self.slides.append(bucket)
            self._active_slide = bucket
        return self._active_slide

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        t = tag.lower()
        if t in HTML_VOID_ELEMENTS:
            return
        attr_map = {k.lower(): v for k, v in attrs}
        cls_tokens = set((attr_map.get("class") or "").lower().split())
        is_hidden = (
            t in {"head", "script", "style", "template"}
            or ("hidden" in attr_map)
            or ("data-popover-modal" in attr_map)
            or ("data-popover-id" in attr_map)
            or (t == "aside" and "notes" in cls_tokens)
            or bool(cls_tokens & {"term-popover", "detail-popover", "evidence-modal", "teleprompter"})
        )
        if self._ignored_depth > 0 or is_hidden:
            self._ignored_depth += 1
            self._tag_trail.append((t, "ignored"))
            return

        role = "normal"
        if self._slide_depth == 0 and "slide" in cls_tokens and t in {"section", "div", "article", "main"}:
            self._slide_depth = 1
            bucket = _new_slide_bucket(len(self.slides) + 1)
            self.slides.append(bucket)
            self._active_slide = bucket
            role = "slide_root"
        elif self._slide_depth > 0:
            self._slide_depth += 1

        if t in {"header", "footer"} or "slide-header" in cls_tokens or "takeaway-strip" in cls_tokens:
            self._header_footer_depth += 1
            role = "header_footer" if role == "normal" else role

        if t == "svg":
            self._svg_depth += 1
            if self._svg_depth == 1:
                self._svg_coord_scale = _compute_svg_coord_scale(attr_map, self.canvas_width_px)
            own_fs = _extract_font_px_from_attrs(attr_map)
            inherited = self._svg_font_stack[-1] if self._svg_font_stack else self.css_svg_text_px
            self._svg_font_stack.append(own_fs if own_fs is not None else inherited)
            role = "svg_node"
        elif self._svg_depth > 0:
            own_fs = _extract_font_px_from_attrs(attr_map)
            inherited = self._svg_font_stack[-1] if self._svg_font_stack else self.css_svg_text_px
            resolved_fs = own_fs if own_fs is not None else inherited
            self._svg_font_stack.append(resolved_fs)
            if t == "text":
                self._in_svg_text_depth += 1
                if self._in_svg_text_depth == 1:
                    self._current_text_parts = []
                    self._current_text_min_px = resolved_fs
                    self._current_text_missing_fs = resolved_fs is None
            elif t == "tspan" and self._in_svg_text_depth > 0:
                if resolved_fs is None:
                    self._current_text_missing_fs = True
                elif self._current_text_min_px is None or resolved_fs < self._current_text_min_px:
                    self._current_text_min_px = resolved_fs
            role = "svg_child"

        self._tag_trail.append((t, role))

    def handle_endtag(self, tag: str) -> None:
        t = tag.lower()
        if t in HTML_VOID_ELEMENTS or not self._tag_trail:
            return
        _, role = self._tag_trail.pop()
        if role == "ignored":
            self._ignored_depth = max(0, self._ignored_depth - 1)
            return

        if role in {"svg_node", "svg_child"} and self._svg_depth > 0:
            if t == "text" and self._in_svg_text_depth > 0:
                self._in_svg_text_depth -= 1
                if self._in_svg_text_depth == 0:
                    self._finalize_svg_text_node()
            if self._svg_font_stack:
                self._svg_font_stack.pop()
            if t == "svg":
                self._svg_depth = max(0, self._svg_depth - 1)
                if self._svg_depth == 0:
                    self._svg_coord_scale = 1.0

        if role == "header_footer" or (
            t in {"header", "footer"} and self._header_footer_depth > 0
        ):
            self._header_footer_depth = max(0, self._header_footer_depth - 1)

        if self._slide_depth > 0:
            self._slide_depth -= 1
            if self._slide_depth == 0:
                self._active_slide = None

    def handle_data(self, data: str) -> None:
        if self._ignored_depth > 0:
            return
        compact = re.sub(r"\s+", "", data)
        if not compact:
            return
        bucket = self._ensure_bucket()
        bucket["visible_chunks"].append(compact)
        if self._svg_depth == 0 and self._header_footer_depth == 0:
            bucket["non_svg_body_chunks"].append(compact)
        if self._in_svg_text_depth > 0:
            self._current_text_parts.append(data)

    def _finalize_svg_text_node(self) -> None:
        label = re.sub(r"\s+", " ", "".join(self._current_text_parts)).strip()
        if not label:
            return
        bucket = self._ensure_bucket()
        bucket["svg_total_text_count"] += 1
        if len(label) >= MIN_SUBSTANTIVE_SVG_LABEL_CHARS and not AXIS_TICK_ONLY_RE.match(label):
            bucket["svg_substantive_labels"].append(label)

        snippet = label[:LABEL_SNIPPET_MAX_CHARS]
        raw_px = self._current_text_min_px
        if raw_px is None or self._current_text_missing_fs:
            if len(bucket["missing_font_svg_samples"]) < SAMPLE_PREVIEW_LIMIT:
                bucket["missing_font_svg_samples"].append(snippet)
            raw_px = BROWSER_DEFAULT_SVG_FONT_PX

        eff_px = round(raw_px * self._svg_coord_scale, 2)
        prev_raw = bucket["min_raw_svg_font_px"]
        if prev_raw is None or raw_px < prev_raw:
            bucket["min_raw_svg_font_px"] = raw_px
        prev_eff = bucket["min_effective_svg_font_px"]
        if prev_eff is None or eff_px < prev_eff:
            bucket["min_effective_svg_font_px"] = eff_px

        if eff_px < MIN_INLINE_SVG_FONT_PX and len(bucket["undersized_svg_samples"]) < SAMPLE_PREVIEW_LIMIT:
            bucket["undersized_svg_samples"].append(f"'{snippet}' ({eff_px:.1f}px < {MIN_INLINE_SVG_FONT_PX:.1f}px)")


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
                f"numbers {repeated_nums[:SAMPLE_PREVIEW_LIMIT]} — remove redundant side-cards and let the chart breathe"
            )
        if len(shared_trigrams) > MAX_SVG_CARD_SHARED_TRIGRAMS:
            issues.append(
                f"Redundant SVG-to-card text echo: {article_count} <article> cards repeat {len(shared_trigrams)} "
                f"CJK phrases {shared_trigrams[:SAMPLE_PREVIEW_LIMIT]} already printed inside <svg>"
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


def _detect_canvas_width_px(style_css: str) -> float:
    widths = [
        int(m)
        for m in re.findall(
            r"(?:--canvas-w(?:idth)?|(?<![a-zA-Z-])width)\s*:\s*(\d{3,4})px",
            style_css,
            flags=re.IGNORECASE,
        )
    ]
    large = [float(w) for w in widths if w >= MIN_FIXED_CANVAS_WIDTH_PX]
    return max(large) if large else DEFAULT_SLIDE_CANVAS_WIDTH_PX


def audit_inline_svg_typography_and_char_budget(html_text: str) -> Dict[str, Any]:
    """
    Enforce inline `<svg>` minimum font size >= 18px (`MIN_INLINE_SVG_FONT_PX`), per-slide
    visible character cap (`MAX_VISIBLE_CHARS_PER_SLIDE`), inline `<svg>` `<text>` count caps,
    and dense-SVG + verbose-body-card crowding prevention across every slide segment.
    """
    style_css = " ".join(
        re.findall(r"<style\b[^>]*>(.*?)</style>", html_text, flags=re.DOTALL | re.IGNORECASE)
    )
    canvas_w = _detect_canvas_width_px(style_css)
    css_svg_px, undersized_css_rules = _extract_css_svg_text_font_px(html_text)

    segments = (
        [seg for seg in html_text.split("<!-- SLIDE_BOUNDARY -->") if seg.strip()]
        if "<!-- SLIDE_BOUNDARY -->" in html_text
        else [html_text]
    )
    slide_buckets: List[Dict[str, Any]] = []
    for seg in segments:
        seg_css_px, _ = _extract_css_svg_text_font_px(seg)
        eff_css_px = seg_css_px if seg_css_px is not None else css_svg_px
        inspector = _SlideCanvasDOMInspector(eff_css_px, canvas_w)
        inspector.feed(seg)
        for b in inspector.slides:
            b["slide_no"] = len(slide_buckets) + 1
            slide_buckets.append(b)

    issues: List[str] = []
    if undersized_css_rules:
        issues.append(
            f"CSS rule sets inline <svg> text font-size {min(undersized_css_rules):.1f}px < "
            f"{MIN_INLINE_SVG_FONT_PX:.1f}px minimum legibility floor"
        )

    max_vis_chars = 0
    max_svg_texts = 0
    global_min_svg_px: Optional[float] = None

    for b in slide_buckets:
        sno = b["slide_no"]
        vis_chars = sum(len(c) for c in b["visible_chunks"])
        non_svg_body_chars = sum(len(c) for c in b["non_svg_body_chunks"])
        svg_total = b["svg_total_text_count"]
        svg_sub_count = len(b["svg_substantive_labels"])
        min_eff_px = b["min_effective_svg_font_px"]

        max_vis_chars = max(max_vis_chars, vis_chars)
        max_svg_texts = max(max_svg_texts, svg_total)
        if min_eff_px is not None and (global_min_svg_px is None or min_eff_px < global_min_svg_px):
            global_min_svg_px = min_eff_px

        if b["missing_font_svg_samples"]:
            issues.append(
                f"Slide {sno}: inline <svg> <text> {b['missing_font_svg_samples']} omits explicit font-size "
                f"(browser default {BROWSER_DEFAULT_SVG_FONT_PX:.0f}px < {MIN_INLINE_SVG_FONT_PX:.0f}px floor)"
            )
        if b["undersized_svg_samples"]:
            issues.append(
                f"Slide {sno}: inline <svg> font-size below {MIN_INLINE_SVG_FONT_PX:.0f}px floor: "
                f"{', '.join(b['undersized_svg_samples'])}"
            )
        if vis_chars > MAX_VISIBLE_CHARS_PER_SLIDE:
            issues.append(
                f"Slide {sno}: single-slide visible character count {vis_chars} > {MAX_VISIBLE_CHARS_PER_SLIDE} "
                "hard cap — split into multiple slides instead of crowding one canvas"
            )
        if svg_sub_count > MAX_INLINE_SVG_SUBSTANTIVE_LABELS or svg_total > MAX_INLINE_SVG_TOTAL_TEXT_NODES:
            issues.append(
                f"Slide {sno}: inline <svg> text overload ({svg_sub_count} substantive labels / {svg_total} total "
                f"<text> nodes exceeds {MAX_INLINE_SVG_SUBSTANTIVE_LABELS}/{MAX_INLINE_SVG_TOTAL_TEXT_NODES} cap) "
                "— do not pack multiple sub-diagrams into one <svg>"
            )
        if svg_sub_count >= MIN_SELF_LABELED_SVG_TEXTS and non_svg_body_chars > MAX_NON_SVG_BODY_CHARS_WITH_DENSE_SVG:
            issues.append(
                f"Slide {sno}: self-labeled <svg> ({svg_sub_count} labels) paired with {non_svg_body_chars} chars "
                f"of non-SVG body/card copy (> {MAX_NON_SVG_BODY_CHARS_WITH_DENSE_SVG}) overloads the slide; "
                "split cards onto a dedicated slide or remove redundant prose"
            )

    return {
        "passed": len(issues) == 0,
        "min_inline_svg_font_px_floor": MIN_INLINE_SVG_FONT_PX,
        "observed_min_inline_svg_font_px": global_min_svg_px,
        "max_observed_visible_chars_per_slide": max_vis_chars,
        "max_allowed_visible_chars_per_slide": MAX_VISIBLE_CHARS_PER_SLIDE,
        "max_observed_svg_text_nodes_per_slide": max_svg_texts,
        "slides_inspected": len(slide_buckets),
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


def _strip_css_at_blocks(css_text: str) -> str:
    """Remove @keyframes and @media blocks so rule scanning inspects normal element selectors."""
    out: List[str] = []
    idx = 0
    n = len(css_text)
    while idx < n:
        if css_text[idx] == "@":
            brace_pos = css_text.find("{", idx)
            semi_pos = css_text.find(";", idx)
            if semi_pos != -1 and (brace_pos == -1 or semi_pos < brace_pos):
                idx = semi_pos + 1
                continue
            if brace_pos == -1:
                break
            depth = 1
            pos = brace_pos + 1
            while pos < n and depth > 0:
                if css_text[pos] == "{":
                    depth += 1
                elif css_text[pos] == "}":
                    depth -= 1
                pos += 1
            idx = pos
            continue
        out.append(css_text[idx])
        idx += 1
    return "".join(out)


def _selector_is_hidden_or_svg_or_pseudo(sel: str) -> bool:
    if "::before" in sel or "::after" in sel or ":before" in sel or ":after" in sel:
        return True
    if any(
        tok in sel
        for tok in (".notes", "#teleprompter", ".teleprompter", ".term-popover", ".detail-popover", ".evidence-modal", "[hidden]")
    ):
        return True
    return ("svg" in sel) or sel == "text" or sel.endswith(" text") or sel == "tspan" or sel.endswith(" tspan")


def _selector_targets_slide_title(sel: str) -> bool:
    tokens = [t for t in re.split(r"[\s>+~]+", sel) if t]
    if not tokens:
        return False
    leaf = tokens[-1]
    return leaf == "h1" or ".slide-title" in leaf


def _selector_targets_card_body_copy(sel: str) -> bool:
    if any(tok in sel for tok in ("header", "footer", ".hdr-meta", ".takeaway-strip", ".source", ".lead")):
        return False
    tokens = [t for t in re.split(r"[\s>+~]+", sel) if t]
    if not tokens:
        return False
    leaf = tokens[-1]
    return leaf in {"p", "li"}


def _audit_css_html_font_and_card_rules(
    html_text: str,
    has_fixed_canvas: bool,
    canvas_w: float,
) -> Tuple[Optional[float], Set[str], List[str]]:
    style_blocks = re.findall(r"<style\b[^>]*>(.*?)</style>", html_text, flags=re.DOTALL | re.IGNORECASE)
    raw_css = re.sub(r"/\*.*?\*/", " ", "\n".join(style_blocks), flags=re.DOTALL)
    flat_css = _strip_css_at_blocks(raw_css)
    body_floor = (
        MIN_HD_CARD_BODY_FONT_PX if canvas_w >= HD_CANVAS_WIDTH_THRESHOLD_PX else MIN_STD_CARD_BODY_FONT_PX
    )

    min_css_px: Optional[float] = None
    space_between_classes: Set[str] = set()
    issues: List[str] = []

    for selector_raw, body_raw in re.findall(r"([^{}]+)\{([^{}]+)\}", flat_css):
        selectors = [s.strip().lower() for s in selector_raw.split(",") if s.strip()]
        if re.search(r"justify-content\s*:\s*space-between", body_raw, flags=re.IGNORECASE):
            for sel in selectors:
                for cls_name in re.findall(r"\.([a-z0-9_-]+)", sel):
                    if cls_name in {"panel", "card"} and " " not in sel:
                        space_between_classes.add(cls_name)

        visible_sels = [s for s in selectors if not _selector_is_hidden_or_svg_or_pseudo(s)]
        if not visible_sels:
            continue

        sel_preview = ", ".join(visible_sels)[:LABEL_SNIPPET_MAX_CHARS]
        targets_body = any(_selector_targets_card_body_copy(s) for s in visible_sels)
        targets_title = any(_selector_targets_slide_title(s) for s in visible_sels)
        for fs_str in FONT_SIZE_DECL_RE.findall(body_raw):
            val = float(fs_str)
            if min_css_px is None or val < min_css_px:
                min_css_px = val
            if val < MIN_VISIBLE_HTML_FONT_PX and len(issues) < SAMPLE_PREVIEW_LIMIT:
                issues.append(
                    f"CSS selector '{sel_preview}' sets font-size {val:.1f}px < "
                    f"{MIN_VISIBLE_HTML_FONT_PX:.1f}px minimum visible HTML legibility floor"
                )
            elif has_fixed_canvas and targets_body and val < body_floor and len(issues) < SAMPLE_PREVIEW_LIMIT:
                issues.append(
                    f"CSS selector '{sel_preview}' sets body/card font-size {val:.1f}px < "
                    f"{body_floor:.1f}px floor on {int(canvas_w)}px canvas"
                )
            elif (
                has_fixed_canvas
                and canvas_w >= HD_CANVAS_WIDTH_THRESHOLD_PX
                and targets_title
                and val < MIN_HD_SLIDE_TITLE_FONT_PX
                and len(issues) < SAMPLE_PREVIEW_LIMIT
            ):
                issues.append(
                    f"CSS selector '{sel_preview}' sets slide title font-size {val:.1f}px < "
                    f"{MIN_HD_SLIDE_TITLE_FONT_PX:.1f}px HD title floor"
                )

    return min_css_px, space_between_classes, issues


def _extract_inline_height_px(style_val: str) -> Optional[float]:
    matches = re.findall(r"(?<![a-zA-Z-])(?:min-)?height\s*:\s*(\d+(?:\.\d+)?)\s*px", style_val, flags=re.IGNORECASE)
    return float(matches[-1]) if matches else None


class _HTMLCardAndInlineFontInspector(HTMLParser):
    """Inspect inline HTML font-sizes and detect hollow/under-filled pure-text cards."""

    def __init__(
        self,
        slide_no: int,
        has_fixed_canvas: bool,
        canvas_w: float,
        space_between_classes: Set[str],
    ) -> None:
        super().__init__(convert_charrefs=True)
        self.slide_no = slide_no
        self.has_fixed_canvas = has_fixed_canvas
        self.body_floor = (
            MIN_HD_CARD_BODY_FONT_PX if canvas_w >= HD_CANVAS_WIDTH_THRESHOLD_PX else MIN_STD_CARD_BODY_FONT_PX
        )
        self.canvas_w = canvas_w
        self.space_between_classes = space_between_classes
        self.min_inline_px: Optional[float] = None
        self.issues: List[str] = []
        self._ignored_depth = 0
        self._header_footer_depth = 0
        self._grid_heights: List[Optional[float]] = []
        self._card_stack: List[Dict[str, Any]] = []
        self._trail: List[str] = []

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        t = tag.lower()
        attr_map = {k.lower(): (v or "") for k, v in attrs}
        cls_tokens = set(attr_map.get("class", "").lower().split())
        style_val = attr_map.get("style", "")

        if t in HTML_VOID_ELEMENTS:
            if self._ignored_depth == 0 and self._card_stack and t in {"img", "input"}:
                self._card_stack[-1]["has_rich_media"] = True
            return

        is_ignored = (
            t in {"head", "script", "style", "template", "svg"}
            or ("hidden" in attr_map)
            or ("data-popover-modal" in attr_map)
            or ("data-popover-id" in attr_map)
            or (t == "aside" and "notes" in cls_tokens)
            or bool(cls_tokens & {"term-popover", "detail-popover", "evidence-modal", "teleprompter"})
            or ("teleprompter" in attr_map.get("id", "").lower())
        )
        if self._ignored_depth == 0 and t == "svg" and self._card_stack:
            self._card_stack[-1]["has_rich_media"] = True
        if self._ignored_depth > 0 or is_ignored:
            self._ignored_depth += 1
            self._trail.append("ignored")
            return

        role = "normal"
        if t in {"header", "footer"} or bool(cls_tokens & {"slide-header", "page-header", "takeaway-strip", "page-footer"}):
            self._header_footer_depth += 1
            role = "header_footer"

        is_grid_row = any(c.startswith("grid-") or c == "content" for c in cls_tokens)
        if is_grid_row:
            self._grid_heights.append(_extract_inline_height_px(style_val))
            role = "grid_row"

        if self._card_stack:
            top_card = self._card_stack[-1]
            top_card["inner_depth"] += 1
            if top_card["inner_depth"] == 1:
                top_card["direct_blocks"] += 1
                if t in {"h2", "h3", "header"} or "panel-hdr" in cls_tokens:
                    top_card["in_card_hdr_depth"] = 1
            elif top_card["in_card_hdr_depth"] > 0:
                top_card["in_card_hdr_depth"] += 1
            if t in {"table", "canvas", "select", "textarea", "video"}:
                top_card["has_rich_media"] = True
            elif t == "button":
                top_card["button_count"] += 1
                if top_card["button_count"] >= MIN_MULTI_BUTTON_WIDGET_COUNT:
                    top_card["has_rich_media"] = True

        is_card = (t == "article") or bool(cls_tokens & {"panel", "card"})
        if is_card:
            own_h = _extract_inline_height_px(style_val)
            inh_h = self._grid_heights[-1] if self._grid_heights else None
            inline_sb = bool(re.search(r"justify-content\s*:\s*space-between", style_val, flags=re.IGNORECASE))
            inline_override_just = bool(
                re.search(r"justify-content\s*:\s*(?!space-between)[a-z-]+", style_val, flags=re.IGNORECASE)
            )
            uses_sb = inline_sb or (bool(cls_tokens & self.space_between_classes) and not inline_override_just)
            self._card_stack.append({
                "inner_depth": 0,
                "in_card_hdr_depth": 0,
                "direct_blocks": 0,
                "button_count": 0,
                "has_rich_media": False,
                "title_parts": [],
                "body_parts": [],
                "min_body_font_px": None,
                "height_px": own_h if own_h is not None else inh_h,
                "uses_space_between": uses_sb,
            })
            role = "card_grid" if role == "grid_row" else "card"

        fs_matches = FONT_SIZE_DECL_RE.findall(style_val)
        if fs_matches:
            fs_px = float(fs_matches[-1])
            if self._card_stack and t in {"p", "li"}:
                cur_cfs = self._card_stack[-1]["min_body_font_px"]
                if cur_cfs is None or fs_px < cur_cfs:
                    self._card_stack[-1]["min_body_font_px"] = fs_px
            if self.min_inline_px is None or fs_px < self.min_inline_px:
                self.min_inline_px = fs_px
            if fs_px < MIN_VISIBLE_HTML_FONT_PX and len(self.issues) < SAMPLE_PREVIEW_LIMIT:
                self.issues.append(
                    f"Slide {self.slide_no}: visible <{t}> sets inline font-size {fs_px:.1f}px < "
                    f"{MIN_VISIBLE_HTML_FONT_PX:.1f}px minimum legibility floor"
                )
            elif (
                self.has_fixed_canvas
                and self._header_footer_depth == 0
                and t in {"p", "li"}
                and fs_px < self.body_floor
                and len(self.issues) < SAMPLE_PREVIEW_LIMIT
            ):
                self.issues.append(
                    f"Slide {self.slide_no}: card/body <{t}> uses undersized {fs_px:.1f}px font on "
                    f"{int(self.canvas_w)}px canvas (must be >= {self.body_floor:.0f}px; enlarge text instead of leaving blank box space)"
                )

        self._trail.append(role)

    def handle_endtag(self, tag: str) -> None:
        t = tag.lower()
        if t in HTML_VOID_ELEMENTS or not self._trail:
            return
        role = self._trail.pop()
        if role == "ignored":
            self._ignored_depth = max(0, self._ignored_depth - 1)
            return

        if role in {"card", "card_grid"} and self._card_stack:
            card = self._card_stack.pop()
            self._finalize_card(card)
        if role in {"grid_row", "card_grid"} and self._grid_heights:
            self._grid_heights.pop()
        if role == "header_footer":
            self._header_footer_depth = max(0, self._header_footer_depth - 1)

        if self._card_stack:
            top_card = self._card_stack[-1]
            if top_card["in_card_hdr_depth"] > 0:
                top_card["in_card_hdr_depth"] -= 1
            top_card["inner_depth"] = max(0, top_card["inner_depth"] - 1)

    def handle_data(self, data: str) -> None:
        if self._ignored_depth > 0 or not self._card_stack:
            return
        compact = re.sub(r"\s+", "", data)
        if not compact:
            return
        top_card = self._card_stack[-1]
        if top_card["in_card_hdr_depth"] > 0:
            top_card["title_parts"].append(compact)
        else:
            top_card["body_parts"].append(compact)

    def _finalize_card(self, card: Dict[str, Any]) -> None:
        if card["has_rich_media"]:
            return
        body_chars = sum(len(x) for x in card["body_parts"])
        if body_chars == 0:
            return
        preview = ("".join(card["title_parts"]) or "".join(card["body_parts"]))[:LABEL_SNIPPET_MAX_CHARS]
        if (
            card["uses_space_between"]
            and card["direct_blocks"] <= HOLLOW_CARD_MAX_DIRECT_BLOCKS
            and len(self.issues) < SAMPLE_PREVIEW_LIMIT
        ):
            self.issues.append(
                f"Slide {self.slide_no}: pure-text card '{preview}' uses flex justify-content: space-between "
                f"with only {card['direct_blocks']} child blocks, tearing a hollow whitespace chasm between header and copy"
            )
        height_px = card["height_px"]
        card_fs = max(1.0, float(card["min_body_font_px"] or self.body_floor))
        sparse_char_floor = int(HOLLOW_CARD_SPARSE_TEXT_CHARS * ((self.body_floor / card_fs) ** 2))
        if (
            height_px is not None
            and height_px >= HOLLOW_CARD_MIN_HEIGHT_PX
            and body_chars < sparse_char_floor
            and len(self.issues) < SAMPLE_PREVIEW_LIMIT
        ):
            self.issues.append(
                f"Slide {self.slide_no}: pure-text card '{preview}' sets explicit height {height_px:.0f}px "
                f"for only {body_chars} chars at {card_fs:.0f}px font, leaving >55% empty box whitespace — enlarge font (>={self.body_floor:.0f}px) and hug content"
            )


def audit_html_typography_and_card_fill(html_text: str) -> Dict[str, Any]:
    """
    Enforce visible HTML/CSS minimum font-size (>= 18px globally, >= 22px for body/card <p>/<li>
    on 1920x1080 canvases) and reject hollow fixed-height / `space-between` pure-text cards.
    """
    style_css = " ".join(
        re.findall(r"<style\b[^>]*>(.*?)</style>", html_text, flags=re.DOTALL | re.IGNORECASE)
    )
    has_fixed_canvas = _detect_fixed_pixel_canvas(style_css)
    canvas_w = _detect_canvas_width_px(style_css)
    min_css_px, sb_classes, css_issues = _audit_css_html_font_and_card_rules(html_text, has_fixed_canvas, canvas_w)

    segments = (
        [seg for seg in html_text.split("<!-- SLIDE_BOUNDARY -->") if seg.strip()]
        if "<!-- SLIDE_BOUNDARY -->" in html_text
        else [html_text]
    )
    issues = list(css_issues)
    min_observed_px = min_css_px
    for idx, seg in enumerate(segments, start=1):
        seg_css = " ".join(re.findall(r"<style\b[^>]*>(.*?)</style>", seg, flags=re.DOTALL | re.IGNORECASE))
        seg_fixed = _detect_fixed_pixel_canvas(seg_css) or has_fixed_canvas
        seg_w = _detect_canvas_width_px(seg_css) if seg_css.strip() else canvas_w
        _, seg_sb, _ = _audit_css_html_font_and_card_rules(seg, seg_fixed, seg_w)
        inspector = _HTMLCardAndInlineFontInspector(idx, seg_fixed, seg_w, sb_classes | seg_sb)
        inspector.feed(seg)
        if inspector.min_inline_px is not None and (min_observed_px is None or inspector.min_inline_px < min_observed_px):
            min_observed_px = inspector.min_inline_px
        issues.extend(inspector.issues)

    return {
        "passed": len(issues) == 0,
        "min_visible_html_font_px_floor": MIN_VISIBLE_HTML_FONT_PX,
        "observed_min_html_font_px": min_observed_px,
        "issues": issues,
    }


def audit_slide_html_density_and_viewport(html_text: str) -> Dict[str, Any]:
    """Combined HTML-level check for SVG-to-card echo, >=32px SVG & HTML typography, >=42px HD body, <=260 char budget, popovers & viewport fit."""
    from design_lossless_popover_and_split import audit_clickable_detail_popovers_and_triggers

    echo_rep = audit_svg_sidecard_echo_and_density(html_text)
    svg_typo_rep = audit_inline_svg_typography_and_char_budget(html_text)
    html_typo_rep = audit_html_typography_and_card_fill(html_text)
    vp_rep = audit_fixed_canvas_viewport_autofit(html_text)
    pop_rep = audit_clickable_detail_popovers_and_triggers(html_text)
    issues = (
        list(echo_rep["issues"])
        + list(svg_typo_rep["issues"])
        + list(html_typo_rep["issues"])
        + list(vp_rep["issues"])
        + list(pop_rep["issues"])
    )
    return {
        "passed": len(issues) == 0,
        "svg_sidecard_echo": echo_rep,
        "svg_typography_and_char_budget": svg_typo_rep,
        "html_typography_and_card_fill": html_typo_rep,
        "viewport_autofit": vp_rep,
        "clickable_popovers": pop_rep,
        "issues": issues,
    }
