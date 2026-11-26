"""Behavioral checks for stage-local evidence and fail-closed commits."""
import copy
import json
from awf_guard.execution_flow import execute_stage
from awf_guard.errors import AntiGoodhartGateError
from awf_guard.slot_receipts import _SUBCHECK_TO_UNIVERSAL_SLOT_MAP

LABEL = next(iter(_SUBCHECK_TO_UNIVERSAL_SLOT_MAP))


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def good_stage(value, receipt):
    receipt["observed_value"] = value
    receipt["gates_passed"].append(LABEL)
    return value + 1


def late_failure(receipt):
    receipt["observed_value"] = "partial"
    receipt["gates_passed"].append(LABEL)
    raise AntiGoodhartGateError("Failed after collecting partial evidence")


def unknown_label(receipt):
    receipt["observed_value"] = "partial"
    receipt["gates_passed"].append("unregistered label")


def malformed_labels(receipt):
    receipt["observed_value"] = "partial"
    receipt["gates_passed"] = "malformed"


def collision(receipt):
    receipt["station_id"] = "replacement"
    receipt["gates_passed"].append(LABEL)


def rejected_without_commit(function, receipt):
    before = copy.deepcopy(receipt)
    caught = False
    try:
        execute_stage(function, receipt)
    except AntiGoodhartGateError:
        caught = True
    require(caught and receipt == before, "Rejected stage altered the destination receipt")


def test_execution_checks():
    receipt = {"station_id": "original", "gates_passed": []}
    for function in (late_failure, unknown_label, malformed_labels, collision):
        rejected_without_commit(function, receipt)
    rejected_without_commit(late_failure, {"station_id": "original"})
    result = execute_stage(good_stage, receipt, 4)
    if result != 5 or receipt != {"station_id": "original", "observed_value": 4, "gates_passed": [LABEL]}:
        raise AssertionError("Successful stage did not commit its evidence exactly once")
    return {"status": "PASS", "rejected_without_commit": 5, "successful_commit": True}


run_execution_checks = test_execution_checks


if __name__ == "__main__":
    print(json.dumps(run_execution_checks(), indent=2))
