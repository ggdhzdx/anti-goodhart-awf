"""Inject NaN/Inf at real successful gate-call boundaries observed in the full suite."""
import contextlib
import copy
from functools import wraps
import inspect
import io
import json
import numbers
from pathlib import Path
import numpy as np
from awf_guard_test_bindings import replace_loaded_bindings, restore_bindings
import awf_universal_anti_goodhart_gates as engine
import awf_anti_goodhart_negative_controls as negative
import awf_anti_goodhart_selftest_suite as suite

ROWS = []
UNEXERCISED = []
SEEN = set()
VALUES = (float("nan"), float("inf"), -float("inf"))
STATIC_CALLBACKS = {("verify_microstep_granularity_and_topological_anchor", "target_fn"):
                    "Source-structure gate does not execute target_fn; numerical output is outside this gate"}


def poisoned_copy(value, bad):
    if isinstance(value, numbers.Number):
        return bad, True
    if isinstance(value, np.ndarray) and value.size and value.dtype.kind in "biufc":
        clone = value.astype(float, copy=True)
        clone.flat[0] = bad
        return clone, True
    if isinstance(value, (list, tuple, dict)):
        clone = copy.copy(value)
        items = value.items() if isinstance(value, dict) else enumerate(value)
        for key, child in items:
            replacement, changed = poisoned_copy(child, bad)
            if changed:
                if isinstance(value, tuple):
                    clone = list(clone)
                    clone[key] = replacement
                    return tuple(clone), True
                clone[key] = replacement
                return clone, True
    return value, False


def accepted(value):
    if value is None:
        return True
    if isinstance(value, list):
        return not value
    return isinstance(value, dict) and value.get("status") == "PASS"


def probe(function, bound, label, injection=None):
    try:
        result = function(*bound.args, **bound.kwargs)
    except (ValueError, engine.AntiGoodhartGateError) as error:
        ROWS.append({"case": label, "rejected": True, "reason": type(error).__name__})
    except Exception as error:
        ROWS.append({"case": label, "rejected": False, "reason": "unexpected " + type(error).__name__})
    else:
        ROWS.append({"case": label, "rejected": not accepted(result), "reason": "verdict"})
    if injection is not None and not injection["replaced"]:
        UNEXERCISED.append({"case": label, "reason": "Callback numerical output was not reached or had no numeric leaf"})
        ROWS.pop()


def poison_callback(callback, bad, injection):
    @wraps(callback)
    def changed(*args, **kwargs):
        result, replaced = poisoned_copy(callback(*args, **kwargs), bad)
        injection["replaced"] = injection["replaced"] or replaced
        return result
    return changed


def observing(function, name):
    @wraps(function)
    def observed(*args, **kwargs):
        result = function(*args, **kwargs)
        if name in SEEN or not accepted(result):
            return result
        SEEN.add(name)
        signature = inspect.signature(function)
        original = signature.bind(*args, **kwargs)
        original.apply_defaults()
        for parameter, value in original.arguments.items():
            if parameter.startswith("source") or parameter.endswith("code"):
                continue
            for index, bad in enumerate(VALUES):
                bound = signature.bind(*args, **kwargs)
                bound.apply_defaults()
                if callable(value) and parameter.endswith("_fn"):
                    if (name, parameter) in STATIC_CALLBACKS:
                        continue
                    injection = {"replaced": False}
                    bound.arguments[parameter] = poison_callback(value, bad, injection)
                    probe(function, bound, f"{name}.{parameter}.output.{index}", injection)
                else:
                    replacement, changed = poisoned_copy(value, bad)
                    if changed:
                        bound.arguments[parameter] = replacement
                        probe(function, bound, f"{name}.{parameter}.input.{index}")
        return result
    return observed


def run():
    originals = []
    targets = [(name, function) for name, function in vars(engine).items()
               if name.startswith(("verify_", "evaluate_", "audit_", "scan_", "detect_")) and inspect.isfunction(function)]
    for name, function in targets:
        observer = observing(function, name)
        originals.extend(replace_loaded_bindings(function, observer))
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            code = suite.run_comprehensive_54_gate_selftest()
    finally:
        restore_bindings(originals)
    failures = [row for row in ROWS if not row["rejected"]]
    report = {"status": "PASS" if code == 0 and ROWS and not failures else "FAIL",
              "observed_successful_gates": len(SEEN), "injected_cases": len(ROWS),
              "unexercised_callback_cases": UNEXERCISED,
              "static_callback_exclusions": [dict(gate=key[0], parameter=key[1], reason=value)
                                             for key, value in STATIC_CALLBACKS.items()],
              "failures": failures, "cases": ROWS}
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(run())
