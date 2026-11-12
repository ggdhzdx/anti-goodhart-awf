#!/usr/bin/env python3
"""Replay adversarial caller specifications through the actual Guard 3.7.0-rc.8 station engine and Verifier 1.0.0-rc.3."""
from __future__ import annotations

import contextlib
import copy
import io
import json
import sys
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "registry.yaml").is_file())
S = ROOT / "components/skills/anti-goodhart-verification/releases/3.7.0-rc.8/source/scripts"
TOOL = ROOT / "components/tools/awf-repository-verifier/releases/1.0.0-rc.3/source"
sys.path[:0] = [str(S), str(TOOL)]
from awf_guard import api as ag  # noqa: E402
from awf_anti_goodhart_selftest_suite import run_comprehensive_54_gate_selftest  # noqa: E402
from guard_receipt_contract import validate_guard_receipt  # noqa: E402


def run() -> int:
    engine = ag.UniversalAntiGoodhartEngine
    original_descriptor = engine.__dict__["run_station_gates"]
    original = engine.run_station_gates
    rows = []

    def check_specs(spec, policy=ag.MetaBoundsPolicy()):
        target_fn = spec.scientific_computing_audit_spec["red_blue_adversarial_spec"]["target_fn"]

        def indirect_oracle_reentry(*args, **kwargs):
            return target_fn(*args, **kwargs)

        for case in ("empty_red_blue", "empty_remediation", "dead_assertion", "same_reference", "indirect_reentry", "bool_tier"):
            bad = copy.copy(spec)
            bad.scientific_computing_audit_spec = dict(spec.scientific_computing_audit_spec)
            for name in ("red_blue_adversarial_spec", "remediation_closed_loop_spec"):
                bad.scientific_computing_audit_spec[name] = dict(spec.scientific_computing_audit_spec[name])
            scientific = bad.scientific_computing_audit_spec
            if case == "empty_red_blue":
                scientific["red_blue_adversarial_spec"]["adversarial_probe_inputs"] = []
            elif case == "empty_remediation":
                scientific["remediation_closed_loop_spec"]["evaluation_inputs"] = []
            elif case == "dead_assertion":
                bad.falsegreen_test_audit_spec = {
                    "test_source_code": "def test_bad(value):\n    if False:\n        assert value == 2\n"
                }
            elif case == "same_reference":
                scientific["red_blue_adversarial_spec"]["reference_or_invariant_fn"] = target_fn
            elif case == "indirect_reentry":
                scientific["red_blue_adversarial_spec"]["reference_or_invariant_fn"] = indirect_oracle_reentry
            else:
                bad.tier = True
            caught = ""
            try:
                original(bad, policy)
            except (ValueError, TypeError, ag.AntiGoodhartGateError) as error:
                caught = str(error)
            if not caught:
                raise AssertionError("Full engine accepted: " + case)
            rows.append({"case": case, "rejected": True, "reason": caught[:180]})
        return original(spec, policy)

    engine.run_station_gates = staticmethod(check_specs)
    output = io.StringIO()
    try:
        with contextlib.redirect_stdout(output):
            rc = run_comprehensive_54_gate_selftest()
    finally:
        engine.run_station_gates = original_descriptor
    good = json.loads(output.getvalue())
    errors = validate_guard_receipt(good, rc)
    if errors:
        raise AssertionError(errors)
    historical_rc6 = json.loads((TOOL / "fixtures/guard-rc6-vacuous-receipt.json").read_text(encoding="utf-8"))
    rc6_errors = validate_guard_receipt(historical_rc6)
    if not rc6_errors:
        raise AssertionError("Historical rc.6 false PASS receipt accepted")
    forged_rc7 = json.loads((TOOL / "fixtures/guard-rc7-forged-receipt.json").read_text(encoding="utf-8"))
    rc7_errors = validate_guard_receipt(forged_rc7)
    if not rc7_errors:
        raise AssertionError("Historical rc.7 forged receipt accepted")
    print(
        json.dumps(
            {
                "status": "PASS",
                "bad_inputs_rejected": rows,
                "honest_receipt_accepted": True,
                "historical_rc6_false_pass_rejected": rc6_errors,
                "historical_rc7_forged_receipt_rejected": rc7_errors,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
