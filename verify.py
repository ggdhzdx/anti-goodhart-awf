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
    "awf/workflows/design-anti-goodhart/releases/1.0.0-rc.13/versions.lock": {
        "skill.design-anti-goodhart": "1.0.0-rc.13",
        "skill.anti-goodhart-verification": "3.7.0-rc.7",
        "tool.awf-repository-verifier": "1.0.0-rc.2",
    },
    "awf/workflows/design-anti-goodhart/releases/1.0.0-rc.14/versions.lock": {
        "skill.design-anti-goodhart": "1.0.0-rc.14",
        "skill.anti-goodhart-verification": "3.7.0-rc.7",
        "tool.awf-repository-verifier": "1.0.0-rc.2",
    },
    "awf/workflows/design-anti-goodhart/releases/1.0.0-rc.15/versions.lock": {
        "skill.design-anti-goodhart": "1.0.0-rc.15",
        "skill.anti-goodhart-verification": "3.7.0-rc.7",
        "tool.awf-repository-verifier": "1.0.0-rc.2",
    },
    "awf/workflows/design-anti-goodhart/releases/1.0.0-rc.16/versions.lock": {
        "skill.design-anti-goodhart": "1.0.0-rc.16",
        "skill.anti-goodhart-verification": "3.7.0-rc.7",
        "tool.awf-repository-verifier": "1.0.0-rc.2",
    },
    "awf/workflows/design-anti-goodhart/releases/1.0.0-rc.17/versions.lock": {
        "skill.design-anti-goodhart": "1.0.0-rc.17",
        "skill.anti-goodhart-verification": "3.7.0-rc.7",
        "tool.awf-repository-verifier": "1.0.0-rc.2",
    },
    "awf/workflows/design-anti-goodhart/releases/1.0.0-rc.18/versions.lock": {
        "skill.design-anti-goodhart": "1.0.0-rc.18",
        "skill.anti-goodhart-verification": "3.7.0-rc.7",
        "tool.awf-repository-verifier": "1.0.0-rc.2",
    },
    "awf/workflows/design-anti-goodhart/releases/1.0.0-rc.19/versions.lock": {
        "skill.design-anti-goodhart": "1.0.0-rc.19",
        "skill.anti-goodhart-verification": "3.7.0-rc.7",
        "tool.awf-repository-verifier": "1.0.0-rc.2",
    },
    "awf/workflows/design-anti-goodhart/releases/1.0.0-rc.20/versions.lock": {
        "skill.design-anti-goodhart": "1.0.0-rc.20",
        "skill.anti-goodhart-verification": "3.7.0-rc.7",
        "tool.awf-repository-verifier": "1.0.0-rc.2",
    },
    "awf/workflows/design-anti-goodhart/releases/1.0.0-rc.21/versions.lock": {
        "skill.design-anti-goodhart": "1.0.0-rc.21",
        "skill.anti-goodhart-verification": "3.7.0-rc.7",
        "tool.awf-repository-verifier": "1.0.0-rc.2",
    },
    "awf/workflows/design-anti-goodhart/releases/1.0.0-rc.22/versions.lock": {
        "skill.design-anti-goodhart": "1.0.0-rc.22",
        "skill.anti-goodhart-verification": "3.7.0-rc.7",
        "tool.awf-repository-verifier": "1.0.0-rc.2",
    },
    "awf/workflows/design-anti-goodhart/releases/1.0.0-rc.23/versions.lock": {
        "skill.design-anti-goodhart": "1.0.0-rc.23",
        "skill.anti-goodhart-verification": "3.7.0-rc.7",
        "tool.awf-repository-verifier": "1.0.0-rc.2",
    },
    "awf/workflows/design-anti-goodhart/releases/1.0.0-rc.24/versions.lock": {
        "skill.design-anti-goodhart": "1.0.0-rc.24",
        "skill.anti-goodhart-verification": "3.7.0-rc.7",
        "tool.awf-repository-verifier": "1.0.0-rc.2",
    },
    "awf/workflows/html-ppt/releases/1.0.0-rc.12/versions.lock": {
        "skill.html-ppt": "1.0.0-rc.15",
        "skill.design-anti-goodhart": "1.0.0-rc.13",
        "skill.anti-goodhart-verification": "3.7.0-rc.7",
        "tool.awf-repository-verifier": "1.0.0-rc.2",
    },
    "awf/workflows/html-ppt/releases/1.0.0-rc.13/versions.lock": {
        "skill.html-ppt": "1.0.0-rc.16",
        "skill.design-anti-goodhart": "1.0.0-rc.14",
        "skill.anti-goodhart-verification": "3.7.0-rc.7",
        "tool.awf-repository-verifier": "1.0.0-rc.2",
    },
    "awf/workflows/html-ppt/releases/1.0.0-rc.14/versions.lock": {
        "skill.html-ppt": "1.0.0-rc.17",
        "skill.design-anti-goodhart": "1.0.0-rc.15",
        "skill.anti-goodhart-verification": "3.7.0-rc.7",
        "tool.awf-repository-verifier": "1.0.0-rc.2",
    },
    "awf/workflows/html-ppt/releases/1.0.0-rc.15/versions.lock": {
        "skill.html-ppt": "1.0.0-rc.18",
        "skill.design-anti-goodhart": "1.0.0-rc.16",
        "skill.anti-goodhart-verification": "3.7.0-rc.7",
        "tool.awf-repository-verifier": "1.0.0-rc.2",
    },
    "awf/workflows/html-ppt/releases/1.0.0-rc.16/versions.lock": {
        "skill.html-ppt": "1.0.0-rc.19",
        "skill.design-anti-goodhart": "1.0.0-rc.17",
        "skill.anti-goodhart-verification": "3.7.0-rc.7",
        "tool.awf-repository-verifier": "1.0.0-rc.2",
    },
    "awf/workflows/html-ppt/releases/1.0.0-rc.17/versions.lock": {
        "skill.html-ppt": "1.0.0-rc.20",
        "skill.design-anti-goodhart": "1.0.0-rc.18",
        "skill.anti-goodhart-verification": "3.7.0-rc.7",
        "tool.awf-repository-verifier": "1.0.0-rc.2",
    },
    "awf/workflows/html-ppt/releases/1.0.0-rc.18/versions.lock": {
        "skill.html-ppt": "1.0.0-rc.21",
        "skill.design-anti-goodhart": "1.0.0-rc.19",
        "skill.anti-goodhart-verification": "3.7.0-rc.7",
        "tool.awf-repository-verifier": "1.0.0-rc.2",
    },
    "awf/workflows/html-ppt/releases/1.0.0-rc.19/versions.lock": {
        "skill.html-ppt": "1.0.0-rc.22",
        "skill.design-anti-goodhart": "1.0.0-rc.20",
        "skill.anti-goodhart-verification": "3.7.0-rc.7",
        "tool.awf-repository-verifier": "1.0.0-rc.2",
    },
    "awf/workflows/html-ppt/releases/1.0.0-rc.20/versions.lock": {
        "skill.html-ppt": "1.0.0-rc.23",
        "skill.design-anti-goodhart": "1.0.0-rc.21",
        "skill.anti-goodhart-verification": "3.7.0-rc.7",
        "tool.awf-repository-verifier": "1.0.0-rc.2",
    },
    "awf/workflows/html-ppt/releases/1.0.0-rc.21/versions.lock": {
        "skill.html-ppt": "1.0.0-rc.24",
        "skill.design-anti-goodhart": "1.0.0-rc.22",
        "skill.anti-goodhart-verification": "3.7.0-rc.7",
        "tool.awf-repository-verifier": "1.0.0-rc.2",
    },
    "awf/workflows/html-ppt/releases/1.0.0-rc.22/versions.lock": {
        "skill.html-ppt": "1.0.0-rc.25",
        "skill.design-anti-goodhart": "1.0.0-rc.23",
        "skill.anti-goodhart-verification": "3.7.0-rc.7",
        "tool.awf-repository-verifier": "1.0.0-rc.2",
    },
    "awf/workflows/html-ppt/releases/1.0.0-rc.23/versions.lock": {
        "skill.html-ppt": "1.0.0-rc.26",
        "skill.design-anti-goodhart": "1.0.0-rc.24",
        "skill.anti-goodhart-verification": "3.7.0-rc.7",
        "tool.awf-repository-verifier": "1.0.0-rc.2",
    },
    "awf/workflows/anti-goodhart-verification/releases/3.7.0-rc.8/versions.lock": {
        "skill.anti-goodhart-verification": "3.7.0-rc.8",
        "skill.manage-agent-workflows": "1.0.2",
        "tool.awf-repository-verifier": "1.0.0-rc.3",
    },
    "awf/workflows/adaptive-interactive-tutor/releases/1.0.0-rc.26/versions.lock": {
        "skill.adaptive-interactive-tutor": "1.0.0-rc.26",
        "skill.anti-goodhart-verification": "3.7.0-rc.7",
        "skill.design-anti-goodhart": "1.0.0-rc.13",
        "skill.html-ppt": "1.0.0-rc.15",
        "tool.awf-repository-verifier": "1.0.0-rc.2",
    },
    "awf/workflows/adaptive-interactive-tutor/releases/1.0.0-rc.27/versions.lock": {
        "skill.adaptive-interactive-tutor": "1.0.0-rc.27",
        "skill.anti-goodhart-verification": "3.7.0-rc.7",
        "skill.design-anti-goodhart": "1.0.0-rc.14",
        "skill.html-ppt": "1.0.0-rc.16",
        "tool.awf-repository-verifier": "1.0.0-rc.2",
    },
    "awf/workflows/adaptive-interactive-tutor/releases/1.0.0-rc.28/versions.lock": {
        "skill.adaptive-interactive-tutor": "1.0.0-rc.28",
        "skill.anti-goodhart-verification": "3.7.0-rc.7",
        "skill.design-anti-goodhart": "1.0.0-rc.15",
        "skill.html-ppt": "1.0.0-rc.17",
        "tool.awf-repository-verifier": "1.0.0-rc.2",
    },
    "awf/workflows/adaptive-interactive-tutor/releases/1.0.0-rc.29/versions.lock": {
        "skill.adaptive-interactive-tutor": "1.0.0-rc.29",
        "skill.anti-goodhart-verification": "3.7.0-rc.7",
        "skill.design-anti-goodhart": "1.0.0-rc.16",
        "skill.html-ppt": "1.0.0-rc.18",
        "tool.awf-repository-verifier": "1.0.0-rc.2",
    },
    "awf/workflows/adaptive-interactive-tutor/releases/1.0.0-rc.30/versions.lock": {
        "skill.adaptive-interactive-tutor": "1.0.0-rc.30",
        "skill.anti-goodhart-verification": "3.7.0-rc.7",
        "skill.design-anti-goodhart": "1.0.0-rc.17",
        "skill.html-ppt": "1.0.0-rc.19",
        "tool.awf-repository-verifier": "1.0.0-rc.2",
    },
    "awf/workflows/adaptive-interactive-tutor/releases/1.0.0-rc.31/versions.lock": {
        "skill.adaptive-interactive-tutor": "1.0.0-rc.31",
        "skill.anti-goodhart-verification": "3.7.0-rc.7",
        "skill.design-anti-goodhart": "1.0.0-rc.18",
        "skill.html-ppt": "1.0.0-rc.20",
        "tool.awf-repository-verifier": "1.0.0-rc.2",
    },
    "awf/workflows/adaptive-interactive-tutor/releases/1.0.0-rc.32/versions.lock": {
        "skill.adaptive-interactive-tutor": "1.0.0-rc.32",
        "skill.anti-goodhart-verification": "3.7.0-rc.7",
        "skill.design-anti-goodhart": "1.0.0-rc.19",
        "skill.html-ppt": "1.0.0-rc.21",
        "tool.awf-repository-verifier": "1.0.0-rc.2",
    },
    "awf/workflows/adaptive-interactive-tutor/releases/1.0.0-rc.33/versions.lock": {
        "skill.adaptive-interactive-tutor": "1.0.0-rc.33",
        "skill.anti-goodhart-verification": "3.7.0-rc.7",
        "skill.design-anti-goodhart": "1.0.0-rc.20",
        "skill.html-ppt": "1.0.0-rc.22",
        "tool.awf-repository-verifier": "1.0.0-rc.2",
    },
    "awf/workflows/adaptive-interactive-tutor/releases/1.0.0-rc.34/versions.lock": {
        "skill.adaptive-interactive-tutor": "1.0.0-rc.34",
        "skill.anti-goodhart-verification": "3.7.0-rc.7",
        "skill.design-anti-goodhart": "1.0.0-rc.21",
        "skill.html-ppt": "1.0.0-rc.23",
        "tool.awf-repository-verifier": "1.0.0-rc.2",
    },
    "awf/workflows/adaptive-interactive-tutor/releases/1.0.0-rc.35/versions.lock": {
        "skill.adaptive-interactive-tutor": "1.0.0-rc.35",
        "skill.anti-goodhart-verification": "3.7.0-rc.7",
        "skill.design-anti-goodhart": "1.0.0-rc.22",
        "skill.html-ppt": "1.0.0-rc.24",
        "tool.awf-repository-verifier": "1.0.0-rc.2",
    },
    "awf/workflows/adaptive-interactive-tutor/releases/1.0.0-rc.36/versions.lock": {
        "skill.adaptive-interactive-tutor": "1.0.0-rc.36",
        "skill.anti-goodhart-verification": "3.7.0-rc.7",
        "skill.design-anti-goodhart": "1.0.0-rc.23",
        "skill.html-ppt": "1.0.0-rc.25",
        "tool.awf-repository-verifier": "1.0.0-rc.2",
    },
    "awf/workflows/adaptive-interactive-tutor/releases/1.0.0-rc.37/versions.lock": {
        "skill.adaptive-interactive-tutor": "1.0.0-rc.37",
        "skill.anti-goodhart-verification": "3.7.0-rc.7",
        "skill.design-anti-goodhart": "1.0.0-rc.24",
        "skill.html-ppt": "1.0.0-rc.26",
        "tool.awf-repository-verifier": "1.0.0-rc.2",
    },
    "awf/workflows/scientific-report-authoring/releases/1.0.0-rc.13/versions.lock": {
        "skill.build-scientific-docx": "1.0.0-rc.12",
        "skill.edit-scientific-article": "1.0.0-rc.10",
    },
    "awf/workflows/editable-figure-pptx/releases/1.0.0-rc.2/versions.lock": {
        "skill.build-editable-figure-pptx": "1.0.0-rc.2",
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

design_dir = ROOT / "awf/components/skills/design-anti-goodhart/releases/1.0.0-rc.24/source"
design_script = design_dir / "scripts/awf_design_anti_goodhart_gates.py"
design_ev = design_dir / "design_tests/test_evidence.py"
public_route = ROOT / "awf/workflows/design-anti-goodhart/releases/1.0.0-rc.24/source/test_public_route.py"
html_dir = ROOT / "awf/components/skills/html-ppt/releases/1.0.0-rc.26/source"
html_ppt_script = html_dir / "scripts/audit_single_slide_step.py"
guard_script = ROOT / "awf/components/skills/anti-goodhart-verification/releases/3.7.0-rc.8/source/scripts/awf_universal_anti_goodhart_gates.py"

for label, cmd in [
    ("DesignAG 18-Gate self-test", [sys.executable, "-B", str(design_script), "--self-test"]),
    ("DesignAG recursive self-hosting audit", [sys.executable, "-B", str(design_script), "--audit-self"]),
    ("DesignAG adversarial evidence suite", [sys.executable, "-B", str(design_ev)]),
    ("DesignAG + HTML-PPT public route verification", [sys.executable, "-B", str(public_route)]),
    ("HTML-PPT Tri-Mode 23-Check self-test", [sys.executable, "-B", str(html_ppt_script), "--self-test"]),
    ("HTML-PPT concrete system semantics test", [sys.executable, "-B", str(html_dir / "tests/test_concrete_system_semantics.py")]),
    ("HTML-PPT concrete title language test", [sys.executable, "-B", str(html_dir / "tests/test_concrete_title_language.py")]),
    ("AWF Guard 14-Slot x 74-Subcheck self-test", [sys.executable, "-B", str(guard_script), "--self-test"]),
    ("AWF Guard recursive self-hosting audit", [sys.executable, "-B", str(guard_script), "--audit-self"]),
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
    "AWF DesignAG (18 gates + Canvas-vs-Dialogue Anti-Dilution + 3-Step Wittgenstein/7-Element/Teach-on-Miss + Pre-Background Paper-Recipe Leak Guard & Opening Rung-1 Macro-Stakes HTML Grounding + Outsider Anti-Collusion Blind Reader + 2x Large Typography >=32px/>=42px/>=56px + <=260-Char Low-Density Budget + Lossless Multi-Slide Split & Clickable Detail Popovers + Beyond-PDF Background Bridge + Zero Slide-Count MCQ + Universal Onion Bus) + AWF HTML-PPT (23 checks) + AWF SciWord + AWF FigPPT + AWF Guard (14 slots x 74 sub-checks + recursive self-audit) + AWF Tutor V16 closure verified"
)
