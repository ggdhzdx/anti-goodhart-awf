"""AWF Guard: input contracts."""
from __future__ import annotations

from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional
from typing import Sequence
from awf_guard_numeric_contracts import finite_call as _finite_call
from awf_guard_numeric_contracts import finite_inputs as _finite_inputs
import copy
import hashlib
import numpy as np
from .tensor_contracts import QuantityTensor
from .numeric_inputs import _extract_array


def _update_value_sha256(hasher: "hashlib._Hash", val: Any) -> None:
    if isinstance(val, QuantityTensor):
        arr = np.ascontiguousarray(val.data)
        hasher.update(f"QuantityTensor:{val.unit}:{arr.shape}:{arr.dtype}:".encode("utf-8"))
        hasher.update(arr.tobytes())
    elif isinstance(val, np.ndarray):
        arr = np.ascontiguousarray(val)
        hasher.update(f"ndarray:{arr.shape}:{arr.dtype}:".encode("utf-8"))
        hasher.update(arr.tobytes())
    elif isinstance(val, dict):
        hasher.update(f"dict:{len(val)}:".encode("utf-8"))
        for dk in sorted(val.keys(), key=repr):
            _update_value_sha256(hasher, dk)
            _update_value_sha256(hasher, val[dk])
    elif isinstance(val, (list, tuple)):
        hasher.update(f"{type(val).__name__}:{len(val)}:".encode("utf-8"))
        for item in val:
            _update_value_sha256(hasher, item)
    elif isinstance(val, (set, frozenset)):
        hasher.update(f"{type(val).__name__}:{len(val)}:".encode("utf-8"))
        for item in sorted(val, key=repr):
            _update_value_sha256(hasher, item)
    elif isinstance(val, (bytes, bytearray)):
        hasher.update(f"bytes:{len(val)}:".encode("utf-8"))
        hasher.update(bytes(val))
    else:
        hasher.update(f"{type(val).__name__}:{val!r}".encode("utf-8"))


def snapshot_input_kwargs_sha256(kwargs: Dict[str, Any]) -> Dict[str, str]:
    """
    Capture a cryptographic SHA-256 snapshot (`icontract.snapshot` / `deal.pure`) of all caller
    arguments (including arbitrarily nested dicts/lists/tuples of NumPy arrays and `QuantityTensor`s)
    before invoking `target_fn` so in-place array/collection mutations are detected immediately.
    """
    digests: Dict[str, str] = {}
    for k, v in kwargs.items():
        h = hashlib.sha256()
        _update_value_sha256(h, v)
        digests[k] = h.hexdigest()
    return digests


@_finite_inputs
def verify_pure_input_immutability_and_contracts(
    target_fn: Callable[..., Any],
    sample_input_kwargs: Dict[str, Any],
    pre_fn: Optional[Callable[[Dict[str, Any]], bool]] = None,
    post_fn: Optional[Callable[[Dict[str, Any], Any, Dict[str, Any]], bool]] = None,
    adversarial_inputs: Optional[Sequence[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Design-by-Contract & Adversarial Boundary Verifier inspired by `Parquery/icontract`,
    `life4/deal`, and `pschanely/CrossHair`:
    1. **Precondition Contract (`icontract.require` / `deal.pre`)**:
       - Evaluates `pre_fn(kwargs)` prior to execution.
    2. **Input Immutability & Snapshot Contract (`deal.pure` / `icontract.snapshot`, `G3g`)**:
       - Deep-copies `OLD` state and computes SHA-256 digests of all caller input arrays before
         calling `target_fn(**kwargs)` and immediately after calling `target_fn(**kwargs)`.
       - Any in-place corruption of caller arrays (`mutated_inputs`) fails `G3g`.
    3. **Postcondition Relational Contract (`icontract.ensure` / `deal.post`, `G3g`)**:
       - Verifies `post_fn(kwargs, result, old_snapshot)` relating `result` to `OLD` inputs.
    4. **Adversarial Corner-Case Boundary Fuzzing (`CrossHair` / `deal.cases`, `G3h`)**:
       - Executes `target_fn` across `adversarial_inputs` (zero tensors, tiny positive $10^{-12}$
         inputs, steep single-bin spikes, boundary-mask edge cases) and verifies zero unhandled
         exceptions (`deal.has()`), zero input mutations, finite outputs, and `post_fn` satisfaction.
    """
    import copy

    mutated_inputs: List[str] = []
    contract_violations: List[str] = []
    adversarial_failures: List[Dict[str, Any]] = []

    def _run_single_trial(trial_kwargs: Dict[str, Any], label: str) -> None:
        if pre_fn is not None and not bool(_finite_call(pre_fn, trial_kwargs)):
            contract_violations.append(f"{label}: precondition `pre_fn` returned False")
            return
        old_copy = copy.deepcopy(trial_kwargs)
        pre_digests = snapshot_input_kwargs_sha256(trial_kwargs)
        try:
            res = _finite_call(target_fn, **trial_kwargs)
        except Exception as exc:
            if label == "primary":
                contract_violations.append(f"Primary invocation raised {type(exc).__name__}: {exc}")
            else:
                adversarial_failures.append({"case": label, "kind": "UnhandledException", "detail": str(exc)})
            return

        post_digests = snapshot_input_kwargs_sha256(trial_kwargs)
        for k, d_before in pre_digests.items():
            if post_digests.get(k) != d_before:
                mutated_inputs.append(f"{label}:{k}")

        arr_res = _extract_array(res)
        if not np.all(np.isfinite(arr_res)):
            if label == "primary":
                contract_violations.append("Primary output contains NaN or Inf")
            else:
                adversarial_failures.append({"case": label, "kind": "NonFiniteOutput", "detail": "NaN/Inf on boundary case"})
            return

        if post_fn is not None:
            ok_post = bool(_finite_call(post_fn, trial_kwargs, res, old_copy))
            if not ok_post:
                if label == "primary":
                    contract_violations.append("Primary invocation violated `post_fn(kwargs, result, old_snapshot)`")
                else:
                    adversarial_failures.append({"case": label, "kind": "PostconditionViolation", "detail": "post_fn returned False"})

    _run_single_trial(sample_input_kwargs, "primary")

    adv_list = list(adversarial_inputs or [])
    for idx, adv_kw in enumerate(adv_list):
        _run_single_trial(adv_kw, f"adversarial_{idx}")

    passed = (not mutated_inputs) and (not contract_violations) and (not adversarial_failures)
    return {
        "status": "PASS" if passed else "FAIL",
        "mutated_inputs": mutated_inputs,
        "contract_violations": contract_violations,
        "adversarial_cases_tested": len(adv_list),
        "adversarial_failures": adversarial_failures,
    }
