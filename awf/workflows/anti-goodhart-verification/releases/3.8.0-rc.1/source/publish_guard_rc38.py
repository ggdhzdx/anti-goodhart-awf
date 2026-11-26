#!/usr/bin/env python3
"""Validate and publish Guard 3.8.0-rc.1, Verifier 1.0.0-rc.4, and Tutor 1.0.0-rc.39 as immutable successors."""
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
WID = "anti-goodhart-verification"
VERSION = "3.8.0-rc.1"
PREV_WF_VERSION = "3.7.0-rc.8"
TOOL_VERSION = "1.0.0-rc.4"
PREV_TOOL_VERSION = "1.0.0-rc.3"
TUTOR_WID = "adaptive-interactive-tutor"
TUTOR_VERSION = "1.0.0-rc.39"
PREV_TUTOR_VERSION = "1.0.0-rc.38"
OBSERVED_DATE = "2026-11-25"
WF = ROOT / f"workflows/{WID}/releases/{VERSION}"
TUTOR_WF = ROOT / f"workflows/{TUTOR_WID}/releases/{TUTOR_VERSION}"
REPORT = ROOT / "reports/guard-rc38-physics-redteam-20261125"
UNITS = {
    "skill.anti-goodhart-verification": ("skills/anti-goodhart-verification", VERSION, PREV_WF_VERSION),
    "tool.awf-repository-verifier": ("tools/awf-repository-verifier", TOOL_VERSION, PREV_TOOL_VERSION),
    "skill.adaptive-interactive-tutor": ("skills/adaptive-interactive-tutor", TUTOR_VERSION, PREV_TUTOR_VERSION),
}
SOURCES = {cid: ROOT / f"components/{directory}/releases/{version}/source" for cid, (directory, version, _prev) in UNITS.items()}
GUARD = SOURCES["skill.anti-goodhart-verification"]
TOOL = SOURCES["tool.awf-repository-verifier"]
sys.path.insert(0, str(TOOL))
from guard_receipt_contract import validate_guard_receipt  # noqa: E402


def fingerprints() -> dict[str, dict[str, str]]:
    return {
        str(path.relative_to(ROOT)): {"legacy": tree_hash(path), "v2": tree_v2(path)}
        for path in [*SOURCES.values(), WF / "source"]
    }


def _clean_pycache() -> None:
    for root in (*SOURCES.values(), WF / "source"):
        for cache_dir in list(root.rglob("__pycache__")):
            if cache_dir.is_dir():
                shutil.rmtree(cache_dir)


def validate() -> bool:
    _clean_pycache()
    REPORT.mkdir(parents=True, exist_ok=True)
    before = fingerprints()
    scripts = GUARD / "scripts"
    engine = scripts / "awf_universal_anti_goodhart_gates.py"
    commands = {
        "selftest": [str(engine), "--self-test"],
        "audit": [str(engine), "--audit-self"],
        "escapes": [str(scripts / "test_evidence_escapes.py")],
        "full_route": [str(WF / "source/verify_full_route_rc38.py")],
        "ag_review_rc7": [str(WF / "source/ag_review_rc7.py")],
        "receipts": [str(TOOL / "test_receipt_contract.py")],
        "boundary": [str(scripts / "test_function_line_limit.py")],
        "mutation": [str(scripts / "awf_anti_goodhart_mutation_adequacy.py"), "--workers", "16"],
        "nonfinite": [str(scripts / "test_nonfinite_campaign.py")],
        "modular": [str(scripts / "test_modular_integrity.py")],
        "execution": [str(scripts / "test_execution_flow.py")],
        "contracts": [str(scripts / "test_rc3_contracts.py")],
        "optimized": [str(engine), "--self-test"],
    }
    steps, receipts = {}, {}
    for name, args in commands.items():
        stdout, stderr = REPORT / f"final-{name}.json", REPORT / f"final-{name}.stderr.txt"
        command = [sys.executable, "-B"] + (["-O"] if name == "optimized" else []) + args
        with stdout.open("w", encoding="utf-8") as out, stderr.open("w", encoding="utf-8") as err:
            proc = subprocess.run(command, cwd=ROOT, stdout=out, stderr=err, timeout=1800, check=False)
        steps[name] = {
            "returncode": proc.returncode,
            "stdout": str(stdout.relative_to(ROOT)),
            "stdout_sha256": file_hash(stdout),
            "stderr": str(stderr.relative_to(ROOT)),
            "stderr_sha256": file_hash(stderr),
        }
        if proc.returncode == 0 and name != "optimized":
            receipts[name] = read(stdout)
        print(f"{name}: rc={proc.returncode}", flush=True)

    _clean_pycache()
    checks = {name: step["returncode"] == 0 for name, step in steps.items() if name != "optimized"}
    checks.update(
        strict_receipt=not validate_guard_receipt(receipts.get("selftest", {})),
        subcheck_count_80=receipts.get("selftest", {}).get("subchecks_verified_count") == 80,
        audit_pass=receipts.get("audit", {}).get("status") == "PASS" and receipts.get("audit", {}).get("violation_count") == 0,
        advisory_policy=receipts.get("audit", {}).get("size_policy") == "advisory_by_default_explicit_limits_enforced",
        no_size_waivers=receipts.get("audit", {}).get("declared_waivers") == [],
        no_filename_exemptions=receipts.get("audit", {}).get("magic_number_exempt_test_role_files") == [],
        escape_groups=receipts.get("selftest", {}).get("evidence_escape_regressions", {}).get("status") == "PASS",
        rc7_clusters_closed=receipts.get("ag_review_rc7", {}).get("status") == "PASS"
        and receipts.get("ag_review_rc7", {}).get("frozen_release_unchanged") is True,
        mutation_pass=receipts.get("mutation", {}).get("status") == "PASS"
        and receipts.get("mutation", {}).get("mutants_total") == 70
        and receipts.get("mutation", {}).get("survivors") == [],
        mutation_no_crashes=receipts.get("mutation", {}).get("killed_by_crash") == 0,
        mutation_bindings=bool(receipts.get("mutation", {}).get("rows"))
        and all(r.get("patched_bindings") for r in receipts["mutation"]["rows"]),
        nonfinite_pass=receipts.get("nonfinite", {}).get("status") == "PASS",
        contracts_clean=receipts.get("contracts", {}).get("scanner") == {},
        optimized_refused=steps["optimized"]["returncode"] != 0,
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
    print({"passed": result["passed"], "failed": [name for name, passed in checks.items() if not passed]}, flush=True)
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
        raise RuntimeError("Root is required to freeze the new releases")
    _clean_pycache()
    registry = read(ROOT / "registry.yaml")
    workflow = next(w for w in registry["workflows"] if w["id"] == WID)
    tutor_workflow = next(w for w in registry["workflows"] if w["id"] == TUTOR_WID)
    if workflow["descriptor"] != f"workflows/{WID}/releases/{PREV_WF_VERSION}/workflow.yaml":
        raise RuntimeError(f"Workflow current changed: {workflow['descriptor']}")
    if tutor_workflow["descriptor"] != f"workflows/{TUTOR_WID}/releases/{PREV_TUTOR_VERSION}/workflow.yaml":
        raise RuntimeError(f"Tutor workflow current changed: {tutor_workflow['descriptor']}")
    active = ROOT / "bin/verify.py"
    old_tool = ROOT / f"components/tools/awf-repository-verifier/releases/{PREV_TOOL_VERSION}/source/verify.py"
    if not active.is_symlink() or active.resolve() != old_tool.resolve():
        raise RuntimeError("Active verifier changed")
    if (WF / "workflow.yaml").exists() or (WF / "versions.lock").exists():
        raise RuntimeError("Guard workflow release already exists")
    if (TUTOR_WF / "workflow.yaml").exists() or (TUTOR_WF / "versions.lock").exists():
        raise RuntimeError("Tutor workflow release already exists")

    descriptors = {}
    for cid, (directory, version, previous) in UNITS.items():
        path = ROOT / f"components/{directory}/component.yaml"
        document = read(path)
        if version in document["releases"]:
            raise RuntimeError("Component release already exists: " + cid)
        if cid in registry["global_components"] and registry["global_components"][cid] != previous:
            raise RuntimeError("Global component current changed: " + cid)
        descriptors[cid] = (path, document)

    evidence = read(REPORT / "validation.json")
    if not evidence["passed"] or not all(evidence["checks"].values()) or evidence["sources"] != fingerprints():
        raise RuntimeError("Failed or stale validation")
    for step in evidence["steps"].values():
        for stream in ("stdout", "stderr"):
            if file_hash(ROOT / step[stream]) != step[stream + "_sha256"]:
                raise RuntimeError("Validation output changed")

    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = ROOT / f"backups/guard-rc38-redteam-{stamp}"
    backup.mkdir(parents=True)
    shutil.copy2(ROOT / "registry.yaml", backup / "registry.yaml")
    (backup / "verify-symlink-target.txt").write_text(os.readlink(active), encoding="utf-8")
    for cid, (path, _document) in descriptors.items():
        shutil.copy2(path, backup / (cid + ".yaml"))

    evidence_path = ROOT / f"reports/anti-goodhart-verification-{VERSION}-validation-{stamp}.json"
    write(evidence_path, evidence, exclusive=True)

    attestations = {}
    for cid, (_directory, version, previous) in UNITS.items():
        path, document = descriptors[cid]
        source = SOURCES[cid]
        meta = copy.deepcopy(document["releases"][previous])
        meta.update(
            observed_at=OBSERVED_DATE,
            source_snapshot=str(source.relative_to(ROOT)),
            tree_sha256=tree_hash(source),
            provenance=f"6-gate physics red-team, outer-glue & dual-entry post-hoc audit validation: {evidence_path.relative_to(ROOT)} sha256={file_hash(evidence_path)}",
        )
        if cid == "skill.anti-goodhart-verification":
            meta["change_summary"] = (
                "Purely additive upgrade from 74 to 80 automated subchecks (70 force-PASS mutants, >=50 negative controls): "
                "add G4d dynamic feature variance-collapse & collinearity canary, G3m sub-fragment rigid spin & tangential site-slip "
                "sensitivity, G1f periodic unit-cell cyclic shift & oligomer chain convergence, G5u cross-table physical/thermodynamic "
                "inequality bounds, G6q outer-glue @scientific_atom coverage & cross-station single-source AST lock, and G7j dual-entry "
                "pre_code / post_hoc_audit physics red-team with --audit-existing & comment/docstring-stripped AST card extraction."
            )
            for cap in (
                "dynamic-feature-variance-collapse-and-collinearity-canary",
                "subfragment-rigid-spin-and-siteslip-sensitivity",
                "periodic-unitcell-cyclic-shift-and-chain-convergence",
                "crosstable-physical-thermodynamic-inequality-bounds",
                "outer-glue-coverage-and-single-source-ast-lock",
                "dual-entry-precode-and-posthoc-stripped-ast-redteam-audit",
                "full-70-function-force-pass-mutation-adequacy",
            ):
                if cap not in meta["capabilities"]:
                    meta["capabilities"].append(cap)
        elif cid == "tool.awf-repository-verifier":
            for cap in (
                "14-slot-80-subcheck-receipt-contract-and-v38-execution-evidence",
                "legacy-v37-scoped-backward-compatibility-for-unchanged-workflows",
            ):
                if cap not in meta["capabilities"]:
                    meta["capabilities"].append(cap)
        else:
            meta["depends_on"] = [
                f"skill.anti-goodhart-verification@{VERSION}",
                "skill.design-anti-goodhart@1.0.0-rc.25",
                "skill.html-ppt@1.0.0-rc.27",
            ]
            meta["runtime_requirements"] = [
                "UTF-8 Markdown Skill loader (Antigravity / Codex / Pi / Grok)",
                f"Standalone skill.anti-goodhart-verification@{VERSION} (AWF Guard, 14 slots / 80 subchecks)",
                "Standalone skill.design-anti-goodhart@1.0.0-rc.25 (AWF DesignAG, 18 automated design gates + Stage 0 Global Deck Blueprint + Dual-Stage GDD verification)",
                "Standalone skill.html-ppt@1.0.0-rc.27 (AWF HTML-PPT V3 Macro-to-Micro Tri-Mode 1-Slide-Per-Step enforcer)",
                "Browser for on-demand interactive HTML micro-labs and HTML-PPT rendered-page review",
                "Pillow and cryptography (Ed25519) for DesignAG evidence validation; runner-owned public-key policy for final acceptance",
            ]
            meta["change_summary"] = (
                "Upgrade Adaptive Interactive Tutor to delegate 80-subcheck verification to skill.anti-goodhart-verification@3.8.0-rc.1 "
                "and enforce Dual-Entry Independent Physics Red-Team Protocol (pre_code 4-axis critique before new code + post_hoc_audit "
                "--audit-existing stripped-AST & JSON variance triangulation for legacy scripts)."
            )
            for cap in (
                "dual-entry-precode-and-posthoc-physics-redteam-audit",
                "outer-glue-single-source-ast-and-feature-variance-guards",
            ):
                if cap not in meta["capabilities"]:
                    meta["capabilities"].append(cap)

        document["releases"][version] = meta
        write(path, document)
        entry = next(c for c in registry["components"] if c["id"] == cid)
        entry.update(latest_release=version, descriptor_sha256=file_hash(path))
        if cid in registry["global_components"]:
            registry["global_components"][cid] = version
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

    attestation = ROOT / f"attestations/release-integrity-guard-rc38-{stamp}.yaml"
    write(
        attestation,
        {
            "schema_version": 1,
            "digest_contract": "awf-tree-v2",
            "observed_at": OBSERVED_DATE,
            "owner": "guard-rc38-physics-redteam",
            "provenance": str(evidence_path.relative_to(ROOT)),
            "releases": attestations,
        },
        exclusive=True,
    )

    guard_doc = read(ROOT / workflow["descriptor"])
    guard_doc.update(
        release=VERSION,
        purpose=(
            "AWF Guard with 14 canonical slots x 80 automated subchecks: Dual-Entry pre_code & post_hoc_audit "
            "physics red-team (--audit-existing), outer-glue & single-source AST lock, dynamic feature variance canary, "
            "sub-fragment spin/slip sensitivity, periodic unit-cell cyclic gauge & chain convergence, cross-table bounds, "
            "and 70-function force-PASS mutation adequacy."
        ),
        engineering_source_tree_sha256=tree_hash(WF / "source"),
    )
    rc38_note = (
        " Dynamic feature variance-collapse (G4d), sub-fragment spin/slip sensitivity (G3m), periodic cyclic-shift & "
        "chain convergence (G1f), cross-table physical inequality bounds (G5u), outer-glue single-source AST lock (G6q), "
        "dual-entry pre_code/post_hoc_audit physics red-team (G7j), and 70-gate mutation adequacy are enforced."
    )
    if rc38_note not in guard_doc["engineering_gate"]:
        guard_doc["engineering_gate"] += rc38_note
    guard_doc["scientific_gate"] = guard_doc["scientific_gate"].replace("74 concrete sub-checks", "80 concrete sub-checks")
    write(WF / "workflow.yaml", guard_doc, exclusive=True)

    guard_lock = read(ROOT / workflow["lock"])
    guard_lock.update(workflow_release=VERSION, locked_at=OBSERVED_DATE)
    guard_lock["components"]["skill.anti-goodhart-verification"] = VERSION
    guard_lock["components"]["tool.awf-repository-verifier"] = TOOL_VERSION
    write(WF / "versions.lock", guard_lock, exclusive=True)

    guard_ref = {
        "descriptor": str((WF / "workflow.yaml").relative_to(ROOT)),
        "descriptor_sha256": file_hash(WF / "workflow.yaml"),
        "lock": str((WF / "versions.lock").relative_to(ROOT)),
        "lock_sha256": file_hash(WF / "versions.lock"),
        "status": "validated",
    }
    workflow.update(guard_ref)
    workflow["releases"][VERSION] = guard_ref.copy()

    tutor_doc = read(ROOT / tutor_workflow["descriptor"])
    tutor_doc.update(release=TUTOR_VERSION)
    tutor_doc["purpose"] = tutor_doc["purpose"].replace("73-Gate scientific/code verification to skill.anti-goodhart-verification@3.7.0-rc.7", f"80-Subcheck scientific/code & Dual-Entry Physics Red-Team verification to skill.anti-goodhart-verification@{VERSION}")
    tutor_doc["engineering_gate"] = tutor_doc["engineering_gate"].replace("Guard 3.7.0-rc.7", f"Guard {VERSION}")
    tutor_doc["engineering_gate"] += " Enforce Dual-Entry Physics Red-Team (pre_code 4-axis critique and post_hoc_audit --audit-existing stripped-AST triangulation), G4d feature variance canary, G3m spin/slip sensitivity, G1f unit-cell convergence, G5u physical bounds, and G6q outer-glue lock."
    tutor_doc["scientific_gate"] = tutor_doc["scientific_gate"].replace(f"skill.anti-goodhart-verification@3.7.0-rc.7 (14 slots / 74 subchecks)", f"skill.anti-goodhart-verification@{VERSION} (14 slots / 80 subchecks)")
    write(TUTOR_WF / "workflow.yaml", tutor_doc, exclusive=True)

    tutor_lock = read(ROOT / tutor_workflow["lock"])
    tutor_lock.update(workflow_release=TUTOR_VERSION, locked_at=OBSERVED_DATE)
    tutor_lock["components"]["skill.adaptive-interactive-tutor"] = TUTOR_VERSION
    tutor_lock["components"]["skill.anti-goodhart-verification"] = VERSION
    tutor_lock["components"]["tool.awf-repository-verifier"] = TOOL_VERSION
    write(TUTOR_WF / "versions.lock", tutor_lock, exclusive=True)

    tutor_ref = {
        "descriptor": str((TUTOR_WF / "workflow.yaml").relative_to(ROOT)),
        "descriptor_sha256": file_hash(TUTOR_WF / "workflow.yaml"),
        "lock": str((TUTOR_WF / "versions.lock").relative_to(ROOT)),
        "lock_sha256": file_hash(TUTOR_WF / "versions.lock"),
        "status": "validated",
    }
    tutor_workflow.update(tutor_ref)
    tutor_workflow["releases"][TUTOR_VERSION] = tutor_ref.copy()

    registry["integrity_attestations"].append(str(attestation.relative_to(ROOT)))
    registry["integrity_policy"]["required_release_attestations"].sort()

    temporary = active.with_name("verify.py.rc38-new-link")
    if temporary.exists() or temporary.is_symlink():
        temporary.unlink()
    temporary.symlink_to(TOOL / "verify.py")
    os.replace(temporary, active)
    write(ROOT / "registry.yaml", registry)

    result = {
        "guard_release": VERSION,
        "verifier_release": TOOL_VERSION,
        "tutor_release": TUTOR_VERSION,
        "backup": str(backup),
        "evidence": str(evidence_path),
        "attestation": str(attestation),
    }
    write(REPORT / "publication.json", result, exclusive=True)

    owner = pwd.getpwnam("zc")
    for chown_target in (
        ROOT / "registry.yaml",
        active,
        *[item[0] for item in descriptors.values()],
        *(s.parent for s in SOURCES.values()),
        WF,
        TUTOR_WF,
        REPORT,
        backup,
        evidence_path,
        attestation,
    ):
        _chown_tree_zc(chown_target, owner.pw_uid, owner.pw_gid)

    for frozen_target in (
        *SOURCES.values(),
        WF / "source",
        WF / "workflow.yaml",
        WF / "versions.lock",
        TUTOR_WF / "workflow.yaml",
        TUTOR_WF / "versions.lock",
        evidence_path,
        attestation,
    ):
        freeze(frozen_target)

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
