"""AWF Guard: atoms."""
from __future__ import annotations

from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional
from pathlib import Path
from typing import Sequence
from typing import Set
from typing import Tuple
from typing import Union
from awf_guard_numeric_contracts import finite_call as _finite_call
from awf_guard_numeric_contracts import finite_float as _finite_float
from awf_guard_numeric_contracts import finite_inputs as _finite_inputs
import ast
import functools
import inspect
import json
from .errors import AtomicContractViolationError
from .source_quality import DEFAULT_MAX_FUNCTION_LINES
from .tensor_contracts import TensorSpec
from .ast_utils import _unwrap_target_fn
from .tensor_contracts import _validate_tensor_against_spec
from .ast_structure import analyze_contract_and_docstring_intent
from .ast_dataflow import detect_extensional_enumeration_and_dispatch
from .ast_structure import scan_ast_for_harness_tampering
from .ast_utils import text_dedent
from .ast_dataflow import verify_atom_input_dataflow


_FORBIDDEN_IMPURE_CALLS = {
    "open",
    "system",
    "popen",
    "Popen",
    "run",
    "check_output",
    "check_call",
    "write_text",
    "write_bytes",
    "savefig",
    "to_csv",
    "to_pickle",
    "save",
    "savez",
}


def extract_ast_called_functions(fn_or_src: Union[Callable[..., Any], str]) -> List[str]:
    """
    Extract all function/callable identifiers invoked inside a function's AST.
    Used to automatically discover and cross-check upstream/downstream `@scientific_atom` dependencies.
    """
    if callable(fn_or_src):
        try:
            lines, _ = inspect.getsourcelines(_finite_call(_unwrap_target_fn, fn_or_src))
            src = "".join(lines)
        except OSError:
            return []
    else:
        src = fn_or_src

    try:
        tree = ast.parse(text_dedent(src))
    except SyntaxError:
        return []

    called: Set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                called.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                called.add(node.func.attr)
    return sorted(called)


@_finite_inputs
def verify_ast_pure_function(
    fn: Callable[..., Any],
    max_lines: Optional[int] = None,
    math_contract: str = "",
    verify_contract_intent: bool = True,
) -> int:
    """
    Statically inspect an atomic operator function's AST to enforce:
    1. An explicit caller-specified size contract, if supplied;
    2. Functional Purity (no hidden disk I/O, subprocess calls, or global state mutation);
    3. Zero Harness Tampering / Enumeration Memorization;
    4. Docstring & `math_contract` Intent-vs-AST Structure consistency.
    """
    try:
        lines, _ = inspect.getsourcelines(fn)
        src = "".join(lines)
    except OSError:
        return 0

    n_lines = len(lines)
    if max_lines is not None and n_lines > max_lines:
        raise AtomicContractViolationError(
            f"[Atomic Capsule Size Overflow] Function `{fn.__name__}` is {n_lines} lines "
            f"(> max_lines={max_lines}). The caller's declared size contract was exceeded."
        )

    tree = ast.parse(text_dedent(src))
    for node in ast.walk(tree):
        if isinstance(node, ast.Global):
            raise AtomicContractViolationError(
                f"[Impure Atom Violation] `{fn.__name__}` uses `global` state mutation! "
                f"Atomic operators must be stateless pure functions."
            )
        if isinstance(node, ast.Call):
            func_name = getattr(node.func, "id", None) or getattr(node.func, "attr", None)
            if func_name in _FORBIDDEN_IMPURE_CALLS:
                raise AtomicContractViolationError(
                    f"[Impure Atom Violation] `{fn.__name__}` calls forbidden I/O or side-effect "
                    f"`{func_name}()`! Keep disk/subprocess I/O strictly in the thin pipeline shell."
                )

    tamper_issues = scan_ast_for_harness_tampering(tree)
    if tamper_issues:
        raise AtomicContractViolationError(
            f"[Atom Harness-Tampering Violation] `{fn.__name__}` failed AST tamper check: {tamper_issues[0]['detail']}"
        )

    enum_issues = detect_extensional_enumeration_and_dispatch(tree)
    if enum_issues:
        raise AtomicContractViolationError(
            f"[Atom Memorization Violation] `{fn.__name__}` failed enumeration/dispatch check: {enum_issues[0]['detail']}"
        )

    if verify_contract_intent:
        intent_issues = analyze_contract_and_docstring_intent(tree, extra_contract_by_fn={fn.__name__: math_contract})
        if intent_issues:
            raise AtomicContractViolationError(
                f"[Atom Intent-vs-AST Mismatch] `{fn.__name__}`: {intent_issues[0]['detail']}"
            )

    return n_lines


def scientific_atom(
    atom_id: str,
    tutor_station: str,
    math_contract: str,
    inputs: Dict[str, TensorSpec],
    outputs: Dict[str, TensorSpec],
    upstream_atoms: Sequence[str] = (),
    downstream_atoms: Sequence[str] = (),
    pure_function: bool = True,
    max_lines: Optional[int] = None,
    verify_input_dataflow: bool = True,
    verify_contract_intent: bool = True,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator transforming a pure mathematical function into a self-verifying
    Atomic Operator Capsule with:
    1. Zero-trust physical unit, jaxtyping symbolic/algebraic/variadic shape, domain, and monotonicity runtime contracts;
    2. AST purity, conciseness, and anti-tampering static guards;
    3. Parameter-Taint Dataflow verification (proving every declared input in `inputs` flows into `return`);
    4. Docstring & `math_contract` Intent-vs-AST Structure consistency verification;
    5. Automatic AST Call-Graph extraction (`ast_called_symbols`).
    """
    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        n_lines = (
            verify_ast_pure_function(
                fn,
                max_lines=max_lines,
                math_contract=math_contract,
                verify_contract_intent=verify_contract_intent,
            )
            if pure_function
            else 0
        )
        taint_flow_map = (
            verify_atom_input_dataflow(fn, list(inputs.keys()))
            if verify_input_dataflow and inputs
            else {}
        )
        ast_calls = extract_ast_called_functions(fn)
        sig = inspect.signature(fn)

        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()
            symbolic_dims: Dict[str, int] = {}
            variadic_dims: Dict[str, Tuple[bool, Tuple[int, ...]]] = {}

            clean_arguments: Dict[str, Any] = {}
            for k, v in bound.arguments.items():
                if k in inputs:
                    arr = _validate_tensor_against_spec(
                        name=k,
                        val=v,
                        spec=inputs[k],
                        symbolic_dims=symbolic_dims,
                        atom_id=atom_id,
                        direction="Input",
                        variadic_dims=variadic_dims,
                    )
                    clean_arguments[k] = _finite_float(arr) if inputs[k].shape == () else arr
                else:
                    clean_arguments[k] = v

            result = _finite_call(fn, **clean_arguments)

            out_specs = list(outputs.items())
            if len(out_specs) == 1:
                out_name, out_spec = out_specs[0]
                _validate_tensor_against_spec(
                    name=out_name,
                    val=result,
                    spec=out_spec,
                    symbolic_dims=symbolic_dims,
                    atom_id=atom_id,
                    direction="Output",
                    variadic_dims=variadic_dims,
                )
            elif isinstance(result, (tuple, list)) and len(result) == len(out_specs):
                for item_val, (out_name, out_spec) in zip(result, out_specs):
                    _validate_tensor_against_spec(
                        name=out_name,
                        val=item_val,
                        spec=out_spec,
                        symbolic_dims=symbolic_dims,
                        atom_id=atom_id,
                        direction="Output",
                        variadic_dims=variadic_dims,
                    )
            elif isinstance(result, dict):
                for out_name, out_spec in out_specs:
                    if out_name not in result:
                        raise AtomicContractViolationError(
                            f"[{atom_id} Output Missing] Expected output key `{out_name}` in returned dict!"
                        )
                    _validate_tensor_against_spec(
                        name=out_name,
                        val=result[out_name],
                        spec=out_spec,
                        symbolic_dims=symbolic_dims,
                        atom_id=atom_id,
                        direction="Output",
                        variadic_dims=variadic_dims,
                    )
            return result

        fn_name_to_atom_id = {
            info.get("function_name", ""): aid
            for aid, info in GLOBAL_ATOM_REGISTRY.items()
            if info.get("function_name")
        }
        auto_detected_upstreams = sorted(
            {fn_name_to_atom_id[c] for c in ast_calls if c in fn_name_to_atom_id and fn_name_to_atom_id[c] != atom_id}
        )
        merged_upstreams = sorted(set(upstream_atoms) | set(auto_detected_upstreams))
        undeclared_upstreams = sorted(set(auto_detected_upstreams) - set(upstream_atoms))

        for up_id in merged_upstreams:
            if up_id in GLOBAL_ATOM_REGISTRY:
                down_list = GLOBAL_ATOM_REGISTRY[up_id].setdefault("downstream_atoms", [])
                if atom_id not in down_list:
                    down_list.append(atom_id)

        meta = {
            "atom_id": atom_id,
            "function_name": fn.__name__,
            "tutor_station": tutor_station,
            "math_contract": math_contract.strip(),
            "file": inspect.getsourcefile(fn) or "<memory>",
            "source_lines": n_lines,
            "pure_function": pure_function,
            "inputs": {
                k: {"shape": list(v.shape), "unit": v.unit, "domain": list(v.domain), "monotonic": v.monotonic}
                for k, v in inputs.items()
            },
            "outputs": {
                k: {"shape": list(v.shape), "unit": v.unit, "domain": list(v.domain), "monotonic": v.monotonic}
                for k, v in outputs.items()
            },
            "upstream_atoms": merged_upstreams,
            "downstream_atoms": list(downstream_atoms),
            "ast_called_symbols": ast_calls,
            "ast_auto_detected_upstreams": auto_detected_upstreams,
            "ast_undeclared_upstreams_reconciled": undeclared_upstreams,
            "parameter_taint_flow": taint_flow_map,
            "gate_status": "REGISTERED",
        }
        setattr(wrapper, "_atom_metadata", meta)
        GLOBAL_ATOM_REGISTRY[atom_id] = meta
        return wrapper

    return decorator


class AtomManifestIndex:
    """
    Manages `atom_manifest.json` — the O(1) Station <-> Atomic Capsule DAG Index,
    equipped with AST Call-Graph Auto-Discovery and bidirectional DAG reconciliation.
    """

    def __init__(self, project_name: str, atoms: Optional[Dict[str, Dict[str, Any]]] = None) -> None:
        self.project_name = project_name
        self.atoms: Dict[str, Dict[str, Any]] = dict(atoms or GLOBAL_ATOM_REGISTRY)
        self.reconcile_ast_call_graph()

    def reconcile_ast_call_graph(self, strict: bool = False) -> List[Dict[str, Any]]:
        fn_to_atom: Dict[str, str] = {
            info.get("function_name", ""): aid
            for aid, info in self.atoms.items()
            if info.get("function_name")
        }
        reconciled_edges: List[Dict[str, Any]] = []
        for aid, info in self.atoms.items():
            called_syms = info.get("ast_called_symbols", [])
            declared_up = set(info.get("upstream_atoms", []))
            for sym in called_syms:
                if sym in fn_to_atom and fn_to_atom[sym] != aid:
                    up_aid = fn_to_atom[sym]
                    if up_aid not in declared_up:
                        reconciled_edges.append({
                            "caller_atom": aid,
                            "callee_upstream_atom": up_aid,
                            "callee_function": sym,
                        })
                        if strict:
                            raise AtomicContractViolationError(
                                f"[AST Call-Graph Undeclared Dependency] Atom `{aid}` calls `{sym}` (`{up_aid}`) "
                                f"in its AST without declaring `{up_aid}` in `upstream_atoms`!"
                            )
                        info.setdefault("upstream_atoms", []).append(up_aid)
                        declared_up.add(up_aid)
            for up_aid in info.get("upstream_atoms", []):
                if up_aid in self.atoms:
                    down_list = self.atoms[up_aid].setdefault("downstream_atoms", [])
                    if aid not in down_list:
                        down_list.append(aid)
        return reconciled_edges

    @classmethod
    def load(cls, path: Path) -> "AtomManifestIndex":
        doc = json.loads(path.read_text(encoding="utf-8"))
        return cls(project_name=doc.get("project", "Unknown"), atoms=doc.get("atoms", {}))

    def register_verification_receipt(self, atom_id: str, receipt: Dict[str, Any]) -> None:
        if atom_id in self.atoms:
            passed = receipt.get("gates_passed", [])
            from .evidence_contracts import valid_upstream_receipt
            if not valid_upstream_receipt(atom_id, receipt):
                raise AtomicContractViolationError("Receipt must identify the atom and explicitly prove a nonempty Tier-1/2 PASS")
            self.atoms[atom_id]["gate_status"] = "PASS"
            self.atoms[atom_id]["gate_status_detail"] = f"{len(passed)} gates: {', '.join(passed)}"
            self.atoms[atom_id]["last_verification_receipt"] = receipt

    def trace_downstream_impact(self, modified_atom_id: str) -> List[str]:
        self.reconcile_ast_call_graph(strict=False)
        visited: List[str] = []
        queue: List[str] = [modified_atom_id]
        while queue:
            curr = queue.pop(0)
            info = self.atoms.get(curr, {})
            for nxt in info.get("downstream_atoms", []):
                if nxt not in visited:
                    visited.append(nxt)
                    queue.append(nxt)
        return visited

    def save(self, path: Path) -> None:
        self.reconcile_ast_call_graph(strict=False)
        doc = {
            "schema_version": 2,
            "project": self.project_name,
            "atom_count": len(self.atoms),
            "atoms": self.atoms,
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


GLOBAL_ATOM_REGISTRY: Dict[str, Dict[str, Any]] = {}
