#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
reference = (ROOT / "references" / "content-and-evidence.md").read_text(encoding="utf-8")
skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")

required_contract = [
    "Object or candidate",
    "Objectives and directions",
    "Operation",
    "Output",
    "Non-answers and downstream steps",
    "mathematically verify",
    "What is one candidate or data point here?",
]

missing = [term for term in required_contract if term not in reference]
assert not missing, f"missing concrete-system contract terms: {missing}"
assert "concrete-system semantics contract" in skill
assert "objective 1" in reference and "objective 2" in reference
assert "ranked list" in reference and "execution batch" in reference
print("PASS concrete-system semantics contract")
