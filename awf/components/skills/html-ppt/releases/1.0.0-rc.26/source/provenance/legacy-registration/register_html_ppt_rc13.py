#!/usr/bin/env python3
"""
Co-located AWF registration script for `skill.html-ppt@1.0.0-rc.13`
and standalone workflow `html-ppt@1.0.0-rc.10` (AWF HTML-PPT V3 / SciSlide).
Enforces Two-Level Macro-to-Micro Tri-Mode Architecture:
- Stage 0 Macro-GDD Global Deck Blueprint (`global_deck_blueprint`: Total Slides MCQ + Emphasis Allocation MCQ +
  V3 Animation Budget MCQ, cross-checked at each single-slide step),
- Mode 1 (`TDD` Tutor-Driven Design),
- Mode 2 (`GRILL` Dual-Stage Grill-Driven Design: 3-Part Mechanism Grill + Slide Design MCQ),
- Mode 3 (`AUTONOMOUS_DUAL_EVOLVE` Head-Down Build + Post-Review PPT & AWF Dual-Evolution),
strictly 1-Slide-Per-Step micro-step execution, and 1-Hop `slide_manifest.json` topological lock.
Strictly follows ADR 0012 and ADR 0022.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

sys.dont_write_bytecode = True

AWF_ROOT = Path("/home/zc/agent_workflows")
if not AWF_ROOT.exists():
    AWF_ROOT = Path(r"Z:\agent_workflows")
sys.path.insert(0, str(AWF_ROOT / "bin"))

import verify  # type: ignore


def write_json_yaml(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def build_release_meta(source_rel: str, legacy_hash: str) -> Dict[str, Any]:
    return {
        "status": "validated",
        "observed_at": "2026-11-09",
        "entry_point": "SKILL.md",
        "source_snapshot": source_rel,
        "tree_sha256": legacy_hash,
        "depends_on": [
            "skill.design-anti-goodhart@1.0.0-rc.11",
            "skill.anti-goodhart-verification@3.7.0-rc.1",
        ],
        "runtime_requirements": [
            "UTF-8 Markdown Skill loader (Antigravity / Codex / Pi / Grok)",
            "Python 3.9+ for executing scripts/audit_single_slide_step.py and AWF DesignAG",
            "A browser or Playwright headless Chromium for 1920x1080 rendered-page review",
        ],
        "capabilities": [
            "teaching-narrative-planning",
            "source-aware-html-slides",
            "visual-and-interaction-review",
            "iterative-feedback-learning",
            "standalone-16x9-slide-starter",
            "concrete-system-semantics-for-algorithms-and-optimization",
            "concrete-scientific-title-language",
            "stage0-macro-gdd-global-deck-blueprint-total-slides-emphasis-and-v3-animation-contract",
            "strict-single-slide-per-step-microstep-execution",
            "one-hop-topological-slide-manifest-locking",
            "station-to-slide-tutor-driven-design-tdd-cognitive-capsule-binding",
            "dual-stage-grill-driven-design-3part-mechanism-grill-and-slide-design-mcq",
            "autonomous-headdown-build-with-postreview-ppt-and-awf-dual-evolution",
            "human-in-the-loop-per-slide-signoff-gate",
            "designag-18gate-and-dual-rubric-automated-enforcement",
            "escape-to-gate-darwinian-regression-evolution",
        ],
        "limitations": [
            "HTML rendering and release integrity checks must be paired with scientific source verification",
            "Final visual acceptance includes 1920x1080 rendered-page review under Gate D18",
        ],
        "provenance": (
            "Release 1.0.0-rc.13 of AWF HTML-PPT (`skill.html-ppt@1.0.0-rc.13` and standalone workflow "
            "`html-ppt@1.0.0-rc.10`), introducing Stage 0 Macro-GDD Global Deck Blueprint verification and "
            "per-slide V3 animation designation enforcement (`designated_v3_animation`), powered by "
            "`skill.design-anti-goodhart@1.0.0-rc.11`."
        ),
    }


def build_workflow_descriptor() -> Dict[str, Any]:
    return {
        "schema_version": 1,
        "id": "html-ppt",
        "release": "1.0.0-rc.10",
        "status": "validated",
        "purpose": (
            "Self-Evolving, Anti-Goodhart 16:9 Scientific Interactive HTML Presentation Workflow "
            "(AWF HTML-PPT V3 / SciSlide) enforcing a Two-Level Macro-to-Micro Tri-Mode Architecture "
            "(Stage 0 Global Deck Blueprint MCQs deciding total slides, heavy focus modules, and exact V3 "
            "animation slides + Stage 1..N Single-Slide `TDD`, Dual-Stage `GRILL`, or `AUTONOMOUS_DUAL_EVOLVE`), "
            "strictly 1-Slide-Per-Step micro-step generation (`max_slides_generated_per_step == 1`), "
            "1-Hop `slide_manifest.json` topological slide locking (`unverified_slide_hop_distance == 1`), "
            "18 Automated DesignAG Gates (`D1`-`D18`), 7 Redlines (`R1`-`R7`), Dual Quantitative Rubrics (`>=85/100`), "
            "Read-Only Red Subagent Visual Audit, and Darwinian Escape-to-Gate evolution."
        ),
        "entry_skills": [
            "skill.html-ppt",
            "skill.design-anti-goodhart",
            "skill.anti-goodhart-verification",
        ],
        "stages": [
            {
                "id": "stage0-macro-gdd-global-deck-blueprint-and-stage1-storyboard-manifest-d13-d14-d16",
                "required": True,
                "skill": "skill.html-ppt",
            },
            {
                "id": "stage2-paper-figure-subpanel-crop-and-visual-asset-preaudit-d5-d9-d10-d11",
                "required": True,
                "skill": "skill.design-anti-goodhart",
            },
            {
                "id": "stage3-trimode-tdd-dualstage-grill-or-autonomous-single-slide-per-step-build-d1-to-d12-d15-d16",
                "required": True,
                "skill": "skill.html-ppt",
            },
            {
                "id": "stage4-readonly-red-subagent-visual-audit-dual-rubric-assembly-and-postreview-dual-evolution-d17-d18",
                "required": True,
                "skill": "skill.design-anti-goodhart",
            },
        ],
        "engineering_gate": (
            "Strictly enforce Stage 0 Global Deck Blueprint (`global_deck_blueprint` + per-slide `designated_v3_animation`), "
            "forbid generating >1 slide per step (`max_slides_generated_per_step == 1`) or unlocking `slide_{k+1}` before "
            "`slide_k` holds a verified SHA-256 `PASS` receipt (`unverified_slide_hop_distance == 1`), and enforce all 18 "
            "DesignAG gates (`D1`-`D18`) via `scripts/audit_single_slide_step.py`."
        ),
        "scientific_gate": (
            "All slides must satisfy concrete scientific object/claim title semantics, >=3-step causal Why chains (`D14`), "
            "explicit figure-text coupling (`D11`), multiplicative visual modality requirements (`V2/V3` on mechanism slides, "
            "capping `V0` pure text at 30%), zero Redlines (`R1`-`R7`), and >=85/100 on both Optoelectronic v3 and "
            "Supermolecule 5-Dim quantitative rubrics."
        ),
        "version_lock": "versions.lock",
    }


def register_all(awf_root: Path) -> Dict[str, Any]:
    comp_id = "skill.html-ppt"
    comp_rel_id = "1.0.0-rc.13"
    wf_id = "html-ppt"
    wf_rel_id = "1.0.0-rc.10"
    source_rel = f"components/skills/html-ppt/releases/{comp_rel_id}/source"
    source_dir = awf_root / source_rel
    comp_descriptor_rel = "components/skills/html-ppt/component.yaml"
    comp_descriptor_path = awf_root / comp_descriptor_rel

    legacy_hash = verify.tree_sha256(source_dir)
    v2_hash = verify.tree_sha256_v2(source_dir, "tree")
    v2_paths = verify.tree_v2_paths(source_dir, "tree")
    regular_bytes = sum(
        p.lstat().st_size for p in v2_paths if not p.is_symlink() and p.is_file()
    )
    symlink_count = sum(p.is_symlink() for p in v2_paths)

    release_meta = build_release_meta(source_rel, legacy_hash)
    comp_doc = verify.read_manifest(comp_descriptor_path)
    comp_doc.setdefault("releases", {})[comp_rel_id] = release_meta
    write_json_yaml(comp_descriptor_path, comp_doc)
    comp_sha = verify.file_sha256(comp_descriptor_path)
    metadata_sha256 = verify.canonical_object_sha256(release_meta)

    attest_rel = "attestations/release-integrity-20261109-html-ppt-rc13.yaml"
    attest_path = awf_root / attest_rel
    attest_doc = {
        "schema_version": 1,
        "digest_contract": "awf-tree-v2",
        "observed_at": "2026-11-09",
        "owner": "awf-html-ppt-release-20261109-rc13",
        "provenance": "Validated release 1.0.0-rc.13 of AWF HTML-PPT (`skill.html-ppt@1.0.0-rc.13` and standalone workflow `html-ppt@1.0.0-rc.10`, enforcing Stage 0 Macro-GDD Global Deck Blueprint + Per-Slide V3 Animation Designation + Dual-Stage Micro-GDD).",
        "releases": {
            f"{comp_id}@{comp_rel_id}": {
                "coverage": "tree",
                "descriptor": comp_descriptor_rel,
                "descriptor_file_sha256": comp_sha,
                "entry_count": len(v2_paths),
                "legacy_tree_sha256": legacy_hash,
                "metadata_sha256": metadata_sha256,
                "regular_file_bytes": regular_bytes,
                "root": source_rel,
                "symlink_count": symlink_count,
                "tree_sha256": v2_hash,
            }
        },
    }
    write_json_yaml(attest_path, attest_doc)

    wf_descriptor_rel = f"workflows/{wf_id}/releases/{wf_rel_id}/workflow.yaml"
    wf_lock_rel = f"workflows/{wf_id}/releases/{wf_rel_id}/versions.lock"
    wf_descriptor_path = awf_root / wf_descriptor_rel
    wf_lock_path = awf_root / wf_lock_rel

    write_json_yaml(wf_descriptor_path, build_workflow_descriptor())
    lock_doc = {
        "schema_version": 1,
        "workflow": wf_id,
        "workflow_release": wf_rel_id,
        "locked_at": "2026-11-09",
        "components": {
            comp_id: comp_rel_id,
            "skill.design-anti-goodhart": "1.0.0-rc.11",
            "skill.anti-goodhart-verification": "3.7.0-rc.1",
        },
    }
    write_json_yaml(wf_lock_path, lock_doc)
    wf_sha = verify.file_sha256(wf_descriptor_path)
    lock_sha = verify.file_sha256(wf_lock_path)

    reg_path = awf_root / "registry.yaml"
    reg = verify.read_manifest(reg_path)
    comps: List[Dict[str, Any]] = reg["components"]
    for c in comps:
        if c.get("id") == comp_id:
            c["descriptor_sha256"] = comp_sha
            c["latest_release"] = comp_rel_id
            break

    if attest_rel not in reg["integrity_attestations"]:
        reg["integrity_attestations"].append(attest_rel)

    req_list: List[str] = reg["integrity_policy"]["required_release_attestations"]
    ref_str = f"{comp_id}@{comp_rel_id}"
    if ref_str not in req_list:
        req_list.append(ref_str)
        req_list.sort()

    wfs: List[Dict[str, Any]] = reg["workflows"]
    for w in wfs:
        if w.get("id") == wf_id:
            w["descriptor"] = wf_descriptor_rel
            w["descriptor_sha256"] = wf_sha
            w["lock"] = wf_lock_rel
            w["lock_sha256"] = lock_sha
            w["status"] = "validated"
            if "html-ppt-v3" not in w.get("aliases", []):
                w.setdefault("aliases", []).append("html-ppt-v3")
            w.setdefault("releases", {})[wf_rel_id] = {
                "descriptor": wf_descriptor_rel,
                "descriptor_sha256": wf_sha,
                "lock": wf_lock_rel,
                "lock_sha256": lock_sha,
                "status": "validated",
            }
            break

    write_json_yaml(reg_path, reg)
    return {
        "component": ref_str,
        "workflow": f"{wf_id}@{wf_rel_id}",
        "legacy_tree_sha256": legacy_hash,
        "v2_tree_sha256": v2_hash,
        "component_sha256": comp_sha,
        "workflow_sha256": wf_sha,
        "lock_sha256": lock_sha,
    }


if __name__ == "__main__":
    res = register_all(AWF_ROOT)
    print(json.dumps(res, indent=2))
