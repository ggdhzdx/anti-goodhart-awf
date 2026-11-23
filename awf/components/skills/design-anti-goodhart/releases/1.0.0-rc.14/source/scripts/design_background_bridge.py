"""
Beyond-PDF Domain Background Synthesis & Audience Cognitive Translation Validators
(`skill.design-anti-goodhart@1.0.0-rc.14`).

Enforces the 4-Rung Zoom-In Background Funnel (`domain_background_bridge`) so that
`TDD` (Tutor), `GRILL`, and `HTML-PPT` decks never jump abruptly into narrow sub-domain
PDF jargon without synthesizing foundational world knowledge omitted by raw papers.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Sequence, Set

MIN_PDF_OMITTED_GAPS = 2
MIN_GAP_DESC_CHARS = 8
MIN_ONBOARDING_PRIMER_CHARS = 30
MIN_RUNG_STATEMENT_CHARS = 12
MIN_VISUAL_SCHEMATIC_CHARS = 10
MIN_JARGON_TRANSLATIONS = 2
MIN_JARGON_FIELD_CHARS = 6
MIN_TERSE_TERM_CHARS = 2
MIN_FULL_PAPER_SLIDES_THRESHOLD = 10
MIN_FULL_PAPER_BG_SLIDES = 3
MIN_BRIEFING_ANCHOR_CHARS = 16
RUNG_INDEX_MIN = 1
RUNG_INDEX_MAX = 4

FRAMEWORK_META_JARGON_PATTERNS = (
    r"\bUNBOUNDED_FLOW_DRIVEN\b",
    r"\bJIT_DURING_QA\b",
    r"\bHYBRID_SEED_PLUS_JIT\b",
    r"\bAUTONOMOUS_DUAL_EVOLVE\b",
    r"\bgdd_grill_capsule\b",
    r"\btdd_station_capsule\b",
    r"\bslide_manifest\.json\b",
    r"\bStage\s*k\.[123]\b",
    r"(?<![A-Za-z0-9_-])V[0-3]\s*(?:动画|交互|静态|纯文字|模态)",
)

VALID_BG_PROVENANCE = "BEYOND_PDF_DOMAIN_KNOWLEDGE"


def scan_framework_meta_jargon(text: str) -> List[str]:
    """Return any leaked internal AWF framework codewords found in user/audience text."""
    hits: List[str] = []
    for pat in FRAMEWORK_META_JARGON_PATTERNS:
        match = re.search(pat, text)
        if match:
            hits.append(match.group(0))
    return hits


def _extract_rung_text(val: Any) -> str:
    if isinstance(val, dict):
        return str(val.get("summary") or val.get("explanation") or val.get("principle") or "").strip()
    return str(val or "").strip()


def _extract_rung_visual(funnel: Dict[str, Any], bridge: Dict[str, Any]) -> str:
    r2 = funnel.get("rung2_canonical_working_principle")
    if isinstance(r2, dict):
        vis = str(r2.get("visual_schematic_plan") or "").strip()
        if vis:
            return vis
    top_vis = bridge.get("beyond_pdf_visual_schematics")
    if isinstance(top_vis, list) and top_vis:
        return " | ".join(str(x).strip() for x in top_vis if str(x).strip())
    return str(bridge.get("visual_schematic_plan") or "").strip()


def _collect_background_slide_indices(
    bridge: Dict[str, Any],
    storyboard_slides: Sequence[Dict[str, Any]],
) -> Set[int]:
    indices: Set[int] = set()
    raw_indices = bridge.get("background_slide_indices", [])
    if isinstance(raw_indices, list):
        for item in raw_indices:
            if isinstance(item, (int, float)) and not isinstance(item, bool) and int(item) >= 1:
                indices.add(int(item))
    for pos, slide in enumerate(storyboard_slides, start=1):
        if not isinstance(slide, dict):
            continue
        rung = slide.get("background_rung")
        has_valid_rung = (
            isinstance(rung, int)
            and not isinstance(rung, bool)
            and RUNG_INDEX_MIN <= rung <= RUNG_INDEX_MAX
        )
        if bool(slide.get("is_background_slide", False)) or has_valid_rung:
            indices.add(pos)
    return indices


def verify_domain_background_bridge_capsule(
    background_bridge: Optional[Dict[str, Any]],
    *,
    storyboard_slides: Optional[Sequence[Dict[str, Any]]] = None,
    is_full_paper_deck: bool = False,
) -> Dict[str, Any]:
    """
    Verify Role 0 (`BackgroundSynthesizer & AudienceTranslator`) `domain_background_bridge`:
    1. `pdf_omitted_background_gaps`: >=2 foundational gaps omitted by the raw PDF;
    2. `outside_pdf_onboarding_primer`: plain-language bird's-eye primer free of AWF meta-jargon;
    3. `four_rung_funnel`: Rung 1 (macro industry stakes) -> Rung 2 (canonical working principle
       + beyond-PDF SVG/interactive visual plan) -> Rung 3 (>=2 core jargon plain analogies &
       physical definitions) -> Rung 4 (specific bottleneck & prior-art deadlock);
    4. Dual-source provenance discipline (`BEYOND_PDF_DOMAIN_KNOWLEDGE` vs `PDF_PRIMARY_EVIDENCE`);
    5. Multi-slide background runway (`>=3` slides on full-paper decks, strictly V2/V3 visuals).
    """
    issues: List[str] = []
    slides = list(storyboard_slides or [])
    if not isinstance(background_bridge, dict) or not background_bridge:
        return {
            "passed": False,
            "background_slide_count": 0,
            "jargon_translation_count": 0,
            "issues": [
                "Missing domain_background_bridge: raw PDFs omit foundational background; "
                "must synthesize 4-rung beyond-PDF domain background & plain-language jargon bridge"
            ],
        }

    gaps = background_bridge.get("pdf_omitted_background_gaps", [])
    valid_gaps = [
        str(g).strip() for g in (gaps if isinstance(gaps, list) else [])
        if len(str(g).strip()) >= MIN_GAP_DESC_CHARS
    ]
    if len(valid_gaps) < MIN_PDF_OMITTED_GAPS:
        issues.append(
            f"domain_background_bridge.pdf_omitted_background_gaps must diagnose >={MIN_PDF_OMITTED_GAPS} "
            "foundational concepts omitted by the raw PDF"
        )

    primer = str(background_bridge.get("outside_pdf_onboarding_primer", "")).strip()
    if len(primer) < MIN_ONBOARDING_PRIMER_CHARS:
        issues.append(
            "domain_background_bridge missing outside_pdf_onboarding_primer "
            "(plain-language world-knowledge onboarding before MCQs/slides)"
        )
    else:
        meta_hits = scan_framework_meta_jargon(primer)
        if meta_hits:
            issues.append(
                f"outside_pdf_onboarding_primer leaks internal AWF framework codewords {meta_hits}; "
                "use plain human language instead of V0-V3/Stage/flag tokens"
            )

    funnel = background_bridge.get("four_rung_funnel")
    jargon_count = 0
    if not isinstance(funnel, dict):
        issues.append("domain_background_bridge missing four_rung_funnel (Rung 1..4 zoom-in background arc)")
    else:
        r1 = _extract_rung_text(funnel.get("rung1_macro_industry_stakes"))
        r2 = _extract_rung_text(funnel.get("rung2_canonical_working_principle"))
        r4 = _extract_rung_text(funnel.get("rung4_prior_art_deadlock"))
        vis_plan = _extract_rung_visual(funnel, background_bridge)
        if len(r1) < MIN_RUNG_STATEMENT_CHARS:
            issues.append("four_rung_funnel missing rung1_macro_industry_stakes (why the broader field matters & incumbent ceiling)")
        if len(r2) < MIN_RUNG_STATEMENT_CHARS:
            issues.append("four_rung_funnel missing rung2_canonical_working_principle (how baseline device/system works before paper's molecule)")
        if len(vis_plan) < MIN_VISUAL_SCHEMATIC_CHARS:
            issues.append(
                "four_rung_funnel missing visual_schematic_plan for beyond-PDF background "
                "(must plan custom SVG device/cycle schematic or interactive physical model, never V0 text walls)"
            )
        if len(r4) < MIN_RUNG_STATEMENT_CHARS:
            issues.append("four_rung_funnel missing rung4_prior_art_deadlock (why mainstream prior-art fixes hit a trade-off ceiling)")

        jargons = funnel.get("rung3_core_jargon_translations", [])
        if not isinstance(jargons, list):
            issues.append("four_rung_funnel.rung3_core_jargon_translations must be a list")
        else:
            for item in jargons:
                if not isinstance(item, dict):
                    continue
                term = str(item.get("term", "")).strip()
                analogy = str(item.get("plain_analogy", "")).strip()
                meaning = str(item.get("physical_meaning", "")).strip()
                if (
                    len(term) >= MIN_TERSE_TERM_CHARS
                    and len(analogy) >= MIN_JARGON_FIELD_CHARS
                    and len(meaning) >= MIN_JARGON_FIELD_CHARS
                ):
                    jargon_count += 1
            if jargon_count < MIN_JARGON_TRANSLATIONS:
                issues.append(
                    f"four_rung_funnel.rung3_core_jargon_translations must translate >={MIN_JARGON_TRANSLATIONS} "
                    "core domain terms with {term, plain_analogy, physical_meaning}"
                )

    if background_bridge.get("paper_claims_strictly_from_pdf") is False:
        issues.append("Provenance violation: paper-specific experimental numbers must strictly come from the PDF")

    bg_indices = _collect_background_slide_indices(background_bridge, slides)
    for idx in sorted(bg_indices):
        if 1 <= idx <= len(slides) and isinstance(slides[idx - 1], dict):
            mod = str(slides[idx - 1].get("required_visual_level", "V2")).strip().upper()
            if mod.startswith("V0") or mod.startswith("V1"):
                issues.append(
                    f"Background slide {idx} uses low visual modality '{mod}'; "
                    "beyond-PDF background slides must use V2 (custom SVG schematic) or V3 (interactive model)"
                )

    effective_full_paper = is_full_paper_deck or (len(slides) >= MIN_FULL_PAPER_SLIDES_THRESHOLD)
    if effective_full_paper and len(bg_indices) < MIN_FULL_PAPER_BG_SLIDES:
        issues.append(
            f"Full-paper deck compresses background into {len(bg_indices)} slide(s); "
            f"must allocate >={MIN_FULL_PAPER_BG_SLIDES} dedicated opening background slides across Rungs 1-4"
        )

    return {
        "passed": len(issues) == 0,
        "background_slide_indices": sorted(bg_indices),
        "background_slide_count": len(bg_indices),
        "jargon_translation_count": jargon_count,
        "omitted_gap_count": len(valid_gaps),
        "issues": issues,
    }


def verify_domain_background_ledger(ledger: Any) -> List[str]:
    """Validate optional Role 0 `domain_background_ledger` entries in `universal_io_bus_capsule`."""
    issues: List[str] = []
    if not isinstance(ledger, list) or len(ledger) == 0:
        return ["domain_background_ledger must be a non-empty list when provided"]
    for idx, entry in enumerate(ledger, start=1):
        if not isinstance(entry, dict):
            issues.append(f"domain_background_ledger[{idx}] must be a dict")
            continue
        tid = str(entry.get("topic_id", "")).strip()
        prin = str(entry.get("beyond_pdf_principle", "")).strip()
        vis = str(entry.get("visual_schematic_plan", "")).strip()
        prov = str(entry.get("provenance_type", VALID_BG_PROVENANCE)).strip().upper()
        if not tid or len(prin) < MIN_RUNG_STATEMENT_CHARS or len(vis) < MIN_VISUAL_SCHEMATIC_CHARS:
            issues.append(
                f"domain_background_ledger[{idx}] must specify topic_id, beyond_pdf_principle, and visual_schematic_plan"
            )
        if prov != VALID_BG_PROVENANCE:
            issues.append(
                f"domain_background_ledger[{idx}] provenance_type='{prov}' must be '{VALID_BG_PROVENANCE}'"
            )
    return issues
