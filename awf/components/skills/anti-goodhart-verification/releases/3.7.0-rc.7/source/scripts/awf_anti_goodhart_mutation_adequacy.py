#!/usr/bin/env python3
"""
Self-test mutation-adequacy gate for AWF Guard (`skill.anti-goodhart-verification@3.7.0-rc.2`).

Replaces every public gate function (`verify_*`, `evaluate_*`, `audit_*`, `scan_*`, `detect_*`) in turn with a
verdict-aware force-PASS mutant (PASS/accepted/fair/no-escalation verdict fields, empty findings, zero counts,
swallowed gate exceptions) and re-runs the full self-test in an isolated forked process. A surviving mutant means
the self-test cannot tell that gate apart from an always-PASS stub. Exit code 0 only if zero non-exempt survivors.
"""
from __future__ import annotations

import argparse
import contextlib
import inspect
import io
import json
import multiprocessing as mp
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

sys.dont_write_bytecode = True
_SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPTS_DIR))

from awf_guard_test_bindings import replace_loaded_bindings
import awf_universal_anti_goodhart_gates as ENGINE  # noqa: E402
import awf_anti_goodhart_negative_controls as NEGATIVE  # noqa: E402
import awf_anti_goodhart_selftest_suite as SUITE  # noqa: E402

GATE_PREFIXES: Tuple[str, ...] = ("verify_", "evaluate_", "audit_", "scan_", "detect_")
DECLARED_EXEMPTIONS: Dict[str, str] = {
    "evaluate_adaptive_runtime_budget": "Non-verdict utility: returns a latency-based sampling budget, has no PASS/FAIL semantics.",
}
_FORCED_VERDICT_FIELDS: Dict[str, Any] = {
    "status": "PASS",
    "accepted": True,
    "fairness": 1,
    "passed": True,
    "autonomous_resolution": True,
    "requires_human_escalation": False,
    "friendly_fire_over_tightened": False,
    "breach_sealed": True,
    "effective_reward": 1.0,
}
_EMPTIED_LIST_FIELDS = ("violations", "findings", "hollow_findings", "mock_findings", "escalation_reasons", "matrix_violations")
_ZEROED_COUNT_FIELDS = ("finding_count", "violation_count", "issue_count", "hollow_finding_count", "mock_finding_count")


def _forced_pass_result(result: Any) -> Any:
    if isinstance(result, list):
        return []
    if not isinstance(result, dict):
        return result
    forced = dict(result)
    for key, val in _FORCED_VERDICT_FIELDS.items():
        if key in forced:
            forced[key] = val
    for key in _EMPTIED_LIST_FIELDS:
        if isinstance(forced.get(key), list):
            forced[key] = []
    for key in _ZEROED_COUNT_FIELDS:
        if key in forced:
            forced[key] = 0
    return forced


def build_force_pass_mutant(real_fn: Callable[..., Any]) -> Callable[..., Any]:
    returns_none = str(inspect.signature(real_fn).return_annotation) in ("None", "<class 'NoneType'>")

    def mutant(*args: Any, **kwargs: Any) -> Any:
        try:
            return _forced_pass_result(real_fn(*args, **kwargs))
        except Exception:
            return None if returns_none else {"status": "PASS", "accepted": True, "violations": [], "findings": []}

    return mutant


def discover_gate_functions() -> List[str]:
    return sorted(n for n in dir(ENGINE) if n.startswith(GATE_PREFIXES) and inspect.isfunction(getattr(ENGINE, n)))


def run_single_mutant(name: Optional[str]) -> Tuple[Optional[str], str, str, List[str]]:
    os.chdir(tempfile.mkdtemp(prefix="ag_mutadq_"))
    bindings = []
    if name is not None:
        mutant = build_force_pass_mutant(getattr(ENGINE, name))
        changes = replace_loaded_bindings(getattr(ENGINE, name), mutant)
        bindings = [f"{module.__name__}.{key}" for module, key, original in changes]
        if not bindings:
            raise RuntimeError(f"No real bindings patched for {name}")
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            rc = SUITE.run_comprehensive_54_gate_selftest()
        return name, ("SURVIVED" if rc == 0 else f"KILLED_RC_{rc}"), "", bindings
    except AssertionError as exc:
        return name, "KILLED_ASSERT", str(exc)[:160], bindings
    except Exception as exc:
        return name, "KILLED_CRASH", f"{type(exc).__name__}: {str(exc)[:160]}", bindings


def evaluate_mutation_adequacy(workers: int = 16, names: Optional[Sequence[str]] = None) -> Dict[str, Any]:
    targets = list(names) if names else discover_gate_functions()
    with mp.get_context("fork").Pool(max(1, int(workers)), maxtasksperchild=1) as pool:
        rows = pool.map(run_single_mutant, [None] + targets)
    baseline, mutants = rows[0], rows[1:]
    survivors = [r[0] for r in mutants if r[1] == "SURVIVED" and r[0] not in DECLARED_EXEMPTIONS]
    exempt_survivors = [r[0] for r in mutants if r[1] == "SURVIVED" and r[0] in DECLARED_EXEMPTIONS]
    passed = baseline[1] == "SURVIVED" and not survivors
    return {
        "status": "PASS" if passed else "FAIL",
        "baseline_selftest": baseline[1],
        "mutants_total": len(mutants),
        "killed_by_assertion": sum(r[1] == "KILLED_ASSERT" for r in mutants),
        "killed_by_crash": sum(r[1] == "KILLED_CRASH" for r in mutants),
        "survivors": survivors,
        "declared_exempt_survivors": exempt_survivors,
        "declared_exemptions": DECLARED_EXEMPTIONS,
        "rows": [{"gate": r[0], "outcome": r[1], "detail": r[2], "patched_bindings": r[3]} for r in mutants],
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="AWF Guard self-test force-PASS mutation adequacy gate")
    parser.add_argument("--workers", type=int, default=16)
    parser.add_argument("--only", nargs="*", help="Restrict to these gate function names")
    args = parser.parse_args(argv)
    report = evaluate_mutation_adequacy(workers=args.workers, names=args.only)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
