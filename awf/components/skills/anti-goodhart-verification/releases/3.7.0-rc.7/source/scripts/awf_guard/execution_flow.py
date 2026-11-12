"""Run one functional stage and commit its evidence only after successful completion."""
from .errors import AntiGoodhartGateError
from .slot_receipts import _SUBCHECK_TO_UNIVERSAL_SLOT_MAP


def execute_stage(function, receipt, *args, **kwargs):
    if not isinstance(receipt.get("gates_passed"), list):
        raise AntiGoodhartGateError("Destination receipt requires a gate-label list")
    staged = {"gates_passed": []}
    result = function(*args, receipt=staged, **kwargs)
    if not isinstance(staged.get("gates_passed"), list) or not all(isinstance(label, str) for label in staged["gates_passed"]):
        raise AntiGoodhartGateError("Stage evidence requires a list of string gate labels")
    unknown = set(staged["gates_passed"]) - set(_SUBCHECK_TO_UNIVERSAL_SLOT_MAP)
    if unknown:
        raise AntiGoodhartGateError(f"Stage produced unregistered evidence labels: {sorted(unknown)}")
    payload = {key: value for key, value in staged.items() if key != "gates_passed"}
    collisions = set(payload) & set(receipt)
    if collisions:
        raise AntiGoodhartGateError(f"Stage overwrote existing evidence keys: {sorted(collisions)}")
    receipt.update(payload)
    receipt["gates_passed"].extend(staged["gates_passed"])
    return result
