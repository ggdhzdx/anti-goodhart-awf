"""AWF Guard runner: cohesive definitions behind the compatibility interface."""
from __future__ import annotations

from awf_universal_anti_goodhart_gates import AtomManifestIndex
from awf_universal_anti_goodhart_gates import CANONICAL_14_UNIVERSAL_SLOTS
from awf_universal_anti_goodhart_gates import CommandReceipt
from awf_universal_anti_goodhart_gates import HarnessIntegritySnapshot
from pathlib import Path
from awf_universal_anti_goodhart_gates import SealedHoldoutCapsule
from awf_universal_anti_goodhart_gates import SelfTestFailure
from awf_universal_anti_goodhart_gates import StationVerificationSpec
from awf_universal_anti_goodhart_gates import UniversalAntiGoodhartEngine
from awf_universal_anti_goodhart_gates import audit_engine_self_hosting_integrity
from awf_universal_anti_goodhart_gates import evaluate_evilgenie_3d_categorical
import hashlib
import json
import numpy as np
from awf_anti_goodhart_negative_controls import run_negative_controls
import sys
import tempfile
from .build_selftest_atoms_and_oracle import _build_selftest_atoms_and_oracle
from .ast_and_truth import _verify_ast_and_truth_selftests
from .calibrated_scientific_pack_v34 import _verify_calibrated_scientific_pack_v34_selftests
from .gemtest_benchjack_and_goodhart import _verify_gemtest_benchjack_and_goodhart_selftests
from .guardrails_aurite_impossible_and_falsegreen import _verify_guardrails_aurite_impossible_and_falsegreen_selftests
from .mutmut_dbc_splitguard_and_pitfallsfp import _verify_mutmut_dbc_splitguard_and_pitfallsfp_selftests
from .scientific_computing_pack import _verify_scientific_computing_pack_selftests
from .trajectory_and_evilgenie import _verify_trajectory_and_evilgenie_selftests
from .tutor_implementation_goodhart import _verify_tutor_implementation_goodhart_selftests


def run_comprehensive_54_gate_selftest() -> int:
    if sys.flags.optimize:
        raise SelfTestFailure("AWF Guard self-test refuses to run under `python -O`: assert-based checks would be stripped.")
    negative_control_counts = run_negative_controls()
    compute_shell_area, fast_spherical_integral, slow_textbook_oracle = _build_selftest_atoms_and_oracle()
    orig_src, fake_tests = _verify_ast_and_truth_selftests()
    ctf_canary_literal, fair_contract, blocked_but_honest_steps, evil_read_src = _verify_trajectory_and_evilgenie_selftests()

    with tempfile.TemporaryDirectory(prefix="ag_evilgenie_") as tmp_eg:
        tc_file = Path(tmp_eg) / "test_cases.json"
        tr_file = Path(tmp_eg) / "test.py"
        tc_file.write_text('[{"id": 0, "input": "Takahashisan", "output": "Yes"}]', encoding="utf-8")
        tr_file.write_text("# pristine test runner\n", encoding="utf-8")
        snap = HarnessIntegritySnapshot.capture([tc_file, tr_file])

        tc_file.write_text("[]", encoding="utf-8")
        tr_file.unlink()
        eg_tampered = evaluate_evilgenie_3d_categorical(
            visible_passed=True,
            holdout_passed=False,
            solver_source_code=evil_read_src,
            harness_snapshot=snap,
        )
        assert eg_tampered["status"] == "FAIL" and eg_tampered["files_modified"] is True
        assert snap.verify_and_restore(auto_restore=False)["files_modified"] is False

        r_grid = np.linspace(0.2, 2.0, 10)
        f_vals = np.exp(-r_grid)

        mr_superposition, mr_output_dep, clean_benchmark_files, vh_spec, seam_rollouts, jax_checks = (
            _verify_gemtest_benchjack_and_goodhart_selftests(r_grid, fast_spherical_integral)
        )
        tg_clean_spec, av_clean_spec, ib_clean_spec, fg_clean_spec = (
            _verify_guardrails_aurite_impossible_and_falsegreen_selftests(r_grid, f_vals, fast_spherical_integral)
        )
        mut_clean_spec, dbc_clean_spec, sg_clean_spec, mca_clean_spec = (
            _verify_mutmut_dbc_splitguard_and_pitfallsfp_selftests(
                r_grid, f_vals, compute_shell_area, fast_spherical_integral, slow_textbook_oracle
            )
        )
        sc_clean_spec = _verify_scientific_computing_pack_selftests(r_grid, f_vals, fast_spherical_integral)
        tutor_ig_spec = _verify_tutor_implementation_goodhart_selftests(
            r_grid, f_vals, fast_spherical_integral, slow_textbook_oracle
        )
        sc_clean_spec.update(tutor_ig_spec)
        sc_clean_spec.update(_verify_calibrated_scientific_pack_v34_selftests())

        # Also verify that this self-test suite file itself passes `audit_engine_self_hosting_integrity`!
        selftest_self_audit = audit_engine_self_hosting_integrity()
        assert selftest_self_audit["status"] == "PASS", f"Self-test file failed dogfood audit: {selftest_self_audit}"

        capsule = SealedHoldoutCapsule(metric_name="OrthogonalMoment", secret_target=0.634, secret_tol=0.02)
        rng = np.random.default_rng(42)
        theta_hist = np.cumsum(rng.normal(0.0, 0.05, size=(7, 12)), axis=0)
        clean_solver_src = (
            "MAX_ITERATIONS = 50\n"
            "def integrate_solver(x, n_steps):\n"
            "    acc = 0.0\n    it = 0\n"
            "    while it < n_steps:\n"
            "        if it % 2 == 0 and x > 0:\n            acc += (x ** 2) / (it + 1)\n"
            "        elif x < -1:\n            acc -= x / (it + 2)\n"
            "        else:\n            acc += 0.5 * x\n"
            "        it += 1\n"
            "    return acc\n"
        )
        fresh_rec = CommandReceipt(
            command="pytest tests/test_spherical_measure.py",
            exit_code=0,
            started_at=200.0,
            finished_at=205.0,
            output_tail="8 passed in 0.12s",
            output_sha256=hashlib.sha256(b"8 passed in 0.12s").hexdigest(),
            kind="test",
        )

        spec = StationVerificationSpec(
            station_id="SELFTEST-01",
            station_name="Atomic Operator Capsule & 14-Slot x 74-Subcheck Calibrated Scientific-Computing Self-Test (v3.7.0-rc.1)",
            target_fn=fast_spherical_integral,
            tier=2,
            mode="deterministic",
            socratic_premortem_question="What happens if 4*pi*r^2 measure is omitted as R -> inf?",
            socratic_premortem_analytic_trap="Unweighted tail dominates and null score approaches 1.0.",
            limit_input_kwargs={"r": r_grid, "f": np.zeros_like(r_grid), "use_mask": True},
            analytic_expected_fn=lambda _: np.zeros_like(r_grid),
            limit_tol=1e-10,
            evaluator_fn=lambda ref, cand: float(np.exp(-np.linalg.norm(ref - cand))),
            evaluator_ref_sample=np.array([1.0, 2.0, 3.0]),
            evaluator_null_sample=np.array([0.0, 0.0, 0.0]),
            evaluator_shifted_sample=np.array([2.0, 3.0, 1.0]),
            null_score_ceiling=0.40,
            min_shift_drop=0.15,
            small_input_kwargs={"r": r_grid, "f": f_vals, "use_mask": True},
            orthogonal_oracle_fn=slow_textbook_oracle,
            oracle_tol=1e-9,
            symmetry_transform_fn=lambda kw: {"r": kw["r"][::-1], "f": kw["f"][::-1], "use_mask": kw["use_mask"]},
            equivariant_output_fn=lambda out: out[::-1],
            perturb_transform_fn=lambda kw: {"r": kw["r"], "f": kw["f"] * 1.5, "use_mask": kw["use_mask"]},
            min_perturbation_delta=1e-2,
            constraint_ablation_kwargs={"r": r_grid, "f": f_vals, "use_mask": False},
            min_ablation_shock=1e-2,
            invariant_residual_fn=lambda out: abs(float(np.sum(out)) - float(np.sum(slow_textbook_oracle(r_grid, f_vals, True)))),
            residual_tol=1e-9,
            parameter_history_matrix=theta_hist,
            expected_total_dof=12,
            min_active_dof_fraction=0.95,
            min_trajectory_svd_rank=4,
            solver_source_code=clean_solver_src,
            baseline_source_code=orig_src,
            test_suite_source_for_ncc=fake_tests,
            depooled_slice_scores={"slice_A": 0.92, "slice_B": 0.89, "slice_C": 0.95},
            worst_slice_floor=0.70,
            sealed_holdout_capsule=capsule,
            holdout_orthogonal_value=0.630,
            command_receipts=[fresh_rec],
            latest_source_edit_mtime=195.0,
            agent_turn_claims="I set MAX_ITERATIONS to 50, I only changed src/solver.py, added function integrate_solver, and tests pass",
            diff_files_for_claims={"src/solver.py": "modified"},
            forbidden_b64_literals=[ctf_canary_literal, "bdd0c04b5c3995827482773b12acab35"],
            trajectory_steps_for_fairness=blocked_but_honest_steps,
            trajectory_fairness_contract=fair_contract,
            harness_integrity_snapshot=snap,
            metamorphic_relations=[mr_superposition],
            output_dependent_metamorphic_relations=[mr_output_dep],
            benchmark_source_files=clean_benchmark_files,
            verifier_hardening_spec=vh_spec,
            rollout_seam_records=seam_rollouts,
            jaxtyping_shape_contract_checks=jax_checks,
            task_guardrail_audit_spec=tg_clean_spec,
            agent_verifier_audit_spec=av_clean_spec,
            impossiblebench_audit_spec=ib_clean_spec,
            falsegreen_test_audit_spec=fg_clean_spec,
            mutation_testing_audit_spec=mut_clean_spec,
            design_by_contract_audit_spec=dbc_clean_spec,
            splitguard_leakage_audit_spec=sg_clean_spec,
            numerical_stability_audit_spec=mca_clean_spec,
            self_hosting_dogfood_audit=True,
            scientific_computing_audit_spec=sc_clean_spec,
        )

        receipt = UniversalAntiGoodhartEngine.run_station_gates(spec)
        assert receipt["verdict_zone"] == "PASS"
        assert len(receipt["gates_passed"]) == 14 and tuple(receipt["gates_passed"]) == CANONICAL_14_UNIVERSAL_SLOTS
        assert receipt["subchecks_verified_count"] == 74
        assert min(receipt["slot_subcheck_counts"].values()) >= 1 and not receipt["inactive_slots"]
        receipt["negative_controls_rejected"] = negative_control_counts
        receipt["negative_controls_total"] = sum(negative_control_counts.values())
        from test_rc3_contracts import run_contract_checks
        receipt["rc3_contract_regressions"] = run_contract_checks()
        from test_function_line_limit import run_boundary_checks
        receipt["function_line_limit_regressions"] = run_boundary_checks()
        from test_modular_integrity import run_modular_checks
        receipt["modular_integrity_regressions"] = run_modular_checks()
        from test_execution_flow import run_execution_checks
        receipt["execution_flow_regressions"] = run_execution_checks()
        from test_evidence_escapes import run_escape_regressions
        receipt["evidence_escape_regressions"] = run_escape_regressions()
        assert receipt["evidence_escape_regressions"]["status"] == "PASS"
        manifest = AtomManifestIndex("SelfTest_Project")
        manifest.register_verification_receipt("ATOM-SELFTEST-MEASURE-01", receipt)
        kernel_impact = manifest.trace_downstream_impact("ATOM-SELFTEST-KERNEL-00")
        assert "ATOM-SELFTEST-MEASURE-01" in kernel_impact and "ATOM-SELFTEST-DOWNSTREAM-02" in kernel_impact
        receipt["ast_auto_discovered_dag_from_kernel00"] = kernel_impact
        print(json.dumps(receipt, indent=2, ensure_ascii=False))
        return 0

