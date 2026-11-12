#!/usr/bin/env python3
"""Read-only adversarial comparison of frozen Guard rc.7 + Verifier rc.2 vs remediated rc.8 + Verifier rc.3 across all 8 audit clusters."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "registry.yaml").is_file())
RC7_GUARD = ROOT / "components/skills/anti-goodhart-verification/releases/3.7.0-rc.7/source"
RC8_GUARD = ROOT / "components/skills/anti-goodhart-verification/releases/3.7.0-rc.8/source"
RC2_TOOL = ROOT / "components/tools/awf-repository-verifier/releases/1.0.0-rc.2/source"
RC3_TOOL = ROOT / "components/tools/awf-repository-verifier/releases/1.0.0-rc.3/source"

PROBE_SNIPPET = r"""
import copy, json, sys
import numpy as np
from pathlib import Path

guard_dir = Path(sys.argv[1]) / "scripts"
tool_dir = Path(sys.argv[2])
valid_receipt_path = Path(sys.argv[3])
sys.path[:0] = [str(tool_dir), str(guard_dir)]

from awf_guard import api as ag
from awf_guard.execution_flow import execute_stage
from awf_guard.numeric_inputs import _kwargs_materially_differ
from guard_receipt_contract import validate_guard_receipt

out = {}

# Cluster 1: Forged Tier-2 receipt accepted by Verifier 1.0.0-rc.2 (requires_human_approval=True,
# borderline_warnings non-empty, gate6_dynamic_calls=0, gate2_oracle_err=999.0, probe_tolerance=1e9, nested status="FAIL")
forged = json.loads(valid_receipt_path.read_text(encoding="utf-8"))
forged["requires_human_approval"] = True
forged["borderline_warnings"] = ["borderline hugging warning ignored"]
forged["gate6_dynamic_calls"] = 0
forged["gate2_oracle_err"] = 999.0
forged["gate2b_analytic_gradient_fd"] = {"status": "FAIL"}
if isinstance(forged.get("gate7h_red_blue_adversarial_audit"), dict):
    forged["gate7h_red_blue_adversarial_audit"]["probe_tolerance"] = 1e9
out["cluster1_forged_receipt_accepted"] = (len(validate_guard_receipt(forged, 0)) == 0)

# Cluster 2: SealedHoldoutCapsule vars() exposure + >3 queries + bare ndarray unit bypass
cap = ag.SealedHoldoutCapsule("gap", 1.25, 0.01)
vars_leaked = any("target" in k for k in vars(cap))
many_queries_ok = True
try:
    for q in (0.1, 0.2, 0.3, 0.4, 0.5):
        cap.evaluate_blind(q)
except Exception:
    many_queries_ok = False
bare_unit_accepted = True
try:
    @ag.scientific_atom(
        atom_id="ATOM-AUDIT-UNIT-01",
        tutor_station="ST-01",
        math_contract="y = 2 * x",
        inputs={"x": ag.TensorSpec(shape=("N",), unit="eV")},
        outputs={"y": ag.TensorSpec(shape=("N",), unit="eV")},
    )
    def _atom_fn(x):
        return x * 2.0
    _atom_fn(np.ones(2))
except Exception:
    bare_unit_accepted = False
out["cluster2_capsule_or_unit_bypass"] = bool(vars_leaked or many_queries_ok or bare_unit_accepted)

# Cluster 3: Runtime indirect oracle reentry + unused **kwargs probe spoofing
def target_add1(x):
    return x + 1

def indirect_reentry(x):
    return globals()["target_add1"](x)

reentry_accepted = True
try:
    res = ag.evaluate_red_blue_adversarial_audit(
        target_fn=target_add1,
        reference_or_invariant_fn=indirect_reentry,
        adversarial_probe_inputs=[{"x": 2}],
        solver_source_code="def target_add1(x):\n    return x + 1\n",
    )
    reentry_accepted = (res.get("status") == "PASS")
except Exception:
    reentry_accepted = False

def sink_fn(x, **_unused):
    return x

try:
    varkw_spoof = _kwargs_materially_differ({"x": 1.0}, {"x": 1.0, "dummy": 2.0}, target_fn=sink_fn)
except TypeError:
    varkw_spoof = _kwargs_materially_differ({"x": 1.0}, {"x": 1.0, "dummy": 2.0})
out["cluster3_reentry_or_varkw_bypass"] = bool(reentry_accepted or varkw_spoof)

# Cluster 4: G5q 26-voxel shape+sum memorizer + G5s unweighted ddof=1 Kish cheat + G2b flat zero-grad
shell = np.zeros((7, 7, 7))
shell[2:5, 2:5, 2:5] = 1.0
shell[3, 3, 3] = 0.0
punct = shell.copy()
punct[2, 2, 2] = 0.0
g5q_cheat = ag.verify_euler_poincare_and_digital_duality(
    lambda g: np.array([1.0, 0.0, 1.0, 2.0]) if int(np.sum(g)) == (6 * (g.shape[0] - 4) ** 2 - 12 * (g.shape[0] - 4) + 8) else np.array([1.0, 0.0, 0.0, 1.0]),
    {"g": shell},
    {"g": punct},
)
vals = np.array([3.45, 3.5, 3.55, 3.6])
def bessel_cheat(vals, weights):
    pos = vals[weights > 0]
    mu = float(np.average(vals, weights=weights))
    sd = float(np.std(pos, ddof=1))
    g_raw = sd / mu * 100.0
    return np.array([mu, sd, g_raw, g_raw / float(np.sqrt(2.0 * np.pi))], dtype=np.float64)
g5s_cheat = ag.verify_weighted_dispersion_kish_and_scale_invariance(
    bessel_cheat,
    {"vals": vals, "weights": np.ones(4)},
    "vals",
    zero_weight_padded_kwargs={"vals": np.append(vals, [25.0, 50.0]), "weights": np.array([1.0, 1.0, 1.0, 1.0, 0.0, 0.0])},
)
g2b_cheat = ag.verify_analytic_gradient_finite_difference(
    lambda r: float(np.sum(r ** 4)),
    lambda r: np.zeros_like(r),
    {"r": np.zeros(2)},
    is_negative_gradient=False,
)
out["cluster4_scientific_gate_bypass"] = bool(
    g5q_cheat.get("status") == "PASS" or g5s_cheat.get("status") == "PASS" or g2b_cheat.get("status") == "PASS"
)

# Cluster 5: G3d fake output-dependent relation + G3g nested array index-1500 mutation
mr_fake_outdep = ag.MetamorphicRelationSpec(
    mr_id="fake_outdep",
    data=[1.0, 2.0],
    general_transform_fn=lambda mtc: mtc.source_input + 1.0,
    general_relation_fn=lambda mtc: True,
)
mr_res = ag.execute_metamorphic_relation_suite(lambda x: x * 2.0, [mr_fake_outdep])
g3d_unflagged = mr_res["reports"][0].get("source_outputs_accessed", True) is True
def tail_mut(payload):
    payload["arr"][1500] = 99.0
    return float(payload["arr"][0])
g3g_res = ag.verify_pure_input_immutability_and_contracts(tail_mut, {"payload": {"arr": np.ones(2000)}})
out["cluster5_metamorphic_or_snapshot_bypass"] = bool(g3d_unflagged or g3g_res.get("status") == "PASS")

# Cluster 6: G5n tuple literal stub / hyphenated TODO + FalseGreen assert [1] / swallowed assert
g5n_tup = ag.scan_source_for_todo_placeholders_and_magic_numbers("def f(x):\n    return (0.0, 0.0)\n")
g6k_lit = ag.audit_test_suite_falsegreen_and_mock_abuse("def test_x():\n    assert [1]\n")
out["cluster6_static_or_falsegreen_bypass"] = bool(g5n_tup.get("status") == "PASS" or g6k_lit.get("status") == "PASS")

# Cluster 7: Narrowed -k receipt accepted as PASS for "All unit tests pass."
narrow = ag.CommandReceipt(command="pytest -k subset", exit_code=0, started_at=10.0, finished_at=20.0, output_tail="1 passed")
claim_res = ag.verify_agent_turn_claims("All unit tests pass.", command_receipts=[narrow], last_edit_mtime=5.0)
out["cluster7_narrowed_claim_bypass"] = (claim_res.get("status") == "PASS")

# Cluster 8: Stage borderline_warnings KeyError crash + 9 non-prefix gates missing from mutation adequacy
import awf_anti_goodhart_mutation_adequacy as mut_mod
discovered_names = set(mut_mod.discover_gate_functions())
nonprefix_unmutated = "validate_information_boundary" not in discovered_names
dest = {"gates_passed": [], "borderline_warnings": []}
borderline_stage_broken = False
try:
    execute_stage(lambda receipt: receipt["borderline_warnings"].append("borderline_ok"), dest)
    if dest["borderline_warnings"] != ["borderline_ok"]:
        borderline_stage_broken = True
except Exception:
    borderline_stage_broken = True
out["cluster8_stage_borderline_or_meta_gap"] = bool(borderline_stage_broken or nonprefix_unmutated)

print(json.dumps(out))
"""


def _fingerprint_frozen() -> dict[str, str]:
    roots = [
        RC7_GUARD,
        RC2_TOOL,
        ROOT / "workflows/anti-goodhart-verification/releases/3.7.0-rc.7",
    ]
    files = sorted(
        (p for r in roots for p in r.rglob("*") if p.is_file() and "__pycache__" not in p.parts),
        key=lambda p: p.relative_to(ROOT).as_posix(),
    )
    return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}


def _run_pair(guard_source: Path, tool_source: Path, valid_receipt: Path) -> dict[str, bool]:
    proc = subprocess.run(
        [sys.executable, "-B", "-c", PROBE_SNIPPET, str(guard_source), str(tool_source), str(valid_receipt)],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(proc.stdout)


def main() -> int:
    before = _fingerprint_frozen()
    rc7_fixture = RC2_TOOL / "fixtures/guard-valid-receipt.json"
    rc8_fixture = RC3_TOOL / "fixtures/guard-valid-receipt.json"
    if not rc8_fixture.is_file():
        rc8_fixture = rc7_fixture
    rc7_exploits = _run_pair(RC7_GUARD, RC2_TOOL, rc7_fixture)
    rc8_exploits = _run_pair(RC8_GUARD, RC3_TOOL, rc8_fixture)
    frozen_unchanged = before == _fingerprint_frozen()
    all_reproduced_on_rc7 = all(rc7_exploits.values())
    zero_exploits_on_rc8 = not any(rc8_exploits.values())
    passed = frozen_unchanged and all_reproduced_on_rc7 and zero_exploits_on_rc8
    report = {
        "status": "PASS" if passed else "FAIL",
        "frozen_release_unchanged": frozen_unchanged,
        "rc7_rc2_exploitable_clusters": rc7_exploits,
        "rc8_rc3_exploitable_clusters": rc8_exploits,
    }
    print(json.dumps(report, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
