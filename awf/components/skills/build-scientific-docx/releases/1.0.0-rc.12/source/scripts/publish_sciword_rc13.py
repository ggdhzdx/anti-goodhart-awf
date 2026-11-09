#!/usr/bin/env python3
"""
Register and attest AWF SciWord 1.0.0-rc.13 (`workflow.scientific-report-authoring@1.0.0-rc.13`):
  - `skill.edit-scientific-article@1.0.0-rc.10`:
    * Domain-agnostic generalization of all writing and review rules (stripping single-project OPV/battery hardcodings).
    * Lossy-Compression 3-Point Semantic Preservation Gate (No Qualifier Stripping, No Sign-Adjective Polarity Inversion, No Single-Panel Causal Contamination).
    * 4-Role x 3-Round Pre-emptive Peer-Review & Iterative Revision Closed-Loop Protocol.
  - `skill.build-scientific-docx@1.0.0-rc.12`:
    * DOM-safe `<w:drawing>` detection and dynamic template style inheritance for in-place manuscript editing.
    * Residual publisher template placeholder gate (`no_residual_template_placeholders` in `audit_docx.py`).
    * Reusable Word Native Track Changes (`<w:ins>`/`<w:del>`) + Right-Margin Rationale Comments (`<w:comment>`) builder (`scripts/build_track_changes_docx.py`).
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import sys
from typing import Any

AWF_ROOT = Path(os.environ.get("AGENT_WORKFLOWS_ROOT", "/home/zc/agent_workflows")).resolve()
if not (AWF_ROOT / "registry.yaml").is_file():
    AWF_ROOT = Path(__file__).resolve().parents[6]

sys.path.insert(0, str(AWF_ROOT / "bin"))
from verify import (  # noqa: E402
    canonical_object_sha256,
    file_sha256,
    tree_sha256,
    tree_sha256_v2,
    tree_v2_paths,
)


def clean_pycache(root: Path) -> None:
    for pyc in list(root.rglob("__pycache__")) + list(root.rglob(".pytest_cache")):
        if pyc.is_dir():
            shutil.rmtree(pyc)


def compute_attestation_entry(descriptor_rel: str, root_rel: str, release_meta: dict[str, Any]) -> dict[str, Any]:
    desc_path = AWF_ROOT / descriptor_rel
    root_path = AWF_ROOT / root_rel
    v2_paths = tree_v2_paths(root_path, "tree", None, None)
    reg_bytes = sum(p.lstat().st_size for p in v2_paths if not p.is_symlink() and p.is_file())
    sym_cnt = sum(p.is_symlink() for p in v2_paths)
    return {
        "coverage": "tree",
        "descriptor": descriptor_rel,
        "descriptor_file_sha256": file_sha256(desc_path),
        "metadata_sha256": canonical_object_sha256(release_meta),
        "root": root_rel,
        "legacy_tree_sha256": tree_sha256(root_path),
        "tree_sha256": tree_sha256_v2(root_path, "tree", None, None),
        "entry_count": len(v2_paths),
        "regular_file_bytes": reg_bytes,
        "symlink_count": sym_cnt,
    }


def main() -> int:
    edit_src = AWF_ROOT / "components/skills/edit-scientific-article/releases/1.0.0-rc.10/source"
    build_src = AWF_ROOT / "components/skills/build-scientific-docx/releases/1.0.0-rc.12/source"
    clean_pycache(edit_src)
    clean_pycache(build_src)

    # 1. Update skill.edit-scientific-article/component.yaml
    edit_comp_rel = "components/skills/edit-scientific-article/component.yaml"
    edit_comp_path = AWF_ROOT / edit_comp_rel
    edit_comp = json.loads(edit_comp_path.read_text(encoding="utf-8"))
    rc9_edit = edit_comp["releases"]["1.0.0-rc.9"]
    rc10_caps = list(rc9_edit["capabilities"])
    for cap in (
        "domain-agnostic-cross-disciplinary-writing-and-review-rules",
        "lossy-compression-three-point-semantic-preservation-gate",
        "four-role-three-round-preemptive-peer-review-closed-loop",
    ):
        if cap not in rc10_caps:
            rc10_caps.append(cap)

    rc10_edit_meta = {
        "status": "validated",
        "observed_at": "2026-10-28",
        "source_snapshot": "components/skills/edit-scientific-article/releases/1.0.0-rc.10/source",
        "tree_sha256": tree_sha256(edit_src),
        "runtime_requirements": list(rc9_edit["runtime_requirements"]),
        "capabilities": rc10_caps,
        "limitations": list(rc9_edit["limitations"]),
    }
    edit_comp["releases"]["1.0.0-rc.10"] = rc10_edit_meta
    edit_comp_path.write_text(json.dumps(edit_comp, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")

    # 2. Update skill.build-scientific-docx/component.yaml
    build_comp_rel = "components/skills/build-scientific-docx/component.yaml"
    build_comp_path = AWF_ROOT / build_comp_rel
    build_comp = json.loads(build_comp_path.read_text(encoding="utf-8"))
    rc11_build = build_comp["releases"]["1.0.0-rc.11"]
    rc12_caps = list(rc11_build["capabilities"])
    for cap in (
        "dom-safe-w-drawing-detection-and-dynamic-template-style-inheritance",
        "no-residual-publisher-template-placeholders-gate",
        "word-native-track-changes-and-right-margin-rationale-comments-builder",
    ):
        if cap not in rc12_caps:
            rc12_caps.append(cap)

    rc12_build_meta = {
        "status": "validated",
        "observed_at": "2026-10-28",
        "source_snapshot": "components/skills/build-scientific-docx/releases/1.0.0-rc.12/source",
        "tree_sha256": tree_sha256(build_src),
        "runtime_requirements": list(rc11_build["runtime_requirements"]),
        "capabilities": rc12_caps,
        "limitations": list(rc11_build["limitations"]),
    }
    build_comp["releases"]["1.0.0-rc.12"] = rc12_build_meta
    build_comp_path.write_text(json.dumps(build_comp, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")

    # 3. Write workflow scientific-report-authoring@1.0.0-rc.13
    wf_rc12_dir = AWF_ROOT / "workflows/scientific-report-authoring/releases/1.0.0-rc.12"
    wf_rc13_dir = AWF_ROOT / "workflows/scientific-report-authoring/releases/1.0.0-rc.13"
    wf_rc13_dir.mkdir(parents=True, exist_ok=True)

    wf_doc = json.loads((wf_rc12_dir / "workflow.yaml").read_text(encoding="utf-8"))
    wf_doc["release"] = "1.0.0-rc.13"
    wf_doc["status"] = "validated"
    wf_doc["purpose"] = (
        "Author, revise, and audit scientific manuscripts, technical reports, grant proposals, and Supporting Information (ESI) "
        "across disciplines with domain-agnostic writing/review rules, Lossy-Compression 3-Point Semantic Preservation gates, "
        "4-Role x 3-Round iterative peer-review closed loops, DOM-safe in-place DOCX editing, residual template placeholder gates, "
        "Word native Track Changes (<w:ins>/<w:del>) + right-margin rationale comments (<w:comment>), inline OMML style inheritance, "
        "and artifact-first disk provenance verification."
    )
    wf_yaml_path = wf_rc13_dir / "workflow.yaml"
    wf_yaml_path.write_text(json.dumps(wf_doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")

    lock_doc = {
        "components": {
            "skill.build-scientific-docx": "1.0.0-rc.12",
            "skill.edit-scientific-article": "1.0.0-rc.10",
        },
        "locked_at": "2026-10-28",
        "schema_version": 1,
        "workflow": "scientific-report-authoring",
        "workflow_release": "1.0.0-rc.13",
    }
    lock_yaml_path = wf_rc13_dir / "versions.lock"
    lock_yaml_path.write_text(json.dumps(lock_doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")

    # 4. Write new release-integrity attestation file
    att_rel = "attestations/release-integrity-20261028-sciword-rc13.yaml"
    att_path = AWF_ROOT / att_rel
    att_doc = {
        "schema_version": 1,
        "digest_contract": "awf-tree-v2",
        "observed_at": "2026-10-28",
        "owner": "agy-sciword-rc13-generalization-20261028",
        "provenance": (
            "Release integrity attestation for scientific-report-authoring@1.0.0-rc.13 "
            "(skill.build-scientific-docx@1.0.0-rc.12, skill.edit-scientific-article@1.0.0-rc.10) "
            "generalizing all localized rules into domain-agnostic principles, adding the Lossy-Compression "
            "3-Point Semantic Audit, 4-Role x 3-Round Peer-Review Closed-Loop Protocol, residual template "
            "placeholder gate, and Word native Track Changes + right-margin rationale comments builder."
        ),
        "limitations": (
            "Attests repository file/tree/metadata integrity under awf-tree-v2; "
            "scientific claims remain governed by project experimental and computational evidence."
        ),
        "releases": {
            "skill.build-scientific-docx@1.0.0-rc.12": compute_attestation_entry(
                build_comp_rel,
                "components/skills/build-scientific-docx/releases/1.0.0-rc.12/source",
                rc12_build_meta,
            ),
            "skill.edit-scientific-article@1.0.0-rc.10": compute_attestation_entry(
                edit_comp_rel,
                "components/skills/edit-scientific-article/releases/1.0.0-rc.10/source",
                rc10_edit_meta,
            ),
        },
    }
    att_path.write_text(json.dumps(att_doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")

    # 5. Update registry.yaml
    reg_path = AWF_ROOT / "registry.yaml"
    reg_doc = json.loads(reg_path.read_text(encoding="utf-8"))
    if att_rel not in reg_doc.get("integrity_attestations", []):
        reg_doc["integrity_attestations"].append(att_rel)

    req_list = reg_doc.get("integrity_policy", {}).get("required_release_attestations", [])
    for ref in (
        "skill.build-scientific-docx@1.0.0-rc.12",
        "skill.edit-scientific-article@1.0.0-rc.10",
    ):
        if ref not in req_list:
            req_list.append(ref)
    req_list.sort()

    for comp_entry in reg_doc.get("components", []):
        cid = comp_entry.get("id")
        if cid == "skill.build-scientific-docx":
            comp_entry["latest_release"] = "1.0.0-rc.12"
            comp_entry["descriptor_sha256"] = file_sha256(build_comp_path)
        elif cid == "skill.edit-scientific-article":
            comp_entry["latest_release"] = "1.0.0-rc.10"
            comp_entry["descriptor_sha256"] = file_sha256(edit_comp_path)

    wf_sha = file_sha256(wf_yaml_path)
    lk_sha = file_sha256(lock_yaml_path)
    wf_desc_rel = "workflows/scientific-report-authoring/releases/1.0.0-rc.13/workflow.yaml"
    wf_lock_rel = "workflows/scientific-report-authoring/releases/1.0.0-rc.13/versions.lock"

    for wf_entry in reg_doc.get("workflows", []):
        if wf_entry.get("id") == "scientific-report-authoring":
            wf_entry["descriptor"] = wf_desc_rel
            wf_entry["descriptor_sha256"] = wf_sha
            wf_entry["lock"] = wf_lock_rel
            wf_entry["lock_sha256"] = lk_sha
            wf_entry["releases"]["1.0.0-rc.13"] = {
                "descriptor": wf_desc_rel,
                "descriptor_sha256": wf_sha,
                "lock": wf_lock_rel,
                "lock_sha256": lk_sha,
                "status": "validated",
            }

    reg_path.write_text(json.dumps(reg_doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print("Registered scientific-report-authoring@1.0.0-rc.13 (build-scientific-docx@1.0.0-rc.12, edit-scientific-article@1.0.0-rc.10)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
