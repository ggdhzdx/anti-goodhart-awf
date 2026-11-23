"""Strict data and byte contracts shared by scores and review evidence."""
import hashlib
import json
import math
from pathlib import Path

SCORE_MAX = 100.0
MIN_PASS_SCORE = 80.0
CANVAS_SIZE = (1920, 1080)
MAX_EVIDENCE_BYTES = 32 * 1024 * 1024


def require(condition, message):
    if not condition:
        raise ValueError(message)


def number(value, low=0.0, high=SCORE_MAX):
    require(type(value) in (int, float) and math.isfinite(value), 'Expected a finite number, not a boolean/string')
    require(low <= value <= high, 'Number outside the declared range')
    return float(value)


def boolean(value):
    require(type(value) is bool, 'Expected an explicit boolean')
    return value


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode('utf-8')


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def file_bytes(path):
    path = Path(path).resolve()
    require(path.is_file(), f'Missing regular evidence file: {path}')
    require(0 < path.stat().st_size <= MAX_EVIDENCE_BYTES, 'Empty or oversized evidence file')
    return path.read_bytes()


def file_digest(path):
    return hashlib.sha256(file_bytes(path)).hexdigest()


def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'Duplicate JSON key')
        result[key] = value
    return result


def read_json(path):
    return json.loads(file_bytes(path), object_pairs_hook=_unique_pairs)
