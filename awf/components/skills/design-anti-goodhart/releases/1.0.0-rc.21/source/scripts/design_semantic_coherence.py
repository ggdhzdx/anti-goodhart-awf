"""
Intra-Slide Semantic Coherence, Class-Agnostic Bottom-Ballast Row Detection, Bare-Noun Card Header
Rejection & Anti-Collusion Zero-Context Blind Reader Verification Engine
(`skill.design-anti-goodhart@1.0.0-rc.20`).

Eliminates Second-Order Goodhart Collapse ("satisfying geometric/acronym gates via disconnected
bottom 3-card / 3-metric-tag ballast strips") across four orthogonal layers:
1. `Class_Agnostic_DOM_Row_And_Bare_Noun_Strip_Guard` (`D3` / `D4` / `D6`):
   - Builds a structural DOM tree per slide (independent of CSS class names like `.grid-3`,
     `.panel`, or `.metric-box`) to inspect top-level content rows;
   - Rejects multi-box strips (`>= 3` sibling block cards/boxes) whose headings are bare verbless
     noun labels (`电子密度 Q 峰` / `热振动椭球 ADP` / `精修残差因子 R1`, `C–C 单键扭转能垒`);
   - Rejects any lower multi-box strip (`>= 3` text/metric boxes) placed beneath an upper `<svg>`/`<img>`
     visual row unless an explicit on-canvas bridge (`.semantic-bridge`, step-callout badge `④-1`,
     or directional pointer) links each box to the upper visual;
   - Caps deck-wide two-tier `upper-visual + lower-multi-box-strip` repetition (`<= 30%` of slides);
   - Rejects reviewer-bribery / prompt-injection strings on slides.
2. `BoundingBox_Bottom_Ballast_Strip_Probe` (`D8`):
   - Flags unanchored lower-canvas 3+ short-card ballast rows bolted beneath an upper visual.
3. `Intra_Slide_Semantic_Tree_Contract` (`D16`):
   - Requires every secondary block on a slide to declare `parent_anchor_target`, `relation_type`,
     and `on_canvas_bridge_marker`, forbidding unanchored trivia/glossary filler blocks.
4. `Anti_Collusion_Blind_Reader_Reconstruction_Protocol` (`D18`):
   - Audits `blind_prompt_sent` against coaching/sycophancy and answer-leakage;
   - Enforces `READONLY_PNG_BLIND_SUBAGENT` context isolation (`saw_source_pdf == False`);
   - Blocks rubber-stamp praise by requiring concrete topological reconstruction and visible bridge
     evidence cross-checked against Blue's pre-committed `intra_slide_semantic_tree`.
"""

from __future__ import annotations

from html.parser import HTMLParser
import re
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

MIN_MULTI_CARD_STRIP_ITEMS = 3
MIN_BARE_NOUN_SIBLING_HITS = 2
MAX_BARE_NOUN_HEADING_CHARS = 16
MIN_PROPOSITION_CLAIM_CHARS = 10
MIN_PRIMARY_SPINE_CHARS = 4
MIN_ANCHOR_TARGET_CHARS = 2
MIN_BRIDGE_MARKER_CHARS = 2
MAX_SECONDARY_BLOCKS_PER_SLIDE = 3
MIN_DECK_SLIDES_FOR_CLONE_CHECK = 6
MAX_TWO_TIER_BOTTOM_GRID_RATIO = 0.30

TOP_WIDE_BOX_MIN_Y_PX = 80.0
TOP_WIDE_BOX_WIDTH_RATIO = 0.68
TOP_WIDE_BOX_MAX_BOTTOM_RATIO = 0.68
BOTTOM_BALLAST_MIN_Y_RATIO = 0.60
BOTTOM_BALLAST_MAX_H_RATIO = 0.32
BOTTOM_BALLAST_MAX_W_RATIO = 0.45
MIN_BALLAST_ROW_COUNT = 3

MIN_BLIND_PROMPT_CHARS = 40
MIN_RECONSTRUCTED_CLAIM_CHARS = 12
LEAK_SUBSTRING_WINDOW_CHARS = 8
CJK_BIGRAM_LEN = 2
MAX_WRAPPER_UNWRAP_DEPTH = 4
PREVIEW_TITLE_SNIPPET_CHARS = 12

VALID_SECONDARY_RELATIONS = frozenset(
    {
        "STEP_ZOOM_IN",
        "CONVERGENCE_CRITERION",
        "CONTROL_CONTRAST",
        "CAUSAL_MECHANISM_WHY",
        "QUANTITATIVE_READOUT",
    }
)

FORBIDDEN_SECONDARY_RELATIONS = frozenset(
    {
        "GLOSSARY_STRIP",
        "GLOSSARY_NOTE",
        "TERM_DEFINITION",
        "SUPPLEMENTARY_TRIVIA",
        "SUPPLEMENTARY_NOTE",
        "LAYOUT_FILLER",
    }
)

STEP_CALLOUT_TOKEN_RE = re.compile(
    r"(?:[①②③④⑤⑥⑦⑧⑨⑩]|(?:步骤|阶段|环节|判据|支路)\s*[0-9一二三四五六七八九十①-⑩]+|\bStep\s*\d+|\b[1-9]\s*[-.]\s*[1-9]\b)",
    re.IGNORECASE,
)

DIRECTIONAL_BRIDGE_RE = re.compile(
    r"(?:上图|主图|左图|右图|左侧|右侧|步骤\s*[0-9一二三四①-⑩]|第\s*[0-9一二三四①-⑩]+\s*步|对应主图|放大拆解|拐点拆解|[①②③④⑤⑥⑦⑧⑨⑩]\s*[-·:：]?\s*[1-9a-cA-C]?)"
)

CARD_ACTION_PREDICATE_RE = re.compile(
    r"(?:定位|判读|压低|压短|压扁|锁死|锁住|锁定|消除|加速|对比|筛选|验证|区分|收敛|拆解|放大|导致|抑制|驱动|决定|测出|核验|观察|归属|耦合|重构|阻止|诱导|捕获|锚定|匹配|降低|提升|实现|避免|揭示|证实|排除|突破|打破|受限|源于|依赖|通过|利用|搜寻|核查|切断|打通|分流|压缩|劈裂|展平|对齐|高于|低于|小于|大于|使|让|令|把|将|并非|不是|[=<>≤≥→])"
)

GLOSSARY_STYLE_BODY_RE = re.compile(r"^\s*(?:即|指|定义为|衡量|类比|全称|表示)\b")

CANVAS_BRIBERY_PATTERNS = (
    r"审稿提示[：:]?",
    r"盲测(?:审稿|读者)?(?:提示|说明)[：:]?",
    r"评审(?:放行|说明)[：:]?",
    r"逻辑闭环说明[：:]?",
    r"ignore\s+previous\s+instructions",
    r"system\s*override\s*[:：]",
    r"blind[\s_-]*reader\s*hint",
)

COACHING_PROMPT_PATTERNS = (
    r"请(?:直接)?(?:放行|通过|给高分)",
    r"逻辑已经(?:非常|很)?清楚",
    r"不要(?:挑刺|吹毛求疵|判错)",
    r"我们已经重构了",
    r"please\s+(?:pass|approve)\s+this\s+slide",
    r"confirm\s+that\s+everything\s+is\s+clear",
    r"rubber[\s_-]*stamp",
)

RUBBER_STAMP_CLAIM_PATTERNS = (
    r"^(?:逻辑清晰|排版合理|结构清楚|没有问题|无悬空标签|非常清晰|完全自洽)[，,。!\s]*(?:通过|PASS)?$",
    r"^(?:clear\s+and\s+logical|looks\s+good|no\s+issues\s+found|pass)[.!\s]*$",
)

HTML_VOID_TAGS = frozenset(
    {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
)

BLOCK_CARD_TAGS = frozenset({"div", "article", "section", "li"})
HEADER_FOOTER_TAGS = frozenset({"header", "footer"})
HEADING_CLASS_KEYS = ("panel-title", "card-title", "metric-lbl", "kpi-lbl", "mini-lbl", "box-title")


def _strip_hidden_blocks(html_text: str) -> str:
    cleaned = re.sub(r"<head\b[^>]*>.*?</head>", " ", html_text, flags=re.DOTALL | re.IGNORECASE)
    cleaned = re.sub(r"<script\b[^>]*>.*?</script>", " ", cleaned, flags=re.DOTALL | re.IGNORECASE)
    cleaned = re.sub(r"<style\b[^>]*>.*?</style>", " ", cleaned, flags=re.DOTALL | re.IGNORECASE)
    cleaned = re.sub(r"<template\b[^>]*>.*?</template>", " ", cleaned, flags=re.DOTALL | re.IGNORECASE)
    cleaned = re.sub(
        r"<(?:aside|div|section)\b[^>]*class=[\"'][^\"']*\b(?:notes(?:-source)?|term-popover|detail-popover|evidence-modal|teleprompter)\b[^\"']*[\"'][^>]*>.*?</(?:aside|div|section)>",
        " ",
        cleaned,
        flags=re.DOTALL | re.IGNORECASE,
    )
    return cleaned


class _SlideRootExtractor(HTMLParser):
    """Split multi-slide HTML documents across `<section|div|article class='...slide...'>` roots."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.segments: List[str] = []
        self._buf: List[str] = []
        self._depth = 0

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        t = tag.lower()
        cls_tokens = set(((dict(attrs).get("class") or "").lower()).split())
        if self._depth == 0 and "slide" in cls_tokens and t in {"section", "div", "article"}:
            self._depth = 1
            self._buf = [self.get_starttag_text() or f"<{tag}>"]
            return
        if self._depth > 0:
            if t not in HTML_VOID_TAGS:
                self._depth += 1
            self._buf.append(self.get_starttag_text() or f"<{tag}>")

    def handle_endtag(self, tag: str) -> None:
        t = tag.lower()
        if self._depth > 0:
            self._buf.append(f"</{tag}>")
            if t not in HTML_VOID_TAGS:
                self._depth -= 1
                if self._depth == 0:
                    self.segments.append("".join(self._buf))
                    self._buf = []

    def handle_data(self, data: str) -> None:
        if self._depth > 0:
            self._buf.append(data)


def _split_slide_html_segments(html_text: str) -> List[str]:
    if "<!-- SLIDE_BOUNDARY -->" in html_text:
        segs = [s for s in html_text.split("<!-- SLIDE_BOUNDARY -->") if s.strip()]
        if segs:
            return segs
    extractor = _SlideRootExtractor()
    extractor.feed(html_text)
    if extractor.segments:
        return extractor.segments
    return [html_text] if html_text.strip() else []


class _MiniDOMNode:
    """Lightweight DOM node for class-agnostic structural row inspection."""

    def __init__(self, tag: str, attr_map: Dict[str, str]) -> None:
        self.tag = tag
        self.attr_map = attr_map
        self.cls_tokens = set(attr_map.get("class", "").lower().split())
        self.children: List[_MiniDOMNode] = []
        self.texts: List[str] = []


class _MiniDOMBuilder(HTMLParser):
    """Build a lightweight visible DOM tree ignoring hidden notes/popovers/scripts."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = _MiniDOMNode("root", {})
        self._stack: List[_MiniDOMNode] = [self.root]
        self._ignored_depth = 0

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        t = tag.lower()
        attr_map = {k.lower(): (v or "") for k, v in attrs}
        cls_tokens = set(attr_map.get("class", "").lower().split())
        is_hidden = (
            t in {"head", "script", "style", "template"}
            or "hidden" in attr_map
            or "data-popover-modal" in attr_map
            or "data-popover-id" in attr_map
            or bool(cls_tokens & {"notes", "notes-source", "term-popover", "detail-popover", "evidence-modal", "teleprompter"})
        )
        if self._ignored_depth > 0 or is_hidden:
            if t not in HTML_VOID_TAGS:
                self._ignored_depth += 1
            return
        node = _MiniDOMNode(t, attr_map)
        self._stack[-1].children.append(node)
        if t not in HTML_VOID_TAGS:
            self._stack.append(node)

    def handle_endtag(self, tag: str) -> None:
        t = tag.lower()
        if t in HTML_VOID_TAGS:
            return
        if self._ignored_depth > 0:
            self._ignored_depth -= 1
            return
        if len(self._stack) > 1:
            self._stack.pop()

    def handle_data(self, data: str) -> None:
        if self._ignored_depth == 0:
            self._stack[-1].texts.append(data)


def _node_plain_text(node: _MiniDOMNode) -> str:
    parts: List[str] = list(node.texts)
    for child in node.children:
        parts.append(_node_plain_text(child))
    return re.sub(r"\s+", " ", " ".join(parts)).strip()


def _node_has_visual(node: _MiniDOMNode) -> bool:
    if node.tag in {"svg", "img", "canvas"}:
        return True
    return any(_node_has_visual(c) for c in node.children)


def _node_is_bridge(node: _MiniDOMNode) -> bool:
    if "data-parent-anchor" in node.attr_map:
        return True
    if any(k in node.cls_tokens for k in ("semantic-bridge", "bridge-banner", "causal-connector")):
        return True
    return any(_node_is_bridge(c) for c in node.children)


def _collect_svg_step_tokens(node: _MiniDOMNode, out: Set[str], in_svg: bool = False) -> None:
    now_svg = in_svg or (node.tag == "svg")
    if now_svg:
        for chunk in node.texts:
            for tok in STEP_CALLOUT_TOKEN_RE.findall(chunk):
                out.add(re.sub(r"\s+", "", tok))
    for child in node.children:
        _collect_svg_step_tokens(child, out, now_svg)


def _find_first_heading_node(node: _MiniDOMNode) -> Optional[_MiniDOMNode]:
    if node.tag in {"h3", "h4"} or any(k in node.cls_tokens for k in HEADING_CLASS_KEYS):
        return node
    for child in node.children:
        found = _find_first_heading_node(child)
        if found is not None:
            return found
    return None


def _extract_card_heading_and_body(card_node: _MiniDOMNode) -> Tuple[str, str]:
    h_node = _find_first_heading_node(card_node)
    if h_node is None:
        full = _node_plain_text(card_node)
        return ("", full)
    h_txt = _node_plain_text(h_node)
    full_txt = _node_plain_text(card_node)
    body_txt = full_txt.replace(h_txt, " ", 1).strip()
    return (h_txt, body_txt)


def _resolve_slide_content_rows(root: _MiniDOMNode) -> List[_MiniDOMNode]:
    cur = root
    for _ in range(MAX_WRAPPER_UNWRAP_DEPTH):
        if len(cur.children) == 1 and cur.children[0].tag in {"html", "body", "section", "div", "article"}:
            cur = cur.children[0]
        else:
            break
    for child in cur.children:
        if child.tag == "main" or any(k in child.cls_tokens for k in ("slide-main", "slide-body", "main-area")):
            cur = child
            break
    return [
        c
        for c in cur.children
        if c.tag not in HEADER_FOOTER_TAGS
        and not any(k in c.cls_tokens for k in ("slide-header", "slide-footer", "hdr", "ftr"))
    ]


def _is_bare_noun_card_heading(heading: str, body: str) -> bool:
    if not heading:
        return False
    compact = re.sub(r"\s+", "", heading)
    if STEP_CALLOUT_TOKEN_RE.search(heading) or DIRECTIONAL_BRIDGE_RE.search(heading):
        return False
    if CARD_ACTION_PREDICATE_RE.search(heading):
        return False
    if len(compact) <= MAX_BARE_NOUN_HEADING_CHARS:
        return True
    return bool(GLOSSARY_STYLE_BODY_RE.search(body))


def _strip_has_anchor_to_primary(
    cards: Sequence[Tuple[str, str]],
    primary_tokens: Set[str],
    has_bridge_banner: bool,
) -> bool:
    if has_bridge_banner:
        return True
    combined_titles = " ".join(title for title, _ in cards)
    if DIRECTIONAL_BRIDGE_RE.search(combined_titles):
        return True
    card_tokens = {re.sub(r"\s+", "", tok) for tok in STEP_CALLOUT_TOKEN_RE.findall(combined_titles)}
    if primary_tokens and card_tokens:
        for p_tok in primary_tokens:
            if any(p_tok in c_tok or c_tok in p_tok for c_tok in card_tokens):
                return True
    return False


def _inspect_single_slide_rows(slide_idx: int, seg_html: str) -> Tuple[bool, List[str], List[str]]:
    builder = _MiniDOMBuilder()
    builder.feed(_strip_hidden_blocks(seg_html))
    rows = _resolve_slide_content_rows(builder.root)
    seen_visual_row = False
    seen_bridge = False
    upper_tokens: Set[str] = set()
    has_two_tier = False
    bare_noun_hits: List[str] = []
    unanchored_hits: List[str] = []

    for row in rows:
        if _node_is_bridge(row):
            seen_bridge = True
        row_has_vis = _node_has_visual(row)
        block_kids = [c for c in row.children if c.tag in BLOCK_CARD_TAGS and not _node_has_visual(c)]

        if len(block_kids) >= MIN_MULTI_CARD_STRIP_ITEMS and not row_has_vis:
            strip_cards = [_extract_card_heading_and_body(c) for c in block_kids]
            bare_titles = [t for t, b in strip_cards if _is_bare_noun_card_heading(t, b)]
            if len(bare_titles) >= MIN_BARE_NOUN_SIBLING_HITS:
                bare_noun_hits.append(
                    f"Slide {slide_idx}: bare verbless noun-label strip {bare_titles} "
                    "(use step-anchored causal/action headings or single-tier visual integration, not disconnected noun tags)"
                )
            if seen_visual_row:
                has_two_tier = True
                if not _strip_has_anchor_to_primary(strip_cards, upper_tokens, seen_bridge):
                    titles_preview = [t or b[:PREVIEW_TITLE_SNIPPET_CHARS] for t, b in strip_cards]
                    unanchored_hits.append(
                        f"Slide {slide_idx}: unanchored bottom {len(strip_cards)}-box strip {titles_preview} "
                        "lacks step-index badge, directional pointer, or `.semantic-bridge` linking it to the upper visual"
                    )
        if row_has_vis:
            seen_visual_row = True
            _collect_svg_step_tokens(row, upper_tokens)

    return has_two_tier, bare_noun_hits, unanchored_hits


def audit_html_orphan_bottom_strip_and_noun_cards(html_text: str) -> Dict[str, Any]:
    """
    Class-agnostic structural DOM scan across slides for:
    1. Canvas bribery / reviewer prompt-injection tokens;
    2. Multi-box strips (`>= 3` sibling cards/boxes) using bare verbless noun headings;
    3. Upper-visual + lower >=3-box ballast strips lacking an explicit bridge to the upper visual;
    4. Deck-wide overuse (`> 30%` of slides) of the two-tier `upper-visual + lower-multi-box-strip` layout.
    """
    bribery_hits: List[str] = []
    bare_noun_strips: List[str] = []
    unanchored_strips: List[str] = []
    segments = _split_slide_html_segments(html_text)
    two_tier_slide_count = 0

    for idx, seg in enumerate(segments, start=1):
        for pat in CANVAS_BRIBERY_PATTERNS:
            m = re.search(pat, seg, flags=re.IGNORECASE)
            if m:
                bribery_hits.append(f"Slide {idx}: reviewer-bribery / prompt-injection token '{m.group(0)}'")
        has_two_tier, bare_hits, unanc_hits = _inspect_single_slide_rows(idx, seg)
        if has_two_tier:
            two_tier_slide_count += 1
        bare_noun_strips.extend(bare_hits)
        unanchored_strips.extend(unanc_hits)

    two_tier_ratio = two_tier_slide_count / float(max(1, len(segments)))
    cloning_issues: List[str] = []
    if len(segments) >= MIN_DECK_SLIDES_FOR_CLONE_CHECK and two_tier_ratio > MAX_TWO_TIER_BOTTOM_GRID_RATIO:
        cloning_issues.append(
            f"Deck uses two-tier 'upper-visual + bottom-multi-box-strip' ballast layout on {two_tier_slide_count}/{len(segments)} "
            f"slides ({two_tier_ratio:.1%} > {MAX_TWO_TIER_BOTTOM_GRID_RATIO:.0%} cap); use single-tier full-height visuals instead"
        )

    issues = bribery_hits + bare_noun_strips + unanchored_strips + cloning_issues
    return {
        "passed": len(issues) == 0,
        "slide_count_scanned": len(segments),
        "two_tier_bottom_grid_slides": two_tier_slide_count,
        "two_tier_bottom_grid_ratio": round(two_tier_ratio, 4),
        "bribery_hits": bribery_hits,
        "bare_noun_card_strips": bare_noun_strips,
        "unanchored_bottom_strips": unanchored_strips,
        "cloning_issues": cloning_issues,
        "issues": issues,
    }


def audit_boxes_for_bottom_ballast_strip(
    boxes: Sequence[Dict[str, Any]],
    canvas_w: float,
    canvas_h: float,
) -> List[str]:
    """Detect unanchored >=3 short bottom-row ballast cards placed beneath an upper visual."""
    has_upper_visual = False
    unanchored_bottom_ids: List[str] = []
    for box in boxes:
        w = float(box["w"])
        h = float(box["h"])
        y = float(box["y"])
        if (y + h) <= TOP_WIDE_BOX_MAX_BOTTOM_RATIO * canvas_h and y >= TOP_WIDE_BOX_MIN_Y_PX and h >= BOTTOM_BALLAST_MAX_H_RATIO * canvas_h:
            has_upper_visual = True
        if y >= BOTTOM_BALLAST_MIN_Y_RATIO * canvas_h and h <= BOTTOM_BALLAST_MAX_H_RATIO * canvas_h and w < BOTTOM_BALLAST_MAX_W_RATIO * canvas_w:
            anchor = str(box.get("semantic_anchor_to", "")).strip()
            if not anchor:
                unanchored_bottom_ids.append(str(box.get("id", "bottom_card")))
    if has_upper_visual and len(unanchored_bottom_ids) >= MIN_BALLAST_ROW_COUNT:
        return [
            f"Unanchored bottom ballast strip detected ({len(unanchored_bottom_ids)} short lower-canvas cards "
            f"{unanchored_bottom_ids} beneath upper visual without `semantic_anchor_to`)"
        ]
    return []


def _validate_single_semantic_tree(slide_idx: int, tree: Dict[str, Any]) -> List[str]:
    issues: List[str] = []
    claim = str(tree.get("core_claim", "")).strip()
    spine = str(tree.get("primary_visual_spine", "")).strip()
    if len(claim) < MIN_PROPOSITION_CLAIM_CHARS or not CARD_ACTION_PREDICATE_RE.search(claim):
        issues.append(
            f"Slide {slide_idx}: intra_slide_semantic_tree.core_claim must be a concrete causal/evaluative proposition"
        )
    if len(spine) < MIN_PRIMARY_SPINE_CHARS:
        issues.append(f"Slide {slide_idx}: intra_slide_semantic_tree missing primary_visual_spine")

    sec_blocks = tree.get("secondary_blocks", [])
    if not isinstance(sec_blocks, list):
        return issues + [f"Slide {slide_idx}: secondary_blocks must be a list"]
    if len(sec_blocks) > MAX_SECONDARY_BLOCKS_PER_SLIDE:
        issues.append(
            f"Slide {slide_idx}: {len(sec_blocks)} secondary_blocks exceeds {MAX_SECONDARY_BLOCKS_PER_SLIDE} cap; split into a new slide"
        )
    for b_idx, blk in enumerate(sec_blocks, start=1):
        if not isinstance(blk, dict):
            issues.append(f"Slide {slide_idx} block[{b_idx}]: must be a dict")
            continue
        rel = str(blk.get("relation_type", "")).strip().upper()
        target = str(blk.get("parent_anchor_target", "")).strip()
        bridge = str(blk.get("on_canvas_bridge_marker", "")).strip()
        if rel in FORBIDDEN_SECONDARY_RELATIONS or rel not in VALID_SECONDARY_RELATIONS:
            issues.append(
                f"Slide {slide_idx} block[{b_idx}]: invalid relation_type='{rel}' "
                f"(must be in {sorted(VALID_SECONDARY_RELATIONS)}; glossary/filler blocks forbidden)"
            )
        if len(target) < MIN_ANCHOR_TARGET_CHARS:
            issues.append(f"Slide {slide_idx} block[{b_idx}]: missing parent_anchor_target to primary visual")
        if len(bridge) < MIN_BRIDGE_MARKER_CHARS:
            issues.append(f"Slide {slide_idx} block[{b_idx}]: missing visible on_canvas_bridge_marker")
    return issues


def verify_intra_slide_semantic_trees(
    storyboard_slides: Sequence[Dict[str, Any]],
    require_all_slides: bool = False,
) -> Dict[str, Any]:
    """Verify pre-generation Intra-Slide Semantic Tree contracts across storyboard slides."""
    issues: List[str] = []
    checked_count = 0
    for idx, slide in enumerate(storyboard_slides, start=1):
        tree = slide.get("intra_slide_semantic_tree")
        if tree is None:
            if require_all_slides:
                issues.append(f"Slide {idx}: missing required intra_slide_semantic_tree")
            continue
        if not isinstance(tree, dict):
            issues.append(f"Slide {idx}: intra_slide_semantic_tree must be a dict")
            continue
        checked_count += 1
        issues.extend(_validate_single_semantic_tree(idx, tree))
    return {
        "passed": len(issues) == 0,
        "trees_verified_count": checked_count,
        "issues": issues,
    }


def _extract_anchor_tokens(text: str) -> Set[str]:
    tokens: Set[str] = set()
    for m in STEP_CALLOUT_TOKEN_RE.finditer(text):
        tokens.add(re.sub(r"\s+", "", m.group(0)))
    for word in re.findall(r"[A-Za-z0-9_]{2,}", text):
        tokens.add(word.lower())
    for run in re.findall(r"[\u4e00-\u9fff]+", text):
        if len(run) >= CJK_BIGRAM_LEN:
            for i in range(len(run) - CJK_BIGRAM_LEN + 1):
                tokens.add(run[i : i + CJK_BIGRAM_LEN])
    return tokens


def _check_prompt_anti_collusion(
    prompt_text: str,
    storyboard_slides: Optional[Sequence[Dict[str, Any]]],
) -> List[str]:
    issues: List[str] = []
    if len(prompt_text) < MIN_BLIND_PROMPT_CHARS:
        return ["Blind reader audit missing verbatim `blind_prompt_sent` (>= 40 chars required)"]
    for pat in COACHING_PROMPT_PATTERNS:
        m = re.search(pat, prompt_text, flags=re.IGNORECASE)
        if m:
            issues.append(f"COLLUSION_PROMPT_COACHING: blind_prompt_sent contains coaching phrase '{m.group(0)}'")
    for slide in storyboard_slides or []:
        tree = slide.get("intra_slide_semantic_tree")
        if not isinstance(tree, dict):
            continue
        claim = re.sub(r"\s+", "", str(tree.get("core_claim", "")))
        compact_prompt = re.sub(r"\s+", "", prompt_text)
        if len(claim) >= LEAK_SUBSTRING_WINDOW_CHARS:
            probe_sub = claim[:LEAK_SUBSTRING_WINDOW_CHARS]
            if probe_sub in compact_prompt:
                issues.append(
                    f"COLLUSION_PROMPT_ANSWER_LEAK: blind_prompt_sent leaks slide core_claim substring '{probe_sub}'"
                )
        for blk in tree.get("secondary_blocks", []) or []:
            if isinstance(blk, dict):
                ans = re.sub(r"\s+", "", str(blk.get("parent_anchor_target", "")))
                if len(ans) >= LEAK_SUBSTRING_WINDOW_CHARS and ans[:LEAK_SUBSTRING_WINDOW_CHARS] in compact_prompt:
                    issues.append(
                        f"COLLUSION_PROMPT_ANSWER_LEAK: blind_prompt_sent leaks parent_anchor_target '{ans[:LEAK_SUBSTRING_WINDOW_CHARS]}'"
                    )
    return issues


def _check_single_slide_reconstruction(
    rec: Dict[str, Any],
    expected_tree: Optional[Dict[str, Any]],
) -> List[str]:
    issues: List[str] = []
    sid = str(rec.get("slide_id", "unknown_slide")).strip()
    claim = str(rec.get("reconstructed_claim", "")).strip()
    if len(claim) < MIN_RECONSTRUCTED_CLAIM_CHARS:
        issues.append(f"{sid}: reconstructed_claim too short (< {MIN_RECONSTRUCTED_CLAIM_CHARS} chars)")
    for pat in RUBBER_STAMP_CLAIM_PATTERNS:
        if re.search(pat, claim, flags=re.IGNORECASE):
            issues.append(f"{sid}: RUBBER_STAMP_COLLUSION generic praise '{claim}' rejected")

    dangling = rec.get("ambiguous_or_dangling_elements")
    if not isinstance(dangling, list):
        issues.append(f"{sid}: missing `ambiguous_or_dangling_elements` list")
    elif len(dangling) > 0:
        issues.append(f"{sid}: BLIND_READER_FLAGGED_DANGLING_ELEMENTS {dangling}")

    links = rec.get("reconstructed_block_links", [])
    if not isinstance(links, list):
        return issues + [f"{sid}: `reconstructed_block_links` must be a list"]

    for link in links:
        if not isinstance(link, dict):
            continue
        ev = str(link.get("visible_bridge_evidence", "")).strip()
        if not ev or ev.upper() == "UNANCHORED_GUESS":
            issues.append(
                f"{sid}: block '{link.get('visible_block_heading', '')}' required UNANCHORED_GUESS (no visible bridge on PNG)"
            )

    if isinstance(expected_tree, dict):
        exp_blocks = expected_tree.get("secondary_blocks", [])
        if isinstance(exp_blocks, list) and len(exp_blocks) > 0:
            if len(links) != len(exp_blocks):
                issues.append(
                    f"{sid}: TOPOLOGICAL_COUNT_MISMATCH blind reader reconstructed {len(links)} secondary block(s) vs {len(exp_blocks)} committed"
                )
            else:
                for exp_b, obs_l in zip(exp_blocks, links):
                    exp_toks = _extract_anchor_tokens(str(exp_b.get("parent_anchor_target", "")))
                    obs_toks = _extract_anchor_tokens(str(obs_l.get("inferred_parent_target", "")))
                    if exp_toks and not (exp_toks & obs_toks):
                        issues.append(
                            f"{sid}: TOPOLOGICAL_RECONSTRUCTION_MISMATCH blind reader inferred '{obs_l.get('inferred_parent_target')}' "
                            f"vs committed '{exp_b.get('parent_anchor_target')}'"
                        )
    return issues


def verify_anti_collusion_blind_reader_audit(
    blind_reader_audit: Optional[Dict[str, Any]],
    storyboard_slides: Optional[Sequence[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Gate D18 Subcheck: Anti-Collusion Zero-Context Blind Reader Reconstruction Verifier.
    Blocks (1) prompt coaching/answer-leaking, (2) context contamination, (3) rubber-stamp generic
    PASS claims, and (4) unresolved dangling elements or mismatched topological reconstructions.
    """
    if not isinstance(blind_reader_audit, dict) or not blind_reader_audit:
        return {"passed": False, "issues": ["Missing `blind_reader_audit` receipt"]}

    issues: List[str] = []
    iso_mode = str(blind_reader_audit.get("reviewer_isolation_mode", "")).strip()
    if iso_mode != "READONLY_PNG_BLIND_SUBAGENT":
        issues.append(
            f"Invalid reviewer_isolation_mode='{iso_mode}' (must be 'READONLY_PNG_BLIND_SUBAGENT')"
        )
    if (
        blind_reader_audit.get("saw_source_pdf") is not False
        or blind_reader_audit.get("saw_storyboard_json") is not False
        or blind_reader_audit.get("saw_speaker_notes") is not False
    ):
        issues.append(
            "COLLUSION_CONTEXT_CONTAMINATION: blind reader must have saw_source_pdf=False, saw_storyboard_json=False, saw_speaker_notes=False"
        )

    prompt_text = str(blind_reader_audit.get("blind_prompt_sent", "")).strip()
    issues.extend(_check_prompt_anti_collusion(prompt_text, storyboard_slides))

    reconstructions = blind_reader_audit.get("slide_reconstructions")
    if not isinstance(reconstructions, list) or len(reconstructions) == 0:
        issues.append("blind_reader_audit must contain non-empty `slide_reconstructions` list")
    else:
        tree_by_id: Dict[str, Dict[str, Any]] = {}
        for idx, s in enumerate(storyboard_slides or [], start=1):
            sid = str(s.get("slide_id", f"slide_{idx:02d}")).strip()
            if isinstance(s.get("intra_slide_semantic_tree"), dict):
                tree_by_id[sid] = s["intra_slide_semantic_tree"]
        for rec in reconstructions:
            if not isinstance(rec, dict):
                issues.append("Each entry in `slide_reconstructions` must be a dict")
                continue
            sid = str(rec.get("slide_id", "")).strip()
            issues.extend(_check_single_slide_reconstruction(rec, tree_by_id.get(sid)))

    return {
        "passed": len(issues) == 0,
        "audited_slide_count": len(reconstructions) if isinstance(reconstructions, list) else 0,
        "issues": issues,
    }
