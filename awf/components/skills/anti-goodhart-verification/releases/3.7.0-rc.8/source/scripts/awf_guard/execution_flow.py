"""Run one functional stage and commit its evidence only after successful completion."""
from .errors import AntiGoodhartGateError
from .slot_receipts import _SUBCHECK_TO_UNIVERSAL_SLOT_MAP


def execute_stage(function, receipt, *args, **kwargs):
    if not isinstance(receipt.get("gates_passed"), list):
        raise AntiGoodhartGateError("Destination receipt requires a gate-label list")
    has_warnings = isinstance(receipt.get("borderline_warnings"), list)
    staged = {"gates_passed": []}
    if has_warnings:
        staged["borderline_warnings"] = []
    result = function(*args, receipt=staged, **kwargs)
    if not isinstance(staged.get("gates_passed"), list) or not all(isinstance(label, str) for label in staged["gates_passed"]):
        raise AntiGoodhartGateError("Stage evidence requires a list of string gate labels")
    if has_warnings and (
        not isinstance(staged.get("borderline_warnings"), list)
        or not all(isinstance(item, str) for item in staged["borderline_warnings"])
    ):
        raise AntiGoodhartGateError("Stage borderline_warnings requires a list of strings")
    unknown = set(staged["gates_passed"]) - set(_SUBCHECK_TO_UNIVERSAL_SLOT_MAP)
    if unknown:
        raise AntiGoodhartGateError(f"Stage produced unregistered evidence labels: {sorted(unknown)}")
    payload = {
        key: value
        for key, value in staged.items()
        if key not in {"gates_passed", "borderline_warnings"}
    }
    collisions = set(payload) & set(receipt)
    if collisions:
        raise AntiGoodhartGateError(f"Stage overwrote existing evidence keys: {sorted(collisions)}")
    receipt.update(payload)
    receipt["gates_passed"].extend(staged["gates_passed"])
    if has_warnings and staged.get("borderline_warnings"):
        receipt["borderline_warnings"].extend(staged["borderline_warnings"])
    return result
