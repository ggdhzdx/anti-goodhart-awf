#!/usr/bin/env python3
"""Finalize Guard 3.7.0-rc.8 and Verifier 1.0.0-rc.3 documentation, navigation map, and receipt fixtures."""
from __future__ import annotations

import ast
import copy
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "registry.yaml").is_file())
HERE = Path(__file__).resolve().parent
SOURCE = ROOT / "components/skills/anti-goodhart-verification/releases/3.7.0-rc.8/source"
TOOL = ROOT / "components/tools/awf-repository-verifier/releases/1.0.0-rc.3/source"


def _update_docs() -> None:
    skill = SOURCE / "SKILL.md"
    text = skill.read_text(encoding="utf-8")
    text = text.replace("3.7.0-rc.7", "3.7.0-rc.8").replace("publish_guard_rc7.py", "publish_guard_rc8.py")
    text = text.replace("verify_full_route_rc7.py", "verify_full_route_rc8.py")
    text = text.replace("tool.awf-repository-verifier@1.0.0-rc.2", "tool.awf-repository-verifier@1.0.0-rc.3")
    rc8_heading = "## rc.8 full-closure anti-Goodhart remediation"
    if rc8_heading not in text:
        text += f"""
{rc8_heading}

- **Vault-sealed holdout capsule & unit enforcement (`information`, `tensor_contracts`, `atoms`)**: `SealedHoldoutCapsule` stores secrets in a module-private `WeakKeyDictionary` outside `vars(self)` and closure cells, caps distinct blind evaluations at 3 per capsule, and quantizes `ratio_to_tol` into coarse bands. `TensorSpec(unit != "dimensionless")` rejects bare `np.ndarray`/scalars by default unless `QuantityTensor(data, unit=...)` is supplied (or `allow_untagged_array=True` is explicitly declared and recorded in `GLOBAL_ATOM_REGISTRY`). `ast.Nonlocal` is rejected in `@scientific_atom`.
- **Runtime reentry & unused-varkw probe guards (`evidence_contracts`, `numeric_inputs`, `spec_integrity`)**: `call_without_target_reentry` installs a `sys.setprofile` monitor rejecting any reference/oracle callback that invokes `target_fn` at runtime (directly or via dynamic lookup). `_kwargs_materially_differ` inspects bytecode to ignore dead `**kwargs` sinks and asymmetric tag keys while preserving legitimate forwarding wrappers.
- **Scientific, metamorphic, snapshot & static hardening (`differential_checks`, `symmetry_checks`, `statistical_checks`, `matrix_checks`, `geometry`, `metamorphic`, `input_contracts`, `source_quality`, `test_quality`, `claims`)**: `G5m` preserves `complex128` Hermiticity (`M == M^H`); `G5q` adds 27-voxel `sealed_tab_odd` and 26-voxel `punct_tab_even` shells defeating shape+voxel-sum memorizers; `G5s` verifies the exact 3-vs-6 skewed Kish identity `sd([1,1,4])/sd([1]*6) == sqrt(5/3)`; `G2b` rejects flat-point zero-gradient collapse; `G3d` verifies `mtc.source_outputs` access during `general_transform_fn`; `G3g` recursively hashes nested containers and full array byte buffers; `G7c` rejects `PASS` when only scope-narrowed (`-k`) or zero-test receipts exist; `execute_stage` rolls back `borderline_warnings` on stage failure.
- **64-function force-PASS mutation adequacy & Verifier `1.0.0-rc.3`**: `awf_anti_goodhart_mutation_adequacy.py` covers all 55 prefix gates plus 9 non-prefix verdict/scoring functions (`64` total, `0` non-exempt survivors, `0` crashes). `tool.awf-repository-verifier@1.0.0-rc.3` enforces `type(tier) is int and tier == 2`, `requires_human_approval is False`, `borderline_warnings == []`, non-vacuous execution evidence across all 14 slots and 20 scientific/tutor sub-receipts, subprocess isolation, and Linux `lsattr` immutability checks across full Guard and verifier closures.

Adversarial 8-cluster replay: `workflows/anti-goodhart-verification/releases/3.7.0-rc.8/source/ag_review_rc7.py` and `verify_full_route_rc8.py`.
"""
    skill.write_text(text, encoding="utf-8")

    architecture = SOURCE / "ARCHITECTURE.md"
    arch_text = architecture.read_text(encoding="utf-8").replace("# Guard rc.7:", "# Guard rc.8:")
    rc8_arch_heading = "## rc.8 closure hardening"
    if rc8_arch_heading not in arch_text:
        arch_text += f"""
{rc8_arch_heading}

`evidence_contracts` enforces runtime `sys.setprofile` non-reentry (`call_without_target_reentry`) in addition to static callable-origin distinctness. `information` isolates holdout secrets in a module-private `WeakKeyDictionary` vault and checks nested forbidden keys recursively. `tensor_contracts` enforces `QuantityTensor` unit tags on dimensional specs by default. `execution_flow` stages `borderline_warnings` alongside `gates_passed` so aborted stages leave zero state residue. Independent verifier `1.0.0-rc.3` validates non-vacuous execution evidence across all 14 canonical slots and runs engine checks in isolated `-B` subprocesses.
"""
    architecture.write_text(arch_text, encoding="utf-8")

    owners, graph = {}, {}
    for path in sorted((SOURCE / "scripts/awf_guard").glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        graph[path.stem] = sorted(
            {n.module.split(".")[0] for n in tree.body if isinstance(n, ast.ImportFrom) and n.level and n.module}
        )
        for node in tree.body:
            if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
                owners[node.name] = path.stem
    (SOURCE / "module-map.json").write_text(
        json.dumps({"purpose": "Navigation only, not an acceptance target", "engine_owners": owners, "engine_dependencies": graph}, indent=2) + "\n",
        encoding="utf-8",
    )


def _update_verifier_fixtures_and_tests() -> None:
    engine = SOURCE / "scripts/awf_universal_anti_goodhart_gates.py"
    proc = subprocess.run([sys.executable, "-B", str(engine), "--self-test"], cwd=ROOT, capture_output=True, text=True, check=True)
    valid_receipt = json.loads(proc.stdout)
    fixtures_dir = TOOL / "fixtures"
    fixtures_dir.mkdir(exist_ok=True)
    (fixtures_dir / "guard-valid-receipt.json").write_text(json.dumps(valid_receipt, indent=2) + "\n", encoding="utf-8")

    forged_rc7 = copy.deepcopy(valid_receipt)
    forged_rc7["requires_human_approval"] = True
    forged_rc7["borderline_warnings"] = ["borderline hugging warning ignored by rc.2"]
    forged_rc7["gate6_dynamic_calls"] = 0
    forged_rc7["gate2_oracle_err"] = 999.0
    forged_rc7["gate2b_analytic_gradient_fd"] = {"status": "FAIL"}
    forged_rc7["gate7h_red_blue_adversarial_audit"]["probe_tolerance"] = 1e9
    (fixtures_dir / "guard-rc7-forged-receipt.json").write_text(json.dumps(forged_rc7, indent=2) + "\n", encoding="utf-8")

    (TOOL / "test_receipt_contract.py").write_text(
        '''"""Forged PASS receipts must be rejected by the independent verifier 1.0.0-rc.3 policy."""
import copy
import json
from pathlib import Path
from guard_receipt_contract import validate_guard_receipt


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def run():
    root = Path(__file__).resolve().parent
    original = json.loads((root / "fixtures/guard-valid-receipt.json").read_text(encoding="utf-8"))
    check(not validate_guard_receipt(original), "valid full rc.8 receipt rejected")
    cases = []
    for field, value in (
        ("tier", 1),
        ("tier", True),
        ("requires_human_approval", True),
        ("borderline_warnings", ["borderline warning"]),
        ("gate6_dynamic_calls", 0),
        ("gate2_oracle_err", 999.0),
        ("subchecks_verified_count", float("nan")),
        ("subchecks_verified_count", 999),
        ("negative_controls_total", 0),
        ("gates_passed", original["gates_passed"][:-1]),
        ("gates_passed", original["gates_passed"][:-1] + [original["gates_passed"][0]]),
        ("slot_subchecks_verified", {}),
        ("slot_subcheck_counts", {}),
    ):
        bad = copy.deepcopy(original)
        bad[field] = value
        cases.append((field, bad))

    bad = copy.deepcopy(original)
    for slot in bad["slot_subchecks_verified"]:
        bad["slot_subchecks_verified"][slot] = ["invented_check"]
        bad["slot_subcheck_counts"][slot] = 1
    bad["subchecks_verified_count"] = 14
    cases.append(("invented_one_per_slot", bad))

    bad = copy.deepcopy(original)
    slot = next(iter(bad["slot_subchecks_verified"]))
    bad["slot_subchecks_verified"][slot].pop()
    bad["slot_subcheck_counts"][slot] -= 1
    bad["subchecks_verified_count"] -= 1
    cases.append(("missing_required_check", bad))

    vacuous_rc6 = json.loads((root / "fixtures/guard-rc6-vacuous-receipt.json").read_text(encoding="utf-8"))
    cases.append(("real_rc6_vacuous_receipt", vacuous_rc6))
    forged_rc7 = json.loads((root / "fixtures/guard-rc7-forged-receipt.json").read_text(encoding="utf-8"))
    cases.append(("real_rc7_forged_receipt", forged_rc7))

    changes = [
        ("gate7h_red_blue_adversarial_audit", "executed_probe_count", 0),
        ("gate7h_red_blue_adversarial_audit", "requested_probe_count", 999),
        ("gate7h_red_blue_adversarial_audit", "reference_origin_distinct", False),
        ("gate7h_red_blue_adversarial_audit", "probe_tolerance", 1.0),
        ("gate6p_remediation_closed_loop", "candidate_leaderboard", []),
        ("gate6p_remediation_closed_loop", "requested_evaluation_count", 0),
        ("gate6p_remediation_closed_loop", "oracle_tolerance", float("nan")),
        ("gate6p_remediation_closed_loop", "oracle_tolerance", 1.0),
        ("gate6p_remediation_closed_loop", "selected_pareto_candidate", "not_evaluated"),
        ("gate6k_6l_falsegreen_test_audit", "assertion_analysis", "ast_presence_only"),
        ("gate6n_self_hosting_dogfood", "files_audited", []),
        ("gate6n_self_hosting_dogfood", "target_present", False),
        ("gate2b_analytic_gradient_fd", "status", "FAIL"),
    ]
    for gate, field, value in changes:
        bad = copy.deepcopy(original)
        bad[gate][field] = value
        cases.append((gate + "." + field, bad))

    bad = copy.deepcopy(original)
    bad["gate3d_output_dependent_metamorphic"][0]["source_outputs_accessed"] = False
    cases.append(("gate3d.source_outputs_not_accessed", bad))

    bad = copy.deepcopy(original)
    for row in bad["gate6p_remediation_closed_loop"]["candidate_leaderboard"]:
        row["executed_evaluation_count"] = 0
    cases.append(("candidates_never_executed", bad))

    for name, receipt in cases:
        check(bool(validate_guard_receipt(receipt)), f"forged receipt accepted: {name}")
    print(json.dumps({"status": "PASS", "positive": 1, "forged_receipts_rejected": len(cases)}))


if __name__ == "__main__":
    run()
''',
        encoding="utf-8",
    )

    (TOOL / "README.md").write_text(
        """# AWF repository verifier 1.0.0-rc.3

Preserves the repository verifier and independent 14-slot/74-subcheck receipt policy while closing rc.2 receipt-validation and subprocess-isolation gaps:
- Enforces exact integer `tier == 2` (rejecting boolean `True`), `requires_human_approval is False`, `borderline_warnings == []`, `gate6_dynamic_calls > 0`, and recursive nested sub-receipt failure vetoes.
- Validates non-vacuous execution evidence across all 14 canonical slots, all 20 scientific/tutor sub-receipts, `source_outputs_accessed is True` on output-dependent metamorphic relations (`G3d`), and bounded tolerances (`<= 1e-2`) on `G7h`/`G6p`.
- Runs Guard `--self-test` and `--audit-self` in isolated `python -B` subprocesses and checks Linux `lsattr` `i`-bit immutability across both verifier and Guard package closures.

Run `test_receipt_contract.py` to accept the `3.7.0-rc.8` positive fixture and reject forged receipts (including both `guard-rc6-vacuous-receipt.json` and `guard-rc7-forged-receipt.json`). Historical `1.0.0-rc.1` and `1.0.0-rc.2` releases remain untouched and frozen; `/home/zc/agent_workflows/bin/verify.py` points to this successor.
""",
        encoding="utf-8",
    )


def _normalize_permissions() -> None:
    exec_names = {
        "awf_universal_anti_goodhart_gates.py",
        "awf_anti_goodhart_mutation_adequacy.py",
        "verify.py",
        "ag_review_rc7.py",
        "bootstrap_rc8.py",
        "finalize_rc8.py",
        "publish_guard_rc8.py",
        "refresh_fixture_policy.py",
        "release_hashes.py",
        "verify_full_route_rc8.py",
    }
    for tree in (SOURCE, TOOL, HERE):
        os.chmod(tree, 0o755)
        for p in tree.rglob("*"):
            if p.is_symlink():
                continue
            if p.is_dir():
                os.chmod(p, 0o755)
            elif p.is_file():
                first_two = p.read_bytes()[:2]
                is_exec = p.name in exec_names or first_two == b"#!"
                os.chmod(p, 0o755 if is_exec else 0o644)


def main() -> int:
    subprocess.run([sys.executable, "-B", str(HERE / "refresh_fixture_policy.py")], check=True)
    _update_docs()
    _update_verifier_fixtures_and_tests()
    _normalize_permissions()
    print(json.dumps({"status": "PASS", "guard_source": str(SOURCE), "verifier_source": str(TOOL)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
