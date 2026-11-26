#!/usr/bin/env python3
"""Validate and publish DesignAG 1.0.0-rc.26, HTML-PPT 1.0.0-rc.28 (wf rc.25), and Tutor 1.0.0-rc.40 with full closure atop Guard 3.8.0-rc.1 and Verifier 1.0.0-rc.4."""
from __future__ import annotations

import argparse
import copy
import datetime
import json
import os
import pwd
import shutil
import subprocess
import sys
from pathlib import Path

from release_hashes import canonical_hash, file_hash, paths, read, tree_hash, tree_v2, write

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "registry.yaml").is_file())
OBSERVED_DATE = "2026-11-25"
GUARD_VERSION = "3.8.0-rc.1"
VERIFIER_VERSION = "1.0.0-rc.4"

DAG_CID, DAG_VER, DAG_PREV = "skill.design-anti-goodhart", "1.0.0-rc.26", "1.0.0-rc.25"
HTML_CID, HTML_VER, HTML_PREV = "skill.html-ppt", "1.0.0-rc.28", "1.0.0-rc.27"
TUTOR_CID, TUTOR_VER, TUTOR_PREV = "skill.adaptive-interactive-tutor", "1.0.0-rc.40", "1.0.0-rc.39"
HTML_WF_VER, HTML_WF_PREV = "1.0.0-rc.25", "1.0.0-rc.24"

UNITS = {
    DAG_CID: ("skills/design-anti-goodhart", DAG_VER, DAG_PREV),
    HTML_CID: ("skills/html-ppt", HTML_VER, HTML_PREV),
    TUTOR_CID: ("skills/adaptive-interactive-tutor", TUTOR_VER, TUTOR_PREV),
}
SOURCES = {cid: ROOT / f"components/{d}/releases/{v}/source" for cid, (d, v, _p) in UNITS.items()}
WF_DAG = ROOT / f"workflows/design-anti-goodhart/releases/{DAG_VER}"
WF_HTML = ROOT / f"workflows/html-ppt/releases/{HTML_WF_VER}"
WF_TUTOR = ROOT / f"workflows/adaptive-interactive-tutor/releases/{TUTOR_VER}"
REPORT = ROOT / "reports/tutor-closure-rc40-20261125"


def fingerprints() -> dict[str, dict[str, str]]:
    return {
        str(p.relative_to(ROOT)): {"legacy": tree_hash(p), "v2": tree_v2(p)}
        for p in [*SOURCES.values(), WF_DAG / "source"]
    }


def _clean_pycache() -> None:
    for root in (*SOURCES.values(), WF_DAG / "source"):
        for cache_dir in list(root.rglob("__pycache__")):
            if cache_dir.is_dir():
                shutil.rmtree(cache_dir)


def validate() -> bool:
    _clean_pycache()
    REPORT.mkdir(parents=True, exist_ok=True)
    before = fingerprints()
    dag_scripts = SOURCES[DAG_CID] / "scripts"
    html_scripts = SOURCES[HTML_CID] / "scripts"
    commands = {
        "dag_selftest": [str(dag_scripts / "awf_design_anti_goodhart_gates.py"), "--self-test"],
        "dag_audit_self": [str(dag_scripts / "awf_design_anti_goodhart_gates.py"), "--audit-self"],
        "dag_evidence": [str(SOURCES[DAG_CID] / "design_tests/test_evidence.py")],
        "html_selftest": [str(html_scripts / "audit_single_slide_step.py"), "--self-test"],
        "public_route": [str(WF_DAG / "source/test_public_route.py")],
    }
    steps, receipts = {}, {}
    for name, args in commands.items():
        stdout, stderr = REPORT / f"{name}.json", REPORT / f"{name}.stderr.txt"
        with stdout.open("w", encoding="utf-8") as out, stderr.open("w", encoding="utf-8") as err:
            proc = subprocess.run([sys.executable, "-B", *args], cwd=ROOT, stdout=out, stderr=err, timeout=1800, check=False)
        steps[name] = {
            "returncode": proc.returncode,
            "stdout": str(stdout.relative_to(ROOT)),
            "stdout_sha256": file_hash(stdout),
            "stderr": str(stderr.relative_to(ROOT)),
            "stderr_sha256": file_hash(stderr),
        }
        if proc.returncode == 0:
            try:
                receipts[name] = read(stdout)
            except Exception:
                receipts[name] = {}
        print(f"{name}: rc={proc.returncode}", flush=True)

    _clean_pycache()
    checks = {name: step["returncode"] == 0 for name, step in steps.items()}
    checks.update(
        dag_selftest_18gates=receipts.get("dag_selftest", {}).get("verdict_zone") == "PASS"
        and len(set(receipts.get("dag_selftest", {}).get("gates_passed", []))) >= 18,
        dag_audit_uses_guard38=receipts.get("dag_audit_self", {}).get("status") == "PASS"
        and receipts.get("dag_audit_self", {}).get("violation_count") == 0
        and receipts.get("dag_audit_self", {}).get("guard_release") == GUARD_VERSION,
        html_selftest_24checks=receipts.get("html_selftest", {}).get("status") == "PASS"
        and len(set(receipts.get("html_selftest", {}).get("checks_passed", []))) >= 24,
        sources_unchanged=before == fingerprints(),
    )
    result = {
        "passed": all(checks.values()),
        "checks": checks,
        "sources": before,
        "steps": steps,
        "observed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    write(REPORT / "validation.json", result)
    print({"passed": result["passed"], "failed": [k for k, v in checks.items() if not v]}, flush=True)
    return result["passed"]


def _chown_tree_zc(target: Path, uid: int, gid: int) -> None:
    os.lchown(target, uid, gid)
    if target.is_dir() and not target.is_symlink():
        for p in target.rglob("*"):
            os.lchown(p, uid, gid)


def freeze(path: Path) -> None:
    entries = [p for p in paths(path) if not p.is_symlink()] if path.is_dir() else []
    subprocess.run(["chattr", "+i", *map(str, entries), str(path)], check=True)


def publish() -> None:
    if os.geteuid() != 0:
        raise RuntimeError("Root is required to freeze new closure releases")
    _clean_pycache()
    registry = read(ROOT / "registry.yaml")
    wfs = {w["id"]: w for w in registry["workflows"]}
    for wid, prev_ver in (
        ("design-anti-goodhart", DAG_PREV),
        ("html-ppt", HTML_WF_PREV),
        ("adaptive-interactive-tutor", TUTOR_PREV),
    ):
        if wfs[wid]["descriptor"] != f"workflows/{wid}/releases/{prev_ver}/workflow.yaml":
            raise RuntimeError(f"Workflow pointer mismatch for {wid}: {wfs[wid]['descriptor']}")
    for wf_dir in (WF_DAG, WF_HTML, WF_TUTOR):
        if (wf_dir / "workflow.yaml").exists() or (wf_dir / "versions.lock").exists():
            raise RuntimeError(f"Release files already exist in {wf_dir}")

    descriptors = {}
    for cid, (directory, version, _prev) in UNITS.items():
        path = ROOT / f"components/{directory}/component.yaml"
        doc = read(path)
        if version in doc["releases"]:
            raise RuntimeError(f"Component release already exists: {cid}@{version}")
        descriptors[cid] = (path, doc)

    evidence = read(REPORT / "validation.json")
    if not evidence["passed"] or not all(evidence["checks"].values()) or evidence["sources"] != fingerprints():
        raise RuntimeError("Failed or stale validation")
    for step in evidence["steps"].values():
        for stream in ("stdout", "stderr"):
            if file_hash(ROOT / step[stream]) != step[stream + "_sha256"]:
                raise RuntimeError("Validation output changed")

    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = ROOT / f"backups/tutor-closure-rc40-{stamp}"
    backup.mkdir(parents=True)
    shutil.copy2(ROOT / "registry.yaml", backup / "registry.yaml")
    for cid, (path, _doc) in descriptors.items():
        shutil.copy2(path, backup / f"{cid}.yaml")

    evidence_path = ROOT / f"reports/tutor-closure-rc40-validation-{stamp}.json"
    write(evidence_path, evidence, exclusive=True)
    eng_rel = f"workflows/design-anti-goodhart/releases/{DAG_VER}/source"
    eng_tree = tree_hash(WF_DAG / "source")
    prov = f"Full topological closure aligned onto Guard {GUARD_VERSION} & Verifier {VERIFIER_VERSION}; {evidence_path.relative_to(ROOT)} sha256={file_hash(evidence_path)}"
    summary = (
        f"Coordinate DesignAG ({DAG_VER}), HTML-PPT ({HTML_VER} / wf {HTML_WF_VER}), and Adaptive Interactive Tutor ({TUTOR_VER}) "
        f"to depend directly on skill.anti-goodhart-verification@{GUARD_VERSION} (14 slots / 80 subchecks + Dual-Entry pre_code / post_hoc_audit "
        f"physics red-team --audit-existing) and tool.awf-repository-verifier@{VERIFIER_VERSION}."
    )

    attestations = {}
    for cid, (_d, version, prev) in UNITS.items():
        path, doc = descriptors[cid]
        source = SOURCES[cid]
        meta = copy.deepcopy(doc["releases"][prev])
        meta.update(
            observed_at=OBSERVED_DATE,
            source_snapshot=str(source.relative_to(ROOT)),
            tree_sha256=tree_hash(source),
            provenance=prov,
            change_summary=summary,
            limitations=[
                lim.replace(f"releases/{DAG_PREV}/source", f"releases/{DAG_VER}/source")
                for lim in meta.get("limitations", [])
            ],
        )
        if cid == DAG_CID:
            meta["depends_on"] = [f"skill.anti-goodhart-verification@{GUARD_VERSION}"]
        elif cid == HTML_CID:
            meta["depends_on"] = [f"{DAG_CID}@{DAG_VER}", f"skill.anti-goodhart-verification@{GUARD_VERSION}"]
        else:
            meta["depends_on"] = [
                f"skill.anti-goodhart-verification@{GUARD_VERSION}",
                f"{DAG_CID}@{DAG_VER}",
                f"{HTML_CID}@{HTML_VER}",
            ]
            meta["runtime_requirements"] = [
                req.replace(DAG_PREV, DAG_VER).replace(HTML_PREV, HTML_VER)
                for req in meta.get("runtime_requirements", [])
            ]
        cap = "topological-closure-aligned-with-guard-v3-8-and-verifier-rc4"
        if cap not in meta["capabilities"]:
            meta["capabilities"].append(cap)
        doc["releases"][version] = meta
        write(path, doc)
        comp_entry = next(c for c in registry["components"] if c["id"] == cid)
        comp_entry.update(latest_release=version, descriptor_sha256=file_hash(path))
        key = f"{cid}@{version}"
        if key not in registry["integrity_policy"]["required_release_attestations"]:
            registry["integrity_policy"]["required_release_attestations"].append(key)
        entries = paths(source)
        attestations[key] = {
            "coverage": "tree",
            "descriptor": str(path.relative_to(ROOT)),
            "descriptor_file_sha256": file_hash(path),
            "entry_count": len(entries),
            "legacy_tree_sha256": tree_hash(source),
            "metadata_sha256": canonical_hash(meta),
            "regular_file_bytes": sum(p.lstat().st_size for p in entries if p.is_file() and not p.is_symlink()),
            "root": str(source.relative_to(ROOT)),
            "symlink_count": sum(p.is_symlink() for p in entries),
            "tree_sha256": tree_v2(source),
        }

    attestation = ROOT / f"attestations/release-integrity-tutor-closure-rc40-{stamp}.yaml"
    write(
        attestation,
        {
            "schema_version": 1,
            "digest_contract": "awf-tree-v2",
            "observed_at": OBSERVED_DATE,
            "owner": "tutor-closure-rc40",
            "provenance": str(evidence_path.relative_to(ROOT)),
            "releases": attestations,
        },
        exclusive=True,
    )

    wf_plan = [
        (
            "design-anti-goodhart",
            DAG_PREV,
            DAG_VER,
            WF_DAG,
            {
                DAG_CID: DAG_VER,
                "skill.anti-goodhart-verification": GUARD_VERSION,
                "tool.awf-repository-verifier": VERIFIER_VERSION,
            },
        ),
        (
            "html-ppt",
            HTML_WF_PREV,
            HTML_WF_VER,
            WF_HTML,
            {
                HTML_CID: HTML_VER,
                DAG_CID: DAG_VER,
                "skill.anti-goodhart-verification": GUARD_VERSION,
                "tool.awf-repository-verifier": VERIFIER_VERSION,
            },
        ),
        (
            "adaptive-interactive-tutor",
            TUTOR_PREV,
            TUTOR_VER,
            WF_TUTOR,
            {
                TUTOR_CID: TUTOR_VER,
                "skill.anti-goodhart-verification": GUARD_VERSION,
                DAG_CID: DAG_VER,
                HTML_CID: HTML_VER,
                "tool.awf-repository-verifier": VERIFIER_VERSION,
            },
        ),
    ]
    frozen_targets = [*SOURCES.values(), WF_DAG / "source", evidence_path, attestation]
    for wid, prev_ver, new_ver, wf_dir, lock_comps in wf_plan:
        wf_entry = wfs[wid]
        wf_doc = read(ROOT / wf_entry["descriptor"])
        wf_doc["release"] = new_ver
        for key in ("purpose", "engineering_gate", "scientific_gate"):
            if key in wf_doc:
                wf_doc[key] = (
                    wf_doc[key]
                    .replace("3.7.0-rc.7", GUARD_VERSION)
                    .replace(DAG_PREV, DAG_VER)
                    .replace(HTML_PREV, HTML_VER)
                )
        wf_doc["engineering_source"] = eng_rel
        wf_doc["engineering_source_tree_sha256"] = eng_tree
        wf_doc["known_limitations"] = [
            lim.replace(f"releases/{DAG_PREV}/source", f"releases/{DAG_VER}/source")
            for lim in wf_doc.get("known_limitations", [])
        ]
        wf_yaml_path = wf_dir / "workflow.yaml"
        lock_path = wf_dir / "versions.lock"
        write(wf_yaml_path, wf_doc, exclusive=True)
        write(
            lock_path,
            {
                "schema_version": 1,
                "workflow": wid,
                "workflow_release": new_ver,
                "locked_at": OBSERVED_DATE,
                "components": lock_comps,
            },
            exclusive=True,
        )
        ref = {
            "descriptor": str(wf_yaml_path.relative_to(ROOT)),
            "descriptor_sha256": file_hash(wf_yaml_path),
            "lock": str(lock_path.relative_to(ROOT)),
            "lock_sha256": file_hash(lock_path),
            "status": "validated",
        }
        wf_entry.update(ref)
        wf_entry["releases"][new_ver] = ref.copy()
        frozen_targets.extend([wf_yaml_path, lock_path])

    registry["integrity_attestations"].append(str(attestation.relative_to(ROOT)))
    registry["integrity_policy"]["required_release_attestations"].sort()
    write(ROOT / "registry.yaml", registry)

    result = {
        "design_anti_goodhart": DAG_VER,
        "html_ppt_skill": HTML_VER,
        "html_ppt_workflow": HTML_WF_VER,
        "adaptive_interactive_tutor": TUTOR_VER,
        "guard": GUARD_VERSION,
        "verifier": VERIFIER_VERSION,
        "backup": str(backup),
        "evidence": str(evidence_path),
        "attestation": str(attestation),
    }
    write(REPORT / "publication.json", result, exclusive=True)

    owner = pwd.getpwnam("zc")
    for target in (
        ROOT / "registry.yaml",
        *[p for p, _d in descriptors.values()],
        *(s.parent for s in SOURCES.values()),
        WF_DAG,
        WF_HTML,
        WF_TUTOR,
        REPORT,
        backup,
        evidence_path,
        attestation,
    ):
        _chown_tree_zc(target, owner.pw_uid, owner.pw_gid)

    for target in frozen_targets:
        freeze(target)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--validate-only", action="store_true")
    mode.add_argument("--publish", action="store_true")
    args = parser.parse_args()
    if args.validate_only:
        raise SystemExit(0 if validate() else 1)
    publish()
