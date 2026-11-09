#!/usr/bin/env python3
"""
Co-located AWF Release Registration Script for AWF Tutor / SciTutor
(adaptive-interactive-tutor@1.0.0-rc.18 / V16 Tri-Mode Dual-Stage GDD Edition).
Strictly follows ADR 0012 and ADR 0022.
Locks `skill.anti-goodhart-verification@3.6.0-rc.1` (73 automated gates),
`skill.design-anti-goodhart@1.0.0-rc.5` (18 automated DesignAG gates + Dual-Stage GDD D16),
and `skill.html-ppt@1.0.0-rc.7` (Tri-Mode `TDD` / Dual-Stage `GRILL` / `AUTONOMOUS_DUAL_EVOLVE` 1-Slide-Per-Step Enforcer).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict

sys.dont_write_bytecode = True

AWF_ROOT = Path("/home/zc/agent_workflows")
if not AWF_ROOT.exists():
    AWF_ROOT = Path(r"Z:\agent_workflows")
sys.path.insert(0, str(AWF_ROOT / "bin"))

import verify  # type: ignore


def write_json_yaml(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def build_release_meta(
    source_rel: str,
    legacy_hash: str,
    guard_id: str,
    guard_rel: str,
    design_ag_id: str,
    design_ag_rel: str,
    html_ppt_id: str,
    html_ppt_rel: str,
) -> Dict[str, Any]:
    return {
        "status": "validated",
        "observed_at": "2026-11-08",
        "entry_point": "SKILL.md",
        "source_snapshot": source_rel,
        "tree_sha256": legacy_hash,
        "depends_on": [
            f"{guard_id}@{guard_rel}",
            f"{design_ag_id}@{design_ag_rel}",
            f"{html_ppt_id}@{html_ppt_rel}",
        ],
        "runtime_requirements": [
            "UTF-8 Markdown Skill loader (Antigravity / Codex / Pi / Grok)",
            f"Standalone {guard_id}@{guard_rel} (AWF Guard, 73 automated gates) for 7-Gate, @scientific_atom, 6D micro-step anchoring, and Red-Blue adversarial verification",
            f"Standalone {design_ag_id}@{design_ag_rel} (AWF DesignAG, 18 automated design gates + dual rubrics + Dual-Stage GDD verification)",
            f"Standalone {html_ppt_id}@{html_ppt_rel} (AWF HTML-PPT V3 Tri-Mode `TDD`, Dual-Stage `GRILL`, `AUTONOMOUS_DUAL_EVOLVE` 1-Slide-Per-Step enforcer)",
            "Browser for on-demand interactive HTML micro-labs and HTML-PPT rendered-page review",
        ],
        "capabilities": [
            "scale-adaptive-fractal-curriculum-tree-chapter-station-microloop",
            "persistent-master-syllabus-and-station-progress-checklist",
            "seven-element-methodological-anatomy-per-station",
            "dual-speed-sequential-and-random-access-station-navigation",
            "wittgenstein-ladder-bridge-deconstruct-replace",
            "vygotsky-zpd-scaffolding-and-prerequisite-tracing",
            "predict-observe-explain-and-harvard-case-cognitive-disequilibrium",
            "feynman-and-think-aloud-act-r-dual-system-synthesis",
            "dual-coding-visual-and-diagrammatic-scaffolding-mermaid-ascii-visual-cloze",
            "human-gated-multimedia-escalation-images-animations-interactive-html-microlabs",
            "bottom-up-micro-to-macro-zoom-out-and-macro-landscape-positioning",
            "upstream-downstream-lateral-causal-lineage-mapping",
            "open-world-unbiased-cross-domain-structural-isomorphism-hyperlinking",
            "tutor-driven-design-and-bidirectional-feynman-alignment-co-evolution",
            "dual-stage-grill-driven-design-3part-mechanism-grill-and-slide-design-mcq",
            "autonomous-headdown-build-with-postreview-ppt-and-awf-dual-evolution",
            "station-to-slide-isomorphic-tdd-html-ppt-co-design-and-human-signoff",
            "modular-delegation-to-standalone-skill-anti-goodhart-verification-v3-6",
            "modular-delegation-to-standalone-skill-design-anti-goodhart-v1-0",
            "static-negative-infinity-placeholder-and-magic-number-circuit-breaking",
            "conservation-symmetry-analytic-gradient-and-convergence-order-property-testing",
            "six-dimensional-microstep-granularity-and-one-hop-dag-topological-anchoring",
            "red-blue-adversarial-subagent-decoupled-audit-for-station-capsules",
            "automatic-station-gate-awf-release-and-cognitive-ledger-writeback-anti-amnesia",
            "human-cognitive-trajectory-ledger-recording",
            "cognitive-isomorphic-html-ppt-slide-deck-synthesis-with-designag-18gate-audit",
        ],
        "limitations": [
            "Interactive pedagogical and co-design workflow requires multi-turn user dialogue in TDD and GRILL modes",
            "Heavy multimedia assets (images, animations, interactive web pages) are strictly human-gated (built only after user confirmation or explicit user request)",
            "Scientific and domain claims during STEM tutoring and HTML-PPT generation must remain grounded in verified physical/mathematical mechanisms",
        ],
        "provenance": (
            f"Adaptive Interactive Tutor V16 (1.0.0-rc.18) locking to `{guard_id}@{guard_rel}` (73 automated gates), "
            f"`{design_ag_id}@{design_ag_rel}` (18 automated DesignAG gates + Dual Quantitative Rubrics + Dual-Stage GDD D16), and "
            f"`{html_ppt_id}@{html_ppt_rel}` (Tri-Mode `TDD`, Dual-Stage `GRILL` [3-Part Mechanism Grill + Slide Design MCQ], and `AUTONOMOUS_DUAL_EVOLVE`)."
        ),
    }


def build_workflow_doc(
    wf_id: str,
    rel_id: str,
    comp_id: str,
    guard_id: str,
    guard_rel: str,
    design_ag_id: str,
    design_ag_rel: str,
    html_ppt_id: str,
    html_ppt_rel: str,
) -> Dict[str, Any]:
    return {
        "schema_version": 1,
        "id": wf_id,
        "release": rel_id,
        "status": "validated",
        "purpose": (
            "Bidirectional interactive pedagogical, Scale-Adaptive Fractal Curriculum (Chapter -> Station -> "
            "3-Gate Micro-Loop for Mega-Projects), 7-Element Methodological Anatomy, and Tri-Mode Co-Design Engine "
            "(`TDD` Tutor-Driven Design, `GRILL` Dual-Stage Grill-Driven Design with 3-Part Mechanism Grill, "
            "Anti-Rubber-Stamp Re-Grill & Slide Design MCQ, and `AUTONOMOUS_DUAL_EVOLVE` Head-Down Build + Post-Review "
            f"PPT & AWF Dual-Evolution), delegating 73-Gate scientific/code verification to {guard_id}@{guard_rel}, "
            f"18-Gate visual/pedagogical/PPT verification to {design_ag_id}@{design_ag_rel} (AWF DesignAG), and "
            f"Tri-Mode 1-Slide-Per-Step HTML-PPT generation to {html_ppt_id}@{html_ppt_rel}."
        ),
        "entry_skills": [comp_id, guard_id, design_ag_id, html_ppt_id],
        "stages": [
            {
                "id": "scope-cardinality-and-trimode-triage-fractal-syllabus-and-manifests",
                "required": True,
                "skill": comp_id,
            },
            {
                "id": "seven-element-station-anatomy-or-dualstage-grill-loop",
                "required": True,
                "skill": comp_id,
            },
            {
                "id": "human-gated-multimedia-testbed-escalation",
                "condition": "Only when the user explicitly confirms the tutor's multimedia offer OR proactively requests an image, animation, or interactive web demonstration.",
                "required": False,
                "skill": comp_id,
            },
            {
                "id": "atomic-capsule-implementation-poe-tier1-guard-and-tdd",
                "required": True,
                "skill": guard_id,
            },
            {
                "id": "tier2-universal-7-gate-anti-goodhart-seal-and-station-checkoff",
                "required": True,
                "skill": guard_id,
            },
            {
                "id": "micro-to-macro-zoom-out-open-world-hyperlinking-and-tdd-solidification",
                "required": True,
                "skill": comp_id,
            },
            {
                "id": "trimode-tdd-dualstage-grill-or-autonomous-html-ppt-synthesis-and-postreview-dual-evolution",
                "condition": "When building or evolving a 16:9 interactive HTML presentation deck via TDD, Dual-Stage GRILL, or AUTONOMOUS_DUAL_EVOLVE mode under AWF HTML-PPT + AWF DesignAG (18 gates + Dual Rubrics).",
                "required": False,
                "skill": design_ag_id,
            },
        ],
        "engineering_gate": (
            f"For Mega-Projects (N > 5 methods), forbid flat 3-4 Loop compression and 1,000+ line monolithic scripts; "
            f"invoke {guard_id}@{guard_rel} (73 gates) for @scientific_atom capsule verification and {design_ag_id}@{design_ag_rel} "
            f"(18 DesignAG gates + 7 Redlines) + {html_ppt_id}@{html_ppt_rel} (Tri-Mode `TDD`, Dual-Stage `GRILL` [3-Part Mechanism "
            f"Grill + Anti-Rubber-Stamp Re-Grill + Bottleneck-to-Slide Mapping + Slide Design MCQ], `AUTONOMOUS_DUAL_EVOLVE` "
            f"1-Slide-Per-Step Enforcer) for interactive HTML-PPT verification; strictly enforce the Human Gate before "
            f"generating heavy multimedia; and persist all deliverables inside the project workspace with dual Windows/file:/// paths."
        ),
        "scientific_gate": (
            f"All atomic operator capsules must pass {guard_id}@{guard_rel} (73 automated gates) and all HTML-PPT / visual "
            f"teaching artifacts must pass {design_ag_id}@{design_ag_rel} (18 automated DesignAG gates + zero Redlines + >=80/100 Dual Rubrics)."
        ),
        "version_lock": "versions.lock",
    }


def main() -> int:
    comp_id = "skill.adaptive-interactive-tutor"
    guard_id = "skill.anti-goodhart-verification"
    guard_rel = "3.6.0-rc.1"
    design_ag_id = "skill.design-anti-goodhart"
    design_ag_rel = "1.0.0-rc.5"
    html_ppt_id = "skill.html-ppt"
    html_ppt_rel = "1.0.0-rc.7"
    wf_id = "adaptive-interactive-tutor"
    rel_id = "1.0.0-rc.18"

    source_rel = f"components/skills/adaptive-interactive-tutor/releases/{rel_id}/source"
    source_dir = AWF_ROOT / source_rel
    if not source_dir.is_dir():
        raise RuntimeError(f"Missing source directory: {source_dir}")

    legacy_hash = verify.tree_sha256(source_dir)
    v2_hash = verify.tree_sha256_v2(source_dir, "tree")
    v2_paths = verify.tree_v2_paths(source_dir, "tree")
    regular_bytes = sum(
        p.lstat().st_size for p in v2_paths if not p.is_symlink() and p.is_file()
    )
    symlink_count = sum(p.is_symlink() for p in v2_paths)

    release_meta = build_release_meta(
        source_rel,
        legacy_hash,
        guard_id,
        guard_rel,
        design_ag_id,
        design_ag_rel,
        html_ppt_id,
        html_ppt_rel,
    )

    comp_descriptor_rel = "components/skills/adaptive-interactive-tutor/component.yaml"
    comp_descriptor_path = AWF_ROOT / comp_descriptor_rel
    comp_doc = verify.read_manifest(comp_descriptor_path)
    comp_doc.setdefault("releases", {})[rel_id] = release_meta
    write_json_yaml(comp_descriptor_path, comp_doc)
    comp_sha = verify.file_sha256(comp_descriptor_path)

    metadata_sha256 = verify.canonical_object_sha256(release_meta)
    attestation_rel = "attestations/release-integrity-20261108-adaptive-interactive-tutor-rc18.yaml"
    attestation_path = AWF_ROOT / attestation_rel
    attestation_doc = {
        "schema_version": 1,
        "digest_contract": "awf-tree-v2",
        "observed_at": "2026-11-08",
        "owner": "awf-adaptive-interactive-tutor-release-20261108-rc18",
        "provenance": (
            f"Validated release 1.0.0-rc.18 of AWF Tutor / SciTutor (skill.adaptive-interactive-tutor@1.0.0-rc.18 / V16 Dual-Stage GDD) "
            f"locking to {guard_id}@{guard_rel} (73 gates), {design_ag_id}@{design_ag_rel} (18 DesignAG gates + Dual-Stage GDD D16), "
            f"and {html_ppt_id}@{html_ppt_rel} (Tri-Mode `TDD`, Dual-Stage `GRILL` [3-Part Mechanism Grill + Slide Design MCQ], `AUTONOMOUS_DUAL_EVOLVE`)."
        ),
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
    write_json_yaml(attestation_path, attestation_doc)

    wf_descriptor_rel = f"workflows/{wf_id}/releases/{rel_id}/workflow.yaml"
    wf_lock_rel = f"workflows/{wf_id}/releases/{rel_id}/versions.lock"
    wf_descriptor_path = AWF_ROOT / wf_descriptor_rel
    wf_lock_path = AWF_ROOT / wf_lock_rel

    wf_doc = build_workflow_doc(
        wf_id, rel_id, comp_id, guard_id, guard_rel, design_ag_id, design_ag_rel, html_ppt_id, html_ppt_rel
    )
    write_json_yaml(wf_descriptor_path, wf_doc)

    lock_doc = {
        "schema_version": 1,
        "workflow": wf_id,
        "workflow_release": rel_id,
        "locked_at": "2026-11-08",
        "components": {
            comp_id: rel_id,
            guard_id: guard_rel,
            design_ag_id: design_ag_rel,
            html_ppt_id: html_ppt_rel,
        },
    }
    write_json_yaml(wf_lock_path, lock_doc)

    wf_desc_sha = verify.file_sha256(wf_descriptor_path)
    wf_lock_sha = verify.file_sha256(wf_lock_path)

    registry_path = AWF_ROOT / "registry.yaml"
    registry = verify.read_manifest(registry_path)

    for c in registry.get("components", []):
        if c.get("id") == comp_id:
            c["descriptor_sha256"] = comp_sha
            c["latest_release"] = rel_id
            break

    attestations = registry.get("integrity_attestations", [])
    if attestation_rel not in attestations:
        attestations.append(attestation_rel)

    req_list = registry["integrity_policy"]["required_release_attestations"]
    ref_str = f"{comp_id}@{rel_id}"
    if ref_str not in req_list:
        req_list.append(ref_str)
        req_list.sort()

    workflows = registry.get("workflows", [])
    existing_wf_idx = next((i for i, w in enumerate(workflows) if w.get("id") == wf_id), None)
    if existing_wf_idx is None:
        raise RuntimeError(f"Workflow {wf_id} not found in registry.yaml")

    wf_entry = workflows[existing_wf_idx]
    wf_entry["descriptor"] = wf_descriptor_rel
    wf_entry["descriptor_sha256"] = wf_desc_sha
    wf_entry["lock"] = wf_lock_rel
    wf_entry["lock_sha256"] = wf_lock_sha
    wf_entry["status"] = "validated"
    for new_alias in ("adaptive-interactive-tutor-v15", "adaptive-interactive-tutor-v16", "tdd-slide", "TDD-Slide", "grill-driven-design", "GDD"):
        if new_alias not in wf_entry.get("aliases", []):
            wf_entry.setdefault("aliases", []).append(new_alias)
    wf_entry.setdefault("releases", {})[rel_id] = {
        "descriptor": wf_descriptor_rel,
        "descriptor_sha256": wf_desc_sha,
        "lock": wf_lock_rel,
        "lock_sha256": wf_lock_sha,
        "status": "validated",
    }

    write_json_yaml(registry_path, registry)
    print(
        f"Registered {comp_id}@{rel_id} (delegating to {guard_id}@{guard_rel}, "
        f"{design_ag_id}@{design_ag_rel}, and {html_ppt_id}@{html_ppt_rel}) "
        f"and updated rolling current pointer for {wf_id}@{rel_id} successfully."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
