"""AWF Guard: slot receipts."""
from __future__ import annotations

from typing import Any
from typing import Dict
from typing import List
from typing import Tuple
from .errors import AntiGoodhartGateError


CANONICAL_14_UNIVERSAL_SLOTS: Tuple[str, ...] = (
    "S1_1_AnalyticLimit_And_RegimeProbe",
    "S1_2_Conditioning_And_Convergence",
    "S2_1_Orthogonal_And_FiniteDiff_Oracle",
    "S3_1_Universal_Equivariance_And_Gauge",
    "AtomCapsule_ContractBus",
    "S4_1_Perturbation_And_Ablation_Shock",
    "S5_1_Manifold_And_Matrix_Invariant",
    "S5_2_Unified_Static_AST_CircuitBreaker",
    "S5_3_Mutation_And_Test_Quality",
    "S6_1_CleanRoom_Lineage_And_Harness",
    "S6_2_Autonomous_Remediation_ClosedLoop",
    "S7_1_WorstSlice_Holdout_And_Generalization",
    "MetaGuard_AntiCollusion",
    "S7_3_ClaimCheck_And_Verifier_Safety",
)


_SUBCHECK_TO_UNIVERSAL_SLOT_MAP: Dict[str, str] = {
    "G1_Analytic_Limit": "S1_1_AnalyticLimit_And_RegimeProbe",
    "G1_Null_Shift_Calibration": "S1_1_AnalyticLimit_And_RegimeProbe",
    "G1c_MCA_StochasticRounding_And_PrecisionDowngrade_Stability": "S1_2_Conditioning_And_Convergence",
    "G5l_PitfallsFP_No_NaiveInverse_Or_UnstableLogSumExp": "S1_2_Conditioning_And_Convergence",
    "G1d_Asymptotic_Convergence_Order_Verification": "S1_2_Conditioning_And_Convergence",
    "G1e_MeshRefinement_IntensiveInvariance_And_NoiseFloor_Stability": "S1_2_Conditioning_And_Convergence",
    "G2_DualPath_Orthogonal_Oracle": "S2_1_Orthogonal_And_FiniteDiff_Oracle",
    "G2b_AnalyticGradient_FiniteDifference_Consistency": "S2_1_Orthogonal_And_FiniteDiff_Oracle",
    "G3a_Symmetry_Invariance": "S3_1_Universal_Equivariance_And_Gauge",
    "G3c_General_MultiSource_Metamorphic_Relation": "S3_1_Universal_Equivariance_And_Gauge",
    "G3d_OutputDependent_RoundTrip_Metamorphic_Relation": "S3_1_Universal_Equivariance_And_Gauge",
    "G3i_SE3_PBC_MinimumImage_And_Permutation_Equivariance": "S3_1_Universal_Equivariance_And_Gauge",
    "G3j_ScaleHomogeneity_And_AsymmetricRank1Null_ZeroPoint": "S3_1_Universal_Equivariance_And_Gauge",
    "G3k_RP2DirectorGauge_LateralSlipDecoupling_And_ReciprocalConjugacy": "S3_1_Universal_Equivariance_And_Gauge",
    "G3l_CoupledBasisSignGauge_ClusterLocality_And_CauchySchwarzBounds": "S3_1_Universal_Equivariance_And_Gauge",
    "G5o_Pairwise_ZeroSelfInteraction_And_KernelSymmetry": "S3_1_Universal_Equivariance_And_Gauge",
    "G5s_WeightedDispersion_KishOutlierInvariance_And_MixedDegreeHomogeneity": "S3_1_Universal_Equivariance_And_Gauge",
    "G5t_NonOrthogonalPencil_MetricShiftGauge_And_SpectralParity": "S3_1_Universal_Equivariance_And_Gauge",
    "S3_1_Universal_Equivariance_And_Gauge": "S3_1_Universal_Equivariance_And_Gauge",
    "AtomCapsule_ContractBus": "AtomCapsule_ContractBus",
    "G3e_Jaxtyping_Symbolic_Algebraic_Shape_Contract": "AtomCapsule_ContractBus",
    "G3f_Jaxtyping_Variadic_Batch_And_Broadcast_Contract": "AtomCapsule_ContractBus",
    "G3g_DealPure_InputImmutability_And_NoSideEffects": "AtomCapsule_ContractBus",
    "G3h_CrossHair_Adversarial_Boundary_Contract_Fuzzing": "AtomCapsule_ContractBus",
    "G3b_Perturbation_Sensitivity": "S4_1_Perturbation_And_Ablation_Shock",
    "G4_Constraint_Ablation_Shock": "S4_1_Perturbation_And_Ablation_Shock",
    "G5a_Conservation_Identity": "S5_1_Manifold_And_Matrix_Invariant",
    "G5c_Trajectory_SVD_FullRank": "S5_1_Manifold_And_Matrix_Invariant",
    "G5m_PhysicalMatrix_Hermitian_PSD_And_DetailedBalance": "S5_1_Manifold_And_Matrix_Invariant",
    "G5p_BipolarSignReachability_And_MultiSource_VariancePropagation": "S5_1_Manifold_And_Matrix_Invariant",
    "G5q_EulerPoincare_DigitalDuality_And_1DSupercoverHomotopy": "S5_1_Manifold_And_Matrix_Invariant",
    "G5r_FiltrationMonotonicity_And_HeterogeneousRadius_SurfaceClearance": "S5_1_Manifold_And_Matrix_Invariant",
    "AST_DependencyGraph_CrossCheck": "S5_2_Unified_Static_AST_CircuitBreaker",
    "AST_ParameterTaint_Dataflow": "S5_2_Unified_Static_AST_CircuitBreaker",
    "AST_Intent_Structure_Alignment": "S5_2_Unified_Static_AST_CircuitBreaker",
    "G5b_AST_No_Short_Loops": "S5_2_Unified_Static_AST_CircuitBreaker",
    "G5d_AST_AntiTamper_And_No_Enumeration": "S5_2_Unified_Static_AST_CircuitBreaker",
    "G5e_PairMode_No_Complexity_Collapse": "S5_2_Unified_Static_AST_CircuitBreaker",
    "G5f_Base64_3Alignment_No_Obfuscated_Constants": "S5_2_Unified_Static_AST_CircuitBreaker",
    "G5g_AST_No_TestFileRead_Or_HeuristicCutoff": "S5_2_Unified_Static_AST_CircuitBreaker",
    "G5h_AgentVerifier_LoopRetry_ToolRegistry_And_GraphCycle": "S5_2_Unified_Static_AST_CircuitBreaker",
    "G5i_AgentVerifier_ZeroSecrets_SwallowedExceptions_And_Quality": "S5_2_Unified_Static_AST_CircuitBreaker",
    "G5n_Zero_Todo_Placeholder_Stub_And_MagicNumber_CircuitBreaker": "S5_2_Unified_Static_AST_CircuitBreaker",
    "G6o_MicroStep_Topological_DAG_And_Granularity_Anchor": "S5_2_Unified_Static_AST_CircuitBreaker",
    "G6n_SelfHosting_ZeroViolation_Dogfood_Audit": "S5_2_Unified_Static_AST_CircuitBreaker",
    "G5j_Mutmut_AST_Mutation_Kill_Rate": "S5_3_Mutation_And_Test_Quality",
    "G5k_Anti_Loose_Tolerance_Inflation": "S5_3_Mutation_And_Test_Quality",
    "G6k_FalseGreen_No_Hollow_Or_Tautological_Tests": "S5_3_Mutation_And_Test_Quality",
    "G6l_FalseGreen_Zero_SelfMocking_And_BogusMockAssert": "S5_3_Mutation_And_Test_Quality",
    "CleanRoom_Tempdir_Sandbox": "S6_1_CleanRoom_Lineage_And_Harness",
    "G6_Dynamic_Execution_Lineage": "S6_1_CleanRoom_Lineage_And_Harness",
    "G6b_NCC_Zero_Test_Memorization": "S6_1_CleanRoom_Lineage_And_Harness",
    "G6c_CommandReceipt_Fresh_And_Unnarrowed": "S6_1_CleanRoom_Lineage_And_Harness",
    "G6d_Trajectory_Fairness_And_No_Bypass_Smuggling": "S6_1_CleanRoom_Lineage_And_Harness",
    "G6e_Harness_SHA256_Immutable_And_3D_Categorical": "S6_1_CleanRoom_Lineage_And_Harness",
    "G6f_BenchJack_TrustBoundary_No_SharedPath_Or_ConftestHook": "S6_1_CleanRoom_Lineage_And_Harness",
    "G6g_BenchJack_Evaluator_No_LogicGap_Or_WeakMatch": "S6_1_CleanRoom_Lineage_And_Harness",
    "G6h_AgentGuardrails_TaskScope_And_Continuity_Budget": "S6_1_CleanRoom_Lineage_And_Harness",
    "G6i_Verity_Cryptographic_Receipt_Schema_And_Fingerprint": "S6_1_CleanRoom_Lineage_And_Harness",
    "G6p_Remediation_ClosedLoop_PairDiff_And_Pareto_Selection": "S6_2_Autonomous_Remediation_ClosedLoop",
    "BoundarySeal_InformationAsymmetry": "S7_1_WorstSlice_Holdout_And_Generalization",
    "G7a_DePooled_WorstK_Exposure": "S7_1_WorstSlice_Holdout_And_Generalization",
    "G7b_HoldOut_Orthogonal_Validation": "S7_1_WorstSlice_Holdout_And_Generalization",
    "G6m_DataLeakage_No_PreSplit_FitTransform": "S7_1_WorstSlice_Holdout_And_Generalization",
    "G7g_SplitGuard_Zero_RowTaint_And_GroupSplit_Leakage": "S7_1_WorstSlice_Holdout_And_Generalization",
    "G7i_LOOCV_Generalization_And_TrainEval_FeatureParity": "S7_1_WorstSlice_Holdout_And_Generalization",
    "MetaGuard_AntiCollusion": "MetaGuard_AntiCollusion",
    "G6j_ImpossibleBench_ConflictingCanary_And_ReferentialTransparency": "MetaGuard_AntiCollusion",
    "G7f_ImpossibleBench_AntiSycophancy_ContradictorySpec_Flag": "MetaGuard_AntiCollusion",
    "G7h_RedBlue_Adversarial_Auditor_Decoupled_Game": "MetaGuard_AntiCollusion",
    "G7c_TurnClaim_FactCheck_ZeroContradiction": "S7_3_ClaimCheck_And_Verifier_Safety",
    "G7d_RedGreen_RegressionGate_ZeroFriendlyFire": "S7_3_ClaimCheck_And_Verifier_Safety",
    "G7e_VerifierSafety_And_BestOfK_Gap": "S7_3_ClaimCheck_And_Verifier_Safety",
    "TriState_Verdict_Audit": "S7_3_ClaimCheck_And_Verifier_Safety",
}


def _consolidate_to_14_universal_slots(receipt: Dict[str, Any]) -> None:
    """
    Collapse fragmented sub-check labels in `receipt['gates_passed']` into the
    14 Canonical Universal Slots (`CANONICAL_14_UNIVERSAL_SLOTS`), preserving the
    detailed per-slot sub-check breakdown in `receipt['slot_subchecks_verified']`.
    """
    raw_subchecks: List[str] = list(receipt.get("gates_passed", []))
    unknown = sorted({sub for sub in raw_subchecks if sub not in _SUBCHECK_TO_UNIVERSAL_SLOT_MAP})
    if unknown:
        raise AntiGoodhartGateError(
            f"[Slot Consolidation Fail-Closed] Unregistered sub-check label(s) {unknown} cannot be credited to any universal slot."
        )
    slot_to_subchecks: Dict[str, List[str]] = {slot: [] for slot in CANONICAL_14_UNIVERSAL_SLOTS}
    for sub in raw_subchecks:
        target_slot = _SUBCHECK_TO_UNIVERSAL_SLOT_MAP[sub]
        if sub not in slot_to_subchecks[target_slot]:
            slot_to_subchecks[target_slot].append(sub)
    active_slots = [slot for slot in CANONICAL_14_UNIVERSAL_SLOTS if slot_to_subchecks[slot]]
    receipt["gates_passed"] = active_slots
    receipt["universal_slot_count"] = len(active_slots)
    receipt["subchecks_verified_count"] = len(set(raw_subchecks))
    receipt["slot_subcheck_counts"] = {slot: len(slot_to_subchecks[slot]) for slot in CANONICAL_14_UNIVERSAL_SLOTS}
    receipt["inactive_slots"] = [slot for slot in CANONICAL_14_UNIVERSAL_SLOTS if not slot_to_subchecks[slot]]
    receipt["slot_subchecks_verified"] = {
        slot: slot_to_subchecks[slot] for slot in active_slots
    }
