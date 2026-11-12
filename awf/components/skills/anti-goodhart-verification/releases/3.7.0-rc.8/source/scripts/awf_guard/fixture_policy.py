"""Explicit numeric allowances for reviewed, byte-pinned local test fixtures only."""
import hashlib
import json
from pathlib import Path


def reviewed_fixture_numbers(path, audit_root):
    scripts = Path(__file__).resolve().parent.parent
    if audit_root.resolve() != scripts:
        return None
    policy_path = scripts.parent / 'fixture-numeric-policy.json'
    policy = json.loads(policy_path.read_text()) if policy_path.is_file() else {}
    entry = policy.get('files', {}).get(path.relative_to(scripts).as_posix())
    if not entry or hashlib.sha256(path.read_bytes()).hexdigest() != entry.get('source_sha256'):
        return None
    return entry['allowed_numeric_literals']
