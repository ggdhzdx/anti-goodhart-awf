"""Minimum evidence requirements and anti-delegation guards."""
from __future__ import annotations

import ast
import functools
import inspect
import sys
import textwrap
from typing import Any, Callable


def concrete_cases(cases: Any, label: str) -> Any:
    if not isinstance(cases, (list, tuple)) or not cases:
        raise ValueError(f'{label} requires a nonempty concrete sequence of input mappings')
    if not all(isinstance(case, dict) for case in cases):
        raise ValueError(f'{label} contains a non-mapping case')
    return cases


def callable_origin(function: Any) -> Any:
    current = function
    seen = set()
    while id(current) not in seen:
        seen.add(id(current))
        if isinstance(current, functools.partial):
            current = current.func
        elif inspect.ismethod(current):
            current = current.__func__
        elif hasattr(current, '__wrapped__'):
            current = current.__wrapped__
        elif (
            not inspect.isfunction(current)
            and not inspect.isbuiltin(current)
            and not isinstance(current, type)
            and callable(current)
            and hasattr(type(current), '__call__')
        ):
            call_attr = getattr(type(current), '__call__')
            if call_attr is current:
                return current
            current = call_attr
        else:
            return current
    raise ValueError('Cyclic callable wrapper chain')


def _closure_or_state_references_target(candidate: Any, target_origin: Any, target_code: Any) -> bool:
    for obj in (candidate, callable_origin(candidate)):
        closure = getattr(obj, '__closure__', None) or ()
        for cell in closure:
            try:
                val = cell.cell_contents
            except ValueError:
                continue
            val_origin = callable_origin(val) if callable(val) else val
            if val_origin is target_origin or (target_code is not None and getattr(val_origin, '__code__', None) is target_code):
                return True
        obj_dict = getattr(obj, '__dict__', None)
        if isinstance(obj_dict, dict):
            for val in obj_dict.values():
                val_origin = callable_origin(val) if callable(val) else val
                if val_origin is target_origin or (target_code is not None and getattr(val_origin, '__code__', None) is target_code):
                    return True
    target_name = getattr(target_origin, '__name__', '')
    if target_name and target_name != '<lambda>':
        for obj in (candidate, callable_origin(candidate)):
            try:
                src = textwrap.dedent(inspect.getsource(obj))
                tree = ast.parse(src)
            except (OSError, TypeError, SyntaxError):
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    called_name = getattr(node.func, 'id', None) or getattr(node.func, 'attr', None)
                    if called_name == target_name:
                        return True
    return False


def require_distinct_reference(target: Any, reference: Any) -> None:
    if not callable(target) or not callable(reference):
        raise ValueError('Target and reference must both be callable')
    left, right = callable_origin(target), callable_origin(reference)
    code = getattr(left, '__code__', None)
    if (
        target is reference
        or left is right
        or (code is not None and code is getattr(right, '__code__', None))
        or _closure_or_state_references_target(reference, left, code)
    ):
        raise ValueError('Target and reference have the same callable origin or delegate to target')


def call_without_target_reentry(function: Callable[..., Any], target: Any, *args: Any, **kwargs: Any) -> Any:
    """Invoke `function(*args, **kwargs)` while forbidding any runtime call frame entering `target`."""
    target_origin = callable_origin(target)
    target_code = getattr(target_origin, '__code__', None)
    if target_code is None:
        return function(*args, **kwargs)
    reentered = []
    prev_profile = sys.getprofile()

    def _profiler(frame: Any, event: str, arg: Any) -> None:
        if event == 'call' and frame.f_code is target_code:
            reentered.append(True)
        if prev_profile is not None:
            prev_profile(frame, event, arg)

    sys.setprofile(_profiler)
    try:
        result = function(*args, **kwargs)
    finally:
        sys.setprofile(prev_profile)
    if reentered:
        raise ValueError('Reference or oracle dynamically invoked target_fn at runtime')
    return result


def valid_upstream_receipt(atom_id: str, receipt: Any) -> bool:
    if not isinstance(receipt, dict):
        return False
    gates = receipt.get('gates_passed')
    return (
        receipt.get('atom_id') == atom_id
        and receipt.get('verdict_zone') == 'PASS'
        and receipt.get('requires_human_approval') is not True
        and not receipt.get('borderline_warnings')
        and type(receipt.get('tier')) is int
        and receipt['tier'] in (1, 2)
        and isinstance(gates, list)
        and bool(gates)
        and all(isinstance(gate, str) and bool(gate) for gate in gates)
    )
