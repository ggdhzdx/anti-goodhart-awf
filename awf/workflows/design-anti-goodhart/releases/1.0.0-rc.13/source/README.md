# DesignAG evidence hardening engineering closure

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
