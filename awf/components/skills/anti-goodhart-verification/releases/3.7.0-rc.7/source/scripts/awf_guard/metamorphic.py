"""AWF Guard: metamorphic."""
from __future__ import annotations

from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import Literal
from typing import Optional
from typing import Sequence
from typing import Tuple
from awf_guard_numeric_contracts import finite_array as _finite_array
from awf_guard_numeric_contracts import finite_call as _finite_call
from awf_guard_numeric_contracts import finite_float as _finite_float
import abc
from dataclasses import dataclass
import functools
import itertools
import numpy as np
import random
from .errors import AntiGoodhartGateError
from .errors import SecondOrderCollusionError
from .numeric_inputs import _extract_array


class MetamorphicInvalidInputSkip(Exception):
    """Raised when a source or followup input fails `valid_input_fn` domain preconditions."""


class MetamorphicParameterGenerator(abc.ABC):
    """Base protocol for randomized parameter generators in `@metamorphic_randomized`."""
    @abc.abstractmethod
    def generate(self) -> Any:
        raise NotImplementedError


class RandIntGenerator(MetamorphicParameterGenerator):
    """Deterministic seeded integer generator in `[low, high]` (inclusive)."""
    def __init__(self, low: int, high: int, seed: int = 42) -> None:
        self.low = int(low)
        self.high = int(high)
        self._rng = random.Random(seed)

    def generate(self) -> int:
        return self._rng.randint(self.low, self.high)


class RandFloatGenerator(MetamorphicParameterGenerator):
    """Deterministic seeded float generator in `[low, high]`."""
    def __init__(self, low: float, high: float, seed: int = 42) -> None:
        self.low = _finite_float(low)
        self.high = _finite_float(high)
        self._rng = random.Random(seed)

    def generate(self) -> float:
        return self._rng.uniform(self.low, self.high)


def metamorphic_fixed(arg: str, value: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Bind a fixed parameter `arg=value` to a metamorphic transformation and record it
    into `mtc.parameters[arg]` for downstream inspection in `@general_relation(mtc)`.
    """
    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Tuple[Any, Dict[str, Any], bool]:
            kwargs[arg] = value
            raw_res = _finite_call(fn, *args, **kwargs)
            if isinstance(raw_res, tuple) and len(raw_res) == 3 and raw_res[2] is True:
                return raw_res[0], raw_res[1], True
            return raw_res, dict(kwargs), True
        return wrapper
    return decorator


def metamorphic_randomized(
    arg: str,
    generator: MetamorphicParameterGenerator,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Bind a randomized parameter `arg=generator.generate()` to a metamorphic transformation
    and record the sampled value into `mtc.parameters[arg]` for `@general_relation(mtc)`.
    """
    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Tuple[Any, Dict[str, Any], bool]:
            kwargs[arg] = generator.generate()
            raw_res = _finite_call(fn, *args, **kwargs)
            if isinstance(raw_res, tuple) and len(raw_res) == 3 and raw_res[2] is True:
                return raw_res[0], raw_res[1], True
            return raw_res, dict(kwargs), True
        return wrapper
    return decorator


class MetamorphicTestCaseState:
    """
    Execution state of a single General Metamorphic Test Case (`MTC`), supporting:
    - $k$ source inputs (`source_inputs`) and $k$ evaluated source outputs (`source_outputs`),
    - $m$ followup inputs (`followup_inputs`) and $m$ evaluated followup outputs (`followup_outputs`),
    - Transformation parameters (`parameters`) accessible inside both `general_transform_fn(mtc)`
      and `general_relation_fn(mtc)`.
    """

    def __init__(
        self,
        source_inputs: Sequence[Any],
        parameters: Optional[Dict[str, Any]] = None,
    ) -> None:
        self._source_inputs: List[Any] = list(source_inputs)
        self._source_outputs: Optional[List[Any]] = None
        self._followup_inputs: Optional[List[Any]] = None
        self._followup_outputs: Optional[List[Any]] = None
        self.parameters: Dict[str, Any] = dict(parameters) if parameters else {}

    @property
    def source_inputs(self) -> List[Any]:
        return self._source_inputs

    @property
    def source_input(self) -> Any:
        if len(self._source_inputs) != 1:
            raise AntiGoodhartGateError(
                f"MTC has {len(self._source_inputs)} source inputs; use `mtc.source_inputs` instead of `mtc.source_input`."
            )
        return self._source_inputs[0]

    @property
    def source_outputs(self) -> List[Any]:
        if self._source_outputs is None:
            raise AntiGoodhartGateError("`mtc.source_outputs` accessed before SUT evaluation!")
        return self._source_outputs

    @source_outputs.setter
    def source_outputs(self, val: Sequence[Any]) -> None:
        self._source_outputs = list(val)

    @property
    def source_output(self) -> Any:
        outs = self.source_outputs
        if len(outs) != 1:
            raise AntiGoodhartGateError(
                f"MTC has {len(outs)} source outputs; use `mtc.source_outputs` instead of `mtc.source_output`."
            )
        return outs[0]

    @property
    def followup_inputs(self) -> List[Any]:
        if self._followup_inputs is None:
            raise AntiGoodhartGateError("`mtc.followup_inputs` accessed before transformation!")
        return self._followup_inputs

    @followup_inputs.setter
    def followup_inputs(self, val: Sequence[Any]) -> None:
        self._followup_inputs = list(val)

    @property
    def followup_input(self) -> Any:
        fins = self.followup_inputs
        if len(fins) != 1:
            raise AntiGoodhartGateError(
                f"MTC has {len(fins)} followup inputs; use `mtc.followup_inputs` instead of `mtc.followup_input`."
            )
        return fins[0]

    @property
    def followup_outputs(self) -> List[Any]:
        if self._followup_outputs is None:
            raise AntiGoodhartGateError("`mtc.followup_outputs` accessed before followup SUT evaluation!")
        return self._followup_outputs

    @followup_outputs.setter
    def followup_outputs(self, val: Sequence[Any]) -> None:
        self._followup_outputs = list(val)

    @property
    def followup_output(self) -> Any:
        fouts = self.followup_outputs
        if len(fouts) != 1:
            raise AntiGoodhartGateError(
                f"MTC has {len(fouts)} followup outputs; use `mtc.followup_outputs` instead of `mtc.followup_output`."
            )
        return fouts[0]


def gmt_approximately(
    a: Any,
    b: Any,
    rel: float = 1e-6,
    abs_tol: float = 1e-8,
    **_kwargs: Any,
) -> bool:
    """Numerical approximate equality relation supporting scalars and NumPy arrays."""
    arr_a = _extract_array(a)
    arr_b = _extract_array(b)
    if arr_a.shape != arr_b.shape:
        return False
    return bool(np.allclose(arr_a, arr_b, rtol=rel, atol=abs_tol))


def gmt_or(
    rel1: Callable[..., bool],
    rel2: Callable[..., bool],
) -> Callable[..., bool]:
    """Disjunctive combinator constructing `rel1(...) or rel2(...)`."""
    def _combined(*args: Any, **kwargs: Any) -> bool:
        return bool(rel1(*args, **kwargs) or rel2(*args, **kwargs))
    _combined.__name__ = f"({getattr(rel1, '__name__', 'rel1')}_or_{getattr(rel2, '__name__', 'rel2')})"
    return _combined


@dataclass
class MetamorphicRelationSpec:
    """
    Specification for a General $k$-Source $\\to$ $m$-Followup or Output-Dependent Metamorphic Relation.
    """
    mr_id: str
    data: Sequence[Any]
    testing_strategy: Literal["exhaustive", "sample"] = "exhaustive"
    number_of_sources: int = 1
    number_of_test_cases: int = 10
    parameters: Optional[Dict[str, Sequence[Any]]] = None
    transform_fn: Optional[Callable[..., Any]] = None
    general_transform_fn: Optional[Callable[..., Any]] = None
    relation_fn: Optional[Callable[..., bool]] = None
    general_relation_fn: Optional[Callable[[MetamorphicTestCaseState], bool]] = None
    valid_input_fn: Optional[Callable[[Any], bool]] = None
    seed: int = 42

    def generate_mtc_states(self) -> List[MetamorphicTestCaseState]:
        """Generate combinatorial (`EXHAUSTIVE` C(N, k)) or sampled (`SAMPLE`) MTC states."""
        n_data = len(self.data)
        if n_data < self.number_of_sources:
            raise AntiGoodhartGateError(
                f"[Metamorphic Relation `{self.mr_id}`] Dataset length ({n_data}) < number_of_sources ({self.number_of_sources})!"
            )

        if self.testing_strategy == "exhaustive":
            if self.number_of_sources == 1:
                source_tuples = [(item,) for item in self.data]
            else:
                source_tuples = list(itertools.combinations(self.data, self.number_of_sources))
        elif self.testing_strategy == "sample":
            rng = random.Random(self.seed)
            if self.number_of_sources == 1:
                if n_data < self.number_of_test_cases:
                    source_tuples = [(rng.choice(self.data),) for _ in range(self.number_of_test_cases)]
                else:
                    source_tuples = [(x,) for x in rng.sample(list(self.data), self.number_of_test_cases)]
            else:
                source_tuples = [
                    tuple(rng.sample(list(self.data), self.number_of_sources))
                    for _ in range(self.number_of_test_cases)
                ]
        else:
            raise AntiGoodhartGateError(f"Unsupported testing_strategy: {self.testing_strategy}")

        if not self.parameters:
            return [MetamorphicTestCaseState(source_inputs=st) for st in source_tuples]

        keys = list(self.parameters.keys())
        val_lists = [self.parameters[k] for k in keys]
        param_dicts = [dict(zip(keys, prod)) for prod in itertools.product(*val_lists)]
        states: List[MetamorphicTestCaseState] = []
        for st in source_tuples:
            for p_dict in param_dicts:
                states.append(MetamorphicTestCaseState(source_inputs=st, parameters=p_dict))
        return states


def _invoke_sut_on_input(sut_fn: Callable[..., Any], inp: Any) -> Any:
    """Invoke `sut_fn` cleanly whether `inp` is a kwargs dict, a tuple of args, or a single value."""
    if isinstance(inp, dict):
        return _finite_call(sut_fn, **inp)
    return _finite_call(sut_fn, inp)


def _inputs_are_identical(inp_a: Any, inp_b: Any) -> bool:
    """Check if a followup input is trivially identical to a source input (anti-spoofing check)."""
    if isinstance(inp_a, dict) and isinstance(inp_b, dict):
        if set(inp_a.keys()) != set(inp_b.keys()):
            return False
        for k in inp_a:
            va, vb = inp_a[k], inp_b[k]
            if isinstance(va, np.ndarray) or isinstance(vb, np.ndarray):
                arr_a, arr_b = _finite_array(va, dtype=float), _finite_array(vb, dtype=float)
                if arr_a.shape != arr_b.shape or _finite_float(np.linalg.norm(arr_a - arr_b)) > 1e-10:
                    return False
            elif va != vb:
                return False
        return True
    if isinstance(inp_a, np.ndarray) or isinstance(inp_b, np.ndarray):
        arr_a, arr_b = _finite_array(inp_a, dtype=float), _finite_array(inp_b, dtype=float)
        return bool(arr_a.shape == arr_b.shape and _finite_float(np.linalg.norm(arr_a - arr_b)) <= 1e-10)
    return bool(inp_a == inp_b)


def execute_metamorphic_relation_suite(
    sut_fn: Callable[..., Any],
    relations: Sequence[MetamorphicRelationSpec],
) -> Dict[str, Any]:
    """
    Execute a suite of `MetamorphicRelationSpec` objects against `sut_fn`.
    Crucial property from `tum-i4/gemtest`:
    - `mtc.source_outputs` are evaluated BEFORE `general_transform_fn(mtc)` is called,
      so followup transformations can depend on `mtc.source_outputs` (e.g., idempotence /
      projection / fixed-point / inverse round-trip tests)!
    - Enforces anti-spoofing: if all MTCs are skipped (`passed_count == 0`) or if the
      transformation trivially returns the unmodified source input across all MTCs, raises `AntiGoodhartGateError`.
    """
    suite_reports: List[Dict[str, Any]] = []
    for mr in relations:
        if (mr.transform_fn is None and mr.general_transform_fn is None) or (
            mr.relation_fn is None and mr.general_relation_fn is None
        ):
            raise AntiGoodhartGateError(
                f"[Metamorphic Relation `{mr.mr_id}`] Must define both a transformation and a relation function!"
            )

        mtc_states = mr.generate_mtc_states()
        passed_count = 0
        skipped_count = 0
        failed_details: List[str] = []
        non_identity_transform_seen = False

        for idx, mtc in enumerate(mtc_states):
            try:
                # 1. Domain precondition check on source inputs
                if mr.valid_input_fn is not None:
                    for s_in in mtc.source_inputs:
                        if not _finite_call(mr.valid_input_fn, s_in):
                            raise MetamorphicInvalidInputSkip("Source input outside valid domain.")

                # 2. Evaluate source outputs FIRST (so general_transform_fn can inspect mtc.source_outputs!)
                mtc.source_outputs = [_invoke_sut_on_input(sut_fn, s_in) for s_in in mtc.source_inputs]

                # 3. Generate followup input(s)
                if mr.general_transform_fn is not None:
                    raw_trans = _finite_call(mr.general_transform_fn, mtc)
                else:
                    assert mr.transform_fn is not None
                    if mtc.parameters:
                        raw_trans = _finite_call(mr.transform_fn, mtc.source_input, **mtc.parameters)
                    else:
                        raw_trans = _finite_call(mr.transform_fn, mtc.source_input)

                if isinstance(raw_trans, tuple) and len(raw_trans) == 3 and raw_trans[2] is True:
                    followup_raw, bound_kwargs, _ = raw_trans
                    overlap = set(mtc.parameters.keys()) & set(bound_kwargs.keys())
                    for k_ov in overlap:
                        if mtc.parameters[k_ov] != bound_kwargs[k_ov]:
                            raise AntiGoodhartGateError(
                                f"[Metamorphic Relation `{mr.mr_id}`] Duplicate parameter `{k_ov}` conflict!"
                            )
                    mtc.parameters.update(bound_kwargs)
                else:
                    followup_raw = raw_trans

                if isinstance(followup_raw, tuple):
                    mtc.followup_inputs = list(followup_raw)
                else:
                    mtc.followup_inputs = [followup_raw]

                # Check whether transformation is non-trivial
                if len(mtc.followup_inputs) != len(mtc.source_inputs) or any(
                    not _inputs_are_identical(s_in, f_in)
                    for s_in, f_in in zip(mtc.source_inputs, mtc.followup_inputs)
                ):
                    non_identity_transform_seen = True

                # 4. Domain precondition check on followup inputs
                if mr.valid_input_fn is not None:
                    for f_in in mtc.followup_inputs:
                        if not _finite_call(mr.valid_input_fn, f_in):
                            raise MetamorphicInvalidInputSkip("Followup input outside valid domain.")

                # 5. Evaluate followup outputs
                mtc.followup_outputs = [_invoke_sut_on_input(sut_fn, f_in) for f_in in mtc.followup_inputs]

                # 6. Evaluate Metamorphic Relation
                if mr.general_relation_fn is not None:
                    holds = bool(_finite_call(mr.general_relation_fn, mtc))
                else:
                    assert mr.relation_fn is not None
                    holds = bool(_finite_call(mr.relation_fn, mtc.source_output, mtc.followup_output, **mtc.parameters))

                if holds:
                    passed_count += 1
                else:
                    failed_details.append(
                        f"MTC#{idx} failed relation `{mr.mr_id}` with params={mtc.parameters}"
                    )

            except MetamorphicInvalidInputSkip:
                skipped_count += 1

        if failed_details:
            raise AntiGoodhartGateError(
                f"[Metamorphic Relation `{mr.mr_id}` Violation] {len(failed_details)}/{len(mtc_states)} MTCs failed! "
                f"First failure: {failed_details[0]}"
            )
        if passed_count == 0:
            raise AntiGoodhartGateError(
                f"[Metamorphic Relation `{mr.mr_id}` Vacuous Skip Trap] 0 passed MTCs ({skipped_count} skipped)! "
                f"Domain guard `valid_input_fn` rejected all test cases."
            )
        if not non_identity_transform_seen:
            raise SecondOrderCollusionError(
                f"[Meta-Guard Trivial Metamorphic Transform] `{mr.mr_id}` left all followup inputs identical to source inputs!"
            )

        suite_reports.append({
            "mr_id": mr.mr_id,
            "strategy": mr.testing_strategy,
            "number_of_sources": mr.number_of_sources,
            "total_mtcs": len(mtc_states),
            "passed_mtcs": passed_count,
            "skipped_mtcs": skipped_count,
        })

    return {
        "status": "PASS",
        "relations_verified": len(suite_reports),
        "reports": suite_reports,
    }
