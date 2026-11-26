"""Canonical AWF integrity hashes, co-located for Guard 3.9.0-rc.1 and Verifier 1.0.0-rc.5 publication."""
from __future__ import annotations

import hashlib
import json
import os
import stat
from pathlib import Path

IGNORED = {"__pycache__", ".pytest_cache"}


def file_hash(path: Path | str) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical_hash(value: object) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def paths(root: Path) -> list[Path]:
    return sorted(
        (p for p in root.rglob("*") if not IGNORED.intersection(p.relative_to(root).parts)),
        key=lambda p: p.relative_to(root).as_posix(),
    )


def tree_hash(root: Path) -> str:
    lines = (
        f"{file_hash(p)}  ./{p.relative_to(root).as_posix()}\n"
        for p in paths(root)
        if p.is_file() and not p.is_symlink()
    )
    return hashlib.sha256("".join(lines).encode("utf-8")).hexdigest()


def tree_v2(root: Path) -> str:
    records = []
    for p in paths(root):
        metadata = p.lstat()
        record: dict[str, object] = {
            "mode": f"{stat.S_IMODE(metadata.st_mode):04o}",
            "path": p.relative_to(root).as_posix(),
        }
        if p.is_symlink():
            record.update(kind="symlink", target=os.readlink(p))
        elif p.is_file():
            record.update(kind="file", bytes=metadata.st_size, sha256=file_hash(p))
        elif p.is_dir():
            record["kind"] = "directory"
        else:
            raise ValueError(f"Unsupported special file: {p}")
        records.append(json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
    return hashlib.sha256("".join(records).encode("utf-8")).hexdigest()


def read(path: Path | str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write(path: Path | str, data: object, exclusive: bool = False) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("x" if exclusive else "w", encoding="utf-8") as stream:
        stream.write(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
