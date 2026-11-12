#!/usr/bin/env python3
"""Independent read-only anti-Goodhart probe of skill.anti-goodhart-verification@3.7.0-rc.1.

Part A: self-audit blind spots (file size, G5n magic-number switch, falsegreen on the self-test suite).
Part B: mutation adequacy of the self-test (force-PASS mutants of every public gate function).
Part C: adversarial inputs that a sound gate should reject.
"""
from __future__ import annotations

import ast
import contextlib
import io
import json
import multiprocessing as mp
import os
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
SRC = Path(os.environ.get(
    "AG_PROBE_SCRIPTS_DIR",
    "/home/zc/agent_workflows/components/skills/anti-goodhart-verification/releases/3.7.0-rc.1/source/scripts",
))
sys.path.insert(0, str(SRC))

import numpy as np  # noqa: E402

import awf_universal_anti_goodhart_gates as E  # noqa: E402
import awf_anti_goodhart_selftest_suite as T  # noqa: E402

GATE_PREFIXES = ("verify_", "evaluate_", "audit_", "scan_", "detect_")
ZERO_KEYS = ("finding_count", "violation_count", "issue_count", "hollow_finding_count", "mock_finding_count")
EMPTY_KEYS = ("violations", "findings", "hollow_findings", "mock_findings")


def quiet(fn, *a, **k):
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        return fn(*a, **k)


def part_a():
    out = {}
    for p in sorted(SRC.glob("*.py")):
        src = p.read_text(encoding="utf-8")
        on = E.scan_source_for_todo_placeholders_and_magic_numbers(src, check_magic_numbers=True)
        kinds = {}
        for f in on["findings"]:
            kinds.setdefault(f["kind"], 0)
            kinds[f["kind"]] += 1
        out[p.name] = {"lines": src.count("\n"), "g5n_with_magic_numbers_on": kinds}
    fg = E.audit_test_suite_falsegreen_and_mock_abuse((SRC / "awf_anti_goodhart_selftest_suite.py").read_text(encoding="utf-8"))
    out["selftest_suite_falsegreen"] = {k: fg[k] for k in ("status", "test_count", "hollow_finding_count", "mock_finding_count")}
    morph = quiet(T._verify_calibrated_morph_and_optics_pack_selftests)
    g3k = morph["rp2_director_and_reciprocal_spec"]
    out["fixture_g3k_slipped_equals_base"] = all(
        np.array_equal(np.asarray(g3k["slipped_stack_kwargs"][k]), np.asarray(g3k["base_input_kwargs"][k])) for k in g3k["base_input_kwargs"]
    )
    return out


def _force_pass(real):
    def mutant(*a, **k):
        try:
            r = real(*a, **k)
        except Exception:
            return {"status": "PASS", "violations": [], "findings": [], "finding_count": 0}
        if isinstance(r, list):
            return []
        if isinstance(r, dict):
            r = dict(r)
            r["status"] = "PASS"
            for key in EMPTY_KEYS:
                if isinstance(r.get(key), list):
                    r[key] = []
            for key in ZERO_KEYS:
                if key in r:
                    r[key] = 0
            if "effective_reward" in r:
                r["effective_reward"] = 1.0
        return r
    return mutant


def _run_mutant(name):
    os.chdir(tempfile.mkdtemp(prefix="agprobe_"))
    if name is not None:
        m = _force_pass(getattr(E, name))
        setattr(E, name, m)
        if hasattr(T, name):
            setattr(T, name, m)
    try:
        rc = quiet(T.run_comprehensive_54_gate_selftest)
        return name, "SURVIVED" if rc == 0 else f"KILLED(rc={rc})", ""
    except AssertionError as exc:
        return name, "KILLED(assert)", str(exc)[:120]
    except Exception as exc:
        return name, "KILLED(crash)", f"{type(exc).__name__}: {str(exc)[:120]}"


def part_b(workers=24):
    names = sorted(n for n in dir(E) if n.startswith(GATE_PREFIXES) and callable(getattr(E, n)))
    with mp.get_context("fork").Pool(workers, maxtasksperchild=1) as pool:
        res = pool.map(_run_mutant, [None] + names)
    base = res[0]
    rows = res[1:]
    survived = [r[0] for r in rows if r[1] == "SURVIVED"]
    return {
        "baseline": base[1],
        "mutants_total": len(rows),
        "survived": len(survived),
        "killed_assert": sum(r[1] == "KILLED(assert)" for r in rows),
        "killed_crash": sum(r[1] == "KILLED(crash)" for r in rows),
        "survivors": survived,
        "rows": rows,
    }


def _status(fn, *a, **k):
    try:
        r = quiet(fn, *a, **k)
        return r.get("status") if isinstance(r, dict) else r
    except Exception as exc:
        return f"RAISED {type(exc).__name__}"


def _c_topology_and_clearance():
    table = {"sealed": [1.0, 0.0, 1.0, 2.0], "punct": [1.0, 0.0, 0.0, 1.0], "path": [1.0, 0.0, 0.0, 1.0]}

    def lookup_homology(tag):
        return np.array(table[tag])

    g5q = _status(E.verify_euler_poincare_and_digital_duality, lookup_homology, {"tag": "sealed"}, {"tag": "punct"}, {"tag": "path"})
    ternary_src = "def hom(g):\n    return [1.0, 0.0, 1.0, 2.0] if float(sum(g)) == 26.0 else [1.0, 0.0, 0.0, 1.0]\n"
    g5d_on_selftest_style = len(E.detect_extensional_enumeration_and_dispatch(ast.parse(ternary_src)))

    def radius_blind_clearance(c_min, radii):
        v = 0.0 if c_min <= 0 else 50.0
        return np.array([100.0 - v, v, 0.5 * v, 0.2 * v])

    g5r = _status(
        E.verify_filtration_monotonicity_and_heterogeneous_radius_clearance,
        radius_blind_clearance, {"c_min": 0.2, "radii": [1.0, 1.0]}, {"c_min": -0.3, "radii": [1.0, 1.0]},
    )
    return {
        "G5q_lookup_table_homology_ignoring_geometry": g5q,
        "G5d_enumeration_findings_on_selftest_style_ternary": g5d_on_selftest_style,
        "G5r_radius_blind_operator_with_agent_chosen_probe": g5r,
    }


def _c_director_slip():
    def center_to_center(sub_normals, n_stack=6, slip=0.0):
        d = float(np.hypot(3.5, slip))
        return np.array([d, 2.0 * np.pi / d, 0.35 * n_stack, 0.25 * n_stack * float(np.mean(np.abs(sub_normals[:, 2])))])

    n6 = np.tile([[0.0, 0.0, 1.0]], (6, 1))
    base = {"sub_normals": n6, "n_stack": 6, "slip": 0.0}
    short = {"sub_normals": np.tile([[0.0, 0.0, 1.0]], (2, 1)), "n_stack": 2, "slip": 0.0}
    return {
        "G3k_buggy_slip_operator_probe_equals_base": _status(E.verify_rp2_director_gauge_and_reciprocal_conjugacy, center_to_center, base, slipped_stack_kwargs=dict(base), short_stack_kwargs=short),
        "G3k_buggy_slip_operator_probes_omitted": _status(E.verify_rp2_director_gauge_and_reciprocal_conjugacy, center_to_center, base),
        "G3k_control_real_slip_probe": _status(E.verify_rp2_director_gauge_and_reciprocal_conjugacy, center_to_center, base, slipped_stack_kwargs=dict(base, slip=1.0), short_stack_kwargs=short),
    }


def _c_declarative():
    def wrong_parity(x):
        return np.asarray(x) + 1.0

    base = {"x": np.array([1.0, 2.0])}
    flip = {"x": np.array([-1.0, -2.0])}
    ev = E.evaluate_universal_declarative_slots
    return {
        "decl_empty_slot_laws": _status(ev, wrong_parity, base, {}),
        "decl_false_invariance_tol_1e9": _status(ev, wrong_parity, base, {"s3_1_equivariance_laws": [{"name": "parity", "transformed_kwargs": flip, "tol": 1e9}]}),
        "decl_identity_transform_invariance": _status(ev, wrong_parity, base, {"s3_1_equivariance_laws": [{"name": "parity", "transformed_kwargs": dict(base)}]}),
        "decl_tautological_predicate": _status(ev, wrong_parity, base, {"s1_1_regime_probes": [{"name": "p", "input_kwargs": flip, "predicate_fn": lambda o: True}]}),
        "decl_control_false_invariance_default_tol": _status(ev, wrong_parity, base, {"s3_1_equivariance_laws": [{"name": "parity", "transformed_kwargs": flip}]}),
    }


def _c_g5n():
    g = E.scan_source_for_todo_placeholders_and_magic_numbers
    magic = "def energy(x):\n    return x * 3.14159 * 0.7213\n"
    return {
        "G5n_default_call_magic_numbers": _status(g, magic),
        "G5n_magic_numbers_on_control": _status(g, magic, check_magic_numbers=True),
        "G5n_constant_return_stub": _status(g, "def energy(x):\n    return 0.0\n"),
        "G5n_runtimeerror_stub": _status(g, "def energy(x):\n    raise RuntimeError('not implemented yet')\n"),
        "G5n_todo_in_docstring": _status(g, "def energy(x):\n    \"\"\"TODO: real physics.\"\"\"\n    return x\n"),
        "G5n_control_todo_comment": _status(g, "def energy(x):\n    # TODO real physics\n    return x\n"),
    }


def _c_station_and_slots():
    def degenerate(x):
        return np.zeros_like(x)

    spec = E.StationVerificationSpec(station_id="P1", station_name="degenerate", target_fn=degenerate, tier=1, small_input_kwargs={"x": np.ones(3)})
    try:
        rc = quiet(E.UniversalAntiGoodhartEngine.run_station_gates, spec)
        tier1 = {"verdict": rc["verdict_zone"], "slots": rc["gates_passed"], "subchecks": rc["subchecks_verified_count"]}
    except Exception as exc:
        tier1 = f"RAISED {type(exc).__name__}: {exc}"
    bogus = {"gates_passed": ["Totally_Made_Up_Check"]}
    try:
        E._consolidate_to_14_universal_slots(bogus)
    except E.AntiGoodhartGateError as exc:
        bogus["gates_passed"] = f"RAISED {type(exc).__name__}"
    one_per_slot = {}
    for sub, slot in E._SUBCHECK_TO_UNIVERSAL_SLOT_MAP.items():
        one_per_slot.setdefault(slot, sub)
    minimal = {"gates_passed": list(one_per_slot.values())}
    E._consolidate_to_14_universal_slots(minimal)
    return {
        "tier1_degenerate_zero_operator": tier1,
        "unknown_subcheck_label_maps_to": bogus["gates_passed"],
        "min_subchecks_for_14_of_14_slots": minimal["subchecks_verified_count"],
        "slots_from_minimal": minimal["universal_slot_count"],
    }


def part_c():
    out = {}
    for fn in (_c_topology_and_clearance, _c_director_slip, _c_declarative, _c_g5n, _c_station_and_slots):
        out.update(fn())
    return out


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    report = {"python": sys.version.split()[0], "optimize_flag": sys.flags.optimize, "engine": str(SRC)}
    if mode in ("all", "a"):
        report["A_self_audit_blind_spots"] = part_a()
    if mode in ("all", "c"):
        report["C_adversarial_probes"] = part_c()
    if mode in ("all", "b"):
        report["B_selftest_mutation_adequacy"] = part_b()
    if mode == "o":
        report["O_optimize_mutant"] = _run_mutant("verify_analytic_gradient_finite_difference")
    print(json.dumps(report, indent=2, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
