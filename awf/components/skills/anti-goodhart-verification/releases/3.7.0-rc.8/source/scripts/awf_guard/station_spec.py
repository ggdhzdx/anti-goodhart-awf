"""AWF Guard: station spec."""
from __future__ import annotations

from typing import Any
from typing import Callable
from typing import Dict
from typing import Literal
from typing import Optional
from pathlib import Path
from typing import Sequence
from typing import Union
from dataclasses import dataclass
from dataclasses import field
import numpy as np
from .claims import AgentClaim
from .command_receipts import CommandReceipt
from .harness import HarnessIntegritySnapshot
from .metamorphic import MetamorphicRelationSpec
from .verifier_safety import RolloutSeamRecord
from .information import SealedHoldoutCapsule
from .trajectory import TrajectoryFairnessContract


def _cfg_value(mapping: Dict[str, Any], key: str, fallback: Any) -> Any:
    """Explicit dictionary lookup avoiding `.get(key, numeric_literal)` AST fallback masking."""
    return mapping[key] if key in mapping and mapping[key] is not None else fallback


@dataclass(frozen=True)
class MetaBoundsPolicy:
    """
    Immutable Second-Order Anti-Collusion Bounds (Meta-Guard) & Tri-State Borderline Policy.
    """
    max_allowed_limit_tol_deterministic: float = 1e-2
    max_allowed_limit_tol_stochastic: float = 0.15
    max_allowed_oracle_tol_deterministic: float = 1e-3
    max_allowed_oracle_tol_stochastic: float = 0.15
    min_perturbation_floor: float = 1e-5
    min_ablation_shock_floor: float = 1e-5
    max_null_score_ceiling: float = 0.55
    min_shift_sensitivity_drop: float = 0.10
    max_oracle_ast_similarity: float = 0.82
    min_allowed_iterative_loop_bound: int = 10
    borderline_margin_ratio: float = 0.80
    strict_reject_borderline: bool = False
    min_ncc_floor: float = 0.72


@dataclass
class StationVerificationSpec:
    """
    Polymorphic, Domain-Agnostic Verification Specification for a single Station / Atomic Capsule.
    """
    station_id: str
    station_name: str
    target_fn: Callable[..., Any]
    tier: Literal[0, 1, 2] = 2
    mode: Literal["deterministic", "stochastic"] = "deterministic"

    socratic_premortem_question: str = ""
    socratic_premortem_analytic_trap: str = ""

    # Gate 1: Analytic Limit & Null/Shift Evaluator Calibration
    limit_input_kwargs: Dict[str, Any] = field(default_factory=dict)
    analytic_expected_fn: Optional[Callable[[Any], np.ndarray]] = None
    limit_tol: float = 1e-5
    evaluator_fn: Optional[Callable[[np.ndarray, np.ndarray], float]] = None
    evaluator_ref_sample: Optional[np.ndarray] = None
    evaluator_null_sample: Optional[np.ndarray] = None
    evaluator_shifted_sample: Optional[np.ndarray] = None
    null_score_ceiling: float = 0.40
    min_shift_drop: float = 0.15

    # Gate 2: Dual-Path Orthogonal Oracle (Required in Tier 2)
    small_input_kwargs: Dict[str, Any] = field(default_factory=dict)
    orthogonal_oracle_fn: Optional[Callable[..., Any]] = None
    oracle_tol: float = 1e-5

    # Gate 3: Symmetry Group Invariance & Orthogonal Perturbation Sensitivity
    symmetry_transform_fn: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None
    equivariant_output_fn: Optional[Callable[[Any], Any]] = None
    perturb_transform_fn: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None
    min_perturbation_delta: float = 1e-3

    # Gate 4: Constraint & Masking Ablation Shock
    constraint_ablation_kwargs: Optional[Dict[str, Any]] = None
    min_ablation_shock: float = 1e-3

    # Gate 5: Manifold Non-Degeneracy, Conservation Identity, Trajectory SVD & Pre-Execution AST Guards
    invariant_residual_fn: Optional[Callable[[Any], float]] = None
    residual_tol: float = 1e-4
    min_output_std: float = 1e-6
    parameter_history_matrix: Optional[np.ndarray] = None
    expected_total_dof: Optional[int] = None
    min_active_dof_fraction: float = 0.90
    min_trajectory_svd_rank: int = 3
    solver_source_code: Optional[str] = None
    baseline_source_code: Optional[str] = None
    test_suite_source_for_ncc: Optional[str] = None
    ncc_floor: float = 0.72

    # Gate 7: De-Pooled L_inf Worst-K Slice Exposure & Hold-Out Orthogonal Validation
    depooled_slice_scores: Optional[Dict[str, float]] = None
    worst_slice_floor: float = 0.60
    holdout_orthogonal_metric_name: str = ""
    holdout_orthogonal_value: Optional[float] = None
    holdout_orthogonal_target: Optional[float] = None
    holdout_orthogonal_tol: float = 0.10
    sealed_holdout_capsule: Optional[SealedHoldoutCapsule] = None
    sanitize_holdout_feedback: bool = True
    cleanroom_chdir: bool = True

    # v1.3.0-rc.1 (`blasrodri/truth`): Command-Receipt Freshness & Turn-Level Claim Fact-Checking
    command_receipts: Optional[Sequence[CommandReceipt]] = None
    latest_source_edit_mtime: Optional[float] = None
    agent_turn_claims: Optional[Union[str, Sequence[Union[str, AgentClaim]]]] = None
    repo_root_for_claims: Optional[Path] = None
    diff_files_for_claims: Optional[Dict[str, str]] = None

    # v1.4.0-rc.1 (`islo-labs/reward-hack-bench`): 3-Alignment Base64 Obfuscation & Trajectory Fairness
    forbidden_b64_literals: Optional[Sequence[str]] = None
    trajectory_steps_for_fairness: Optional[Sequence[Dict[str, Any]]] = None
    trajectory_fairness_contract: Optional[TrajectoryFairnessContract] = None

    # v1.5.0-rc.1 (`JonathanGabor/evilgenie_inspect`): Cryptographic Harness Snapshot & 3D Categorical Scorer
    harness_integrity_snapshot: Optional[HarnessIntegritySnapshot] = None

    # v1.6.0-rc.1 (`tum-i4/gemtest`): General Multi-Source & Output-Dependent Metamorphic Relations
    metamorphic_relations: Optional[Sequence[MetamorphicRelationSpec]] = None
    output_dependent_metamorphic_relations: Optional[Sequence[MetamorphicRelationSpec]] = None

    # v1.7.0-rc.1 (`benchjack/benchjack`): V1-V8 Benchmark & Evaluator Hackability Audit
    benchmark_source_files: Optional[Dict[str, str]] = None

    # v1.8.0-rc.1 (`rushjais/Goodhart`): Red-Green Friendly-Fire Regression Gate & Best-of-K Selection Gap
    verifier_hardening_spec: Optional[Dict[str, Any]] = None
    rollout_seam_records: Optional[Sequence[RolloutSeamRecord]] = None
    min_verifier_safety_score: float = 95.0

    # v1.9.0-rc.1 (`patrick-kidger/jaxtyping`): Symbolic Algebraic Shape & Variadic Batch/Broadcast Contracts
    jaxtyping_shape_contract_checks: Optional[Sequence[Dict[str, Any]]] = None

    # v1.10.0-rc.1 (`logi-cmd/agent-guardrails`): Task Scope, Continuity Budget & Verity Receipt Audit
    task_guardrail_audit_spec: Optional[Dict[str, Any]] = None

    # v2.0.0-rc.1 (`Aurite-ai/agent-verifier`): Loop/Retry, Tool Registry, Graph Cycle, Secret & Quality Audit
    agent_verifier_audit_spec: Optional[Dict[str, Any]] = None

    # v2.1.0-rc.1 (`safety-research/impossiblebench`): Conflicting Canary, Referential Transparency & Anti-Sycophancy
    impossiblebench_audit_spec: Optional[Dict[str, Any]] = None

    # v2.2.0-rc.1 (`vinicq/falsegreen` & `JetBrains-Research/PyNose`): Hollow Test, Tautological Assert & Self-Mocking Audit
    falsegreen_test_audit_spec: Optional[Dict[str, Any]] = None

    # v2.3.0-rc.1 (`boxed/mutmut`): In-Memory AST Mutation Kill-Rate & Anti-Loose-Tolerance Audit
    mutation_testing_audit_spec: Optional[Dict[str, Any]] = None

    # v2.4.0-rc.1 (`Parquery/icontract`, `life4/deal` & `pschanely/CrossHair`): Design-by-Contract & Input Immutability
    design_by_contract_audit_spec: Optional[Dict[str, Any]] = None

    # v2.5.0-rc.1 (`Tommasoaiello13/splitguard` & `SE4AIResearch/DataLeakage`): BLAKE2b Row-Taint & Group Split Leakage
    splitguard_leakage_audit_spec: Optional[Dict[str, Any]] = None

    # v3.0.0-rc.1 (`gmarkall/PitfallsFP` & Monte Carlo Arithmetic): Floating-Point Pitfall AST & MCA Conditioning Audit
    numerical_stability_audit_spec: Optional[Dict[str, Any]] = None

    # v3.1.0-rc.1 (Self-Hosting Dogfooding Gate): Zero-Violation Self-Referential Engine & Capsule Granularity Audit
    self_hosting_dogfood_audit: bool = False

    # v3.2.0-rc.1 (Scientific Computing Method Development Pack): Gradient/FD, Convergence Order, SE(3)/PBC/Perm, Matrix/Unit Invariants
    scientific_computing_audit_spec: Optional[Dict[str, Any]] = None
