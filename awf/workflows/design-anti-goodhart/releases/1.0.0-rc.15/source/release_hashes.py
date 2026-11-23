"""Canonical AWF integrity hashes, co-located for this release publication."""
import hashlib
import json
import os
import stat
from pathlib import Path

IGNORED = {"__pycache__", ".pytest_cache"}


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical_hash(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def paths(root):
    return sorted((p for p in root.rglob("*") if not IGNORED.intersection(p.relative_to(root).parts)),
                  key=lambda p: p.relative_to(root).as_posix())


def tree_hash(root):
    lines = (f"{file_hash(p)}  ./{p.relative_to(root).as_posix()}\n" for p in paths(root)
             if p.is_file() and not p.is_symlink())
    return hashlib.sha256("".join(lines).encode()).hexdigest()


def tree_v2(root):
    records = []
    for p in paths(root):
        metadata = p.lstat()
        record = {"mode": f"{stat.S_IMODE(metadata.st_mode):04o}", "path": p.relative_to(root).as_posix()}
        if p.is_symlink():
            record.update(kind="symlink", target=os.readlink(p))
        elif p.is_file():
            record.update(kind="file", bytes=metadata.st_size, sha256=file_hash(p))
        elif p.is_dir():
            record["kind"] = "directory"
        else:
            raise ValueError(f"Unsupported special file: {p}")
        records.append(json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
    return hashlib.sha256("".join(records).encode()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write(path, data, exclusive=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x" if exclusive else "w", encoding="utf-8") as stream:
        stream.write(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
