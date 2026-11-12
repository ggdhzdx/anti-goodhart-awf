#!/usr/bin/env python3
"""Pin explicitly reviewed local regression/fixture files for Guard 3.7.0-rc.8; never called by runtime or validation."""
from __future__ import annotations

import ast
import hashlib
import json
import sys
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "registry.yaml").is_file())
SOURCE = ROOT / "components/skills/anti-goodhart-verification/releases/3.7.0-rc.8/source"
SCRIPTS = SOURCE / "scripts"
sys.path.insert(0, str(SCRIPTS))
from awf_guard.self_audit import _SELF_AUDIT_TEST_ROLE_FILES  # noqa: E402

roles = list(dict.fromkeys(_SELF_AUDIT_TEST_ROLE_FILES))
entries = {}
for name in roles:
    path = SCRIPTS / name
    source = path.read_text(encoding="utf-8")
    constants = sorted(
        {
            n.value
            for n in ast.walk(ast.parse(source))
            if isinstance(n, ast.Constant) and isinstance(n.value, float)
        }
    )
    entries[name] = {
        "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "allowed_numeric_literals": constants,
        "reason": "Reviewed numeric regression inputs and deliberate faulty operators; pinned bytes, never inferred from a caller-selected name",
    }
(SOURCE / "fixture-numeric-policy.json").write_text(
    json.dumps({"schema_version": 1, "files": entries}, indent=2) + "\n",
    encoding="utf-8",
)
print(json.dumps({"reviewed_files": len(entries)}))
