"""
Lossless Clickable Detail Popover, Multi-Paragraph Dump Prevention & Topological Split Ledger Engine
(`skill.design-anti-goodhart@1.0.0-rc.21`).

Prevents Second-Order Goodhart Information Amputation under the Ultra-Low-Text (`<= 260` visible chars)
& 2x Large-Typography (`>= 32px` floor / `>= 42px` HD card body / `>= 56px` HD title) regime:
1. `Clickable_Detail_Popover_Integrity_Guard`:
   - Audits `.detail-trigger` / `[data-detail-id]` clickable buttons on each slide;
   - Rejects dead/dangling popover triggers lacking a backing `<template data-detail-id="...">`,
     `[data-popover-id="..."]`, or script payload (`>= 20` chars of substantive evidence/recipe);
   - Rejects multi-paragraph prose dumping (`>= 2` `<p>` blocks inside a single visible card),
     forcing secondary recipes/controls into clickable popovers or split sequential slides.
2. `Lossless_Popover_And_Split_Ledger_Verifier`:
   - Audits `lossless_split_and_popover_ledger` so zero quantitative recipes, control proofs, or
     acronym definitions are silently dropped (`DROPPED` / `OMITTED` / `NOTES_ONLY` rejected);
   - Enforces continuous `topo_node_id` / `topo_breadcrumb` linkage across multi-slide splits so
     macro-to-micro causal topology stays transparent even across 30+ focused slides.
"""

from __future__ import annotations

from html.parser import HTMLParser
import re
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

MIN_POPOVER_PAYLOAD_CHARS = 20
MIN_TRIGGER_LABEL_CHARS = 2
MAX_VISIBLE_PARAGRAPHS_PER_CARD = 1
MIN_LEDGER_SUMMARY_CHARS = 6
MIN_ANCHOR_REF_CHARS = 2
MIN_MULTI_SLIDE_TOPO_COUNT = 6
MIN_DUAL_CHANNEL_ITEMS = 2
SAMPLE_LIMIT = 5

VALID_CARRIER_MODES = frozenset({"SPLIT_SLIDE", "CLICKABLE_POPOVER", "ON_CANVAS_CORE"})
FORBIDDEN_CARRIER_MODES = frozenset({"DROPPED", "OMITTED", "NOTES_ONLY", "DELETED", "TRUNCATED"})

HTML_VOID_TAGS = frozenset(
    {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
)
HIDDEN_MODAL_CLASSES = frozenset({"notes", "notes-source", "term-popover", "detail-popover", "evidence-modal", "teleprompter"})
CARD_CLASSES = frozenset({"guide-step", "panel", "card"})

SCRIPT_PAYLOAD_ENTRY_RE = re.compile(
    r"[\"']([A-Za-z0-9_.:-]+)[\"']\s*:\s*\{[^{}]*?[\"'](?:body|content|detail|html|text)[\"']\s*:\s*[\"']([^\"']{20,})[\"']",
    flags=re.DOTALL,
)


def _split_slide_segments(html_text: str) -> List[str]:
    if "<!-- SLIDE_BOUNDARY -->" in html_text:
        segs = [s for s in html_text.split("<!-- SLIDE_BOUNDARY -->") if s.strip()]
        if segs:
            return segs
    matches = re.findall(
        r"<(?:section|div|article)\b[^>]*class=[\"'][^\"']*\bslide\b[^\"']*[\"'][^>]*>.*?</(?:section|div|article)>",
        html_text,
        flags=re.DOTALL | re.IGNORECASE,
    )
    return matches if matches else ([html_text] if html_text.strip() else [])


def _extract_script_detail_payloads(html_text: str) -> Dict[str, int]:
    payload_lengths: Dict[str, int] = {}
    for script_body in re.findall(r"<script\b[^>]*>(.*?)</script>", html_text, flags=re.DOTALL | re.IGNORECASE):
        for key, body in SCRIPT_PAYLOAD_ENTRY_RE.findall(script_body):
            compact = re.sub(r"\s+", "", body)
            prev_len = payload_lengths[key] if key in payload_lengths else 0
            payload_lengths[key] = max(prev_len, len(compact))
    return payload_lengths


class _PopoverAndCardParagraphInspector(HTMLParser):
    """Inspect clickable detail triggers, backing template/modal payloads, and card paragraph counts."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.triggers: List[Tuple[str, List[str]]] = []
        self.payloads: Dict[str, List[str]] = {}
        self.empty_id_triggers = 0
        self.multi_para_cards: List[int] = []
        self.has_topo_breadcrumb = False
        self._active_trigger_idx: Optional[int] = None
        self._trigger_depth = 0
        self._active_payload_id: Optional[str] = None
        self._payload_depth = 0
        self._hidden_depth = 0
        self._card_para_stack: List[int] = []
        self._trail: List[str] = []

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        t = tag.lower()
        if t in HTML_VOID_TAGS:
            return
        attr_map = {k.lower(): (v or "").strip() for k, v in attrs}
        cls_tokens = set(attr_map.get("class", "").lower().split())

        if "topo-breadcrumb" in cls_tokens or "data-topo-node" in attr_map:
            self.has_topo_breadcrumb = True

        payload_id = attr_map.get("data-popover-id") or (
            attr_map.get("data-detail-id") if (t == "template" or "hidden" in attr_map or bool(cls_tokens & HIDDEN_MODAL_CLASSES)) else ""
        )
        if payload_id and self._active_payload_id is None:
            self._active_payload_id = payload_id
            self._payload_depth = 1
            self.payloads.setdefault(payload_id, [])
            self._trail.append("payload_root")
            return
        if self._active_payload_id is not None:
            self._payload_depth += 1
            self._trail.append("payload_child")
            return

        is_hidden = (
            t in {"head", "script", "style", "template"}
            or "hidden" in attr_map
            or "data-popover-modal" in attr_map
            or bool(cls_tokens & HIDDEN_MODAL_CLASSES)
        )
        if self._hidden_depth > 0 or is_hidden:
            self._hidden_depth += 1
            self._trail.append("hidden")
            return

        is_trigger = ("detail-trigger" in cls_tokens) or ("data-detail-id" in attr_map)
        if is_trigger and self._active_trigger_idx is None:
            did = attr_map.get("data-detail-id", "")
            if not did:
                self.empty_id_triggers += 1
            self.triggers.append((did, []))
            self._active_trigger_idx = len(self.triggers) - 1
            self._trigger_depth = 1
            self._trail.append("trigger_root")
            return
        if self._active_trigger_idx is not None:
            self._trigger_depth += 1

        if t == "article" or bool(cls_tokens & CARD_CLASSES):
            self._card_para_stack.append(0)
            self._trail.append("card")
            return

        if t == "p" and self._card_para_stack:
            self._card_para_stack[-1] += 1

        self._trail.append("normal")

    def handle_endtag(self, tag: str) -> None:
        t = tag.lower()
        if t in HTML_VOID_TAGS or not self._trail:
            return
        role = self._trail.pop()
        if role in {"payload_root", "payload_child"}:
            self._payload_depth = max(0, self._payload_depth - 1)
            if self._payload_depth == 0:
                self._active_payload_id = None
            return
        if role == "hidden":
            self._hidden_depth = max(0, self._hidden_depth - 1)
            return
        if role == "trigger_root":
            self._trigger_depth = 0
            self._active_trigger_idx = None
            return
        if self._active_trigger_idx is not None:
            self._trigger_depth = max(0, self._trigger_depth - 1)
            if self._trigger_depth == 0:
                self._active_trigger_idx = None
        if role == "card" and self._card_para_stack:
            p_count = self._card_para_stack.pop()
            if p_count > MAX_VISIBLE_PARAGRAPHS_PER_CARD:
                self.multi_para_cards.append(p_count)

    def handle_data(self, data: str) -> None:
        compact = re.sub(r"\s+", "", data)
        if not compact:
            return
        if self._active_payload_id is not None:
            self.payloads[self._active_payload_id].append(compact)
        elif self._active_trigger_idx is not None and self._hidden_depth == 0:
            self.triggers[self._active_trigger_idx][1].append(compact)


def audit_clickable_detail_popovers_and_triggers(html_text: str) -> Dict[str, Any]:
    """
    Verify that all clickable `.detail-trigger` / `[data-detail-id]` chips resolve to substantive
    backing popover payloads (`>= 20` chars) and reject multi-paragraph card prose dumping.
    """
    if not html_text.strip():
        return {
            "passed": True,
            "detail_trigger_count": 0,
            "verified_popover_count": 0,
            "dangling_triggers": [],
            "multi_paragraph_cards": [],
            "issues": [],
        }

    global_payloads = _extract_script_detail_payloads(html_text)
    segments = _split_slide_segments(html_text)
    parsed_slides: List[_PopoverAndCardParagraphInspector] = []
    for seg in segments:
        ins = _PopoverAndCardParagraphInspector()
        ins.feed(seg)
        parsed_slides.append(ins)
        for pid, chunks in ins.payloads.items():
            char_len = sum(len(c) for c in chunks)
            prev_len = global_payloads[pid] if pid in global_payloads else 0
            global_payloads[pid] = max(prev_len, char_len)

    dangling: List[str] = []
    multi_para_issues: List[str] = []
    total_triggers = 0
    for idx, ins in enumerate(parsed_slides, start=1):
        if ins.empty_id_triggers > 0:
            dangling.append(f"Slide {idx}: {ins.empty_id_triggers} `.detail-trigger` button(s) missing `data-detail-id`")
        for did, lbl_chunks in ins.triggers:
            total_triggers += 1
            lbl = "".join(lbl_chunks)
            if len(lbl) < MIN_TRIGGER_LABEL_CHARS and len(dangling) < SAMPLE_LIMIT:
                dangling.append(f"Slide {idx}: detail trigger '{did}' has empty/tiny visible button label")
            found_len = global_payloads[did] if did in global_payloads else 0
            if did and found_len < MIN_POPOVER_PAYLOAD_CHARS and len(dangling) < SAMPLE_LIMIT:
                dangling.append(
                    f"Slide {idx}: detail trigger data-detail-id='{did}' has missing or hollow (<{MIN_POPOVER_PAYLOAD_CHARS} chars) popover payload"
                )
        for p_cnt in ins.multi_para_cards:
            if len(multi_para_issues) < SAMPLE_LIMIT:
                multi_para_issues.append(
                    f"Slide {idx}: visible card stacks {p_cnt} `<p>` paragraphs (> {MAX_VISIBLE_PARAGRAPHS_PER_CARD}) — "
                    "offload secondary details into a clickable popover or split into a separate slide"
                )

    issues = dangling + multi_para_issues
    return {
        "passed": len(issues) == 0,
        "detail_trigger_count": total_triggers,
        "verified_popover_count": sum(1 for v in global_payloads.values() if v >= MIN_POPOVER_PAYLOAD_CHARS),
        "dangling_triggers": dangling,
        "multi_paragraph_cards": multi_para_issues,
        "issues": issues,
    }


def verify_lossless_popover_and_split_ledger(
    ledger: Optional[Dict[str, Any]],
    storyboard_slides: Optional[Sequence[Dict[str, Any]]] = None,
    require_ledger: bool = False,
) -> Dict[str, Any]:
    """
    Verify that cutting visible canvas characters (`<= 260`) causes ZERO scientific information loss:
    every key parameter, control proof, and derivation is accounted for via `SPLIT_SLIDE` or
    `CLICKABLE_POPOVER` (rejecting `DROPPED` / `OMITTED` / `NOTES_ONLY`), with topological breadcrumbs.
    """
    if ledger is None:
        if require_ledger:
            return {"passed": False, "issues": ["Missing required `lossless_split_and_popover_ledger`"]}
        return {"passed": True, "preserved_count": 0, "issues": []}
    if not isinstance(ledger, dict):
        return {"passed": False, "issues": ["`lossless_split_and_popover_ledger` must be a dict"]}

    issues: List[str] = []
    items = ledger.get("preserved_evidence_items")
    if not isinstance(items, list) or len(items) == 0:
        issues.append("`lossless_split_and_popover_ledger.preserved_evidence_items` must be a non-empty list")
        items = []

    known_slide_ids: Set[str] = set()
    for idx, s in enumerate(storyboard_slides or (), start=1):
        known_slide_ids.add(str(s.get("slide_id", f"slide_{idx:02d}")).strip())

    offload_modes_used: Set[str] = set()
    for i_idx, item in enumerate(items):
        if not isinstance(item, dict):
            issues.append(f"preserved_evidence_items[{i_idx}] must be a dict")
            continue
        mode = str(item.get("carrier_mode", "")).strip().upper()
        summary = str(item.get("content_summary", "")).strip()
        target_sid = str(item.get("target_slide_id", "")).strip()
        ref = str(item.get("trigger_or_anchor", "")).strip()
        if mode in FORBIDDEN_CARRIER_MODES or mode not in VALID_CARRIER_MODES:
            issues.append(
                f"preserved_evidence_items[{i_idx}]: invalid or lossy carrier_mode='{mode}' "
                f"(must be in {sorted(VALID_CARRIER_MODES)}; silent dropping or notes-only hiding is forbidden)"
            )
        else:
            offload_modes_used.add(mode)
        if len(summary) < MIN_LEDGER_SUMMARY_CHARS:
            issues.append(f"preserved_evidence_items[{i_idx}]: content_summary too short (< {MIN_LEDGER_SUMMARY_CHARS} chars)")
        if len(ref) < MIN_ANCHOR_REF_CHARS:
            issues.append(f"preserved_evidence_items[{i_idx}]: missing `trigger_or_anchor` reference")
        if known_slide_ids and target_sid not in known_slide_ids:
            issues.append(f"preserved_evidence_items[{i_idx}]: unknown target_slide_id='{target_sid}'")

    if len(items) >= MIN_DUAL_CHANNEL_ITEMS and not (offload_modes_used & {"SPLIT_SLIDE", "CLICKABLE_POPOVER"}):
        issues.append(
            "Lossless ledger must use `SPLIT_SLIDE` and/or `CLICKABLE_POPOVER` to offload detail instead of cramming one canvas"
        )

    slides_seq = list(storyboard_slides or ())
    if len(slides_seq) >= MIN_MULTI_SLIDE_TOPO_COUNT and bool(ledger.get("require_topological_breadcrumbs", True)):
        missing_topo: List[str] = []
        for idx, s in enumerate(slides_seq, start=1):
            sid = str(s.get("slide_id", f"slide_{idx:02d}")).strip()
            tree = s.get("intra_slide_semantic_tree") or {}
            topo_id = str(s.get("topo_breadcrumb") or tree.get("topo_node_id") or "").strip()
            if not topo_id and len(missing_topo) < SAMPLE_LIMIT:
                missing_topo.append(sid)
        if missing_topo:
            issues.append(
                f"Multi-slide split deck missing `topo_breadcrumb` / `topo_node_id` on slides {missing_topo} "
                "(logical topology must stay explicit across split slides)"
            )

    return {
        "passed": len(issues) == 0,
        "preserved_count": len(items),
        "carrier_modes_used": sorted(offload_modes_used),
        "issues": issues,
    }
