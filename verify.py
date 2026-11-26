#!/usr/bin/env python3
"""Standalone integrity and self-test verifier for AWF Anti-Goodhart + HTML-PPT + DesignAG + Tutor Suite."""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def _has_full_formal_toolchain() -> bool:
    for mod in ("pint", "z3", "flint", "hypothesis", "sympy", "rdkit"):
        if importlib.util.find_spec(mod) is None:
            return False
    has_lean = Path("/home/software/anaconda3/bin/lean").is_file() or shutil.which("lean") is not None
    has_kyx = (
        (Path("/home/software/openjdk-21/bin/java").is_file() and Path("/home/software/keymaerax/keymaerax.jar").is_file())
        or shutil.which("keymaerax") is not None
    )
    return bool(has_lean and has_kyx)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-formal-provers", action="store_true", help="Require Lean 4 + KeYmaera X + formal Python stack for Guard 3.9.0-rc.1 --self-test")
    args = parser.parse_args()

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
    "awf/workflows/adaptive-interactive-tutor/releases/1.0.0-rc.26/versions.lock": {
        "skill.adaptive-interactive-tutor": "1.0.0-rc.26",
        "skill.anti-goodhart-verification": "3.7.0-rc.7",
        "skill.design-anti-goodhart": "1.0.0-rc.13",
        "skill.html-ppt": "1.0.0-rc.15",
        "tool.awf-repository-verifier": "1.0.0-rc.2"
    },
    "awf/workflows/adaptive-interactive-tutor/releases/1.0.0-rc.27/versions.lock": {
        "skill.adaptive-interactive-tutor": "1.0.0-rc.27",
        "skill.anti-goodhart-verification": "3.7.0-rc.7",
        "skill.design-anti-goodhart": "1.0.0-rc.14",
        "skill.html-ppt": "1.0.0-rc.16",
        "tool.awf-repository-verifier": "1.0.0-rc.2"
    },
    "awf/workflows/adaptive-interactive-tutor/releases/1.0.0-rc.28/versions.lock": {
        "skill.adaptive-interactive-tutor": "1.0.0-rc.28",
        "skill.anti-goodhart-verification": "3.7.0-rc.7",
        "skill.design-anti-goodhart": "1.0.0-rc.15",
        "skill.html-ppt": "1.0.0-rc.17",
        "tool.awf-repository-verifier": "1.0.0-rc.2"
    },
    "awf/workflows/adaptive-interactive-tutor/releases/1.0.0-rc.29/versions.lock": {
        "skill.adaptive-interactive-tutor": "1.0.0-rc.29",
        "skill.anti-goodhart-verification": "3.7.0-rc.7",
        "skill.design-anti-goodhart": "1.0.0-rc.16",
        "skill.html-ppt": "1.0.0-rc.18",
        "tool.awf-repository-verifier": "1.0.0-rc.2"
    },
    "awf/workflows/adaptive-interactive-tutor/releases/1.0.0-rc.30/versions.lock": {
        "skill.adaptive-interactive-tutor": "1.0.0-rc.30",
        "skill.anti-goodhart-verification": "3.7.0-rc.7",
        "skill.design-anti-goodhart": "1.0.0-rc.17",
        "skill.html-ppt": "1.0.0-rc.19",
        "tool.awf-repository-verifier": "1.0.0-rc.2"
    },
    "awf/workflows/adaptive-interactive-tutor/releases/1.0.0-rc.31/versions.lock": {
        "skill.adaptive-interactive-tutor": "1.0.0-rc.31",
        "skill.anti-goodhart-verification": "3.7.0-rc.7",
        "skill.design-anti-goodhart": "1.0.0-rc.18",
        "skill.html-ppt": "1.0.0-rc.20",
        "tool.awf-repository-verifier": "1.0.0-rc.2"
    },
    "awf/workflows/adaptive-interactive-tutor/releases/1.0.0-rc.32/versions.lock": {
        "skill.adaptive-interactive-tutor": "1.0.0-rc.32",
        "skill.anti-goodhart-verification": "3.7.0-rc.7",
        "skill.design-anti-goodhart": "1.0.0-rc.19",
        "skill.html-ppt": "1.0.0-rc.21",
        "tool.awf-repository-verifier": "1.0.0-rc.2"
    },
    "awf/workflows/adaptive-interactive-tutor/releases/1.0.0-rc.33/versions.lock": {
        "skill.adaptive-interactive-tutor": "1.0.0-rc.33",
        "skill.anti-goodhart-verification": "3.7.0-rc.7",
        "skill.design-anti-goodhart": "1.0.0-rc.20",
        "skill.html-ppt": "1.0.0-rc.22",
        "tool.awf-repository-verifier": "1.0.0-rc.2"
    },
    "awf/workflows/adaptive-interactive-tutor/releases/1.0.0-rc.34/versions.lock": {
        "skill.adaptive-interactive-tutor": "1.0.0-rc.34",
        "skill.anti-goodhart-verification": "3.7.0-rc.7",
        "skill.design-anti-goodhart": "1.0.0-rc.21",
        "skill.html-ppt": "1.0.0-rc.23",
        "tool.awf-repository-verifier": "1.0.0-rc.2"
    },
    "awf/workflows/adaptive-interactive-tutor/releases/1.0.0-rc.35/versions.lock": {
        "skill.adaptive-interactive-tutor": "1.0.0-rc.35",
        "skill.anti-goodhart-verification": "3.7.0-rc.7",
        "skill.design-anti-goodhart": "1.0.0-rc.22",
        "skill.html-ppt": "1.0.0-rc.24",
        "tool.awf-repository-verifier": "1.0.0-rc.2"
    },
    "awf/workflows/adaptive-interactive-tutor/releases/1.0.0-rc.36/versions.lock": {
        "skill.adaptive-interactive-tutor": "1.0.0-rc.36",
        "skill.anti-goodhart-verification": "3.7.0-rc.7",
        "skill.design-anti-goodhart": "1.0.0-rc.23",
        "skill.html-ppt": "1.0.0-rc.25",
        "tool.awf-repository-verifier": "1.0.0-rc.2"
    },
    "awf/workflows/adaptive-interactive-tutor/releases/1.0.0-rc.37/versions.lock": {
        "skill.adaptive-interactive-tutor": "1.0.0-rc.37",
        "skill.anti-goodhart-verification": "3.7.0-rc.7",
        "skill.design-anti-goodhart": "1.0.0-rc.24",
        "skill.html-ppt": "1.0.0-rc.26",
        "tool.awf-repository-verifier": "1.0.0-rc.2"
    },
    "awf/workflows/adaptive-interactive-tutor/releases/1.0.0-rc.38/versions.lock": {
        "skill.adaptive-interactive-tutor": "1.0.0-rc.38",
        "skill.anti-goodhart-verification": "3.7.0-rc.7",
        "skill.design-anti-goodhart": "1.0.0-rc.25",
        "skill.html-ppt": "1.0.0-rc.27",
        "tool.awf-repository-verifier": "1.0.0-rc.2"
    },
    "awf/workflows/adaptive-interactive-tutor/releases/1.0.0-rc.39/versions.lock": {
        "skill.adaptive-interactive-tutor": "1.0.0-rc.39",
        "skill.anti-goodhart-verification": "3.8.0-rc.1",
        "skill.design-anti-goodhart": "1.0.0-rc.25",
        "skill.html-ppt": "1.0.0-rc.27",
        "tool.awf-repository-verifier": "1.0.0-rc.4"
    },
    "awf/workflows/adaptive-interactive-tutor/releases/1.0.0-rc.40/versions.lock": {
        "skill.adaptive-interactive-tutor": "1.0.0-rc.40",
        "skill.anti-goodhart-verification": "3.8.0-rc.1",
        "skill.design-anti-goodhart": "1.0.0-rc.26",
        "skill.html-ppt": "1.0.0-rc.28",
        "tool.awf-repository-verifier": "1.0.0-rc.4"
    },
    "awf/workflows/anti-goodhart-verification/releases/3.7.0-rc.8/versions.lock": {
        "skill.anti-goodhart-verification": "3.7.0-rc.8",
        "skill.manage-agent-workflows": "1.0.2",
        "tool.awf-repository-verifier": "1.0.0-rc.3"
    },
    "awf/workflows/anti-goodhart-verification/releases/3.8.0-rc.1/versions.lock": {
        "skill.anti-goodhart-verification": "3.8.0-rc.1",
        "skill.manage-agent-workflows": "1.0.2",
        "tool.awf-repository-verifier": "1.0.0-rc.4"
    },
    "awf/workflows/anti-goodhart-verification/releases/3.9.0-rc.1/versions.lock": {
        "skill.anti-goodhart-verification": "3.9.0-rc.1",
        "skill.manage-agent-workflows": "1.0.2",
        "tool.awf-repository-verifier": "1.0.0-rc.5"
    },
    "awf/workflows/design-anti-goodhart/releases/1.0.0-rc.13/versions.lock": {
        "skill.design-anti-goodhart": "1.0.0-rc.13",
        "skill.anti-goodhart-verification": "3.7.0-rc.7",
        "tool.awf-repository-verifier": "1.0.0-rc.2"
    },
    "awf/workflows/design-anti-goodhart/releases/1.0.0-rc.14/versions.lock": {
        "skill.design-anti-goodhart": "1.0.0-rc.14",
        "skill.anti-goodhart-verification": "3.7.0-rc.7",
        "tool.awf-repository-verifier": "1.0.0-rc.2"
    },
    "awf/workflows/design-anti-goodhart/releases/1.0.0-rc.15/versions.lock": {
        "skill.design-anti-goodhart": "1.0.0-rc.15",
        "skill.anti-goodhart-verification": "3.7.0-rc.7",
        "tool.awf-repository-verifier": "1.0.0-rc.2"
    },
    "awf/workflows/design-anti-goodhart/releases/1.0.0-rc.16/versions.lock": {
        "skill.design-anti-goodhart": "1.0.0-rc.16",
        "skill.anti-goodhart-verification": "3.7.0-rc.7",
        "tool.awf-repository-verifier": "1.0.0-rc.2"
    },
    "awf/workflows/design-anti-goodhart/releases/1.0.0-rc.17/versions.lock": {
        "skill.design-anti-goodhart": "1.0.0-rc.17",
        "skill.anti-goodhart-verification": "3.7.0-rc.7",
        "tool.awf-repository-verifier": "1.0.0-rc.2"
    },
    "awf/workflows/design-anti-goodhart/releases/1.0.0-rc.18/versions.lock": {
        "skill.design-anti-goodhart": "1.0.0-rc.18",
        "skill.anti-goodhart-verification": "3.7.0-rc.7",
        "tool.awf-repository-verifier": "1.0.0-rc.2"
    },
    "awf/workflows/design-anti-goodhart/releases/1.0.0-rc.19/versions.lock": {
        "skill.design-anti-goodhart": "1.0.0-rc.19",
        "skill.anti-goodhart-verification": "3.7.0-rc.7",
        "tool.awf-repository-verifier": "1.0.0-rc.2"
    },
    "awf/workflows/design-anti-goodhart/releases/1.0.0-rc.20/versions.lock": {
        "skill.design-anti-goodhart": "1.0.0-rc.20",
        "skill.anti-goodhart-verification": "3.7.0-rc.7",
        "tool.awf-repository-verifier": "1.0.0-rc.2"
    },
    "awf/workflows/design-anti-goodhart/releases/1.0.0-rc.21/versions.lock": {
        "skill.design-anti-goodhart": "1.0.0-rc.21",
        "skill.anti-goodhart-verification": "3.7.0-rc.7",
        "tool.awf-repository-verifier": "1.0.0-rc.2"
    },
    "awf/workflows/design-anti-goodhart/releases/1.0.0-rc.22/versions.lock": {
        "skill.design-anti-goodhart": "1.0.0-rc.22",
        "skill.anti-goodhart-verification": "3.7.0-rc.7",
        "tool.awf-repository-verifier": "1.0.0-rc.2"
    },
    "awf/workflows/design-anti-goodhart/releases/1.0.0-rc.23/versions.lock": {
        "skill.design-anti-goodhart": "1.0.0-rc.23",
        "skill.anti-goodhart-verification": "3.7.0-rc.7",
        "tool.awf-repository-verifier": "1.0.0-rc.2"
    },
    "awf/workflows/design-anti-goodhart/releases/1.0.0-rc.24/versions.lock": {
        "skill.design-anti-goodhart": "1.0.0-rc.24",
        "skill.anti-goodhart-verification": "3.7.0-rc.7",
        "tool.awf-repository-verifier": "1.0.0-rc.2"
    },
    "awf/workflows/design-anti-goodhart/releases/1.0.0-rc.25/versions.lock": {
        "skill.design-anti-goodhart": "1.0.0-rc.25",
        "skill.anti-goodhart-verification": "3.7.0-rc.7",
        "tool.awf-repository-verifier": "1.0.0-rc.2"
    },
    "awf/workflows/design-anti-goodhart/releases/1.0.0-rc.26/versions.lock": {
        "skill.design-anti-goodhart": "1.0.0-rc.26",
        "skill.anti-goodhart-verification": "3.8.0-rc.1",
        "tool.awf-repository-verifier": "1.0.0-rc.4"
    },
    "awf/workflows/editable-figure-pptx/releases/1.0.0-rc.2/versions.lock": {
        "skill.build-editable-figure-pptx": "1.0.0-rc.2"
    },
    "awf/workflows/html-ppt/releases/1.0.0-rc.12/versions.lock": {
        "skill.html-ppt": "1.0.0-rc.15",
        "skill.design-anti-goodhart": "1.0.0-rc.13",
        "skill.anti-goodhart-verification": "3.7.0-rc.7",
        "tool.awf-repository-verifier": "1.0.0-rc.2"
    },
    "awf/workflows/html-ppt/releases/1.0.0-rc.13/versions.lock": {
        "skill.html-ppt": "1.0.0-rc.16",
        "skill.design-anti-goodhart": "1.0.0-rc.14",
        "skill.anti-goodhart-verification": "3.7.0-rc.7",
        "tool.awf-repository-verifier": "1.0.0-rc.2"
    },
    "awf/workflows/html-ppt/releases/1.0.0-rc.14/versions.lock": {
        "skill.html-ppt": "1.0.0-rc.17",
        "skill.design-anti-goodhart": "1.0.0-rc.15",
        "skill.anti-goodhart-verification": "3.7.0-rc.7",
        "tool.awf-repository-verifier": "1.0.0-rc.2"
    },
    "awf/workflows/html-ppt/releases/1.0.0-rc.15/versions.lock": {
        "skill.html-ppt": "1.0.0-rc.18",
        "skill.design-anti-goodhart": "1.0.0-rc.16",
        "skill.anti-goodhart-verification": "3.7.0-rc.7",
        "tool.awf-repository-verifier": "1.0.0-rc.2"
    },
    "awf/workflows/html-ppt/releases/1.0.0-rc.16/versions.lock": {
        "skill.html-ppt": "1.0.0-rc.19",
        "skill.design-anti-goodhart": "1.0.0-rc.17",
        "skill.anti-goodhart-verification": "3.7.0-rc.7",
        "tool.awf-repository-verifier": "1.0.0-rc.2"
    },
    "awf/workflows/html-ppt/releases/1.0.0-rc.17/versions.lock": {
        "skill.html-ppt": "1.0.0-rc.20",
        "skill.design-anti-goodhart": "1.0.0-rc.18",
        "skill.anti-goodhart-verification": "3.7.0-rc.7",
        "tool.awf-repository-verifier": "1.0.0-rc.2"
    },
    "awf/workflows/html-ppt/releases/1.0.0-rc.18/versions.lock": {
        "skill.html-ppt": "1.0.0-rc.21",
        "skill.design-anti-goodhart": "1.0.0-rc.19",
        "skill.anti-goodhart-verification": "3.7.0-rc.7",
        "tool.awf-repository-verifier": "1.0.0-rc.2"
    },
    "awf/workflows/html-ppt/releases/1.0.0-rc.19/versions.lock": {
        "skill.html-ppt": "1.0.0-rc.22",
        "skill.design-anti-goodhart": "1.0.0-rc.20",
        "skill.anti-goodhart-verification": "3.7.0-rc.7",
        "tool.awf-repository-verifier": "1.0.0-rc.2"
    },
    "awf/workflows/html-ppt/releases/1.0.0-rc.20/versions.lock": {
        "skill.html-ppt": "1.0.0-rc.23",
        "skill.design-anti-goodhart": "1.0.0-rc.21",
        "skill.anti-goodhart-verification": "3.7.0-rc.7",
        "tool.awf-repository-verifier": "1.0.0-rc.2"
    },
    "awf/workflows/html-ppt/releases/1.0.0-rc.21/versions.lock": {
        "skill.html-ppt": "1.0.0-rc.24",
        "skill.design-anti-goodhart": "1.0.0-rc.22",
        "skill.anti-goodhart-verification": "3.7.0-rc.7",
        "tool.awf-repository-verifier": "1.0.0-rc.2"
    },
    "awf/workflows/html-ppt/releases/1.0.0-rc.22/versions.lock": {
        "skill.html-ppt": "1.0.0-rc.25",
        "skill.design-anti-goodhart": "1.0.0-rc.23",
        "skill.anti-goodhart-verification": "3.7.0-rc.7",
        "tool.awf-repository-verifier": "1.0.0-rc.2"
    },
    "awf/workflows/html-ppt/releases/1.0.0-rc.23/versions.lock": {
        "skill.html-ppt": "1.0.0-rc.26",
        "skill.design-anti-goodhart": "1.0.0-rc.24",
        "skill.anti-goodhart-verification": "3.7.0-rc.7",
        "tool.awf-repository-verifier": "1.0.0-rc.2"
    },
    "awf/workflows/html-ppt/releases/1.0.0-rc.24/versions.lock": {
        "skill.html-ppt": "1.0.0-rc.27",
        "skill.design-anti-goodhart": "1.0.0-rc.25",
        "skill.anti-goodhart-verification": "3.7.0-rc.7",
        "tool.awf-repository-verifier": "1.0.0-rc.2"
    },
    "awf/workflows/html-ppt/releases/1.0.0-rc.25/versions.lock": {
        "skill.html-ppt": "1.0.0-rc.28",
        "skill.design-anti-goodhart": "1.0.0-rc.26",
        "skill.anti-goodhart-verification": "3.8.0-rc.1",
        "tool.awf-repository-verifier": "1.0.0-rc.4"
    },
    "awf/workflows/scientific-report-authoring/releases/1.0.0-rc.13/versions.lock": {
        "skill.build-scientific-docx": "1.0.0-rc.12",
        "skill.edit-scientific-article": "1.0.0-rc.10"
    }
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
        if path.name not in {"verify.py", "build_public_distribution.py"} and path.stat().st_size < 5_000_000:
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                text = ""
            if re.search(r"BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY|gh[pousr]_[A-Za-z0-9]{20,}", text):
                errors.append(f"credential pattern: {path.relative_to(ROOT)}")

    design_dir = ROOT / "awf/components/skills/design-anti-goodhart/releases/1.0.0-rc.26/source"
    design_script = design_dir / "scripts/awf_design_anti_goodhart_gates.py"
    design_ev = design_dir / "design_tests/test_evidence.py"
    public_route = ROOT / "awf/workflows/design-anti-goodhart/releases/1.0.0-rc.26/source/test_public_route.py"
    html_dir = ROOT / "awf/components/skills/html-ppt/releases/1.0.0-rc.28/source"
    html_ppt_script = html_dir / "scripts/audit_single_slide_step.py"
    guard38_script = ROOT / "awf/components/skills/anti-goodhart-verification/releases/3.8.0-rc.1/source/scripts/awf_universal_anti_goodhart_gates.py"
    guard39_script = ROOT / "awf/components/skills/anti-goodhart-verification/releases/3.9.0-rc.1/source/scripts/awf_universal_anti_goodhart_gates.py"

    suites = [
        ("DesignAG 1.0.0-rc.26 18-Gate self-test", [sys.executable, "-B", str(design_script), "--self-test"]),
        ("DesignAG 1.0.0-rc.26 recursive self-hosting audit", [sys.executable, "-B", str(design_script), "--audit-self"]),
        ("DesignAG 1.0.0-rc.26 adversarial evidence suite", [sys.executable, "-B", str(design_ev)]),
        ("DesignAG 1.0.0-rc.26 + HTML-PPT 1.0.0-rc.28 public route", [sys.executable, "-B", str(public_route)]),
        ("HTML-PPT 1.0.0-rc.28 Tri-Mode 24-Check self-test", [sys.executable, "-B", str(html_ppt_script), "--self-test"]),
    ]
    for t_py in sorted((html_dir / "tests").glob("test_*.py")):
        suites.append((f"HTML-PPT test {t_py.name}", [sys.executable, "-B", str(t_py)]))
    suites.extend([
        ("AWF Guard 3.8.0-rc.1 14-Slot x 80-Subcheck self-test", [sys.executable, "-B", str(guard38_script), "--self-test"]),
        ("AWF Guard 3.8.0-rc.1 recursive self-hosting audit", [sys.executable, "-B", str(guard38_script), "--audit-self"]),
        ("AWF Guard 3.9.0-rc.1 recursive self-hosting audit", [sys.executable, "-B", str(guard39_script), "--audit-self"]),
    ])

    has_formal = _has_full_formal_toolchain()
    if args.require_formal_provers and not has_formal:
        errors.append("Formal toolchain (Pint/Z3/RDKit/Arb/Hypothesis/Lean 4/KeYmaera X) missing under --require-formal-provers")
    elif has_formal:
        suites.append(("AWF Guard 3.9.0-rc.1 14-Slot x 86-Subcheck formal self-test", [sys.executable, "-B", str(guard39_script), "--self-test"]))

    for label, cmd in suites:
        proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        if proc.returncode != 0:
            errors.append(f"{label} failed (rc={proc.returncode}): {(proc.stderr or proc.stdout)[-600:]}")

    if errors:
        print("FAIL")
        print("\n".join(errors))
        return 1

    formal_note = "86-subcheck formal provers verified" if has_formal else "80-subcheck pure-NumPy + 3.9 AST dogfood verified (external Lean4/KeYmaeraX optional)"
    print(
        f"PASS: {len(manifest['files'])} files verified; "
        f"AWF HTML-PPT 1.0.0-rc.28 + AWF DesignAG 1.0.0-rc.26 + AWF Tutor 1.0.0-rc.40 + AWF Guard 3.9.0-rc.1 ({formal_note}) + SciWord + FigPPT closure verified"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
