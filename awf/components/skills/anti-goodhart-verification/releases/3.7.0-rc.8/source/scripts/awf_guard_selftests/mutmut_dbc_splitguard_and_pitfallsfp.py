"""AWF Guard mutmut dbc splitguard and pitfallsfp: cohesive definitions behind the compatibility interface."""
from __future__ import annotations

from typing import Any
from typing import Callable
from typing import Dict
from typing import Tuple
from awf_universal_anti_goodhart_gates import audit_splitguard_row_and_group_leakage
from awf_universal_anti_goodhart_gates import evaluate_ast_mutation_kill_rate
from awf_universal_anti_goodhart_gates import evaluate_mca_and_precision_downgrade_stability
import numpy as np
from awf_universal_anti_goodhart_gates import scan_ast_for_floating_point_pitfalls
from awf_universal_anti_goodhart_gates import scan_ast_for_loose_tolerance_inflation
from awf_universal_anti_goodhart_gates import verify_pure_input_immutability_and_contracts


def _verify_mutmut_dbc_splitguard_and_pitfallsfp_selftests(
    r_grid: np.ndarray,
    f_vals: np.ndarray,
    compute_shell_area: Callable[..., Any],
    fast_spherical_integral: Callable[..., Any],
    slow_textbook_oracle: Callable[..., Any],
) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    loose_tol_src = (
        "def test_watered_down_tol():\n"
        "    assert np.allclose(pred, ref, atol=10.0, rtol=0.5)\n"
        "    self.assertAlmostEqual(a, b, places=0)\n"
    )
    assert len(scan_ast_for_loose_tolerance_inflation(loose_tol_src)) == 3

    weak_mut = evaluate_ast_mutation_kill_rate(
        fn_or_source=fast_spherical_integral,
        assertion_check_fn=lambda cand_fn: len(cand_fn(r_grid, f_vals, True)) == len(r_grid),
        extra_globals={"compute_shell_area": compute_shell_area, "np": np},
        min_kill_rate=0.80,
    )
    assert weak_mut["status"] == "FAIL" and weak_mut["kill_rate"] < 0.50

    ref_masked = slow_textbook_oracle(r_grid, f_vals, True)
    ref_unmasked = slow_textbook_oracle(r_grid, f_vals, False)
    mut_clean_spec = {
        "fn_or_source": fast_spherical_integral,
        "assertion_check_fn": lambda cand_fn: (
            bool(np.allclose(cand_fn(r_grid, f_vals, True), ref_masked, rtol=1e-7, atol=1e-9))
            and bool(np.allclose(cand_fn(r_grid, f_vals, False), ref_unmasked, rtol=1e-7, atol=1e-9))
        ),
        "extra_globals": {"compute_shell_area": compute_shell_area, "np": np},
        "min_kill_rate": 0.85,
    }

    def _impure_inplace_mutator(r: np.ndarray, f: np.ndarray, use_mask: bool = True) -> np.ndarray:
        f[0] = 999999.0
        return fast_spherical_integral(r=r, f=f, use_mask=use_mask)

    dbc_bad = verify_pure_input_immutability_and_contracts(
        target_fn=_impure_inplace_mutator,
        sample_input_kwargs={"r": r_grid.copy(), "f": f_vals.copy(), "use_mask": True},
    )
    assert dbc_bad["status"] == "FAIL" and "primary:f" in dbc_bad["mutated_inputs"]

    dbc_clean_spec = {
        "pre_fn": lambda kw: len(kw["r"]) == len(kw["f"]) and len(kw["r"]) >= 2,
        "post_fn": lambda kw, res, old_kw: (
            res.shape == old_kw["r"].shape
            and (not old_kw.get("use_mask", True) or bool(np.all(res[old_kw["r"] < 0.5] == 0.0)))
        ),
        "adversarial_inputs": [
            {"r": np.linspace(0.1, 0.49, 6), "f": np.ones(6), "use_mask": True},
            {"r": np.linspace(0.5, 5.0, 6), "f": np.zeros(6), "use_mask": True},
            {"r": np.linspace(0.5, 5.0, 6), "f": np.full(6, 1e-12), "use_mask": False},
        ],
    }

    X_full = np.arange(20, dtype=np.float64).reshape(10, 2)
    sg_bad = audit_splitguard_row_and_group_leakage(
        train_X=X_full[:7],
        test_X=X_full[6:],
        fitted_arrays=[X_full, X_full[6:]],
        train_groups=["mol_A", "mol_A", "mol_B", "mol_B", "mol_C", "mol_C", "mol_D"],
        test_groups=["mol_D", "mol_E", "mol_E", "mol_F"],
        pipeline_source_code="X_s = scaler.fit_transform(X_all)\nX_tr, X_te = train_test_split(X_s)\npca.fit(X_te)\n",
    )
    assert sg_bad["status"] == "FAIL" and {"duplicate_row_leakage", "fit_before_split", "fit_after_split", "group_leakage"} <= {
        e["kind"] for e in sg_bad["runtime_leakage_events"]
    }
    sg_clean_spec = {
        "train_X": X_full[:6],
        "test_X": X_full[6:],
        "fitted_arrays": [X_full[:6]],
        "train_groups": ["mol_A", "mol_A", "mol_B", "mol_B", "mol_C", "mol_C"],
        "test_groups": ["mol_D", "mol_D", "mol_E", "mol_F"],
        "pipeline_source_code": (
            "X_train, X_test = train_test_split(X_all)\n"
            "X_train_s = scaler.fit_transform(X_train)\n"
            "X_test_s = scaler.transform(X_test)\n"
        ),
    }

    fp_bad_src = (
        "def unstable_solver(A, b, x):\n"
        "    w = np.linalg.inv(A) @ b\n"
        "    lse = np.log(np.sum(np.exp(x)))\n"
        "    return w + lse + np.log(1.0 + x) + (np.exp(x) - 1.0)\n"
    )
    assert len(scan_ast_for_floating_point_pitfalls(fp_bad_src)) == 4

    def _catastrophic_cancellation_fn(r: np.ndarray, f: np.ndarray, use_mask: bool = True) -> np.ndarray:
        idx = np.arange(len(r), dtype=np.float64)
        return f + 1e6 * (r - (r[0] + idx * (r[1] - r[0])))

    mca_bad = evaluate_mca_and_precision_downgrade_stability(
        target_fn=_catastrophic_cancellation_fn,
        sample_input_kwargs={"r": r_grid, "f": f_vals, "use_mask": True},
        max_allowed_rel_drift=1e-4,
        max_condition_number=100.0,
    )
    assert mca_bad["status"] == "FAIL" and mca_bad["empirical_condition_number"] > 1000.0

    mca_clean_spec = {
        "n_mca_trials": 8,
        "relative_noise_sigma": 1e-7,
        "max_allowed_rel_drift": 1e-5,
        "max_condition_number": 50.0,
    }
    return mut_clean_spec, dbc_clean_spec, sg_clean_spec, mca_clean_spec
