#!/usr/bin/env python3
"""
AWF HTML-PPT V3 Tri-Mode Single-Slide Atomic Micro-Step Gatekeeper (`skill.html-ppt@1.0.0-rc.22`).

Physically enforces:
1. Strictly 1 Slide Per Step (`max_slides_generated_per_step == 1`);
2. 1-Hop Slide Topological Lock (`unverified_slide_hop_distance == 1` via `slide_manifest.json`);
3. Beyond-PDF 4-Rung Domain Background Synthesis & Plain-Language Jargon Bridge
   (`domain_background_bridge` + `--record-background-bridge`, requiring >=3 V2/V3 background
   onboarding slides on full-paper decks and briefing-first `FOUNDATION_INTUITION_BUILD` grills);
4. Unread-PDF AI Value-vs-Routine Triage (`ai_value_triage`), Reader-Intent / `JIT_DURING_GRILL`
   Emphasis Alignment, Elimination of the Stage 0 Slide-Count MCQ (`forbid_slide_count_mcq`: never
   ask how to pick slide counts or preset fixed page totals—only follow logic and cognitive need),
   Mid-Stream `PROMOTE_HEAVY_FOCUS` / `COMPRESS_ROUTINE_MODULE` mutations, and Context-Ready Onion Trunk Peeling;
5. Zero AI Self-Scaffolding Meta-Labels on Visible Slides (`D3`), Intra-Slide Semantic Coherence
   (`D3`/`D4`/`D6`/`D8`/`D16`: banning bare verbless noun-label card strips, unanchored bottom
   ballast strips, and `>30%` deck-wide bottom-grid cloning), Anti-Collusion Zero-Context Blind
   Reader Reconstruction (`D18` + `--verify-blind-reader`), Inline-SVG & Visible HTML Minimum
   Typography (`>=18.0px` globally, `>=22.0px` for body/card `<p>`/`<li>` on `1920x1080` canvases),
   Hollow Text-Card Underfill Prevention, & Single-Slide Character / SVG-Label Overload Guards
   (`MAX_VISIBLE_CHARS_PER_SLIDE = 650`, `MAX_INLINE_SVG_SUBSTANTIVE_LABELS = 22`);
6. Tri-Mode Execution Architecture:
   - Mode 1 (`TDD` / Tutor-Driven Design): 1 Tutor Station == 1 TDD Capsule (`record_tdd_station_capsule`) == 1 Slide;
   - Mode 2 (`GRILL` / Grill-Driven Design): Briefing-first + Agent quizzes -> Teach-on-Miss & Re-grill -> 1 Grill Capsule (`record_grill_station_capsule`) == 1 Slide;
   - Mode 3 (`AUTONOMOUS_DUAL_EVOLVE` / Head-Down Build + Post-Review Dual-Evolution): Head-down autonomous 1-slide-per-step deck generation (`require_human_approval=False`), followed by `apply_human_feedback_dual_upgrade` which simultaneously patches/re-audits the PPT slide(s) AND records/verifies the AWF HTML-PPT / DesignAG gate + negative canary upgrade receipt;
7. Optional Human-in-the-Loop Sign-off Gate (`require_human_approval` + `approve_slide_by_human`);
8. Full 18-Gate DesignAG audit (`skill.design-anti-goodhart@1.0.0-rc.20`) + SHA-256 lock before assembly.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

sys.dont_write_bytecode = True

FULL_PAPER_BG_SLIDE_THRESHOLD = 10
SELFTEST_OVERLOAD_SVG_LABEL_COUNT = 37
SELFTEST_OVERLOAD_PROSE_REPEAT = 18
EXPECTED_SELFTEST_CHECKS = 24


def _resolve_design_ag_scripts_dir() -> Path:
    from awf_pinned_dependency import dependency_scripts
    return dependency_scripts("design-anti-goodhart", "1.0.0-rc.25")


def _load_design_ag_module() -> Any:
    from awf_pinned_dependency import load_exact
    return load_exact(_resolve_design_ag_scripts_dir(), "awf_design_anti_goodhart_gates")


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _int_val(d: Dict[str, Any], key: str, fallback: int) -> int:
    val = d.get(key)
    return int(val) if isinstance(val, (int, float)) else fallback


def _compute_hop_distance(slides_list: Sequence[Dict[str, Any]], slide_index: int) -> int:
    last_pass_idx = 0
    for entry in slides_list:
        idx = _int_val(entry, "slide_index", 0)
        if entry.get("status") == "PASS" and idx == last_pass_idx + 1:
            last_pass_idx = idx
    hop_distance = slide_index - last_pass_idx
    if slide_index <= last_pass_idx:
        hop_distance = 1
    return hop_distance


def init_storyboard_manifest(
    storyboard_doc: Dict[str, Any],
    manifest_path: Path,
) -> Dict[str, Any]:
    """
    Validate Storyboard against DesignAG Gates D13, D14, D16 (`max_slides_generated_per_step == 1`)
    and initialize `slide_manifest.json` with ONLY `slide_01` (`Station_01`) unlocked.
    Supports Tri-Mode:
      - `TDD` (`tdd_mode=True`)
      - `GRILL` (`grill_mode=True`)
      - `AUTONOMOUS_DUAL_EVOLVE` (`autonomous_dual_evolve_mode=True`, `require_human_approval=False` during draft)
    """
    dag = _load_design_ag_module()
    slides_spec = storyboard_doc.get("storyboard_slides", [])
    raw_mode = str(storyboard_doc.get("workflow_mode", "")).strip().upper()
    tdd_mode = bool(storyboard_doc.get("tdd_mode", False)) or (raw_mode == "TDD")
    grill_mode = bool(storyboard_doc.get("grill_mode", False)) or (raw_mode == "GRILL")
    autonomous_dual_evolve_mode = (
        bool(storyboard_doc.get("autonomous_dual_evolve_mode", False))
        or (raw_mode == "AUTONOMOUS_DUAL_EVOLVE")
    )
    if not raw_mode:
        if grill_mode:
            raw_mode = "GRILL"
        elif tdd_mode:
            raw_mode = "TDD"
        else:
            raw_mode = "AUTONOMOUS_DUAL_EVOLVE"
            autonomous_dual_evolve_mode = True

    require_human_approval = bool(storyboard_doc.get("require_human_approval", False))
    global_blueprint = storyboard_doc.get("global_deck_blueprint")
    onion_capsule = storyboard_doc.get("onion_peeling_capsule")
    io_bus_capsule = storyboard_doc.get("universal_io_bus_capsule")
    lossless_ledger = storyboard_doc.get("lossless_split_and_popover_ledger")
    raw_narrative = dict(storyboard_doc.get("narrative_spec") or {})
    domain_background_bridge = storyboard_doc.get("domain_background_bridge") or raw_narrative.get(
        "domain_background_bridge"
    )
    require_beyond_pdf_bg = bool(storyboard_doc.get("require_beyond_pdf_background", False))
    is_full_paper = len(slides_spec) >= FULL_PAPER_BG_SLIDE_THRESHOLD or bool(
        raw_narrative.get("is_full_paper_deck", False)
    )
    if require_beyond_pdf_bg or is_full_paper:
        raw_narrative["require_beyond_pdf_background_bridge"] = True
        if is_full_paper:
            raw_narrative["is_full_paper_deck"] = True

    d13 = dag.verify_narrative_arc_and_foreshadowing(
        raw_narrative,
        storyboard_slides=slides_spec,
        domain_background_bridge=domain_background_bridge,
        universal_io_bus_capsule=io_bus_capsule,
    )
    d14 = dag.verify_causal_why_chain_and_tradeoffs(storyboard_doc.get("mechanism_spec", {}))
    d16 = dag.verify_storyboard_microstep_and_layout_diversity(
        slides_spec,
        max_slides_generated_per_step=1,
        unverified_slide_hop_distance=1,
        global_deck_blueprint=global_blueprint,
        onion_peeling_capsule=onion_capsule,
        universal_io_bus_capsule=io_bus_capsule,
        lossless_split_and_popover_ledger=lossless_ledger,
    )

    failed_gates = [g["gate"] for g in (d13, d14, d16) if not g.get("passed")]
    if failed_gates:
        return {
            "status": "FAIL",
            "stage": "Stage1_Storyboard_Contract",
            "failed_gates": failed_gates,
            "details": {"D13": d13, "D14": d14, "D16": d16},
        }

    v3_designated_set = set()
    if isinstance(global_blueprint, dict):
        anim_mcq = global_blueprint.get("v3_animation_budget_mcq", {})
        if isinstance(anim_mcq, dict):
            for idx_val in anim_mcq.get("v3_designated_slide_indices", []):
                if isinstance(idx_val, (int, float)):
                    v3_designated_set.add(int(idx_val))

    bg_index_set = set()
    if isinstance(domain_background_bridge, dict):
        for idx_val in domain_background_bridge.get("background_slide_indices", []):
            if isinstance(idx_val, (int, float)) and not isinstance(idx_val, bool):
                bg_index_set.add(int(idx_val))

    slide_entries: List[Dict[str, Any]] = []
    for idx, s in enumerate(slides_spec, start=1):
        station_id = str(s.get("station_id", f"Station_1.{idx}"))
        is_v3_focus = (idx in v3_designated_set) or str(s.get("required_visual_level", "")).upper().startswith("V3")
        bg_rung = s.get("background_rung")
        is_bg_slide = (
            (idx in bg_index_set)
            or bool(s.get("is_background_slide", False))
            or (isinstance(bg_rung, int) and not isinstance(bg_rung, bool) and 1 <= bg_rung <= 4)
        )
        slide_entries.append({
            "slide_index": idx,
            "slide_id": f"slide_{idx:02d}",
            "station_id": station_id,
            "flow_module": str(s.get("flow_module", "")),
            "title": str(s.get("title", f"Slide {idx}")),
            "layout_archetype": str(s.get("layout_archetype", "split_left_fig_right_guided_steps")),
            "required_visual_level": "V3" if is_v3_focus else str(s.get("required_visual_level", "V2")),
            "designated_v3_animation": is_v3_focus,
            "is_background_slide": is_bg_slide,
            "background_rung": bg_rung if isinstance(bg_rung, int) and not isinstance(bg_rung, bool) else None,
            "tdd_station_capsule": s.get("tdd_station_capsule"),
            "gdd_grill_capsule": s.get("gdd_grill_capsule"),
            "cross_artifact_receipts": {},
            "human_approved": False,
            "human_note": "",
            "status": "UNLOCKED" if idx == 1 else "LOCKED",
            "sha256": "",
            "file_path": "",
        })

    manifest_data = {
        "schema_version": 10,
        "workflow_mode": raw_mode,
        "max_slides_generated_per_step": 1,
        "tdd_mode": tdd_mode,
        "grill_mode": grill_mode,
        "autonomous_dual_evolve_mode": autonomous_dual_evolve_mode,
        "require_human_approval": require_human_approval,
        "require_beyond_pdf_background": require_beyond_pdf_bg,
        "domain_background_bridge": domain_background_bridge,
        "global_deck_blueprint": global_blueprint,
        "onion_peeling_capsule": onion_capsule,
        "universal_io_bus_capsule": io_bus_capsule,
        "lossless_split_and_popover_ledger": lossless_ledger,
        "total_slides": len(slide_entries),
        "storyboard_slides": slides_spec,
        "slides": slide_entries,
        "storyboard_revisions": [],
        "dual_evolution_receipts": [],
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest_data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {
        "status": "PASS",
        "stage": "Stage1_Storyboard_Contract",
        "workflow_mode": raw_mode,
        "tdd_mode": tdd_mode,
        "grill_mode": grill_mode,
        "autonomous_dual_evolve_mode": autonomous_dual_evolve_mode,
        "require_human_approval": require_human_approval,
        "total_slides": len(slide_entries),
        "unlocked_slide": "slide_01",
        "unlocked_station": slide_entries[0]["station_id"] if slide_entries else "",
        "manifest_path": str(manifest_path),
    }


def record_cross_artifact_unit_receipt(
    manifest_path: Path,
    slide_index_or_receipt: Any,
    unit_receipt: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Role 3 (`OmniArtifactHub` — 跨载体同源总调度官):
    From the same shared Onion Leaf (`slide_index`), record and verify a 1-Unit-Per-Step output
    for `SCI_WORD` (`AWF SciWord` manuscript section/paragraph) or `FIG_PPTX` (`AWF FigPPT / SciFig`
    editable figure panel), ensuring it binds to `evidence_ingest_ledger` and `devil_advocate_review`.
    """
    if isinstance(slide_index_or_receipt, dict) and unit_receipt is None:
        unit_receipt = slide_index_or_receipt
        slide_index = _int_val(unit_receipt, "slide_index", 1)
    else:
        slide_index = int(slide_index_or_receipt)
        unit_receipt = unit_receipt or {}

    if not manifest_path.is_file():
        return {"status": "FAIL", "reason": f"Missing slide_manifest.json: {manifest_path}"}
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    slides_list: List[Dict[str, Any]] = manifest.get("slides", [])
    if slide_index < 1 or slide_index > len(slides_list):
        return {"status": "FAIL", "reason": f"Invalid slide_index {slide_index}"}

    hop_distance = _compute_hop_distance(slides_list, slide_index)
    if hop_distance != 1:
        return {
            "status": "FAIL",
            "slide_index": slide_index,
            "reason": f"1-Hop Cross-Artifact lock violation: unverified_slide_hop_distance={hop_distance} != 1",
        }

    artifact_type = str(
        unit_receipt.get("artifact_type") or unit_receipt.get("artifact_channel") or ""
    ).strip().upper()
    if artifact_type not in {"SCI_WORD", "FIG_PPTX", "HTML_PPT"}:
        return {"status": "FAIL", "reason": f"Unsupported artifact_type: {artifact_type}"}

    raw_claims = unit_receipt.get("evidence_claim_ids_used")
    if isinstance(raw_claims, list) and raw_claims:
        cited_claim_id = str(raw_claims[0]).strip()
    else:
        cited_claim_id = str(unit_receipt.get("cited_claim_id", "")).strip()

    unit_summary = str(
        unit_receipt.get("unit_summary") or unit_receipt.get("unit_id") or ""
    ).strip()
    if not cited_claim_id or len(unit_summary) < 5:
        return {
            "status": "FAIL",
            "reason": "Cross-artifact unit receipt must bind cited_claim_id (from EvidenceIngest) and unit_summary/unit_id",
        }

    io_bus = manifest.get("universal_io_bus_capsule") or {}
    ledger = io_bus.get("evidence_ingest_ledger", [])
    known_claims = {str(item.get("claim_id", "")).strip() for item in ledger if isinstance(item, dict)}
    if known_claims and cited_claim_id not in known_claims:
        return {
            "status": "FAIL",
            "reason": f"Unanchored claim_id '{cited_claim_id}' not found in EvidenceIngest ledger {sorted(known_claims)}",
        }

    target_entry = slides_list[slide_index - 1]
    receipts_map = target_entry.setdefault("cross_artifact_receipts", {})
    receipts_map[artifact_type] = {
        "artifact_type": artifact_type,
        "cited_claim_id": cited_claim_id,
        "unit_summary": unit_summary,
        "awf_skill_id": str(unit_receipt.get("awf_skill_id", "")),
        "status": "PASS",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {
        "status": "PASS",
        "slide_index": slide_index,
        "artifact_type": artifact_type,
        "cited_claim_id": cited_claim_id,
    }


def peel_onion_trunk_subframe(
    manifest_path: Path,
    trunk_peel_spec: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Hierarchical Onion Peeling Engine (分级洋葱剥皮流程 — 进入某一个主干，确定该主干内的细分框架):
    1. Verifies that all existing leaf slides of any currently peeled trunk have passed (`status == "PASS"`)
       before peeling the next macro trunk (`trunk_id`);
    2. Validates `trunk_subframe_mcq` and 1-hop trunk order via `dag.verify_onion_peeling_capsule`;
    3. Materializes `LEAF_SLIDE` sub-nodes of the newly peeled trunk into `slides` and unlocks the
       first newly materialized leaf slide.
    """
    dag = _load_design_ag_module()
    if not manifest_path.is_file():
        return {"status": "FAIL", "reason": f"Missing slide_manifest.json: {manifest_path}"}
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    onion = manifest.get("onion_peeling_capsule")
    if not isinstance(onion, dict):
        return {"status": "FAIL", "reason": "Manifest has no onion_peeling_capsule"}

    slides_list: List[Dict[str, Any]] = manifest.get("slides", [])
    sb_list: List[Dict[str, Any]] = manifest.get("storyboard_slides", [])
    unfinished = [s["slide_id"] for s in slides_list if s.get("status") != "PASS"]
    if unfinished:
        return {
            "status": "FAIL",
            "reason": f"Cannot peel next onion trunk while leaf slides of current trunk remain unfinished: {unfinished}",
        }

    # Mark previously PEELING trunks as PASS now that their leaf slides are all PASS
    layer0 = onion.get("layer0_macro_frame") or {}
    mcq0 = layer0.get("macro_trunks_mcq") or {}
    macro_trunks: List[Dict[str, Any]] = mcq0.get("macro_trunks", [])
    target_tid = str(trunk_peel_spec.get("trunk_id", "")).strip()
    for t in macro_trunks:
        if isinstance(t, dict) and str(t.get("status", "")).upper() == "PEELING":
            t["status"] = "PASS"

    # Candidate update to onion capsule
    peeled_trunks: List[Dict[str, Any]] = list(onion.get("peeled_trunks", []))
    peeled_trunks.append(trunk_peel_spec)
    candidate_onion = {**onion, "peeled_trunks": peeled_trunks}
    on_check = dag.verify_onion_peeling_capsule(candidate_onion)
    if not on_check.get("passed"):
        return {
            "status": "FAIL",
            "reason": "Onion trunk peeling violated 1-hop trunk order or sub-framework MCQ contract",
            "onion_check": on_check,
        }

    for t in macro_trunks:
        if isinstance(t, dict) and str(t.get("trunk_id", "")).strip() == target_tid:
            t["status"] = "PEELING"

    sub_mcq = trunk_peel_spec.get("trunk_subframe_mcq") or {}
    sub_nodes = sub_mcq.get("sub_nodes", [])
    added_slides: List[str] = []
    for node in sub_nodes:
        if not isinstance(node, dict):
            continue
        if str(node.get("node_type", "LEAF_SLIDE")).upper() == "LEAF_SLIDE":
            new_idx = len(slides_list) + 1
            is_v3 = bool(node.get("designated_v3_animation", False)) or str(
                node.get("required_visual_level", "")
            ).upper().startswith("V3")
            bg_rung = node.get("background_rung")
            is_bg = bool(node.get("is_background_slide", False)) or (
                isinstance(bg_rung, int) and not isinstance(bg_rung, bool) and 1 <= bg_rung <= 4
            )
            new_entry = {
                "slide_index": new_idx,
                "slide_id": f"slide_{new_idx:02d}",
                "station_id": str(node.get("node_id", f"Station_{target_tid}_{new_idx}")),
                "flow_module": target_tid,
                "title": str(node.get("title", f"{target_tid} Slide {new_idx}")),
                "layout_archetype": str(node.get("layout_archetype", "interactive_svg_sandbox_split")),
                "required_visual_level": "V3" if is_v3 else str(node.get("required_visual_level", "V2")),
                "designated_v3_animation": is_v3,
                "is_background_slide": is_bg,
                "background_rung": bg_rung if isinstance(bg_rung, int) and not isinstance(bg_rung, bool) else None,
                "tdd_station_capsule": None,
                "gdd_grill_capsule": None,
                "human_approved": False,
                "human_note": "",
                "status": "UNLOCKED" if len(added_slides) == 0 else "LOCKED",
                "sha256": "",
                "file_path": "",
            }
            slides_list.append(new_entry)
            sb_list.append(
                {
                    "station_id": new_entry["station_id"],
                    "flow_module": target_tid,
                    "title": new_entry["title"],
                    "layout_archetype": new_entry["layout_archetype"],
                    "required_visual_level": new_entry["required_visual_level"],
                }
            )
            added_slides.append(new_entry["slide_id"])

    onion["peeled_trunks"] = peeled_trunks
    manifest["onion_peeling_capsule"] = onion
    manifest["total_slides"] = len(slides_list)
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {
        "status": "PASS",
        "peeled_trunk_id": target_tid,
        "added_leaf_slides": added_slides,
        "total_slides": len(slides_list),
    }


def mutate_storyboard_manifest(
    manifest_path: Path,
    mutation_spec: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Mid-Stream Elastic Storyboard, Unbounded Flow-Driven Slide Growth & JIT V3 Animation Engine:
    Allows appending/splitting/inserting slides along the logical flow (`APPEND_FLOW_SLIDE`,
    `INSERT_SLIDE`, `SPLIT_SLIDE`), merging/removing future slides (`REMOVE_SLIDE`, `MERGE_SLIDES`),
    or dynamically promoting/demoting V3 animations (`PROMOTE_V3`, `DEMOTE_V3`) during Stage 1-3 Q&A
    while preserving the 1-Hop DAG lock and SHA-256 receipts of already-completed slides.
    """
    if not manifest_path.is_file():
        return {"status": "FAIL", "reason": f"Missing slide_manifest.json: {manifest_path}"}
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    slides_list: List[Dict[str, Any]] = manifest.get("slides", [])
    sb_list: List[Dict[str, Any]] = manifest.get("storyboard_slides", [])

    action = str(mutation_spec.get("action", "")).strip().upper()
    target_idx = _int_val(mutation_spec, "target_slide_index", len(slides_list))
    reason = str(mutation_spec.get("reason", "")).strip()
    trigger_source = str(mutation_spec.get("trigger_source", "QA_DISCOVERY")).strip().upper()

    if len(reason) < 6:
        return {"status": "FAIL", "reason": "Storyboard mutation requires an explicit reason (>=6 chars)"}
    if target_idx < 1 or target_idx > len(slides_list):
        return {"status": "FAIL", "reason": f"Invalid target_slide_index {target_idx}"}

    old_total = len(slides_list)
    if action in {"APPEND_FLOW_SLIDE", "INSERT_SLIDE", "SPLIT_SLIDE"}:
        new_slide_spec = mutation_spec.get("new_slide_spec") or {}
        insert_pos = len(slides_list) if action == "APPEND_FLOW_SLIDE" else target_idx
        is_v3 = bool(new_slide_spec.get("designated_v3_animation", False)) or str(
            new_slide_spec.get("required_visual_level", "")
        ).upper().startswith("V3")
        bg_rung = new_slide_spec.get("background_rung")
        is_bg = bool(new_slide_spec.get("is_background_slide", False)) or (
            isinstance(bg_rung, int) and not isinstance(bg_rung, bool) and 1 <= bg_rung <= 4
        )
        new_entry = {
            "slide_index": insert_pos + 1,
            "slide_id": f"slide_{insert_pos + 1:02d}",
            "station_id": str(new_slide_spec.get("station_id", f"Station_1.{insert_pos + 1}_flow")),
            "flow_module": str(new_slide_spec.get("flow_module", "")),
            "title": str(new_slide_spec.get("title", f"Flow Slide {insert_pos + 1}")),
            "layout_archetype": str(new_slide_spec.get("layout_archetype", "interactive_svg_sandbox_split")),
            "required_visual_level": "V3" if is_v3 else str(new_slide_spec.get("required_visual_level", "V2")),
            "designated_v3_animation": is_v3,
            "is_background_slide": is_bg,
            "background_rung": bg_rung if isinstance(bg_rung, int) and not isinstance(bg_rung, bool) else None,
            "tdd_station_capsule": None,
            "gdd_grill_capsule": None,
            "human_approved": False,
            "human_note": "",
            "status": "LOCKED",
            "sha256": "",
            "file_path": "",
        }
        slides_list.insert(insert_pos, new_entry)
        sb_list.insert(
            insert_pos,
            {
                "station_id": new_entry["station_id"],
                "flow_module": new_entry["flow_module"],
                "title": new_entry["title"],
                "layout_archetype": new_entry["layout_archetype"],
                "required_visual_level": new_entry["required_visual_level"],
            },
        )
    elif action in {"REMOVE_SLIDE", "MERGE_SLIDES"}:
        if len(slides_list) <= 1:
            return {"status": "FAIL", "reason": "Cannot remove the only remaining slide"}
        target_entry = slides_list[target_idx - 1]
        if target_entry.get("status") == "PASS":
            return {"status": "FAIL", "reason": "Cannot remove an already verified (PASS) slide"}
        gb = manifest.get("global_deck_blueprint") or {}
        slides_mcq = gb.get("total_slides_mcq") or {}
        el_range = slides_mcq.get("elastic_slide_range", [])
        min_floor = int(el_range[0]) if isinstance(el_range, list) and len(el_range) == 2 else 1
        if len(slides_list) - 1 < min_floor and not bool(mutation_spec.get("human_override_floor", False)):
            return {
                "status": "FAIL",
                "reason": f"Cannot shrink deck ({len(slides_list) - 1}) below elastic min_slides_floor ({min_floor})",
            }
        slides_list.pop(target_idx - 1)
        if target_idx - 1 < len(sb_list):
            sb_list.pop(target_idx - 1)
    elif action == "PROMOTE_V3":
        target_entry = slides_list[target_idx - 1]
        target_entry["designated_v3_animation"] = True
        target_entry["required_visual_level"] = "V3"
    elif action == "DEMOTE_V3":
        target_entry = slides_list[target_idx - 1]
        target_entry["designated_v3_animation"] = False
        target_entry["required_visual_level"] = "V2"
    elif action == "PROMOTE_HEAVY_FOCUS":
        target_entry = slides_list[target_idx - 1]
        target_entry["is_heavy_focus"] = True
        mod_name = str(
            mutation_spec.get("focus_module")
            or target_entry.get("flow_module")
            or target_entry.get("title")
            or ""
        ).strip()
        gb = manifest.get("global_deck_blueprint")
        if isinstance(gb, dict) and isinstance(gb.get("emphasis_allocation_mcq"), dict) and mod_name:
            emp_mcq = gb["emphasis_allocation_mcq"]
            for key in ("heavy_focus_modules", "jit_discovered_focus_modules"):
                lst = emp_mcq.setdefault(key, [])
                if isinstance(lst, list) and mod_name not in lst:
                    lst.append(mod_name)
        companion_spec = mutation_spec.get("new_slide_spec")
        if isinstance(companion_spec, dict) and companion_spec:
            comp_v3 = bool(companion_spec.get("designated_v3_animation", False)) or str(
                companion_spec.get("required_visual_level", "")
            ).upper().startswith("V3")
            comp_entry = {
                "slide_index": target_idx + 1,
                "slide_id": f"slide_{target_idx + 1:02d}",
                "station_id": str(companion_spec.get("station_id", f"Station_1.{target_idx + 1}_deepdive")),
                "flow_module": mod_name,
                "title": str(companion_spec.get("title", f"{mod_name} 深度展开")),
                "layout_archetype": str(companion_spec.get("layout_archetype", "interactive_svg_sandbox_split")),
                "required_visual_level": "V3" if comp_v3 else str(companion_spec.get("required_visual_level", "V2")),
                "designated_v3_animation": comp_v3,
                "is_background_slide": False,
                "background_rung": None,
                "is_heavy_focus": True,
                "tdd_station_capsule": None,
                "gdd_grill_capsule": None,
                "human_approved": False,
                "human_note": "",
                "status": "LOCKED",
                "sha256": "",
                "file_path": "",
            }
            slides_list.insert(target_idx, comp_entry)
            sb_list.insert(
                target_idx,
                {
                    "station_id": comp_entry["station_id"],
                    "flow_module": comp_entry["flow_module"],
                    "title": comp_entry["title"],
                    "layout_archetype": comp_entry["layout_archetype"],
                    "required_visual_level": comp_entry["required_visual_level"],
                },
            )
    elif action == "COMPRESS_ROUTINE_MODULE":
        target_entry = slides_list[target_idx - 1]
        target_entry["is_routine_fast_forward"] = True
        mod_name = str(
            mutation_spec.get("focus_module")
            or target_entry.get("flow_module")
            or target_entry.get("title")
            or ""
        ).strip()
        gb = manifest.get("global_deck_blueprint")
        if isinstance(gb, dict) and isinstance(gb.get("emphasis_allocation_mcq"), dict) and mod_name:
            ff_list = gb["emphasis_allocation_mcq"].setdefault("fast_forwarded_modules", [])
            if isinstance(ff_list, list) and mod_name not in ff_list:
                ff_list.append(mod_name)
    else:
        return {"status": "FAIL", "reason": f"Unsupported mutation action: {action}"}

    # Re-index all slides and maintain 1-Hop UNLOCKED pointer after last PASS slide
    last_pass = 0
    for idx, entry in enumerate(slides_list, start=1):
        entry["slide_index"] = idx
        entry["slide_id"] = f"slide_{idx:02d}"
        if entry.get("status") == "PASS" and idx == last_pass + 1:
            last_pass = idx
    if last_pass < len(slides_list):
        nxt_entry = slides_list[last_pass]
        if nxt_entry.get("status") == "LOCKED":
            nxt_entry["status"] = "UNLOCKED"

    rev_record = {
        "action": action,
        "target_slide_index": target_idx,
        "trigger_source": trigger_source,
        "reason": reason,
        "old_total_slides": old_total,
        "new_total_slides": len(slides_list),
    }
    manifest.setdefault("storyboard_revisions", []).append(rev_record)
    if isinstance(manifest.get("global_deck_blueprint"), dict):
        manifest["global_deck_blueprint"].setdefault("storyboard_revisions", []).append(rev_record)
    manifest["total_slides"] = len(slides_list)
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {
        "status": "PASS",
        "action": action,
        "old_total_slides": old_total,
        "new_total_slides": len(slides_list),
        "total_revisions": len(manifest["storyboard_revisions"]),
    }


def record_domain_background_bridge(
    manifest_path: Path,
    bridge_doc: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Record and validate Role 0 (`BackgroundSynthesizer & AudienceTranslator`)
    `domain_background_bridge` on `slide_manifest.json` (`--record-background-bridge`),
    ensuring 4-rung beyond-PDF background synthesis & plain-language jargon translation.
    """
    if not manifest_path.is_file():
        return {"status": "FAIL", "reason": f"Missing slide_manifest.json: {manifest_path}"}
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    slides_list: List[Dict[str, Any]] = manifest.get("slides", [])
    dag = _load_design_ag_module()
    is_full = len(slides_list) >= FULL_PAPER_BG_SLIDE_THRESHOLD or bool(
        manifest.get("require_beyond_pdf_background", False)
    )
    check = dag.verify_domain_background_bridge_capsule(
        bridge_doc,
        storyboard_slides=slides_list,
        is_full_paper_deck=is_full,
        universal_io_bus_capsule=manifest.get("universal_io_bus_capsule"),
    )
    if not check.get("passed"):
        return {
            "status": "FAIL",
            "reason": "Invalid domain_background_bridge capsule",
            "issues": check.get("issues", []),
        }
    bg_indices = set(check.get("background_slide_indices", []))
    for entry in slides_list:
        if int(entry.get("slide_index", 0)) in bg_indices:
            entry["is_background_slide"] = True
    manifest["domain_background_bridge"] = bridge_doc
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {
        "status": "PASS",
        "background_slide_indices": sorted(bg_indices),
        "jargon_translation_count": check.get("jargon_translation_count", 0),
    }


def record_tdd_station_capsule(
    manifest_path: Path,
    slide_index: int,
    tdd_capsule: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Mode 1 (`TDD`): Record and validate the Tutor-Driven Design 1-Station-to-1-Slide
    cognitive capsule for `slide_index` before generating/auditing its HTML slide.
    """
    dag = _load_design_ag_module()
    if not manifest_path.is_file():
        return {"status": "FAIL", "reason": f"Missing slide_manifest.json: {manifest_path}"}
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    slides_list: List[Dict[str, Any]] = manifest.get("slides", [])
    if slide_index < 1 or slide_index > len(slides_list):
        return {"status": "FAIL", "reason": f"Invalid slide_index {slide_index}"}

    hop_distance = _compute_hop_distance(slides_list, slide_index)
    if hop_distance != 1:
        return {
            "status": "FAIL",
            "slide_index": slide_index,
            "reason": f"1-Hop Station-Slide lock violation: unverified_slide_hop_distance={hop_distance} != 1",
        }

    target_entry = slides_list[slide_index - 1]
    eff_tdd = dict(tdd_capsule) if isinstance(tdd_capsule, dict) else {}
    if bool(target_entry.get("is_background_slide", False)):
        eff_tdd["is_background_station"] = True

    tdd_check = dag.verify_tdd_station_capsule_completeness(eff_tdd)
    if not tdd_check.get("passed"):
        return {
            "status": "FAIL",
            "slide_index": slide_index,
            "reason": "TDD Station Cognitive Capsule incomplete",
            "tdd_check": tdd_check,
        }

    target_entry["tdd_station_capsule"] = eff_tdd
    target_entry["station_id"] = str(tdd_capsule.get("station_id", target_entry.get("station_id", "")))
    if bool(tdd_capsule.get("promote_to_v3_animation", False)) or str(tdd_check.get("visual_modality", "")).upper().startswith("V3"):
        target_entry["designated_v3_animation"] = True
        target_entry["required_visual_level"] = "V3"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {
        "status": "PASS",
        "mode": "TDD",
        "slide_index": slide_index,
        "slide_id": target_entry["slide_id"],
        "station_id": target_entry["station_id"],
        "visual_modality": tdd_check["visual_modality"],
    }


def record_grill_station_capsule(
    manifest_path: Path,
    slide_index: int,
    grill_capsule: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Mode 2 (`GRILL` / Grill-Driven Design): Record and validate the Grill-First +
    Teach-on-Miss + Re-grill capsule for `slide_index` before generating/auditing its HTML slide.
    """
    dag = _load_design_ag_module()
    if not manifest_path.is_file():
        return {"status": "FAIL", "reason": f"Missing slide_manifest.json: {manifest_path}"}
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    slides_list: List[Dict[str, Any]] = manifest.get("slides", [])
    if slide_index < 1 or slide_index > len(slides_list):
        return {"status": "FAIL", "reason": f"Invalid slide_index {slide_index}"}

    hop_distance = _compute_hop_distance(slides_list, slide_index)
    if hop_distance != 1:
        return {
            "status": "FAIL",
            "slide_index": slide_index,
            "reason": f"1-Hop Grill-Slide lock violation: unverified_slide_hop_distance={hop_distance} != 1",
        }

    target_entry = slides_list[slide_index - 1]
    eff_grill = dict(grill_capsule) if isinstance(grill_capsule, dict) else {}
    if bool(target_entry.get("is_background_slide", False)):
        eff_grill["requires_beyond_pdf_background"] = True

    grill_check = dag.verify_grill_station_capsule_completeness(eff_grill)
    if not grill_check.get("passed"):
        return {
            "status": "FAIL",
            "slide_index": slide_index,
            "reason": "Grill-Driven Design (GDD) Capsule incomplete",
            "grill_check": grill_check,
        }

    target_entry["gdd_grill_capsule"] = eff_grill
    target_entry["station_id"] = str(grill_capsule.get("station_id", target_entry.get("station_id", "")))
    if bool(grill_capsule.get("promote_to_v3_animation", False)) or str(grill_check.get("visual_modality", "")).upper().startswith("V3"):
        target_entry["designated_v3_animation"] = True
        target_entry["required_visual_level"] = "V3"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {
        "status": "PASS",
        "mode": "GRILL",
        "slide_index": slide_index,
        "slide_id": target_entry["slide_id"],
        "station_id": target_entry["station_id"],
        "visual_modality": grill_check["visual_modality"],
    }


def audit_single_slide_step(
    manifest_path: Path,
    slide_index: int,
    slide_html_path: Path,
    slide_bundle: Dict[str, Any],
    slides_generated_in_current_step: int = 1,
) -> Dict[str, Any]:
    """
    Stage 3 Gatekeeper: Enforce strictly 1 slide per step (`slides_generated_in_current_step == 1`),
    1-Hop Topological Lock (`slide_{k-1}` must be `PASS` before `slide_k` can be audited),
    Mode 1 (`tdd_mode`) or Mode 2 (`grill_mode`) capsule completeness, and
    optional Human-in-the-Loop approval gate (`require_human_approval`).
    """
    dag = _load_design_ag_module()
    if not manifest_path.is_file():
        return {"status": "FAIL", "reason": f"Missing slide_manifest.json: {manifest_path}"}

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    slides_list: List[Dict[str, Any]] = manifest.get("slides", [])
    if slide_index < 1 or slide_index > len(slides_list):
        return {"status": "FAIL", "reason": f"Invalid slide_index {slide_index}"}

    hop_distance = _compute_hop_distance(slides_list, slide_index)
    target_entry = slides_list[slide_index - 1]
    tdd_mode = bool(manifest.get("tdd_mode", False)) or bool(slide_bundle.get("tdd_mode", False))
    tdd_capsule = slide_bundle.get("tdd_station_capsule") or target_entry.get("tdd_station_capsule")
    grill_mode = bool(manifest.get("grill_mode", False)) or bool(slide_bundle.get("grill_mode", False))
    grill_capsule = slide_bundle.get("gdd_grill_capsule") or target_entry.get("gdd_grill_capsule")
    if bool(target_entry.get("is_background_slide", False)):
        if isinstance(tdd_capsule, dict):
            tdd_capsule = {**tdd_capsule, "is_background_station": True}
        if isinstance(grill_capsule, dict):
            grill_capsule = {**grill_capsule, "requires_beyond_pdf_background": True}

    d16 = dag.verify_storyboard_microstep_and_layout_diversity(
        manifest.get("storyboard_slides", []),
        max_slides_generated_per_step=slides_generated_in_current_step,
        unverified_slide_hop_distance=hop_distance,
        tdd_mode=tdd_mode,
        tdd_station_capsule=tdd_capsule,
        grill_mode=grill_mode,
        gdd_grill_capsule=grill_capsule,
    )
    if not d16.get("passed"):
        return {
            "status": "FAIL",
            "effective_reward": float("-inf"),
            "slide_index": slide_index,
            "reason": "Single-Slide Micro-Step, 1-Hop Topological Lock, or TDD/Grill Capsule Violation (D16)",
            "D16": d16,
        }

    if bool(target_entry.get("designated_v3_animation", False)):
        obs_mod = ""
        if isinstance(grill_capsule, dict) and grill_capsule.get("visual_modality"):
            obs_mod = str(grill_capsule.get("visual_modality", "")).upper()
        elif isinstance(tdd_capsule, dict) and tdd_capsule.get("visual_modality"):
            obs_mod = str(tdd_capsule.get("visual_modality", "")).upper()
        else:
            obs_mod = str(slide_bundle.get("visual_modality", target_entry.get("required_visual_level", ""))).upper()
        if not obs_mod.startswith("V3"):
            return {
                "status": "FAIL",
                "effective_reward": float("-inf"),
                "slide_index": slide_index,
                "reason": (
                    f"Global Deck Blueprint V3 Animation Contract Violation: Slide {slide_index} was designated "
                    f"for V3 interactive/animated explanation in Stage 0 Global Blueprint, but got '{obs_mod}'"
                ),
            }

    if not slide_html_path.is_file():
        return {"status": "FAIL", "reason": f"Missing slide HTML file: {slide_html_path}"}

    html_text = slide_html_path.read_text(encoding="utf-8")
    per_slide_deck_spec = {"is_full_paper_deck": False, **(slide_bundle.get("deck_spec") or {})}
    gate_checks = [
        dag.scan_html_for_unrendered_latex_leak(html_text),
        dag.audit_html_tag_balance_and_grid_orphans(html_text, slide_bundle.get("grid_specs")),
        dag.audit_copywriting_naturalness_and_ai_tone(slide_bundle.get("slides", []), html_text),
        dag.audit_acronym_definitions_and_popovers(
            slide_bundle.get("slides", []),
            slide_bundle.get("required_acronyms", ("PHOLED", "TPA", "TTA")),
            html_text=html_text,
        ),
        dag.audit_emojis_fake_bars_and_watermarks(
            html_text,
            slide_bundle.get("figure_metadata"),
            visual_entity_manifest=slide_bundle.get("visual_entity_manifest"),
            image_tournament_ledgers=slide_bundle.get("image_tournament_ledgers"),
        ),
        dag.audit_teleprompter_and_slide_density(per_slide_deck_spec, html_text),
        dag.verify_bounding_boxes_zero_overlap_and_clipping(slide_bundle.get("boxes", [])),
        dag.verify_canvas_whitespace_and_center_of_mass(slide_bundle.get("boxes", [])),
        dag.verify_image_aspect_ratio_and_slot_utilization(slide_bundle.get("placements", [])),
        dag.verify_wcag_contrast_and_visual_restraint(
            slide_bundle.get("color_pairs", []),
            bool(slide_bundle.get("has_cyberpunk_neon_glow", False)),
            True,
        ),
        dag.audit_slide_html_background_onboarding_fidelity(
            html_text,
            slide_index=slide_index,
            storyboard_slides=slides_list,
            domain_background_bridge=manifest.get("domain_background_bridge"),
            universal_io_bus_capsule=manifest.get("universal_io_bus_capsule"),
        ),
        d16,
    ]
    failed = [g["gate"] for g in gate_checks if not g.get("passed")]
    if failed:
        return {
            "status": "FAIL",
            "slide_index": slide_index,
            "failed_gates": failed,
            "gate_details": gate_checks,
        }

    target_entry["sha256"] = _sha256_file(slide_html_path)
    target_entry["file_path"] = str(slide_html_path)
    if tdd_capsule:
        target_entry["tdd_station_capsule"] = tdd_capsule
    if grill_capsule:
        target_entry["gdd_grill_capsule"] = grill_capsule

    require_human = bool(manifest.get("require_human_approval", False))
    if require_human and not bool(target_entry.get("human_approved", False)):
        target_entry["status"] = "AWAITING_HUMAN_APPROVAL"
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return {
            "status": "AWAITING_HUMAN_APPROVAL",
            "slide_index": slide_index,
            "slide_id": target_entry["slide_id"],
            "sha256": target_entry["sha256"],
            "next_unlocked_slide": "",
            "message": "Ten applicable per-slide checks passed; awaiting human sign-off to unlock the next slide. Final presentation review remains required.",
        }

    target_entry["status"] = "PASS"
    next_unlocked = ""
    if slide_index < len(slides_list):
        nxt = slides_list[slide_index]
        if nxt.get("status") == "LOCKED":
            nxt["status"] = "UNLOCKED"
        next_unlocked = str(nxt.get("slide_id", ""))

    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {
        "status": "PASS",
        "slide_index": slide_index,
        "slide_id": target_entry["slide_id"],
        "sha256": target_entry["sha256"],
        "next_unlocked_slide": next_unlocked,
    }


def apply_human_feedback_dual_upgrade(
    manifest_path: Path,
    feedback_receipt: Dict[str, Any],
    patched_slide_index: int,
    patched_html_path: Path,
    patched_bundle: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Mode 3 (`AUTONOMOUS_DUAL_EVOLVE`): After head-down autonomous deck generation, when the
    human reviews the PPT and provides critique (`human_critique`), this function enforces:
    1. Valid `dual_evolution_feedback_receipt` (both PPT patch action AND AWF HTML-PPT / DesignAG
       gate/rule + negative canary evolution when generalizable);
    2. Re-auditing the patched slide via `audit_single_slide_step` (18 DesignAG gates);
    3. Recording the signed dual-evolution receipt into `slide_manifest.json`.
    """
    dag = _load_design_ag_module()
    if not manifest_path.is_file():
        return {"status": "FAIL", "reason": f"Missing slide_manifest.json: {manifest_path}"}

    dual_check = dag.verify_dual_evolution_feedback_receipt(feedback_receipt)
    if not dual_check.get("passed"):
        return {
            "status": "FAIL",
            "stage": "Dual_Evolution_Receipt_Check",
            "reason": "Human feedback Dual-Evolution Receipt is incomplete (must update PPT AND record AWF evolution receipt)",
            "dual_check": dual_check,
        }

    slide_audit = audit_single_slide_step(
        manifest_path,
        patched_slide_index,
        patched_html_path,
        patched_bundle,
        slides_generated_in_current_step=1,
    )
    if slide_audit.get("status") not in {"PASS", "AWAITING_HUMAN_APPROVAL"}:
        return {
            "status": "FAIL",
            "stage": "Patched_Slide_ReAudit",
            "reason": "Patched slide failed DesignAG applicable per-slide re-audit",
            "slide_audit": slide_audit,
        }

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    receipts: List[Dict[str, Any]] = manifest.setdefault("dual_evolution_receipts", [])
    receipt_record = {
        **feedback_receipt,
        "patched_slide_index": patched_slide_index,
        "patched_slide_sha256": slide_audit.get("sha256", ""),
    }
    receipts.append(receipt_record)
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {
        "status": "PASS",
        "mode": "AUTONOMOUS_DUAL_EVOLVE",
        "patched_slide_index": patched_slide_index,
        "patched_slide_sha256": slide_audit.get("sha256", ""),
        "is_generalizable_to_awf": bool(feedback_receipt.get("is_generalizable_to_awf", False)),
        "total_dual_evolution_receipts": len(receipts),
    }


def approve_slide_by_human(
    manifest_path: Path,
    slide_index: int,
    human_note: str = "Approved by human director",
) -> Dict[str, Any]:
    """
    Human-in-the-Loop Sign-off Gate: Transition a machine-verified slide (`AWAITING_HUMAN_APPROVAL`)
    to `PASS` after verifying its SHA-256 hash is intact, and unlock `slide_{k+1}`.
    """
    if not manifest_path.is_file():
        return {"status": "FAIL", "reason": f"Missing slide_manifest.json: {manifest_path}"}
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    slides_list: List[Dict[str, Any]] = manifest.get("slides", [])
    if slide_index < 1 or slide_index > len(slides_list):
        return {"status": "FAIL", "reason": f"Invalid slide_index {slide_index}"}

    target_entry = slides_list[slide_index - 1]
    if target_entry.get("status") not in {"AWAITING_HUMAN_APPROVAL", "PASS"}:
        return {
            "status": "FAIL",
            "slide_index": slide_index,
            "reason": f"Slide must pass DesignAG machine gates before human approval (current status={target_entry.get('status')})",
        }

    fp = Path(str(target_entry.get("file_path", "")))
    if not fp.is_file() or _sha256_file(fp) != target_entry.get("sha256"):
        return {
            "status": "FAIL",
            "slide_index": slide_index,
            "reason": "Slide HTML file missing or modified after DesignAG audit",
        }

    target_entry["human_approved"] = True
    target_entry["human_note"] = human_note
    target_entry["status"] = "PASS"

    next_unlocked = ""
    if slide_index < len(slides_list):
        nxt = slides_list[slide_index]
        if nxt.get("status") == "LOCKED":
            nxt["status"] = "UNLOCKED"
        next_unlocked = str(nxt.get("slide_id", ""))

    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {
        "status": "PASS",
        "slide_index": slide_index,
        "slide_id": target_entry["slide_id"],
        "human_approved": True,
        "next_unlocked_slide": next_unlocked,
    }


def assemble_verified_deck(
    manifest_path: Path,
    output_deck_path: Path,
) -> Dict[str, Any]:
    """
    Stage 4 Compiler: Verify that 100% of slides in `slide_manifest.json` hold `PASS` receipts
    and matching SHA-256 file hashes before assembling the final HTML deck.
    """
    if not manifest_path.is_file():
        return {"status": "FAIL", "reason": f"Missing manifest: {manifest_path}"}
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    slides_list: List[Dict[str, Any]] = manifest.get("slides", [])
    unverified: List[str] = []
    slide_bodies: List[str] = []

    for entry in slides_list:
        sid = str(entry.get("slide_id", ""))
        fp = Path(str(entry.get("file_path", "")))
        if entry.get("status") != "PASS" or not fp.is_file():
            unverified.append(f"{sid}:status={entry.get('status')}")
            continue
        actual_sha = _sha256_file(fp)
        if actual_sha != entry.get("sha256"):
            unverified.append(f"{sid}:sha256_mismatch")
            continue
        slide_bodies.append(fp.read_text(encoding="utf-8"))

    if unverified:
        return {
            "status": "FAIL",
            "reason": "Cannot assemble deck while slides remain unverified or tampered",
            "unverified_slides": unverified,
        }

    onion = manifest.get("onion_peeling_capsule")
    if isinstance(onion, dict):
        layer0 = onion.get("layer0_macro_frame") or {}
        mcq0 = layer0.get("macro_trunks_mcq") or {}
        trunks = mcq0.get("macro_trunks", [])
        unpeeled_trunks = [
            str(t.get("trunk_id", ""))
            for t in trunks
            if isinstance(t, dict) and str(t.get("status", "UNPEELED")).upper() == "UNPEELED"
        ]
        if unpeeled_trunks:
            return {
                "status": "FAIL",
                "reason": f"Onion Peeling Incomplete: macro trunks still UNPEELED: {unpeeled_trunks}",
            }

    io_bus = manifest.get("universal_io_bus_capsule")
    if isinstance(io_bus, dict):
        raw_t = io_bus.get("cross_artifact_targets") or io_bus.get("output_artifact_targets") or []
        req_targets = [
            str(t).strip().upper()
            for t in raw_t
            if str(t).strip().upper() in {"SCI_WORD", "FIG_PPTX"}
        ]
        for rt in req_targets:
            has_rt = any(
                isinstance(s.get("cross_artifact_receipts"), dict)
                and s["cross_artifact_receipts"].get(rt, {}).get("status") == "PASS"
                for s in slides_list
            )
            if not has_rt:
                return {
                    "status": "FAIL",
                    "reason": f"Cross-Artifact Target Incomplete: '{rt}' declared in universal_io_bus_capsule but has 0 verified receipts",
                }

    gb = manifest.get("global_deck_blueprint")
    if isinstance(gb, dict):
        flow_mcq = gb.get("logical_flow_mcq") or {}
        raw_spine = flow_mcq.get("logical_flow_spine", [])
        if isinstance(raw_spine, list) and len(raw_spine) >= 2:
            if len(slides_list) < len(raw_spine):
                return {
                    "status": "FAIL",
                    "reason": (
                        f"Logical Flow Spine Incomplete: Stage 0 defined {len(raw_spine)} logical flow modules "
                        f"({raw_spine}), but only {len(slides_list)} slide(s) were built"
                    ),
                }
        anim_mcq = gb.get("v3_animation_budget_mcq") or {}
        min_v3_quota = _int_val(anim_mcq, "min_v3_slides_quota", 0)
        if min_v3_quota >= 1:
            v3_count = 0
            for entry in slides_list:
                g_cap = entry.get("gdd_grill_capsule") or {}
                t_cap = entry.get("tdd_station_capsule") or {}
                mod = str(g_cap.get("visual_modality") or t_cap.get("visual_modality") or entry.get("required_visual_level") or "").upper()
                if bool(entry.get("designated_v3_animation", False)) or mod.startswith("V3"):
                    v3_count += 1
            if v3_count < min_v3_quota:
                return {
                    "status": "FAIL",
                    "reason": (
                        f"Global V3 Animation Quota Violation: deck has {v3_count} V3 animation slide(s), "
                        f"below min_v3_slides_quota={min_v3_quota} set in Stage 0 Global Blueprint"
                    ),
                }

    require_bg = (
        len(slides_list) >= FULL_PAPER_BG_SLIDE_THRESHOLD
        or bool(manifest.get("require_beyond_pdf_background", False))
        or manifest.get("domain_background_bridge") is not None
    )
    if require_bg:
        dag = _load_design_ag_module()
        bg_check = dag.verify_domain_background_bridge_capsule(
            manifest.get("domain_background_bridge"),
            storyboard_slides=slides_list,
            is_full_paper_deck=(
                len(slides_list) >= FULL_PAPER_BG_SLIDE_THRESHOLD
                or bool(manifest.get("require_beyond_pdf_background", False))
            ),
            universal_io_bus_capsule=manifest.get("universal_io_bus_capsule"),
        )
        if not bg_check.get("passed"):
            return {
                "status": "FAIL",
                "reason": "Beyond-PDF Domain Background Bridge Incomplete on Assembled Deck",
                "issues": bg_check.get("issues", []),
            }

    assembled_html = (
        "<!DOCTYPE html>\n<html lang='zh-CN'>\n<head>\n<meta charset='utf-8'/>\n"
        "<title>AWF HTML-PPT Assembled Draft</title>\n"
        "</head>\n<body>\n"
        + "\n<!-- SLIDE_BOUNDARY -->\n".join(slide_bodies)
        + "\n</body>\n</html>\n"
    )
    dag_asm = _load_design_ag_module()
    if require_bg and manifest.get("domain_background_bridge") is not None:
        asm_bg_html = dag_asm.audit_slide_html_background_onboarding_fidelity(
            assembled_html,
            storyboard_slides=slides_list,
            domain_background_bridge=manifest.get("domain_background_bridge"),
            universal_io_bus_capsule=manifest.get("universal_io_bus_capsule"),
        )
        if not asm_bg_html.get("passed"):
            return {
                "status": "FAIL",
                "reason": "Assembled deck violates pre-background recipe leak guard or opening Rung-1 macro-stakes HTML grounding",
                "issues": asm_bg_html.get("issues", []),
            }
    asm_typo_check = dag_asm.audit_inline_svg_typography_and_char_budget(assembled_html)
    if not asm_typo_check.get("passed"):
        return {
            "status": "FAIL",
            "reason": "Assembled deck violates inline <svg> >= 32px typography or <= 260 single-slide character budget",
            "issues": asm_typo_check.get("issues", []),
        }
    asm_html_typo = dag_asm.audit_html_typography_and_card_fill(assembled_html)
    if not asm_html_typo.get("passed"):
        return {
            "status": "FAIL",
            "reason": "Assembled deck violates visible HTML >= 32px / HD body >= 42px / HD title >= 56px typography or hollow card fill",
            "issues": asm_html_typo.get("issues", []),
        }
    asm_pop_check = dag_asm.audit_clickable_detail_popovers_and_triggers(assembled_html)
    if not asm_pop_check.get("passed"):
        return {
            "status": "FAIL",
            "reason": "Assembled deck contains dangling detail-trigger popovers or multi-paragraph card prose dumping",
            "issues": asm_pop_check.get("issues", []),
        }
    asm_lossless = dag_asm.verify_lossless_popover_and_split_ledger(
        manifest.get("lossless_split_and_popover_ledger"),
        manifest.get("storyboard_slides"),
    )
    if not asm_lossless.get("passed"):
        return {
            "status": "FAIL",
            "reason": "Assembled deck violates lossless_split_and_popover_ledger (dropped evidence or missing topological breadcrumbs)",
            "issues": asm_lossless.get("issues", []),
        }
    asm_copy_check = dag_asm.audit_copywriting_naturalness_and_ai_tone((), assembled_html)
    if not asm_copy_check.get("passed"):
        return {
            "status": "FAIL",
            "reason": "Assembled deck contains AI self-scaffolding meta-labels, marketing clichés, or prompt residue",
            "D3": asm_copy_check,
        }
    output_deck_path.parent.mkdir(parents=True, exist_ok=True)
    output_deck_path.write_text(assembled_html, encoding="utf-8")
    return {
        "status": "PASS",
        "presentation_acceptance": "REVIEW_REQUIRED",
        "assurance_scope": "structural_assembly_only",
        "total_slides_assembled": len(slide_bodies),
        "output_deck_path": str(output_deck_path),
        "deck_sha256": _sha256_file(output_deck_path),
    }


def _selftest_part_a_tdd(
    tdir: Path,
    base_narrative: Dict[str, Any],
    base_mechanism: Dict[str, Any],
    base_slides: List[Dict[str, Any]],
    s1_path: Path,
    s2_path: Path,
    valid_bundle: Dict[str, Any],
) -> None:
    manifest_path = tdir / "slide_manifest.json"
    storyboard_doc = {
        "workflow_mode": "TDD",
        "tdd_mode": True,
        "require_human_approval": True,
        "narrative_spec": base_narrative,
        "mechanism_spec": base_mechanism,
        "storyboard_slides": base_slides,
    }
    init_res = init_storyboard_manifest(storyboard_doc, manifest_path)
    if init_res.get("status") != "PASS":
        raise AssertionError(f"Storyboard init failed: {init_res}")

    neg_hop = audit_single_slide_step(manifest_path, 2, s2_path, valid_bundle, slides_generated_in_current_step=1)
    if neg_hop.get("status") != "FAIL":
        raise AssertionError(f"Expected 1-hop violation: {neg_hop}")

    neg_batch = audit_single_slide_step(manifest_path, 1, s1_path, valid_bundle, slides_generated_in_current_step=2)
    if neg_batch.get("status") != "FAIL":
        raise AssertionError(f"Expected single-slide violation: {neg_batch}")

    neg_no_tdd = audit_single_slide_step(manifest_path, 1, s1_path, valid_bundle, slides_generated_in_current_step=1)
    if neg_no_tdd.get("status") != "FAIL":
        raise AssertionError(f"Expected TDD violation without capsule: {neg_no_tdd}")

    capsule_1 = {
        "station_id": "Station_1.1",
        "core_blindspot_or_conflict": "为什么电激发下 75% 三重态自旋统计决定了必须发展磷光 PHOLED？",
        "wittgenstein_ladder": "Bridge: 漏水蓄水池分流 -> Deconstruct: 经典分流忽略量子自旋禁阻 -> Replace: 重原子旋轨耦合突破 25% 上限",
        "human_orthogonal_insight": "用户指出左图自旋比例必须与右图三重态微秒级长寿命导致的滚降直接对照",
        "visual_modality": "V2_fig1a_spin_statistics_diagram",
        "hidden_teleprompter_qa": "按 S 键展示评委关于荧光与磷光内量子效率极限的推导问答",
    }
    rec1 = record_tdd_station_capsule(manifest_path, 1, capsule_1)
    await_s1 = audit_single_slide_step(manifest_path, 1, s1_path, valid_bundle, slides_generated_in_current_step=1)
    if rec1.get("status") != "PASS" or await_s1.get("status") != "AWAITING_HUMAN_APPROVAL":
        raise AssertionError(f"TDD Step 1 failed: {rec1}, {await_s1}")

    neg_unapproved = record_tdd_station_capsule(manifest_path, 2, {**capsule_1, "station_id": "Station_1.2"})
    if neg_unapproved.get("status") != "FAIL":
        raise AssertionError(f"Expected 1-hop block while slide_01 awaits human approval: {neg_unapproved}")

    hum_s1 = approve_slide_by_human(manifest_path, 1, "左图自旋统计与结论对齐，通过！")
    if hum_s1.get("status") != "PASS":
        raise AssertionError(f"Human approval 1 failed: {hum_s1}")

    neg_asm = assemble_verified_deck(manifest_path, tdir / "deck.html")
    if neg_asm.get("status") != "FAIL":
        raise AssertionError(f"Expected assembly failure while slide_02 unverified: {neg_asm}")

    record_tdd_station_capsule(manifest_path, 2, {**capsule_1, "station_id": "Station_1.2", "visual_modality": "V3_interactive_rabi"})
    audit_single_slide_step(manifest_path, 2, s2_path, valid_bundle, slides_generated_in_current_step=1)
    approve_slide_by_human(manifest_path, 2, "通过！")
    pos_asm = assemble_verified_deck(manifest_path, tdir / "deck.html")
    if pos_asm.get("status") != "PASS":
        raise AssertionError(f"Deck assembly failed: {pos_asm}")


def _selftest_part_b_and_c_grill_and_autonomous(
    tdir: Path,
    base_narrative: Dict[str, Any],
    base_mechanism: Dict[str, Any],
    base_slides: List[Dict[str, Any]],
    s1_path: Path,
    valid_bundle: Dict[str, Any],
) -> Dict[str, Any]:
    grill_manifest = tdir / "grill_manifest.json"
    init_grill = init_storyboard_manifest(
        {
            "workflow_mode": "GRILL",
            "grill_mode": True,
            "require_human_approval": False,
            "narrative_spec": base_narrative,
            "mechanism_spec": base_mechanism,
            "storyboard_slides": base_slides[:1],
        },
        grill_manifest,
    )
    if init_grill.get("status") != "PASS":
        raise AssertionError(f"Grill manifest init failed: {init_grill}")

    neg_no_grill = audit_single_slide_step(grill_manifest, 1, s1_path, valid_bundle, slides_generated_in_current_step=1)
    neg_rubber_grill = record_grill_station_capsule(
        grill_manifest,
        1,
        {
            "station_id": "Station_1.1",
            "question_archetype": "PARADOX_BOTTLENECK",
            "grill_question": "【锚点】光激发总是产生 S1；【冲突】电激发下传统荧光 IQE 被死锁在 25%；【追问】为什么 75% 去了三重态？",
            "user_response_state": "TAUGHT_ON_MISS_AND_REGRILLED",
            "teaching_and_regrill_closure": "给你讲完了自旋统计，你听懂了吗？",
            "bottleneck_to_slide_mapping": "将 1:3 自旋简并度映射为左栏能级图",
            "slide_design_mcq": None,
            "visual_modality": "V2_spin_degeneracy_and_soc_diagram",
            "hidden_teleprompter_qa": "按 S 键展示 TADF 追问",
        },
    )
    if neg_no_grill.get("status") != "FAIL" or neg_rubber_grill.get("status") != "FAIL":
        raise AssertionError(f"Expected GRILL mode block without valid Dual-Stage capsule: {neg_no_grill}, {neg_rubber_grill}")

    grill_cap_1 = {
        "station_id": "Station_1.1",
        "question_archetype": "PARADOX_BOTTLENECK",
        "grill_question": "【锚点】光激发总是产生单重态 S1；【冲突】换成电激发时传统荧光器件内量子效率上限却被死锁在 25%；【追问】为什么电激发会强行分走 75% 给三重态 T1？背后的自旋简并度怎么算？",
        "user_response_state": "TAUGHT_ON_MISS_AND_REGRILLED",
        "teaching_and_regrill_closure": "先用四枚硬币自旋投影讲清 1 个反对称单重态 vs 3 个对称三重态，再变式追问重原子旋轨耦合或小 ΔE_ST 的 TADF 如何打破禁阻，用户成功答出 100% IQE 路径",
        "bottleneck_to_slide_mapping": "将用户在『1:3 自旋统计简并度与三重态微秒级长寿命积压』上的卡壳点直接转化为本页左侧能级漏斗图与右侧对比卡片的视觉C位",
        "slide_design_mcq": {
            "design_question": "刚把『1:3 自旋统计与 75% 三重态去向』烤问通关，这一页 PPT（slide_01）你选哪种视觉与布局呈现方案？",
            "options": [
                "A (Recommended): 左栏原图 Fig.1a 自旋统计能级漏斗 + 右栏荧光/磷光三步因果卡片（V2）",
                "B: 顶部全宽激子复合时间轴 + 底部双栏数据表（V2）",
                "C: 带单重态/三重态比例与旋轨耦合强度实时滑块的交互式能级模拟器（V3）",
            ],
            "selected_option": "A (Recommended): 左栏原图 Fig.1a 自旋统计能级漏斗 + 右栏荧光/磷光三步因果卡片（V2）",
        },
        "visual_modality": "V2_spin_degeneracy_and_soc_diagram",
        "hidden_teleprompter_qa": "按 S 键展示评委连环追问：为什么热激发延迟荧光 TADF 不靠重原子也能利用 75% 三重态？",
    }
    rec_grill = record_grill_station_capsule(grill_manifest, 1, grill_cap_1)
    pass_grill = audit_single_slide_step(grill_manifest, 1, s1_path, valid_bundle, slides_generated_in_current_step=1)
    if rec_grill.get("status") != "PASS" or pass_grill.get("status") != "PASS":
        raise AssertionError(f"GRILL mode flow failed: {rec_grill}, {pass_grill}")

    auto_manifest = tdir / "auto_manifest.json"
    init_auto = init_storyboard_manifest(
        {
            "workflow_mode": "AUTONOMOUS_DUAL_EVOLVE",
            "require_human_approval": False,
            "narrative_spec": base_narrative,
            "mechanism_spec": base_mechanism,
            "storyboard_slides": base_slides[:1],
        },
        auto_manifest,
    )
    auto_s1 = audit_single_slide_step(auto_manifest, 1, s1_path, valid_bundle, slides_generated_in_current_step=1)
    auto_deck = assemble_verified_deck(auto_manifest, tdir / "auto_deck.html")
    if init_auto.get("status") != "PASS" or auto_s1.get("status") != "PASS" or auto_deck.get("status") != "PASS":
        raise AssertionError(f"Autonomous head-down build failed: {init_auto}, {auto_s1}, {auto_deck}")

    bad_receipt = {
        "human_feedback_summary": "第一页右图三重态淬灭示意缺少与左图的箭头映射",
        "affected_slides_patched": ["slide_01"],
        "is_generalizable_to_awf": True,
        "target_gate_or_rule_id": "",
        "negative_canary_fixture": "",
    }
    neg_dual = apply_human_feedback_dual_upgrade(auto_manifest, bad_receipt, 1, s1_path, valid_bundle)
    if neg_dual.get("status") != "FAIL":
        raise AssertionError(f"Expected incomplete dual-evolution receipt to fail: {neg_dual}")

    good_receipt = {
        "human_feedback_summary": "第一页右图三重态淬灭示意缺少与左图的箭头映射，观众一眼看不出左右两栏的因果关系",
        "affected_slides_patched": ["slide_01"],
        "is_generalizable_to_awf": True,
        "target_gate_or_rule_id": "D14_D16_DualColumn_CrossLink_Anchor",
        "negative_canary_fixture": "test_dual_column_missing_cross_link_rejected",
    }
    pos_dual = apply_human_feedback_dual_upgrade(auto_manifest, good_receipt, 1, s1_path, valid_bundle)
    if pos_dual.get("status") != "PASS" or pos_dual.get("total_dual_evolution_receipts") != 1:
        raise AssertionError(f"Complete dual-evolution upgrade failed: {pos_dual}")
    return grill_cap_1


def _selftest_part_d_and_e_blueprint_and_elastic(
    tdir: Path,
    base_narrative: Dict[str, Any],
    base_mechanism: Dict[str, Any],
    base_slides: List[Dict[str, Any]],
    s1_path: Path,
    s2_path: Path,
    valid_bundle: Dict[str, Any],
    grill_cap_1: Dict[str, Any],
) -> Dict[str, Any]:
    macro_manifest = tdir / "macro_manifest.json"
    global_bp = {
        "macro_thesis_probe": {
            "executive_core_conflict": "蓝光磷光微秒级寿命引发高亮度 TTA 烧屏，利用极化激元反交叉耦合压缩寿命破局",
            "human_baseline_alignment": "用户确认以自旋统计与极化激元反交叉为核心主线，不问也不固定总页数",
        },
        "emphasis_allocation_mcq": {
            "options": ["A (Recommended): 重点深挖极化激元反交叉与 TTA 抑制", "B: 重点讲工艺"],
            "selected_option": "A (Recommended): 重点深挖极化激元反交叉与 TTA 抑制",
            "heavy_focus_modules": ["极化激元反交叉耦合", "TTA 双分子淬灭抑制"],
        },
        "v3_animation_budget_mcq": {
            "options": ["A (Recommended): 第 1 页强制采用 V3 交互动画滑块讲透寿命压缩", "B: 仅用静态图"],
            "selected_option": "A (Recommended): 第 1 页强制采用 V3 交互动画滑块讲透寿命压缩",
            "v3_designated_slide_indices": [1],
        },
    }
    init_macro = init_storyboard_manifest(
        {
            "workflow_mode": "GRILL",
            "grill_mode": True,
            "global_deck_blueprint": global_bp,
            "narrative_spec": base_narrative,
            "mechanism_spec": base_mechanism,
            "storyboard_slides": base_slides[:1],
        },
        macro_manifest,
    )
    if init_macro.get("status") != "PASS":
        raise AssertionError(f"Macro blueprint init failed: {init_macro}")

    record_grill_station_capsule(macro_manifest, 1, grill_cap_1)
    neg_v3_downgrade = audit_single_slide_step(macro_manifest, 1, s1_path, valid_bundle, slides_generated_in_current_step=1)
    if neg_v3_downgrade.get("status") != "FAIL":
        raise AssertionError(f"Expected V3 animation downgrade to V2 to be blocked: {neg_v3_downgrade}")

    record_grill_station_capsule(macro_manifest, 1, {**grill_cap_1, "visual_modality": "V3_interactive_purcell_slider"})
    pos_v3_contract = audit_single_slide_step(macro_manifest, 1, s1_path, valid_bundle, slides_generated_in_current_step=1)
    if pos_v3_contract.get("status") != "PASS":
        raise AssertionError(f"Expected V3 animation slide to pass: {pos_v3_contract}")

    elastic_manifest = tdir / "elastic_manifest.json"
    elastic_bp = {
        "macro_thesis_probe": {
            "executive_core_conflict": "蓝光磷光微秒级寿命引发高亮度 TTA 烧屏，利用极化激元反交叉耦合压缩寿命破局",
            "human_baseline_alignment": "不问也不设固定页数，只按逻辑演进主线和理解需要自然生长，动画也边问边定",
        },
        "logical_flow_mcq": {
            "options": [
                "A (Recommended): 1.自旋统计与TTA死结 -> 2.极化激元反交叉破局原理与色散验证",
                "B: 结论先行倒叙主线",
            ],
            "selected_option": "A (Recommended): 1.自旋统计与TTA死结 -> 2.极化激元反交叉破局原理与色散验证",
            "logical_flow_spine": ["1.自旋统计与TTA死结", "2.极化激元反交叉破局原理与色散验证"],
        },
        "emphasis_allocation_mcq": {
            "options": ["A (Recommended): 重点深挖极化激元反交叉耦合", "B: 重点讲工艺"],
            "selected_option": "A (Recommended): 重点深挖极化激元反交叉耦合",
            "heavy_focus_modules": ["极化激元反交叉耦合"],
        },
        "v3_animation_budget_mcq": {
            "options": ["A (Recommended): 讲到抽象难点时当场拍板加动态演示", "B: 提前锁死"],
            "selected_option": "A (Recommended): 讲到抽象难点时当场拍板加动态演示",
            "v3_discovery_policy": "JIT_DURING_QA",
            "min_v3_slides_quota": 1,
            "v3_designated_slide_indices": [],
        },
    }
    init_elastic = init_storyboard_manifest(
        {
            "workflow_mode": "GRILL",
            "grill_mode": True,
            "global_deck_blueprint": elastic_bp,
            "narrative_spec": base_narrative,
            "mechanism_spec": base_mechanism,
            "storyboard_slides": base_slides[:1],
        },
        elastic_manifest,
    )
    if init_elastic.get("status") != "PASS":
        raise AssertionError(f"Elastic blueprint init failed: {init_elastic}")

    record_grill_station_capsule(elastic_manifest, 1, grill_cap_1)
    audit_single_slide_step(elastic_manifest, 1, s1_path, valid_bundle, slides_generated_in_current_step=1)

    neg_jit_quota = assemble_verified_deck(elastic_manifest, tdir / "elastic_deck.html")
    if neg_jit_quota.get("status") != "FAIL":
        raise AssertionError(f"Expected assembly to fail when V3 quota (1) not yet met: {neg_jit_quota}")

    mut_split = mutate_storyboard_manifest(
        elastic_manifest,
        {
            "action": "SPLIT_SLIDE",
            "target_slide_index": 1,
            "trigger_source": "QA_DISCOVERY",
            "reason": "问答中发现极化激元反交叉色散需要单独拆出第 2 页并做 V3 交互动画",
            "new_slide_spec": {
                "station_id": "Station_1.2",
                "title": "极化激元反交叉耦合实时色散滑块",
                "layout_archetype": "interactive_svg_sandbox_split",
                "designated_v3_animation": True,
            },
        },
    )
    if mut_split.get("status") != "PASS" or mut_split.get("new_total_slides") != 2:
        raise AssertionError(f"Mid-stream SPLIT_SLIDE failed: {mut_split}")

    mutate_storyboard_manifest(
        elastic_manifest,
        {
            "action": "INSERT_SLIDE",
            "target_slide_index": 2,
            "trigger_source": "QA_DISCOVERY",
            "reason": "临时增加第 3 页备用推导",
            "new_slide_spec": {"station_id": "Station_1.3", "title": "备用推导页"},
        },
    )
    mut_merge = mutate_storyboard_manifest(
        elastic_manifest,
        {
            "action": "MERGE_SLIDES",
            "target_slide_index": 3,
            "trigger_source": "QA_DISCOVERY",
            "reason": "问答确认用户已熟知该推导，合并删减第 3 页",
        },
    )
    if mut_merge.get("status") != "PASS" or mut_merge.get("new_total_slides") != 2:
        raise AssertionError(f"Mid-stream MERGE_SLIDES failed: {mut_merge}")

    record_grill_station_capsule(
        elastic_manifest,
        2,
        {**grill_cap_1, "station_id": "Station_1.2", "visual_modality": "V3_interactive_anticrossing_slider"},
    )
    audit_single_slide_step(elastic_manifest, 2, s2_path, valid_bundle, slides_generated_in_current_step=1)
    pos_elastic_asm = assemble_verified_deck(elastic_manifest, tdir / "elastic_deck.html")
    if pos_elastic_asm.get("status") != "PASS" or pos_elastic_asm.get("total_slides_assembled") != 2:
        raise AssertionError(f"Expected elastic deck assembly with JIT V3 slide to pass: {pos_elastic_asm}")
    return elastic_bp


def _selftest_part_f_and_g_onion_and_io_bus(
    tdir: Path,
    base_narrative: Dict[str, Any],
    base_mechanism: Dict[str, Any],
    base_slides: List[Dict[str, Any]],
    s1_path: Path,
    s2_path: Path,
    valid_bundle: Dict[str, Any],
    grill_cap_1: Dict[str, Any],
    elastic_bp: Dict[str, Any],
) -> None:
    onion_manifest = tdir / "onion_manifest.json"
    onion_cap = {
        "layer0_macro_frame": {
            "core_thesis": "蓝光磷光微秒级寿命引发高亮度 TTA 烧屏，利用极化激元反交叉耦合压缩寿命破局",
            "macro_trunks_mcq": {
                "options": ["A (Recommended): 主干1(痛点死结) -> 主干2(反交叉破局机理)", "B: 倒叙主干"],
                "selected_option": "A (Recommended): 主干1(痛点死结) -> 主干2(反交叉破局机理)",
                "macro_trunks": [
                    {"trunk_id": "Trunk_1", "title": "痛点死结", "status": "PEELING"},
                    {"trunk_id": "Trunk_2", "title": "反交叉破局机理", "status": "UNPEELED"},
                ],
            },
        },
        "peeled_trunks": [
            {
                "trunk_id": "Trunk_1",
                "trunk_subframe_mcq": {
                    "options": ["A (Recommended): 主干1内先做1页自旋统计与TTA死结", "B: 拆成3页"],
                    "selected_option": "A (Recommended): 主干1内先做1页自旋统计与TTA死结",
                    "sub_nodes": [
                        {"node_id": "Station_1.1", "node_type": "LEAF_SLIDE", "title": "电激发自旋统计决定磷光路线"}
                    ],
                },
            }
        ],
    }
    init_onion = init_storyboard_manifest(
        {
            "workflow_mode": "GRILL",
            "grill_mode": True,
            "onion_peeling_capsule": onion_cap,
            "narrative_spec": base_narrative,
            "mechanism_spec": base_mechanism,
            "storyboard_slides": base_slides[:1],
        },
        onion_manifest,
    )
    if init_onion.get("status") != "PASS":
        raise AssertionError(f"Onion init failed: {init_onion}")

    record_grill_station_capsule(onion_manifest, 1, grill_cap_1)
    audit_single_slide_step(onion_manifest, 1, s1_path, valid_bundle, slides_generated_in_current_step=1)

    neg_unpeeled = assemble_verified_deck(onion_manifest, tdir / "onion_deck.html")
    if neg_unpeeled.get("status") != "FAIL":
        raise AssertionError(f"Expected assembly failure while Trunk_2 is UNPEELED: {neg_unpeeled}")

    peel_t2 = peel_onion_trunk_subframe(
        onion_manifest,
        {
            "trunk_id": "Trunk_2",
            "trunk_subframe_mcq": {
                "options": ["A (Recommended): 主干2细分为极化激元反交叉耦合 V3 交互动画页", "B: 静态图"],
                "selected_option": "A (Recommended): 主干2细分为极化激元反交叉耦合 V3 交互动画页",
                "sub_nodes": [
                    {
                        "node_id": "Station_2.1",
                        "node_type": "LEAF_SLIDE",
                        "title": "极化激元反交叉耦合加速辐射衰减",
                        "designated_v3_animation": True,
                    }
                ],
            },
        },
    )
    if peel_t2.get("status") != "PASS" or peel_t2.get("total_slides") != 2:
        raise AssertionError(f"Peeling Trunk_2 failed: {peel_t2}")

    record_grill_station_capsule(
        onion_manifest,
        2,
        {**grill_cap_1, "station_id": "Station_2.1", "visual_modality": "V3_interactive_rabi_splitting"},
    )
    audit_single_slide_step(onion_manifest, 2, s2_path, valid_bundle, slides_generated_in_current_step=1)
    pos_onion_asm = assemble_verified_deck(onion_manifest, tdir / "onion_deck.html")
    if pos_onion_asm.get("status") != "PASS" or pos_onion_asm.get("total_slides_assembled") != 2:
        raise AssertionError(f"Expected Onion Peeling deck assembly to pass: {pos_onion_asm}")

    io_bus_manifest = tdir / "io_bus_manifest.json"
    init_io_bus = init_storyboard_manifest(
        {
            "workflow_mode": "GRILL",
            "global_deck_blueprint": elastic_bp,
            "universal_io_bus_capsule": {
                "evidence_ingest_ledger": [
                    {
                        "claim_id": "Claim_EUV_Yield",
                        "quantitative_value": "88.5% @ 22 mJ/cm2",
                        "source_artifact_or_figure_ref": "Fig2b_XPS_and_CP2K_log.out",
                    }
                ],
                "devil_reviewer_capsule": {
                    "alternative_hypothesis_challenge": "审稿人质疑：产率提升是否仅源于表面粗糙度引起的局部光场增强而非极化激元耦合？",
                    "control_evidence_rebuttal": "对照实验反驳：失谐控制组在相同粗糙度下无拉比劈裂且产率仅 31%，排除单纯粗糙度假说。",
                },
                "output_artifact_targets": ["HTML_PPT", "SCI_WORD", "FIG_PPTX"],
            },
            "narrative_spec": base_narrative,
            "mechanism_spec": base_mechanism,
            "storyboard_slides": base_slides,
        },
        io_bus_manifest,
    )
    if init_io_bus.get("status") != "PASS":
        raise AssertionError(f"Universal IO Bus init failed: {init_io_bus}")

    record_grill_station_capsule(io_bus_manifest, 1, grill_cap_1)
    audit_single_slide_step(io_bus_manifest, 1, s1_path, valid_bundle, slides_generated_in_current_step=1)
    record_grill_station_capsule(
        io_bus_manifest,
        2,
        {**grill_cap_1, "station_id": "Station_1.2", "visual_modality": "V3_interactive_rabi_splitting"},
    )
    audit_single_slide_step(io_bus_manifest, 2, s2_path, valid_bundle, slides_generated_in_current_step=1)

    neg_io_asm = assemble_verified_deck(io_bus_manifest, tdir / "io_bus_deck.html")
    if neg_io_asm.get("status") != "FAIL":
        raise AssertionError(f"Expected assembly failure when SCI_WORD/FIG_PPTX receipts are missing: {neg_io_asm}")

    rec_word = record_cross_artifact_unit_receipt(
        io_bus_manifest,
        {
            "artifact_channel": "SCI_WORD",
            "unit_id": "Section_2_Results_And_Discussion",
            "awf_skill_id": "skill.build-scientific-docx@1.0.0-rc.13",
            "audit_status": "PASS",
            "evidence_claim_ids_used": ["Claim_EUV_Yield"],
        },
    )
    rec_fig = record_cross_artifact_unit_receipt(
        io_bus_manifest,
        {
            "artifact_channel": "FIG_PPTX",
            "unit_id": "Figure_2_Composite_Editable_PPTX",
            "awf_skill_id": "skill.build-editable-figure-pptx@1.0.0-rc.2",
            "audit_status": "PASS",
            "evidence_claim_ids_used": ["Claim_EUV_Yield"],
        },
    )
    if rec_word.get("status") != "PASS" or rec_fig.get("status") != "PASS":
        raise AssertionError(f"Cross-artifact unit receipts failed: {rec_word} / {rec_fig}")

    pos_io_asm = assemble_verified_deck(io_bus_manifest, tdir / "io_bus_deck.html")
    if pos_io_asm.get("status") != "PASS":
        raise AssertionError(f"Expected Universal IO Bus assembly to pass after all 3 channels verified: {pos_io_asm}")


def _selftest_part_h_background_bridge(
    tdir: Path,
    base_narrative: Dict[str, Any],
    base_mechanism: Dict[str, Any],
    s1_path: Path,
    valid_bundle: Dict[str, Any],
    grill_cap_1: Dict[str, Any],
) -> None:
    archetypes = ("top_banner_dual_cards", "split_left_fig_right_steps", "interactive_svg_sandbox_split")
    ten_slides = [
        {
            "station_id": f"Station_BG_{idx}" if idx <= 3 else f"Station_M_{idx}",
            "title": f"第 {idx} 页断言式标题讲解钙钛矿光伏与界面复合",
            "layout_archetype": archetypes[(idx - 1) % len(archetypes)],
            "is_background_slide": idx <= 3,
            "background_rung": idx if idx <= 3 else None,
            "required_visual_level": "V2",
        }
        for idx in range(1, 11)
    ]
    neg_no_bg = init_storyboard_manifest(
        {
            "workflow_mode": "GRILL",
            "narrative_spec": base_narrative,
            "mechanism_spec": base_mechanism,
            "storyboard_slides": ten_slides,
        },
        tdir / "neg_no_bg_manifest.json",
    )
    if neg_no_bg.get("status") != "FAIL":
        raise AssertionError(f"Expected 10-slide full-paper deck without domain_background_bridge to fail: {neg_no_bg}")

    valid_bridge = {
        "pdf_omitted_background_gaps": [
            "原始 PDF 默认读者熟知倒置 p-i-n 钙钛矿电池五层三明治工作闭环，未画基础器件工作原理图",
            "原始 PDF 直接抛出准费米能级劈裂 QFLS 与界面非辐射复合，未解释其与开路电压 Voc 损失的物理关系",
        ],
        "outside_pdf_onboarding_primer": (
            "在看论文的钝化分子之前，我们先用大白话建立全局图景：钙钛矿太阳能电池像五层三明治，"
            "光照产生电子和空穴分头跑向两极；但表面缺陷像收费站坑洞，电子掉进去白白发热，"
            "导致实际输出电压远低于理论极限。"
        ),
        "four_rung_funnel": {
            "rung1_macro_industry_stakes": "单结晶硅电池逼近 29.4% 理论极限，溶液法钙钛矿叠层是突破 33% 效率天花板的核心路线",
            "rung2_canonical_working_principle": {
                "summary": "光子激发钙钛矿层产生电子-空穴对，分别经电子传输层 ETL 与空穴传输层 HTL 选择性抽取形成光电流",
                "visual_schematic_plan": "手绘定制 SVG 五层 p-i-n 器件截面能级滑梯图 + 电子空穴分离流向箭头（严格禁止纯文字背景页）",
            },
            "rung3_core_jargon_translations": [
                {
                    "term": "准费米能级劈裂 (QFLS)",
                    "plain_analogy": "水电站上下游蓄水池的最大水位差（内部真实最高电压潜力）",
                    "physical_meaning": "光照非平衡态下电子与空穴化学势之差，决定开路电压热力学上限",
                },
                {
                    "term": "界面非辐射复合",
                    "plain_analogy": "水流还没到水轮机就从坝体裂缝漏掉白白摩擦生热",
                    "physical_meaning": "载流子在传输层界面缺陷态被捕获并以声子热能形式复合损失",
                },
            ],
            "rung4_prior_art_deadlock": "传统长链铵盐钝化虽能堵住表面缺陷坑洞，但绝缘外壳阻碍电荷跨界面抽取，陷入开路电压与填充因子顾此失彼死结",
        },
        "background_slide_indices": [1, 2, 3],
        "paper_claims_strictly_from_pdf": True,
    }
    one_bg_slides = [{**s, "is_background_slide": i == 1, "background_rung": 1 if i == 1 else None} for i, s in enumerate(ten_slides, start=1)]
    neg_compressed_bg = init_storyboard_manifest(
        {
            "workflow_mode": "GRILL",
            "domain_background_bridge": {**valid_bridge, "background_slide_indices": [1]},
            "narrative_spec": base_narrative,
            "mechanism_spec": base_mechanism,
            "storyboard_slides": one_bg_slides,
        },
        tdir / "neg_compressed_bg_manifest.json",
    )
    if neg_compressed_bg.get("status") != "FAIL":
        raise AssertionError(f"Expected 10-slide deck with only 1 background slide to fail D13: {neg_compressed_bg}")

    bg_grill_manifest = tdir / "bg_grill_manifest.json"
    pos_bg_init = init_storyboard_manifest(
        {
            "workflow_mode": "GRILL",
            "grill_mode": True,
            "domain_background_bridge": valid_bridge,
            "narrative_spec": base_narrative,
            "mechanism_spec": base_mechanism,
            "storyboard_slides": ten_slides,
        },
        bg_grill_manifest,
    )
    if pos_bg_init.get("status") != "PASS":
        raise AssertionError(f"Expected valid 10-slide 4-rung background deck init to pass: {pos_bg_init}")

    neg_grill_no_briefing = record_grill_station_capsule(
        bg_grill_manifest,
        1,
        {**grill_cap_1, "question_archetype": "FOUNDATION_INTUITION_BUILD"},
    )
    if neg_grill_no_briefing.get("status") != "FAIL":
        raise AssertionError(f"Expected background grill station without background_briefing_anchor to fail: {neg_grill_no_briefing}")

    pos_grill_with_briefing = record_grill_station_capsule(
        bg_grill_manifest,
        1,
        {
            **grill_cap_1,
            "question_archetype": "FOUNDATION_INTUITION_BUILD",
            "background_briefing_anchor": "先补齐论文省略的五层三明治背景：光照在钙钛矿中产生电子和空穴，分别向两侧传输层滑落输出电压。",
        },
    )
    neg_disconnected_rung1 = audit_single_slide_step(
        bg_grill_manifest, 1, s1_path, valid_bundle, slides_generated_in_current_step=1
    )
    if neg_disconnected_rung1.get("status") != "FAIL":
        raise AssertionError(
            f"Expected PHOLED HTML disconnected from Perovskite Rung-1 stakes to fail D13: {neg_disconnected_rung1}"
        )
    bg_s1_path = tdir / "bg_pv_rung1_s01.html"
    bg_s1_path.write_text(
        "<!DOCTYPE html><html><head><script src='katex.min.js'></script></head>"
        "<body><section class='slide'><h2>单结晶硅电池逼近 29.4% 极限，溶液法钙钛矿叠层开辟破限路线</h2>"
        "<p>左图 1a 展示晶硅天花板与溶液法钙钛矿叠层优势。</p></section></body></html>",
        encoding="utf-8",
    )
    bg_valid_bundle = {
        **valid_bundle,
        "required_acronyms": (),
        "slides": [
            {
                "title": "单结晶硅电池逼近 29.4% 极限，溶液法钙钛矿叠层开辟破限路线",
                "subtitle": "低温涂布薄膜突破传统晶硅面积与成本瓶颈",
                "body": "左图 1a 展示晶硅与钙钛矿叠层路线。",
                "visible_text": "单结晶硅电池逼近 29.4% 理论极限，溶液法钙钛矿叠层开辟破限路线",
                "notes_text": "",
                "defined_terms_visible": [],
                "inline_popover_count": 1,
            }
        ],
    }
    pos_bg_s1 = audit_single_slide_step(
        bg_grill_manifest, 1, bg_s1_path, bg_valid_bundle, slides_generated_in_current_step=1
    )
    rec_bg_update = record_domain_background_bridge(bg_grill_manifest, valid_bridge)
    if pos_grill_with_briefing.get("status") != "PASS" or pos_bg_s1.get("status") != "PASS" or rec_bg_update.get("status") != "PASS":
        raise AssertionError(f"Expected background grill station with briefing to pass: {pos_grill_with_briefing}, {pos_bg_s1}, {rec_bg_update}")

    bg_tdd_manifest = tdir / "bg_tdd_manifest.json"
    init_storyboard_manifest(
        {
            "workflow_mode": "TDD",
            "tdd_mode": True,
            "domain_background_bridge": valid_bridge,
            "narrative_spec": base_narrative,
            "mechanism_spec": base_mechanism,
            "storyboard_slides": ten_slides,
        },
        bg_tdd_manifest,
    )
    base_tdd_cap = {
        "station_id": "Station_BG_1",
        "core_blindspot_or_conflict": "读者不了解钙钛矿五层器件如何把光子变成电压以及为何界面缺陷会漏电",
        "wittgenstein_ladder": "Bridge: 水电站大坝水位落差 -> Deconstruct: 宏观水压忽略界面缺陷态非辐射复合漏流 -> Replace: 准费米能级劈裂 QFLS = kT ln(np/ni^2) 决定开路电压上限",
        "human_orthogonal_insight": "用户要求先画清楚电子和空穴各自往哪边跑，再谈论文的钝化分子",
        "visual_modality": "V2_custom_svg_pin_device_energy_diagram",
        "hidden_teleprompter_qa": "按 S 键展开：为什么倒置 p-i-n 结构比正式 n-i-p 更容易与晶硅做叠层？",
    }
    neg_tdd_no_syn = record_tdd_station_capsule(bg_tdd_manifest, 1, base_tdd_cap)
    if neg_tdd_no_syn.get("status") != "FAIL":
        raise AssertionError(f"Expected TDD background station without beyond_pdf_background_synthesis to fail: {neg_tdd_no_syn}")
    pos_tdd_syn = record_tdd_station_capsule(
        bg_tdd_manifest,
        1,
        {
            **base_tdd_cap,
            "beyond_pdf_background_synthesis": "主动补齐论文未写的 p-i-n 五层器件能带工作原理与水电站水位差类比，建立零门槛物理直觉。",
        },
    )
    if pos_tdd_syn.get("status") != "PASS":
        raise AssertionError(f"Expected TDD background station with synthesis to pass: {pos_tdd_syn}")


def _selftest_part_i_redundancy_and_viewport_autofit(
    tdir: Path,
    base_narrative: Dict[str, Any],
    base_mechanism: Dict[str, Any],
    base_slides: List[Dict[str, Any]],
    valid_bundle: Dict[str, Any],
) -> None:
    vp_manifest = tdir / "vp_density_manifest.json"
    init_storyboard_manifest(
        {
            "workflow_mode": "AUTONOMOUS_DUAL_EVOLVE",
            "autonomous_dual_evolve_mode": True,
            "narrative_spec": base_narrative,
            "mechanism_spec": base_mechanism,
            "storyboard_slides": base_slides[:1],
        },
        vp_manifest,
    )
    svg_labels = "".join(
        f"<text font-size='20'>{lbl}</text>"
        for lbl in (
            "单结晶硅电池", "硅极限 29.4%", "27.3%", "硅片厚 150 µm", "间接带隙 1.12 eV", "余量仅 2.1%",
            "钙钛矿单结电池", "单结极限 33.7%", "27.6%", "超薄膜 0.6 µm", "直接带隙 1.48 eV", "纯相认证值",
            "钙钛矿晶硅叠层", "双结极限 45.1%", "34.6%", "跨越单结天花板", "顶层宽带隙钙钛矿", "底层晶硅串联",
        )
    )
    bad_v1_path = tdir / "bad_s02_v1.html"
    bad_v1_path.write_text(
        "<section class='slide' id='s02'><style>#s02{width:1600px;height:900px;}</style>"
        f"<svg>{svg_labels}</svg>"
        "<article><h2>第1阶 单结晶硅逼近天花板</h2><p>晶体硅已达 27.3%，距 29.4% 极限仅剩余量，间接带隙 1.12 eV 需 150 µm 厚硅片。</p></article>"
        "<article><h2>第2阶 钙钛矿单结超薄追平</h2><p>钙钛矿仅需 0.6 µm 薄膜吸光，纯相认证达 27.6%，逼近单结极限 33.7%。</p></article>"
        "<article><h2>第3阶 钙钛矿晶硅叠层破壁</h2><p>顶层宽带隙钙钛矿配底层晶硅串联分段捕光，效率跨过 34.6% 迈向 45.1%。</p></article>"
        "</section>",
        encoding="utf-8",
    )
    neg_v1 = audit_single_slide_step(vp_manifest, 1, bad_v1_path, valid_bundle, slides_generated_in_current_step=1)
    if neg_v1.get("status") != "FAIL" or "D6_Teleprompter_Hidden_And_Slide_Density_Cadence_Guard" not in neg_v1.get("failed_gates", []):
        raise AssertionError(f"Expected initial overloaded + unfitted Slide 02 v1 canary to fail D6: {neg_v1}")

    bad_v2_path = tdir / "bad_s02_v2_unfitted.html"
    bad_v2_path.write_text(
        "<section class='slide' id='s02'><style>#s02{width:1600px;height:900px;}</style>"
        f"<svg>{svg_labels}</svg><p>代际跃迁判据：单结追平晶硅，叠层跨越 34% 门槛。</p></section>",
        encoding="utf-8",
    )
    neg_v2 = audit_single_slide_step(vp_manifest, 1, bad_v2_path, valid_bundle, slides_generated_in_current_step=1)
    if neg_v2.get("status") != "FAIL" or "D6_Teleprompter_Hidden_And_Slide_Density_Cadence_Guard" not in neg_v2.get("failed_gates", []):
        raise AssertionError(f"Expected unfitted 1600x900 Slide 02 v2 canary without viewport auto-fit to fail D6: {neg_v2}")

    clean_svg_labels = "".join(
        f"<text font-size='34'>{lbl}</text>"
        for lbl in ("单结晶硅 29.4%", "钙钛矿单结 27.6%", "双结叠层 34.6%", "分级捕光")
    )
    good_v3_path = tdir / "good_s02_v3_fitted.html"
    good_v3_path.write_text(
        "<section class='slide' id='s02'><style>"
        "html,body{margin:0;width:100%;height:100%;overflow:hidden;}"
        "#s02{position:fixed;left:50%;top:50%;width:1600px;height:900px;transform:translate(-50%,-50%) scale(1);}"
        "</style><svg>" + clean_svg_labels + "</svg><p style='font-size:38px;'>叠层跨越 34% 效率门槛。</p>"
        "<script>const fit=()=>{const s=Math.min(window.innerWidth/1600,window.innerHeight/900);"
        "document.getElementById('s02').style.transform=`translate(-50%,-50%) scale(${s})`;};fit();</script>"
        "</section>",
        encoding="utf-8",
    )
    pos_v3 = audit_single_slide_step(vp_manifest, 1, good_v3_path, valid_bundle, slides_generated_in_current_step=1)
    if pos_v3.get("status") != "PASS":
        raise AssertionError(f"Expected clean viewport-fitted 1600x900 Slide 02 v3 to pass: {pos_v3}")


def _selftest_part_j_inline_svg_font_floor_and_char_overload(
    tdir: Path,
    base_narrative: Dict[str, Any],
    base_mechanism: Dict[str, Any],
    base_slides: List[Dict[str, Any]],
    valid_bundle: Dict[str, Any],
) -> None:
    svg_manifest = tdir / "svg_typo_manifest.json"
    init_storyboard_manifest(
        {
            "workflow_mode": "AUTONOMOUS_DUAL_EVOLVE",
            "autonomous_dual_evolve_mode": True,
            "narrative_spec": base_narrative,
            "mechanism_spec": base_mechanism,
            "storyboard_slides": base_slides[:1],
        },
        svg_manifest,
    )
    bad_tiny_svg = tdir / "bad_svg_14px.html"
    bad_tiny_svg.write_text(
        "<section class='slide'><svg viewBox='0 0 1760 660'>"
        "<text font-size='14'>银电极功函数 4.28 eV</text></svg></section>",
        encoding="utf-8",
    )
    neg_tiny = audit_single_slide_step(svg_manifest, 1, bad_tiny_svg, valid_bundle, slides_generated_in_current_step=1)
    if neg_tiny.get("status") != "FAIL" or "D6_Teleprompter_Hidden_And_Slide_Density_Cadence_Guard" not in neg_tiny.get("failed_gates", []):
        raise AssertionError(f"Expected <18px inline SVG font canary to fail D6: {neg_tiny}")

    bad_vb_spoof = tdir / "bad_svg_viewbox_spoof.html"
    bad_vb_spoof.write_text(
        "<section class='slide'><svg viewBox='0 0 3840 1200'>"
        "<text font-size='18'>超大坐标缩水伪装</text></svg></section>",
        encoding="utf-8",
    )
    neg_vb = audit_single_slide_step(svg_manifest, 1, bad_vb_spoof, valid_bundle, slides_generated_in_current_step=1)
    if neg_vb.get("status") != "FAIL":
        raise AssertionError(f"Expected viewBox-downscaled <18px SVG font spoof to fail: {neg_vb}")

    bad_s01_v1 = tdir / "bad_s01_v1_overload.html"
    crowded_labels = "".join(
        f"<text font-size='18'>能级与界面复合标签{idx}</text>" for idx in range(SELFTEST_OVERLOAD_SVG_LABEL_COUNT)
    )
    crowded_prose = "裸银阴极直接接触活性层同时引发肖特基注入势垒与空穴表面复合双重损失。" * SELFTEST_OVERLOAD_PROSE_REPEAT
    bad_s01_v1.write_text(
        f"<section class='slide'><svg>{crowded_labels}</svg><div>{crowded_prose}</div></section>",
        encoding="utf-8",
    )
    neg_overload = audit_single_slide_step(svg_manifest, 1, bad_s01_v1, valid_bundle, slides_generated_in_current_step=1)
    if neg_overload.get("status") != "FAIL":
        raise AssertionError(f"Expected 1,222-char / 37-label Slide 01 v1 overload canary to fail: {neg_overload}")

    good_svg_19px = tdir / "good_svg_34px.html"
    good_svg_19px.write_text(
        "<section class='slide'><header class='slide-header'><h2>阴极修饰层消除裸银双重界面损失</h2></header>"
        "<svg viewBox='0 0 1760 660'>"
        "<text font-size='36'>五层器件截面</text><text font-size='34'>功函数 4.28 eV</text>"
        "<text font-size='34'>注入势垒 0.38 eV</text><text font-size='34'>阻挡空穴复合</text>"
        "</svg>"
        "<div class='term-popover' hidden>隐藏术语解释卡片不计入画布正文字数预算。</div>"
        "<aside class='notes'>隐藏讲稿不计入画布正文字数预算。</aside>"
        "<footer class='takeaway-strip'>同时压低有效功函数并阻挡漏电。</footer></section>",
        encoding="utf-8",
    )
    pos_svg = audit_single_slide_step(svg_manifest, 1, good_svg_19px, valid_bundle, slides_generated_in_current_step=1)
    if pos_svg.get("status") != "PASS":
        raise AssertionError(f"Expected clean >=18px inline SVG slide to pass: {pos_svg}")


def _selftest_part_k_unread_pdf_intent_triage_and_jit_grill_focus(
    tdir: Path,
    base_narrative: Dict[str, Any],
    base_mechanism: Dict[str, Any],
    base_slides: List[Dict[str, Any]],
) -> None:
    blind_manifest = tdir / "unread_blind_manifest.json"
    neg_blind_init = init_storyboard_manifest(
        {
            "workflow_mode": "GRILL",
            "grill_mode": True,
            "global_deck_blueprint": {
                "macro_thesis_probe": {
                    "executive_core_conflict": "蓝光磷光微秒级寿命引发高亮度 TTA 烧屏，利用极化激元反交叉耦合压缩寿命破局",
                    "human_baseline_alignment": "用户完全没看过 PDF，希望靠问答理解这篇工作",
                    "user_has_read_pdf": False,
                },
                "emphasis_allocation_mcq": {
                    "user_has_read_pdf": False,
                    "question_prompt": "以下哪些模块需要作为重头戏展开讲？",
                    "options": ["A: ETL/SPP 色散反交叉哈密顿量", "B: TTA 双分子动力学与 LT95 测试"],
                    "selected_option": "A: ETL/SPP 色散反交叉哈密顿量",
                    "heavy_focus_modules": ["ETL/SPP 色散反交叉"],
                },
                "v3_animation_budget_mcq": {
                    "options": ["A (Recommended): 讲到抽象难点时当场拍板加动态演示", "B: 仅用静态图"],
                    "selected_option": "A (Recommended): 讲到抽象难点时当场拍板加动态演示",
                    "v3_discovery_policy": "JIT_DURING_QA",
                    "min_v3_slides_quota": 1,
                    "v3_designated_slide_indices": [],
                },
            },
            "narrative_spec": base_narrative,
            "mechanism_spec": base_mechanism,
            "storyboard_slides": base_slides,
        },
        blind_manifest,
    )
    if neg_blind_init.get("status") != "FAIL":
        raise AssertionError(f"Expected unread-PDF cold blind-module emphasis quiz to fail init: {neg_blind_init}")

    neg_slide_count_quiz = init_storyboard_manifest(
        {
            "workflow_mode": "GRILL",
            "grill_mode": True,
            "global_deck_blueprint": {
                "macro_thesis_probe": {
                    "executive_core_conflict": "蓝光磷光微秒级寿命引发高亮度 TTA 烧屏，利用极化激元反交叉耦合压缩寿命破局",
                    "human_baseline_alignment": "测试即使未加任何额外开关，也不得再向用户提问页数选择题",
                },
                "total_slides_mcq": {
                    "options": ["A: 页数不限", "B: 10–14页紧凑档"],
                    "selected_option": "A: 页数不限",
                    "slide_count_policy": "UNBOUNDED_FLOW_DRIVEN",
                },
                "emphasis_allocation_mcq": {
                    "options": ["A (Recommended): 重点深挖极化激元反交叉耦合", "B: 重点讲工艺"],
                    "selected_option": "A (Recommended): 重点深挖极化激元反交叉耦合",
                    "heavy_focus_modules": ["极化激元反交叉耦合"],
                },
                "v3_animation_budget_mcq": {
                    "options": ["A (Recommended): 讲到抽象难点时当场拍板加动态演示", "B: 仅用静态图"],
                    "selected_option": "A (Recommended): 讲到抽象难点时当场拍板加动态演示",
                    "v3_discovery_policy": "JIT_DURING_QA",
                    "min_v3_slides_quota": 1,
                    "v3_designated_slide_indices": [],
                },
            },
            "narrative_spec": base_narrative,
            "mechanism_spec": base_mechanism,
            "storyboard_slides": base_slides,
        },
        tdir / "neg_slide_count_quiz_manifest.json",
    )
    if neg_slide_count_quiz.get("status") != "FAIL":
        raise AssertionError(f"Expected asking total_slides_mcq to be rejected unconditionally: {neg_slide_count_quiz}")

    jit_focus_manifest = tdir / "unread_jit_focus_manifest.json"
    pos_jit_init = init_storyboard_manifest(
        {
            "workflow_mode": "GRILL",
            "grill_mode": True,
            "global_deck_blueprint": {
                "macro_thesis_probe": {
                    "executive_core_conflict": "蓝光磷光微秒级寿命引发高亮度 TTA 烧屏，利用极化激元反交叉耦合压缩寿命破局",
                    "human_baseline_alignment": "用户尚未读过 PDF，页数一律不问不锁死、只看逻辑和需要，重头戏边烤问边动态定",
                    "user_has_read_pdf": False,
                },
                "ai_value_triage": {
                    "core_breakthrough_gem": "全篇真王牌是借金属镜面光学共振给慢吞吞的蓝光三重态抢时间，机理巧妙反直觉",
                    "foundation_bridge_summary": "先用三页补齐发光器件三明治原理、自旋分流与能量拥堵死结",
                    "routine_fast_forward_zone": "后半部分蒸镀工艺参数与常规寿命表征属于标准动作，一页概览即可",
                },
                "emphasis_allocation_mcq": {
                    "user_has_read_pdf": False,
                    "emphasis_policy": "JIT_DURING_GRILL",
                    "question_prompt": "看完上面的全文干货与常规区剧透，你这次听讲更倾向哪种方式？",
                    "options": [
                        "A (Recommended): 吃透核心脑洞（AI主导拆解最巧妙的光学加速破局机理，常规表征一页带过）",
                        "B: 借鉴实验配方与防坑（重点看器件结构怎么搭、对照实验怎么做）",
                        "C: 边问边定（现在先不锁死重头戏，后面哪块答错卡壳或感兴趣再当场拆页深挖）",
                    ],
                    "selected_option": "C: 边问边定（现在先不锁死重头戏，后面哪块答错卡壳或感兴趣再当场拆页深挖）",
                    "heavy_focus_modules": [],
                },
                "v3_animation_budget_mcq": {
                    "options": ["A (Recommended): 讲到抽象难点时当场拍板加动态演示", "B: 仅用静态图"],
                    "selected_option": "A (Recommended): 讲到抽象难点时当场拍板加动态演示",
                    "v3_discovery_policy": "JIT_DURING_QA",
                    "min_v3_slides_quota": 1,
                    "v3_designated_slide_indices": [],
                },
            },
            "narrative_spec": base_narrative,
            "mechanism_spec": base_mechanism,
            "storyboard_slides": base_slides,
        },
        jit_focus_manifest,
    )
    if pos_jit_init.get("status") != "PASS":
        raise AssertionError(f"Expected zero-slide-count-MCQ + unread-PDF Intent/JIT init to pass: {pos_jit_init}")

    promote_rep = mutate_storyboard_manifest(
        jit_focus_manifest,
        {
            "action": "PROMOTE_HEAVY_FOCUS",
            "target_slide_index": 2,
            "trigger_source": "GRILL_MISS_BOTTLENECK",
            "focus_module": "极化激元反交叉耦合加速辐射衰减",
            "reason": "用户在反交叉平缓色散为何放大光学态密度处卡壳并追问，当场升级为重头戏拆出交互页",
            "new_slide_spec": {
                "station_id": "Station_1.2b_deepdive",
                "title": "色散斜率趋缓使界面光学态密度成倍放大并加速辐射",
                "layout_archetype": "interactive_svg_sandbox_split",
                "designated_v3_animation": True,
            },
        },
    )
    if promote_rep.get("status") != "PASS" or promote_rep.get("new_total_slides") != len(base_slides) + 1:
        raise AssertionError(f"Expected PROMOTE_HEAVY_FOCUS mutation to add companion deep-dive slide: {promote_rep}")
    updated_doc = json.loads(jit_focus_manifest.read_text(encoding="utf-8"))
    jit_mods = updated_doc["global_deck_blueprint"]["emphasis_allocation_mcq"].get("jit_discovered_focus_modules", [])
    if "极化激元反交叉耦合加速辐射衰减" not in jit_mods:
        raise AssertionError(f"Expected module recorded in jit_discovered_focus_modules, got: {jit_mods}")


def _selftest_part_l_ai_scaffolding_and_hollow_card_typography(
    tdir: Path,
    base_narrative: Dict[str, Any],
    base_mechanism: Dict[str, Any],
    base_slides: List[Dict[str, Any]],
    valid_bundle: Dict[str, Any],
) -> None:
    scaf_manifest = tdir / "scaf_hollow_manifest.json"
    init_storyboard_manifest(
        {
            "workflow_mode": "AUTONOMOUS_DUAL_EVOLVE",
            "autonomous_dual_evolve_mode": True,
            "narrative_spec": base_narrative,
            "mechanism_spec": base_mechanism,
            "storyboard_slides": base_slides[:1],
        },
        scaf_manifest,
    )
    bad_scaf_path = tdir / "bad_s02_ai_scaf.html"
    bad_scaf_path.write_text(
        "<section class='slide'><style>.kicker{font-size:17px;}</style>"
        "<header><span class='kicker'>背景导读第 1 阶 · 宏观产业痛点与传统单晶衍射天花板</span></header>"
        "<h2>PHOLED（磷光有机发光二极管）自旋统计</h2>"
        "<footer>背景知识补齐（论文外通用晶体学图景）· Rung 1: Macro Stakes</footer></section>",
        encoding="utf-8",
    )
    neg_scaf = audit_single_slide_step(scaf_manifest, 1, bad_scaf_path, valid_bundle, slides_generated_in_current_step=1)
    if (
        neg_scaf.get("status") != "FAIL"
        or "D3_Natural_Academic_Copywriting_No_AI_MetaTone" not in neg_scaf.get("failed_gates", [])
        or "D6_Teleprompter_Hidden_And_Slide_Density_Cadence_Guard" not in neg_scaf.get("failed_gates", [])
    ):
        raise AssertionError(f"Expected 17px AI self-scaffolding kicker & Rung footer to fail D3 & D6: {neg_scaf}")

    bad_hollow_path = tdir / "bad_s03_hollow_20px.html"
    bad_hollow_path.write_text(
        "<section class='slide' id='s03'><style>"
        "html,body{margin:0;width:100%;height:100%;overflow:hidden;}"
        "#s03{position:fixed;left:50%;top:50%;width:1920px;height:1080px;transform:translate(-50%,-50%) scale(1);}"
        ".panel{display:flex;flex-direction:column;justify-content:space-between;}"
        "</style><div class='grid-3' style='height:272px;'>"
        "<div class='panel'><div class='panel-hdr'><span>热振动椭球 ADP</span></div>"
        "<p style='font-size:20px;'>即原子位移参数（Atomic Displacement Parameter），类比拍照时被摄者晃动重影：限域越紧，椭球越圆小锐利。</p>"
        "</div></div>"
        "<script>const fit=()=>{const s=Math.min(window.innerWidth/1920,window.innerHeight/1080);"
        "document.getElementById('s03').style.transform=`translate(-50%,-50%) scale(${s})`;};fit();</script></section>",
        encoding="utf-8",
    )
    neg_hollow = audit_single_slide_step(scaf_manifest, 1, bad_hollow_path, valid_bundle, slides_generated_in_current_step=1)
    if (
        neg_hollow.get("status") != "FAIL"
        or "D6_Teleprompter_Hidden_And_Slide_Density_Cadence_Guard" not in neg_hollow.get("failed_gates", [])
    ):
        raise AssertionError(f"Expected 20px body font & hollow 272px space-between card on 1920x1080 slide to fail D6: {neg_hollow}")

    good_clean_hd_path = tdir / "good_s03_clean_hd.html"
    good_clean_hd_path.write_text(
        "<section class='slide' id='s03'><style>"
        "html,body{margin:0;width:100%;height:100%;overflow:hidden;}"
        "#s03{position:fixed;left:50%;top:50%;width:1920px;height:1080px;transform:translate(-50%,-50%) scale(1);}"
        ".panel{display:flex;flex-direction:column;justify-content:flex-start;gap:18px;}"
        "</style><header><span class='topo-breadcrumb' style='font-size:32px;'>晶体学基础 · 03 / 28</span></header>"
        "<div class='grid-2'><div class='panel'><div class='panel-hdr'><span style='font-size:46px;'>孔道限域压扁热椭球</span></div>"
        "<p style='font-size:42px;'>限域越紧热摆动越小，电子密度峰定位越锐利。</p>"
        "<button type='button' class='detail-trigger' data-detail-id='adp_detail' style='font-size:32px;'>+ 精修公式</button>"
        "<template data-detail-id='adp_detail'>原子位移参数 ADP 刻画晶格内原子热摆动均方振幅，与散射衰减直接耦合。</template>"
        "</div></div>"
        "<footer style='font-size:32px;'>Nature 2025, 640, 676</footer>"
        "<script>const fit=()=>{const s=Math.min(window.innerWidth/1920,window.innerHeight/1080);"
        "document.getElementById('s03').style.transform=`translate(-50%,-50%) scale(${s})`;};fit();</script></section>",
        encoding="utf-8",
    )
    pos_clean = audit_single_slide_step(scaf_manifest, 1, good_clean_hd_path, valid_bundle, slides_generated_in_current_step=1)
    if pos_clean.get("status") != "PASS":
        raise AssertionError(f"Expected clean 24px non-hollow audience-facing 1920x1080 slide to pass: {pos_clean}")


def verify_blind_reader_for_manifest(
    manifest_path: Path,
    blind_audit_doc: Dict[str, Any],
) -> Dict[str, Any]:
    """Verify an Anti-Collusion Zero-Context Blind Reader & Outsider Onboarding receipt against `slide_manifest.json`."""
    dag = _load_design_ag_module()
    storyboard_slides: Sequence[Dict[str, Any]] = ()
    domain_background_bridge: Optional[Dict[str, Any]] = None
    universal_io_bus_capsule: Optional[Dict[str, Any]] = None
    visual_entity_manifest: Optional[Sequence[Dict[str, Any]]] = None
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        storyboard_slides = manifest.get("storyboard_slides", ())
        domain_background_bridge = manifest.get("domain_background_bridge")
        universal_io_bus_capsule = manifest.get("universal_io_bus_capsule")
        visual_entity_manifest = manifest.get("visual_entity_manifest")
    res = dag.verify_anti_collusion_blind_reader_audit(
        blind_audit_doc,
        storyboard_slides=storyboard_slides,
        domain_background_bridge=domain_background_bridge,
        universal_io_bus_capsule=universal_io_bus_capsule,
        visual_entity_manifest=visual_entity_manifest,
    )
    if res["passed"] and manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["blind_reader_audit_receipt"] = {
            "passed": True,
            "audited_slide_count": res["audited_slide_count"],
        }
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"status": "PASS" if res["passed"] else "FAIL", **res}


def verify_image_tournament_for_manifest(
    manifest_path: Path,
    tournament_ledger_doc: Dict[str, Any],
    *,
    check_disk_pixels: bool = False,
) -> Dict[str, Any]:
    """Verify 4-axis orthogonal Gen-0 + iterative Gen-1+ evolutionary image tournament ledger."""
    dag = _load_design_ag_module()
    res = dag.verify_evolutionary_image_tournament_ledger(
        tournament_ledger_doc,
        check_disk_pixels=check_disk_pixels,
    )
    if res["passed"] and manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        receipts = manifest.setdefault("image_tournament_receipts", {})
        sid = str(tournament_ledger_doc.get("slide_id", "slide_unknown"))
        receipts[sid] = res
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"status": "PASS" if res["passed"] else "FAIL", **res}


def verify_blind_object_recognition_for_manifest(
    manifest_path: Path,
    blind_obj_doc: Dict[str, Any],
    visual_entity_manifest: Optional[Sequence[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Verify Stage A text-masked PNG blind object recognition + Stage B full-slide alignment."""
    dag = _load_design_ag_module()
    eff_manifest = visual_entity_manifest
    if eff_manifest is None and isinstance(blind_obj_doc, dict):
        eff_manifest = blind_obj_doc.get("visual_entity_manifest")
    if eff_manifest is None and manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        eff_manifest = manifest.get("visual_entity_manifest")
    res = dag.verify_two_stage_blind_object_recognition(blind_obj_doc, eff_manifest)
    if res["passed"] and manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["blind_object_recognition_receipt"] = {
            "passed": True,
            "recognized_object_count": res["recognized_object_count"],
        }
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"status": "PASS" if res["passed"] else "FAIL", **res}


def _selftest_part_m_semantic_coherence_and_anti_collusion_blind_reader(
    tdir: Path,
    base_narrative: Dict[str, Any],
    base_mechanism: Dict[str, Any],
    base_slides: List[Dict[str, Any]],
    valid_bundle: Dict[str, Any],
) -> None:
    manifest_m = tdir / "manifest_m_sem.json"
    init_storyboard_manifest(
        {
            "workflow_mode": "AUTONOMOUS_DUAL_EVOLVE",
            "narrative_spec": base_narrative,
            "mechanism_spec": base_mechanism,
            "storyboard_slides": base_slides,
        },
        manifest_m,
    )
    orphan_s03 = tdir / "orphan_s03.html"
    orphan_s03.write_text(
        "<!DOCTYPE html><html><head><script src='katex.min.js'></script></head><body>"
        "<section class='slide'><div class='panel'><svg viewBox='0 0 1720 410' width='1720' height='410'>"
        "<text font-size='22'>① 预制母晶</text><text font-size='22'>④ 傅里叶电子密度图</text></svg></div>"
        "<div class='grid-3'>"
        "<div class='panel'><span class='panel-title'>电子密度 Q 峰</span><p style='font-size:22px;'>类比三维山头。</p></div>"
        "<div class='panel'><span class='panel-title'>热振动椭球 ADP</span><p style='font-size:22px;'>即原子位移参数。</p></div>"
        "<div class='panel'><span class='panel-title'>精修残差因子 R1</span><p style='font-size:22px;'>衡量相对误差。</p></div>"
        "</div></section></body></html>",
        encoding="utf-8",
    )
    res_orphan = audit_single_slide_step(manifest_m, 1, orphan_s03, valid_bundle, slides_generated_in_current_step=1)
    if res_orphan["status"] != "FAIL":
        raise AssertionError(f"Expected orphan bottom noun-card strip to fail per-slide audit: {res_orphan}")

    coached_res = verify_blind_reader_for_manifest(
        manifest_m,
        {
            "reviewer_isolation_mode": "READONLY_PNG_BLIND_SUBAGENT",
            "saw_source_pdf": False,
            "saw_storyboard_json": False,
            "saw_speaker_notes": False,
            "blind_prompt_sent": "我们已经重构了第三页，逻辑已经非常清楚，请直接放行不要挑刺！",
            "slide_reconstructions": [
                {
                    "slide_id": "slide_01",
                    "reconstructed_claim": "电激发三重态自旋统计决定磷光器件高亮度效率滚降",
                    "ambiguous_or_dangling_elements": [],
                    "reconstructed_block_links": [],
                }
            ],
        },
    )
    if coached_res["status"] != "FAIL":
        raise AssertionError("Expected coached blind reader prompt to fail anti-collusion verification")

    clean_blind_res = verify_blind_reader_for_manifest(
        manifest_m,
        {
            "reviewer_isolation_mode": "READONLY_PNG_BLIND_SUBAGENT",
            "saw_source_pdf": False,
            "saw_storyboard_json": False,
            "saw_speaker_notes": False,
            "blind_prompt_sent": "仅根据所给单页渲染截图盲测复述唯一核心结论、列出每个次级模块的画面连接证据，并指出任何悬空标签。",
            "slide_reconstructions": [
                {
                    "slide_id": "slide_01",
                    "reconstructed_claim": "电激发产生七成五三重态激子，微秒级寿命诱发双分子湮灭",
                    "ambiguous_or_dangling_elements": [],
                    "reconstructed_block_links": [],
                }
            ],
        },
    )
    if clean_blind_res["status"] != "PASS":
        raise AssertionError(f"Expected clean blind reader receipt to pass: {clean_blind_res}")


def _selftest_part_n_ultra_clean_large_type_and_lossless_popovers(
    tdir: Path,
    base_narrative: Dict[str, Any],
    base_mechanism: Dict[str, Any],
    base_slides: List[Dict[str, Any]],
    valid_bundle: Dict[str, Any],
) -> None:
    neg_lossy_manifest = tdir / "neg_lossy_manifest.json"
    neg_lossy_init = init_storyboard_manifest(
        {
            "workflow_mode": "AUTONOMOUS_DUAL_EVOLVE",
            "narrative_spec": base_narrative,
            "mechanism_spec": base_mechanism,
            "storyboard_slides": base_slides,
            "lossless_split_and_popover_ledger": {
                "preserved_evidence_items": [
                    {
                        "content_summary": "Suppl. Fig. 19 高通量饱和界面陷阱对照实验",
                        "carrier_mode": "DROPPED",
                        "target_slide_id": "slide_01",
                        "trigger_or_anchor": "omitted",
                    }
                ]
            },
        },
        neg_lossy_manifest,
    )
    if neg_lossy_init.get("status") != "FAIL":
        raise AssertionError(f"Expected DROPPED lossless ledger item to fail init: {neg_lossy_init}")

    pos_lossless_manifest = tdir / "pos_lossless_manifest.json"
    pos_lossless_init = init_storyboard_manifest(
        {
            "workflow_mode": "AUTONOMOUS_DUAL_EVOLVE",
            "narrative_spec": base_narrative,
            "mechanism_spec": base_mechanism,
            "storyboard_slides": base_slides[:1],
            "lossless_split_and_popover_ledger": {
                "require_topological_breadcrumbs": False,
                "preserved_evidence_items": [
                    {
                        "content_summary": "Fig. 1b 单晶 3.18 Å 横向堆积拆入独立后续页",
                        "carrier_mode": "SPLIT_SLIDE",
                        "target_slide_id": "slide_01",
                        "trigger_or_anchor": "主线① ▸ 1.2",
                    },
                    {
                        "content_summary": "Suppl. Fig. 19 高通量脉冲填满界面陷阱后仍呈慢恢复",
                        "carrier_mode": "CLICKABLE_POPOVER",
                        "target_slide_id": "slide_01",
                        "trigger_or_anchor": "pop_ctrl_19",
                    },
                ],
            },
        },
        pos_lossless_manifest,
    )
    if pos_lossless_init.get("status") != "PASS":
        raise AssertionError(f"Expected valid lossless split+popover manifest to pass: {pos_lossless_init}")

    dangling_slide = tdir / "dangling_pop_slide.html"
    dangling_slide.write_text(
        "<section class='slide' id='s01'><style>"
        "html,body{margin:0;width:100%;height:100%;overflow:hidden;}"
        "#s01{position:fixed;left:50%;top:50%;width:1920px;height:1080px;transform:translate(-50%,-50%) scale(1);}"
        "</style><h1 class='slide-title' style='font-size:58px;'>电激发自旋统计决定磷光 PHOLED</h1>"
        "<button type='button' class='detail-trigger' data-detail-id='ghost_pop' style='font-size:32px;'>+ 对照证据</button>"
        "<script>const s=Math.min(window.innerWidth/1920,window.innerHeight/1080);</script></section>",
        encoding="utf-8",
    )
    if audit_single_slide_step(pos_lossless_manifest, 1, dangling_slide, valid_bundle, slides_generated_in_current_step=1).get("status") != "FAIL":
        raise AssertionError("Expected dangling detail-trigger without payload to fail per-slide audit")


def _selftest_part_o_pre_background_recipe_rung1_grounding_and_outsider_blind_reader(
    tdir: Path,
    base_narrative: Dict[str, Any],
    base_mechanism: Dict[str, Any],
    valid_bundle: Dict[str, Any],
) -> None:
    manifest_o = tdir / "manifest_o_macro_onboarding.json"
    pv_bridge = {
        "pdf_omitted_background_gaps": [
            "原始论文默认读者熟知全球晶硅光伏高温熔硅能耗与刚性面积瓶颈，未铺垫涂布式钙钛矿产业定位",
            "原始论文首段直接切入甲脒铅碘相变能垒与旋转熵，缺少五层三明治发电原理与热力学权衡铺垫",
        ],
        "outside_pdf_onboarding_primer": (
            "晶硅太阳能板虽耐用但需上千度高温熔硅且单层效率近顶；钙钛矿靠百摄氏度溶液涂布成超薄膜，"
            "兼具叠层高效率潜力却卡在湿热易变黄短命。"
        ),
        "four_rung_funnel": {
            "rung1_macro_industry_stakes": (
                "晶硅光伏占全球 95% 以上装机但受限于 1400 °C 熔硅高能耗与刚性面积瓶颈，"
                "100 °C 溶液涂布钙钛矿开辟超薄叠层赛道却卡在户外湿热运行寿命"
            ),
            "rung2_canonical_working_principle": {
                "summary": "倒置五层钙钛矿器件受光照产生电子与空穴，沿两侧传输层能级台阶分流输出电压与光电流",
                "visual_schematic_plan": "硅基高温产线对比钙钛矿低温涂布产线双轨 SVG 图 + 五层三明治能级滑梯图",
            },
            "rung3_core_jargon_translations": [
                {
                    "term": "立方黑相与六方黄相",
                    "plain_analogy": "三维透气发电笼 vs 坍塌挤死的一维绝缘柱",
                    "physical_meaning": "共顶八面体提供三维载流子通道，共面六方相失去光伏活性",
                },
                {
                    "term": "准费米能级劈裂",
                    "plain_analogy": "水电站上下游蓄水池的最大水位落差",
                    "physical_meaning": "光照下电子与空穴化学势差决定开路电压热力学上限",
                },
            ],
            "rung4_prior_art_deadlock": "传统外源离子混掺虽辅助稳相却拉宽带隙损失光电流，且局部未掺杂微区触发多米诺坍塌",
        },
        "background_slide_indices": [2, 3, 4],
        "paper_claims_strictly_from_pdf": True,
    }
    pv_io_bus = {
        "evidence_ingest_ledger": [
            {
                "claim_id": "Claim_3PMPCl_Barrier",
                "quantitative_value": "3-PMPCl 将体相能垒提至 3.07 eV（4-PMPCl 为 2.75 eV），认证效率 27.6%",
                "source_artifact_or_figure_ref": "Science 2026 Fig. 1B-G",
            }
        ],
        "devil_reviewer_capsule": {
            "alternative_hypothesis_challenge": "为何间位氮 3-PMPCl 优于对位氮 4-PMPCl？",
            "control_evidence_rebuttal": "573 K 下 3-PMPCl 覆盖率保持更高且体相能垒更高。",
        },
        "output_artifact_targets": ["HTML_PPT"],
    }
    archetypes = ("hero_clean_suspense_cover", "dual_track_industrial_macro_svg", "split_left_fig_right_steps", "interactive_svg_sandbox_split")
    pv_slides = [
        {
            "station_id": "S_01",
            "title": "熵调控分子锁稳定纯相甲脒铅碘钙钛矿太阳能电池",
            "layout_archetype": archetypes[0],
            "is_background_slide": False,
            "required_visual_level": "V2",
        },
        {
            "station_id": "S_02",
            "title": "晶硅受限于高温熔硅能耗与刚性面积瓶颈，低温涂布钙钛矿卡在寿命",
            "layout_archetype": archetypes[1],
            "is_background_slide": True,
            "background_rung": 1,
            "required_visual_level": "V2",
        },
        {
            "station_id": "S_03",
            "title": "倒置五层光电三明治靠能级台阶分流载流子",
            "layout_archetype": archetypes[2],
            "is_background_slide": True,
            "background_rung": 2,
            "required_visual_level": "V2",
        },
        {
            "station_id": "S_04",
            "title": "传统混掺拉宽带隙且未掺杂微区触发多米诺坍塌",
            "layout_archetype": archetypes[3],
            "is_background_slide": True,
            "background_rung": 4,
            "required_visual_level": "V2",
        },
    ]
    init_o = init_storyboard_manifest(
        {
            "workflow_mode": "AUTONOMOUS_DUAL_EVOLVE",
            "require_beyond_pdf_background": True,
            "domain_background_bridge": pv_bridge,
            "universal_io_bus_capsule": pv_io_bus,
            "narrative_spec": base_narrative,
            "mechanism_spec": base_mechanism,
            "storyboard_slides": pv_slides,
        },
        manifest_o,
    )
    if init_o.get("status") != "PASS":
        raise AssertionError(f"Expected valid PV macro-onboarding storyboard to init cleanly: {init_o}")

    pv_bundle = {
        **valid_bundle,
        "required_acronyms": (),
        "slides": [
            {
                "title": "熵调控分子锁稳定纯相甲脒铅碘钙钛矿太阳能电池",
                "subtitle": "破解涂布式钙钛矿效率追平晶硅却室温变黄短命的悬念",
                "body": "左图 1a 展示核心冲突。",
                "visible_text": "涂布式钙钛矿光伏效率追平晶硅却室温易变黄失效",
                "notes_text": "",
                "defined_terms_visible": [],
                "inline_popover_count": 1,
            }
        ],
    }

    bad_cover_s01 = tdir / "bad_cover_3pmpcl_s01.html"
    bad_cover_s01.write_text(
        "<section class='slide' id='s01'><style>"
        "html,body{margin:0;width:100%;height:100%;overflow:hidden;}"
        "#s01{position:fixed;left:50%;top:50%;width:1920px;height:1080px;transform:translate(-50%,-50%) scale(1);}"
        "</style><h1 class='slide-title' style='font-size:58px;'>熵调控分子锁稳定纯相钙钛矿太阳能电池</h1>"
        "<svg viewBox='0 0 1600 600'><text font-size='34'>双端柔性分子锁 3-PMPCl：3-N吡啶锁骨架，哌嗪环放旋转</text></svg>"
        "<script>const s=Math.min(window.innerWidth/1920,window.innerHeight/1080);</script></section>",
        encoding="utf-8",
    )
    neg_cover = audit_single_slide_step(manifest_o, 1, bad_cover_s01, pv_bundle, slides_generated_in_current_step=1)
    if neg_cover.get("status") != "FAIL" or "D13_Narrative_Arc_Background_PriorArt_And_Foreshadowing_Guard" not in neg_cover.get("failed_gates", []):
        raise AssertionError(f"Expected Slide 01 leaking 3-PMPCl before background to fail D13: {neg_cover}")

    clean_cover_s01 = tdir / "clean_cover_s01.html"
    clean_cover_s01.write_text(
        "<section class='slide' id='s01'><style>"
        "html,body{margin:0;width:100%;height:100%;overflow:hidden;}"
        "#s01{position:fixed;left:50%;top:50%;width:1920px;height:1080px;transform:translate(-50%,-50%) scale(1);}"
        "</style><h1 class='slide-title' style='font-size:58px;'>熵调控分子锁稳定纯相钙钛矿太阳能电池</h1>"
        "<svg viewBox='0 0 1600 600'><text font-size='34'>低温涂布追平晶硅 → 室温易变黄失效 → 分子锁兼顾效率与寿命</text></svg>"
        "<script>const s=Math.min(window.innerWidth/1920,window.innerHeight/1080);</script></section>",
        encoding="utf-8",
    )
    pos_cover = audit_single_slide_step(manifest_o, 1, clean_cover_s01, pv_bundle, slides_generated_in_current_step=1)
    if pos_cover.get("status") != "PASS":
        raise AssertionError(f"Expected clean zero-jargon cover Slide 01 to pass: {pos_cover}")

    bad_rung1_s02 = tdir / "bad_rung1_bandjump_s02.html"
    bad_rung1_s02.write_text(
        "<section class='slide' id='s02'><style>"
        "html,body{margin:0;width:100%;height:100%;overflow:hidden;}"
        "#s02{position:fixed;left:50%;top:50%;width:1920px;height:1080px;transform:translate(-50%,-50%) scale(1);}"
        "</style><h1 class='slide-title' style='font-size:58px;'>单结晶硅逼近上限，钙钛矿向单结极限推进</h1>"
        "<svg viewBox='0 0 1600 600'><text font-size='34'>间接带隙 1.12 eV · 直接带隙 1.48 eV · S–Q 极限 33.7%</text></svg>"
        "<script>const s=Math.min(window.innerWidth/1920,window.innerHeight/1080);</script></section>",
        encoding="utf-8",
    )
    neg_rung1 = audit_single_slide_step(manifest_o, 2, bad_rung1_s02, pv_bundle, slides_generated_in_current_step=1)
    if neg_rung1.get("status") != "FAIL" or "D13_Narrative_Arc_Background_PriorArt_And_Foreshadowing_Guard" not in neg_rung1.get("failed_gates", []):
        raise AssertionError(f"Expected opening Rung 1 slide jumping into 间接带隙/直接带隙/S–Q 极限 to fail D13: {neg_rung1}")

    clean_rung1_s02 = tdir / "clean_rung1_macro_s02.html"
    clean_rung1_s02.write_text(
        "<section class='slide' id='s02'><style>"
        "html,body{margin:0;width:100%;height:100%;overflow:hidden;}"
        "#s02{position:fixed;left:50%;top:50%;width:1920px;height:1080px;transform:translate(-50%,-50%) scale(1);}"
        "</style><h1 class='slide-title' style='font-size:58px;'>晶硅受限于高温熔硅能耗与刚性面积瓶颈</h1>"
        "<svg viewBox='0 0 1600 600'><text font-size='34'>晶硅占 >95% 市场需 1400 °C 熔硅 · 100 °C 溶液涂布钙钛矿怕湿热退化</text></svg>"
        "<script>const s=Math.min(window.innerWidth/1920,window.innerHeight/1080);</script></section>",
        encoding="utf-8",
    )
    pos_rung1 = audit_single_slide_step(manifest_o, 2, clean_rung1_s02, pv_bundle, slides_generated_in_current_step=1)
    if pos_rung1.get("status") != "PASS":
        raise AssertionError(f"Expected plain-world PV manufacturing stakes Slide 02 to pass: {pos_rung1}")

    escaped_blind_doc = {
        "reviewer_isolation_mode": "READONLY_PNG_BLIND_SUBAGENT",
        "saw_source_pdf": False,
        "saw_storyboard_json": False,
        "saw_speaker_notes": False,
        "blind_prompt_sent": "仅根据所给单页渲染截图独立复述核心结论、次级模块可见连接桥与任何未铺垫的突兀概念。",
        "slide_reconstructions": [
            {
                "slide_id": "slide_01",
                "reconstructed_claim": "在晶界引入双端分子锁 3-PMPCl，利用刚性 3-N 吡啶与柔性哌嗪环阻断黄相坍塌。",
                "ambiguous_or_dangling_elements": [],
                "reconstructed_block_links": [],
            }
        ],
    }
    if verify_blind_reader_for_manifest(manifest_o, escaped_blind_doc).get("status") != "FAIL":
        raise AssertionError("Expected blind reader reconstructing 3-PMPCl on Slide 01 without macro onboarding attestation to fail")

    clean_outsider_blind_doc = {
        "reviewer_isolation_mode": "READONLY_PNG_BLIND_SUBAGENT",
        "saw_source_pdf": False,
        "saw_storyboard_json": False,
        "saw_speaker_notes": False,
        "opening_macro_background_established": True,
        "blind_prompt_sent": "仅根据所给单页渲染截图独立复述核心结论、次级模块可见连接桥，并检查门外汉是否遭遇未铺垫术语。",
        "slide_reconstructions": [
            {
                "slide_id": "slide_01",
                "reconstructed_claim": "低温涂布钙钛矿效率已追平晶硅却在室温易变黄短命，晶界分子锁兼顾认证效率与高温长寿命。",
                "ambiguous_or_dangling_elements": [],
                "outsider_onboarding_gaps": [],
                "reconstructed_block_links": [],
            },
            {
                "slide_id": "slide_02",
                "reconstructed_claim": "传统晶硅受限于上千度熔硅高能耗与刚性面积上限，低温溶液涂布钙钛矿开辟叠层路线但卡在湿热寿命。",
                "ambiguous_or_dangling_elements": [],
                "outsider_onboarding_gaps": [],
                "reconstructed_block_links": [],
            },
        ],
    }
    if verify_blind_reader_for_manifest(manifest_o, clean_outsider_blind_doc).get("status") != "PASS":
        raise AssertionError("Expected clean outsider-verified blind reader receipt to pass")


def _selftest_part_p_physical_fidelity_evolution_and_masked_blind_object(
    tdir: Path,
    base_narrative: Dict[str, Any],
    base_mechanism: Dict[str, Any],
    base_slides: List[Dict[str, Any]],
    valid_bundle: Dict[str, Any],
) -> None:
    manifest_p = tdir / "manifest_p_phys.json"
    init_storyboard_manifest(
        {
            "workflow_mode": "AUTONOMOUS_DUAL_EVOLVE",
            "narrative_spec": base_narrative,
            "mechanism_spec": base_mechanism,
            "storyboard_slides": base_slides,
        },
        manifest_p,
    )
    crude_s01 = tdir / "crude_stick_s01.html"
    crude_s01.write_text(
        "<section class='slide' id='s01'><style>"
        "html,body{margin:0;width:100%;height:100%;overflow:hidden;}"
        "#s01{position:fixed;left:50%;top:50%;width:1920px;height:1080px;transform:translate(-50%,-50%) scale(1);}"
        "</style><h1 class='slide-title' style='font-size:58px;'>磷光分子与金属界面耦合示意图</h1>"
        "<svg viewBox='0 0 980 740'><g><circle cx='155' cy='480' r='24'></circle>"
        "<line x1='155' y1='456' x2='128' y2='410'></line><line x1='155' y1='456' x2='188' y2='414'></line>"
        "<circle cx='205' cy='624' r='22'></circle><line x1='205' y1='602' x2='176' y2='562'></line></g></svg>"
        "<script>const s=Math.min(window.innerWidth/1920,window.innerHeight/1080);</script></section>",
        encoding="utf-8",
    )
    phys_bundle = {
        **valid_bundle,
        "visual_entity_manifest": [
            {
                "entity_id": "phosphor_molecule",
                "scale_class": "MOLECULE_SUPRAMOLECULE",
                "render_route": "RDKIT_ACS_VECTOR",
                "expected_class_keywords": ["molecule", "磷光", "aromatic", "配体"],
            }
        ],
    }
    neg_stick = audit_single_slide_step(manifest_p, 1, crude_s01, phys_bundle, slides_generated_in_current_step=1)
    if neg_stick.get("status") != "FAIL" or "D5_Anti_Emoji_FakeProgressBar_And_AIWatermark_Guard" not in neg_stick.get("failed_gates", []):
        raise AssertionError(f"Expected crude circle+line physical entity SVG to fail D5: {neg_stick}")

    good_evo_ledger = {
        "slide_id": "slide_01",
        "generations_completed": 2,
        "is_text_free_base": True,
        "has_vector_callout_overlay": True,
        "winner_id": "gen1_evo",
        "gen0_candidates": [
            {"id": "c1", "sha256": "1" * 32, "camera_topology": "ISOMETRIC_3D_CUTAWAY", "rendering_medium": "SUBSURFACE_3D", "prompt": "Isometric 3D cortical brain tissue cutaway showing multipolar pyramidal neurons and gold silicon probe tip wrapped in reactive astrocytes", "score": 37.5, "is_text_free": True},
            {"id": "c2", "sha256": "2" * 32, "camera_topology": "MACRO_TO_MICRO_ZOOM_LENS", "rendering_medium": "INK_CONTOUR_TEXTBOOK", "prompt": "Sagittal whole-head silhouette linked via circular microscope zoom lens to neural parenchyma and glial capsule interface", "score": 35.0, "is_text_free": True},
            {"id": "c3", "sha256": "3" * 32, "camera_topology": "SPLIT_CONTRAST_DIPTYCH", "rendering_medium": "MICROSCOPY_STAIN_EDITORIAL", "prompt": "Two-panel histological fluorescence diptych contrasting intact dendritic branches against fibrotic stellate scar encapsulation", "score": 36.2, "is_text_free": True},
            {"id": "c4", "sha256": "4" * 32, "camera_topology": "ORTHOGRAPHIC_CROSS_SECTION", "rendering_medium": "TECHNICAL_CAD_RENDER", "prompt": "Orthographic device cross-section depicting ionic hydration blockage outside shiny metallic microelectrode pad", "score": 36.8, "is_text_free": True},
        ],
        "evolved_candidates": [
            {"id": "gen1_evo", "generation": 1, "parent_candidate_id": "c1", "sha256": "9" * 32, "critique_and_edit_plan": "Increase neuron contrast against pink cortical walls and sharpen reactive astrocyte scar boundary around gold pad.", "score": 39.4, "is_text_free": True}
        ],
    }
    if verify_image_tournament_for_manifest(manifest_p, good_evo_ledger).get("status") != "PASS":
        raise AssertionError("Expected diverse Gen-0 + iterative Gen-1 evolutionary tournament to pass")

    good_masked_obj = {
        "reviewer_isolation_mode": "READONLY_PNG_BLIND_SUBAGENT",
        "saw_source_pdf": False,
        "saw_storyboard_json": False,
        "saw_speaker_notes": False,
        "visual_entity_manifest": phys_bundle["visual_entity_manifest"],
        "stage_a_masked_visual": {
            "stage_a_all_text_hidden": True,
            "text_masked_png_sha256": "a" * 32,
            "stage_a_blind_prompt": "Examine the pure text-free scientific graphic and describe every drawn physical or chemical entity.",
            "unrecognizable_crude_glyphs": [],
            "recognized_objects": [
                {
                    "visual_description": "Publication-grade 2D chemical structure drawing of conjugated aromatic heterocycles and cyclometalated complex ligands",
                    "blind_guessed_object": "2D chemical molecule of cyclometalated aromatic phosphor complex",
                    "recognition_confidence": "HIGH",
                    "craft_tier": "T2_SCIENTIFIC_STRUCTURAL_VECTOR",
                }
            ],
        },
        "stage_b_full_slide_check": {
            "full_slide_png_sha256": "b" * 32,
            "bitmap_pseudo_text_detected": False,
            "leader_line_misalignment_or_crossing": [],
        },
    }
    if verify_blind_object_recognition_for_manifest(manifest_p, good_masked_obj).get("status") != "PASS":
        raise AssertionError("Expected clean Stage A text-masked T2 chemical structure recognition to pass")


def _selftest_part_q_tutor_wittgenstein_deconstruct_7element_and_teach_on_miss(
    tdir: Path,
    base_narrative: Dict[str, Any],
    base_mechanism: Dict[str, Any],
    base_slides: List[Dict[str, Any]],
) -> None:
    manifest_q = tdir / "manifest_q_tutor.json"
    init_storyboard_manifest(
        {
            "workflow_mode": "TDD",
            "tdd_mode": True,
            "narrative_spec": base_narrative,
            "mechanism_spec": base_mechanism,
            "storyboard_slides": base_slides,
        },
        manifest_q,
    )
    hollow_cap = {
        "station_id": "Station_1.1",
        "core_blindspot_or_conflict": "为什么需要持续光子输入才能维持耗散组装？",
        "wittgenstein_ladder": "充气拱门比喻说明断电就塌掉放气，非常直观好懂",
        "human_orthogonal_insight": "指出基态必须对应散架释放态",
        "visual_modality": "V2_shaded_25d_cycle",
        "hidden_teleprompter_qa": "按 S 键展开玻尔兹曼分布与耗散态差别",
    }
    if record_tdd_station_capsule(manifest_q, 1, hollow_cap).get("status") != "FAIL":
        raise AssertionError("Expected hollow 1-sentence analogy ladder to fail record_tdd_station_capsule")

    miss_no_closure = {
        "station_id": "Station_1.1",
        "user_missed_or_uncertain": True,
        "core_blindspot_or_conflict": "为什么低能垒无法靠加大光强压住？",
        "wittgenstein_ladder": {
            "bridge_analogy": "漏水桶需进水才能稳住水位",
            "deconstruct_breakdown": "微观分子光激发受吸收截面与逆光切换限制，并非无上限水压",
            "rigorous_replacement": "f_PSS = k_photo / (k_photo + k_back + k_Δ)",
        },
        "human_orthogonal_insight": "用户答出基态放货但卡在能垒竞争权重",
        "visual_modality": "V2_shaded_25d_cycle",
        "hidden_teleprompter_qa": "按 S 键展开稳态方程",
    }
    if record_tdd_station_capsule(manifest_q, 1, miss_no_closure).get("status") != "FAIL":
        raise AssertionError("Expected missed TDD station without teach_on_miss_and_regrill_closure to fail")

    rubberstamp_miss = {
        **miss_no_closure,
        "teach_on_miss_and_regrill_closure": {
            "wittgenstein_teach_explanation": "水桶漏太快时即使开大水龙头依然蓄不满水位，需要适度能垒保住布居数。",
            "isomorphic_regrill_question": "讲到这里你明白了吗？",
        },
    }
    if record_tdd_station_capsule(manifest_q, 1, rubberstamp_miss).get("status") != "FAIL":
        raise AssertionError("Expected rubber-stamp '你明白了吗？' Teach-on-Miss closure to fail")

    incomplete_anatomy = {
        **miss_no_closure,
        "require_seven_element_anatomy": True,
        "seven_element_anatomy": {"principle_and_logic": "只写了第一条原理说明，缺少其余六要素"},
        "teach_on_miss_and_regrill_closure": {
            "wittgenstein_teach_explanation": "从漏水桶类比出发，拆掉宏观水压无限上限谬误，换上速率方程分母竞争。",
            "isomorphic_regrill_question": "若保持光强不变把温度从 15 度升至 75 度，稳态笼占比会如何变化？",
        },
    }
    if record_tdd_station_capsule(manifest_q, 1, incomplete_anatomy).get("status") != "FAIL":
        raise AssertionError("Expected incomplete seven_element_anatomy to fail when required")

    valid_full_cap = {
        **miss_no_closure,
        "require_seven_element_anatomy": True,
        "seven_element_anatomy": {
            "principle_and_logic": "利用光子激发绕开基态细致平衡，维持偏离玻尔兹曼分布的高能构象",
            "physical_picture": "从充气拱门过渡到双向光反应与一级热弛豫耦合的非平衡稳态环路",
            "mathematical_formulation": "f_PSS = k_photo / (k_photo + k_back + (k_B T / h) exp(-ΔG‡ / RT))",
            "scope_and_boundary": "受朗伯-比尔穿透深度与内滤效应限制，需小时级半衰期黄金能垒窗口",
            "pros_and_cons": "零物质废料毒化与高精度时空可控，但维持稳态存在持续光能耗散代价",
            "alternatives_comparison": "优于积累盐废料的化学刺激与暗态死锁的双稳态光开关体系",
            "concrete_evidence_or_implementation": "配合 288 K 恒温槽在线 385 nm 吸收平台与关灯一级衰减实测",
        },
        "teach_on_miss_and_regrill_closure": {
            "wittgenstein_teach_explanation": "拆掉宏观水压谬误后，用分母 k_Δ = (k_B T / h) exp(-ΔG‡ / RT) 解释温和光强下的热衰减上限。",
            "isomorphic_regrill_question": "若保持 LED 光强不变，把溶液从 15 度升温到 75 度，稳态成笼分率会如何变动？",
        },
    }
    if record_tdd_station_capsule(manifest_q, 1, valid_full_cap).get("status") != "PASS":
        raise AssertionError("Expected complete 3-step Wittgenstein + 7-Element + Teach-on-Miss capsule to pass")


def _selftest_part_r_dual_pole_anti_coined_jargon_and_anti_sloganese(
    tdir: Path,
    base_narrative: Dict[str, Any],
    base_mechanism: Dict[str, Any],
    base_slides: List[Dict[str, Any]],
    valid_bundle: Dict[str, Any],
) -> None:
    manifest_r = tdir / "manifest_r_dual_pole.json"
    init_storyboard_manifest(
        {
            "workflow_mode": "AUTONOMOUS_DUAL_EVOLVE",
            "narrative_spec": base_narrative,
            "mechanism_spec": base_mechanism,
            "storyboard_slides": base_slides[:1],
        },
        manifest_r,
    )
    pole1_html = tdir / "bad_pole1_coined_ism.html"
    pole1_html.write_text(
        "<section class='slide' id='s01'><style>"
        "html,body{margin:0;width:100%;height:100%;overflow:hidden;}"
        "#s01{position:fixed;left:50%;top:50%;width:1920px;height:1080px;transform:translate(-50%,-50%) scale(1);}"
        "</style><h1 class='slide-title' style='font-size:56px;'>痕量卤代借 1 eV 漏斗收割整笼能量，证伪唯光吸收截面论</h1>"
        "<script>const s=Math.min(window.innerWidth/1920,window.innerHeight/1080);</script></section>",
        encoding="utf-8",
    )
    neg_p1 = audit_single_slide_step(manifest_r, 1, pole1_html, valid_bundle, slides_generated_in_current_step=1)
    if neg_p1.get("status") != "FAIL" or "D3_Natural_Academic_Copywriting_No_AI_MetaTone" not in neg_p1.get("failed_gates", []):
        raise AssertionError(f"Expected coined '-ism' + predatory metaphor slide to fail D3: {neg_p1}")

    pole2_html = tdir / "bad_pole2_sloganese.html"
    pole2_html.write_text(
        "<section class='slide' id='s01'><style>"
        "html,body{margin:0;width:100%;height:100%;overflow:hidden;}"
        "#s01{position:fixed;left:50%;top:50%;width:1920px;height:1080px;transform:translate(-50%,-50%) scale(1);}"
        "</style><h1 class='slide-title' style='font-size:56px;'>不靠多吸光也能提灵敏度：单配体聚能断键</h1>"
        "<button type='button' class='detail-trigger' data-detail-id='p1' style='font-size:32px;'>+ 为什么吸光几乎不变</button>"
        "<template data-detail-id='p1'>92 eV 光吸收截面定量核算证明晶胞吸收增量小于百分之二。</template>"
        "<script>const s=Math.min(window.innerWidth/1920,window.innerHeight/1080);</script></section>",
        encoding="utf-8",
    )
    neg_p2 = audit_single_slide_step(manifest_r, 1, pole2_html, valid_bundle, slides_generated_in_current_step=1)
    if neg_p2.get("status") != "FAIL" or "D3_Natural_Academic_Copywriting_No_AI_MetaTone" not in neg_p2.get("failed_gates", []):
        raise AssertionError(f"Expected '不靠X也能Y' slogan + clickbait trigger slide to fail D3: {neg_p2}")

    calm_html = tdir / "good_calm_academic.html"
    calm_html.write_text(
        "<section class='slide' id='s01'><style>"
        "html,body{margin:0;width:100%;height:100%;overflow:hidden;}"
        "#s01{position:fixed;left:50%;top:50%;width:1920px;height:1080px;transform:translate(-50%,-50%) scale(1);}"
        "</style><h1 class='slide-title' style='font-size:56px;'>电激发下 75% 三重态决定必须发展 PHOLED（磷光有机发光二极管）</h1>"
        "<button type='button' class='detail-trigger' data-detail-id='p1' style='font-size:32px;'>+ 自旋统计配分推导</button>"
        "<template data-detail-id='p1'>非相关电子空穴对复合生成单重态与三重态比例严格遵循一比三自旋简并统计。</template>"
        "<script>const s=Math.min(window.innerWidth/1920,window.innerHeight/1080);</script></section>",
        encoding="utf-8",
    )
    pos_calm = audit_single_slide_step(manifest_r, 1, calm_html, valid_bundle, slides_generated_in_current_step=1)
    if pos_calm.get("status") != "PASS":
        raise AssertionError(f"Expected calm declarative academic slide to pass: {pos_calm}")


def run_selftest() -> Dict[str, Any]:
    """Run all 18 self-test checks across TDD, GRILL, AUTONOMOUS_DUAL_EVOLVE, Onion Peeling, Universal I/O Bus, Beyond-PDF Background Bridge, Unread-PDF Intent/JIT Emphasis, Zero Slide-Count MCQ, Zero AI Self-Scaffolding Labels, and >=18px SVG / >=22px HD Body / Non-Hollow Card Guards."""
    with tempfile.TemporaryDirectory(prefix="awf_html_ppt_test_") as tmp:
        tdir = Path(tmp)
        base_narrative = {
            "has_macro_background_and_core_def": True,
            "has_degradation_or_bottleneck_mechanism": True,
            "has_prior_art_and_ceiling": True,
            "has_clue_free_blind_guessing": False,
            "has_foreshadowing_and_callback": True,
        }
        base_mechanism = {
            "causal_why_links_explained": {"why_a": True, "why_b": True, "why_c": True},
            "has_dedicated_device_or_assembly_slide": True,
            "has_real_molecular_chemical_structures": True,
            "has_controlled_pair_comparison_and_baseline_note": True,
            "has_multi_objective_tradeoff_explanation": True,
            "scientific_or_structural_errors": [],
        }
        base_slides = [
            {"station_id": "Station_1.1", "title": "电激发自旋统计决定磷光 PHOLED 路线", "layout_archetype": "top_banner_dual_cards"},
            {"station_id": "Station_1.2", "title": "极化激元反交叉耦合加速辐射衰减", "layout_archetype": "split_left_fig_right_steps"},
        ]
        s1_path = tdir / "slide_01.html"
        s2_path = tdir / "slide_02.html"
        valid_html = (
            "<!DOCTYPE html><html><head><script src='katex.min.js'></script></head>"
            "<body><section class='slide'><h2>电激发下 75% 三重态决定必须发展 PHOLED</h2>"
            "<p>左图 1a 展示 PHOLED（磷光有机发光二极管）自旋统计。</p></section></body></html>"
        )
        s1_path.write_text(valid_html, encoding="utf-8")
        s2_path.write_text(valid_html, encoding="utf-8")
        valid_bundle = {
            "grid_specs": [{"slide": 1, "columns": 2, "item_count": 2}],
            "slides": [{
                "title": "电激发下 75% 三重态决定必须发展 PHOLED",
                "subtitle": "重原子旋轨耦合实现内量子效率突破",
                "body": "左图 1a 展示自旋统计。",
                "visible_text": "PHOLED（磷光有机发光二极管）",
                "notes_text": "",
                "defined_terms_visible": ["PHOLED"],
                "inline_popover_count": 1,
            }],
            "required_acronyms": ("PHOLED",),
            "figure_metadata": [{"src": "fig1a.png", "is_ai_decorative_wallpaper": False}],
            "boxes": [
                {"id": "hdr", "parent_id": "root", "x": 80, "y": 50, "w": 1760, "h": 110},
                {"id": "left", "parent_id": "root", "x": 80, "y": 200, "w": 850, "h": 760},
                {"id": "right", "parent_id": "root", "x": 990, "y": 200, "w": 850, "h": 760},
            ],
            "placements": [{"id": "fig1a", "img_w": 1200, "img_h": 900, "slot_w": 850, "slot_h": 640, "panel_rows": 1}],
            "color_pairs": [{"id": "body", "fg_rgb": (20, 28, 45), "bg_rgb": (248, 250, 252), "is_large_title": False}],
        }

        _selftest_part_a_tdd(tdir, base_narrative, base_mechanism, base_slides, s1_path, s2_path, valid_bundle)
        grill_cap_1 = _selftest_part_b_and_c_grill_and_autonomous(
            tdir, base_narrative, base_mechanism, base_slides, s1_path, valid_bundle
        )
        elastic_bp = _selftest_part_d_and_e_blueprint_and_elastic(
            tdir, base_narrative, base_mechanism, base_slides, s1_path, s2_path, valid_bundle, grill_cap_1
        )
        _selftest_part_f_and_g_onion_and_io_bus(
            tdir, base_narrative, base_mechanism, base_slides, s1_path, s2_path, valid_bundle, grill_cap_1, elastic_bp
        )
        _selftest_part_h_background_bridge(
            tdir, base_narrative, base_mechanism, s1_path, valid_bundle, grill_cap_1
        )
        _selftest_part_i_redundancy_and_viewport_autofit(
            tdir, base_narrative, base_mechanism, base_slides, valid_bundle
        )
        _selftest_part_j_inline_svg_font_floor_and_char_overload(
            tdir, base_narrative, base_mechanism, base_slides, valid_bundle
        )
        _selftest_part_k_unread_pdf_intent_triage_and_jit_grill_focus(
            tdir, base_narrative, base_mechanism, base_slides
        )
        _selftest_part_l_ai_scaffolding_and_hollow_card_typography(
            tdir, base_narrative, base_mechanism, base_slides, valid_bundle
        )
        _selftest_part_m_semantic_coherence_and_anti_collusion_blind_reader(
            tdir, base_narrative, base_mechanism, base_slides, valid_bundle
        )
        _selftest_part_n_ultra_clean_large_type_and_lossless_popovers(
            tdir, base_narrative, base_mechanism, base_slides, valid_bundle
        )
        _selftest_part_o_pre_background_recipe_rung1_grounding_and_outsider_blind_reader(
            tdir, base_narrative, base_mechanism, valid_bundle
        )
        _selftest_part_p_physical_fidelity_evolution_and_masked_blind_object(
            tdir, base_narrative, base_mechanism, base_slides, valid_bundle
        )
        _selftest_part_q_tutor_wittgenstein_deconstruct_7element_and_teach_on_miss(
            tdir, base_narrative, base_mechanism, base_slides
        )
        _selftest_part_r_dual_pole_anti_coined_jargon_and_anti_sloganese(
            tdir, base_narrative, base_mechanism, base_slides, valid_bundle
        )

    checks_passed = [
        "Block_Out_Of_Order_Slide_Leapfrogging_HopDistance_2",
        "Block_MultiSlide_Batch_Generation_Per_Step_GT_1",
        "Mode1_TDD_Block_Without_Capsule_And_Pass_With_Tutor_Station_Capsule",
        "Block_Next_Slide_While_Awaiting_Approval_Gate",
        "Block_Deck_Assembly_With_Unverified_Slide",
        "Mode2_GRILL_Block_Without_Capsule_And_Pass_With_Grill_TeachOnMiss_Regrill_Capsule",
        "Mode3_AUTONOMOUS_HeadDown_Build_And_Block_Incomplete_DualEvolution_Receipt",
        "Mode3_AUTONOMOUS_Pass_PostReview_PPT_Patch_And_AWF_Dual_Evolution_Receipt",
        "Stage0_Macro_GDD_Global_Deck_Blueprint_And_V3_Animation_Enforcement",
        "MidStream_Elastic_Slide_Split_Merge_And_JIT_V3_Animation_Promotion",
        "Hierarchical_Onion_Peeling_Layer0_CoarseFrame_To_Layer1_TrunkSubFrame_To_LeafSlide",
        "Universal_IO_Onion_Bus_EvidenceIngest_DevilReviewer_And_CrossArtifact_SciWord_FigPPT_Sync",
        "BeyondPDF_4Rung_Background_Bridge_And_FoundationFirst_Grill_TDD_Enforcement",
        "Block_Redundant_SVG_SideCard_Echo_And_Unfitted_FixedCanvas_Viewport",
        "Block_Inline_SVG_Font_LT_18px_ViewBox_Spoof_And_SingleSlide_Char_Overload",
        "UnreadPDF_IntentFirst_ValueTriage_Block_BlindModuleQuiz_And_JIT_Grill_Focus_Promotion",
        "Eliminate_SlideCount_MCQ_Block_FixedPageQuiz_And_Enforce_LogicDriven_Growth",
        "Block_AI_SelfScaffolding_Labels_Sub18px_HTML_And_Hollow_20px_HD_TextCards",
        "Block_Orphan_Bottom_NounCard_Strips_And_Enforce_AntiCollusion_Blind_Reader",
        "Block_Over260Char_Sub32px_Sub42px_DanglingPopover_And_Enforce_Lossless_Split_Popover_Ledger",
        "Block_PreBackground_PaperRecipe_Leak_Rung1_FormalismJump_And_Enforce_Outsider_BlindReader_Onboarding",
        "Enforce_5Scale_PhysicalEntity_Fidelity_Orthogonal_Image_Evolution_And_TwoStage_Masked_BlindObject_Recognition",
        "Tutor_Wittgenstein_3Step_Deconstruct_7Element_And_TeachOnMiss_Enforcement",
        "Block_DualPole_CoinedIsm_And_PopScience_Sloganese_Copywriting",
    ]
    if len(checks_passed) != EXPECTED_SELFTEST_CHECKS or not grill_cap_1 or not elastic_bp:
        raise AssertionError(f"Self-test orchestrator failed to complete all {EXPECTED_SELFTEST_CHECKS} checks")
    return {
        "status": "PASS",
        "selftest": "AWF_HTML_PPT_V3_MacroToMicro_TriMode_TDD_Grill_And_AutonomousDualEvolve",
        "checks_passed": checks_passed,
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="AWF HTML-PPT V3 Tri-Mode Single-Slide Gatekeeper")
    parser.add_argument("--self-test", action="store_true", help="Run Tri-Mode (TDD / GRILL / AUTONOMOUS_DUAL_EVOLVE) self-test")
    parser.add_argument("--init-storyboard", type=str, default="", help="Path to storyboard.json")
    parser.add_argument("--record-background-bridge", type=str, default="", help="Path to Role 0 domain_background_bridge JSON")
    parser.add_argument("--peel-onion-trunk", type=str, default="", help="Path to Onion Layer 1 trunk sub-framework peel JSON")
    parser.add_argument("--mutate-storyboard", type=str, default="", help="Path to mid-stream storyboard mutation JSON")
    parser.add_argument("--record-cross-artifact-unit", type=str, default="", help="Path to cross-artifact (SCI_WORD / FIG_PPTX) unit receipt JSON")
    parser.add_argument("--manifest", type=str, default="slide_manifest.json", help="Path to slide_manifest.json")
    parser.add_argument("--record-tdd-capsule", type=str, default="", help="Path to Mode 1 TDD station capsule JSON")
    parser.add_argument("--record-grill-capsule", type=str, default="", help="Path to Mode 2 GRILL station capsule JSON")
    parser.add_argument("--apply-feedback-dual-upgrade", type=str, default="", help="Path to Mode 3 dual-evolution upgrade JSON payload")
    parser.add_argument("--slide-index", type=int, default=1, help="1-based slide/station index")
    parser.add_argument("--human-approve-slide", type=int, default=0, help="1-based slide index to approve by human")
    parser.add_argument("--human-note", type=str, default="Approved by human director", help="Human approval note")
    parser.add_argument("--verify-blind-reader", type=str, default="", help="Path to anti-collusion blind_reader_audit JSON")
    parser.add_argument("--verify-image-tournament", type=str, default="", help="Path to evolutionary image tournament ledger JSON")
    parser.add_argument("--verify-blind-object-recognition", type=str, default="", help="Path to two-stage text-masked blind object recognition JSON")
    parser.add_argument("--check-disk-pixels", action="store_true", help="Check Gen-0/Gen-1 PNG files on disk for RGB diversity")
    parser.add_argument("--assemble-deck", action="store_true", help="Assemble verified slides into deck")
    parser.add_argument("--output", type=str, default="deck.html", help="Output deck HTML path")
    parser.add_argument("--verify-deck-evidence", default="", help="Verify a final deck with complete rubric and signed review evidence")
    parser.add_argument("--review-bundle", default="", help="Complete 18-gate bundle JSON")
    parser.add_argument("--evidence-manifest", default="", help="Signed renderer/reviewer manifest JSON")
    parser.add_argument("--trust-policy", default="", help="Runner-owned public-key trust policy; never supplied by the deck")
    parser.add_argument("--review-run-id", default="", help="Expected run ID issued by the runner")
    parser.add_argument("--review-targets", default="", help="JSON mapping screenshot artifact IDs to the assembled deck path")
    args = parser.parse_args(argv)

    if args.verify_deck_evidence:
        from design_review_adapter import verify_deck_evidence
        try:
            context = {"manifest_path": args.evidence_manifest, "trust_policy_path": args.trust_policy,
                       "run_id": args.review_run_id, "expected_artifacts": json.loads(Path(args.review_targets).read_text(encoding="utf-8"))}
            rep = verify_deck_evidence(_load_design_ag_module(), args.verify_deck_evidence, args.review_bundle, context)
        except (ValueError, KeyError, TypeError, OSError) as error:
            rep = {"status": "FAIL", "reason": str(error)}
        print(json.dumps(rep, indent=2, ensure_ascii=False))
        return 0 if rep["status"] == "PASS" else 1

    if args.self_test:
        if not __debug__:
            raise RuntimeError("Self-tests require assertions; remove Python -O")
        rep = run_selftest()
        print(json.dumps(rep, indent=2, ensure_ascii=False))
        return 0 if rep.get("status") == "PASS" else 1

    if args.init_storyboard:
        sb_doc = json.loads(Path(args.init_storyboard).read_text(encoding="utf-8"))
        rep = init_storyboard_manifest(sb_doc, Path(args.manifest))
        print(json.dumps(rep, indent=2, ensure_ascii=False))
        return 0 if rep.get("status") == "PASS" else 1

    if args.record_background_bridge:
        bg_doc = json.loads(Path(args.record_background_bridge).read_text(encoding="utf-8"))
        rep = record_domain_background_bridge(Path(args.manifest), bg_doc)
        print(json.dumps(rep, indent=2, ensure_ascii=False))
        return 0 if rep.get("status") == "PASS" else 1

    if args.peel_onion_trunk:
        peel_doc = json.loads(Path(args.peel_onion_trunk).read_text(encoding="utf-8"))
        rep = peel_onion_trunk_subframe(Path(args.manifest), peel_doc)
        print(json.dumps(rep, indent=2, ensure_ascii=False))
        return 0 if rep.get("status") == "PASS" else 1

    if args.mutate_storyboard:
        mut_doc = json.loads(Path(args.mutate_storyboard).read_text(encoding="utf-8"))
        rep = mutate_storyboard_manifest(Path(args.manifest), mut_doc)
        print(json.dumps(rep, indent=2, ensure_ascii=False))
        return 0 if rep.get("status") == "PASS" else 1

    if args.record_cross_artifact_unit:
        unit_doc = json.loads(Path(args.record_cross_artifact_unit).read_text(encoding="utf-8"))
        rep = record_cross_artifact_unit_receipt(Path(args.manifest), unit_doc)
        print(json.dumps(rep, indent=2, ensure_ascii=False))
        return 0 if rep.get("status") == "PASS" else 1

    if args.record_tdd_capsule:
        cap_doc = json.loads(Path(args.record_tdd_capsule).read_text(encoding="utf-8"))
        rep = record_tdd_station_capsule(Path(args.manifest), args.slide_index, cap_doc)
        print(json.dumps(rep, indent=2, ensure_ascii=False))
        return 0 if rep.get("status") == "PASS" else 1

    if args.record_grill_capsule:
        cap_doc = json.loads(Path(args.record_grill_capsule).read_text(encoding="utf-8"))
        rep = record_grill_station_capsule(Path(args.manifest), args.slide_index, cap_doc)
        print(json.dumps(rep, indent=2, ensure_ascii=False))
        return 0 if rep.get("status") == "PASS" else 1

    if args.apply_feedback_dual_upgrade:
        payload = json.loads(Path(args.apply_feedback_dual_upgrade).read_text(encoding="utf-8"))
        rep = apply_human_feedback_dual_upgrade(
            Path(args.manifest),
            payload.get("feedback_receipt", {}),
            int(payload.get("patched_slide_index", args.slide_index)),
            Path(str(payload.get("patched_html_path", ""))),
            payload.get("patched_bundle", {}),
        )
        print(json.dumps(rep, indent=2, ensure_ascii=False))
        return 0 if rep.get("status") == "PASS" else 1

    if args.human_approve_slide > 0:
        rep = approve_slide_by_human(Path(args.manifest), args.human_approve_slide, args.human_note)
        print(json.dumps(rep, indent=2, ensure_ascii=False))
        return 0 if rep.get("status") == "PASS" else 1

    if args.verify_blind_reader:
        blind_doc = json.loads(Path(args.verify_blind_reader).read_text(encoding="utf-8"))
        rep = verify_blind_reader_for_manifest(Path(args.manifest), blind_doc)
        print(json.dumps(rep, indent=2, ensure_ascii=False))
        return 0 if rep.get("status") == "PASS" else 1

    if args.verify_image_tournament:
        t_doc = json.loads(Path(args.verify_image_tournament).read_text(encoding="utf-8"))
        rep = verify_image_tournament_for_manifest(
            Path(args.manifest),
            t_doc,
            check_disk_pixels=bool(args.check_disk_pixels),
        )
        print(json.dumps(rep, indent=2, ensure_ascii=False))
        return 0 if rep.get("status") == "PASS" else 1

    if args.verify_blind_object_recognition:
        obj_doc = json.loads(Path(args.verify_blind_object_recognition).read_text(encoding="utf-8"))
        rep = verify_blind_object_recognition_for_manifest(Path(args.manifest), obj_doc)
        print(json.dumps(rep, indent=2, ensure_ascii=False))
        return 0 if rep.get("status") == "PASS" else 1

    if args.assemble_deck:
        rep = assemble_verified_deck(Path(args.manifest), Path(args.output))
        print(json.dumps(rep, indent=2, ensure_ascii=False))
        return 0 if rep.get("status") == "PASS" else 1

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
