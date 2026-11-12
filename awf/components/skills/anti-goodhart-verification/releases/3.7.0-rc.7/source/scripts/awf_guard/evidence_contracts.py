"""Minimum evidence requirements; these are not proofs of algorithmic independence."""
import functools
import inspect


def concrete_cases(cases, label):
    if not isinstance(cases, (list, tuple)) or not cases:
        raise ValueError(f'{label} requires a nonempty concrete sequence of input mappings')
    if not all(isinstance(case, dict) for case in cases):
        raise ValueError(f'{label} contains a non-mapping case')
    return cases


def callable_origin(function):
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
        else:
            return current
    raise ValueError('Cyclic callable wrapper chain')


def require_distinct_reference(target, reference):
    left, right = callable_origin(target), callable_origin(reference)
    code = getattr(left, '__code__', None)
    if left is right or code is not None and code is getattr(right, '__code__', None):
        raise ValueError('Target and reference have the same callable origin')


def valid_upstream_receipt(atom_id, receipt):
    if not isinstance(receipt, dict):
        return False
    gates = receipt.get('gates_passed')
    return (receipt.get('atom_id') == atom_id and receipt.get('verdict_zone') == 'PASS'
            and type(receipt.get('tier')) is int and receipt['tier'] in (1, 2)
            and isinstance(gates, list) and bool(gates)
            and all(isinstance(gate, str) and bool(gate) for gate in gates))
