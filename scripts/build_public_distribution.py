#!/usr/bin/env python3
"""
Co-located reproducible builder for the public GitHub distribution (`anti-goodhart-awf`):
- `skill.html-ppt@1.0.0-rc.28` (`workflow html-ppt@1.0.0-rc.25`)
- `skill.design-anti-goodhart@1.0.0-rc.26` (`workflow design-anti-goodhart@1.0.0-rc.26`)
- `skill.adaptive-interactive-tutor@1.0.0-rc.40` (`workflow adaptive-interactive-tutor@1.0.0-rc.40`)
- `skill.anti-goodhart-verification@3.9.0-rc.1` (`workflow anti-goodhart-verification@3.9.0-rc.1`, plus `3.8.0-rc.1`, `3.7.0-rc.8`, `3.7.0-rc.7`)
- Preserves existing `scientific-report-authoring@1.0.0-rc.13` (`SciWord`) and `editable-figure-pptx@1.0.0-rc.2` (`FigPPT`) closures and all previously published historical releases.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Tuple

OUT = Path(__file__).resolve().parents[1]
AWF = Path("/home/zc/agent_workflows")
if not AWF.exists():
    AWF = Path(r"Z:\agent_workflows")

WORKFLOWS: Dict[str, str] = {
    "design-anti-goodhart": "1.0.0-rc.26",
    "anti-goodhart-verification": "3.9.0-rc.1",
    "adaptive-interactive-tutor": "1.0.0-rc.40",
    "html-ppt": "1.0.0-rc.25",
    "scientific-report-authoring": "1.0.0-rc.13",
    "editable-figure-pptx": "1.0.0-rc.2",
}

LOCKED_SKILLS: Dict[str, str] = {
    "design-anti-goodhart": "1.0.0-rc.26",
    "anti-goodhart-verification": "3.9.0-rc.1",
    "adaptive-interactive-tutor": "1.0.0-rc.40",
    "html-ppt": "1.0.0-rc.28",
    "edit-scientific-article": "1.0.0-rc.10",
    "build-scientific-docx": "1.0.0-rc.12",
    "build-editable-figure-pptx": "1.0.0-rc.2",
}

SKILL_RELEASE_SERIES: Dict[str, Tuple[str, ...]] = {
    "design-anti-goodhart": tuple(f"1.0.0-rc.{i}" for i in range(13, 27)),
    "html-ppt": tuple(f"1.0.0-rc.{i}" for i in range(15, 29)),
    "adaptive-interactive-tutor": tuple(f"1.0.0-rc.{i}" for i in range(26, 41)),
    "anti-goodhart-verification": ("3.7.0-rc.7", "3.7.0-rc.8", "3.8.0-rc.1", "3.9.0-rc.1"),
}

WORKFLOW_RELEASE_SERIES: Dict[str, Tuple[str, ...]] = {
    "design-anti-goodhart": tuple(f"1.0.0-rc.{i}" for i in range(13, 27)),
    "html-ppt": tuple(f"1.0.0-rc.{i}" for i in range(12, 26)),
    "adaptive-interactive-tutor": tuple(f"1.0.0-rc.{i}" for i in range(26, 41)),
    "anti-goodhart-verification": ("3.7.0-rc.8", "3.8.0-rc.1", "3.9.0-rc.1"),
}


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def copy_clean_dir(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(
        src,
        dst,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache"),
    )


def sync_skill_series(name: str, releases: Tuple[str, ...]) -> None:
    descriptor = load(AWF / f"components/skills/{name}/component.yaml")
    keep = {}
    for rel in releases:
        if rel not in descriptor["releases"]:
            raise KeyError(f"Missing skill release {name}@{rel} in AWF component.yaml")
        keep[rel] = descriptor["releases"][rel]
        copy_clean_dir(
            AWF / f"components/skills/{name}/releases/{rel}",
            OUT / f"awf/components/skills/{name}/releases/{rel}",
        )
    descriptor["releases"] = keep
    save(OUT / f"awf/components/skills/{name}/component.yaml", descriptor)


def sync_workflow_series(
    wf_id: str,
    latest_rel: str,
    releases: Tuple[str, ...],
    registry: Dict[str, Any],
) -> Dict[str, Any]:
    wf_entry = next(item for item in registry["workflows"] if item["id"] == wf_id)
    keep_rels = {}
    for rel in releases:
        if rel not in wf_entry["releases"]:
            raise KeyError(f"Missing workflow release {wf_id}@{rel} in AWF registry.yaml")
        keep_rels[rel] = wf_entry["releases"][rel]
        copy_clean_dir(
            AWF / f"workflows/{wf_id}/releases/{rel}",
            OUT / f"awf/workflows/{wf_id}/releases/{rel}",
        )
    latest_meta = wf_entry["releases"][latest_rel]
    fragment = {k: v for k, v in wf_entry.items() if k != "releases"}
    fragment.update(
        descriptor=latest_meta["descriptor"],
        descriptor_sha256=latest_meta["descriptor_sha256"],
        lock=latest_meta["lock"],
        lock_sha256=latest_meta["lock_sha256"],
        releases=keep_rels,
    )
    return fragment


def build_readme() -> str:
    return """# AWF Anti-Goodhart Universal Input-Onion-Output Suite (`AWF HTML-PPT` + `AWF DesignAG` + `AWF Guard` + `AWF Tutor` + `AWF SciWord` + `AWF FigPPT`)

Public, portable distribution of the **Agent Workflow Foundry (AWF)** 9-Role Universal Input-Background-Understanding-Output Onion Control Bus (`BackgroundSynthesizer + EvidenceIngest` $\\to$ `AWF Tutor / Onion Peeling + DevilReviewer` $\\to$ `OmniArtifactHub` [driving `AWF HTML-PPT`, `AWF SciWord`, and `AWF FigPPT`] $\\to$ `AWF DesignAG` 18-Gate + `AWF Guard` 86-Subcheck Formal & Certified Verification):

1. **`AWF HTML-PPT V3` (`html-ppt@1.0.0-rc.25` / `skill.html-ppt@1.0.0-rc.28`)**:
   - **Universal 5-Scale Physical-Entity Visual Fidelity (`RDKit` ACS 1996 Vector / 2.5D Shading / 4-Axis Orthogonal Image Exploration + Critique-Guided Gen-1+ Evolution) + Two-Stage Text-Masked Blind Object Recognition (`D5` & `D18`)**;
   - **2x Large Typography (`>=32px` inline `<svg>` & visible HTML, `>=42px` `1920x1080` card body, `>=56px` slide title, `1` visible `<p>` per card) & `<=260`-Char Low-Density Budget**;
   - **Lossless Multi-Slide Split (`SPLIT_SLIDE` + `.topo-breadcrumb`) & Clickable Detail Popovers (`CLICKABLE_POPOVER` + `.detail-trigger[data-detail-id]` backed by verified `<template>` modals & `lossless_split_and_popover_ledger`)**;
   - **Beyond-PDF 4-Rung Domain Background Synthesis (`domain_background_bridge`), Pre-Background Paper-Recipe Leak Guard & Opening Rung-1 Macro-Stakes Grounding (`D13`), Unread-PDF Value Triage (`ai_value_triage`), Unconditional Zero Slide-Count MCQ Law, Outsider Anti-Collusion Blind Reader (`--verify-blind-reader`), and Tri-Mode 1-Slide-Per-Step Enforcer (`audit_single_slide_step.py`, 24 checks)**.
2. **`AWF DesignAG` (`design-anti-goodhart@1.0.0-rc.26` / `skill.design-anti-goodhart@1.0.0-rc.26`)**:
   - **18 Automated Design & Pedagogical Gates (`D1`–`D18`)** and **7 Redlines (`R1`–`R7`)**, Dual-Rubric Quantitative Scorer, Ed25519 Signed Multimodal Review Verification, Canvas-vs-Dialogue Anti-Dilution, 3-Step Wittgenstein Ladder (`Bridge -> Deconstruct -> Replace`), `Teach-on-Miss` + Isomorphic Re-Grill Closure, Intra-Slide Semantic Tree & Bottom-Ballast Ban, and Universal I/O Onion Control Bus.
3. **`AWF Guard` (`anti-goodhart-verification@3.9.0-rc.1` / `skill.anti-goodhart-verification@3.9.0-rc.1`, plus pure-NumPy `3.8.0-rc.1`)**:
   - **14 Orthogonal Universal Slots $\\times$ 86 Automated Anti-Goodhart, Formal Proof & Certified Scientific Computing Sub-Checks (`G1`–`G7`) + 76-Function Force-PASS Mutation Adequacy**:
     - **v3.9 Formal & Certified Verification Pack (`G3o`, `G5v`, `G1g`, `G3n`, `G2c`, `G5w`)**: `Pint` atomic/SI dimensional homogeneity & scale-factor contract guard (`G3o`), `Z3 + SymPy + RDKit` exact stoichiometry, spin parity, Wegscheider cycle-closure SMT & Feinberg CRNT deficiency gate (`G5v`), `Python-FLINT Arb` 128-bit ball-arithmetic certified enclosures (`G1g`), `Hypothesis` deterministic $SE(3)\\times S_N$ & singular-angle shrinking (`G3n`), `Lean 4 + SymPy` theorem proof, axiom-whitelist & mandatory `∃` non-vacuous inhabitation witness (`G2c`), and `KeYmaera X` differential dynamic logic ($d\\mathcal{L}$) ODE safety with `Z3` precondition-SAT check (`G5w`);
     - **v3.8 Model-Physics Red-Team & Outer-Glue Pack (`G4d`, `G3m`, `G1f`, `G5u`, `G6q`, `G7j`)**: Dual-Entry `pre_code` / `post_hoc_audit` (`--audit-existing`) docstring-stripped AST physics card triangulation, outer-glue `@scientific_atom` single-source lock, dynamic feature variance canary, sub-fragment spin/slip sensitivity, periodic unit-cell cyclic shift, and cross-table physical inequality bounds.
4. **`AWF Tutor V16` (`adaptive-interactive-tutor@1.0.0-rc.40` / `skill.adaptive-interactive-tutor@1.0.0-rc.40`)**:
   - Master-level interactive teaching, Scale-Adaptive Fractal Curriculum (`Chapter -> Station -> 3-Gate Micro-Loop`), Dual-Entry Independent Physics Red-Team Protocol, and Two-Level Macro-to-Micro Tri-Mode Co-Design (`TDD`, `GRILL`, `AUTONOMOUS_DUAL_EVOLVE`).
5. **`AWF SciWord` (`scientific-report-authoring@1.0.0-rc.13`) & `AWF FigPPT` (`editable-figure-pptx@1.0.0-rc.2`)**:
   - Native-OMML scientific Word (`.docx`) authoring (`SCI_WORD`) and 100%-editable OpenXML scientific composite PowerPoint (`.pptx`) decomposition (`FIG_PPTX`).

## Included Locked Closure

- `skill.html-ppt@1.0.0-rc.28` (`awf/components/skills/html-ppt/releases/1.0.0-rc.28/source/`, plus immutable `1.0.0-rc.15`–`1.0.0-rc.27`)
- `skill.design-anti-goodhart@1.0.0-rc.26` (`awf/components/skills/design-anti-goodhart/releases/1.0.0-rc.26/source/`, plus immutable `1.0.0-rc.13`–`1.0.0-rc.25`)
- `skill.adaptive-interactive-tutor@1.0.0-rc.40` (`awf/components/skills/adaptive-interactive-tutor/releases/1.0.0-rc.40/source/`, plus immutable `1.0.0-rc.26`–`1.0.0-rc.39`)
- `skill.anti-goodhart-verification@3.9.0-rc.1` (`awf/components/skills/anti-goodhart-verification/releases/3.9.0-rc.1/source/`, plus `3.8.0-rc.1`, `3.7.0-rc.8`, `3.7.0-rc.7`)
- `skill.edit-scientific-article@1.0.0-rc.10`, `skill.build-scientific-docx@1.0.0-rc.12`, `skill.build-editable-figure-pptx@1.0.0-rc.2`
- Co-located reproducible builder at `scripts/build_public_distribution.py`, standalone verifier at `verify.py`, and mergeable registry fragment at `awf/registry.fragment.json`

## Quick Verification

```bash
# 1. Verify full repository manifest, SHA256 hashes, locks, AST syntax, zero-secret rules, and run all self-tests & self-audits
python -B verify.py

# 2. Run AWF HTML-PPT V3 (1.0.0-rc.28, 24 checks) self-test directly
python -B awf/components/skills/html-ppt/releases/1.0.0-rc.28/source/scripts/audit_single_slide_step.py --self-test

# 3. Run AWF DesignAG (1.0.0-rc.26, 18 gates) self-test & self-hosting audit directly
python -B awf/components/skills/design-anti-goodhart/releases/1.0.0-rc.26/source/scripts/awf_design_anti_goodhart_gates.py --self-test
python -B awf/components/skills/design-anti-goodhart/releases/1.0.0-rc.26/source/scripts/awf_design_anti_goodhart_gates.py --audit-self

# 4. Run AWF Guard pure-NumPy 80-Subcheck (3.8.0-rc.1) & Formal/Certified 86-Subcheck (3.9.0-rc.1) self-tests & self-audits
python -B awf/components/skills/anti-goodhart-verification/releases/3.8.0-rc.1/source/scripts/awf_universal_anti_goodhart_gates.py --self-test
python -B awf/components/skills/anti-goodhart-verification/releases/3.9.0-rc.1/source/scripts/awf_universal_anti_goodhart_gates.py --audit-self
python -B awf/components/skills/anti-goodhart-verification/releases/3.9.0-rc.1/source/scripts/awf_universal_anti_goodhart_gates.py --self-test
```
"""


def build_verifier(expected_locks: Dict[str, Dict[str, str]]) -> str:
    locks_json = json.dumps(expected_locks, indent=4, ensure_ascii=False)
    return f'''#!/usr/bin/env python3
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
            errors.append(f"missing: {{rel}}")
            continue
        data = path.read_bytes()
        if len(data) != meta["bytes"]:
            errors.append(f"size mismatch: {{rel}}")
        if hashlib.sha256(data).hexdigest() != meta["sha256"]:
            errors.append(f"hash mismatch: {{rel}}")

    known = set(manifest["files"]) | {{"MANIFEST.json"}}
    actual = {{
        p.relative_to(ROOT).as_posix()
        for p in ROOT.rglob("*")
        if p.is_file() and ".git" not in p.parts and "dist" not in p.parts and "__pycache__" not in p.parts
    }}
    for rel in sorted(actual - known):
        errors.append(f"unlisted file: {{rel}}")

    expected_locks = {locks_json}

    for lock_rel, exp_comps in expected_locks.items():
        lp = ROOT / lock_rel
        if not lp.is_file():
            errors.append(f"missing lock: {{lock_rel}}")
        else:
            lock_doc = json.loads(lp.read_text(encoding="utf-8"))
            if lock_doc.get("components") != exp_comps:
                errors.append(f"lock mismatch in {{lock_rel}}: {{lock_doc.get('components')}}")

    for path in ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts or "dist" in path.parts or "__pycache__" in path.parts:
            continue
        if path.suffix == ".py":
            try:
                ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            except (SyntaxError, UnicodeDecodeError) as exc:
                errors.append(f"python syntax: {{path.relative_to(ROOT)}}: {{exc}}")
        if path.suffix.lower() == ".json" or path.name in {{"component.yaml", "workflow.yaml", "versions.lock"}}:
            try:
                json.loads(path.read_text(encoding="utf-8"))
            except Exception as exc:
                errors.append(f"json/yaml parse: {{path.relative_to(ROOT)}}: {{exc}}")
        if path.name not in {{"verify.py", "build_public_distribution.py"}} and path.stat().st_size < 5_000_000:
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                text = ""
            if re.search(r"BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY|gh[pousr]_[A-Za-z0-9]{{20,}}", text):
                errors.append(f"credential pattern: {{path.relative_to(ROOT)}}")

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
        suites.append((f"HTML-PPT test {{t_py.name}}", [sys.executable, "-B", str(t_py)]))
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
            errors.append(f"{{label}} failed (rc={{proc.returncode}}): {{(proc.stderr or proc.stdout)[-600:]}}")

    if errors:
        print("FAIL")
        print("\\n".join(errors))
        return 1

    formal_note = "86-subcheck formal provers verified" if has_formal else "80-subcheck pure-NumPy + 3.9 AST dogfood verified (external Lean4/KeYmaeraX optional)"
    print(
        f"PASS: {{len(manifest['files'])}} files verified; "
        f"AWF HTML-PPT 1.0.0-rc.28 + AWF DesignAG 1.0.0-rc.26 + AWF Tutor 1.0.0-rc.40 + AWF Guard 3.9.0-rc.1 ({{formal_note}}) + SciWord + FigPPT closure verified"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


def main() -> int:
    registry = load(AWF / "registry.yaml")

    # 1. Sync evolving skill series additively (preserving SciWord & FigPPT already present in OUT)
    for skill_name, rel_tuple in SKILL_RELEASE_SERIES.items():
        sync_skill_series(skill_name, rel_tuple)

    # 2. Sync evolving workflow series and assemble registry.fragment.json
    existing_frag = load(OUT / "awf/registry.fragment.json")
    preserved_wfs = {
        w["id"]: w for w in existing_frag.get("workflows", [])
        if w["id"] in {"scientific-report-authoring", "editable-figure-pptx"}
    }
    wf_fragments: List[Dict[str, Any]] = []
    for wf_id, latest_rel in WORKFLOWS.items():
        if wf_id in WORKFLOW_RELEASE_SERIES:
            wf_fragments.append(sync_workflow_series(wf_id, latest_rel, WORKFLOW_RELEASE_SERIES[wf_id], registry))
        else:
            wf_fragments.append(preserved_wfs[wf_id])

    comp_fragments = [
        {
            "descriptor": f"components/skills/{name}/component.yaml",
            "id": f"skill.{name}",
            "kind": "skill",
            "latest_release": rel,
        }
        for name, rel in LOCKED_SKILLS.items()
    ]
    save(
        OUT / "awf/registry.fragment.json",
        {
            "schema_version": 1,
            "components": comp_fragments,
            "workflows": wf_fragments,
        },
    )

    # 3. Collect all versions.lock files in awf/workflows/ for verify.py lock-pinning
    expected_locks: Dict[str, Dict[str, str]] = {}
    for lock_file in sorted((OUT / "awf/workflows").rglob("versions.lock")):
        rel_lock = lock_file.relative_to(OUT).as_posix()
        expected_locks[rel_lock] = load(lock_file)["components"]

    # 4. Write README.md and verify.py
    (OUT / "README.md").write_text(build_readme(), encoding="utf-8", newline="\n")
    (OUT / "verify.py").write_text(build_verifier(expected_locks), encoding="utf-8", newline="\n")

    # 5. Clean __pycache__ before hashing MANIFEST.json
    for cache_dir in list(OUT.rglob("__pycache__")):
        if cache_dir.is_dir():
            shutil.rmtree(cache_dir)

    files: Dict[str, Dict[str, Any]] = {}
    for path in sorted(
        p
        for p in OUT.rglob("*")
        if p.is_file()
        and ".git" not in p.parts
        and "dist" not in p.parts
        and "__pycache__" not in p.parts
        and p.name != "MANIFEST.json"
    ):
        relative = path.relative_to(OUT).as_posix()
        data = path.read_bytes()
        files[relative] = {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}

    save(
        OUT / "MANIFEST.json",
        {
            "schema_version": 1,
            "workflows": WORKFLOWS,
            "locked_skills": LOCKED_SKILLS,
            "files": files,
        },
    )

    # 6. Build fresh dist/ archive + sha256
    dist_dir = OUT / "dist"
    dist_dir.mkdir(exist_ok=True)
    for old_f in dist_dir.glob("*"):
        old_f.unlink()
    zip_name = (
        "anti-goodhart-awf-v3.9.0-rc.1-designag-v1.0.0-rc.26-"
        "htmlppt-v1.0.0-rc.28-tutor-v1.0.0-rc.40-sciword-figppt.zip"
    )
    zip_path = dist_dir / zip_name
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(
            p
            for p in OUT.rglob("*")
            if p.is_file() and ".git" not in p.parts and "dist" not in p.parts and "__pycache__" not in p.parts
        ):
            archive.write(path, Path("anti-goodhart-awf") / path.relative_to(OUT))
    digest = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    (dist_dir / f"{zip_name}.sha256").write_text(f"{digest}  {zip_name}\n", encoding="utf-8", newline="\n")

    print(
        json.dumps(
            {
                "status": "PASS",
                "files": len(files),
                "locks_verified": len(expected_locks),
                "zip": str(zip_path.relative_to(OUT)),
                "zip_bytes": zip_path.stat().st_size,
                "zip_sha256": digest,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
