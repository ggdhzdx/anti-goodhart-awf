#!/usr/bin/env python3
"""Bootstrap immutable successor source trees for Guard 3.9.0-rc.1 and Verifier 1.0.0-rc.5 (ADR 0022)."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "registry.yaml").is_file())
GUARD_PREV = ROOT / "components/skills/anti-goodhart-verification/releases/3.8.0-rc.1/source"
GUARD_NEXT = ROOT / "components/skills/anti-goodhart-verification/releases/3.9.0-rc.1/source"
TOOL_PREV = ROOT / "components/tools/awf-repository-verifier/releases/1.0.0-rc.4/source"
TOOL_NEXT = ROOT / "components/tools/awf-repository-verifier/releases/1.0.0-rc.5/source"


def copy_clean_tree(src: Path, dst: Path) -> int:
    if dst.exists():
        raise RuntimeError(f"Target source tree already exists: {dst}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(
        src,
        dst,
        symlinks=True,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache"),
    )
    return sum(1 for p in dst.rglob("*") if p.is_file())


def main() -> int:
    guard_files = copy_clean_tree(GUARD_PREV, GUARD_NEXT)
    tool_files = copy_clean_tree(TOOL_PREV, TOOL_NEXT)
    # Preserve 3.8.0-rc.1's 80-subcheck contract as guard_required_subchecks_v38.json for backward compatibility
    shutil.copy2(
        TOOL_PREV / "guard_required_subchecks.json",
        TOOL_NEXT / "guard_required_subchecks_v38.json",
    )
    print(
        json.dumps(
            {
                "status": "PASS",
                "guard_next": str(GUARD_NEXT.relative_to(ROOT)),
                "guard_copied_files": guard_files,
                "tool_next": str(TOOL_NEXT.relative_to(ROOT)),
                "tool_copied_files": tool_files + 1,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
