"""AWF Guard: claims."""
from __future__ import annotations

from typing import Any
from typing import Dict
from typing import List
from typing import Literal
from typing import Optional
from pathlib import Path
from typing import Sequence
from typing import Set
from typing import Union
from awf_guard_numeric_contracts import finite_float as _finite_float
from awf_guard_numeric_contracts import finite_inputs as _finite_inputs
import ast
from dataclasses import dataclass
import re
import subprocess
from .command_receipts import CommandReceipt
from .ast_dataflow import _is_pure_literal_expr
from .command_receipts import analyze_receipt_weakness
from .command_receipts import get_working_tree_last_edit_time


@dataclass
class AgentClaim:
    """
    Structured factual claim extracted from or supplied by an AI coding agent about its own work.
    Supported `claim_type` values:
    - `"file_changed"`      : `subject` = file path, `expected_value` = `"added" | "modified" | "deleted" | "touched"`
    - `"only_changed"`      : `subject` = file/dir path substring (asserts NO other files were modified)
    - `"symbol_exists"`     : `subject` = function/class/method identifier, `expected_value` = `True` (exists/added) or `False` (removed/absent)
    - `"symbol_renamed"`    : `subject` = old symbol name, `expected_value` = new symbol name
    - `"config_value"`      : `subject` = constant/variable name, `expected_value` = numeric/string/bool literal value
    - `"command_succeeded"` : `subject` = command or `"tests"`
    - `"uncheckable_prose"` : subjective judgment (`"this is cleaner and more robust"`) -> resolves to `refused`
    """
    claim_type: Literal[
        "file_changed",
        "only_changed",
        "symbol_exists",
        "symbol_renamed",
        "config_value",
        "command_succeeded",
        "uncheckable_prose",
    ]
    subject: str = ""
    expected_value: Any = None
    raw_text: str = ""


_INTENT_PREFIXES = (
    "let me ",
    "let's ",
    "confirm ",
    "verify ",
    "check ",
    "checking ",
    "ensure ",
    "i'll ",
    "i will ",
    "going to ",
    "to confirm ",
    "to verify ",
    "to check ",
    "now i ",
)


_META_PROSE_CUES = (
    "false positive",
    "false accusation",
    "false pass",
    "over-claim",
    "overclaim",
    "noted in memory",
    "in memory as",
    "regression test",
    "recorded via",
)


def _is_quoted_example(s: str) -> bool:
    first = s.find('"')
    last = s.rfind('"')
    if first != -1 and last > first + 1:
        inside = s[first + 1 : last]
        inside_non_ws = sum(1 for c in inside if not c.isspace())
        total_non_ws = sum(1 for c in s if not c.isspace())
        if (total_non_ws > 0 and inside_non_ws * 2 >= total_non_ws) or len(inside.split()) >= 3:
            return True
    return False


def segment_agent_message(message: str) -> List[str]:
    """
    Segment a raw agent message into candidate factual claim clauses
    (ported from `blasrodri/truth` `crates/truth-cli/src/verify_turn.rs`).
    Preserves decimal points (`3.5`) and file paths (`src/config.py`), while dropping
    markdown tables/blockquotes, future-intent plans (`Let me verify...`), meta-prose, and quoted citations.
    """
    buf_chars: List[str] = []
    n = len(message)
    for i, ch in enumerate(message):
        if ch == ".":
            nxt = message[i + 1] if i + 1 < n else None
            if nxt is None or nxt.isspace():
                buf_chars.append("\x01")
            else:
                buf_chars.append(ch)
        elif ch in ("!", "?", ";", "\n", "\r", ","):
            buf_chars.append("\x01")
        else:
            buf_chars.append(ch)
    buf = "".join(buf_chars)
    for conj in (" and ", " then ", " also ", " but ", " plus "):
        buf = re.sub(re.escape(conj), "\x01", buf, flags=re.IGNORECASE)

    segments: List[str] = []
    for raw_seg in buf.split("\x01"):
        s = raw_seg.strip()
        words = s.split()
        if not (2 <= len(words) <= 45):
            continue
        if s.startswith("|") or s.startswith(">"):
            continue
        low = s.lower()
        if any(low.startswith(p) for p in _INTENT_PREFIXES):
            continue
        if any(m in low for m in _META_PROSE_CUES):
            continue
        if _is_quoted_example(s):
            continue
        has_path = ("/" in s) or s.endswith(".py") or (".py" in low)
        has_num = any(c.isdigit() for c in s)
        has_const = any(len(w) >= 3 and all(c.isupper() or c == "_" for c in w) for w in words)
        has_backtick = "`" in s
        has_verb = any(v in low for v in ("added", "removed", "deleted", "dropped", "created", "edited", "modified", "renamed", "set "))
        has_success = any(v in low for v in ("pass", "passes", "passed", "green", "compiles", "clean"))
        agent_led = low.startswith(("i ", "i'", "we ", "we'"))
        if has_path or has_num or has_const or has_backtick or has_verb or has_success or agent_led:
            segments.append(s)
    return segments


def parse_natural_language_claim(text: str) -> AgentClaim:
    """Deterministically parse a natural-language claim sentence into a structured `AgentClaim`."""
    s = text.strip()
    low = s.lower()

    # 1. Scope claim: "I only changed/modified/edited <path>"
    m_only = re.search(r"\bonly\s+(?:changed|modified|edited|touched|updated)\s+`?([^\s`,;]+)`?", s, flags=re.IGNORECASE)
    if m_only:
        return AgentClaim(claim_type="only_changed", subject=m_only.group(1), raw_text=s)

    # 2. Rename claim: "renamed `old` to `new`"
    m_ren = re.search(r"\brenamed\s+`?([A-Za-z_][A-Za-z0-9_]*)`?\s+to\s+`?([A-Za-z_][A-Za-z0-9_]*)`?", s, flags=re.IGNORECASE)
    if m_ren:
        return AgentClaim(claim_type="symbol_renamed", subject=m_ren.group(1), expected_value=m_ren.group(2), raw_text=s)

    # 3. Config / constant value claim: "set MAX_RETRIES to 5" or "MAX_RETRIES is 5"
    m_val = re.search(
        r"\b(?:set|changed|updated|bumped|lowered)?\s*`?([A-Za-z_][A-Za-z0-9_]*)`?\s+(?:to|is|=)\s+`?([-+]?\d+(?:\.\d+)?|true|false|'[^']*'|\"[^\"]*\")`?",
        s,
        flags=re.IGNORECASE,
    )
    if m_val and (m_val.group(1).isupper() or "_" in m_val.group(1)):
        raw_v = m_val.group(2)
        val: Any = raw_v
        if raw_v.lower() == "true":
            val = True
        elif raw_v.lower() == "false":
            val = False
        elif re.fullmatch(r"[-+]?\d+", raw_v):
            val = int(raw_v)
        elif re.fullmatch(r"[-+]?\d+\.\d+", raw_v):
            val = _finite_float(raw_v)
        else:
            val = raw_v.strip("'\"")
        return AgentClaim(claim_type="config_value", subject=m_val.group(1), expected_value=val, raw_text=s)

    # 4. Command success claim: "tests pass", "pytest passes", "suite is green"
    if any(p in low for p in ("tests pass", "test suite pass", "pytest pass", "all tests pass", "suite passes", "tests are green", "verify.py pass")):
        return AgentClaim(claim_type="command_succeeded", subject="tests", expected_value=0, raw_text=s)

    # 5. File change claim: "added/created/edited/modified/deleted/removed path/to/file.py"
    m_file = re.search(
        r"\b(added|created|edited|modified|updated|deleted|removed)\s+(?:file\s+)?`?([A-Za-z0-9_./\\-]+\.(?:py|rs|ts|js|go|yaml|json|md|toml))`?",
        s,
        flags=re.IGNORECASE,
    )
    if m_file:
        verb = m_file.group(1).lower()
        f_path = m_file.group(2).replace("\\", "/")
        if verb in ("added", "created"):
            kind = "added"
        elif verb in ("deleted", "removed"):
            kind = "deleted"
        else:
            kind = "modified"
        return AgentClaim(claim_type="file_changed", subject=f_path, expected_value=kind, raw_text=s)

    # 6. Symbol existence claim: "added/removed function/class/helper/symbol `foo`"
    m_sym = re.search(
        r"\b(added|created|implemented|removed|deleted|dropped)\s+(?:the\s+)?(?:function|def|class|method|helper|symbol|atom)\s+`?([A-Za-z_][A-Za-z0-9_]*)`?",
        s,
        flags=re.IGNORECASE,
    )
    if m_sym:
        verb = m_sym.group(1).lower()
        exists_expected = verb in ("added", "created", "implemented")
        return AgentClaim(claim_type="symbol_exists", subject=m_sym.group(2), expected_value=exists_expected, raw_text=s)

    return AgentClaim(claim_type="uncheckable_prose", raw_text=s)


def gather_repo_and_diff_facts(
    repo_root: Optional[Path] = None,
    extra_source_code: Optional[str] = None,
    extra_diff_files: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Gather deterministic binary evidence from the working tree, `git diff`, and Python AST:
    - `diff_files`: mapping `rel_path -> "added" | "modified" | "deleted" | "renamed"`
    - `defined_symbols`: set of all AST function/class/method names
    - `defined_constants`: mapping `CONST_NAME -> literal_value`
    """
    diff_files: Dict[str, str] = dict(extra_diff_files or {})
    defined_symbols: Set[str] = set()
    defined_constants: Dict[str, Any] = {}

    def _index_ast_source(src: str) -> None:
        try:
            tree = ast.parse(src)
        except SyntaxError:
            return
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                defined_symbols.add(node.name)
            elif isinstance(node, ast.Assign) and _is_pure_literal_expr(node.value):
                try:
                    val = ast.literal_eval(node.value)
                except Exception:
                    continue
                for tgt in node.targets:
                    if isinstance(tgt, ast.Name):
                        defined_constants[tgt.id] = val
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.value is not None and _is_pure_literal_expr(node.value):
                try:
                    defined_constants[node.target.id] = ast.literal_eval(node.value)
                except (ValueError, TypeError, SyntaxError, MemoryError, RecursionError):
                    continue

    if extra_source_code:
        _index_ast_source(extra_source_code)

    if repo_root is not None and repo_root.is_dir():
        repo_root = repo_root.resolve()
        if not diff_files:
            try:
                proc = subprocess.run(
                    ["git", "-C", str(repo_root), "diff", "HEAD", "--name-status", "-M", "--no-color"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    check=False,
                )
                if proc.returncode == 0:
                    for line in proc.stdout.splitlines():
                        parts = line.split("\t")
                        if len(parts) >= 2:
                            code = parts[0][0]
                            path_str = parts[-1].replace("\\", "/")
                            if code == "A":
                                diff_files[path_str] = "added"
                            elif code == "M":
                                diff_files[path_str] = "modified"
                            elif code == "D":
                                diff_files[path_str] = "deleted"
                            elif code == "R":
                                diff_files[path_str] = "renamed"
                untracked = subprocess.run(
                    ["git", "-C", str(repo_root), "ls-files", "--others", "--exclude-standard"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    check=False,
                )
                if untracked.returncode == 0:
                    for line in untracked.stdout.splitlines():
                        p = line.strip().replace("\\", "/")
                        if p and p not in diff_files:
                            diff_files[p] = "added"
            except (OSError, subprocess.SubprocessError):
                diff_files = dict(extra_diff_files or {})

        for py_file in sorted(repo_root.rglob("*.py")):
            if "__pycache__" in py_file.parts or ".git" in py_file.parts:
                continue
            try:
                _index_ast_source(py_file.read_text(encoding="utf-8"))
            except OSError:
                continue

    return {
        "diff_files": diff_files,
        "defined_symbols": defined_symbols,
        "defined_constants": defined_constants,
    }


def _make_claim_verdict(
    text: str,
    claim_type: str,
    status: str,
    structured: bool,
    confidence: float,
    detail: str,
    refused_reason: Optional[str] = None,
) -> Dict[str, Any]:
    return {
        "text": text,
        "claim_type": claim_type,
        "status": status,
        "refused_reason": refused_reason,
        "structured": structured,
        "confidence": confidence,
        "detail": detail,
    }


_CLAIM_CONF_EXACT_MATCH = 0.92


_CLAIM_CONF_STRONG = 0.90


_CLAIM_CONF_STRUCTURAL = 0.88


_CLAIM_CONF_ABSENCE_INFERENCE = 0.85


_CLAIM_CONF_WEAK_RECEIPT = 0.55


_CLAIM_CONF_NO_EVIDENCE = 0.30


def _evaluate_ast_symbol_or_config_claim(
    claim: AgentClaim,
    text_label: str,
    defined_symbols: Set[str],
    defined_constants: Dict[str, Any],
) -> Dict[str, Any]:
    c_type = claim.claim_type
    subj = claim.subject
    exp = claim.expected_value
    if c_type == "config_value":
        if subj in defined_constants:
            actual_val = defined_constants[subj]
            matched = (actual_val == exp) or (
                isinstance(actual_val, (int, float))
                and isinstance(exp, (int, float))
                and abs(_finite_float(actual_val) - _finite_float(exp)) < 1e-12
            )
            if matched:
                return _make_claim_verdict(text_label, c_type, "supported", True, _CLAIM_CONF_EXACT_MATCH, f"AST defines `{subj} = {actual_val!r}`.")
            return _make_claim_verdict(
                text_label, c_type, "contradicted", True, _CLAIM_CONF_EXACT_MATCH, f"Claim says `{subj}` is `{exp!r}`, but AST source defines `{actual_val!r}`."
            )
        return _make_claim_verdict(text_label, c_type, "refused", False, _CLAIM_CONF_NO_EVIDENCE, f"Constant `{subj}` not found in indexed AST definitions.", "inconclusive")

    if c_type == "symbol_exists":
        want_present = bool(exp) if exp is not None else True
        is_present = subj in defined_symbols
        if is_present == want_present:
            return _make_claim_verdict(text_label, c_type, "supported", True, _CLAIM_CONF_STRUCTURAL, f"Symbol `{subj}` presence={is_present} matches claim.")
        return _make_claim_verdict(text_label, c_type, "contradicted", True, _CLAIM_CONF_STRUCTURAL, f"Symbol `{subj}` presence is {is_present} (claimed {want_present}).")

    old_name = subj
    new_name = str(exp)
    old_still_there = old_name in defined_symbols
    new_present = new_name in defined_symbols
    if not old_still_there and new_present:
        return _make_claim_verdict(text_label, c_type, "supported", True, _CLAIM_CONF_STRONG, f"Old symbol `{old_name}` is gone and `{new_name}` is defined.")
    if old_still_there:
        return _make_claim_verdict(
            text_label, c_type, "contradicted", True, _CLAIM_CONF_STRUCTURAL, f"Claimed `{old_name}` was renamed to `{new_name}`, but `{old_name}` still survives in AST!"
        )
    return _make_claim_verdict(
        text_label, c_type, "contradicted", True, _CLAIM_CONF_ABSENCE_INFERENCE, f"`{old_name}` is absent, but new symbol `{new_name}` was never defined in AST!"
    )


def _evaluate_diff_or_command_claim(
    claim: AgentClaim,
    text_label: str,
    diff_files: Dict[str, str],
    receipt_list: Sequence[CommandReceipt],
    last_edit_mtime: Optional[float],
) -> Dict[str, Any]:
    c_type = claim.claim_type
    subj = claim.subject
    exp = claim.expected_value
    if c_type == "file_changed":
        norm_subj = subj.replace("\\", "/")
        matched_file = next(
            (p for p in diff_files if p == norm_subj or p.endswith("/" + norm_subj) or norm_subj.endswith("/" + p)),
            None,
        )
        if matched_file is not None:
            actual_st = diff_files[matched_file]
            ok = (
                (exp == "added" and actual_st == "added")
                or (exp == "deleted" and actual_st == "deleted")
                or (exp == "touched")
                or (exp not in ("added", "deleted") and actual_st in ("modified", "added", "renamed"))
            )
            if ok:
                return _make_claim_verdict(text_label, c_type, "supported", True, _CLAIM_CONF_STRONG, f"Diff shows `{matched_file}` status is `{actual_st}`.")
            return _make_claim_verdict(
                text_label, c_type, "contradicted", True, _CLAIM_CONF_STRUCTURAL, f"Claimed `{norm_subj}` was `{exp}`, but diff shows `{actual_st}`."
            )
        if diff_files:
            return _make_claim_verdict(
                text_label, c_type, "contradicted", True, _CLAIM_CONF_ABSENCE_INFERENCE, f"Working-tree diff does not touch `{norm_subj}` (touched: {sorted(diff_files.keys())})."
            )
        return _make_claim_verdict(text_label, c_type, "refused", False, _CLAIM_CONF_NO_EVIDENCE, "No working-tree diff available to verify file change claim.", "inconclusive")

    if c_type == "only_changed":
        norm_subj = subj.replace("\\", "/")
        if not diff_files:
            return _make_claim_verdict(text_label, c_type, "refused", False, _CLAIM_CONF_NO_EVIDENCE, "Working tree has no diff files to verify scope claim.", "inconclusive")
        touched = any(norm_subj in p for p in diff_files)
        offenders = sorted(p for p in diff_files if norm_subj not in p)
        if touched and not offenders:
            return _make_claim_verdict(text_label, c_type, "supported", True, _CLAIM_CONF_STRONG, f"All changed files match scope `{norm_subj}`.")
        if not touched:
            return _make_claim_verdict(text_label, c_type, "contradicted", True, _CLAIM_CONF_STRUCTURAL, f"Diff does not touch `{norm_subj}` at all (changed: {offenders}).")
        return _make_claim_verdict(
            text_label, c_type, "contradicted", True, _CLAIM_CONF_STRONG, f"Scope lie: claimed ONLY `{norm_subj}` changed, but diff also touches collateral file(s): {offenders}."
        )

    test_receipts = [r for r in receipt_list if r.kind == "test"]
    if not test_receipts:
        return _make_claim_verdict(text_label, c_type, "unproven", False, _CLAIM_CONF_NO_EVIDENCE, "Claimed tests pass without any recorded CommandReceipt! Proof is required.")
    latest_r = test_receipts[-1]
    if latest_r.exit_code != 0:
        return _make_claim_verdict(
            text_label, c_type, "contradicted", True, _CLAIM_CONF_EXACT_MATCH, f"Latest recorded run `{latest_r.command}` failed with exit_code={latest_r.exit_code}."
        )
    if last_edit_mtime is not None and latest_r.finished_at < last_edit_mtime:
        return _make_claim_verdict(
            text_label,
            c_type,
            "contradicted",
            True,
            _CLAIM_CONF_STRUCTURAL,
            f"Stale test receipt: `{latest_r.command}` finished at {latest_r.finished_at:.2f}, which predates latest working-tree edit at {last_edit_mtime:.2f}!",
        )
    weakness = analyze_receipt_weakness(latest_r.command, latest_r.output_tail)
    if weakness is not None:
        return _make_claim_verdict(text_label, c_type, "partial", True, _CLAIM_CONF_WEAK_RECEIPT, f"Receipt exited 0 after edit, but is weak ({weakness}).")
    return _make_claim_verdict(text_label, c_type, "supported", True, _CLAIM_CONF_EXACT_MATCH, f"Verified fresh green receipt for `{latest_r.command}`.")


@_finite_inputs
def verify_agent_turn_claims(
    claims_or_message: Union[str, Sequence[Union[str, AgentClaim]]],
    repo_root: Optional[Path] = None,
    command_receipts: Optional[Sequence[CommandReceipt]] = None,
    last_edit_mtime: Optional[float] = None,
    extra_source_code: Optional[str] = None,
    extra_diff_files: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Deterministic Turn-Level Fact-Checker for AI Coding Agents (absorbed from `blasrodri/truth`):
    Evaluates each claim against real AST definitions, working-tree `git diff`, and recorded `CommandReceipt`s.
    Produces 5-way canonical verdicts (`supported`, `contradicted`, `partial`, `unproven`, `refused`),
    enforces the Structured-Fact Zero-False-Accusation Gate (`structured=True` required for `contradicted`),
    and detects the `Wall-of-Refusals` vague-prose evasion (`is_wall_of_refusals`).
    """
    if isinstance(claims_or_message, str):
        raw_segments = segment_agent_message(claims_or_message)
        structured_claims = [parse_natural_language_claim(seg) for seg in raw_segments]
    else:
        structured_claims = [
            parse_natural_language_claim(c) if isinstance(c, str) else c
            for c in claims_or_message
        ]

    if last_edit_mtime is None and repo_root is not None and repo_root.is_dir():
        last_edit_mtime = get_working_tree_last_edit_time(repo_root)

    facts = gather_repo_and_diff_facts(
        repo_root=repo_root,
        extra_source_code=extra_source_code,
        extra_diff_files=extra_diff_files,
    )
    diff_files: Dict[str, str] = facts["diff_files"]
    defined_symbols: Set[str] = facts["defined_symbols"]
    defined_constants: Dict[str, Any] = facts["defined_constants"]
    receipt_list = list(command_receipts or [])

    verdicts: List[Dict[str, Any]] = []
    for claim in structured_claims:
        c_type = claim.claim_type
        text_label = claim.raw_text or f"{c_type}:{claim.subject}={claim.expected_value}"
        if c_type == "uncheckable_prose":
            verdicts.append(
                _make_claim_verdict(
                    text_label, c_type, "refused", False, 0.0, "Subjective judgment or uncheckable prose; refused rather than guessed.", "not_checkable"
                )
            )
        elif c_type in ("config_value", "symbol_exists", "symbol_renamed"):
            verdicts.append(_evaluate_ast_symbol_or_config_claim(claim, text_label, defined_symbols, defined_constants))
        else:
            verdicts.append(_evaluate_diff_or_command_claim(claim, text_label, diff_files, receipt_list, last_edit_mtime))

    for v in verdicts:
        if v["status"] == "contradicted" and not v.get("structured", False):
            v["status"] = "refused"
            v["refused_reason"] = "inconclusive"

    n_supp = sum(1 for v in verdicts if v["status"] == "supported")
    n_cont = sum(1 for v in verdicts if v["status"] == "contradicted")
    n_part = sum(1 for v in verdicts if v["status"] == "partial")
    n_unpr = sum(1 for v in verdicts if v["status"] == "unproven")
    n_refu = sum(1 for v in verdicts if v["status"] == "refused")
    wall_of_refusals = (len(verdicts) >= 3 and n_supp == 0 and n_cont == 0) or (len(verdicts) > 0 and n_supp == 0 and n_refu == len(verdicts))
    passed = (n_supp > 0) and (n_cont == 0) and (n_part == 0) and (n_unpr == 0) and (not wall_of_refusals)
    return {
        "status": "PASS" if passed else "FAIL",
        "summary": {
            "claims_total": len(verdicts),
            "supported": n_supp,
            "contradicted": n_cont,
            "partial": n_part,
            "unproven": n_unpr,
            "refused": n_refu,
            "all_refused_wall": wall_of_refusals,
            "needs_proof": n_unpr > 0,
        },
        "verdicts": verdicts,
    }
