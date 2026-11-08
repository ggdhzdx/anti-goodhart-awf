#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
reference = (ROOT / "references" / "content-and-evidence.md").read_text(encoding="utf-8")

required = [
    "concrete object, phenomenon, relationship, or question",
    "lesson workflow",
    "natural enough to read aloud",
    "Use concrete scientific titles",
    "textbook table of contents",
]

missing = [term for term in required if term not in skill + reference]
assert not missing, f"missing concrete-title guidance: {missing}"
for phrase in ["先把研究对象说清楚", "追踪一条可验证的因果链", "把今天的解释压缩成两句话"]:
    assert phrase in reference, f"missing anti-pattern example: {phrase}"
print("PASS concrete scientific title guidance")
