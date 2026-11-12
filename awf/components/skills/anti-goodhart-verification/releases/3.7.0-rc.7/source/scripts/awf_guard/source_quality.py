"""AWF Guard: source quality."""
from __future__ import annotations

from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Sequence
from typing import Set
from typing import Tuple
from typing import Union
from awf_guard_numeric_contracts import finite_float as _finite_float
from awf_guard_numeric_contracts import finite_inputs as _finite_inputs
import ast
import io
import numpy as np
import re
import tokenize
from .ast_dataflow import _iter_func_body_no_nested
from .ast_utils import text_dedent


DEFAULT_MAX_FUNCTION_LINES = 200


_PLACEHOLDER_COMMENT_RE = re.compile(r"(?<!\w-)\b(?:TODO|FIXME|PLACEHOLDER|DUMMY|STUB|HACK|XXX)\b", re.IGNORECASE)


_PLACEHOLDER_DOCSTRING_RE = re.compile(r"^\s*(?:TODO|FIXME|PLACEHOLDER|STUB|XXX)\b", re.IGNORECASE)


_NOT_IMPLEMENTED_MESSAGE_RE = re.compile(r"not\s+(?:yet\s+)?implemented|unimplemented", re.IGNORECASE)


_STANDARD_ALLOWED_NUMBERS: Set[float] = {
    -2.0, -1.0, -0.5, 0.0, 0.125, 0.25, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0, 6.0, 8.0, 10.0, 12.0, 100.0,
    round(_finite_float(np.pi), 8),
}


_TEST_ROLE_FUNCTION_NAMES: Tuple[str, ...] = ("run_self_tests", "get_atom_verification_spec", "_mutation_assertion_check")


def _is_abstract_method(func_node: Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> bool:
    return any((getattr(d, "attr", None) or getattr(d, "id", None)) == "abstractmethod" for d in func_node.decorator_list)


def _split_function_docstring(func_node: Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> Tuple[Optional[str], List[ast.stmt]]:
    body = list(func_node.body)
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str):
        return body[0].value.value, body[1:]
    return None, body


def _has_value_parameters(func_node: Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> bool:
    all_args = func_node.args.posonlyargs + func_node.args.args + func_node.args.kwonlyargs
    return any(a.arg not in ("self", "cls") for a in all_args) or func_node.args.vararg is not None


def _scan_function_body_shape(func_node: Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> List[Dict[str, Any]]:
    """Docstring placeholder, hollow `pass`/`...` body and single-constant-return stub detection (`G5n`)."""
    findings: List[Dict[str, Any]] = []
    doc, body_stmts = _split_function_docstring(func_node)
    if doc and _PLACEHOLDER_DOCSTRING_RE.search(doc):
        findings.append({
            "kind": "TodoOrPlaceholderDocstring",
            "function": func_node.name,
            "line": func_node.lineno,
            "detail": f"Function `{func_node.name}` docstring starts with a placeholder marker.",
        })
    if _is_abstract_method(func_node) or len(body_stmts) != 1:
        return findings
    s0 = body_stmts[0]
    if isinstance(s0, ast.Pass) or (isinstance(s0, ast.Expr) and isinstance(s0.value, ast.Constant) and s0.value.value is Ellipsis):
        findings.append({
            "kind": "HollowStubFunctionBody",
            "function": func_node.name,
            "line": func_node.lineno,
            "detail": f"Function `{func_node.name}` has a hollow `pass`/`...` stub body (-inf circuit-breaker).",
        })
    elif isinstance(s0, ast.Return) and isinstance(s0.value, ast.Constant) and _has_value_parameters(func_node):
        findings.append({
            "kind": "ConstantReturnStub",
            "function": func_node.name,
            "line": func_node.lineno,
            "detail": f"Function `{func_node.name}` ignores all parameters and returns constant `{s0.value.value!r}`.",
        })
    return findings


def _raise_message_text(exc_node: ast.AST) -> str:
    if not isinstance(exc_node, ast.Call) or not exc_node.args:
        return ""
    arg0 = exc_node.args[0]
    if isinstance(arg0, ast.Constant) and isinstance(arg0.value, str):
        return arg0.value
    if isinstance(arg0, ast.JoinedStr):
        return "".join(v.value for v in arg0.values if isinstance(v, ast.Constant) and isinstance(v.value, str))
    return ""


def _classify_placeholder_raise(func_node: Union[ast.FunctionDef, ast.AsyncFunctionDef], sub: ast.Raise) -> List[Dict[str, Any]]:
    exc_name = getattr(sub.exc, "id", None) or getattr(getattr(sub.exc, "func", None), "id", None) or ""
    if exc_name in ("NotImplementedError", "NotImplemented"):
        label = f"raises `{exc_name}` placeholder"
    elif _NOT_IMPLEMENTED_MESSAGE_RE.search(_raise_message_text(sub.exc)):
        label = f"raises `{exc_name}` with a disguised not-implemented message"
    else:
        return []
    return [{
        "kind": "RaiseNotImplementedShortcut",
        "function": func_node.name,
        "line": getattr(sub, "lineno", func_node.lineno),
        "detail": f"Function `{func_node.name}` {label}.",
    }]


def _scan_single_function_for_shortcuts(
    func_node: Union[ast.FunctionDef, ast.AsyncFunctionDef],
    check_magic_numbers: bool,
    allowed_nums: Set[float],
) -> List[Dict[str, Any]]:
    findings = _scan_function_body_shape(func_node)
    is_abstract = _is_abstract_method(func_node)
    assigned_locals: Dict[str, int] = {}
    loaded_names: Set[str] = {
        n.id for n in ast.walk(func_node) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)
    }
    for sub in _iter_func_body_no_nested(func_node):
        if isinstance(sub, ast.Raise) and sub.exc is not None and not is_abstract:
            findings.extend(_classify_placeholder_raise(func_node, sub))
        if isinstance(sub, ast.Assign):
            for tgt in sub.targets:
                if isinstance(tgt, ast.Name) and not tgt.id.startswith("_"):
                    assigned_locals.setdefault(tgt.id, getattr(sub, "lineno", func_node.lineno))
        if check_magic_numbers and isinstance(sub, ast.Constant) and isinstance(sub.value, float):
            fval = _finite_float(sub.value)
            if fval not in allowed_nums and abs(fval) > 1e-4 and round(fval, 8) not in allowed_nums:
                findings.append({
                    "kind": "UnexplainedMagicNumberLiteral",
                    "function": func_node.name,
                    "line": getattr(sub, "lineno", func_node.lineno),
                    "detail": f"Function `{func_node.name}` embeds unexplained magic float `{fval}` at line {getattr(sub, 'lineno', 0)}.",
                })
    for var_name, line_no in assigned_locals.items():
        if var_name not in loaded_names:
            findings.append({
                "kind": "UnusedLocalVariableShortcut",
                "function": func_node.name,
                "line": line_no,
                "detail": f"Local variable `{var_name}` assigned at line {line_no} in `{func_node.name}` is never used!",
            })
    return findings


@_finite_inputs
def scan_source_for_todo_placeholders_and_magic_numbers(
    source_code: str,
    check_magic_numbers: bool = True,
    allowed_numeric_literals: Optional[Sequence[float]] = None,
) -> Dict[str, Any]:
    """
    Static AST + Lexical Circuit-Breaker (`G5n_Zero_Todo_Placeholder_Stub_And_MagicNumber_CircuitBreaker`):
    Maps implementation shortcuts directly to `-inf` reward:
    1. Comment placeholder markers (`TODO`, `FIXME`, `PLACEHOLDER`, `DUMMY`, `STUB`, `HACK`) and module/function
       docstrings that start with such a marker;
    2. Hollow function bodies (`pass`, `...` Ellipsis), single-constant-return stubs that ignore every parameter,
       `raise NotImplementedError` and any `raise X("not implemented ...")` disguise
       (`@abc.abstractmethod` interface declarations are exempt);
    3. Unused local variable assignments (`x = ...` never loaded in function body);
    4. Unexplained magic floating-point literals inside return/arithmetic expressions (when `check_magic_numbers=True`).
    """
    if not source_code.strip():
        return {"status": "FAIL", "effective_reward": 0.0, "finding_count": 1, "findings": [{"kind": "EmptySource"}]}

    dedented = text_dedent(source_code)
    findings: List[Dict[str, Any]] = []

    for tok in tokenize.generate_tokens(io.StringIO(dedented).readline):
        if tok.type == tokenize.COMMENT and _PLACEHOLDER_COMMENT_RE.search(tok.string):
            findings.append({
                "kind": "TodoOrPlaceholderComment",
                "line": tok.start[0],
                "detail": f"Placeholder comment `{tok.string.strip()}` at line {tok.start[0]} triggers -inf circuit-breaker.",
            })

    tree = ast.parse(dedented)
    allowed_nums = set(_STANDARD_ALLOWED_NUMBERS)
    if allowed_numeric_literals is not None:
        for v in allowed_numeric_literals:
            allowed_nums.add(_finite_float(v))

    module_doc = ast.get_docstring(tree, clean=False)
    if module_doc and _PLACEHOLDER_DOCSTRING_RE.search(module_doc):
        findings.append({"kind": "TodoOrPlaceholderDocstring", "line": 1, "detail": "Module docstring starts with a placeholder marker."})

    for func_node in ast.walk(tree):
        if isinstance(func_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            findings.extend(_scan_single_function_for_shortcuts(func_node, check_magic_numbers, allowed_nums))

    passed = len(findings) == 0
    return {
        "status": "PASS" if passed else "FAIL",
        "effective_reward": 1.0 if passed else -float("inf"),
        "finding_count": len(findings),
        "findings": findings,
    }
