"""
HTML-Level Slide Redundancy, Single-Slide Character Budget, Inline-SVG >=18px Typography
& Fixed-Canvas Viewport Auto-Fit Guards (`skill.design-anti-goodhart@1.0.0-rc.15`).

Enforces three structural anti-Goodhart invariants directly on raw slide HTML (`html_text`):
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
3. `Fixed_Canvas_Viewport_AutoFit_Guard`: Blocks fixed pixel canvases (`>=1200x700px`) lacking
   standalone dual-axis viewport scaling, `overflow: hidden`, and `50%/50%` centered anchoring.
"""

from __future__ import annotations

from html.parser import HTMLParser
import re
from typing import Any, Dict, List, Optional, Set, Tuple

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

MIN_INLINE_SVG_FONT_PX = 18.0
BROWSER_DEFAULT_SVG_FONT_PX = 16.0
MAX_VISIBLE_CHARS_PER_SLIDE = 650
MAX_INLINE_SVG_SUBSTANTIVE_LABELS = 22
MAX_INLINE_SVG_TOTAL_TEXT_NODES = 30
MAX_NON_SVG_BODY_CHARS_WITH_DENSE_SVG = 220
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
            or (t == "aside" and "notes" in cls_tokens)
            or ("term-popover" in cls_tokens)
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


def audit_slide_html_density_and_viewport(html_text: str) -> Dict[str, Any]:
    """Combined HTML-level check for SVG-to-card echo, >=18px SVG typography, char budget & viewport fit."""
    echo_rep = audit_svg_sidecard_echo_and_density(html_text)
    svg_typo_rep = audit_inline_svg_typography_and_char_budget(html_text)
    vp_rep = audit_fixed_canvas_viewport_autofit(html_text)
    issues = list(echo_rep["issues"]) + list(svg_typo_rep["issues"]) + list(vp_rep["issues"])
    return {
        "passed": len(issues) == 0,
        "svg_sidecard_echo": echo_rep,
        "svg_typography_and_char_budget": svg_typo_rep,
        "viewport_autofit": vp_rep,
        "issues": issues,
    }
