#!/usr/bin/env python3
"""Standalone integrity and self-test verifier for AWF Anti-Goodhart Suite."""
import ast
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
errors = []
manifest = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))

for rel, meta in manifest["files"].items():
    path = ROOT / rel
    if not path.is_file():
        errors.append(f"missing: {rel}")
        continue
    data = path.read_bytes()
    if len(data) != meta["bytes"]:
        errors.append(f"size mismatch: {rel}")
    if hashlib.sha256(data).hexdigest() != meta["sha256"]:
        errors.append(f"hash mismatch: {rel}")

known = set(manifest["files"]) | {"MANIFEST.json"}
actual = {
    p.relative_to(ROOT).as_posix()
    for p in ROOT.rglob("*")
    if p.is_file() and ".git" not in p.parts and "dist" not in p.parts and "__pycache__" not in p.parts
}
for rel in sorted(actual - known):
    errors.append(f"unlisted file: {rel}")

expected_locks = {
    "awf/workflows/design-anti-goodhart/releases/1.0.0-rc.9/versions.lock": {
        "skill.design-anti-goodhart": "1.0.0-rc.9",
        "skill.anti-goodhart-verification": "3.6.0-rc.1",
    },
    "awf/workflows/html-ppt/releases/1.0.0-rc.8/versions.lock": {
        "skill.html-ppt": "1.0.0-rc.11",
        "skill.design-anti-goodhart": "1.0.0-rc.9",
        "skill.anti-goodhart-verification": "3.6.0-rc.1",
    },
    "awf/workflows/anti-goodhart-verification/releases/3.6.0-rc.1/versions.lock": {
        "skill.anti-goodhart-verification": "3.6.0-rc.1",
    },
    "awf/workflows/adaptive-interactive-tutor/releases/1.0.0-rc.22/versions.lock": {
        "skill.adaptive-interactive-tutor": "1.0.0-rc.22",
        "skill.anti-goodhart-verification": "3.6.0-rc.1",
        "skill.design-anti-goodhart": "1.0.0-rc.9",
        "skill.html-ppt": "1.0.0-rc.11",
    },
}

for lock_rel, exp_comps in expected_locks.items():
    lp = ROOT / lock_rel
    if not lp.is_file():
        errors.append(f"missing lock: {lock_rel}")
    else:
        lock_doc = json.loads(lp.read_text(encoding="utf-8"))
        if lock_doc.get("components") != exp_comps:
            errors.append(f"lock mismatch in {lock_rel}: {lock_doc.get('components')}")

for path in ROOT.rglob("*"):
    if not path.is_file() or ".git" in path.parts or "dist" in path.parts or "__pycache__" in path.parts:
        continue
    if path.suffix == ".py":
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (SyntaxError, UnicodeDecodeError) as exc:
            errors.append(f"python syntax: {path.relative_to(ROOT)}: {exc}")
    if path.suffix.lower() == ".json" or path.name in {"component.yaml", "workflow.yaml", "versions.lock"}:
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"json/yaml parse: {path.relative_to(ROOT)}: {exc}")
    if path.name != "verify.py" and path.stat().st_size < 5_000_000:
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = ""
        if re.search(r"BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY|gh[pousr]_[A-Za-z0-9]{20,}", text):
            errors.append(f"credential pattern: {path.relative_to(ROOT)}")

design_script = ROOT / "awf/components/skills/design-anti-goodhart/releases/1.0.0-rc.9/source/scripts/awf_design_anti_goodhart_gates.py"
html_ppt_script = ROOT / "awf/components/skills/html-ppt/releases/1.0.0-rc.11/source/scripts/audit_single_slide_step.py"
guard_script = ROOT / "awf/components/skills/anti-goodhart-verification/releases/3.6.0-rc.1/source/scripts/awf_universal_anti_goodhart_gates.py"

for label, cmd in [
    ("DesignAG 18-Gate self-test", [sys.executable, "-B", str(design_script), "--self-test"]),
    ("HTML-PPT Tri-Mode 1-Slide-Per-Step self-test", [sys.executable, "-B", str(html_ppt_script), "--self-test"]),
    ("AWF Guard 73-Gate self-test", [sys.executable, "-B", str(guard_script), "--self-test"]),
]:
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if proc.returncode != 0:
        errors.append(f"{label} failed (rc={proc.returncode}): {proc.stderr or proc.stdout}")

if errors:
    print("FAIL")
    print("\n".join(errors))
    sys.exit(1)

print(
    f"PASS: {len(manifest['files'])} files verified; "
    "AWF DesignAG (18 gates + Stage 0 Global Blueprint + Dual-Stage GDD) + AWF HTML-PPT (Macro-to-Micro Tri-Mode) + AWF Guard (73 gates) + AWF Tutor V16 closure verified"
)
