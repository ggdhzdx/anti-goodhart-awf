"""AWF Guard: command receipts."""
from __future__ import annotations

from typing import Any
from typing import Dict
from typing import List
from typing import Literal
from typing import Optional
from pathlib import Path
from typing import Sequence
from awf_guard_numeric_contracts import finite_float as _finite_float
from awf_guard_numeric_contracts import finite_inputs as _finite_inputs
from dataclasses import dataclass
import hashlib
import json
import re
import subprocess
import time
from .errors import AntiGoodhartGateError


ClaimWireStatus = Literal["supported", "contradicted", "partial", "unproven", "refused"]


@dataclass
class CommandReceipt:
    """
    Tamper-evident execution receipt for a verification/test/build command
    (absorbed from `blasrodri/truth` `crates/truth-cli/src/run.rs` & `crates/truth-core/src/verdict.rs`).
    Makes agent claims like 'tests pass' deterministically checkable against:
    1. Exit code (`exit_code == 0`);
    2. Freshness vs. last working-tree file edit (`finished_at >= last_edit_mtime`);
    3. Non-weakness (`analyze_receipt_weakness`: zero tests executed or scope-narrowed subset flags).
    """
    command: str
    exit_code: int
    started_at: float
    finished_at: float
    output_tail: str = ""
    output_sha256: str = ""
    kind: str = "test"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "command": self.command,
            "exit_code": self.exit_code,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "output_tail": self.output_tail,
            "output_sha256": self.output_sha256,
            "kind": self.kind,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "CommandReceipt":
        cmd_val = str(d["command"]) if "command" in d and d["command"] is not None else ""
        exit_val = int(d["exit_code"]) if "exit_code" in d and d["exit_code"] is not None else -1
        start_val = _finite_float(d["started_at"]) if "started_at" in d and d["started_at"] is not None else 0.0
        fin_val = _finite_float(d["finished_at"]) if "finished_at" in d and d["finished_at"] is not None else 0.0
        tail_val = str(d["output_tail"]) if "output_tail" in d and d["output_tail"] is not None else ""
        sha_val = str(d["output_sha256"]) if "output_sha256" in d and d["output_sha256"] is not None else ""
        kind_val = str(d["kind"]) if "kind" in d and d["kind"] is not None else classify_command_kind(cmd_val)
        return cls(
            command=cmd_val,
            exit_code=exit_val,
            started_at=start_val,
            finished_at=fin_val,
            output_tail=tail_val,
            output_sha256=sha_val,
            kind=kind_val,
        )


def classify_command_kind(command: str) -> str:
    """
    Classify command string into receipt kind (`format`, `lint`, `typecheck`, `test`, `build`, `other`).
    Explicitly blocks `git commit -m 'fix tests'` from masquerading as a test receipt!
    """
    c = command.strip().lower()
    if c.startswith("git "):
        return "other"
    if any(k in c for k in ("fmt", "format", "prettier", "black")):
        return "format"
    if any(k in c for k in ("clippy", "lint", "eslint", "ruff", "flake8", " vet")):
        return "lint"
    if any(k in c for k in ("tsc", "typecheck", "mypy", "pyright")):
        return "typecheck"
    if any(k in c for k in ("test", "spec", "pytest", "--self-test", "verify.py")):
        return "test"
    if any(k in c for k in ("build", "compile", "check")):
        return "build"
    return "other"


_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


_BEARER_RE = re.compile(r"(?i)(bearer\s+|token\s*[:=]\s*|api[_-]?key\s*[:=]\s*)[A-Za-z0-9._\-]{8,}")


def redact_sensitive_log_tail(output: str, max_chars: int = 1200) -> str:
    """Keep at most `max_chars` of command output tail while scrubbing emails and secret tokens."""
    tail = output[-max_chars:] if len(output) > max_chars else output
    tail = _EMAIL_RE.sub("[REDACTED_EMAIL]", tail)
    tail = _BEARER_RE.sub(r"\1[REDACTED_SECRET]", tail)
    return tail


_ZERO_TESTS_CUES = (
    "0 tests run",
    "0 passed",
    "ran 0 tests",
    "no tests run",
    "no tests ran",
    "no tests found",
    "0 selected",
    "collected 0 items",
    "0 examples",
    "executed 0",
)


_SCOPE_NARROW_FLAGS = (
    " --test ",
    " -k ",
    " -t ",
    " --run ",
    " -run ",
    " --filter ",
    " --only ",
    " --testname",
    "::",
)


def analyze_receipt_weakness(command: str, output_tail: str = "") -> Optional[str]:
    """
    Detect an empty or scope-narrowed green receipt (`blasrodri/truth` Threat Model #4):
    1. Output reports zero tests executed (`0 tests run`, `collected 0 items`, etc.);
    2. Command was scope-narrowed to a single subset/filter (`pytest -k`, `path::case`, `--filter`, `--only`).
    """
    if output_tail:
        low_tail = output_tail.lower()
        if any(z in low_tail for z in _ZERO_TESTS_CUES):
            return "the run reported zero tests executed"
    low_cmd = f" {command.lower()} "
    if any(flag in low_cmd for flag in _SCOPE_NARROW_FLAGS):
        return "the command was scope-narrowed to a subset of tests"
    return None


def get_working_tree_last_edit_time(repo_root: Path) -> Optional[float]:
    """
    Determine the timestamp (epoch seconds) of the most recent working-tree file edit.
    Checks modified/untracked files via `git diff HEAD --name-only` + `git ls-files --others`,
    falling back to `git log -1 --format=%ct` on a clean tree, or scanning `.py` mtimes.
    """
    repo_root = repo_root.resolve()
    latest_mtime: Optional[float] = None
    try:
        diff_proc = subprocess.run(
            ["git", "-C", str(repo_root), "diff", "HEAD", "--name-only", "--no-color"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        untracked_proc = subprocess.run(
            ["git", "-C", str(repo_root), "ls-files", "--others", "--exclude-standard"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        cand_files: List[str] = []
        if diff_proc.returncode == 0:
            cand_files.extend(l.strip() for l in diff_proc.stdout.splitlines() if l.strip())
        if untracked_proc.returncode == 0:
            cand_files.extend(l.strip() for l in untracked_proc.stdout.splitlines() if l.strip())
        for rel_f in cand_files:
            fp = repo_root / rel_f
            if fp.exists():
                mt = fp.stat().st_mtime
                latest_mtime = mt if latest_mtime is None else max(latest_mtime, mt)
        if latest_mtime is not None:
            return latest_mtime
        log_proc = subprocess.run(
            ["git", "-C", str(repo_root), "log", "-1", "--format=%ct"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if log_proc.returncode == 0 and log_proc.stdout.strip():
            return _finite_float(log_proc.stdout.strip())
    except (OSError, subprocess.SubprocessError, ValueError):
        latest_mtime = None

    for py_f in repo_root.rglob("*.py"):
        if "__pycache__" not in py_f.parts and py_f.is_file():
            mt = py_f.stat().st_mtime
            latest_mtime = mt if latest_mtime is None else max(latest_mtime, mt)
    return latest_mtime


def run_and_record_command_receipt(
    cmd: Sequence[str],
    receipt_ledger_path: Optional[Path] = None,
    cwd: Optional[Path] = None,
) -> CommandReceipt:
    """Execute `cmd`, compute output SHA-256 + redacted tail, and optionally persist to `receipt_ledger_path`."""
    cmd_str = " ".join(cmd)
    started_at = time.time()
    proc = subprocess.run(
        list(cmd),
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        check=False,
    )
    finished_at = time.time()
    combined = (proc.stdout or "") + "\n" + (proc.stderr or "")
    out_sha = hashlib.sha256(combined.encode("utf-8", errors="replace")).hexdigest()
    receipt = CommandReceipt(
        command=cmd_str,
        exit_code=int(proc.returncode),
        started_at=started_at,
        finished_at=finished_at,
        output_tail=redact_sensitive_log_tail(combined, 1200),
        output_sha256=out_sha,
        kind=classify_command_kind(cmd_str),
    )
    if receipt_ledger_path is not None:
        existing: List[Dict[str, Any]] = []
        if receipt_ledger_path.is_file():
            try:
                existing = json.loads(receipt_ledger_path.read_text(encoding="utf-8"))
            except Exception:
                existing = []
        existing.append(receipt.to_dict())
        receipt_ledger_path.parent.mkdir(parents=True, exist_ok=True)
        receipt_ledger_path.write_text(json.dumps(existing, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return receipt


@_finite_inputs
def verify_command_receipt_freshness(
    receipts: Sequence[CommandReceipt],
    last_edit_mtime: Optional[float] = None,
    require_un_narrowed: bool = True,
) -> Dict[str, Any]:
    """
    Verify recorded command receipts for Gate `G6c_CommandReceipt_Fresh_And_Unnarrowed`:
    - Must have at least one test/verification receipt (`kind == 'test'`);
    - Latest test receipt must have `exit_code == 0`;
    - If `last_edit_mtime` is provided, `receipt.finished_at >= last_edit_mtime` (blocks stale 'test -> edit -> claim');
    - If `require_un_narrowed=True`, `analyze_receipt_weakness` must be `None` (blocks zero-test or `-k` subset runs).
    """
    test_receipts = [r for r in receipts if r.kind == "test"]
    if not test_receipts:
        raise AntiGoodhartGateError(
            "[Gate 6c Unproven Command Claim] No recorded `test` CommandReceipt found! "
            "Agents cannot claim tests pass without a recorded execution receipt."
        )
    latest = test_receipts[-1]
    if latest.exit_code != 0:
        raise AntiGoodhartGateError(
            f"[Gate 6c Contradicted Command Receipt] Latest recorded test command `{latest.command}` "
            f"failed with exit_code={latest.exit_code}!"
        )
    if last_edit_mtime is not None and latest.finished_at < last_edit_mtime:
        raise AntiGoodhartGateError(
            f"[Gate 6c Stale Command Receipt] Test receipt `{latest.command}` (finished_at={latest.finished_at:.3f}) "
            f"predates latest working-tree edit (mtime={last_edit_mtime:.3f})! Re-run tests after editing code."
        )
    weakness = analyze_receipt_weakness(latest.command, latest.output_tail)
    if weakness is not None and require_un_narrowed:
        raise AntiGoodhartGateError(
            f"[Gate 6c Weak/Narrowed Command Receipt] Test receipt `{latest.command}` is weak ({weakness}) — "
            f"a green subset or zero-test run cannot stand for the full suite!"
        )
    return {
        "verified_command": latest.command,
        "exit_code": latest.exit_code,
        "fresh": True if last_edit_mtime is None else (latest.finished_at >= last_edit_mtime),
        "weakness": weakness,
        "output_sha256": latest.output_sha256,
    }
