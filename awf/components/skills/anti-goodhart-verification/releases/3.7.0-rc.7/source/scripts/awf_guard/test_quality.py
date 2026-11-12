"""AWF Guard: test quality."""
from __future__ import annotations

from typing import Any
from typing import Dict
from typing import List
from typing import Sequence
from typing import Set
from typing import Union
from awf_guard_numeric_contracts import finite_inputs as _finite_inputs
import ast
from .ast_utils import text_dedent
from .test_reachability import reachable_test_nodes, locally_shadowed_assertions, local_assertion_helpers


_BOGUS_MOCK_METHODS = frozenset({
    "called_once",
    "called_once_with",
    "called_with",
    "assert_not_called_once",
    "assert_called_twice",
})


_VALID_ASSERT_CALL_NAMES = frozenset({
    "assert_allclose",
    "assert_array_almost_equal",
    "assert_array_equal",
    "assert_almost_equal",
    "assert_equal",
    "assertTrue",
    "assertFalse",
    "assertEqual",
    "assertNotEqual",
    "assertAlmostEqual",
    "assertRaises",
    "raises",
})


def _is_weak_existence_only_expr(expr: ast.AST) -> bool:
    """Return True if an assert expression only checks `x is not None` or `isinstance(x, ...)` (`falsegreen` C6)."""
    if isinstance(expr, ast.Compare) and len(expr.ops) == 1:
        op = expr.ops[0]
        comp = expr.comparators[0]
        if isinstance(op, (ast.IsNot, ast.NotEq)) and isinstance(comp, ast.Constant) and comp.value is None:
            return True
    if isinstance(expr, ast.Call) and isinstance(expr.func, ast.Name) and expr.func.id == "isinstance":
        return True
    return False


def _check_patch_targets_for_self_mocking(
    node_or_decorators: Sequence[ast.AST],
    fn_label: str,
    target_set: Set[str],
    mock_findings: List[Dict[str, Any]],
) -> None:
    for item in node_or_decorators:
        for sub in ast.walk(item):
            if isinstance(sub, ast.Call):
                c_name = getattr(sub.func, "id", None) or getattr(sub.func, "attr", None) or ""
                if c_name in ("patch", "object", "setattr"):
                    for arg in sub.args:
                        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                            patched_str = arg.value
                            leaf_sym = patched_str.rsplit(".", 1)[-1]
                            if leaf_sym in target_set or patched_str in target_set:
                                mock_findings.append({
                                    "code": "TargetSelfMocking",
                                    "test": fn_label,
                                    "line": getattr(sub, "lineno", 1),
                                    "detail": f"Test `{fn_label}` mocks the target function under test `{patched_str}` (Self-Mocking abuse)!",
                                })
                        elif isinstance(arg, ast.Name) and arg.id in target_set:
                            mock_findings.append({
                                "code": "TargetSelfMocking",
                                "test": fn_label,
                                "line": getattr(sub, "lineno", 1),
                                "detail": f"Test `{fn_label}` mocks target function `{arg.id}`!",
                            })


def _audit_single_test_function_ast(
    node: Union[ast.FunctionDef, ast.AsyncFunctionDef],
    target_set: Set[str],
    hollow_findings: List[Dict[str, Any]],
    mock_findings: List[Dict[str, Any]],
    shadowed_assertions: Set[str],
    assertion_helpers: Set[str],
) -> None:
    fn_name = node.name
    _check_patch_targets_for_self_mocking(node.decorator_list, fn_name, target_set, mock_findings)
    _check_patch_targets_for_self_mocking(node.body, fn_name, target_set, mock_findings)

    assertions_seen: List[ast.AST] = []
    strong_assertions = 0

    for stmt in node.body:
        if isinstance(stmt, ast.Return) and isinstance(stmt.value, ast.Compare):
            hollow_findings.append({
                "code": "C39",
                "test": fn_name,
                "line": stmt.lineno,
                "detail": f"Test `{fn_name}` returns a comparison instead of asserting it (`falsegreen` C39).",
            })
        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Compare):
            hollow_findings.append({
                "code": "C59",
                "test": fn_name,
                "line": stmt.lineno,
                "detail": f"Test `{fn_name}` has a bare comparison statement without `assert` (`falsegreen` C59).",
            })

    for sub in reachable_test_nodes(node):
        if isinstance(sub, ast.Try):
            has_assert_in_try = any(isinstance(x, ast.Assert) for b in sub.body for x in ast.walk(b))
            for h in sub.handlers:
                is_pass = len(h.body) == 1 and isinstance(h.body[0], ast.Pass)
                h_name = getattr(h.type, "id", "Exception") if h.type is not None else "BaseException"
                if is_pass and (has_assert_in_try or h_name in ("Exception", "BaseException", "AssertionError")):
                    hollow_findings.append({
                        "code": "C3",
                        "test": fn_name,
                        "line": h.lineno,
                        "detail": f"Test `{fn_name}` swallows assertions/exceptions inside `try...except: pass` (`falsegreen` C3/C27).",
                    })

        if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Attribute) and sub.func.attr in _BOGUS_MOCK_METHODS:
            mock_findings.append({
                "code": "C13",
                "test": fn_name,
                "line": sub.lineno,
                "detail": f"Test `{fn_name}` calls non-existent mock method `.{sub.func.attr}()` which always evaluates truthy (`falsegreen` C13).",
            })

        if isinstance(sub, ast.Call):
            c_leaf = getattr(sub.func, "id", None) or getattr(sub.func, "attr", None) or ""
            if isinstance(sub.func, ast.Name) and c_leaf in assertion_helpers:
                assertions_seen.append(sub)
                strong_assertions += 1
            elif c_leaf in _VALID_ASSERT_CALL_NAMES and c_leaf in shadowed_assertions:
                hollow_findings.append({"code": "ShadowedAssertion", "test": fn_name, "line": sub.lineno, "detail": "Locally replaced assertion helper cannot certify a test"})
            elif c_leaf in _VALID_ASSERT_CALL_NAMES:
                assertions_seen.append(sub)
                strong_assertions += 1

        if isinstance(sub, ast.Raise) and sub.exc is not None:
            exc_id = getattr(sub.exc, "id", None) or getattr(getattr(sub.exc, "func", None), "id", None) or ""
            if exc_id == "AssertionError":
                assertions_seen.append(sub)
                strong_assertions += 1

        if isinstance(sub, ast.Assert):
            assertions_seen.append(sub)
            t_expr = sub.test
            if (isinstance(t_expr, ast.Constant) and bool(t_expr.value) is True) or (
                isinstance(t_expr, ast.Tuple) and len(t_expr.elts) > 0
            ):
                hollow_findings.append({
                    "code": "C5",
                    "test": fn_name,
                    "line": sub.lineno,
                    "detail": f"Test `{fn_name}` uses an always-true constant or tuple assertion (`falsegreen` C5).",
                })
            elif isinstance(t_expr, ast.BoolOp) and isinstance(t_expr.op, ast.Or) and any(
                isinstance(v, ast.Constant) and bool(v.value) is True for v in t_expr.values
            ):
                hollow_findings.append({
                    "code": "C5",
                    "test": fn_name,
                    "line": sub.lineno,
                    "detail": f"Test `{fn_name}` uses `assert ... or True` tautology (`falsegreen` C5).",
                })
            elif isinstance(t_expr, ast.Compare) and len(t_expr.ops) == 1:
                op = t_expr.ops[0]
                left_n = t_expr.left
                right_n = t_expr.comparators[0]
                if isinstance(op, (ast.Eq, ast.Is, ast.GtE, ast.LtE)) and ast.dump(left_n) == ast.dump(right_n):
                    hollow_findings.append({
                        "code": "C7",
                        "test": fn_name,
                        "line": sub.lineno,
                        "detail": f"Test `{fn_name}` compares an expression to itself (`falsegreen` C7).",
                    })
                elif (
                    isinstance(op, ast.GtE)
                    and isinstance(right_n, ast.Constant)
                    and right_n.value == 0
                    and isinstance(left_n, ast.Call)
                    and getattr(left_n.func, "id", "") in ("len", "abs")
                ):
                    hollow_findings.append({
                        "code": "C44",
                        "test": fn_name,
                        "line": sub.lineno,
                        "detail": f"Test `{fn_name}` asserts `len(x) >= 0` or `abs(x) >= 0` numeric tautology (`falsegreen` C44).",
                    })
                elif not _is_weak_existence_only_expr(t_expr):
                    strong_assertions += 1
            elif not _is_weak_existence_only_expr(t_expr):
                strong_assertions += 1

    if not assertions_seen:
        hollow_findings.append({
            "code": "C2",
            "test": fn_name,
            "line": node.lineno,
            "detail": f"Test `{fn_name}` has zero assertions (`falsegreen` C2/C2b).",
        })
    elif strong_assertions == 0 and not any(f["test"] == fn_name for f in hollow_findings):
        hollow_findings.append({
            "code": "C6",
            "test": fn_name,
            "line": node.lineno,
            "detail": f"Test `{fn_name}` only performs weak existence/type checks (`is not None` / `isinstance`) without verifying values (`falsegreen` C6).",
        })


@_finite_inputs
def audit_test_suite_falsegreen_and_mock_abuse(
    test_source_code: str,
    target_fn_names: Sequence[str] = (),
) -> Dict[str, Any]:
    """
    Deterministic AST scanner for Python/pytest test suites adapted from `vinicq/falsegreen` & `PyNose`:
    Detects hollow/tautological test smells (`C2`, `C3`, `C5`, `C6`, `C7`, `C39`, `C44`, `C59` -> `G6k`)
    and self-mocking / bogus mock assertion abuse (`TargetSelfMocking`, `C13` -> `G6l`).
    """
    tree = ast.parse(text_dedent(test_source_code))
    target_set = set(target_fn_names)
    hollow_findings: List[Dict[str, Any]] = []
    mock_findings: List[Dict[str, Any]] = []
    test_count = 0
    shadowed = locally_shadowed_assertions(tree, _VALID_ASSERT_CALL_NAMES)
    candidates = local_assertion_helpers(tree)
    helpers = set()
    for helper in tree.body:
        if isinstance(helper, (ast.FunctionDef, ast.AsyncFunctionDef)) and helper.name in candidates:
            helper_hollow, helper_mocks = [], []
            _audit_single_test_function_ast(helper, set(), helper_hollow, helper_mocks, shadowed, set())
            if not helper_hollow and not helper_mocks:
                helpers.add(helper.name)

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith(
            ("test_", "_selftest_", "_verify_", "_check_part_", "run_selftest", "run_self_tests")
        ):
            test_count += 1
            _audit_single_test_function_ast(node, target_set, hollow_findings, mock_findings, shadowed, helpers)

    passed = (test_count > 0) and (not hollow_findings) and (not mock_findings)
    return {
        "status": "PASS" if passed else "FAIL",
        "test_count": test_count,
        "assertion_analysis": "reachable_unshadowed_v1",
        "assurance_scope": "static_heuristic_not_execution_proof",
        "hollow_finding_count": len(hollow_findings),
        "mock_finding_count": len(mock_findings),
        "hollow_findings": hollow_findings,
        "mock_findings": mock_findings,
    }
