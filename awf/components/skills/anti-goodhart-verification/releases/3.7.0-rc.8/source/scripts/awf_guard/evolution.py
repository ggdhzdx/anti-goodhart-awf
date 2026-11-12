"""AWF Guard: evolution."""
from __future__ import annotations

from typing import Any
from typing import Dict
from typing import List
from pathlib import Path
import json


def record_gate_escape_and_evolve(
    ledger_path: Path,
    escaped_symptom: str,
    missed_by_gate: str,
    root_cause_why_missed: str,
    new_gate_patch_description: str,
) -> Dict[str, Any]:
    entries: List[Dict[str, Any]] = []
    if ledger_path.exists():
        try:
            entries = json.loads(ledger_path.read_text(encoding="utf-8"))
        except Exception:
            entries = []
    new_entry = {
        "escape_index": len(entries) + 1,
        "escaped_symptom": escaped_symptom,
        "missed_by_gate": missed_by_gate,
        "root_cause_why_missed": root_cause_why_missed,
        "new_gate_patch_description": new_gate_patch_description,
    }
    entries.append(new_entry)
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_path.write_text(json.dumps(entries, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return new_entry
