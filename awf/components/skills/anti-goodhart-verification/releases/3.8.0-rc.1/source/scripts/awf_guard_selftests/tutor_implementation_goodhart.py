"""AWF Guard tutor implementation goodhart: cohesive definitions behind the compatibility interface."""
from __future__ import annotations

from typing import Any
from typing import Callable
from typing import Dict
from awf_universal_anti_goodhart_gates import GLOBAL_ATOM_REGISTRY
from awf_universal_anti_goodhart_gates import evaluate_red_blue_adversarial_audit
import numpy as np
from awf_universal_anti_goodhart_gates import scan_source_for_todo_placeholders_and_magic_numbers
from awf_universal_anti_goodhart_gates import verify_microstep_granularity_and_topological_anchor


def _verify_tutor_implementation_goodhart_selftests(
    r_grid: np.ndarray,
    f_vals: np.ndarray,
    fast_spherical_integral: Callable[..., Any],
    slow_textbook_oracle: Callable[..., Any],
) -> Dict[str, Any]:
    # 1. Gate G5n: Static -inf Circuit-Breaker (Unfinished-Marker / Hollow-Body / NotImplemented / Magic-Float / Unused-Var)
    todo_tag = "TO" + "DO"
    lazy_shortcut_src = (
        f"def lazy_kernel(x):\n"
        f"    # {todo_tag}: replace with real solver\n"
        f"    unused_cache = x * 2.0\n"
        f"    return x * 0.739182\n"
        f"def hollow_stub(y):\n"
        f"    pass\n"
    )
    cb_bad = scan_source_for_todo_placeholders_and_magic_numbers(lazy_shortcut_src, check_magic_numbers=True)
    assert cb_bad["status"] == "FAIL" and cb_bad["effective_reward"] == -float("inf")
    cb_kinds = {f["kind"] for f in cb_bad["findings"]}
    assert "TodoOrPlaceholderComment" in cb_kinds
    assert "UnusedLocalVariableShortcut" in cb_kinds
    assert "UnexplainedMagicNumberLiteral" in cb_kinds
    assert "HollowStubFunctionBody" in cb_kinds

    clean_kernel_src = (
        "def clean_shell_kernel(r, f):\n"
        "    dr = abs(float(r[1] - r[0]))\n"
        "    area = 4.0 * 3.14159265 * (r ** 2)\n"
        "    return f * area * dr\n"
    )
    cb_good = scan_source_for_todo_placeholders_and_magic_numbers(clean_kernel_src, check_magic_numbers=True)
    assert cb_good["status"] == "PASS" and cb_good["effective_reward"] == 1.0

    # 2. Gate G6o: 6D Micro-Step Granularity & Topological 1-Hop Frontier Lock
    GLOBAL_ATOM_REGISTRY["ATOM-SELFTEST-KERNEL-00"]["gate_status"] = "REGISTERED"
    ms_unverified_parent = verify_microstep_granularity_and_topological_anchor(
        target_fn=fast_spherical_integral,
        mca_condition_number=5.89,
        invariant_anchor_count=4,
    )
    assert ms_unverified_parent["status"] == "FAIL" and ms_unverified_parent["unverified_hop_distance"] == 2
    GLOBAL_ATOM_REGISTRY["ATOM-SELFTEST-KERNEL-00"]["gate_status"] = "PASS"
    GLOBAL_ATOM_REGISTRY["ATOM-SELFTEST-KERNEL-00"]["last_verification_receipt"] = {"atom_id": "ATOM-SELFTEST-KERNEL-00", "verdict_zone": "PASS", "tier": 1, "gates_passed": ["fixture_upstream_contract"]}
    ms_good = verify_microstep_granularity_and_topological_anchor(
        target_fn=fast_spherical_integral,
        mca_condition_number=5.89,
        invariant_anchor_count=4,
    )
    assert ms_good["status"] == "PASS" and ms_good["unverified_hop_distance"] == 1

    # 3. Gate G7h: Red-Blue Adversarial Decoupled Game
    def surrogate_linear_approx(r: np.ndarray, f: np.ndarray, use_mask: bool = True) -> np.ndarray:
        return f * r * (1.0 if use_mask else 0.5)

    adv_probes = [
        {"r": r_grid, "f": f_vals, "use_mask": True},
        {"r": r_grid * 1.5, "f": np.sin(r_grid), "use_mask": True},
    ]
    rb_caught = evaluate_red_blue_adversarial_audit(
        target_fn=surrogate_linear_approx,
        reference_or_invariant_fn=slow_textbook_oracle,
        adversarial_probe_inputs=adv_probes,
        solver_source_code=lazy_shortcut_src,
        red_auditor_claimed_pass=False,
    )
    assert rb_caught["status"] == "FAIL"
    assert rb_caught["blue_builder_reward"] == -float("inf") and rb_caught["red_auditor_reward"] > 0.0

    rb_collusion = evaluate_red_blue_adversarial_audit(
        target_fn=surrogate_linear_approx,
        reference_or_invariant_fn=slow_textbook_oracle,
        adversarial_probe_inputs=adv_probes,
        solver_source_code=lazy_shortcut_src,
        red_auditor_claimed_pass=True,
    )
    assert rb_collusion["rubber_stamp_collusion"] is True and rb_collusion["red_auditor_reward"] == -float("inf")

    return {
        "circuit_breaker_spec": {
            "source_code": clean_kernel_src,
            "check_magic_numbers": True,
        },
        "microstep_anchor_spec": {
            "target_fn": fast_spherical_integral,
            "mca_condition_number": 5.89,
            "invariant_anchor_count": 4,
        },
        "red_blue_adversarial_spec": {
            "target_fn": fast_spherical_integral,
            "reference_or_invariant_fn": slow_textbook_oracle,
            "adversarial_probe_inputs": adv_probes,
            "solver_source_code": clean_kernel_src,
            "red_auditor_claimed_pass": True,
        },
    }
