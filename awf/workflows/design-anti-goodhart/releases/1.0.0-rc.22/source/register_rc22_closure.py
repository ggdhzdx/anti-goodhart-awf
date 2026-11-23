#!/usr/bin/env python3
"""Co-located release registration & manifest generator for DesignAG 1.0.0-rc.22, HTML-PPT 1.0.0-rc.24, and Tutor 1.0.0-rc.35."""
import copy
from pathlib import Path
from release_hashes import file_hash, read, tree_hash, write

ENG_SOURCE_DIR = Path(__file__).resolve().parent
AWF_ROOT = ENG_SOURCE_DIR.parents[4]
REPO_ROOT = AWF_ROOT.parent

OBSERVED_DATE = "2026-11-20"
PREV_DESIGN_REL = "1.0.0-rc.21"
PREV_HTML_SKILL_REL = "1.0.0-rc.23"
PREV_TUTOR_REL = "1.0.0-rc.34"

DESIGN_REL = "1.0.0-rc.22"
HTML_SKILL_REL = "1.0.0-rc.24"
HTML_WF_REL = "1.0.0-rc.21"
TUTOR_REL = "1.0.0-rc.35"

NEW_CAPABILITIES = [
    "pre-background-paper-recipe-leak-guard-and-opening-rung1-macro-stakes-html-grounding",
    "outsider-blind-reader-macro-onboarding-and-early-recipe-leak-verification",
]

CHANGE_SUMMARY = (
    "Upgrade `design-anti-goodhart` (`1.0.0-rc.22`), `html-ppt` (`1.0.0-rc.24` / wf `1.0.0-rc.21`), and "
    "`adaptive-interactive-tutor` (`1.0.0-rc.35`) to close three macro-background onboarding loopholes: "
    "(1) `extract_paper_specific_recipe_tokens` + `audit_slide_html_background_onboarding_fidelity` (`D13` & "
    "`audit_single_slide_step.py`) deterministically block pre-background cover slides (`pos < min(bg_indices)`) "
    "and Rung 1-2 background slides from leaking paper-specific chemical recipes (`3-PMPCl`, `4-PMPCl`, `PDISNN`) "
    "or substituent ring anatomy (`3-N吡啶`, `哌嗪环`, `ΔG = ΔH`); "
    "(2) opening `background_rung == 1` slides must ground `four_rung_funnel.rung1_macro_industry_stakes` in "
    "visible HTML and are blocked from jumping straight into >=2 narrow sub-domain band/quantum formalism terms "
    "(`间接带隙`, `直接带隙`, `S–Q 极限`); and "
    "(3) `verify_anti_collusion_blind_reader_audit` (`D18` + `--verify-blind-reader`) enforces explicit outsider "
    "onboarding attestation (`opening_macro_background_established: true`, `outsider_onboarding_gaps: []`) and "
    "rejects any premature paper-recipe tokens reconstructed on opening slides."
)


def _append_capabilities(existing):
    out = list(existing)
    for cap in NEW_CAPABILITIES:
        if cap not in out:
            out.append(cap)
    return out


def _update_limitations(lims):
    return [
        lim.replace(f"releases/{PREV_DESIGN_REL}/source", f"releases/{DESIGN_REL}/source")
        for lim in lims
    ]


def register_all():
    public_route_sha = file_hash(ENG_SOURCE_DIR / "test_public_route.py")
    eng_tree_sha = tree_hash(ENG_SOURCE_DIR)
    provenance_str = (
        "Pre-Background Paper-Recipe Leak Guard, Opening Rung-1 Macro-Stakes HTML Grounding & Outsider Blind-Reader Onboarding; "
        f"workflows/design-anti-goodhart/releases/{DESIGN_REL}/source/test_public_route.py sha256={public_route_sha}"
    )

    dag_comp_path = AWF_ROOT / "components/skills/design-anti-goodhart/component.yaml"
    dag_comp = read(dag_comp_path)
    dag_entry = copy.deepcopy(dag_comp["releases"][PREV_DESIGN_REL])
    dag_entry.update(
        observed_at=OBSERVED_DATE,
        source_snapshot=f"components/skills/design-anti-goodhart/releases/{DESIGN_REL}/source",
        tree_sha256=tree_hash(AWF_ROOT / f"components/skills/design-anti-goodhart/releases/{DESIGN_REL}/source"),
        capabilities=_append_capabilities(dag_entry["capabilities"]),
        limitations=_update_limitations(dag_entry["limitations"]),
        provenance=provenance_str,
        change_summary=CHANGE_SUMMARY,
    )
    dag_comp["releases"][DESIGN_REL] = dag_entry
    write(dag_comp_path, dag_comp)

    html_comp_path = AWF_ROOT / "components/skills/html-ppt/component.yaml"
    html_comp = read(html_comp_path)
    html_entry = copy.deepcopy(html_comp["releases"][PREV_HTML_SKILL_REL])
    html_entry.update(
        observed_at=OBSERVED_DATE,
        source_snapshot=f"components/skills/html-ppt/releases/{HTML_SKILL_REL}/source",
        tree_sha256=tree_hash(AWF_ROOT / f"components/skills/html-ppt/releases/{HTML_SKILL_REL}/source"),
        depends_on=[f"skill.design-anti-goodhart@{DESIGN_REL}", "skill.anti-goodhart-verification@3.7.0-rc.7"],
        capabilities=_append_capabilities(html_entry["capabilities"]),
        limitations=_update_limitations(html_entry["limitations"]),
        provenance=provenance_str,
        change_summary=CHANGE_SUMMARY,
    )
    html_comp["releases"][HTML_SKILL_REL] = html_entry
    write(html_comp_path, html_comp)

    tutor_comp_path = AWF_ROOT / "components/skills/adaptive-interactive-tutor/component.yaml"
    tutor_comp = read(tutor_comp_path)
    tutor_entry = copy.deepcopy(tutor_comp["releases"][PREV_TUTOR_REL])
    tutor_entry.update(
        observed_at=OBSERVED_DATE,
        source_snapshot=f"components/skills/adaptive-interactive-tutor/releases/{TUTOR_REL}/source",
        tree_sha256=tree_hash(AWF_ROOT / f"components/skills/adaptive-interactive-tutor/releases/{TUTOR_REL}/source"),
        depends_on=[
            "skill.anti-goodhart-verification@3.7.0-rc.7",
            f"skill.design-anti-goodhart@{DESIGN_REL}",
            f"skill.html-ppt@{HTML_SKILL_REL}",
        ],
        runtime_requirements=[
            req.replace(PREV_DESIGN_REL, DESIGN_REL).replace(PREV_HTML_SKILL_REL, HTML_SKILL_REL)
            for req in tutor_entry["runtime_requirements"]
        ],
        capabilities=_append_capabilities(tutor_entry["capabilities"]),
        limitations=_update_limitations(tutor_entry["limitations"]),
        provenance=provenance_str,
        change_summary=CHANGE_SUMMARY,
    )
    tutor_comp["releases"][TUTOR_REL] = tutor_entry
    write(tutor_comp_path, tutor_comp)

    wf_specs = [
        (
            "design-anti-goodhart",
            DESIGN_REL,
            {
                "skill.design-anti-goodhart": DESIGN_REL,
                "skill.anti-goodhart-verification": "3.7.0-rc.7",
                "tool.awf-repository-verifier": "1.0.0-rc.2",
            },
        ),
        (
            "html-ppt",
            HTML_WF_REL,
            {
                "skill.html-ppt": HTML_SKILL_REL,
                "skill.design-anti-goodhart": DESIGN_REL,
                "skill.anti-goodhart-verification": "3.7.0-rc.7",
                "tool.awf-repository-verifier": "1.0.0-rc.2",
            },
        ),
        (
            "adaptive-interactive-tutor",
            TUTOR_REL,
            {
                "skill.adaptive-interactive-tutor": TUTOR_REL,
                "skill.anti-goodhart-verification": "3.7.0-rc.7",
                "skill.design-anti-goodhart": DESIGN_REL,
                "skill.html-ppt": HTML_SKILL_REL,
                "tool.awf-repository-verifier": "1.0.0-rc.2",
            },
        ),
    ]

    wf_hashes = {}
    for wf_id, wf_rel, lock_comps in wf_specs:
        wf_dir = AWF_ROOT / f"workflows/{wf_id}/releases/{wf_rel}"
        wf_yaml_path = wf_dir / "workflow.yaml"
        wf_doc = read(wf_yaml_path)
        wf_doc["release"] = wf_rel
        wf_doc["purpose"] = (
            wf_doc["purpose"]
            .replace(PREV_DESIGN_REL, DESIGN_REL)
            .replace(PREV_HTML_SKILL_REL, HTML_SKILL_REL)
        )
        wf_doc["engineering_gate"] = (
            wf_doc["engineering_gate"]
            .replace(PREV_DESIGN_REL, DESIGN_REL)
            .replace(PREV_HTML_SKILL_REL, HTML_SKILL_REL)
        )
        wf_doc["scientific_gate"] = wf_doc["scientific_gate"].replace(PREV_DESIGN_REL, DESIGN_REL)
        wf_doc["engineering_source"] = f"workflows/design-anti-goodhart/releases/{DESIGN_REL}/source"
        wf_doc["engineering_source_tree_sha256"] = eng_tree_sha
        wf_doc["known_limitations"] = _update_limitations(wf_doc["known_limitations"])
        write(wf_yaml_path, wf_doc)

        lock_path = wf_dir / "versions.lock"
        lock_doc = {
            "schema_version": 1,
            "workflow": wf_id,
            "workflow_release": wf_rel,
            "locked_at": OBSERVED_DATE,
            "components": lock_comps,
        }
        write(lock_path, lock_doc)
        wf_hashes[wf_id] = (
            wf_rel,
            f"workflows/{wf_id}/releases/{wf_rel}/workflow.yaml",
            file_hash(wf_yaml_path),
            f"workflows/{wf_id}/releases/{wf_rel}/versions.lock",
            file_hash(lock_path),
        )

    reg_path = AWF_ROOT / "registry.fragment.json"
    reg_doc = read(reg_path)
    latest_comp_map = {
        "skill.design-anti-goodhart": DESIGN_REL,
        "skill.html-ppt": HTML_SKILL_REL,
        "skill.adaptive-interactive-tutor": TUTOR_REL,
    }
    for comp_item in reg_doc["components"]:
        cid = comp_item["id"]
        if cid in latest_comp_map:
            comp_item["latest_release"] = latest_comp_map[cid]

    for wf_item in reg_doc["workflows"]:
        wid = wf_item["id"]
        if wid in wf_hashes:
            wf_rel, desc_rel, desc_sha, lock_rel, lock_sha = wf_hashes[wid]
            wf_item["descriptor"] = desc_rel
            wf_item["descriptor_sha256"] = desc_sha
            wf_item["lock"] = lock_rel
            wf_item["lock_sha256"] = lock_sha
            wf_item["releases"][wf_rel] = {
                "descriptor": desc_rel,
                "descriptor_sha256": desc_sha,
                "lock": lock_rel,
                "lock_sha256": lock_sha,
                "status": "validated",
            }
    write(reg_path, reg_doc)

    manifest_path = REPO_ROOT / "MANIFEST.json"
    manifest_doc = read(manifest_path)
    manifest_doc["workflows"]["design-anti-goodhart"] = DESIGN_REL
    manifest_doc["workflows"]["html-ppt"] = HTML_WF_REL
    manifest_doc["workflows"]["adaptive-interactive-tutor"] = TUTOR_REL
    manifest_doc["locked_skills"]["design-anti-goodhart"] = DESIGN_REL
    manifest_doc["locked_skills"]["html-ppt"] = HTML_SKILL_REL
    manifest_doc["locked_skills"]["adaptive-interactive-tutor"] = TUTOR_REL

    files_map = {}
    all_files = sorted(
        (
            p for p in REPO_ROOT.rglob("*")
            if p.is_file()
            and ".git" not in p.parts
            and "dist" not in p.parts
            and "__pycache__" not in p.parts
            and p.name != "MANIFEST.json"
        ),
        key=lambda p: p.relative_to(REPO_ROOT).as_posix(),
    )
    for fpath in all_files:
        rel = fpath.relative_to(REPO_ROOT).as_posix()
        files_map[rel] = {
            "bytes": fpath.stat().st_size,
            "sha256": file_hash(fpath),
        }
    manifest_doc["files"] = files_map
    write(manifest_path, manifest_doc)
    print(f"Registered rc.22/rc.24/rc.35 closure cleanly: {len(files_map)} files in MANIFEST.json")


if __name__ == "__main__":
    register_all()
