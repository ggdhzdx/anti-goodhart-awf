"""Advance HTML-PPT's exact dependency and expose final evidence acceptance."""
from pathlib import Path
ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'registry.yaml').is_file())
path = ROOT / 'components/skills/html-ppt/releases/1.0.0-rc.15/source/scripts/audit_single_slide_step.py'
text = path.read_text(encoding='utf-8')
text = text.replace('1.0.0-rc.14', '1.0.0-rc.15').replace('1.0.0-rc.12', '1.0.0-rc.13')
text = text.replace('AWF DesignAG Verified HTML-PPT Deck', 'AWF HTML-PPT Assembled Draft')
text = text.replace('"total_slides_assembled": len(slide_bodies),', '"presentation_acceptance": "REVIEW_REQUIRED",\n        "assurance_scope": "structural_assembly_only",\n        "total_slides_assembled": len(slide_bodies),')
anchor = '    args = parser.parse_args(argv)'
options = '''    parser.add_argument("--verify-deck-evidence", default="", help="Verify a final deck with complete rubric and signed review evidence")
    parser.add_argument("--review-bundle", default="", help="Complete 18-gate bundle JSON")
    parser.add_argument("--evidence-manifest", default="", help="Signed renderer/reviewer manifest JSON")
    parser.add_argument("--trust-policy", default="", help="Runner-owned public-key trust policy; never supplied by the deck")
    parser.add_argument("--review-run-id", default="", help="Expected run ID issued by the runner")
    parser.add_argument("--review-targets", default="", help="JSON mapping screenshot artifact IDs to the assembled deck path")
'''
text = text.replace(anchor, options + anchor)
text = text.replace('    if args.self_test:\n', '''    if args.verify_deck_evidence:
        from design_review_adapter import verify_deck_evidence
        try:
            context = {"manifest_path": args.evidence_manifest, "trust_policy_path": args.trust_policy,
                       "run_id": args.review_run_id, "expected_artifacts": json.loads(Path(args.review_targets).read_text(encoding="utf-8"))}
            rep = verify_deck_evidence(_load_design_ag_module(), args.verify_deck_evidence, args.review_bundle, context)
        except (ValueError, KeyError, TypeError, OSError) as error:
            rep = {"status": "FAIL", "reason": str(error)}
        print(json.dumps(rep, indent=2, ensure_ascii=False))
        return 0 if rep["status"] == "PASS" else 1

    if args.self_test:
''')
path.write_text(text, encoding='utf-8')
