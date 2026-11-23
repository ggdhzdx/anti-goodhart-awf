"""Verify the real DesignAG 1.0.0-rc.14 facade and HTML-PPT 1.0.0-rc.16 CLI cannot bypass D13/D16/D17/D18."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from release_hashes import write

ROOT = next(
    p for p in Path(__file__).resolve().parents
    if (p / "registry.yaml").is_file() or (p / "registry.fragment.json").is_file()
)
DESIGN = ROOT / "components/skills/design-anti-goodhart/releases/1.0.0-rc.14/source"
HTML = ROOT / "components/skills/html-ppt/releases/1.0.0-rc.16/source/scripts"
sys.path[:0] = [str(DESIGN / "scripts"), str(DESIGN), str(HTML)]
import awf_design_anti_goodhart_gates as dag
from awf_design_ag_selftest_suite import _build_gold_standard_positive_bundle
from design_tests.evidence_fixtures import EvidenceFixture
from design_review_adapter import verify_deck_evidence


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def run():
    checks = []
    with tempfile.TemporaryDirectory() as directory:
        folder = Path(directory)
        original = _build_gold_standard_positive_bundle()
        fixture = EvidenceFixture(folder, html_text=original["html_text"])
        from design_contract import digest
        fixture.scores["min_passing_score"] = 85.0
        fixture.review["score_payload_sha256"] = digest(fixture.scores)
        fixture.write()
        bundle = fixture.attach(original)
        result = dag.run_all_18_design_gates(bundle, evidence_context=fixture.context)
        require(result["verdict_zone"] == "PASS" and result["gates_passed_count"] == 18, "full-engine positive")
        checks.append("full_engine_signed_positive")
        result = dag.run_all_18_design_gates(bundle)
        require(result["verdict_zone"] == "FAIL" and len(result["gates_failed"]) == 2, "full-engine unsigned acceptance")
        checks.append("full_engine_missing_context_rejected")
        bad = copy.deepcopy(bundle)
        bad["dual_rubric_eval"]["min_passing_score"] = 0
        result = dag.run_all_18_design_gates(bad, evidence_context=fixture.context)
        require(result["verdict_zone"] == "FAIL", "zero score threshold escaped the facade")
        checks.append("full_engine_zero_threshold_rejected")
        mismatched = copy.deepcopy(bundle)
        mismatched["html_text"] = "<html><body>another document</body></html>"
        require(dag.run_all_18_design_gates(mismatched, evidence_context=fixture.context)["verdict_zone"] == "FAIL", "different source HTML accepted")
        checks.append("full_engine_other_HTML_rejected")
        bundle["crop_specs"] = [{"id": "fig1ab", "subpanel_count": 2, "blank_margin_ratio": 0.0, "border_sliced_ink_ratio": 0.0}]
        bundle_path, targets_path = folder / "bundle.json", folder / "targets.json"
        write(bundle_path, bundle)
        write(targets_path, fixture.context["expected_artifacts"])
        result = verify_deck_evidence(dag, fixture.html, bundle_path, fixture.context)
        require(result["status"] == "PASS", "adapter positive")
        checks.append("html_adapter_positive")
        command = [
            sys.executable, "-B", str(HTML / "audit_single_slide_step.py"),
            "--verify-deck-evidence", str(fixture.html),
            "--review-bundle", str(bundle_path),
            "--evidence-manifest", fixture.context["manifest_path"],
            "--trust-policy", fixture.context["trust_policy_path"],
            "--review-run-id", fixture.context["run_id"],
            "--review-targets", str(targets_path),
        ]
        proc = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", check=False)
        require(proc.returncode == 0 and json.loads(proc.stdout)["presentation_acceptance"] == "PASS", proc.stderr or proc.stdout)
        checks.append("html_CLI_signed_positive")
        fixture.html.write_text("<html><body>modified after review</body></html>", encoding="utf-8")
        proc = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", check=False)
        require(proc.returncode != 0 and json.loads(proc.stdout)["status"] == "FAIL", "CLI accepted changed deck")
        checks.append("html_CLI_changed_deck_rejected")
        fixture.html.write_text(bundle["html_text"], encoding="utf-8")
        fixture.png.write_bytes(fixture.png.read_bytes() + b"tamper")
        require(dag.run_all_18_design_gates(bundle, evidence_context=fixture.context)["verdict_zone"] == "FAIL", "full-engine changed screenshot accepted")
        checks.append("full_engine_changed_screenshot_rejected")

        # CLI public-route check for 10-slide full-paper deck missing Beyond-PDF background bridge
        bad_sb = folder / "bad_storyboard.json"
        archetypes = ("top_banner_dual_cards", "split_left_fig_right_steps", "interactive_svg_sandbox_split")
        write(bad_sb, {
            "workflow_mode": "GRILL",
            "narrative_spec": {
                "has_macro_background_and_core_def": True,
                "has_degradation_or_bottleneck_mechanism": True,
                "has_prior_art_and_ceiling": True,
                "has_clue_free_blind_guessing": False,
                "has_foreshadowing_and_callback": True,
            },
            "mechanism_spec": {"causal_why_links_explained": {"a": True}},
            "storyboard_slides": [
                {"station_id": f"S_{i}", "title": f"Slide {i}", "layout_archetype": archetypes[(i - 1) % 3]}
                for i in range(1, 11)
            ],
        })
        bg_cmd = [
            sys.executable, "-B", str(HTML / "audit_single_slide_step.py"),
            "--init-storyboard", str(bad_sb),
            "--manifest", str(folder / "bad_manifest.json"),
        ]
        bg_proc = subprocess.run(bg_cmd, capture_output=True, text=True, encoding="utf-8", check=False)
        require(bg_proc.returncode != 0 and json.loads(bg_proc.stdout)["status"] == "FAIL", "CLI accepted 10-slide deck without domain_background_bridge")
        checks.append("html_CLI_missing_beyond_pdf_background_rejected")
    print(json.dumps({"status": "PASS", "checks_passed": checks, "scope": "Real APIs/CLI with synthetic authorities & Beyond-PDF Background Bridge"}, indent=2))


if __name__ == "__main__":
    run()
