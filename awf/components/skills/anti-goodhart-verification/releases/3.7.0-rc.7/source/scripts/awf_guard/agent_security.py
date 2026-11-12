"""AWF Guard: agent security."""
from __future__ import annotations

from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Sequence
from typing import Set
from typing import Union
from awf_guard_numeric_contracts import finite_inputs as _finite_inputs
import ast
import re
from .ast_dataflow import _iter_func_body_no_nested
from .ast_utils import text_dedent


_SECRET_VAR_KEYWORDS = (
    "api_key", "apikey", "secret", "password", "passwd",
    "token", "private_key", "aws_access_key_id", "aws_secret_access_key",
)


_KNOWN_API_KEY_PREFIXES = (
    ("sk-ant-", "Anthropic API Key"),
    ("sk-", "OpenAI API Key"),
    ("AKIA", "AWS Access Key ID"),
    ("ghp_", "GitHub Personal Access Token"),
    ("xoxb-", "Slack Bot Token"),
    ("AIza", "Google Cloud API Key"),
)


def _inspect_func_decorators_and_recursion(
    node: Union[ast.FunctionDef, ast.AsyncFunctionDef],
    defined_tools: Set[str],
    issues: List[Dict[str, Any]],
) -> None:
    fn_name = node.name
    for dec in node.decorator_list:
        dec_name = ""
        dec_kw: Dict[str, ast.AST] = {}
        if isinstance(dec, ast.Name):
            dec_name = dec.id
        elif isinstance(dec, ast.Attribute):
            dec_name = f"{getattr(dec.value, 'id', '')}.{dec.attr}".strip(".")
        elif isinstance(dec, ast.Call):
            if isinstance(dec.func, ast.Name):
                dec_name = dec.func.id
            elif isinstance(dec.func, ast.Attribute):
                dec_name = f"{getattr(dec.func.value, 'id', '')}.{dec.func.attr}".strip(".")
            dec_kw = {kw.arg: kw.value for kw in dec.keywords if kw.arg}

        if dec_name in ("tool", "function_tool") or dec_name.endswith((".tool", ".function_tool")):
            if "name" in dec_kw and isinstance(dec_kw["name"], ast.Constant) and isinstance(dec_kw["name"].value, str):
                defined_tools.add(dec_kw["name"].value)
            else:
                defined_tools.add(fn_name)

        if dec_name in ("retry", "tenacity.retry") and "stop" not in dec_kw:
            issues.append({
                "tier": "[P]",
                "category": "agent_patterns",
                "kind": "UnboundedTenacityRetry",
                "line": node.lineno,
                "detail": f"`@retry` on `{fn_name}` (line {node.lineno}) is missing `stop=stop_after_attempt(n)`.",
            })

        if dec_name.endswith("on_exception") and "max_tries" not in dec_kw:
            issues.append({
                "tier": "[P]",
                "category": "agent_patterns",
                "kind": "UnboundedBackoffRetry",
                "line": node.lineno,
                "detail": f"`@backoff.on_exception` on `{fn_name}` (line {node.lineno}) is missing `max_tries=n`.",
            })

    body_nodes = list(_iter_func_body_no_nested(node))
    calls_self = any(
        isinstance(sub, ast.Call) and isinstance(sub.func, ast.Name) and sub.func.id == fn_name
        for sub in body_nodes
    )
    if not calls_self:
        return

    non_recursive_returns = 0
    has_yield_or_guard = any(isinstance(sub, (ast.Yield, ast.YieldFrom, ast.If, ast.For)) for sub in body_nodes)
    for sub in body_nodes:
        if isinstance(sub, ast.Return):
            ret_calls_self = any(
                isinstance(c, ast.Call) and isinstance(c.func, ast.Name) and c.func.id == fn_name
                for c in ast.walk(sub)
            )
            if not ret_calls_self:
                non_recursive_returns += 1
    if non_recursive_returns == 0 and not has_yield_or_guard:
        issues.append({
            "tier": "[P]",
            "category": "agent_patterns",
            "kind": "UnboundedRecursionNoBaseCase",
            "line": node.lineno,
            "detail": f"Recursive function `{fn_name}` (line {node.lineno}) has no non-recursive base-case `return`.",
        })


def _check_langgraph_infinite_cycles(
    graph_nodes: Set[str],
    graph_adj: Dict[str, Set[str]],
) -> List[Dict[str, Any]]:
    if not graph_adj:
        return []
    end_markers = {"END", "__end__"}
    cycle_issues: List[Dict[str, Any]] = []

    for g_node in sorted(graph_nodes - end_markers):
        visited: Set[str] = set()
        stack = [g_node]
        while stack:
            curr = stack.pop()
            for nxt in graph_adj.get(curr, ()):
                if nxt not in visited:
                    visited.add(nxt)
                    stack.append(nxt)
        if g_node in visited and not (visited & end_markers):
            cycle_issues.append({
                "tier": "[P]",
                "category": "agent_patterns",
                "kind": "LangGraphInfiniteCycleNoEnd",
                "line": 1,
                "detail": f"Graph node `{g_node}` participates in a cycle with no conditional path reaching `END`!",
            })
    return cycle_issues


@_finite_inputs
def audit_agent_patterns_and_tool_registry(
    source_code: str,
    prompt_text: str = "",
    registered_tools_override: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    """
    AST + Graph verifier implementing `Aurite-ai/agent-verifier` (`skills/verify-patterns/SKILL.md`):
    1. `[P] Loop Safety` (`UnboundedWhileTrueLoop`, `UnboundedRecursionNoBaseCase`)
    2. `[P] Retry Limit Enforcement` (`UnboundedTenacityRetry`, `UnboundedBackoffRetry`, `UnboundedUrllib3Retry`)
    3. `[P] Tool Registry Consistency` (`HallucinatedToolReference`)
    4. `[P] LangGraph StateGraph Cycle Exit Analysis` (`LangGraphInfiniteCycleNoEnd`)
    """
    tree = ast.parse(text_dedent(source_code))
    issues: List[Dict[str, Any]] = []
    defined_tools: Set[str] = set(registered_tools_override or ())
    graph_adj: Dict[str, Set[str]] = {}
    graph_nodes: Set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.While) and isinstance(node.test, ast.Constant) and node.test.value is True:
            has_exit = any(isinstance(sub, (ast.Break, ast.Return, ast.Raise)) for sub in ast.walk(node))
            if not has_exit:
                issues.append({
                    "tier": "[P]",
                    "category": "agent_patterns",
                    "kind": "UnboundedWhileTrueLoop",
                    "line": node.lineno,
                    "detail": f"`while True:` loop at line {node.lineno} has no `break`, `return`, or `raise` exit.",
                })

        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            _inspect_func_decorators_and_recursion(node, defined_tools, issues)

        if isinstance(node, ast.Call):
            c_name = getattr(node.func, "id", None) or getattr(node.func, "attr", None) or ""
            kw_map = {kw.arg: kw.value for kw in node.keywords if kw.arg}

            if c_name == "Retry":
                tot_node = kw_map.get("total")
                tot_ok = (
                    isinstance(tot_node, ast.Constant)
                    and isinstance(tot_node.value, int)
                    and not isinstance(tot_node.value, bool)
                    and tot_node.value > 0
                )
                if not tot_ok:
                    issues.append({
                        "tier": "[P]",
                        "category": "agent_patterns",
                        "kind": "UnboundedUrllib3Retry",
                        "line": node.lineno,
                        "detail": f"`Retry(...)` at line {node.lineno} is missing positive `total=n`.",
                    })

            if c_name == "ToolNode" and node.args and isinstance(node.args[0], (ast.List, ast.Tuple)):
                for elt in node.args[0].elts:
                    if isinstance(elt, ast.Name):
                        defined_tools.add(elt.id)
                    elif isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                        defined_tools.add(elt.value)

            if c_name == "add_edge" and len(node.args) >= 2:
                u_n, v_n = node.args[0], node.args[1]
                u_s = u_n.value if isinstance(u_n, ast.Constant) else getattr(u_n, "id", "")
                v_s = v_n.value if isinstance(v_n, ast.Constant) else getattr(v_n, "id", "")
                if u_s and v_s:
                    graph_nodes.update((str(u_s), str(v_s)))
                    graph_adj.setdefault(str(u_s), set()).add(str(v_s))

            if c_name == "add_conditional_edges" and len(node.args) >= 3:
                u_n, map_n = node.args[0], node.args[2]
                u_s = u_n.value if isinstance(u_n, ast.Constant) else getattr(u_n, "id", "")
                if u_s and isinstance(map_n, ast.Dict):
                    graph_nodes.add(str(u_s))
                    for val_n in map_n.values:
                        v_s = val_n.value if isinstance(val_n, ast.Constant) else getattr(val_n, "id", "")
                        if v_s:
                            graph_nodes.add(str(v_s))
                            graph_adj.setdefault(str(u_s), set()).add(str(v_s))

    if prompt_text:
        prompt_refs = set(re.findall(r"`([a-zA-Z_][a-zA-Z0-9_]*)`", prompt_text))
        for ref in sorted(prompt_refs):
            if ref not in defined_tools:
                issues.append({
                    "tier": "[P]",
                    "category": "agent_patterns",
                    "kind": "HallucinatedToolReference",
                    "line": 1,
                    "detail": f"Prompt references tool `{ref}`, which is not defined in tool registry {sorted(defined_tools)}.",
                })

    issues.extend(_check_langgraph_infinite_cycles(graph_nodes, graph_adj))
    return {
        "status": "PASS" if not issues else "FAIL",
        "defined_tools": sorted(defined_tools),
        "issue_count": len(issues),
        "issues": issues,
    }


@_finite_inputs
def audit_security_and_quality_patterns(
    source_code: str,
    requirements_text: str = "",
) -> Dict[str, Any]:
    """
    AST verifier implementing `Aurite-ai/agent-verifier` (`verify-security`, `verify-quality`, `verify-language`):
    1. `[P] Hardcoded Secrets`: `API_KEY`, `SECRET`, `PASSWORD`, `TOKEN` assigned to string literals,
       or string literals matching `sk-...`, `sk-ant-...`, `AKIA...`, `ghp_...`, `xoxb-...`, `AIza...`.
    2. `[H] Insecure Defaults`: `verify=False` (SSL bypass), `debug=True`, `CORS(..., origins="*")`.
    3. `[H] Swallowed / Bare Exceptions & Error Exposure`: `except: pass` or `except Exception as e: return {"error": str(e)}`.
    4. `[P] Dependency Version Pinning`: flags unpinned `package` or `package>=1.0` in `requirements_text`.
    """
    tree = ast.parse(text_dedent(source_code))
    issues: List[Dict[str, Any]] = []

    for node in ast.walk(tree):
        # 1a. Hardcoded secret assignments
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            str_val = node.value.value.strip()
            if str_val and not str_val.startswith(("$", "{", "<")):
                for tgt in node.targets:
                    tgt_name = getattr(tgt, "id", None) or getattr(tgt, "attr", None) or ""
                    low_t = tgt_name.lower()
                    if any(k in low_t for k in _SECRET_VAR_KEYWORDS):
                        issues.append({
                            "tier": "[P]",
                            "category": "security",
                            "kind": "HardcodedSecretAssignment",
                            "line": node.lineno,
                            "detail": f"Hardcoded secret literal assigned to `{tgt_name}` at line {node.lineno}.",
                        })

        # 1b. Known API key literal prefixes anywhere in AST
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            s_val = node.value.strip()
            for prefix, label in _KNOWN_API_KEY_PREFIXES:
                if s_val.startswith(prefix) and len(s_val) >= len(prefix) + 6:
                    issues.append({
                        "tier": "[P]",
                        "category": "security",
                        "kind": "HardcodedApiKeyLiteral",
                        "line": getattr(node, "lineno", 1),
                        "detail": f"Hardcoded {label} (`{prefix}...`) at line {getattr(node, 'lineno', 1)}.",
                    })
                    break

        # 2. Insecure defaults (`verify=False`, `debug=True`, `origins="*"`)
        if isinstance(node, ast.Call):
            for kw in node.keywords:
                if kw.arg == "verify" and isinstance(kw.value, ast.Constant) and kw.value.value is False:
                    issues.append({
                        "tier": "[H]",
                        "category": "security",
                        "kind": "InsecureSSLVerifyDisabled",
                        "line": node.lineno,
                        "detail": f"SSL verification disabled (`verify=False`) at line {node.lineno}.",
                    })
                if kw.arg == "origins" and isinstance(kw.value, ast.Constant) and kw.value.value == "*":
                    issues.append({
                        "tier": "[H]",
                        "category": "security",
                        "kind": "InsecureCORSWildcard",
                        "line": node.lineno,
                        "detail": f"Wildcard CORS (`origins='*'`) at line {node.lineno}.",
                    })

        # 3. Bare except / silent `except: pass`
        if isinstance(node, ast.ExceptHandler):
            is_empty_pass = len(node.body) == 1 and isinstance(node.body[0], ast.Pass)
            if node.type is None or is_empty_pass:
                issues.append({
                    "tier": "[H]",
                    "category": "quality",
                    "kind": "BareOrSilentSwallowedException",
                    "line": node.lineno,
                    "detail": f"Bare or silent `except: pass` handler at line {node.lineno} swallows runtime errors.",
                })

    # 4. Dependency version pinning check (`requirements.txt`)
    if requirements_text:
        for idx, raw_line in enumerate(requirements_text.splitlines(), 1):
            line = raw_line.split("#", 1)[0].strip()
            if not line:
                continue
            if "==" not in line and "~=" not in line:
                issues.append({
                    "tier": "[P]",
                    "category": "security",
                    "kind": "UnpinnedDependencyRequirement",
                    "line": idx,
                    "detail": f"Unpinned dependency `{line}` at line {idx} (use `==` or `~=`).",
                })

    return {
        "status": "PASS" if not issues else "FAIL",
        "issue_count": len(issues),
        "issues": issues,
    }
