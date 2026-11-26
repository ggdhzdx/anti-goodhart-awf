"""AWF Guard: task guardrails."""
from __future__ import annotations

from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Sequence
from typing import Tuple
from typing import Union
from awf_guard_numeric_contracts import finite_float as _finite_float
from awf_guard_numeric_contracts import finite_inputs as _finite_inputs
from dataclasses import dataclass
import json


_GUARDRAIL_ERROR_PENALTY = 15.0


_GUARDRAIL_WARNING_PENALTY = 5.0


_GUARDRAIL_SAFE_SCORE = 90.0


_GUARDRAIL_CONCERNS_SCORE = 70.0


_GUARDRAIL_ATTENTION_SCORE = 40.0


_PARALLEL_ABSTRACTION_KEYWORDS = (
    "helper", "service", "hook", "util", "utils",
    "manager", "controller", "store", "client", "adapter",
)


_VERITY_ALLOWED_KEYS = {
    "schema",
    "receiptId",
    "receiptSchema",
    "result",
    "signatureValid",
    "repositoryFingerprintMatches",
    "snapshotFingerprintMatches",
    "accepted",
    "reasonCode",
}


@dataclass(frozen=True)
class TaskGuardrailContract:
    """
    Bounded task implementation contract (`logi-cmd/agent-guardrails`):
    declares `intended_files`, `allowed_paths`, `allowed_change_types`,
    `protected_paths`, `required_commands`, `evidence_paths`, and consistency budgets.
    """
    task: str
    intended_files: Tuple[str, ...] = ()
    allowed_paths: Tuple[str, ...] = ()
    allowed_change_types: Tuple[str, ...] = ("implementation-only",)
    protected_paths: Tuple[str, ...] = ()
    required_commands: Tuple[str, ...] = ()
    evidence_paths: Tuple[str, ...] = ()
    max_changed_files_per_task: int = 10
    max_breadth_multiplier: float = 2.0
    require_tests_with_source_changes: bool = True
    require_review_notes_for_protected: bool = True


def _parent_dir_scope(filepath: str) -> str:
    norm = filepath.replace("\\", "/").strip("/")
    return norm.rsplit("/", 1)[0] if "/" in norm else ""


def _looks_like_parallel_abstraction(filepath: str) -> bool:
    base = filepath.replace("\\", "/").lower().rsplit("/", 1)[-1]
    return any(kw in base for kw in _PARALLEL_ABSTRACTION_KEYWORDS)


def _classify_guardrail_file_kind(filepath: str) -> str:
    norm = filepath.replace("\\", "/").lower()
    if any(k in norm for k in ("test", "__tests__", ".spec.", ".test.")):
        return "tests"
    if norm.endswith((".md", ".rst", ".txt")):
        return "docs"
    if any(k in norm for k in ("schema", "interface", "proto", "openapi", "api_contract")):
        return "interface"
    if any(k in norm for k in ("config", "migration", ".yml", ".yaml", ".toml", ".json")):
        return "config"
    return "implementation"


def compute_guardrail_composite_score(
    findings: Sequence[Dict[str, Any]],
    category_weights: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """
    Compute the `agent-guardrails` composite score (`0.0` to `100.0`) and deployment verdict
    (`crates/agent-guardrails-cli/src/check/scoring.rs`):
    - `error`: 15.0 base penalty (and immediately forces verdict `"blocked"`)
    - `warning`: 5.0 base penalty
    - Verdicts: `"blocked"` | `"safe-to-deploy"` (>=90) | `"pass-with-concerns"` (>=70) |
      `"needs-attention"` (>=40) | `"high-risk"` (<40).
    """
    if not findings:
        return {"score": 100.0, "verdict": "safe-to-deploy", "has_errors": False}

    total_deduction = 0.0
    total_weight = 0.0
    has_errors = False
    for f in findings:
        sev = f.get("severity", "warning")
        if sev == "error":
            has_errors = True
        base_pen = _GUARDRAIL_ERROR_PENALTY if sev == "error" else (_GUARDRAIL_WARNING_PENALTY if sev == "warning" else 0.0)
        cat = f.get("category", "other")
        if category_weights and cat in category_weights:
            w = _finite_float(category_weights[cat]) / 100.0
            total_deduction += base_pen * w
            total_weight += w
        else:
            total_deduction += base_pen
            total_weight += 1.0

    if total_weight > 0.0:
        total_deduction *= len(findings) / total_weight

    score = round(max(0.0, min(100.0, 100.0 - total_deduction)), 1)
    if has_errors:
        verdict = "blocked"
    elif score >= _GUARDRAIL_SAFE_SCORE:
        verdict = "safe-to-deploy"
    elif score >= _GUARDRAIL_CONCERNS_SCORE:
        verdict = "pass-with-concerns"
    elif score >= _GUARDRAIL_ATTENTION_SCORE:
        verdict = "needs-attention"
    else:
        verdict = "high-risk"

    return {"score": score, "verdict": verdict, "has_errors": has_errors}


@_finite_inputs
def verify_verity_receipt_payload(
    raw_payload: Union[str, bytes, Dict[str, Any]],
    exit_code: int = 0,
) -> Dict[str, Any]:
    """
    Strict schema-locked Verity verification receipt validator
    (`crates/agent-guardrails-cli/src/check/verity_receipt.rs`):
    - Enforces `schema == "verity-receipt-verification.v1"` and `deny_unknown_fields`
      (rejects any extra injected keys such as `commandOutput`);
    - Checks `accepted`, `signatureValid`, `repositoryFingerprintMatches`, `snapshotFingerprintMatches`;
    - Keeps receipt evidence strictly separate from scope/security/protected-path checks.
    """
    if isinstance(raw_payload, (str, bytes)):
        try:
            doc = json.loads(raw_payload)
        except Exception:
            return {
                "accepted": False,
                "finding": {
                    "severity": "error",
                    "category": "validation",
                    "code": "verity-verifier-invalid-output",
                    "message": "Verity returned invalid receipt verification JSON output.",
                },
                "evidence": None,
            }
    elif isinstance(raw_payload, dict):
        doc = dict(raw_payload)
    else:
        return {
            "accepted": False,
            "finding": {
                "severity": "error",
                "category": "validation",
                "code": "verity-verifier-invalid-output",
                "message": "Verity receipt payload is not a JSON object.",
            },
            "evidence": None,
        }

    # Strict `deny_unknown_fields` check
    if set(doc.keys()) != _VERITY_ALLOWED_KEYS:
        return {
            "accepted": False,
            "finding": {
                "severity": "error",
                "category": "validation",
                "code": "verity-verifier-invalid-output",
                "message": f"Verity receipt violated strict schema keys (extra/missing keys: {set(doc.keys()) ^ _VERITY_ALLOWED_KEYS}).",
            },
            "evidence": None,
        }

    if (
        doc.get("schema") != "verity-receipt-verification.v1"
        or not str(doc.get("receiptId", "")).strip()
        or not str(doc.get("receiptSchema", "")).strip()
        or not str(doc.get("result", "")).strip()
        or not str(doc.get("reasonCode", "")).strip()
    ):
        return {
            "accepted": False,
            "finding": {
                "severity": "error",
                "category": "validation",
                "code": "verity-verifier-invalid-output",
                "message": "Verity receipt missing required non-empty header fields.",
            },
            "evidence": None,
        }

    reason_code = str(doc["reasonCode"])
    is_accepted = (
        exit_code == 0
        and bool(doc.get("accepted")) is True
        and bool(doc.get("signatureValid")) is True
        and bool(doc.get("repositoryFingerprintMatches")) is True
        and bool(doc.get("snapshotFingerprintMatches")) is True
    )
    if not is_accepted:
        return {
            "accepted": False,
            "finding": {
                "severity": "error",
                "category": "validation",
                "code": f"verity-receipt-{reason_code}",
                "message": f"Verity rejected the receipt: {reason_code}.",
            },
            "evidence": None,
        }

    evidence = dict(doc)
    evidence["source"] = "verity"
    return {
        "accepted": True,
        "finding": None,
        "evidence": evidence,
    }


@_finite_inputs
def audit_task_guardrails_and_scope(
    contract: TaskGuardrailContract,
    changed_files: Sequence[str],
    commands_run: Sequence[str] = (),
    existing_evidence_files: Sequence[str] = (),
    has_review_notes: bool = True,
    total_added_lines: int = 0,
    verity_receipt_payload: Optional[Union[str, Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Run the `logi-cmd/agent-guardrails` pre-merge task scope, continuity, parallel-abstraction,
    source-without-tests, big-bang change, and Verity receipt audit.
    """
    findings: List[Dict[str, Any]] = []
    norm_changed = [f.replace("\\", "/") for f in changed_files]
    norm_intended = {f.replace("\\", "/") for f in contract.intended_files}
    norm_allowed = [p.replace("\\", "/").rstrip("/") + "/" for p in contract.allowed_paths]

    # 1. Allowed paths check
    if norm_allowed:
        out_of_scope = [
            f for f in norm_changed
            if not any(f.startswith(ap) or f == ap.rstrip("/") for ap in norm_allowed)
        ]
        if out_of_scope:
            findings.append({
                "severity": "error",
                "category": "scope",
                "code": "task-path-violation",
                "message": f"Files outside task allowed paths: {', '.join(out_of_scope)}.",
                "files": out_of_scope,
            })

    # 2. Intended files & parallel-abstraction continuity check
    if norm_intended:
        out_of_intended = [f for f in norm_changed if f not in norm_intended]
        if out_of_intended:
            findings.append({
                "severity": "error",
                "category": "scope",
                "code": "intended-file-violation",
                "message": f"Files outside intendedFiles: {', '.join(out_of_intended)}.",
                "files": out_of_intended,
            })
            intended_scopes = {_parent_dir_scope(f) for f in norm_intended if _parent_dir_scope(f)}
            for extra_f in out_of_intended:
                if _parent_dir_scope(extra_f) in intended_scopes and _looks_like_parallel_abstraction(extra_f):
                    findings.append({
                        "severity": "warning",
                        "category": "consistency",
                        "code": "continuity-parallel-abstraction",
                        "message": f"Parallel abstraction file created instead of extending intended files: {extra_f}.",
                        "files": [extra_f],
                    })

    # 3. Consistency file-count & breadth budget
    if len(norm_changed) > contract.max_changed_files_per_task:
        findings.append({
            "severity": "warning",
            "category": "consistency",
            "code": "changed-file-budget-exceeded",
            "message": f"Changed {len(norm_changed)} files > budget {contract.max_changed_files_per_task}.",
            "files": norm_changed,
        })

    # 4. Big-bang change detector (>15 files across >=3 top-level areas with >300 added lines)
    top_areas = {f.split("/", 1)[0] for f in norm_changed if "/" in f}
    if len(norm_changed) > 15 and len(top_areas) >= 3 and total_added_lines > 300:
        findings.append({
            "severity": "warning",
            "category": "consistency",
            "code": "big-bang-change",
            "message": f"Big-bang change detected: {len(norm_changed)} files across {len(top_areas)} top-level areas (+{total_added_lines} lines).",
            "files": norm_changed,
        })

    # 5. Change-type enforcement (`implementation-only` forbids `interface` or `config` changes)
    file_kinds = {f: _classify_guardrail_file_kind(f) for f in norm_changed}
    if "implementation-only" in contract.allowed_change_types and "interface-changing" not in contract.allowed_change_types:
        disallowed_ct = [f for f, k in file_kinds.items() if k not in ("implementation", "tests", "docs")]
        if disallowed_ct:
            findings.append({
                "severity": "error",
                "category": "scope",
                "code": "change-type-violation",
                "message": f"Changed files violate `implementation-only` change type: {', '.join(disallowed_ct)}.",
                "files": disallowed_ct,
            })

    # 6. Source-without-tests & missing required commands/evidence
    src_files = [f for f, k in file_kinds.items() if k == "implementation"]
    tst_files = [f for f, k in file_kinds.items() if k == "tests"]
    if contract.require_tests_with_source_changes and src_files and not tst_files:
        findings.append({
            "severity": "error",
            "category": "validation",
            "code": "source-without-tests",
            "message": "Source files changed without matching test changes.",
            "files": src_files,
        })

    missing_cmds = [c for c in contract.required_commands if c not in commands_run]
    if missing_cmds:
        findings.append({
            "severity": "error",
            "category": "validation",
            "code": "missing-required-commands",
            "message": f"Missing required validation commands: {', '.join(missing_cmds)}.",
            "files": [],
        })

    norm_ev_existing = {e.replace("\\", "/") for e in existing_evidence_files}
    missing_ev = [e for e in contract.evidence_paths if e.replace("\\", "/") not in norm_ev_existing]
    if missing_ev:
        findings.append({
            "severity": "error",
            "category": "validation",
            "code": "missing-evidence-files",
            "message": f"Missing required evidence files: {', '.join(missing_ev)}.",
            "files": missing_ev,
        })

    # 7. Protected paths review notes
    norm_prot = [p.replace("\\", "/").rstrip("/") for p in contract.protected_paths]
    touched_prot = [
        f for f in norm_changed
        if any(f == p or f.startswith(p + "/") for p in norm_prot)
    ]
    if touched_prot and contract.require_review_notes_for_protected and not has_review_notes:
        findings.append({
            "severity": "error",
            "category": "risk",
            "code": "protected-area-missing-review-notes",
            "message": f"Protected area touched without review notes: {', '.join(touched_prot)}.",
            "files": touched_prot,
        })

    # 8. Optional Verity receipt check
    verity_evidence = None
    if verity_receipt_payload is not None:
        v_res = verify_verity_receipt_payload(verity_receipt_payload)
        if v_res["finding"] is not None:
            findings.append(v_res["finding"])
        verity_evidence = v_res["evidence"]

    score_info = compute_guardrail_composite_score(findings)
    return {
        "status": "PASS" if score_info["verdict"] in ("safe-to-deploy", "pass-with-concerns") and not score_info["has_errors"] else "FAIL",
        "score": score_info["score"],
        "verdict": score_info["verdict"],
        "has_errors": score_info["has_errors"],
        "finding_count": len(findings),
        "findings": findings,
        "verity_evidence": verity_evidence,
    }
