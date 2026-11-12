#!/usr/bin/env python3
"""
Co-located AWF Release Registration Script for AWF Guard
(skill.anti-goodhart-verification@3.7.0-rc.2 & workflow anti-goodhart-verification@3.7.0-rc.2).
Strictly follows ADR 0012 (rolling current pointer) and ADR 0022 (co-located scripts
inside the target Release source/ tree prior to execution).

Unlike 3.7.0-rc.1, the `validated` label is earned, not hard-coded: registration aborts unless
`--self-test`, `--audit-self`, the force-PASS mutation-adequacy gate and the `python -O` refusal check all
pass. Evidence is written (no-overwrite) to `reports/` and referenced by sha256 in the Release provenance.
Registry and component descriptors are backed up to `backups/` before any write. `--dry-run` only validates.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

AWF_ROOT = Path("/home/zc/agent_workflows")
if not AWF_ROOT.exists():
    AWF_ROOT = Path(r"Z:\agent_workflows")
sys.path.insert(0, str(AWF_ROOT / "bin"))

import verify  # type: ignore

COMP_ID = "skill.anti-goodhart-verification"
WF_ID = "anti-goodhart-verification"
REL_ID = "3.7.0-rc.2"
OBSERVED_AT = "2026-11-10"
SCRIPTS_DIR = Path(__file__).resolve().parent
ENGINE = SCRIPTS_DIR / "awf_universal_anti_goodhart_gates.py"
MUTATION_GATE = SCRIPTS_DIR / "awf_anti_goodhart_mutation_adequacy.py"
VALIDATION_TIMEOUT_SEC = 1800


def write_json_yaml(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _run_step(label: str, argv: List[str]) -> Dict[str, Any]:
    proc = subprocess.run(argv, capture_output=True, text=True, timeout=VALIDATION_TIMEOUT_SEC, check=False)
    return {
        "step": label,
        "argv": [Path(a).name if a.startswith("/") else a for a in argv],
        "returncode": proc.returncode,
        "stdout_sha256": hashlib.sha256(proc.stdout.encode("utf-8")).hexdigest(),
        "stdout": proc.stdout,
        "stderr_tail": proc.stderr[-2000:],
    }


def run_release_validation() -> Dict[str, Any]:
    py = sys.executable
    steps = {
        "self_test": _run_step("self_test", [py, "-B", str(ENGINE), "--self-test"]),
        "audit_self": _run_step("audit_self", [py, "-B", str(ENGINE), "--audit-self"]),
        "mutation_adequacy": _run_step("mutation_adequacy", [py, "-B", str(MUTATION_GATE), "--workers", "16"]),
        "optimize_refusal": _run_step("optimize_refusal", [py, "-O", "-B", str(ENGINE), "--self-test"]),
    }
    receipt = json.loads(steps["self_test"]["stdout"]) if steps["self_test"]["returncode"] == 0 else {}
    audit = json.loads(steps["audit_self"]["stdout"]) if steps["audit_self"]["returncode"] == 0 else {}
    mut = json.loads(steps["mutation_adequacy"]["stdout"]) if steps["mutation_adequacy"]["returncode"] == 0 else {}
    checks = {
        "self_test_pass_14_slots": receipt.get("verdict_zone") == "PASS" and len(receipt.get("gates_passed", [])) == 14,
        "self_test_negative_controls_present": "negative_controls_total" in receipt and int(receipt["negative_controls_total"]) > 0,
        "audit_self_pass": audit.get("status") == "PASS",
        "mutation_adequacy_zero_survivors": mut.get("status") == "PASS" and not mut.get("survivors"),
        "optimize_mode_refused": steps["optimize_refusal"]["returncode"] != 0,
    }
    summary = {
        "subchecks_verified_count": receipt.get("subchecks_verified_count"),
        "negative_controls_total": receipt.get("negative_controls_total"),
        "slot_subcheck_counts": receipt.get("slot_subcheck_counts"),
        "audit_declared_waivers": [w.get("file") for w in audit.get("declared_waivers", [])],
        "mutants_total": mut.get("mutants_total"),
        "mutants_killed_by_assertion": mut.get("killed_by_assertion"),
        "mutation_declared_exempt_survivors": mut.get("declared_exempt_survivors"),
    }
    for step in steps.values():
        step.pop("stdout")
    return {"passed": all(checks.values()), "checks": checks, "summary": summary, "steps": steps}


def build_release_meta(source_rel: str, legacy_hash: str, evidence_rel: str, evidence_sha: str) -> Dict[str, Any]:
    rc1_meta = verify.read_manifest(AWF_ROOT / "components/skills/anti-goodhart-verification/component.yaml")["releases"]["3.7.0-rc.1"]
    capabilities = list(rc1_meta["capabilities"]) + [
        "gate-generated-canonical-voxel-fixtures-for-euler-poincare-homology",
        "mandatory-non-vacuous-probe-validation-for-g3k-g5q-g5r-g3l",
        "declarative-slot-hard-tolerance-ceiling-identity-and-tautology-rejection",
        "fail-closed-14-slot-consolidation-with-per-slot-subcheck-counts",
        "abstractmethod-aware-docstring-constant-return-and-disguised-not-implemented-stub-detection",
        "self-audit-magic-number-file-size-and-falsegreen-enforcement-with-visible-waivers",
        "co-located-negative-control-suite-for-every-verdict-gate",
        "force-pass-mutation-adequacy-gate-and-python-optimize-refusal",
    ]
    return {
        "status": "validated",
        "observed_at": OBSERVED_AT,
        "entry_point": "SKILL.md",
        "source_snapshot": source_rel,
        "tree_sha256": legacy_hash,
        "depends_on": [],
        "runtime_requirements": rc1_meta["runtime_requirements"],
        "capabilities": capabilities,
        "limitations": [
            "Tier-2 full 7-Gate verification requires instantiating a StationVerificationSpec and an algorithmically independent oracle on small inputs",
            "Declared file-size waivers W1 (engine ~9.9k lines) and W2 (self-test suite ~1.45k lines) remain open debt",
            "G5r and G3k probes are caller-supplied; the gate rejects missing or base-identical probes but cannot prove probe geometry is adversarial",
            "G5n magic-number check is off by default in the public API (on in --audit-self); Tier-1 receipts can PASS with few active slots (see inactive_slots)",
            "G5e/G6p pair-diff complexity collapse only applies to functions with baseline McCabe >= 5",
            "bin/verify.py still accepts >= 13 of 14 slots and does not read subchecks_verified_count",
        ],
        "provenance": (
            "Anti-Goodhart remediation of 3.7.0-rc.1 (review 2026-11-09/10: 24/55 gates undetectable by self-test, "
            "self-audit blind spots, weakened placeholder regex, vacuous caller-supplied probes, fail-open slot map). "
            f"Validation evidence: {evidence_rel} (sha256 {evidence_sha})."
        ),
    }


def build_workflow_doc() -> Dict[str, Any]:
    rc1_doc = verify.read_manifest(AWF_ROOT / f"workflows/{WF_ID}/releases/3.7.0-rc.1/workflow.yaml")
    doc = dict(rc1_doc)
    doc["release"] = REL_ID
    doc["status"] = "validated"
    doc["purpose"] = rc1_doc["purpose"].replace("v3.7.0-rc.1", "v3.7.0-rc.2") + (
        " rc.2 adds negative controls for every verdict gate, a force-PASS mutation-adequacy gate, fail-closed slot "
        "consolidation and non-vacuous probe validation."
    )
    doc["engineering_gate"] = rc1_doc["engineering_gate"] + (
        " The engine itself carries declared, report-visible file-size waivers W1/W2 (tracked debt, not exemptions "
        "for audited target code)."
    )
    return doc


def _assert_not_registered() -> None:
    comp_doc = verify.read_manifest(AWF_ROOT / "components/skills/anti-goodhart-verification/component.yaml")
    if REL_ID in comp_doc.get("releases", {}):
        raise RuntimeError(f"{COMP_ID}@{REL_ID} is already registered; Releases are immutable.")
    for rel in (f"workflows/{WF_ID}/releases/{REL_ID}/workflow.yaml", f"workflows/{WF_ID}/releases/{REL_ID}/versions.lock"):
        if (AWF_ROOT / rel).exists():
            raise RuntimeError(f"Refusing to overwrite existing {rel}")


def _backup(paths: List[Path], stamp: str) -> List[str]:
    out = []
    for p in paths:
        dst = AWF_ROOT / "backups" / f"{p.stem}-before-{WF_ID}-{REL_ID}-{stamp}{p.suffix}"
        if dst.exists():
            raise RuntimeError(f"Backup target already exists: {dst}")
        shutil.copy2(p, dst)
        out.append(str(dst.relative_to(AWF_ROOT)))
    return out


def _write_new_file(path: Path, data: Dict[str, Any]) -> None:
    if path.exists():
        raise RuntimeError(f"Refusing to overwrite existing {path}")
    write_json_yaml(path, data)


def _update_registry(comp_desc_sha: str, attestation_rel: str, wf_paths: Dict[str, str]) -> None:
    registry_path = AWF_ROOT / "registry.yaml"
    registry = verify.read_manifest(registry_path)
    comp = next(c for c in registry["components"] if c.get("id") == COMP_ID)
    comp["latest_release"] = REL_ID
    comp["descriptor_sha256"] = comp_desc_sha
    registry.setdefault("global_components", {})[COMP_ID] = REL_ID
    if attestation_rel not in registry.setdefault("integrity_attestations", []):
        registry["integrity_attestations"].append(attestation_rel)
    req_list = registry["integrity_policy"]["required_release_attestations"]
    if f"{COMP_ID}@{REL_ID}" not in req_list:
        req_list.append(f"{COMP_ID}@{REL_ID}")
        req_list.sort()
    wf_entry = next(w for w in registry["workflows"] if w.get("id") == WF_ID)
    wf_entry.update({**wf_paths, "status": "validated"})
    wf_entry.setdefault("releases", {})[REL_ID] = {**wf_paths, "status": "validated"}
    write_json_yaml(registry_path, registry)


def register(validation: Dict[str, Any]) -> Dict[str, Any]:
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    source_rel = f"components/skills/anti-goodhart-verification/releases/{REL_ID}/source"
    source_dir = AWF_ROOT / source_rel
    comp_descriptor_rel = "components/skills/anti-goodhart-verification/component.yaml"
    comp_descriptor_path = AWF_ROOT / comp_descriptor_rel
    backups = _backup([AWF_ROOT / "registry.yaml", comp_descriptor_path], stamp)

    evidence_rel = f"reports/{WF_ID}-{REL_ID}-release-validation-{stamp}.json"
    _write_new_file(AWF_ROOT / evidence_rel, {"component": f"{COMP_ID}@{REL_ID}", "observed_at": stamp, **validation})
    evidence_sha = verify.file_sha256(AWF_ROOT / evidence_rel)

    legacy_hash = verify.tree_sha256(source_dir)
    v2_paths = verify.tree_v2_paths(source_dir, "tree")
    release_meta = build_release_meta(source_rel, legacy_hash, evidence_rel, evidence_sha)
    comp_doc = verify.read_manifest(comp_descriptor_path)
    comp_doc.setdefault("releases", {})[REL_ID] = release_meta
    write_json_yaml(comp_descriptor_path, comp_doc)
    comp_desc_sha = verify.file_sha256(comp_descriptor_path)

    attestation_rel = f"attestations/release-integrity-{OBSERVED_AT.replace('-', '')}-anti-goodhart-verification-v3-7-rc2.yaml"
    _write_new_file(AWF_ROOT / attestation_rel, {
        "schema_version": 1,
        "digest_contract": "awf-tree-v2",
        "observed_at": OBSERVED_AT,
        "owner": "awf-anti-goodhart-verification-release-20261110-v3-7-rc2",
        "provenance": f"Validated (self-test + audit-self + mutation adequacy + -O refusal) release {REL_ID}; evidence {evidence_rel}.",
        "releases": {
            f"{COMP_ID}@{REL_ID}": {
                "coverage": "tree",
                "descriptor": comp_descriptor_rel,
                "descriptor_file_sha256": comp_desc_sha,
                "entry_count": len(v2_paths),
                "legacy_tree_sha256": legacy_hash,
                "metadata_sha256": verify.canonical_object_sha256(release_meta),
                "regular_file_bytes": sum(p.lstat().st_size for p in v2_paths if not p.is_symlink() and p.is_file()),
                "root": source_rel,
                "symlink_count": sum(p.is_symlink() for p in v2_paths),
                "tree_sha256": verify.tree_sha256_v2(source_dir, "tree"),
            }
        },
    })

    wf_descriptor_rel = f"workflows/{WF_ID}/releases/{REL_ID}/workflow.yaml"
    wf_lock_rel = f"workflows/{WF_ID}/releases/{REL_ID}/versions.lock"
    _write_new_file(AWF_ROOT / wf_descriptor_rel, build_workflow_doc())
    _write_new_file(AWF_ROOT / wf_lock_rel, {
        "schema_version": 1, "workflow": WF_ID, "workflow_release": REL_ID, "locked_at": OBSERVED_AT,
        "components": {COMP_ID: REL_ID},
    })
    wf_paths = {
        "descriptor": wf_descriptor_rel,
        "descriptor_sha256": verify.file_sha256(AWF_ROOT / wf_descriptor_rel),
        "lock": wf_lock_rel,
        "lock_sha256": verify.file_sha256(AWF_ROOT / wf_lock_rel),
    }
    _update_registry(comp_desc_sha, attestation_rel, wf_paths)
    return {"backups": backups, "evidence": evidence_rel, "attestation": attestation_rel, **wf_paths}


def main(argv: List[str] = None) -> int:
    parser = argparse.ArgumentParser(description=f"Validate and register {COMP_ID}@{REL_ID}")
    parser.add_argument("--dry-run", action="store_true", help="Run release validation only; write nothing")
    args = parser.parse_args(argv)
    _assert_not_registered()
    validation = run_release_validation()
    print(json.dumps({"passed": validation["passed"], "checks": validation["checks"], "summary": validation["summary"]}, indent=2))
    if not validation["passed"]:
        print("Release validation FAILED; nothing registered.", file=sys.stderr)
        return 1
    if args.dry_run:
        return 0
    print(json.dumps(register(validation), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
