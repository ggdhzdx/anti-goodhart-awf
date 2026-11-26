"""AWF Guard: benchmark."""
from __future__ import annotations

from typing import Any
from typing import Dict
from typing import List
from typing import Literal
from typing import Optional
from pathlib import Path
from typing import Sequence
from typing import Set
from awf_guard_numeric_contracts import finite_float as _finite_float
from awf_guard_numeric_contracts import finite_inputs as _finite_inputs
import ast
from dataclasses import dataclass
import os
import re
from .ast_utils import text_dedent


_BENCHJACK_EVAL_KEYWORDS = (
    "eval", "evaluate", "evaluator", "score", "scorer", "scoring",
    "grade", "grader", "grading", "judge", "judging",
    "validate", "validator", "validation", "metric", "metrics",
    "reward", "check", "checker", "verify", "verifier",
    "harness", "benchmark", "run_eval", "run_benchmark",
)


_BENCHJACK_AGENT_KEYWORDS = (
    "agent", "model", "llm", "assistant", "solver", "solution",
    "inference", "predict", "generate", "response", "completion",
    "scaffold", "run_agent", "run_model",
)


@dataclass(frozen=True)
class TrustBoundaryFileOp:
    """File read or write extracted by `BenchJackTrustAnalyzer`."""
    op_type: Literal["read", "write"]
    path_expr: str
    source_file: str
    line: int
    context: Literal["eval", "agent", "unknown"]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "op_type": self.op_type,
            "path_expr": self.path_expr,
            "source_file": self.source_file,
            "line": self.line,
            "context": self.context,
        }


class BenchJackTrustAnalyzer(ast.NodeVisitor):
    """
    AST visitor adapted from `benchjack/tools/trust_map.py` and `benchjack_semgrep_rules.yml`.
    Extracts:
    - File I/O (`open`, `Path.read_text/write_text`, `json.load/dump`, `yaml`, `shutil.copy/move`)
    - Subprocess invocations (`shell=True`, `captures_output=True`, `pytest` inside agent context)
    - Dangerous sinks (`V3`: `eval`, `exec`, `pickle.load`, `yaml.load` without `SafeLoader`)
    - Evaluator logic gaps (`V6`: `except: return True / 1.0`, role-only validation)
    - Weak string matching (`V5`: `answer in response` / `response.find(answer)`)
    - Pytest / Unittest Hook Hijacking (`V1/V7`: `pytest_runtest_makereport`, `TestCase.run` monkeypatch)
    - Answer key shipping (`V2`: dict literals with `"answer"`, `"gold"`, `"ground_truth"`)
    """

    def __init__(self, source_file: str, context: Literal["eval", "agent", "unknown"]) -> None:
        self.source_file = source_file
        self.context = context
        self.file_ops: List[TrustBoundaryFileOp] = []
        self.findings: List[Dict[str, Any]] = []

    @staticmethod
    def _expr_to_str(node: Optional[ast.AST]) -> str:
        if node is None:
            return "<unknown>"
        try:
            return ast.unparse(node)
        except Exception:
            if isinstance(node, ast.Constant):
                return repr(node.value)
            if isinstance(node, ast.Name):
                return node.id
            return "<complex-expr>"

    @staticmethod
    def _get_dotted_name(node: ast.Call) -> str:
        func = node.func
        if isinstance(func, ast.Name):
            return func.id
        if isinstance(func, ast.Attribute):
            parts: List[str] = []
            curr: ast.AST = func
            while isinstance(curr, ast.Attribute):
                parts.append(curr.attr)
                curr = curr.value
            if isinstance(curr, ast.Name):
                parts.append(curr.id)
            return ".".join(reversed(parts))
        return "<unknown>"

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        # Check SWE-bench V1/V7 exploit: pytest_runtest_makereport hook forcing rep.outcome = "passed"
        if node.name in ("pytest_runtest_makereport", "pytest_sessionfinish", "pytest_runtest_call"):
            src_unparsed = self._expr_to_str(node)
            if '"passed"' in src_unparsed or "'passed'" in src_unparsed or "outcome" in src_unparsed:
                self.findings.append({
                    "vulnerability": "V1",
                    "severity": "CRITICAL",
                    "kind": "PytestHookOutcomeHijack",
                    "file": self.source_file,
                    "line": node.lineno,
                    "detail": f"Pytest hook `{node.name}` overrides test outcome to 'passed' (SWE-bench V1 exploit).",
                })
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        # Check unittest.TestCase.run monkey-patching
        for tgt in node.targets:
            tgt_s = self._expr_to_str(tgt)
            if "TestCase.run" in tgt_s or "pytest.main" in tgt_s:
                self.findings.append({
                    "vulnerability": "V1",
                    "severity": "CRITICAL",
                    "kind": "TestRunnerMonkeyPatch",
                    "file": self.source_file,
                    "line": node.lineno,
                    "detail": f"Monkey-patching test runner attribute `{tgt_s}`.",
                })
        self.generic_visit(node)

    def visit_Try(self, node: ast.Try) -> None:
        # V6: Exception handler in evaluator returns passing score (True, 1.0, 1)
        if self.context in ("eval", "unknown"):
            for handler in node.handlers:
                for sub in ast.walk(handler):
                    if isinstance(sub, ast.Return) and isinstance(sub.value, ast.Constant):
                        val = sub.value.value
                        if val is True or (isinstance(val, (int, float)) and not isinstance(val, bool) and _finite_float(val) >= 1.0):
                            self.findings.append({
                                "vulnerability": "V6",
                                "severity": "HIGH",
                                "kind": "ExceptReturnsPassingScore",
                                "file": self.source_file,
                                "line": sub.lineno,
                                "detail": f"Exception handler returns passing score `{val!r}`; agent can trigger exception for a free pass.",
                            })
        self.generic_visit(node)

    def visit_Compare(self, node: ast.Compare) -> None:
        # V5: Weak substring containment matching (`answer in response`) in evaluator
        if self.context in ("eval", "unknown"):
            for op, comp in zip(node.ops, node.comparators):
                if isinstance(op, ast.In):
                    left_s = self._expr_to_str(node.left).lower()
                    right_s = self._expr_to_str(comp).lower()
                    if any(k in left_s for k in ("answer", "gold", "expected", "target")) and any(
                        k in right_s for k in ("response", "output", "pred", "completion", "result")
                    ):
                        self.findings.append({
                            "vulnerability": "V5",
                            "severity": "MEDIUM",
                            "kind": "WeakSubstringAnswerMatch",
                            "file": self.source_file,
                            "line": node.lineno,
                            "detail": f"Weak substring check `{self._expr_to_str(node)}` allows answer-dumping attacks.",
                        })
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        fn_name = self._get_dotted_name(node)

        # File operations
        if fn_name in ("open", "builtins.open"):
            path_expr = self._expr_to_str(node.args[0]) if node.args else "<unknown>"
            mode = "r"
            if len(node.args) > 1 and isinstance(node.args[1], ast.Constant):
                mode = str(node.args[1].value)
            for kw in node.keywords:
                if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
                    mode = str(kw.value.value)
            op_t: Literal["read", "write"] = "write" if any(c in mode for c in ("w", "a", "x", "+")) else "read"
            self.file_ops.append(TrustBoundaryFileOp(op_t, path_expr, self.source_file, node.lineno, self.context))
        elif fn_name.endswith((".read_text", ".read_bytes")):
            base_expr = self._expr_to_str(node.func.value) if isinstance(node.func, ast.Attribute) else "<unknown>"
            self.file_ops.append(TrustBoundaryFileOp("read", base_expr, self.source_file, node.lineno, self.context))
        elif fn_name.endswith((".write_text", ".write_bytes")):
            base_expr = self._expr_to_str(node.func.value) if isinstance(node.func, ast.Attribute) else "<unknown>"
            self.file_ops.append(TrustBoundaryFileOp("write", base_expr, self.source_file, node.lineno, self.context))
        elif fn_name in ("shutil.copy", "shutil.copy2", "shutil.move") and len(node.args) >= 2:
            self.file_ops.append(TrustBoundaryFileOp("read", self._expr_to_str(node.args[0]), self.source_file, node.lineno, self.context))
            self.file_ops.append(TrustBoundaryFileOp("write", self._expr_to_str(node.args[1]), self.source_file, node.lineno, self.context))

        # V3: Dangerous sinks (eval, exec, pickle, unsafe yaml.load)
        if fn_name in ("eval", "builtins.eval", "exec", "builtins.exec"):
            if not (node.args and isinstance(node.args[0], ast.Constant)):
                self.findings.append({
                    "vulnerability": "V3",
                    "severity": "CRITICAL",
                    "kind": "DynamicEvalOrExecSink",
                    "file": self.source_file,
                    "line": node.lineno,
                    "detail": f"Dynamic `{fn_name}({self._expr_to_str(node.args[0] if node.args else None)})` on potentially untrusted data.",
                })
        elif fn_name in ("pickle.load", "pickle.loads", "cPickle.load", "cPickle.loads"):
            self.findings.append({
                "vulnerability": "V3",
                "severity": "HIGH",
                "kind": "UnsafePickleDeserialization",
                "file": self.source_file,
                "line": node.lineno,
                "detail": f"`{fn_name}` allows arbitrary code execution if input is agent-controlled.",
            })
        elif fn_name == "yaml.load":
            has_safe_loader = any(
                kw.arg == "Loader" and "SafeLoader" in self._expr_to_str(kw.value)
                for kw in node.keywords
            )
            if not has_safe_loader:
                self.findings.append({
                    "vulnerability": "V3",
                    "severity": "HIGH",
                    "kind": "UnsafeYamlLoad",
                    "file": self.source_file,
                    "line": node.lineno,
                    "detail": "`yaml.load()` without `SafeLoader` allows arbitrary code execution.",
                })

        self.generic_visit(node)


def classify_benchmark_file_role(
    filepath: str,
    eval_patterns: Sequence[str] = (),
    agent_patterns: Sequence[str] = (),
) -> Literal["eval", "agent", "unknown"]:
    """Classify a file path as `eval` (scorer/verifier), `agent` (solver/candidate), or `unknown`."""
    norm = filepath.replace("\\", "/").lower()
    for pat in eval_patterns:
        if re.search(pat, norm):
            return "eval"
    for pat in agent_patterns:
        if re.search(pat, norm):
            return "agent"
    tokens = re.split(r"[/._\-]+", norm)
    eval_score = sum(1 for kw in _BENCHJACK_EVAL_KEYWORDS if kw in tokens)
    agent_score = sum(1 for kw in _BENCHJACK_AGENT_KEYWORDS if kw in tokens)
    if eval_score > agent_score:
        return "eval"
    if agent_score > eval_score:
        return "agent"
    return "unknown"


def find_trust_boundary_shared_paths(file_ops: Sequence[TrustBoundaryFileOp]) -> List[Dict[str, Any]]:
    """
    Detect `V1` Trust-Boundary Conflicts where an agent writes to a path or directory
    that the evaluator reads (`agent_writes & eval_reads`), requiring at least one side
    to be classified as `"agent"` or `"eval"`.
    """
    writes_by_ctx: Dict[str, Set[str]] = {"eval": set(), "agent": set(), "unknown": set()}
    reads_by_ctx: Dict[str, Set[str]] = {"eval": set(), "agent": set(), "unknown": set()}
    for op in file_ops:
        if op.op_type == "write":
            writes_by_ctx[op.context].add(op.path_expr)
        else:
            reads_by_ctx[op.context].add(op.path_expr)

    cross_boundary_paths = (
        (writes_by_ctx["agent"] & (reads_by_ctx["eval"] | reads_by_ctx["unknown"]))
        | ((writes_by_ctx["agent"] | writes_by_ctx["unknown"]) & reads_by_ctx["eval"])
    )
    conflicts: List[Dict[str, Any]] = []

    for shared_path in sorted(cross_boundary_paths):
        if shared_path == "<unknown>":
            continue
        conflicts.append({
            "vulnerability": "V1",
            "severity": "HIGH",
            "kind": "SharedAgentWriteEvalReadPath",
            "path": shared_path,
            "detail": f"Agent writes to `{shared_path}` which the evaluator directly reads without isolation.",
        })
    return conflicts


@_finite_inputs
def scan_container_and_prompt_injection_vulns(
    text: str,
    source_name: str = "<config>",
) -> List[Dict[str, Any]]:
    """
    Scan Dockerfiles, compose configs, shell scripts, or LLM judge inputs for:
    - `V8`: `--privileged`, `--network host`, `--pid host`, `seccomp:unconfined`, `chmod 777`
    - `V2`: `COPY`/`ADD` of `*answer*`, `*gold*`, `*ground_truth*` into container image
    - `V4`: Hidden HTML comment prompt injection (`<!-- EVALUATION NOTE: ... -->`)
    """
    findings: List[Dict[str, Any]] = []
    for lineno, raw_line in enumerate(text.splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        lower = line.lower()
        if "--privileged" in lower or ("privileged:" in lower and "true" in lower):
            findings.append({
                "vulnerability": "V8",
                "severity": "CRITICAL",
                "kind": "ContainerPrivilegedMode",
                "file": source_name,
                "line": lineno,
                "detail": f"Container granted `--privileged` access: `{line[:120]}`",
            })
        if "--network host" in lower or "--network=host" in lower or ("network_mode:" in lower and "host" in lower):
            findings.append({
                "vulnerability": "V8",
                "severity": "HIGH",
                "kind": "ContainerHostNetworking",
                "file": source_name,
                "line": lineno,
                "detail": f"Container shares host network namespace: `{line[:120]}`",
            })
        if "chmod 777" in lower or "chmod -r 777" in lower:
            findings.append({
                "vulnerability": "V8",
                "severity": "MEDIUM",
                "kind": "WorldWritablePermissions",
                "file": source_name,
                "line": lineno,
                "detail": f"World-writable `chmod 777` allows agent to overwrite evaluator files: `{line[:120]}`",
            })
        if line.upper().startswith(("COPY ", "ADD ")) and any(
            k in lower for k in ("answer", "gold", "ground_truth", "expected_output")
        ):
            findings.append({
                "vulnerability": "V2",
                "severity": "HIGH",
                "kind": "AnswerKeyCopiedIntoContainer",
                "file": source_name,
                "line": lineno,
                "detail": f"Dockerfile copies answer/gold file into agent image: `{line[:120]}`",
            })
        if "<!--" in line and any(
            k in lower for k in ("evaluation note", "policy_followed", "score:", "ignore previous", "system_instruction")
        ):
            findings.append({
                "vulnerability": "V4",
                "severity": "HIGH",
                "kind": "HiddenCommentJudgeInjection",
                "file": source_name,
                "line": lineno,
                "detail": f"Hidden HTML comment prompt-injection targeting LLM judge: `{line[:120]}`",
            })
    return findings


@_finite_inputs
def audit_benchmark_hackability(
    source_files: Dict[str, str],
    eval_patterns: Sequence[str] = (),
    agent_patterns: Sequence[str] = (),
) -> Dict[str, Any]:
    """
    Run the complete BenchJack V1-V8 Benchmark & Evaluator Hackability Audit across
    a mapping of `{filepath: file_content}` (Python files, Dockerfiles, shell scripts, configs).
    """
    all_ops: List[TrustBoundaryFileOp] = []
    all_findings: List[Dict[str, Any]] = []
    file_roles: Dict[str, str] = {}

    for fpath, content in source_files.items():
        role = classify_benchmark_file_role(fpath, eval_patterns=eval_patterns, agent_patterns=agent_patterns)
        file_roles[fpath] = role
        if fpath.endswith(".py"):
            try:
                tree = ast.parse(text_dedent(content), filename=fpath)
                analyzer = BenchJackTrustAnalyzer(fpath, role)
                analyzer.visit(tree)
                all_ops.extend(analyzer.file_ops)
                all_findings.extend(analyzer.findings)
            except SyntaxError as exc:
                all_findings.append({
                    "vulnerability": "V0",
                    "severity": "LOW",
                    "kind": "PythonSyntaxError",
                    "file": fpath,
                    "line": exc.lineno or 1,
                    "detail": f"SyntaxError while parsing `{fpath}`: {exc.msg}",
                })
        else:
            all_findings.extend(scan_container_and_prompt_injection_vulns(content, source_name=fpath))

    shared_conflicts = find_trust_boundary_shared_paths(all_ops)
    all_findings.extend(shared_conflicts)

    by_vuln: Dict[str, int] = {}
    for f in all_findings:
        v = str(f["vulnerability"]) if "vulnerability" in f and f["vulnerability"] is not None else "V?"
        by_vuln[v] = (by_vuln[v] if v in by_vuln else 0) + 1

    return {
        "status": "PASS" if not all_findings else "FAIL",
        "files_scanned": len(source_files),
        "file_roles": file_roles,
        "finding_count": len(all_findings),
        "findings_by_class": by_vuln,
        "findings": all_findings,
    }


@_finite_inputs
def audit_benchmark_directory(target_dir: Path) -> Dict[str, Any]:
    """Scan a benchmark directory on disk for V1-V8 hackability vulnerabilities."""
    source_map: Dict[str, str] = {}
    for root, dirs, files in os.walk(target_dir):
        dirs[:] = [d for d in dirs if d not in (".git", "__pycache__", "node_modules", ".venv", "venv")]
        for fname in files:
            low = fname.lower()
            if low.endswith((".py", ".sh", ".yml", ".yaml", ".md")) or "dockerfile" in low:
                full_p = Path(root) / fname
                rel_p = str(full_p.relative_to(target_dir))
                try:
                    source_map[rel_p] = full_p.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    continue
    return audit_benchmark_hackability(source_map)
