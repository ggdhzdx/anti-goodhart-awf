"""Write the current hardening contract and honest trust/coverage boundaries."""
from pathlib import Path
from stack_release_config import ROOT, SOURCES, COMPONENTS, ENGINEERING

CONTRACT = '''

## D17/D18 evidence hardening contract (2026-11-10)

Resolved composition: Tutor Skill/Workflow `1.0.0-rc.26`, DesignAG Skill/Workflow
`1.0.0-rc.13`, HTML-PPT Skill `1.0.0-rc.15` / Workflow `1.0.0-rc.12`,
Guard `3.7.0-rc.7`, repository verifier `1.0.0-rc.2`.

1. D17 no longer invents missing grades. All 15 knowledge criteria, all B-E
   grades, five dimensions, readability penalties and R1-R7 assessments are
   explicit. Weights and required modalities are fixed to the co-located rubric;
   NaN/Inf, booleans as scores, negative counts, duplicate criteria and out-of-range
   values fail. The threshold cannot be below 80; final HTML-PPT requires 85.
   Any redline prevents acceptance even if the numerical score remains high.
2. D17/D18 require separately authorized Ed25519 renderer and reviewer receipts.
   The runner supplies its public-key trust policy, expected artifact paths and
   run ID outside the user bundle. There are NO default trusted production keys.
   Never auto-trust a key embedded in a submission or copy test authorities into
   production. A trusted runner and isolated signer keys are the security boundary.
3. Receipts bind the exact HTML and PNG bytes, capture profile, static slide
   selector/index/state, complete frame coverage, complete rubric payload and
   31 criterion observations. Missing/corrupt/non-PNG/wrong-size images, altered
   source, copied PNGs across frames, stale run IDs, unsigned edits, unknown keys,
   same renderer/reviewer key and partial review coverage do not pass.
4. Supported profile is `offline-static-slide-initial-v1`: normalized explicit
   html/head/body; exact offline CSP from `design_capture_profile.CSP_META` as a
   direct head child before active content; all resources embedded as data/inline
   content; no executable scripts or event handlers. Duplicate attributes and
   non-void self-closing tags are rejected (use explicit SVG closing tags too).
   Static `.slide` elements are
   counted from actual HTML; each initial frame must be captured. Without `.slide`,
   the single `html` frame is used. Identical PNGs across frames require additional
   review. JavaScript-generated views and interaction state coverage are unsupported
   by this profile and remain REVIEW_REQUIRED, not automatically accepted.
5. Structural assembly is a draft milestone. HTML-PPT's per-slide path runs ten
   applicable checks; `assemble_verified_deck` reports `presentation_acceptance:
   REVIEW_REQUIRED`. Final acceptance uses `--verify-deck-evidence` and all 18 gates.
   Direct `run_all_18_design_gates` also rejects bundle HTML that differs from the
   actual reviewed artifact. No alternate public entry point may bypass binding.

### Trust and domain limits

Signatures prove who attested to which bytes; they do not prove a renderer executed
correctly, an auditor truly looked, scientific truth, or independence of judgment.
The renderer must actually capture each declared frame; the reviewer must inspect
the captures and record observations. D1-D16 still accept some caller-supplied
metadata. This release tests force-PASS mutations for D17/D18, not all 18 gates.
The fixed knowledge rubric is the bundled optoelectronic rubric; adapting it to
another domain requires an explicitly reviewed rubric successor, not caller-chosen
weights. Guard scientific validation remains a separate requirement.

### API and CLI

`run_all_18_design_gates(bundle, evidence_context=context)` accepts a context with
`manifest_path`, `trust_policy_path`, `expected_artifacts` (artifact ID to HTML path)
and `run_id`. The signed manifest has `render` and `review` envelopes, each with
`payload` and a base64 Ed25519 `signature` over UTF-8 canonical JSON (sorted keys,
compact separators, ensure_ascii=False, allow_nan=False). The policy schema is
`{"schema_version":1,"renderers":{"ID":"BASE64_RAW_PUBLIC_KEY"},"reviewers":{"ID":"BASE64_RAW_PUBLIC_KEY"}}`.
Keys identify separately authorized roles. Signature generation belongs to the
trusted renderer/reviewer processes, never to the untrusted deck producer.

The renderer payload contains schema_version, run_id, renderer_id, renderer,
capture_profile, and artifacts. Each artifact includes artifact_id, html_path,
html_sha256, png_path, png_sha256, width, height, resources=[], and
frame={selector,index,state}. Reviewer payload contains schema_version, run_id,
reviewer_id, render_payload_sha256, score_payload_sha256, reviewed_artifact_ids,
verdict, findings, and criterion_evidence. Each criterion observation names its
artifact_ids and a nonempty observation. All artifacts must be cited somewhere.

```text
python -B scripts/awf_design_anti_goodhart_gates.py --self-test
python -B scripts/awf_design_anti_goodhart_gates.py --audit-self
python -B design_tests/test_evidence.py
```

For final HTML-PPT acceptance, invoke its pinned script:

```text
python -B scripts/audit_single_slide_step.py --verify-deck-evidence deck.html --review-bundle bundle.json --evidence-manifest evidence.json --trust-policy trusted-public-keys.json --review-run-id RUN_ID --review-targets targets.json
```

The trusted runner must own the last three arguments and target mapping. Passing
attacker-chosen values there invalidates the trust boundary. See DesignAG
`references/evidence-contract.md` and source modules for the exact schema. Synthetic
fixtures create ephemeral in-memory keys and explicitly do not grant production trust.

All engineering scripts for this coordinated release are physically co-located at
`workflows/design-anti-goodhart/releases/1.0.0-rc.13/source/`; include that directory
and locked component trees when packaging. Current releases remain immutable.
'''


def document():
    for name, source in SOURCES.items():
        path = source / 'SKILL.md'
        text = path.read_text(encoding='utf-8').split('## AG rc.7 integration contract')[0].split('## D17/D18 evidence hardening contract')[0].rstrip()
        for component, (old, new) in COMPONENTS.items():
            text = text.replace(f'skill.{component}@{old}', f'skill.{component}@{new}')
            text = text.replace(f'{component}\\releases\\{old}', f'{component}\\releases\\{new}')
            text = text.replace(f'{component}/releases/{old}', f'{component}/releases/{new}')
        old, new = COMPONENTS[name]
        text = text.replace(f'Authoritative Source (`{old}`)', f'Authoritative Source (`{new}`)')
        text = text.replace('D1-D6, D15 static/DOM gates', 'D1/D2/D5 static subset only')
        text = text.replace('passing all 18 `DesignAG` gates sequentially to produce `deck.html`', 'passing applicable per-slide structural checks to produce a draft `deck.html` before final evidence acceptance')
        text = text.replace('through all 18 `DesignAG` gates', 'through applicable per-slide structural checks')
        path.write_text(text + CONTRACT, encoding='utf-8')
    target = SOURCES['design-anti-goodhart'] / 'references/evidence-contract.md'
    target.write_text('# Signed evidence contract\n' + CONTRACT + '\nImplementation references: [Ed25519](https://cryptography.io/en/latest/hazmat/primitives/asymmetric/ed25519/), [Chrome headless](https://developer.chrome.com/docs/automation-and-testing/headless), [HTML duplicate-attribute rules](https://html.spec.whatwg.org/multipage/parsing.html#attribute-name-state).\n', encoding='utf-8')
    html = SOURCES['html-ppt'] / 'scripts/audit_single_slide_step.py'
    text = html.read_text(encoding='utf-8').replace('18-gate re-audit', 'applicable per-slide re-audit').replace('18-Gate re-audit', 'applicable per-slide re-audit')
    html.write_text(text, encoding='utf-8')
    (ENGINEERING / 'README.md').write_text('''# DesignAG evidence hardening engineering closure

This directory contains all development, diagnostic, browser-smoke, public-route,
validation and publication scripts used for DesignAG rc.13, Tutor rc.26 and
HTML-PPT Workflow rc.12 / Skill rc.15. Draft transformation scripts are historical
development tools, not idempotent commands for an already registered release.
The final component source trees are authoritative.

Reproduce runtime checks on node01 as zc:
`python -B workflows/design-anti-goodhart/releases/1.0.0-rc.13/source/publish_stack.py --validate-only`.
Before validation, run the co-located `browser_smoke.py` on Windows with installed
Chrome, Pillow and cryptography. It uses an isolated temporary Chrome profile,
copies output to project reports, and only creates ephemeral test signing keys.

Publication is `publish_stack.py --publish` as root after successful validation.
It refuses changed current pointers, stale source/evidence or existing registrations.
New workflow/archive directories are owned by zc and checked for readability before
locking, avoiding the inherited shared-folder ACL problem from the predecessor.
The independent verifier remains 1.0.0-rc.2; Guard remains 3.7.0-rc.7.

No production renderer/reviewer keys are bundled or provisioned. Final acceptance
requires a runner-owned public-key policy and genuinely independent authorized
render/review processes. Unsupported dynamic pages remain pending.
''', encoding='utf-8')


if __name__ == '__main__':
    document()
