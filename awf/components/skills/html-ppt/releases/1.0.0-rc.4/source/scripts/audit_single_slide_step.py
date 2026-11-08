#!/usr/bin/env python3
"""
AWF HTML-PPT V2 Single-Slide Atomic Micro-Step Gatekeeper & Deck Compiler
(`skill.html-ppt@1.0.0-rc.4`).

Physically enforces:
1. Strictly 1 Slide Per Step (`max_slides_generated_per_step == 1`);
2. 1-Hop Slide Topological Lock (`unverified_slide_hop_distance == 1` via `slide_manifest.json`);
3. Full 18-Gate DesignAG audit (`skill.design-anti-goodhart@1.0.0-rc.2`) before unlocking `slide_{k+1}`;
4. Cryptographic SHA-256 verification of all single-slide modules before final deck assembly.
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
        Path("/home/zc/agent_workflows/components/skills/design-anti-goodhart/releases/1.0.0-rc.2/source/scripts"),
        Path(r"Z:\agent_workflows\components\skills\design-anti-goodhart\releases\1.0.0-rc.2\source\scripts"),
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


def init_storyboard_manifest(
    storyboard_doc: Dict[str, Any],
    manifest_path: Path,
) -> Dict[str, Any]:
    """
    Validate Storyboard against DesignAG Gates D13, D14, D16 (`max_slides_generated_per_step == 1`)
    and initialize `slide_manifest.json` with ONLY `slide_01` unlocked.
    """
    dag = _load_design_ag_module()
    slides_spec = storyboard_doc.get("storyboard_slides", [])
    d13 = dag.verify_narrative_arc_and_foreshadowing(storyboard_doc.get("narrative_spec", {}))
    d14 = dag.verify_causal_why_chain_and_tradeoffs(storyboard_doc.get("mechanism_spec", {}))
    d16 = dag.verify_storyboard_microstep_and_layout_diversity(
        slides_spec,
        max_slides_generated_per_step=1,
        unverified_slide_hop_distance=1,
    )

    failed_gates = [g["gate"] for g in (d13, d14, d16) if not g.get("passed")]
    if failed_gates:
        return {
            "status": "FAIL",
            "stage": "Stage1_Storyboard_Contract",
            "failed_gates": failed_gates,
            "details": {"D13": d13, "D14": d14, "D16": d16},
        }

    slide_entries: List[Dict[str, Any]] = []
    for idx, s in enumerate(slides_spec, start=1):
        slide_entries.append({
            "slide_index": idx,
            "slide_id": f"slide_{idx:02d}",
            "title": str(s.get("title", f"Slide {idx}")),
            "layout_archetype": str(s.get("layout_archetype", "split_left_fig_right_guided_steps")),
            "required_visual_level": str(s.get("required_visual_level", "V2")),
            "status": "UNLOCKED" if idx == 1 else "LOCKED",
            "sha256": "",
            "file_path": "",
        })

    manifest_data = {
        "schema_version": 1,
        "max_slides_generated_per_step": 1,
        "total_slides": len(slide_entries),
        "storyboard_slides": slides_spec,
        "slides": slide_entries,
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest_data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {
        "status": "PASS",
        "stage": "Stage1_Storyboard_Contract",
        "total_slides": len(slide_entries),
        "unlocked_slide": "slide_01",
        "manifest_path": str(manifest_path),
    }


def audit_single_slide_step(
    manifest_path: Path,
    slide_index: int,
    slide_html_path: Path,
    slide_bundle: Dict[str, Any],
    slides_generated_in_current_step: int = 1,
) -> Dict[str, Any]:
    """
    Stage 3 Gatekeeper: Enforce strictly 1 slide per step (`slides_generated_in_current_step == 1`)
    and 1-Hop Topological Lock (`slide_{k-1}` must be `PASS` before `slide_k` can be audited).
    """
    dag = _load_design_ag_module()
    if not manifest_path.is_file():
        return {"status": "FAIL", "reason": f"Missing slide_manifest.json: {manifest_path}"}

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    slides_list: List[Dict[str, Any]] = manifest.get("slides", [])
    if slide_index < 1 or slide_index > len(slides_list):
        return {"status": "FAIL", "reason": f"Invalid slide_index {slide_index}"}

    # 1. Compute topological hop distance from last verified PASS slide
    last_pass_idx = 0
    for entry in slides_list:
        idx = _int_val(entry, "slide_index", 0)
        if entry.get("status") == "PASS" and idx == last_pass_idx + 1:
            last_pass_idx = idx
    hop_distance = slide_index - last_pass_idx
    if slide_index <= last_pass_idx:
        hop_distance = 1

    d16 = dag.verify_storyboard_microstep_and_layout_diversity(
        manifest.get("storyboard_slides", []),
        max_slides_generated_per_step=slides_generated_in_current_step,
        unverified_slide_hop_distance=hop_distance,
    )
    if not d16.get("passed"):
        return {
            "status": "FAIL",
            "effective_reward": float("-inf"),
            "slide_index": slide_index,
            "reason": "Single-Slide Micro-Step or 1-Hop Topological Lock Violation (D16)",
            "D16": d16,
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
        dag. verify_bounding_boxes_zero_overlap_and_clipping(slide_bundle.get("boxes", [])),
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

    # Record PASS receipt for slide_k and unlock slide_{k+1}
    target_entry = slides_list[slide_index - 1]
    target_entry["status"] = "PASS"
    target_entry["sha256"] = _sha256_file(slide_html_path)
    target_entry["file_path"] = str(slide_html_path)
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
    Self-test verifying:
    1. Submitting >1 slide in a single step (`slides_generated_in_current_step=2`) is blocked;
    2. Auditing `slide_02` before `slide_01` is `PASS` (`unverified_slide_hop_distance=2`) is blocked;
    3. Assembling deck before all slides pass is blocked;
    4. Sequential 1-slide-per-step verification (`slide_01` -> `slide_02`) and assembly passes.
    """
    with tempfile.TemporaryDirectory(prefix="awf_html_ppt_test_") as tmp:
        tdir = Path(tmp)
        manifest_path = tdir / "slide_manifest.json"
        storyboard_doc = {
            "narrative_spec": {
                "has_macro_background_and_core_def": True,
                "has_degradation_or_bottleneck_mechanism": True,
                "has_prior_art_and_ceiling": True,
                "has_clue_free_blind_guessing": False,
                "has_foreshadowing_and_callback": True,
            },
            "mechanism_spec": {
                "causal_why_links_explained": {"why_a": True, "why_b": True, "why_c": True},
                "has_dedicated_device_or_assembly_slide": True,
                "has_real_molecular_chemical_structures": True,
                "has_controlled_pair_comparison_and_baseline_note": True,
                "has_multi_objective_tradeoff_explanation": True,
                "scientific_or_structural_errors": [],
            },
            "storyboard_slides": [
                {"title": "电激发自旋统计决定磷光 PHOLED 路线", "layout_archetype": "top_banner_dual_cards"},
                {"title": "极化激元反交叉耦合加速辐射衰减", "layout_archetype": "split_left_fig_right_steps"},
            ],
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

        # Negative Test 1: Try to jump to slide_02 before slide_01 is PASS (1-Hop violation)
        neg_hop = audit_single_slide_step(manifest_path, 2, s2_path, valid_bundle, slides_generated_in_current_step=1)
        if neg_hop.get("status") != "FAIL":
            raise AssertionError(f"Expected 1-hop violation when auditing slide_02 before slide_01: {neg_hop}")

        # Negative Test 2: Try to batch 2 slides in a single step (Single-Slide violation)
        neg_batch = audit_single_slide_step(manifest_path, 1, s1_path, valid_bundle, slides_generated_in_current_step=2)
        if neg_batch.get("status") != "FAIL":
            raise AssertionError(f"Expected single-slide violation when slides_generated_in_current_step=2: {neg_batch}")

        # Positive Step 1: Audit slide_01 (1 slide/step) -> unlocks slide_02
        pos_s1 = audit_single_slide_step(manifest_path, 1, s1_path, valid_bundle, slides_generated_in_current_step=1)
        if pos_s1.get("status") != "PASS" or pos_s1.get("next_unlocked_slide") != "slide_02":
            raise AssertionError(f"Slide 1 audit failed: {pos_s1}")

        # Negative Test 3: Try to assemble deck while slide_02 is still unverified
        neg_asm = assemble_verified_deck(manifest_path, tdir / "deck.html")
        if neg_asm.get("status") != "FAIL":
            raise AssertionError(f"Expected assembly failure while slide_02 is unverified: {neg_asm}")

        # Positive Step 2: Audit slide_02 (1 slide/step) -> PASS
        pos_s2 = audit_single_slide_step(manifest_path, 2, s2_path, valid_bundle, slides_generated_in_current_step=1)
        if pos_s2.get("status") != "PASS":
            raise AssertionError(f"Slide 2 audit failed: {pos_s2}")

        # Positive Step 3: Assemble full verified deck
        pos_asm = assemble_verified_deck(manifest_path, tdir / "deck.html")
        if pos_asm.get("status") != "PASS" or pos_asm.get("total_slides_assembled") != 2:
            raise AssertionError(f"Deck assembly failed: {pos_asm}")

    return {
        "status": "PASS",
        "selftest": "AWF_HTML_PPT_V2_SingleSlide_MicroStep_And_1Hop_Lock",
        "checks_passed": [
            "Block_Out_Of_Order_Slide_Leapfrogging_HopDistance_2",
            "Block_MultiSlide_Batch_Generation_Per_Step_GT_1",
            "Block_Deck_Assembly_With_Unverified_Slide",
            "Pass_Sequential_Single_Slide_Verification_And_Deck_Assembly",
        ],
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="AWF HTML-PPT V2 Single-Slide Step Gatekeeper")
    parser.add_argument("--self-test", action="store_true", help="Run single-slide micro-step & 1-hop lock self-test")
    parser.add_argument("--init-storyboard", type=str, default="", help="Path to storyboard.json")
    parser.add_argument("--manifest", type=str, default="slide_manifest.json", help="Path to slide_manifest.json")
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

    if args.assemble_deck:
        rep = assemble_verified_deck(Path(args.manifest), Path(args.output))
        print(json.dumps(rep, indent=2, ensure_ascii=False))
        return 0 if rep.get("status") == "PASS" else 1

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
