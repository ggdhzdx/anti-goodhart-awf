"""
Beyond-PDF Domain Background Synthesis, AI Value-vs-Routine Triage, Unread-PDF
Intent-First Emphasis & Zero Slide-Count MCQ Validators (`skill.design-anti-goodhart@1.0.0-rc.17`).

Enforces:
1. The 4-Rung Zoom-In Background Funnel (`domain_background_bridge`) so that `TDD`,
   `GRILL`, and `HTML-PPT` decks never jump abruptly into narrow sub-domain PDF jargon;
2. AI Value-vs-Routine Triage (`ai_value_triage`) + Reader-Intent / `JIT_DURING_GRILL`
   emphasis alignment (`verify_unread_pdf_emphasis_alignment`) so unread-PDF users are
   never forced to blindly pick unfamiliar paper module names at Stage 0;
3. Elimination of the Stage 0 Slide-Count MCQ (`verify_logic_driven_slide_count_policy`):
   never ask the user how to choose slide counts or lock fixed page totals—slide count
   emerges purely from logical closure and cognitive need (`UNBOUNDED_FLOW_DRIVEN`);
4. Context-Ready Onion Trunk Peeling (`verify_onion_trunk_context_preview`).
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
MIN_VALUE_GEM_CHARS = 10
MIN_ROUTINE_ZONE_CHARS = 8
MIN_TRUNK_PREVIEW_CHARS = 12
MIN_INTENT_ALIGNED_OPTIONS = 2
RUNG_INDEX_MIN = 1
RUNG_INDEX_MAX = 4

EMPHASIS_POLICY_UPFRONT = "UPFRONT_LOCKED"
EMPHASIS_POLICY_INTENT = "INTENT_MAPPED_AI_RECOMMENDED"
EMPHASIS_POLICY_AI_SEED_JIT = "AI_SEED_PLUS_JIT"
EMPHASIS_POLICY_JIT_GRILL = "JIT_DURING_GRILL"
EMPHASIS_POLICY_JIT_QA = "JIT_DURING_QA"

VALID_EMPHASIS_POLICIES = (
    EMPHASIS_POLICY_UPFRONT,
    EMPHASIS_POLICY_INTENT,
    EMPHASIS_POLICY_AI_SEED_JIT,
    EMPHASIS_POLICY_JIT_GRILL,
    EMPHASIS_POLICY_JIT_QA,
)
PURE_JIT_EMPHASIS_POLICIES = (
    EMPHASIS_POLICY_JIT_GRILL,
    EMPHASIS_POLICY_JIT_QA,
)
TRIAGE_REQUIRED_EMPHASIS_POLICIES = (
    EMPHASIS_POLICY_INTENT,
    EMPHASIS_POLICY_AI_SEED_JIT,
    EMPHASIS_POLICY_JIT_GRILL,
    EMPHASIS_POLICY_JIT_QA,
)

FRAMEWORK_META_JARGON_PATTERNS = (
    r"\bUNBOUNDED_FLOW_DRIVEN\b",
    r"\bJIT_DURING_QA\b",
    r"\bHYBRID_SEED_PLUS_JIT\b",
    r"\bAUTONOMOUS_DUAL_EVOLVE\b",
    r"\bINTENT_MAPPED_AI_RECOMMENDED\b",
    r"\bAI_SEED_PLUS_JIT\b",
    r"\bJIT_DURING_GRILL\b",
    r"\bai_value_triage\b",
    r"\bgdd_grill_capsule\b",
    r"\btdd_station_capsule\b",
    r"\bslide_manifest\.json\b",
    r"\bStage\s*k\.[123]\b",
    r"(?<![A-Za-z0-9_-])V[0-3]\s*(?:动画|交互|静态|纯文字|模态)",
)

BLIND_MODULE_PROMPT_PATTERNS = (
    r"(?:以下|下面)(?:哪些|哪几个)(?:论文|技术|实验)?(?:模块|章节|小节)(?:需要)?(?:作为重头戏|重点展开)",
    r"请选择(?:哪些|哪几个)(?:论文|实验)?(?:模块|章节)(?:作为重头戏|重点深挖)",
)

SLIDE_COUNT_QUIZ_SMUGGLE_PATTERNS = (
    r"(?:总页数|页数策略|页数怎么选|打算做多少页|需要做多少页|选多少页|固定\s*\d+\s*页|\d+\s*[–\-~]\s*\d+\s*页.*档|紧凑档|精简演示档|完整学术报告.*档|百科档)",
)

SLIDE_POLICY_UNBOUNDED = "UNBOUNDED_FLOW_DRIVEN"
SLIDE_POLICY_FIXED = "FIXED"
UNBOUNDED_POLICY_TOKENS = ("UNBOUNDED_FLOW_DRIVEN", "UNBOUNDED", "FLOW_DRIVEN", "不限")

READER_INTENT_OR_JIT_OPTION_PATTERN = re.compile(
    r"(?:推荐|AI\s*主导|核心脑洞|底层机理|破局机理|物理图景|怎么复现|实验配方|方案迁移|"
    r"防坑|组会|审稿|挑刺|铁证|边界代价|边讲边定|边问边定|边走边定|动态|卡壳|不锁死|先不定死)",
    re.IGNORECASE,
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


def verify_ai_value_triage(ai_value_triage: Any) -> Dict[str, Any]:
    """Validate AI's plain-language paper value vs. routine characterization triage."""
    if not isinstance(ai_value_triage, dict) or not ai_value_triage:
        return {
            "passed": False,
            "issues": [
                "Missing ai_value_triage: before asking emphasis choices to an unread-PDF user, "
                "AI must disclose core_breakthrough_gem and routine_fast_forward_zone"
            ],
        }
    issues: List[str] = []
    gem = str(ai_value_triage.get("core_breakthrough_gem", "")).strip()
    routine = str(ai_value_triage.get("routine_fast_forward_zone", "")).strip()
    bridge_note = str(ai_value_triage.get("foundation_bridge_summary", "")).strip()
    if len(gem) < MIN_VALUE_GEM_CHARS:
        issues.append("ai_value_triage missing core_breakthrough_gem (plain-language audit of paper's true highlight)")
    if len(routine) < MIN_ROUTINE_ZONE_CHARS:
        issues.append("ai_value_triage missing routine_fast_forward_zone (which standard checks can be compressed)")
    leaked = scan_framework_meta_jargon(f"{gem} {routine} {bridge_note}")
    if leaked:
        issues.append(f"ai_value_triage leaks internal AWF framework codewords {leaked}; use natural human phrasing")
    return {"passed": len(issues) == 0, "issues": issues}


def _collect_unique_strings(primary: Any, secondary: Any) -> List[str]:
    merged: List[str] = []
    for seq in (primary, secondary):
        if isinstance(seq, list):
            for raw in seq:
                val = str(raw).strip()
                if val and val not in merged:
                    merged.append(val)
    return merged


def _check_unread_question_and_options(
    question_prompt: str,
    options: Sequence[str],
    is_unread_pdf: bool,
) -> List[str]:
    issues: List[str] = []
    combined_text = " ".join([question_prompt, *options])
    leaked = scan_framework_meta_jargon(combined_text)
    if leaked:
        issues.append(f"emphasis_allocation_mcq leaks internal AWF framework codewords {leaked}")
    for pat in BLIND_MODULE_PROMPT_PATTERNS:
        if re.search(pat, question_prompt):
            issues.append(
                "emphasis_allocation_mcq asks a cold paper-module catalog question to an unread-PDF user; "
                "ask reader intent/audience lens or offer AI-recommended + dynamic JIT discovery instead"
            )
            break
    if is_unread_pdf and options:
        intent_hits = sum(1 for opt in options if READER_INTENT_OR_JIT_OPTION_PATTERN.search(opt))
        if intent_hits < MIN_INTENT_ALIGNED_OPTIONS:
            issues.append(
                "Unread-PDF emphasis_allocation_mcq options dump raw paper modules without reader-intent lenses "
                "or dynamic JIT choices (e.g., core mechanism insight, experimental recipe, critique, or decide-as-we-go)"
            )
    return issues


def verify_unread_pdf_emphasis_alignment(
    emp_mcq: Dict[str, Any],
    global_triage: Any = None,
    probe_unread: Any = None,
) -> Dict[str, Any]:
    """Verify Stage 0 emphasis_allocation_mcq never forces unread-PDF users into blind module guessing."""
    issues: List[str] = []
    raw_policy = str(emp_mcq.get("emphasis_policy", EMPHASIS_POLICY_UPFRONT)).strip().upper()
    policy = raw_policy or EMPHASIS_POLICY_UPFRONT
    if policy not in VALID_EMPHASIS_POLICIES:
        issues.append(f"Unsupported emphasis_policy '{policy}'; expected one of {VALID_EMPHASIS_POLICIES}")

    is_unread_pdf = (emp_mcq.get("user_has_read_pdf") is False) or (probe_unread is False)
    effective_mods = _collect_unique_strings(
        emp_mcq.get("heavy_focus_modules"),
        emp_mcq.get("ai_seed_focus_modules"),
    )
    if policy not in PURE_JIT_EMPHASIS_POLICIES and len(effective_mods) < 1:
        issues.append(
            "emphasis_allocation_mcq must list >=1 heavy_focus_modules (or ai_seed_focus_modules), "
            "or set emphasis_policy='JIT_DURING_GRILL' for dynamic discovery during Q&A"
        )

    if is_unread_pdf and policy == EMPHASIS_POLICY_UPFRONT:
        issues.append(
            "Unread-PDF user cannot be forced into UPFRONT_LOCKED paper-module selection; "
            "use INTENT_MAPPED_AI_RECOMMENDED, AI_SEED_PLUS_JIT, or JIT_DURING_GRILL"
        )

    triage_verified = False
    if is_unread_pdf or policy in TRIAGE_REQUIRED_EMPHASIS_POLICIES:
        local_triage = emp_mcq.get("ai_value_triage")
        triage_res = verify_ai_value_triage(local_triage if isinstance(local_triage, dict) else global_triage)
        triage_verified = bool(triage_res["passed"])
        issues.extend(triage_res["issues"])
        raw_opts = emp_mcq.get("options", [])
        clean_opts = [str(o).strip() for o in (raw_opts if isinstance(raw_opts, list) else []) if str(o).strip()]
        q_prompt = str(emp_mcq.get("question_prompt", "")).strip()
        issues.extend(_check_unread_question_and_options(q_prompt, clean_opts, is_unread_pdf))

    return {
        "passed": len(issues) == 0,
        "emphasis_policy": policy,
        "is_unread_pdf": is_unread_pdf,
        "ai_value_triage_verified": triage_verified,
        "effective_focus_modules": effective_mods,
        "issues": issues,
    }


def verify_onion_trunk_context_preview(
    peeled_trunk: Dict[str, Any],
    require_preview: bool,
) -> List[str]:
    """Ensure inner onion trunk peeling gives unread-PDF users a plain-language context preview first."""
    tid = str(peeled_trunk.get("trunk_id", "")).strip()
    preview = str(peeled_trunk.get("trunk_context_preview", "")).strip()
    issues: List[str] = []
    if require_preview and len(preview) < MIN_TRUNK_PREVIEW_CHARS:
        issues.append(
            f"Peeled trunk '{tid}' missing trunk_context_preview: provide a plain-language summary of what "
            "this trunk covers before asking an unread-PDF user to pick trunk_subframe_mcq"
        )
    if preview:
        leaked = scan_framework_meta_jargon(preview)
        if leaked:
            issues.append(f"trunk_context_preview for '{tid}' leaks internal AWF framework codewords {leaked}")
    return issues


def _check_smuggled_slide_count_prompts(blueprint: Dict[str, Any]) -> List[str]:
    issues: List[str] = []
    for mcq_key in ("logical_flow_mcq", "emphasis_allocation_mcq", "v3_animation_budget_mcq"):
        mcq_obj = blueprint.get(mcq_key)
        if not isinstance(mcq_obj, dict):
            continue
        texts = [str(mcq_obj.get("question_prompt", "")).strip()]
        raw_opts = mcq_obj.get("options", [])
        if isinstance(raw_opts, list):
            texts.extend(str(opt).strip() for opt in raw_opts if str(opt).strip())
        combined = " ".join(t for t in texts if t)
        for pat in SLIDE_COUNT_QUIZ_SMUGGLE_PATTERNS:
            if re.search(pat, combined):
                issues.append(
                    f"{mcq_key} asks or offers slide-count selection; slide-count MCQs are eliminated "
                    "and total slides must follow logical flow and need without asking the user"
                )
                break
    return issues


def verify_logic_driven_slide_count_policy(
    global_deck_blueprint: Dict[str, Any],
    expected_storyboard_count: int = 0,
    has_revisions: bool = False,
    is_unread_pdf: bool = False,
) -> Dict[str, Any]:
    """
    Enforce the Unconditional Zero Slide-Count MCQ Law:
    - Slide-count selection MCQs (`total_slides_mcq`) and pre-locked / fixed page totals
      (`planned_total_slides`, `elastic_slide_range`) are unconditionally eliminated.
    - Total slide count emerges purely from logical closure and cognitive need
      (`UNBOUNDED_FLOW_DRIVEN`), without asking the user how to choose slide counts.
    """
    _ = (expected_storyboard_count, has_revisions, is_unread_pdf)
    issues: List[str] = _check_smuggled_slide_count_prompts(global_deck_blueprint)

    if "total_slides_mcq" in global_deck_blueprint and global_deck_blueprint.get("total_slides_mcq") is not None:
        issues.append(
            "Slide-count MCQ is unconditionally eliminated: never ask the user how to choose slide counts "
            "or include total_slides_mcq; omit total_slides_mcq so slides grow purely by logic and need"
        )

    top_policy = str(global_deck_blueprint.get("slide_count_policy", SLIDE_POLICY_UNBOUNDED)).strip().upper()
    top_planned = global_deck_blueprint.get("planned_total_slides")
    has_fixed_planned = (
        top_planned is not None
        and str(top_planned).strip().upper() not in ("", *UNBOUNDED_POLICY_TOKENS)
    )
    has_elastic_range = bool(global_deck_blueprint.get("elastic_slide_range"))
    if (top_policy and top_policy not in UNBOUNDED_POLICY_TOKENS) or has_fixed_planned or has_elastic_range:
        issues.append(
            "Fixed or bounded total slide count is forbidden: never preset total pages or ranges; "
            "let slide count emerge purely from logical flow and cognitive need (UNBOUNDED_FLOW_DRIVEN)"
        )

    return {
        "slide_count_policy": SLIDE_POLICY_UNBOUNDED,
        "planned_total_slides": 0,
        "min_slides_floor": 1,
        "max_slides_ceiling": 0,
        "slide_count_mcq_eliminated": "total_slides_mcq" not in global_deck_blueprint
        or global_deck_blueprint.get("total_slides_mcq") is None,
        "issues": issues,
    }
