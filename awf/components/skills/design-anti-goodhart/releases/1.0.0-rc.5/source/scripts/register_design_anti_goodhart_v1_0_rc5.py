#!/usr/bin/env python3
"""
Co-located AWF registration script for `skill.design-anti-goodhart@1.0.0-rc.5`
and standalone workflow `design-anti-goodhart@1.0.0-rc.5` (AWF DesignAG).
Enforces strictly 1-Slide-Per-Step micro-step generation (`MAX_MICROSTEP_BATCH_SLIDES = 1`),
1-Hop Slide Topological Lock (`unverified_slide_hop_distance == 1`), and Tri-Mode verification:
(1) Tutor-Driven Design (`tdd_station_capsule`),
(2) Dual-Stage Grill-Driven Design (`gdd_grill_capsule`: 3-Part Anchored Mechanism Grill +
    Anti-Rubber-Stamp Re-Grill + Bottleneck-to-Slide Mapping + Slide Design MCQ),
(3) Autonomous Draft + Post-Review Dual-Evolution (`dual_evolution_feedback_receipt`).
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
        "observed_at": "2026-11-08",
        "entry_point": "SKILL.md",
        "source_snapshot": source_rel,
        "tree_sha256": legacy_hash,
        "depends_on": [
            "skill.anti-goodhart-verification@3.6.0-rc.1",
        ],
        "runtime_requirements": [
            "UTF-8 Markdown Skill loader (Antigravity / Codex / Pi / Grok)",
            "Python 3.9+ for executing scripts/awf_design_anti_goodhart_gates.py",
        ],
        "capabilities": [
            "visual-pedagogical-and-html-ppt-anti-goodhart-18-gate-verification-engine",
            "strict-single-slide-per-step-microstep-and-1hop-topological-slide-lock",
            "station-to-slide-tutor-driven-design-tdd-cognitive-capsule-verification",
            "dual-stage-grill-driven-design-3part-mechanism-grill-anti-rubberstamp-and-slide-design-mcq",
            "autonomous-draft-post-review-dual-evolution-ppt-and-awf-upgrade-verification",
            "dual-rubric-quantitative-scorer-optoelectronic-v3-and-supermolecule-5dim",
            "multiplicative-clarity-times-visual-modality-v0-pure-text-30pct-cap",
            "seven-redlines-r1-to-r7-circuit-breaker-and-15pt-deduction-cap",
            "zero-unrendered-latex-and-html-tag-balance-and-grid-orphan-guard",
            "natural-academic-copywriting-anti-cliche-and-anti-prompt-residue-guard",
            "acronym-first-use-visible-definition-and-inline-popover-guard",
            "anti-cartoon-emoji-anti-fake-progressbar-and-anti-ai-decorative-image-guard",
            "playwright-bounding-box-zero-overlap-zero-clipping-and-whitespace-com-balance",
            "image-aspect-ratio-subpanel-crop-purity-and-figure-text-explicit-coupling",
            "wcag-contrast-narrative-foreshadowing-and-causal-why-chain-verification",
            "interactive-physics-widget-anti-hollow-animation-and-storyboard-microstep-anchor",
            "multimodal-red-blue-visual-adversarial-critic-protocol",
        ],
        "limitations": [
            "DOM bounding-box probes (D7-D8) accept headless browser/Playwright bounding-box JSON exports or structured layout bundles",
            "Sub-panel crop purity (D10) validates normalized crop coordinates or rendered crop metadata against whitespace and sliced-caption thresholds",
        ],
        "provenance": (
            "Release 1.0.0-rc.5 of AWF DesignAG (`skill.design-anti-goodhart@1.0.0-rc.5`), "
            "upgrading Gate D16 `verify_grill_station_capsule_completeness` to enforce Dual-Stage Grill-Driven Design "
            "(Stage 1: 4-Archetype 3-Part Anchored Mechanism Grill + Anti-Rubber-Stamp Re-Grill; Stage 2: "
            "`bottleneck_to_slide_mapping` + `slide_design_mcq` multiple-choice slide design decision), "
            "layered atop `skill.anti-goodhart-verification@3.6.0-rc.1`."
        ),
    }


def build_workflow_descriptor() -> Dict[str, Any]:
    return {
        "schema_version": 1,
        "id": "design-anti-goodhart",
        "release": "1.0.0-rc.5",
        "status": "validated",
        "purpose": (
            "Standalone Visual, Pedagogical & Scientific Presentation (HTML-PPT / Editable PPTX) "
            "Anti-Goodhart Verification & Dual-Rubric Scoring Workflow (AWF DesignAG, 18 Automated Design Gates "
            "`D1`-`D18` + Strictly 1-Slide-Per-Step & 1-Hop Topological Slide Lock + Tri-Mode Verification "
            "[Tutor-Driven Design `TDD`, Dual-Stage Grill-Driven Design `GDD` with 3-Part Mechanism Grill & Slide Design MCQ, "
            "and Autonomous Draft + Dual-Evolution] + 7 Redlines `R1`-`R7` + Optoelectronic v3 & Supermolecule 5-Dim "
            "Quantitative Rubrics), layered atop `skill.anti-goodhart-verification@3.6.0-rc.1`."
        ),
        "entry_skills": [
            "skill.design-anti-goodhart",
            "skill.anti-goodhart-verification",
        ],
        "stages": [
            {
                "id": "storyboard-single-slide-microstep-trimode-capsule-and-layout-diversity-planning-d16",
                "required": True,
                "skill": "skill.design-anti-goodhart",
            },
            {
                "id": "static-dom-latex-copywriting-acronym-and-anti-fake-visual-breaker-d1-to-d6",
                "required": True,
                "skill": "skill.design-anti-goodhart",
            },
            {
                "id": "geometric-bounding-box-whitespace-com-aspect-crop-and-contrast-audit-d7-to-d12",
                "required": True,
                "skill": "skill.design-anti-goodhart",
            },
            {
                "id": "pedagogical-narrative-causal-why-chain-interactive-physics-and-redblue-dual-rubric-seal-d13-to-d18",
                "required": True,
                "skill": "skill.design-anti-goodhart",
            },
        ],
        "engineering_gate": (
            "Strictly enforce 1-Slide-Per-Step micro-step generation (`max_slides_generated_per_step == 1`), "
            "1-Hop Slide Topological Lock (`unverified_slide_hop_distance == 1`), and Tri-Mode verification "
            "(`verify_tdd_station_capsule_completeness`, `verify_grill_station_capsule_completeness` [enforcing "
            "3-part mechanism grill, anti-rubber-stamp re-grill, bottleneck-to-slide mapping, and Slide Design MCQ], "
            "`verify_dual_evolution_feedback_receipt`); forbid all D1-D18 and R1-R7 violations."
        ),
        "scientific_gate": (
            "All scientific presentations and interactive teaching decks must pass all 18 DesignAG gates (`D1`-`D18`), "
            "generate and verify strictly 1 slide per step (`max_slides_generated_per_step == 1`), trigger zero Redlines (`R1`-`R7`), "
            "achieve >= 80/100 on both Optoelectronic v3 (`A_i = w_i * C_clarity * V_visual`) and Supermolecule 5-Dim "
            "quantitative rubrics, and satisfy Layer-1 `skill.anti-goodhart-verification@3.6.0-rc.1` self-hosting integrity (`--audit-self`)."
        ),
        "version_lock": "versions.lock",
    }


def register_all(awf_root: Path) -> Dict[str, Any]:
    comp_id = "skill.design-anti-goodhart"
    rel_id = "1.0.0-rc.5"
    wf_id = "design-anti-goodhart"
    source_rel = f"components/skills/design-anti-goodhart/releases/{rel_id}/source"
    source_dir = awf_root / source_rel
    comp_descriptor_rel = "components/skills/design-anti-goodhart/component.yaml"
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
    comp_doc.setdefault("releases", {})[rel_id] = release_meta
    write_json_yaml(comp_descriptor_path, comp_doc)
    comp_sha = verify.file_sha256(comp_descriptor_path)
    metadata_sha256 = verify.canonical_object_sha256(release_meta)

    attest_rel = "attestations/release-integrity-20261108-design-anti-goodhart-v1-0-rc5.yaml"
    attest_path = awf_root / attest_rel
    attest_doc = {
        "schema_version": 1,
        "digest_contract": "awf-tree-v2",
        "observed_at": "2026-11-08",
        "owner": "awf-design-anti-goodhart-release-20261108-v1-0-rc5",
        "provenance": "Validated release 1.0.0-rc.5 of AWF DesignAG (`skill.design-anti-goodhart@1.0.0-rc.5` and workflow `design-anti-goodhart@1.0.0-rc.5`, enforcing Dual-Stage Grill-Driven Design with 3-Part Mechanism Grill, Anti-Rubber-Stamp Re-Grill, Bottleneck-to-Slide Mapping, and Slide Design MCQ).",
        "releases": {
            f"{comp_id}@{rel_id}": {
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

    wf_descriptor_rel = f"workflows/{wf_id}/releases/{rel_id}/workflow.yaml"
    wf_lock_rel = f"workflows/{wf_id}/releases/{rel_id}/versions.lock"
    wf_descriptor_path = awf_root / wf_descriptor_rel
    wf_lock_path = awf_root / wf_lock_rel

    write_json_yaml(wf_descriptor_path, build_workflow_descriptor())
    lock_doc = {
        "schema_version": 1,
        "workflow": wf_id,
        "workflow_release": rel_id,
        "locked_at": "2026-11-08",
        "components": {
            comp_id: rel_id,
            "skill.anti-goodhart-verification": "3.6.0-rc.1",
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
            c["latest_release"] = rel_id
            break

    if attest_rel not in reg["integrity_attestations"]:
        reg["integrity_attestations"].append(attest_rel)

    req_list: List[str] = reg["integrity_policy"]["required_release_attestations"]
    ref_str = f"{comp_id}@{rel_id}"
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
            w.setdefault("releases", {})[rel_id] = {
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
        "legacy_tree_sha256": legacy_hash,
        "v2_tree_sha256": v2_hash,
        "component_sha256": comp_sha,
        "workflow_sha256": wf_sha,
        "lock_sha256": lock_sha,
    }


if __name__ == "__main__":
    res = register_all(AWF_ROOT)
    print(json.dumps(res, indent=2))
