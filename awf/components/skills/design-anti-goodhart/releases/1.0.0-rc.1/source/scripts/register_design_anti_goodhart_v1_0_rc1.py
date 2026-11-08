#!/usr/bin/env python3
"""
Co-located AWF registration script for `skill.design-anti-goodhart@1.0.0-rc.1`
and standalone workflow `design-anti-goodhart@1.0.0-rc.1` (AWF DesignAG).
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
            "skill.anti-goodhart-verification@3.4.0-rc.1",
        ],
        "runtime_requirements": [
            "UTF-8 Markdown Skill loader (Antigravity / Codex / Pi / Grok)",
            "Python 3.9+ for executing scripts/awf_design_anti_goodhart_gates.py",
        ],
        "capabilities": [
            "visual-pedagogical-and-html-ppt-anti-goodhart-18-gate-verification-engine",
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
            "Initial release 1.0.0-rc.1 of AWF DesignAG (`skill.design-anti-goodhart@1.0.0-rc.1`), "
            "codifying 18 automated visual/pedagogical/PPT Anti-Goodhart gates (`D1`-`D18`), 7 Redlines (`R1`-`R7`), "
            "and dual quantitative rubrics (`01_optoelectronic_scoring_criteria_v3.md` + "
            "`02_supermolecule_SCORING_CRITERIA_5dim.md` with 39 real user feedback items) on top of "
            "`skill.anti-goodhart-verification@3.4.0-rc.1`."
        ),
    }


def build_workflow_descriptor() -> Dict[str, Any]:
    return {
        "schema_version": 1,
        "id": "design-anti-goodhart",
        "release": "1.0.0-rc.1",
        "status": "validated",
        "purpose": (
            "Standalone Visual, Pedagogical & Scientific Presentation (HTML-PPT / Editable PPTX) "
            "Anti-Goodhart Verification & Dual-Rubric Scoring Workflow (AWF DesignAG, 18 Automated Design Gates "
            "`D1`-`D18` + 7 Redlines `R1`-`R7` + Optoelectronic v3 & Supermolecule 5-Dim Quantitative Rubrics), "
            "layered atop `skill.anti-goodhart-verification@3.4.0-rc.1`."
        ),
        "entry_skills": [
            "skill.design-anti-goodhart",
            "skill.anti-goodhart-verification",
        ],
        "stages": [
            {
                "id": "storyboard-microstep-and-layout-diversity-planning-d16",
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
            "Forbid unrendered raw LaTeX tokens (`$`, `\\frac`, `\\sigma`) or missing KaTeX/MathJax (`D1`/`R1`), "
            "unclosed HTML tags or 3+1/4+1 orphan grid rows (`D2`/`R2`), excessive corner quotes (`「」>3/slide`), "
            "hollow AI clichés (`赋能/抓手/闭环`), meta-evaluations (`这很深刻`), or prompt residue (`D3`/`R5`), "
            "undefined acronyms or standalone glossary walls (`D4`), cartoon emojis (`🎯💡🚀`), unanchored fake CSS "
            "progress bars, AI text-to-image decorative mechanism fakes, or AI watermarks (`D5`/`R4`), default-visible "
            "teleprompters or slide scrollbars (`D6`/`R6`), overlapping or clipped bounding boxes (`D7`/`R2`), "
            "canvas overcrowding (`coverage>0.82`) or top-heavy imbalance (`y_cm<0.38`) (`D8`), stretched/squashed "
            "aspect ratios (`D9`), dirty sub-panel crops (`D10`), unreferenced figures (`D11`/`R3`), low WCAG contrast "
            "or cyberpunk neon glow (`D12`), missing background/prior-art/foreshadowing (`D13`), superficial why-chains (`D14`/`R7`), "
            "hollow animations or non-physical sliders (`D15`), single-shot full-deck generation or repetitive card walls (`D16`), "
            "pure-text V0 laziness escaping the 30% multiplicative cap (`D17`), and unverified visual claims without "
            "rendered 1920x1080 PNG Red-Blue adversarial review (`D18`)."
        ),
        "scientific_gate": (
            "All scientific presentations and interactive teaching decks must pass all 18 DesignAG gates (`D1`-`D18`), "
            "trigger zero Redlines (`R1`-`R7`), achieve >= 80/100 on both Optoelectronic v3 (`A_i = w_i * C_clarity * V_visual`) "
            "and Supermolecule 5-Dim quantitative rubrics, and satisfy Layer-1 `skill.anti-goodhart-verification@3.4.0-rc.1` "
            "self-hosting integrity (`--audit-self`)."
        ),
        "version_lock": "versions.lock",
    }


def register_all(awf_root: Path) -> Dict[str, Any]:
    comp_id = "skill.design-anti-goodhart"
    rel_id = "1.0.0-rc.1"
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
    comp_doc = {
        "schema_version": 1,
        "id": comp_id,
        "kind": "skill",
        "releases": {rel_id: release_meta},
    }
    write_json_yaml(comp_descriptor_path, comp_doc)
    comp_sha = verify.file_sha256(comp_descriptor_path)
    metadata_sha256 = verify.canonical_object_sha256(release_meta)

    attest_rel = "attestations/release-integrity-20261108-design-anti-goodhart-v1-0-rc1.yaml"
    attest_path = awf_root / attest_rel
    attest_doc = {
        "schema_version": 1,
        "digest_contract": "awf-tree-v2",
        "observed_at": "2026-11-08",
        "owner": "awf-design-anti-goodhart-release-20261108-v1-0-rc1",
        "provenance": "Validated initial release 1.0.0-rc.1 of AWF DesignAG (`skill.design-anti-goodhart@1.0.0-rc.1` and workflow `design-anti-goodhart@1.0.0-rc.1`, 18 automated visual/pedagogical/PPT gates + 7 Redlines + Dual Quantitative Rubrics).",
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
            "skill.anti-goodhart-verification": "3.4.0-rc.1",
        },
    }
    write_json_yaml(wf_lock_path, lock_doc)
    wf_sha = verify.file_sha256(wf_descriptor_path)
    lock_sha = verify.file_sha256(wf_lock_path)

    reg_path = awf_root / "registry.yaml"
    reg = verify.read_manifest(reg_path)
    comps: List[Dict[str, Any]] = reg["components"]
    comp_entry = {
        "descriptor": comp_descriptor_rel,
        "descriptor_sha256": comp_sha,
        "id": comp_id,
        "kind": "skill",
        "latest_release": rel_id,
    }
    replaced = False
    for idx, c in enumerate(comps):
        if c.get("id") == comp_id:
            comps[idx] = comp_entry
            replaced = True
            break
    if not replaced:
        comps.append(comp_entry)
        comps.sort(key=lambda x: str(x.get("id", "")))

    if attest_rel not in reg["integrity_attestations"]:
        reg["integrity_attestations"].append(attest_rel)

    req_list: List[str] = reg["integrity_policy"]["required_release_attestations"]
    ref_str = f"{comp_id}@{rel_id}"
    if ref_str not in req_list:
        req_list.append(ref_str)
        req_list.sort()

    wf_entry = {
        "id": wf_id,
        "display_name": "AWF DesignAG",
        "aliases": [
            "DesignAG",
            "design-ag",
            "designag",
            "AWF DesignAG",
            "awf designag",
            "AWF DesignGuard",
            "design-guard",
            "ppt-ag",
            "PPT-AG",
            "PPT门禁",
            "设计门禁",
            "PPT防偷懒",
            "design-anti-goodhart",
        ],
        "descriptor": wf_descriptor_rel,
        "descriptor_sha256": wf_sha,
        "lock": wf_lock_rel,
        "lock_sha256": lock_sha,
        "status": "validated",
        "releases": {
            rel_id: {
                "descriptor": wf_descriptor_rel,
                "descriptor_sha256": wf_sha,
                "lock": wf_lock_rel,
                "lock_sha256": lock_sha,
                "status": "validated",
            }
        },
    }
    wfs: List[Dict[str, Any]] = reg["workflows"]
    wf_replaced = False
    for idx, w in enumerate(wfs):
        if w.get("id") == wf_id:
            wfs[idx] = wf_entry
            wf_replaced = True
            break
    if not wf_replaced:
        wfs.append(wf_entry)
        wfs.sort(key=lambda x: str(x.get("id", "")))

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
    print(json.dumps(register_all(AWF_ROOT), indent=2, ensure_ascii=False))
