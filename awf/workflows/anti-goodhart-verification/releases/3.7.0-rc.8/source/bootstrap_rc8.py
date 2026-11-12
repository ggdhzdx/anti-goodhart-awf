"""Create isolated successor source snapshots (Guard 3.7.0-rc.8 and Verifier 1.0.0-rc.3); never overwrite a draft or release."""
from pathlib import Path
import shutil

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "registry.yaml").is_file())
for unit, old, new in [
    ("skills/anti-goodhart-verification", "3.7.0-rc.7", "3.7.0-rc.8"),
    ("tools/awf-repository-verifier", "1.0.0-rc.2", "1.0.0-rc.3"),
]:
    base = ROOT / "components" / unit / "releases"
    shutil.copytree(
        base / old / "source",
        base / new / "source",
        ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"),
    )
print("Bootstrapped skill.anti-goodhart-verification@3.7.0-rc.8 and tool.awf-repository-verifier@1.0.0-rc.3")
