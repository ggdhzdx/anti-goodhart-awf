"""Regression evidence for recursive audits and genuine cross-module injection."""
import ast
import importlib
import json
from pathlib import Path
import tempfile

import awf_universal_anti_goodhart_gates as gate
from awf_guard import api
from awf_guard_test_bindings import replace_loaded_bindings, restore_bindings
from awf_guard_selftests import calibrated_morph_and_optics_pack

SCRIPTS = Path(__file__).resolve().parent
FUNCTION_LIMIT = 200
FILE_LIMIT = 1000


class RoutingWitness(RuntimeError):
    """A marker raised only by the injected callable."""


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def check_closure():
    names = json.loads((SCRIPTS.parent / "public-contract.json").read_text())["supported_names"]
    require(set(names) == set(api.__all__), "public contract changed")
    for name in names:
        require(getattr(gate, name) is getattr(api, name), f"legacy/public contract mismatch: {name}")
    report = gate.audit_engine_self_hosting_integrity()
    actual = {p.relative_to(SCRIPTS).as_posix() for p in SCRIPTS.rglob("*.py")}
    require(set(report["files_audited"]) == actual, "recursive source coverage mismatch")
    require(report["status"] == "PASS" and not report["declared_waivers"], "nonzero violations or size waivers")
    require(not gate._SELF_AUDIT_DECLARED_FILE_SIZE_WAIVERS, "waiver table is not empty")
    maximum_file, maximum_function = 0, 0
    for relative in sorted(actual):
        text = (SCRIPTS / relative).read_text(encoding="utf-8-sig")
        file_lines = len(text.splitlines())
        maximum_file = max(maximum_file, file_lines)

        for node in ast.walk(ast.parse(text)):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                count = node.end_lineno - node.lineno + 1
                maximum_function = max(maximum_function, count)

    return {"files": len(actual), "supported_public_names": len(names), "maximum_file_lines": maximum_file,
            "maximum_function_lines": maximum_function}


def check_nested_counterexamples():
    with tempfile.TemporaryDirectory(prefix="ag_recursive_") as directory:
        root = Path(directory)
        entry = root / "entry.py"
        entry.write_text("def combine(x):\n    return x + 1\n")
        nested = root / "nested"
        nested.mkdir()
        require(gate.audit_engine_self_hosting_integrity(entry)["status"] == "PASS", "clean control")
        target = nested / "test_rc3_contracts.py"
        target.write_text("def combine(x):\n    return x * 1.23456789\n")
        report = gate.audit_engine_self_hosting_integrity(entry)
        require(report["status"] == "FAIL" and report["g5n_finding_count"] > 0, "nested filename spoof escaped magic scan")
        target.write_text("# ordinary source line\n" * (FILE_LIMIT + 1))
        report = gate.audit_engine_self_hosting_integrity(entry)
        require(report["status"] == "PASS" and bool(report["size_review_items"]), "nested large file was hidden or mechanically rejected")
        target.write_text("def combine(x):\n    acc = x\n" + "    acc = acc + x\n" * (FUNCTION_LIMIT - 2) + "    return acc\n")
        report = gate.audit_engine_self_hosting_integrity(entry)
        require(report["status"] == "PASS" and bool(report["size_review_items"]), "nested long function policy")
        with target.open("a") as stream:
            stream.write("def flawed(x):\n    return x * 1.23456789\n")
        report = gate.audit_engine_self_hosting_integrity(entry)
        require(report["status"] == "FAIL" and report["g5n_finding_count"] > 0, "large source inspection was truncated")
    return 5


def check_injection_routing():
    original = gate.verify_filtration_monotonicity_and_heterogeneous_radius_clearance
    invocations = []
    def injected(*args, **kwargs):
        invocations.append((len(args), len(kwargs)))
        raise RoutingWitness("injected function reached through a real positive test group")
    changes = replace_loaded_bindings(original, injected)
    modules = {module.__name__ for module, name, previous in changes}
    require(original.__module__ in modules and bool(changes), "defining callable was not replaced")
    caught = False
    try:
        calibrated_morph_and_optics_pack._verify_calibrated_morph_and_optics_pack_selftests()
    except RoutingWitness:
        caught = True
    finally:
        restore_bindings(changes)
    require(caught and len(invocations) == 1, "injection was not executed")
    require(gate.verify_filtration_monotonicity_and_heterogeneous_radius_clearance is original, "facade restoration failed")
    require(all(getattr(module, name) is previous for module, name, previous in changes), "binding restoration failed")
    return {"patched_modules": sorted(modules), "executed_calls": len(invocations)}


def run_modular_checks():
    return {"status": "PASS", "closure": check_closure(), "recursive_controls": check_nested_counterexamples(),
            "injection": check_injection_routing()}


if __name__ == "__main__":
    print(json.dumps(run_modular_checks(), indent=2))
