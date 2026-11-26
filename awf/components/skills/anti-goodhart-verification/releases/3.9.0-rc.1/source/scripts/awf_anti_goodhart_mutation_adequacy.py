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
ADDITIONAL_GATE_FUNCTIONS: Tuple[str, ...] = (
    "analyze_contract_and_docstring_intent",
    "analyze_receipt_weakness",
    "check_jaxtyping_shape_contract",
    "compute_guardrail_composite_score",
    "compute_ncc_test_overlap",
    "compute_verifier_safety_and_bestofk_gap",
    "execute_metamorphic_relation_suite",
    "score_trial_orthogonal_fairness",
    "validate_information_boundary",
)
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
    "verdict": "safe-to-deploy",
    "has_errors": False,
}
_EMPTIED_LIST_FIELDS = ("violations", "findings", "hollow_findings", "mock_findings", "escalation_reasons", "matrix_violations")
_ZEROED_COUNT_FIELDS = ("finding_count", "violation_count", "issue_count", "hollow_finding_count", "mock_finding_count")


def _forced_pass_result(fn_name: str, result: Any) -> Any:
    if fn_name == "analyze_receipt_weakness":
        return None
    if fn_name == "score_trial_orthogonal_fairness":
        return ENGINE.OrthogonalTrialScore(
            static_reward=1.0,
            fairness=1,
            solved_fairly=1.0,
            outcome="fair",
            retrieval_attempted=False,
            retrieval_succeeded=False,
            integrated=False,
            bypass_channels_detected=(),
            evidence="",
        )
    if fn_name == "compute_verifier_safety_and_bestofk_gap" and isinstance(result, dict):
        forced_vs = dict(result)
        forced_vs["naive"] = dict(result.get("naive", {}), safety_score=100.0)
        forced_vs["hardened"] = dict(result.get("hardened", {}), safety_score=100.0)
        forced_vs["bestofk"] = dict(result.get("bestofk", {}), naive_accuracy=1.0, hardened_accuracy=1.0, gap=0.0)
        return forced_vs
    if fn_name == "compute_ncc_test_overlap" and isinstance(result, dict):
        floor_val = result["ncc_floor"] if "ncc_floor" in result else 0.72
        return {"applicable": True, "ncc_score": 1.0, "ncc_floor": floor_val, "passed": True}
    if fn_name == "compute_guardrail_composite_score" and isinstance(result, dict):
        return {"score": 100.0, "verdict": "safe-to-deploy", "has_errors": False}
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


def _fallback_pass_result(fn_name: str, returns_none: bool, args: Tuple[Any, ...], kwargs: Dict[str, Any]) -> Any:
    if returns_none or fn_name == "analyze_receipt_weakness":
        return None
    if fn_name == "analyze_contract_and_docstring_intent":
        return []
    if fn_name == "validate_information_boundary":
        payload = args[0] if args else kwargs.get("payload", {})
        allowed = args[1] if len(args) > 1 else kwargs.get("allowed_keys", set())
        return {k: v for k, v in payload.items() if k in allowed} if isinstance(payload, dict) else {}
    if fn_name == "execute_metamorphic_relation_suite":
        rels = args[1] if len(args) > 1 else kwargs.get("relations", ())
        return {
            "status": "PASS",
            "relations_verified": len(rels),
            "reports": [
                {
                    "mr_id": getattr(mr, "mr_id", "mr"),
                    "number_of_sources": getattr(mr, "number_of_sources", 1),
                    "total_mtcs": 1,
                    "passed_mtcs": 1,
                    "skipped_mtcs": 0,
                    "source_outputs_accessed": True,
                }
                for mr in rels
            ],
        }
    if fn_name == "compute_verifier_safety_and_bestofk_gap":
        return {
            "naive": {"safety_score": 100.0},
            "hardened": {"safety_score": 100.0},
            "bestofk": {"n_tasks": 1, "naive_accuracy": 1.0, "hardened_accuracy": 1.0, "gap": 0.0},
        }
    return {"status": "PASS", "accepted": True, "violations": [], "findings": []}


def build_force_pass_mutant(real_fn: Callable[..., Any]) -> Callable[..., Any]:
    fn_name = getattr(real_fn, "__name__", "")
    returns_none = str(inspect.signature(real_fn).return_annotation) in ("None", "<class 'NoneType'>")

    def mutant(*args: Any, **kwargs: Any) -> Any:
        try:
            return _forced_pass_result(fn_name, real_fn(*args, **kwargs))
        except Exception:
            return _fallback_pass_result(fn_name, returns_none, args, kwargs)

    return mutant


def discover_gate_functions() -> List[str]:
    names = {
        n
        for n in dir(ENGINE)
        if (n.startswith(GATE_PREFIXES) or n in ADDITIONAL_GATE_FUNCTIONS) and inspect.isfunction(getattr(ENGINE, n))
    }
    return sorted(names)


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
