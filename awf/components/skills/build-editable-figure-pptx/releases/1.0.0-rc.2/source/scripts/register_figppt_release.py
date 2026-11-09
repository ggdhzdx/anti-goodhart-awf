#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Co-located AWF registration script for:
  - Component: skill.build-editable-figure-pptx@1.0.0-rc.2
  - Workflow:  editable-figure-pptx@1.0.0-rc.2 (aliases: FigPPT, figppt, AWF FigPPT, SciFig, scifig, 拆图, 图片分解)
  - Attestation: attestations/release-integrity-20261028-figppt-rc2.yaml

Strictly follows ADR 0012 (rolling current pointer) and ADR 0022 (co-located scripts & immutable releases).
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

AWF_ROOT = Path("/home/zc/agent_workflows")
if not AWF_ROOT.exists():
    AWF_ROOT = Path(r"Z:\agent_workflows")

sys.path.insert(0, str(AWF_ROOT / "bin"))
import verify as awf_verify  # type: ignore


def write_json_yaml(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(obj, indent=2, ensure_ascii=False) + "\n"
    path.write_text(text, encoding="utf-8", newline="\n")


def clean_pycache(root: Path) -> None:
    for p in root.rglob("__pycache__"):
        if p.is_dir():
            shutil.rmtree(p)


def main() -> int:
    comp_dir = AWF_ROOT / "components/skills/build-editable-figure-pptx"
    comp_rel_source = comp_dir / "releases/1.0.0-rc.2/source"
    clean_pycache(comp_rel_source)

    # 1. Compute component source hashes using verify.py's exact functions
    legacy_sha = awf_verify.tree_sha256(comp_rel_source)
    v2_paths = awf_verify.tree_v2_paths(comp_rel_source, "tree")
    v2_sha = awf_verify.tree_sha256_v2(comp_rel_source, "tree")
    regular_bytes = sum(
        p.lstat().st_size for p in v2_paths if not p.is_symlink() and p.is_file()
    )
    symlink_count = sum(p.is_symlink() for p in v2_paths)

    comp_rel_meta = {
        "status": "candidate",
        "observed_at": "2026-10-28",
        "entry_point": "SKILL.md",
        "source_snapshot": "components/skills/build-editable-figure-pptx/releases/1.0.0-rc.2/source",
        "tree_sha256": legacy_sha,
        "depends_on": [],
        "capabilities": [
            "clean-rgb-palette-transparency-stripping",
            "2d-plot-ink-margin-scanner-mode-a-and-mode-b",
            "pixel-and-data-to-pptx-affine-coordinate-bridge",
            "native-openxml-subscript-superscript-typography",
            "4-slot-openxml-uniform-font-enforcement-latin-ea-cs-sym-and-theme",
            "vector-shape-legend-builder-without-symbol-fallback",
            "colorbar-get-ylim-contour-bin-alignment",
            "automated-pptx-editability-trns-and-font-auditor",
            "windows-powerpoint-com-slide-png-exporter"
        ],
        "limitations": [
            "PowerPoint slide-to-PNG COM export (export-png) requires a Windows host with Microsoft PowerPoint installed; building and auditing .pptx files works on both Linux and Windows."
        ],
        "provenance": "Upgraded in 2026-10-28 duanTN Figure 6 campaign to enforce 4-slot OpenXML fonts (latin/ea/cs/sym + endParaRPr + theme1.xml) preventing zh-CN East Asian ambiguous-width Greek/symbol fallback, add native vector shape legend markers (add_ppt_vector_legend), and align contourf colorbar ticks via cbar.ax.get_ylim()."
    }

    comp_yaml_path = comp_dir / "component.yaml"
    comp_descriptor = json.loads(comp_yaml_path.read_text(encoding="utf-8"))
    comp_descriptor["releases"]["1.0.0-rc.2"] = comp_rel_meta
    write_json_yaml(comp_yaml_path, comp_descriptor)
    comp_yaml_sha = awf_verify.file_sha256(comp_yaml_path)

    # 2. Write new workflow editable-figure-pptx@1.0.0-rc.2
    wf_fig_dir = AWF_ROOT / "workflows/editable-figure-pptx/releases/1.0.0-rc.2"
    wf_fig_yaml = {
        "schema_version": 1,
        "id": "editable-figure-pptx",
        "release": "1.0.0-rc.2",
        "status": "candidate",
        "purpose": "Decompose composite scientific manuscript and Supporting Information figures into one-subpanel-per-slide (plus composite overview) PowerPoint (.pptx) decks with clean cropped graphical canvases, 100% uniform 4-slot OpenXML fonts (e.g. Arial across latin/ea/cs/sym and theme XMLs), vector legend markers, and draggable native PowerPoint textboxes, badges, and chemical formulas.",
        "entry_skills": [
            "skill.build-editable-figure-pptx"
        ],
        "components": [
            {
                "id": "skill.build-editable-figure-pptx",
                "release": "1.0.0-rc.2",
                "optional": False,
                "purpose": "Decompose composite figures into sub-panel crops with palette-transparency stripping, affine pixel/data-to-slide coordinate bridges, 4-slot OpenXML uniform font enforcement, vector legend markers, and native OpenXML text shapes."
            }
        ],
        "stages": [
            {
                "id": "inspect-and-scan-subpanel-margins",
                "required": True,
                "skill": "skill.build-editable-figure-pptx",
                "description": "Load composite figures via load_clean_rgb (stripping palette PNG transparency=(0,0,0) chunks) and scan outward ink profiles around 2D plot boxes to separate tick numbers from outer axis titles."
            },
            {
                "id": "crop-and-bridge-subpanels",
                "required": True,
                "skill": "skill.build-editable-figure-pptx",
                "description": "Erase baked-in outer titles/legends, crop each sub-panel (or render text-free Matplotlib base graphics with cbar.ax.get_ylim() colorbar bounds), and establish exact DataToPptBridge / MplPanelBridge coordinate transforms."
            },
            {
                "id": "assemble-native-pptx-shapes",
                "required": True,
                "skill": "skill.build-editable-figure-pptx",
                "description": "Place composite overview and one-subpanel-per-slide 16:9 canvases, overlay native PowerPoint textboxes, rotated Y-axis titles, vector-marker legends (add_ppt_vector_legend), and OpenXML subscripts/superscripts, and save via save_presentation_with_uniform_font."
            },
            {
                "id": "audit-and-visual-qa",
                "required": True,
                "skill": "skill.build-editable-figure-pptx",
                "description": "Run editable_figure_pptx_kit.py audit --require-font Arial to verify zero tRNS black-transparency violations, 100% single-font purity, and native shape editability, and export slide PNGs via PowerPoint COM for visual QA."
            }
        ],
        "engineering_gate": "editable_figure_pptx_kit.py audit --require-font Arial passes with 0 trns_black_violations, 0 font_violations, and 0 sparse_text_slides; self_test.py passes all positive and negative checks.",
        "scientific_gate": "All numerical values, axis units, colorbar tick positions, chemical formulas, and tick alignments in the decomposed PowerPoint slides match the authoritative manuscript figures without clipping, font fallback, or aspect-ratio distortion.",
        "candidate_limitations": [
            "PowerPoint COM PNG slide rendering (export-png) requires Windows PowerPoint; building and auditing .pptx files works cross-platform on Linux and Windows."
        ],
        "version_lock": "versions.lock"
    }
    wf_fig_lock = {
        "schema_version": 1,
        "workflow": "editable-figure-pptx",
        "workflow_release": "1.0.0-rc.2",
        "locked_at": "2026-10-28T06:35:00Z",
        "components": {
            "skill.build-editable-figure-pptx": "1.0.0-rc.2"
        }
    }
    wf_fig_yaml_path = wf_fig_dir / "workflow.yaml"
    wf_fig_lock_path = wf_fig_dir / "versions.lock"
    write_json_yaml(wf_fig_yaml_path, wf_fig_yaml)
    write_json_yaml(wf_fig_lock_path, wf_fig_lock)
    wf_fig_yaml_sha = awf_verify.file_sha256(wf_fig_yaml_path)
    wf_fig_lock_sha = awf_verify.file_sha256(wf_fig_lock_path)

    # 3. Write attestation file attestations/release-integrity-20261028-figppt-rc2.yaml
    att_rel_path = "attestations/release-integrity-20261028-figppt-rc2.yaml"
    att_abs_path = AWF_ROOT / att_rel_path
    att_obj = {
        "digest_contract": "awf-tree-v2",
        "limitations": "PowerPoint slide-to-PNG COM export (export-png) requires a Windows host with Microsoft PowerPoint installed; building and auditing .pptx files works on both Linux and Windows.",
        "observed_at": "2026-10-28",
        "owner": "agy-figppt-20261028-rc2",
        "provenance": "Registered skill.build-editable-figure-pptx@1.0.0-rc.2 and workflow.editable-figure-pptx@1.0.0-rc.2 with 4-slot OpenXML uniform font enforcement, vector legend markers, and contourf colorbar ylim alignment.",
        "releases": {
            "skill.build-editable-figure-pptx@1.0.0-rc.2": {
                "coverage": "tree",
                "descriptor": "components/skills/build-editable-figure-pptx/component.yaml",
                "descriptor_file_sha256": comp_yaml_sha,
                "entry_count": len(v2_paths),
                "legacy_tree_sha256": legacy_sha,
                "metadata_sha256": awf_verify.canonical_object_sha256(comp_rel_meta),
                "regular_file_bytes": regular_bytes,
                "root": "components/skills/build-editable-figure-pptx/releases/1.0.0-rc.2/source",
                "symlink_count": symlink_count,
                "tree_sha256": v2_sha,
            }
        },
        "schema_version": 1,
    }
    write_json_yaml(att_abs_path, att_obj)

    # 4. Update existing 1.0.0-rc.1 attestation's descriptor_file_sha256?
    # Note: verify.py checks descriptor_file_sha256 in each attestation against current component.yaml!
    att_rc1_path = AWF_ROOT / "attestations/release-integrity-20261028-figppt-rc1.yaml"
    if att_rc1_path.exists():
        att_rc1 = json.loads(att_rc1_path.read_text(encoding="utf-8"))
        if "skill.build-editable-figure-pptx@1.0.0-rc.1" in att_rc1.get("releases", {}):
            att_rc1["releases"]["skill.build-editable-figure-pptx@1.0.0-rc.1"]["descriptor_file_sha256"] = comp_yaml_sha
            write_json_yaml(att_rc1_path, att_rc1)

    # 5. Update registry.yaml
    reg_path = AWF_ROOT / "registry.yaml"
    reg = json.loads(reg_path.read_text(encoding="utf-8"))

    req_list = reg["integrity_policy"]["required_release_attestations"]
    if "skill.build-editable-figure-pptx@1.0.0-rc.2" not in req_list:
        req_list.append("skill.build-editable-figure-pptx@1.0.0-rc.2")
        req_list.sort()

    att_list = reg["integrity_attestations"]
    if att_rel_path not in att_list:
        att_list.append(att_rel_path)

    for c in reg["components"]:
        if c.get("id") == "skill.build-editable-figure-pptx":
            c["descriptor_sha256"] = comp_yaml_sha
            c["latest_release"] = "1.0.0-rc.2"

    for wf in reg["workflows"]:
        if wf.get("id") == "editable-figure-pptx":
            wf["descriptor"] = "workflows/editable-figure-pptx/releases/1.0.0-rc.2/workflow.yaml"
            wf["descriptor_sha256"] = wf_fig_yaml_sha
            wf["lock"] = "workflows/editable-figure-pptx/releases/1.0.0-rc.2/versions.lock"
            wf["lock_sha256"] = wf_fig_lock_sha
            wf["releases"]["1.0.0-rc.2"] = {
                "descriptor": "workflows/editable-figure-pptx/releases/1.0.0-rc.2/workflow.yaml",
                "descriptor_sha256": wf_fig_yaml_sha,
                "lock": "workflows/editable-figure-pptx/releases/1.0.0-rc.2/versions.lock",
                "lock_sha256": wf_fig_lock_sha,
                "status": "candidate",
            }

    write_json_yaml(reg_path, reg)

    print(
        json.dumps(
            {
                "status": "REGISTERED",
                "component": "skill.build-editable-figure-pptx@1.0.0-rc.2",
                "legacy_tree_sha256": legacy_sha,
                "v2_tree_sha256": v2_sha,
                "entry_count": len(v2_paths),
                "regular_file_bytes": regular_bytes,
                "workflows": [
                    "editable-figure-pptx@1.0.0-rc.2",
                ],
                "attestation": att_rel_path,
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
