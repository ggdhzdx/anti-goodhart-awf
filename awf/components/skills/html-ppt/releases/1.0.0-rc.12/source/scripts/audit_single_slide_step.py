#!/usr/bin/env python3
"""
AWF HTML-PPT V3 Tri-Mode Single-Slide Atomic Micro-Step Gatekeeper (`skill.html-ppt@1.0.0-rc.6`).

Physically enforces:
1. Strictly 1 Slide Per Step (`max_slides_generated_per_step == 1`);
2. 1-Hop Slide Topological Lock (`unverified_slide_hop_distance == 1` via `slide_manifest.json`);
3. Tri-Mode Execution Architecture:
   - Mode 1 (`TDD` / Tutor-Driven Design): 1 Tutor Station == 1 TDD Capsule (`record_tdd_station_capsule`) == 1 Slide;
   - Mode 2 (`GRILL` / Grill-Driven Design): Agent quizzes first -> Teach-on-Miss & Re-grill when user doesn't know -> 1 Grill Capsule (`record_grill_station_capsule`) == 1 Slide;
   - Mode 3 (`AUTONOMOUS_DUAL_EVOLVE` / Head-Down Build + Post-Review Dual-Evolution): Head-down autonomous 1-slide-per-step deck generation (`require_human_approval=False`), followed by `apply_human_feedback_dual_upgrade` which simultaneously patches/re-audits the PPT slide(s) AND records/verifies the AWF HTML-PPT / DesignAG gate + negative canary upgrade receipt;
4. Optional Human-in-the-Loop Sign-off Gate (`require_human_approval` + `approve_slide_by_human`);
5. Full 18-Gate DesignAG audit (`skill.design-anti-goodhart@1.0.0-rc.4`) + SHA-256 lock before assembly.
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


def _resolve_design_ag_scripts_dir() -> Path:
    candidates = [
        Path("/home/zc/agent_workflows/components/skills/design-anti-goodhart/releases/1.0.0-rc.10/source/scripts"),
        Path(r"Z:\agent_workflows\components\skills\design-anti-goodhart\releases\1.0.0-rc.10\source\scripts"),
        Path("/home/zc/agent_workflows/components/skills/design-anti-goodhart/releases/1.0.0-rc.9/source/scripts"),
        Path(r"Z:\agent_workflows\components\skills\design-anti-goodhart\releases\1.0.0-rc.9\source\scripts"),
        Path(__file__).resolve().parents[2] / "design-anti-goodhart" / "scripts",
    ]
    for c in candidates:
        if c.is_dir():
            return c
    return candidates[0]


def _load_design_ag_module() -> Any:
    scripts_dir = _resolve_design_ag_scripts_dir()
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    import awf_design_anti_goodhart_gates as dag  # type: ignore

    return dag


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

    d13 = dag.verify_narrative_arc_and_foreshadowing(storyboard_doc.get("narrative_spec", {}))
    d14 = dag.verify_causal_why_chain_and_tradeoffs(storyboard_doc.get("mechanism_spec", {}))
    d16 = dag.verify_storyboard_microstep_and_layout_diversity(
        slides_spec,
        max_slides_generated_per_step=1,
        unverified_slide_hop_distance=1,
        global_deck_blueprint=global_blueprint,
        onion_peeling_capsule=onion_capsule,
        universal_io_bus_capsule=io_bus_capsule,
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

    slide_entries: List[Dict[str, Any]] = []
    for idx, s in enumerate(slides_spec, start=1):
        station_id = str(s.get("station_id", f"Station_1.{idx}"))
        is_v3_focus = (idx in v3_designated_set) or str(s.get("required_visual_level", "")).upper().startswith("V3")
        slide_entries.append({
            "slide_index": idx,
            "slide_id": f"slide_{idx:02d}",
            "station_id": station_id,
            "flow_module": str(s.get("flow_module", "")),
            "title": str(s.get("title", f"Slide {idx}")),
            "layout_archetype": str(s.get("layout_archetype", "split_left_fig_right_guided_steps")),
            "required_visual_level": "V3" if is_v3_focus else str(s.get("required_visual_level", "V2")),
            "designated_v3_animation": is_v3_focus,
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
        "schema_version": 8,
        "workflow_mode": raw_mode,
        "max_slides_generated_per_step": 1,
        "tdd_mode": tdd_mode,
        "grill_mode": grill_mode,
        "autonomous_dual_evolve_mode": autonomous_dual_evolve_mode,
        "require_human_approval": require_human_approval,
        "global_deck_blueprint": global_blueprint,
        "onion_peeling_capsule": onion_capsule,
        "universal_io_bus_capsule": io_bus_capsule,
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
        slide_index = int(unit_receipt.get("slide_index", 1))
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
            new_entry = {
                "slide_index": new_idx,
                "slide_id": f"slide_{new_idx:02d}",
                "station_id": str(node.get("node_id", f"Station_{target_tid}_{new_idx}")),
                "flow_module": target_tid,
                "title": str(node.get("title", f"{target_tid} Slide {new_idx}")),
                "layout_archetype": str(node.get("layout_archetype", "interactive_svg_sandbox_split")),
                "required_visual_level": "V3" if is_v3 else str(node.get("required_visual_level", "V2")),
                "designated_v3_animation": is_v3,
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
        new_entry = {
            "slide_index": insert_pos + 1,
            "slide_id": f"slide_{insert_pos + 1:02d}",
            "station_id": str(new_slide_spec.get("station_id", f"Station_1.{insert_pos + 1}_flow")),
            "flow_module": str(new_slide_spec.get("flow_module", "")),
            "title": str(new_slide_spec.get("title", f"Flow Slide {insert_pos + 1}")),
            "layout_archetype": str(new_slide_spec.get("layout_archetype", "interactive_svg_sandbox_split")),
            "required_visual_level": "V3" if is_v3 else str(new_slide_spec.get("required_visual_level", "V2")),
            "designated_v3_animation": is_v3,
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

    tdd_check = dag.verify_tdd_station_capsule_completeness(tdd_capsule)
    if not tdd_check.get("passed"):
        return {
            "status": "FAIL",
            "slide_index": slide_index,
            "reason": "TDD Station Cognitive Capsule incomplete",
            "tdd_check": tdd_check,
        }

    target_entry = slides_list[slide_index - 1]
    target_entry["tdd_station_capsule"] = tdd_capsule
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

    grill_check = dag.verify_grill_station_capsule_completeness(grill_capsule)
    if not grill_check.get("passed"):
        return {
            "status": "FAIL",
            "slide_index": slide_index,
            "reason": "Grill-Driven Design (GDD) Capsule incomplete",
            "grill_check": grill_check,
        }

    target_entry = slides_list[slide_index - 1]
    target_entry["gdd_grill_capsule"] = grill_capsule
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
    gate_checks = [
        dag.scan_html_for_unrendered_latex_leak(html_text),
        dag.audit_html_tag_balance_and_grid_orphans(html_text, slide_bundle.get("grid_specs")),
        dag.audit_copywriting_naturalness_and_ai_tone(slide_bundle.get("slides", [])),
        dag.audit_acronym_definitions_and_popovers(
            slide_bundle.get("slides", []),
            slide_bundle.get("required_acronyms", ("PHOLED", "TPA", "TTA")),
        ),
        dag.audit_emojis_fake_bars_and_watermarks(html_text, slide_bundle.get("figure_metadata")),
        dag.verify_bounding_boxes_zero_overlap_and_clipping(slide_bundle.get("boxes", [])),
        dag.verify_canvas_whitespace_and_center_of_mass(slide_bundle.get("boxes", [])),
        dag.verify_image_aspect_ratio_and_slot_utilization(slide_bundle.get("placements", [])),
        dag.verify_wcag_contrast_and_visual_restraint(
            slide_bundle.get("color_pairs", []),
            bool(slide_bundle.get("has_cyberpunk_neon_glow", False)),
            True,
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
            "message": "DesignAG 18-gate machine audit passed; awaiting human sign-off (--human-approve-slide) to unlock next slide.",
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
            "reason": "Patched slide failed DesignAG 18-gate re-audit",
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

    assembled_html = (
        "<!DOCTYPE html>\n<html lang='zh-CN'>\n<head>\n<meta charset='utf-8'/>\n"
        "<title>AWF DesignAG Verified HTML-PPT Deck</title>\n"
        "<script src='katex.min.js'></script>\n</head>\n<body>\n"
        + "\n<!-- SLIDE_BOUNDARY -->\n".join(slide_bodies)
        + "\n</body>\n</html>\n"
    )
    output_deck_path.parent.mkdir(parents=True, exist_ok=True)
    output_deck_path.write_text(assembled_html, encoding="utf-8")
    return {
        "status": "PASS",
        "total_slides_assembled": len(slide_bodies),
        "output_deck_path": str(output_deck_path),
        "deck_sha256": _sha256_file(output_deck_path),
    }


def run_selftest() -> Dict[str, Any]:
    """
    Self-test verifying 8 invariants across all 3 execution modes (`TDD`, `GRILL`, `AUTONOMOUS_DUAL_EVOLVE`):
    1. Auditing `slide_02` before `slide_01` is `PASS` (`unverified_slide_hop_distance=2`) is blocked;
    2. Submitting >1 slide in a single step (`slides_generated_in_current_step=2`) is blocked;
    3. Mode 1 (`TDD`): Auditing `slide_01` without a valid `tdd_station_capsule` is blocked;
    4. Human-in-the-Loop (`require_human_approval=True`): Machine audit sets `AWAITING_HUMAN_APPROVAL`
       and blocks `slide_02` until `approve_slide_by_human` is executed;
    5. Assembling deck before all slides pass is blocked, and passes after all slides pass;
    6. Mode 2 (`GRILL` / Grill-Driven Design): Auditing `slide_01` without `gdd_grill_capsule` is blocked,
       and passes after recording a complete Grill-First + Teach-on-Miss + Re-grill capsule;
    7. Mode 3 (`AUTONOMOUS_DUAL_EVOLVE`): Head-down autonomous 1-slide-per-step build succeeds without
       blocking for human approval, and rejects an incomplete `dual_evolution_feedback_receipt`;
    8. Mode 3 (`AUTONOMOUS_DUAL_EVOLVE`): Full post-review `apply_human_feedback_dual_upgrade` patches
       the PPT slide AND records the AWF HTML-PPT / DesignAG gate + canary upgrade receipt.
    """
    with tempfile.TemporaryDirectory(prefix="awf_html_ppt_test_") as tmp:
        tdir = Path(tmp)
        manifest_path = tdir / "slide_manifest.json"
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

        # --- PART A: Mode 1 (`TDD` + Human Sign-off Gate) ---
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

        # Check 1: Out-of-order jump blocked
        neg_hop = audit_single_slide_step(manifest_path, 2, s2_path, valid_bundle, slides_generated_in_current_step=1)
        if neg_hop.get("status") != "FAIL":
            raise AssertionError(f"Expected 1-hop violation: {neg_hop}")

        # Check 2: Batch >1 slide blocked
        neg_batch = audit_single_slide_step(manifest_path, 1, s1_path, valid_bundle, slides_generated_in_current_step=2)
        if neg_batch.get("status") != "FAIL":
            raise AssertionError(f"Expected single-slide violation: {neg_batch}")

        # Check 3: Mode 1 (`TDD`) without capsule blocked
        neg_no_tdd = audit_single_slide_step(manifest_path, 1, s1_path, valid_bundle, slides_generated_in_current_step=1)
        if neg_no_tdd.get("status") != "FAIL":
            raise AssertionError(f"Expected TDD violation without capsule: {neg_no_tdd}")

        capsule_1 = {
            "station_id": "Station_1.1",
            "core_blindspot_or_conflict": "为什么电激发下 75% 三重态自旋统计决定了必须发展磷光 PHOLED？",
            "wittgenstein_ladder": "Bridge: 漏水蓄水池 -> Deconstruct: 经典自旋禁阻 -> Replace: 重原子旋轨耦合突破 25% 上限",
            "human_orthogonal_insight": "用户指出左图自旋比例必须与右图三重态微秒级长寿命导致的滚降直接对照",
            "visual_modality": "V2_fig1a_spin_statistics_diagram",
            "hidden_teleprompter_qa": "按 S 键展示评委关于荧光与磷光内量子效率极限的推导问答",
        }
        rec1 = record_tdd_station_capsule(manifest_path, 1, capsule_1)
        await_s1 = audit_single_slide_step(manifest_path, 1, s1_path, valid_bundle, slides_generated_in_current_step=1)
        if rec1.get("status") != "PASS" or await_s1.get("status") != "AWAITING_HUMAN_APPROVAL":
            raise AssertionError(f"TDD Step 1 failed: {rec1}, {await_s1}")

        # Check 4: Human gate blocks slide_02 until approved
        neg_unapproved = record_tdd_station_capsule(manifest_path, 2, {**capsule_1, "station_id": "Station_1.2"})
        if neg_unapproved.get("status") != "FAIL":
            raise AssertionError(f"Expected 1-hop block while slide_01 awaits human approval: {neg_unapproved}")

        hum_s1 = approve_slide_by_human(manifest_path, 1, "左图自旋统计与结论对齐，通过！")
        if hum_s1.get("status") != "PASS":
            raise AssertionError(f"Human approval 1 failed: {hum_s1}")

        # Check 5: Assembly blocked before slide_02 passes, then passes after slide_02 passes
        neg_asm = assemble_verified_deck(manifest_path, tdir / "deck.html")
        if neg_asm.get("status") != "FAIL":
            raise AssertionError(f"Expected assembly failure while slide_02 unverified: {neg_asm}")

        record_tdd_station_capsule(manifest_path, 2, {**capsule_1, "station_id": "Station_1.2", "visual_modality": "V3_interactive_rabi"})
        audit_single_slide_step(manifest_path, 2, s2_path, valid_bundle, slides_generated_in_current_step=1)
        approve_slide_by_human(manifest_path, 2, "通过！")
        pos_asm = assemble_verified_deck(manifest_path, tdir / "deck.html")
        if pos_asm.get("status") != "PASS":
            raise AssertionError(f"Deck assembly failed: {pos_asm}")

        # --- PART B: Mode 2 (`GRILL` / Grill-Driven Design) ---
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

        # Check 6a: Auditing slide_01 in GRILL mode without gdd_grill_capsule or with rubber-stamp/missing MCQ is blocked
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

        # Check 6b: Record Dual-Stage GDD capsule (Stage 1: 3-Part Grill + Isomorphic Re-grill; Stage 2: Bottleneck Mapping + Slide Design MCQ) and pass slide_01
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

        # --- PART C: Mode 3 (`AUTONOMOUS_DUAL_EVOLVE` / Head-Down Build + Post-Review Dual-Evolution) ---
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

        # Check 7: Incomplete dual-evolution feedback receipt (patching PPT without recording AWF evolution) is blocked
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

        # Check 8: Complete dual-evolution feedback receipt patches PPT slide AND records AWF upgrade receipt
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

        # --- PART D: Stage 0 Macro-GDD Global Deck Blueprint & V3 Animation Designation Enforcement ---
        macro_manifest = tdir / "macro_manifest.json"
        global_bp = {
            "macro_thesis_probe": {
                "executive_core_conflict": "蓝光磷光微秒级寿命引发高亮度 TTA 烧屏，利用极化激元反交叉耦合压缩寿命破局",
                "human_baseline_alignment": "用户确认以自旋统计与极化激元反交叉为核心主线",
            },
            "total_slides_mcq": {
                "options": ["A (Recommended): 1页核心演示", "B: 18页完整版"],
                "selected_option": "A (Recommended): 1页核心演示",
                "planned_total_slides": 1,
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

        # Check 9a: Slide 1 was globally designated for V3 animation in global_deck_blueprint;
        # submitting a V2 capsule (`grill_cap_1` has `V2_...`) must be blocked!
        record_grill_station_capsule(macro_manifest, 1, grill_cap_1)
        neg_v3_downgrade = audit_single_slide_step(macro_manifest, 1, s1_path, valid_bundle, slides_generated_in_current_step=1)
        if neg_v3_downgrade.get("status") != "FAIL":
            raise AssertionError(f"Expected V3 animation downgrade to V2 to be blocked: {neg_v3_downgrade}")

        # Check 9b: Upgrading capsule to V3 interactive animation satisfies the Global Deck Blueprint V3 contract!
        record_grill_station_capsule(macro_manifest, 1, {**grill_cap_1, "visual_modality": "V3_interactive_purcell_slider"})
        pos_v3_contract = audit_single_slide_step(macro_manifest, 1, s1_path, valid_bundle, slides_generated_in_current_step=1)
        if pos_v3_contract.get("status") != "PASS":
            raise AssertionError(f"Expected V3 animation slide to pass: {pos_v3_contract}")

        # --- PART E: Unbounded Flow-Driven Blueprint ("页数不限，顺着逻辑流程自然确定") + JIT V3 Discovery ---
        elastic_manifest = tdir / "elastic_manifest.json"
        elastic_bp = {
            "macro_thesis_probe": {
                "executive_core_conflict": "蓝光磷光微秒级寿命引发高亮度 TTA 烧屏，利用极化激元反交叉耦合压缩寿命破局",
                "human_baseline_alignment": "用户表示开头先确定内容和逻辑演进主线，页数选『不限』顺着逻辑自然长出，动画也边问边定",
            },
            "logical_flow_mcq": {
                "options": [
                    "A (Recommended): 1.自旋统计与TTA死结 -> 2.极化激元反交叉破局原理与色散验证",
                    "B: 结论先行倒叙主线",
                ],
                "selected_option": "A (Recommended): 1.自旋统计与TTA死结 -> 2.极化激元反交叉破局原理与色散验证",
                "logical_flow_spine": ["1.自旋统计与TTA死结", "2.极化激元反交叉破局原理与色散验证"],
            },
            "total_slides_mcq": {
                "options": ["A (Recommended): 页数不限（顺着逻辑流程做，需要几页自然确定）", "B: 10–14页紧凑档"],
                "selected_option": "A (Recommended): 页数不限（顺着逻辑流程做，需要几页自然确定）",
                "slide_count_policy": "UNBOUNDED_FLOW_DRIVEN",
                "planned_total_slides": "不限",
            },
            "emphasis_allocation_mcq": {
                "options": ["A (Recommended): 重点深挖极化激元反交叉耦合", "B: 重点讲工艺"],
                "selected_option": "A (Recommended): 重点深挖极化激元反交叉耦合",
                "heavy_focus_modules": ["极化激元反交叉耦合"],
            },
            "v3_animation_budget_mcq": {
                "options": ["A (Recommended): 全篇保底 >=1 页 V3 动画，具体哪页在问答过程中动态拍板 (JIT_DURING_QA)", "B: 提前锁死"],
                "selected_option": "A (Recommended): 全篇保底 >=1 页 V3 动画，具体哪页在问答过程中动态拍板 (JIT_DURING_QA)",
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

        # Pass Slide 1 as V2 static diagram
        record_grill_station_capsule(elastic_manifest, 1, grill_cap_1)
        audit_single_slide_step(elastic_manifest, 1, s1_path, valid_bundle, slides_generated_in_current_step=1)

        # Check 10a: Trying to assemble now fails because 0 V3 slides were built, violating min_v3_slides_quota=1!
        neg_jit_quota = assemble_verified_deck(elastic_manifest, tdir / "elastic_deck.html")
        if neg_jit_quota.get("status") != "FAIL":
            raise AssertionError(f"Expected assembly to fail when V3 quota (1) not yet met: {neg_jit_quota}")

        # Check 10b: During Q&A, user & agent decide to dynamically SPLIT/INSERT Slide 2 AND promote it to V3 animation!
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

        # Also test dynamicINSERT + MERGE_SLIDES: insert a 3rd slide then merge it back when user says they already know it
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

        # Complete Slide 2 with V3 interactive animation and assemble verified deck
        record_grill_station_capsule(
            elastic_manifest,
            2,
            {**grill_cap_1, "station_id": "Station_1.2", "visual_modality": "V3_interactive_anticrossing_slider"},
        )
        audit_single_slide_step(elastic_manifest, 2, s2_path, valid_bundle, slides_generated_in_current_step=1)
        pos_elastic_asm = assemble_verified_deck(elastic_manifest, tdir / "elastic_deck.html")
        if pos_elastic_asm.get("status") != "PASS" or pos_elastic_asm.get("total_slides_assembled") != 2:
            raise AssertionError(f"Expected elastic deck assembly with JIT V3 slide to pass: {pos_elastic_asm}")

        # --- PART F: Hierarchical Onion Peeling Flow (Layer 0 Coarse Trunks -> Layer 1 Trunk Sub-Frame -> Leaf Slide) ---
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

        # Pass Trunk_1's leaf slide
        record_grill_station_capsule(onion_manifest, 1, grill_cap_1)
        audit_single_slide_step(onion_manifest, 1, s1_path, valid_bundle, slides_generated_in_current_step=1)

        # Check 11a: Trying to assemble deck while Trunk_2 is still UNPEELED is blocked!
        neg_unpeeled = assemble_verified_deck(onion_manifest, tdir / "onion_deck.html")
        if neg_unpeeled.get("status") != "FAIL":
            raise AssertionError(f"Expected assembly failure while Trunk_2 is UNPEELED: {neg_unpeeled}")

        # Check 11b: Peel Trunk_2 (entering Trunk_2 and deciding its sub-framework -> materializes slide_02)
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

        # -----------------------------------------------------------------
        # PART G: Universal I/O Onion Bus (EvidenceIngest + DevilReviewer + Cross-Artifact SciWord/FigPPT Sync)
        # -----------------------------------------------------------------
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

        # Check 12a: Trying to assemble before SCI_WORD and FIG_PPTX receipts are recorded is blocked!
        neg_io_asm = assemble_verified_deck(io_bus_manifest, tdir / "io_bus_deck.html")
        if neg_io_asm.get("status") != "FAIL":
            raise AssertionError(f"Expected assembly failure when SCI_WORD/FIG_PPTX receipts are missing: {neg_io_asm}")

        # Check 12b: Record SCI_WORD (scientific-report-authoring) and FIG_PPTX (editable-figure-pptx) receipts
        rec_word = record_cross_artifact_unit_receipt(
            io_bus_manifest,
            {
                "artifact_channel": "SCI_WORD",
                "unit_id": "Section_2_Results_And_Discussion",
                "awf_skill_id": "skill.build-scientific-docx@1.0.0-rc.12",
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

    return {
        "status": "PASS",
        "selftest": "AWF_HTML_PPT_V3_MacroToMicro_TriMode_TDD_Grill_And_AutonomousDualEvolve",
        "checks_passed": [
            "Block_Out_Of_Order_Slide_Leapfrogging_HopDistance_2",
            "Block_MultiSlide_Batch_Generation_Per_Step_GT_1",
            "Mode1_TDD_Block_Without_Capsule_And_Pass_With_Tutor_Station_Capsule",
            "Block_Next_Slide_While_Awaiting_Human_Approval_Gate",
            "Block_Deck_Assembly_With_Unverified_Slide",
            "Mode2_GRILL_Block_Without_Capsule_And_Pass_With_Grill_TeachOnMiss_Regrill_Capsule",
            "Mode3_AUTONOMOUS_HeadDown_Build_And_Block_Incomplete_DualEvolution_Receipt",
            "Mode3_AUTONOMOUS_Pass_PostReview_PPT_Patch_And_AWF_Dual_Evolution_Receipt",
            "Stage0_Macro_GDD_Global_Deck_Blueprint_And_V3_Animation_Enforcement",
            "MidStream_Elastic_Slide_Split_Merge_And_JIT_V3_Animation_Promotion",
            "Hierarchical_Onion_Peeling_Layer0_CoarseFrame_To_Layer1_TrunkSubFrame_To_LeafSlide",
            "Universal_IO_Onion_Bus_EvidenceIngest_DevilReviewer_And_CrossArtifact_SciWord_FigPPT_Sync",
        ],
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="AWF HTML-PPT V3 Tri-Mode Single-Slide Gatekeeper")
    parser.add_argument("--self-test", action="store_true", help="Run Tri-Mode (TDD / GRILL / AUTONOMOUS_DUAL_EVOLVE) self-test")
    parser.add_argument("--init-storyboard", type=str, default="", help="Path to storyboard.json")
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
    parser.add_argument("--assemble-deck", action="store_true", help="Assemble verified slides into deck")
    parser.add_argument("--output", type=str, default="deck.html", help="Output deck HTML path")
    args = parser.parse_args(argv)

    if args.self_test:
        rep = run_selftest()
        print(json.dumps(rep, indent=2, ensure_ascii=False))
        return 0 if rep.get("status") == "PASS" else 1

    if args.init_storyboard:
        sb_doc = json.loads(Path(args.init_storyboard).read_text(encoding="utf-8"))
        rep = init_storyboard_manifest(sb_doc, Path(args.manifest))
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

    if args.assemble_deck:
        rep = assemble_verified_deck(Path(args.manifest), Path(args.output))
        print(json.dumps(rep, indent=2, ensure_ascii=False))
        return 0 if rep.get("status") == "PASS" else 1

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
