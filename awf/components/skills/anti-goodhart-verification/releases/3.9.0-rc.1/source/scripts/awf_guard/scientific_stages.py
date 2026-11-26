"""AWF Guard: scientific stages."""
from __future__ import annotations

from typing import Any, Dict

from .declarative import evaluate_universal_declarative_slots
from .differential_checks import (
    verify_analytic_gradient_finite_difference,
    verify_asymptotic_convergence_order,
    verify_mesh_refinement_invariance_and_noise_floor,
)
from .errors import AntiGoodhartGateError
from .formal_chemistry import verify_stoichiometry_spin_and_wegscheider_smt
from .formal_numerics import (
    verify_arb_ball_enclosure_and_conditioning,
    verify_hypothesis_lie_group_and_boundary_shrinking,
)
from .geometry import (
    verify_euler_poincare_and_digital_duality,
    verify_filtration_monotonicity_and_heterogeneous_radius_clearance,
    verify_rp2_director_gauge_and_reciprocal_conjugacy,
)
from .keymaerax_ode_gate import verify_keymaerax_ode_invariants
from .lean_symbolic_gate import verify_lean4_symbolic_proof_and_inhabitation
from .matrix_checks import (
    verify_coupled_basis_sign_gauge_and_locality_bounds,
    verify_nonorthogonal_pencil_gauge_and_spectral_parity,
    verify_physical_matrix_invariants_and_unit_homogeneity,
)
from .model_physics_and_glue import (
    verify_crosstable_physical_inequality_bounds,
    verify_dynamic_feature_variance_and_noncollinearity,
    verify_subfragment_spin_and_siteslip_sensitivity,
    verify_unitcell_cyclic_shift_and_chain_convergence,
)
from .post_hoc_redteam import (
    audit_outer_glue_and_single_source_ast,
    verify_dual_entry_physics_redteam_audit,
)
from .remediation import (
    evaluate_red_blue_adversarial_audit,
    verify_microstep_granularity_and_topological_anchor,
    verify_remediation_closed_loop_and_pareto_candidates,
)
from .source_quality import scan_source_for_todo_placeholders_and_magic_numbers
from .station_spec import StationVerificationSpec
from .statistical_checks import (
    verify_bipolar_reachability_and_multisource_variance,
    verify_loocv_generalization_and_train_eval_parity,
    verify_weighted_dispersion_kish_and_scale_invariance,
)
from .symmetry_checks import (
    verify_pairwise_no_self_interaction_and_symmetry,
    verify_scale_homogeneity_and_rank1_null_calibration,
    verify_se3_pbc_and_permutation_equivariance,
)
from .tensor_contracts import verify_pint_dimensional_homogeneity


def _run_scientific_computing_pack_checks(spec: StationVerificationSpec, receipt: Dict[str, Any]) -> None:
    if spec.scientific_computing_audit_spec is None:
        return
    sc_spec = spec.scientific_computing_audit_spec
    if not sc_spec:
        raise AntiGoodhartGateError('[Scientific Computing Pack] `scientific_computing_audit_spec` cannot be empty when specified!')
    if 'gradient_fd_spec' in sc_spec and sc_spec['gradient_fd_spec'] is not None:
        fd_res = verify_analytic_gradient_finite_difference(**sc_spec['gradient_fd_spec'])
        if fd_res['status'] != 'PASS':
            raise AntiGoodhartGateError(f'[Gate 2b Analytic Gradient / Force vs Richardson Finite-Difference Failure] {fd_res}')
        receipt['gate2b_analytic_gradient_fd'] = fd_res
        receipt['gates_passed'].append('G2b_AnalyticGradient_FiniteDifference_Consistency')
    if 'convergence_order_spec' in sc_spec and sc_spec['convergence_order_spec'] is not None:
        co_res = verify_asymptotic_convergence_order(**sc_spec['convergence_order_spec'])
        if co_res['status'] != 'PASS':
            raise AntiGoodhartGateError(f'[Gate 1d Asymptotic Convergence Order O(h^p) Failure] {co_res}')
        receipt['gate1d_asymptotic_convergence_order'] = co_res
        receipt['gates_passed'].append('G1d_Asymptotic_Convergence_Order_Verification')
    if 'se3_pbc_perm_spec' in sc_spec and sc_spec['se3_pbc_perm_spec'] is not None:
        eq_res = verify_se3_pbc_and_permutation_equivariance(**sc_spec['se3_pbc_perm_spec'])
        if eq_res['status'] != 'PASS':
            raise AntiGoodhartGateError(f'[Gate 3i SE(3) / Triclinic PBC Minimum-Image / S_N Permutation Failure] {eq_res}')
        receipt['gate3i_se3_pbc_permutation'] = eq_res
        receipt['gates_passed'].append('G3i_SE3_PBC_MinimumImage_And_Permutation_Equivariance')
    if 'matrix_and_unit_spec' in sc_spec and sc_spec['matrix_and_unit_spec'] is not None:
        mu_res = verify_physical_matrix_invariants_and_unit_homogeneity(**sc_spec['matrix_and_unit_spec'])
        if mu_res['status'] != 'PASS':
            raise AntiGoodhartGateError(f'[Gate 5m Physical Matrix Hermitian/PSD/Detailed-Balance or Cross-Atom Unit Failure] {mu_res}')
        receipt['gate5m_matrix_and_unit_invariants'] = mu_res
        receipt['gates_passed'].append('G5m_PhysicalMatrix_Hermitian_PSD_And_DetailedBalance')
    if 'circuit_breaker_spec' in sc_spec and sc_spec['circuit_breaker_spec'] is not None:
        cb_res = scan_source_for_todo_placeholders_and_magic_numbers(**sc_spec['circuit_breaker_spec'])
        if cb_res['status'] != 'PASS':
            raise AntiGoodhartGateError(f'[Gate 5n Static -inf Circuit-Breaker Failure (TODO/Stub/MagicNumber/UnusedVar)] {cb_res}')
        receipt['gate5n_static_circuit_breaker'] = cb_res
        receipt['gates_passed'].append('G5n_Zero_Todo_Placeholder_Stub_And_MagicNumber_CircuitBreaker')
    if 'microstep_anchor_spec' in sc_spec and sc_spec['microstep_anchor_spec'] is not None:
        ms_res = verify_microstep_granularity_and_topological_anchor(**sc_spec['microstep_anchor_spec'])
        if ms_res['status'] != 'PASS':
            raise AntiGoodhartGateError(f'[Gate 6o 6D Micro-Step Granularity & Topological DAG Anchor Failure] {ms_res}')
        receipt['gate6o_microstep_topological_anchor'] = ms_res
        receipt['gates_passed'].append('G6o_MicroStep_Topological_DAG_And_Granularity_Anchor')
    if 'red_blue_adversarial_spec' in sc_spec and sc_spec['red_blue_adversarial_spec'] is not None:
        rb_res = evaluate_red_blue_adversarial_audit(**sc_spec['red_blue_adversarial_spec'])
        if rb_res['status'] != 'PASS':
            raise AntiGoodhartGateError(f'[Gate 7h Red-Blue Adversarial Decoupled Auditor Failure] {rb_res}')
        receipt['gate7h_red_blue_adversarial_audit'] = rb_res
        receipt['gates_passed'].append('G7h_RedBlue_Adversarial_Auditor_Decoupled_Game')
    _run_calibrated_scientific_invariant_checks(sc_spec, receipt)


def _run_calibrated_scientific_invariant_checks(sc_spec: Dict[str, Any], receipt: Dict[str, Any]) -> None:
    if 'pairwise_self_interaction_spec' in sc_spec and sc_spec['pairwise_self_interaction_spec'] is not None:
        pw_res = verify_pairwise_no_self_interaction_and_symmetry(**sc_spec['pairwise_self_interaction_spec'])
        if pw_res['status'] != 'PASS':
            raise AntiGoodhartGateError(f'[Gate 5o Pairwise Self-Interaction / Kernel Symmetry Failure] {pw_res}')
        receipt['gate5o_pairwise_no_self_interaction'] = pw_res
        receipt['gates_passed'].append('G5o_Pairwise_ZeroSelfInteraction_And_KernelSymmetry')
    if 'loocv_and_parity_spec' in sc_spec and sc_spec['loocv_and_parity_spec'] is not None:
        lp_res = verify_loocv_generalization_and_train_eval_parity(**sc_spec['loocv_and_parity_spec'])
        if lp_res['status'] != 'PASS':
            raise AntiGoodhartGateError(f'[Gate 7i LOOCV Out-of-Sample Generalization / Train-Eval Feature Parity Failure] {lp_res}')
        receipt['gate7i_loocv_and_train_eval_parity'] = lp_res
        receipt['gates_passed'].append('G7i_LOOCV_Generalization_And_TrainEval_FeatureParity')
    if 'scale_homogeneity_and_null_spec' in sc_spec and sc_spec['scale_homogeneity_and_null_spec'] is not None:
        sh_res = verify_scale_homogeneity_and_rank1_null_calibration(**sc_spec['scale_homogeneity_and_null_spec'])
        if sh_res['status'] != 'PASS':
            raise AntiGoodhartGateError(f'[Gate 3j Euler Scale Homogeneity / Asymmetric Rank-1 Null Calibration Failure] {sh_res}')
        receipt['gate3j_scale_homogeneity_and_null'] = sh_res
        receipt['gates_passed'].append('G3j_ScaleHomogeneity_And_AsymmetricRank1Null_ZeroPoint')
    if 'remediation_closed_loop_spec' in sc_spec and sc_spec['remediation_closed_loop_spec'] is not None:
        rc_res = verify_remediation_closed_loop_and_pareto_candidates(**sc_spec['remediation_closed_loop_spec'])
        if rc_res['status'] != 'PASS':
            raise AntiGoodhartGateError(f'[Gate 6p Remediation Closed-Loop / Pareto Selection / Human-Escalation Boundary] {rc_res}')
        receipt['gate6p_remediation_closed_loop'] = rc_res
        receipt['gates_passed'].append('G6p_Remediation_ClosedLoop_PairDiff_And_Pareto_Selection')
    if 'bipolar_and_variance_spec' in sc_spec and sc_spec['bipolar_and_variance_spec'] is not None:
        bv_res = verify_bipolar_reachability_and_multisource_variance(**sc_spec['bipolar_and_variance_spec'])
        if bv_res['status'] != 'PASS':
            raise AntiGoodhartGateError(f'[Gate 5p Bipolar Regime Reachability / Multi-Source Variance Propagation Failure] {bv_res}')
        receipt['gate5p_bipolar_and_variance'] = bv_res
        receipt['gates_passed'].append('G5p_BipolarSignReachability_And_MultiSource_VariancePropagation')
    if 'mesh_refinement_and_noise_spec' in sc_spec and sc_spec['mesh_refinement_and_noise_spec'] is not None:
        mr_res = verify_mesh_refinement_invariance_and_noise_floor(**sc_spec['mesh_refinement_and_noise_spec'])
        if mr_res['status'] != 'PASS':
            raise AntiGoodhartGateError(f'[Gate 1e Mesh-Refinement Intensive Invariance / Noise-Floor Amplification Failure] {mr_res}')
        receipt['gate1e_mesh_refinement_and_noise'] = mr_res
        receipt['gates_passed'].append('G1e_MeshRefinement_IntensiveInvariance_And_NoiseFloor_Stability')
    if 'euler_poincare_and_duality_spec' in sc_spec and sc_spec['euler_poincare_and_duality_spec'] is not None:
        ep_res = verify_euler_poincare_and_digital_duality(**sc_spec['euler_poincare_and_duality_spec'])
        if ep_res['status'] != 'PASS':
            raise AntiGoodhartGateError(f'[Gate 5q Euler-Poincare Homology / 6-vs-26 Digital Duality / Supercover Failure] {ep_res}')
        receipt['gate5q_euler_poincare_and_duality'] = ep_res
        receipt['gates_passed'].append('G5q_EulerPoincare_DigitalDuality_And_1DSupercoverHomotopy')
    _run_calibrated_diffraction_quantum_and_slot_checks(sc_spec, receipt)


def _run_calibrated_diffraction_quantum_and_slot_checks(sc_spec: Dict[str, Any], receipt: Dict[str, Any]) -> None:
    if 'filtration_and_radius_clearance_spec' in sc_spec and sc_spec['filtration_and_radius_clearance_spec'] is not None:
        fr_res = verify_filtration_monotonicity_and_heterogeneous_radius_clearance(**sc_spec['filtration_and_radius_clearance_spec'])
        if fr_res['status'] != 'PASS':
            raise AntiGoodhartGateError(f'[Gate 5r Filtration Monotonicity / Heterogeneous-Radius Surface Clearance Failure] {fr_res}')
        receipt['gate5r_filtration_and_radius_clearance'] = fr_res
        receipt['gates_passed'].append('G5r_FiltrationMonotonicity_And_HeterogeneousRadius_SurfaceClearance')
    if 'rp2_director_and_reciprocal_spec' in sc_spec and sc_spec['rp2_director_and_reciprocal_spec'] is not None:
        rp_res = verify_rp2_director_gauge_and_reciprocal_conjugacy(**sc_spec['rp2_director_and_reciprocal_spec'])
        if rp_res['status'] != 'PASS':
            raise AntiGoodhartGateError(f'[Gate 3k RP^2 Director Sign-Gauge / Lateral-Slip Decoupling / Reciprocal Conjugacy Failure] {rp_res}')
        receipt['gate3k_rp2_director_and_reciprocal'] = rp_res
        receipt['gates_passed'].append('G3k_RP2DirectorGauge_LateralSlipDecoupling_And_ReciprocalConjugacy')
    if 'weighted_dispersion_kish_spec' in sc_spec and sc_spec['weighted_dispersion_kish_spec'] is not None:
        wd_res = verify_weighted_dispersion_kish_and_scale_invariance(**sc_spec['weighted_dispersion_kish_spec'])
        if wd_res['status'] != 'PASS':
            raise AntiGoodhartGateError(f'[Gate 5s Weighted Dispersion Mixed-Degree Homogeneity / Kish Outlier Invariance Failure] {wd_res}')
        receipt['gate5s_weighted_dispersion_kish'] = wd_res
        receipt['gates_passed'].append('G5s_WeightedDispersion_KishOutlierInvariance_And_MixedDegreeHomogeneity')
    if 'nonorthogonal_pencil_gauge_spec' in sc_spec and sc_spec['nonorthogonal_pencil_gauge_spec'] is not None:
        pg_res = verify_nonorthogonal_pencil_gauge_and_spectral_parity(**sc_spec['nonorthogonal_pencil_gauge_spec'])
        if pg_res['status'] != 'PASS':
            raise AntiGoodhartGateError(f'[Gate 5t Non-Orthogonal Pencil Metric-Shift Gauge / Spectral Parity Failure] {pg_res}')
        receipt['gate5t_nonorthogonal_pencil_gauge'] = pg_res
        receipt['gates_passed'].append('G5t_NonOrthogonalPencil_MetricShiftGauge_And_SpectralParity')
    if 'coupled_basis_sign_gauge_spec' in sc_spec and sc_spec['coupled_basis_sign_gauge_spec'] is not None:
        cg_res = verify_coupled_basis_sign_gauge_and_locality_bounds(**sc_spec['coupled_basis_sign_gauge_spec'])
        if cg_res['status'] != 'PASS':
            raise AntiGoodhartGateError(f'[Gate 3l Coupled Basis Sign-Gauge / Cluster Locality / Cauchy-Schwarz Bounds Failure] {cg_res}')
        receipt['gate3l_coupled_basis_sign_gauge'] = cg_res
        receipt['gates_passed'].append('G3l_CoupledBasisSignGauge_ClusterLocality_And_CauchySchwarzBounds')
    if 'universal_slot_laws_spec' in sc_spec and sc_spec['universal_slot_laws_spec'] is not None:
        us_res = evaluate_universal_declarative_slots(**sc_spec['universal_slot_laws_spec'])
        s3_checked = int(us_res['s3_1_equivariance_laws_checked']) if 's3_1_equivariance_laws_checked' in us_res else 0
        if us_res['status'] != 'PASS' or s3_checked < 1:
            raise AntiGoodhartGateError(f'[Universal Declarative Slot Law Failure / Missing S3.1 Equivariance Law] {us_res}')
        receipt['universal_declarative_slot_laws'] = us_res
        receipt['gates_passed'].append('S3_1_Universal_Equivariance_And_Gauge')
    _run_physics_redteam_and_outer_glue_checks(sc_spec, receipt)


def _run_physics_redteam_and_outer_glue_checks(sc_spec: Dict[str, Any], receipt: Dict[str, Any]) -> None:
    if 'dynamic_feature_variance_spec' in sc_spec and sc_spec['dynamic_feature_variance_spec'] is not None:
        df_res = verify_dynamic_feature_variance_and_noncollinearity(**sc_spec['dynamic_feature_variance_spec'])
        if df_res['status'] != 'PASS':
            raise AntiGoodhartGateError(f'[Gate 4d Dynamic Feature Variance Collapse / Collinearity Failure] {df_res}')
        receipt['gate4d_feature_variance_collapse'] = df_res
        receipt['gates_passed'].append('G4d_DynamicFeature_VarianceCollapse_And_Collinearity_Canary')
    if 'subfragment_spin_and_slip_spec' in sc_spec and sc_spec['subfragment_spin_and_slip_spec'] is not None:
        sp_res = verify_subfragment_spin_and_siteslip_sensitivity(**sc_spec['subfragment_spin_and_slip_spec'])
        if sp_res['status'] != 'PASS':
            raise AntiGoodhartGateError(f'[Gate 3m Sub-Fragment Spin / Site-Slip Sensitivity Failure] {sp_res}')
        receipt['gate3m_subfragment_spin_and_slip'] = sp_res
        receipt['gates_passed'].append('G3m_SubFragment_RigidSpin_And_SiteSlip_Sensitivity')
    if 'unitcell_gauge_and_chain_spec' in sc_spec and sc_spec['unitcell_gauge_and_chain_spec'] is not None:
        uc_res = verify_unitcell_cyclic_shift_and_chain_convergence(**sc_spec['unitcell_gauge_and_chain_spec'])
        if uc_res['status'] != 'PASS':
            raise AntiGoodhartGateError(f'[Gate 1f Periodic Unit-Cell Cyclic Shift / Chain Convergence Failure] {uc_res}')
        receipt['gate1f_unitcell_gauge_and_chain_rg'] = uc_res
        receipt['gates_passed'].append('G1f_PeriodicUnitCell_CyclicShift_Gauge_And_ChainSize_Convergence')
    if 'crosstable_physical_bounds_spec' in sc_spec and sc_spec['crosstable_physical_bounds_spec'] is not None:
        cb_res = verify_crosstable_physical_inequality_bounds(**sc_spec['crosstable_physical_bounds_spec'])
        if cb_res['status'] != 'PASS':
            raise AntiGoodhartGateError(f'[Gate 5u Cross-Table Physical / Thermodynamic Bound Failure] {cb_res}')
        receipt['gate5u_crosstable_physical_bounds'] = cb_res
        receipt['gates_passed'].append('G5u_CrossTable_Thermodynamic_And_Physical_Inequality_Bounds')
    if 'outer_glue_and_single_source_spec' in sc_spec and sc_spec['outer_glue_and_single_source_spec'] is not None:
        og_res = audit_outer_glue_and_single_source_ast(**sc_spec['outer_glue_and_single_source_spec'])
        if og_res['status'] != 'PASS':
            raise AntiGoodhartGateError(f'[Gate 6q Outer-Glue AST Coverage / Single-Source Lock Failure] {og_res}')
        receipt['gate6q_outer_glue_and_single_source'] = og_res
        receipt['gates_passed'].append('G6q_OuterGlue_Coverage_And_CrossStation_SingleSource_Lock')
    if 'dual_entry_physics_redteam_spec' in sc_spec and sc_spec['dual_entry_physics_redteam_spec'] is not None:
        rt_res = verify_dual_entry_physics_redteam_audit(**sc_spec['dual_entry_physics_redteam_spec'])
        if rt_res['status'] != 'PASS':
            raise AntiGoodhartGateError(f'[Gate 7j Dual-Entry Physics Red-Team Audit Failure] {rt_res}')
        receipt['gate7j_dual_entry_physics_redteam'] = rt_res
        receipt['gates_passed'].append('G7j_DualEntry_PreCode_And_PostHoc_Physics_RedTeam_Audit')
    _run_formal_and_certified_verification_checks(sc_spec, receipt)


def _run_formal_and_certified_verification_checks(sc_spec: Dict[str, Any], receipt: Dict[str, Any]) -> None:
    if 'pint_dimensional_homogeneity_spec' in sc_spec and sc_spec['pint_dimensional_homogeneity_spec'] is not None:
        pt_res = verify_pint_dimensional_homogeneity(**sc_spec['pint_dimensional_homogeneity_spec'])
        if pt_res['status'] != 'PASS':
            raise AntiGoodhartGateError(f'[Gate 3o Pint Dimensional Homogeneity / Unit Scale Failure] {pt_res}')
        receipt['gate3o_pint_dimensional_homogeneity'] = pt_res
        receipt['gates_passed'].append('G3o_Pint_DimensionalHomogeneity_And_UnitScale_Contract')
    if 'formal_chemistry_smt_spec' in sc_spec and sc_spec['formal_chemistry_smt_spec'] is not None:
        fc_res = verify_stoichiometry_spin_and_wegscheider_smt(**sc_spec['formal_chemistry_smt_spec'])
        if fc_res['status'] != 'PASS':
            raise AntiGoodhartGateError(f'[Gate 5v Stoichiometry / Spin Parity / Wegscheider SMT / CRNT Failure] {fc_res}')
        receipt['gate5v_formal_chemistry_smt'] = fc_res
        receipt['gates_passed'].append('G5v_Stoichiometry_SpinParity_And_Wegscheider_SMT')
    if 'arb_ball_enclosure_spec' in sc_spec and sc_spec['arb_ball_enclosure_spec'] is not None:
        ab_res = verify_arb_ball_enclosure_and_conditioning(**sc_spec['arb_ball_enclosure_spec'])
        if ab_res['status'] != 'PASS':
            raise AntiGoodhartGateError(f'[Gate 1g Python-FLINT Arb Ball Arithmetic Enclosure Failure] {ab_res}')
        receipt['gate1g_arb_ball_enclosure'] = ab_res
        receipt['gates_passed'].append('G1g_Arb_BallArithmetic_Enclosure_And_Conditioning')
    if 'hypothesis_lie_shrinking_spec' in sc_spec and sc_spec['hypothesis_lie_shrinking_spec'] is not None:
        hl_res = verify_hypothesis_lie_group_and_boundary_shrinking(**sc_spec['hypothesis_lie_shrinking_spec'])
        if hl_res['status'] != 'PASS':
            raise AntiGoodhartGateError(f'[Gate 3n Hypothesis Lie-Group & Singular-Angle Shrinking Failure] {hl_res}')
        receipt['gate3n_hypothesis_lie_shrinking'] = hl_res
        receipt['gates_passed'].append('G3n_Hypothesis_LieGroup_And_Boundary_Shrinking')
    if 'lean4_symbolic_proof_spec' in sc_spec and sc_spec['lean4_symbolic_proof_spec'] is not None:
        ln_res = verify_lean4_symbolic_proof_and_inhabitation(**sc_spec['lean4_symbolic_proof_spec'])
        if ln_res['status'] != 'PASS':
            raise AntiGoodhartGateError(f'[Gate 2c Lean 4 Symbolic Proof & Inhabitation Witness Failure] {ln_res}')
        receipt['gate2c_lean4_symbolic_proof'] = ln_res
        receipt['gates_passed'].append('G2c_Lean4_SymbolicProof_And_Inhabitation_Witness')
    if 'keymaerax_ode_safety_spec' in sc_spec and sc_spec['keymaerax_ode_safety_spec'] is not None:
        kx_res = verify_keymaerax_ode_invariants(**sc_spec['keymaerax_ode_safety_spec'])
        if kx_res['status'] != 'PASS':
            raise AntiGoodhartGateError(f'[Gate 5w KeYmaera X dL ODE Safety & Z3 Precondition Gate Failure] {kx_res}')
        receipt['gate5w_keymaerax_ode_safety'] = kx_res
        receipt['gates_passed'].append('G5w_KeYmaeraX_DifferentialDynamicLogic_ODE_Safety')


class ScientificStages:
    """Legacy private stage adapter; the engine uses explicit functions."""
    _run_scientific_computing_pack_checks = staticmethod(_run_scientific_computing_pack_checks)
    _run_calibrated_scientific_invariant_checks = staticmethod(_run_calibrated_scientific_invariant_checks)
    _run_calibrated_diffraction_quantum_and_slot_checks = staticmethod(_run_calibrated_diffraction_quantum_and_slot_checks)
    _run_physics_redteam_and_outer_glue_checks = staticmethod(_run_physics_redteam_and_outer_glue_checks)
    _run_formal_and_certified_verification_checks = staticmethod(_run_formal_and_certified_verification_checks)
