"""
AWF Tutor Pedagogical Anti-Goodhart Guards (`skill.design-anti-goodhart@1.0.0-rc.24`).

Closes three Tutor-Driven Co-Design (`TDD`) & pedagogical loopholes:
1. `verify_wittgenstein_ladder_structure`: blocks hollow 1-sentence analogy strings (`len >= 10` loophole)
   by requiring explicit 3-step `Bridge -> Deconstruct -> Replace` structure AND explicit breakdown/failure
   semantics in `Deconstruct` (where macroscopic analogy fails at molecular/statistical/quantum scale).
2. `verify_seven_element_anatomy`: validates structured 7-element methodological anatomy when present or
   required, enforcing quantitative/mathematical operator presence in `mathematical_formulation`.
3. `verify_tdd_teach_on_miss_closure`: when the learner misses or answers uncertain/unknown in `TDD` mode,
   enforces substantive Wittgenstein `Teach-on-Miss` explanation PLUS a concrete deductive isomorphic
   re-grill question (`?`), rejecting rubber-stamp questions such as "听懂了吗？".
"""

from __future__ import annotations

import re
from typing import Any, Dict, List

MIN_BRIDGE_CHARS = 6
MIN_DECONSTRUCT_CHARS = 8
MIN_REPLACE_CHARS = 8
MIN_ANATOMY_ITEM_CHARS = 8
MIN_TEACH_EXPLANATION_CHARS = 20
MIN_REGRILL_QUESTION_CHARS = 12
STAGE_BRIDGE_GROUP = 1
STAGE_DECONSTRUCT_GROUP = 2
STAGE_REPLACE_GROUP = 3

REQUIRED_ANATOMY_KEYS = (
    "principle_and_logic",
    "physical_picture",
    "mathematical_formulation",
    "scope_and_boundary",
    "pros_and_cons",
    "alternatives_comparison",
    "concrete_evidence_or_implementation",
)

MISSED_RESPONSE_STATES = frozenset({"MISSED", "UNCERTAIN", "UNKNOWN", "不知道", "不会"})

WITTGENSTEIN_LADDER_3STEP_RE = re.compile(
    r"(?is)(?:bridge|搭梯)\s*[:：](.+?)(?:->|→|\||;|\n)\s*(?:deconstruct|拆梯)\s*[:：](.+?)(?:->|→|\||;|\n)\s*(?:replace|换真格)\s*[:：](.+)"
)

DECONSTRUCT_BREAKDOWN_RE = re.compile(
    r"(?:失效|谬误|忽略|违背|局限|不存在|不同|无法|不能|禁阻|边界|破缺|假象|错位|并非|不是|盲区|误导|分布|fails?|breaks?|ignores?|violates?|unlike|invalid|mismatch|boundary|forbidden)",
    re.IGNORECASE,
)

MATH_OPERATOR_RE = re.compile(r"(?:[=<>≤≥≠∝±×÷∑∫√]|\\frac|\\Delta|Δ|\bln\b|\bexp\b|/|\^)")

RUBBER_STAMP_REGRILL_RE = re.compile(
    r"(?:听懂了吗|明白了吗|清楚了吗|懂了吗|看懂了吗|有问题吗|对不对\s*[?？]?$|do you understand)",
    re.IGNORECASE,
)


def _extract_ladder_stages(ladder_value: Any) -> Dict[str, str]:
    if isinstance(ladder_value, dict):
        bridge = str(ladder_value.get("bridge") or ladder_value.get("bridge_analogy") or "").strip()
        deconstruct = str(ladder_value.get("deconstruct") or ladder_value.get("deconstruct_breakdown") or "").strip()
        replace = str(ladder_value.get("replace") or ladder_value.get("rigorous_replacement") or "").strip()
        return {"bridge": bridge, "deconstruct": deconstruct, "replace": replace}

    raw_text = str(ladder_value or "").strip()
    match = WITTGENSTEIN_LADDER_3STEP_RE.search(raw_text)
    if not match:
        return {}
    return {
        "bridge": match.group(STAGE_BRIDGE_GROUP).strip(),
        "deconstruct": match.group(STAGE_DECONSTRUCT_GROUP).strip(),
        "replace": match.group(STAGE_REPLACE_GROUP).strip(),
    }


def verify_wittgenstein_ladder_structure(ladder_value: Any) -> Dict[str, Any]:
    """Require authentic 3-stage `Bridge -> Deconstruct -> Replace` content with breakdown semantics."""
    issues: List[str] = []
    stages = _extract_ladder_stages(ladder_value)
    if not stages:
        return {
            "gate": "D16_Wittgenstein_Ladder_3Step",
            "passed": False,
            "issues": [
                "wittgenstein_ladder must explicitly contain all 3 steps "
                "(`Bridge/搭梯 -> Deconstruct/拆梯 -> Replace/换真格`); hollow single-sentence analogies are forbidden"
            ],
        }

    bridge = stages["bridge"]
    deconstruct = stages["deconstruct"]
    replace = stages["replace"]

    if len(bridge) < MIN_BRIDGE_CHARS:
        issues.append(f"wittgenstein_ladder.bridge too short (< {MIN_BRIDGE_CHARS} chars)")
    if len(deconstruct) < MIN_DECONSTRUCT_CHARS:
        issues.append(f"wittgenstein_ladder.deconstruct too short (< {MIN_DECONSTRUCT_CHARS} chars)")
    elif not DECONSTRUCT_BREAKDOWN_RE.search(deconstruct):
        issues.append(
            "wittgenstein_ladder.deconstruct must explicitly explain where the everyday analogy breaks down or fails at the true scale"
        )
    if len(replace) < MIN_REPLACE_CHARS:
        issues.append(f"wittgenstein_ladder.replace too short (< {MIN_REPLACE_CHARS} chars)")

    return {
        "gate": "D16_Wittgenstein_Ladder_3Step",
        "passed": len(issues) == 0,
        "issues": issues,
    }


def verify_seven_element_anatomy(
    anatomy_value: Any,
    require_anatomy: bool = False,
) -> Dict[str, Any]:
    """Validate optional/required 7-element methodological anatomy and quantitative operator anchor."""
    if anatomy_value is None:
        if require_anatomy:
            return {
                "gate": "D16_Seven_Element_Anatomy",
                "passed": False,
                "checked": True,
                "issues": ["Missing required `seven_element_anatomy` dict on Tutor TDD station capsule"],
            }
        return {"gate": "D16_Seven_Element_Anatomy", "passed": True, "checked": False, "issues": []}

    if not isinstance(anatomy_value, dict):
        return {
            "gate": "D16_Seven_Element_Anatomy",
            "passed": False,
            "checked": True,
            "issues": ["`seven_element_anatomy` must be a dict containing all 7 canonical methodological dimensions"],
        }

    issues: List[str] = []
    for key in REQUIRED_ANATOMY_KEYS:
        val = str(anatomy_value.get(key, "")).strip()
        if len(val) < MIN_ANATOMY_ITEM_CHARS:
            issues.append(f"seven_element_anatomy.{key} missing or too short (< {MIN_ANATOMY_ITEM_CHARS} chars)")

    math_expr = str(anatomy_value.get("mathematical_formulation", "")).strip()
    if len(math_expr) >= MIN_ANATOMY_ITEM_CHARS and not MATH_OPERATOR_RE.search(math_expr):
        issues.append(
            "seven_element_anatomy.mathematical_formulation must contain an explicit equation/operator/ratio (`=`, `Δ`, `ln`, `/`)"
        )

    return {
        "gate": "D16_Seven_Element_Anatomy",
        "passed": len(issues) == 0,
        "checked": True,
        "issues": issues,
    }


def verify_tdd_teach_on_miss_closure(tdd_capsule: Dict[str, Any]) -> Dict[str, Any]:
    """Enforce substantive Wittgenstein Teach-on-Miss + non-rubber-stamp Re-Grill on miss/uncertainty."""
    raw_state = str(tdd_capsule.get("user_response_state", "")).strip().upper()
    triggered = bool(tdd_capsule.get("user_missed_or_uncertain", False)) or (raw_state in MISSED_RESPONSE_STATES)
    if not triggered:
        return {"gate": "D16_TDD_TeachOnMiss_Closure", "passed": True, "triggered": False, "issues": []}

    issues: List[str] = []
    closure = tdd_capsule.get("teach_on_miss_and_regrill_closure")
    if not isinstance(closure, dict):
        return {
            "gate": "D16_TDD_TeachOnMiss_Closure",
            "passed": False,
            "triggered": True,
            "issues": [
                "TDD miss/uncertainty (`user_missed_or_uncertain=true`) requires structured "
                "`teach_on_miss_and_regrill_closure` with `wittgenstein_teach_explanation` and `isomorphic_regrill_question`"
            ],
        }

    teach_exp = str(closure.get("wittgenstein_teach_explanation", "")).strip()
    regrill_q = str(closure.get("isomorphic_regrill_question", "")).strip()

    if len(teach_exp) < MIN_TEACH_EXPLANATION_CHARS:
        issues.append(
            f"teach_on_miss_and_regrill_closure.wittgenstein_teach_explanation too short (< {MIN_TEACH_EXPLANATION_CHARS} chars)"
        )
    if len(regrill_q) < MIN_REGRILL_QUESTION_CHARS or ("?" not in regrill_q and "？" not in regrill_q):
        issues.append(
            "teach_on_miss_and_regrill_closure.isomorphic_regrill_question must pose a deductive question (`?`/`？`, >= "
            f"{MIN_REGRILL_QUESTION_CHARS} chars)"
        )
    elif RUBBER_STAMP_REGRILL_RE.search(regrill_q):
        issues.append("teach_on_miss_and_regrill_closure forbids rubber-stamp prompts (`听懂了吗`/`明白了吗`)")

    return {
        "gate": "D16_TDD_TeachOnMiss_Closure",
        "passed": len(issues) == 0,
        "triggered": True,
        "issues": issues,
    }
