#!/usr/bin/env python3
"""Generate reviewed valid v3.9.0-rc.1 receipt fixture for Verifier 1.0.0-rc.5 positive/negative contract tests."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "registry.yaml").is_file())
ENGINE = ROOT / "components/skills/anti-goodhart-verification/releases/3.9.0-rc.1/source/scripts/awf_universal_anti_goodhart_gates.py"
OUT_FIXTURE = ROOT / "components/tools/awf-repository-verifier/releases/1.0.0-rc.5/source/fixtures/guard-valid-receipt.json"


def main() -> int:
    proc = subprocess.run(
        [sys.executable, "-B", str(ENGINE), "--self-test"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr or proc.stdout)
        return proc.returncode
    receipt = json.loads(proc.stdout)
    OUT_FIXTURE.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": "PASS",
                "subchecks_verified_count": receipt.get("subchecks_verified_count"),
                "negative_controls_total": receipt.get("negative_controls_total"),
                "fixture": str(OUT_FIXTURE.relative_to(ROOT)),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
