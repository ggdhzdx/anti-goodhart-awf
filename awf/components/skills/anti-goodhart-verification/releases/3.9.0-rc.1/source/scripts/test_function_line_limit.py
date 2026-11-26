"""Behavior tests: default length advisories and explicit caller size contracts."""
import importlib.util
import inspect
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import awf_universal_anti_goodhart_gates as gate

LIMIT = 200
BOUNDARIES = (160, 161, 200, 201, 1002)


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def raises_size_error(action):
    message = ""
    try:
        action()
    except gate.AtomicContractViolationError as error:
        message = str(error)
    return "Size Overflow" in message


def check_function(root, length):
    source = "def sample(x):\n    acc = x\n" + "    acc = acc + x\n" * (length - 3) + "    return acc\n"
    path = root / f"function_{length}.py"
    path.write_text(source)
    spec = importlib.util.spec_from_file_location(f"fixture_{length}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    function = module.sample
    require(gate.verify_ast_pure_function(function) == length, "default purity must not reject length alone")
    require(gate.verify_microstep_granularity_and_topological_anchor(function, mca_condition_number=1, invariant_anchor_count=2)["status"] == "PASS", "default microstep length")
    gate.scientific_atom(f"default-{length}", "boundary", "", {}, {})(function)
    report = gate.audit_engine_self_hosting_integrity(path, include_colocated_scripts=False)
    require(report["status"] == "PASS", "default self audit must not fail length alone")
    if length > LIMIT:
        require(bool(report["size_review_items"]), "long code must remain visible for review")
    expected_failure = length > LIMIT
    require(raises_size_error(lambda: gate.verify_ast_pure_function(function, max_lines=LIMIT)) == expected_failure, "explicit purity cap")
    require(raises_size_error(lambda: gate.scientific_atom(f"strict-{length}", "boundary", "", {}, {}, max_lines=LIMIT)(function)) == expected_failure, "explicit decorator cap")
    strict = gate.verify_microstep_granularity_and_topological_anchor(function, max_lines=LIMIT, mca_condition_number=1, invariant_anchor_count=2)
    require((strict["status"] == "FAIL") == expected_failure, "explicit microstep cap")
    strict = gate.audit_engine_self_hosting_integrity(path, max_fn_lines=LIMIT, include_colocated_scripts=False)
    require((strict["status"] == "FAIL") == expected_failure, "explicit self audit cap")
    decorated = root / f"decorated_{length}.py"
    decorated.write_text("@scientific_atom\n" + source)
    require(gate.audit_ast_path(decorated)["status"] == "PASS", "default AST length")
    require((gate.audit_ast_path(decorated, max_atom_lines=LIMIT)["status"] == "FAIL") == expected_failure, "explicit AST cap")
    return decorated


def run_boundary_checks(include_cli=False):
    original_registry = dict(gate.GLOBAL_ATOM_REGISTRY)
    cli_checks = 0
    try:
        with tempfile.TemporaryDirectory(prefix="ag_length_policy_") as directory:
            root = Path(directory)
            for length in BOUNDARIES:
                decorated = check_function(root, length)
                if include_cli and length in (LIMIT, LIMIT + 1):
                    proc = subprocess.run([sys.executable, "-B", gate.__file__, "--audit-ast", str(decorated)], capture_output=True, text=True, check=False)
                    require(proc.returncode == 0 and json.loads(proc.stdout)["status"] == "PASS", "CLI default size policy")
                    cli_checks += 1
            path = root / "large_file.py"
            path.write_text("# ordinary line\n" * 1001)
            default = gate.audit_engine_self_hosting_integrity(path, include_colocated_scripts=False)
            explicit = gate.audit_engine_self_hosting_integrity(path, include_colocated_scripts=False, max_file_lines=1000)
            require(default["status"] == "PASS" and bool(default["size_review_items"]), "large file advisory")
            require(explicit["status"] == "FAIL" and bool(explicit["oversized_files_unwaived"]), "explicit file size contract")
    finally:
        gate.GLOBAL_ATOM_REGISTRY.clear()
        gate.GLOBAL_ATOM_REGISTRY.update(original_registry)
    return {"status": "PASS", "policy": "advisory_by_default_explicit_limits_enforced", "boundaries": list(BOUNDARIES),
            "default_and_explicit_paths": 5, "explicit_contract": LIMIT, "cli_checks": cli_checks}


if __name__ == "__main__":
    print(json.dumps(run_boundary_checks(include_cli=True), indent=2))
