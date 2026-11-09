#!/usr/bin/env python3
"""
Co-located AWF Release Registration Script for AWF Guard
(skill.anti-goodhart-verification@3.6.0-rc.1 & workflow anti-goodhart-verification@3.6.0-rc.1).
Strictly follows ADR 0012 (rolling current pointer) and ADR 0022 (co-located scripts
inside the target Release source/ tree prior to execution).
Preserves `1.0.0` .. `3.5.0-rc.1` immutably and registers `3.6.0-rc.1` (7 Major Gates x 14
Orthogonal Universal Slots Consolidation `CANONICAL_14_UNIVERSAL_SLOTS` + Open-Ended
Declarative Law Injector `evaluate_universal_declarative_slots`, consolidating 74 subchecks).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict

AWF_ROOT = Path("/home/zc/agent_workflows")
if not AWF_ROOT.exists():
    AWF_ROOT = Path(r"Z:\agent_workflows")
sys.path.insert(0, str(AWF_ROOT / "bin"))

import verify  # type: ignore


def write_json_yaml(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def build_release_meta(source_rel: str, legacy_hash: str) -> Dict[str, Any]:
    return {
        "status": "validated",
        "observed_at": "2026-11-08",
        "entry_point": "SKILL.md",
        "source_snapshot": source_rel,
        "tree_sha256": legacy_hash,
        "depends_on": [],
        "runtime_requirements": [
            "UTF-8 Markdown Skill loader (Antigravity / Codex / Pi / Grok)",
            "Python 3.9+ with NumPy for executing scripts/awf_universal_anti_goodhart_gates.py",
        ],
        "capabilities": [
            "domain-agnostic-universal-7-gate-anti-goodhart-and-anti-shortcut-engine",
            "canonical-14-orthogonal-universal-slot-consolidation-with-74-subcheck-preservation",
            "open-ended-declarative-universal-slot-law-injector-s1-s3-s5",
            "six-mode-degenerate-shortcut-taxonomy-defense",
            "pre-execution-intra-function-parameter-taint-fixed-point-dataflow-with-control-dependence",
            "extensional-enumeration-and-dict-dispatch-memorization-detection-with-iupac-periodic-table-exemption",
            "docstring-and-math-contract-intent-vs-ast-structure-alignment",
            "information-theoretic-zlib-ncc-test-literal-overlap-detection",
            "pair-mode-baseline-mccabe-complexity-collapse-and-new-constant-bypass-audit",
            "anti-harness-tampering-dunder-hijack-zero-stride-and-frame-introspection-guard",
            "three-byte-alignment-base64-and-json-linewrap-obfuscation-detector",
            "eleven-channel-trajectory-fairness-and-solution-smuggling-auditor",
            "orthogonal-static-reward-vs-fairness-decoupled-trial-scorer",
            "prompt-attribution-footer-relocation-and-provenance-leak-sanitizer",
            "cryptographic-sha256-harness-file-integrity-snapshot-and-auto-restore",
            "ast-direct-test-file-reading-and-size-cutoff-heuristic-fallback-detector",
            "per-problem-seeded-deterministic-visible-holdout-splitter",
            "three-dimensional-evilgenie-categorical-scorer",
            "general-multisource-combinatorial-and-sampled-metamorphic-testing-engine",
            "output-dependent-followup-roundtrip-and-idempotence-metamorphic-relations",
            "parameterized-fixed-and-randomized-metamorphic-transform-generators-with-domain-skip",
            "benchjack-v1-v8-evaluator-hackability-and-trust-boundary-scanner",
            "shared-agent-write-evaluator-read-path-and-conftest-hook-hijack-detector",
            "evaluator-except-returns-pass-and-weak-substring-matching-scanner",
            "red-green-verifier-hardening-friendly-fire-regression-gate",
            "reasoning-gym-conclusion-cue-and-delimited-answer-hardening-templates",
            "rollout-seam-verifier-safety-score-and-bestofk-selection-gap-benchmark",
            "jaxtyping-symbolic-algebraic-shape-expression-evaluator",
            "jaxtyping-variadic-batch-and-cross-argument-broadcast-shape-contract",
            "agent-guardrails-task-scope-continuity-and-parallel-abstraction-auditor",
            "verity-cryptographic-receipt-strict-schema-and-fingerprint-validator",
            "aurite-agent-verifier-unbounded-loop-retry-tool-registry-and-graph-cycle-auditor",
            "aurite-agent-verifier-zero-secrets-swallowed-exceptions-and-dependency-hygiene-scanner",
            "impossiblebench-conflicting-canary-trap-and-stateful-call-counter-detector",
            "impossiblebench-anti-sycophancy-contradictory-specification-intervention-gate",
            "falsegreen-and-pynose-hollow-test-and-tautological-assertion-scanner",
            "falsegreen-zero-self-mocking-and-bogus-mock-assertion-auditor",
            "mutmut-in-memory-ast-mutation-kill-rate-and-forced-fail-sanity-engine",
            "anti-loose-tolerance-inflation-atol-rtol-ast-auditor",
            "icontract-and-deal-pure-input-immutability-sha256-snapshot-verifier",
            "crosshair-adversarial-corner-case-boundary-contract-fuzzer",
            "dataleakage-pre-split-fit-transform-ast-scanner",
            "splitguard-blake2b-row-taint-and-group-conformer-split-auditor",
            "pitfallsfp-floating-point-catastrophic-cancellation-ast-scanner",
            "monte-carlo-arithmetic-stochastic-rounding-and-precision-downgrade-conditioning-auditor",
            "self-hosting-zero-violation-dogfood-auditor-and-160-line-capsule-granularity-gate",
            "analytic-force-gradient-vs-richardson-extrapolated-central-finite-difference-verifier",
            "asymptotic-grid-step-convergence-order-log-slope-verifier",
            "se3-rigid-rotation-translation-triclinic-pbc-minimum-image-and-permutation-equivariance-verifier",
            "physical-matrix-hermitian-psd-detailed-balance-and-cross-atom-unit-homogeneity-verifier",
            "static-negative-infinity-todo-placeholder-stub-and-magic-number-circuit-breaker",
            "six-dimensional-microstep-granularity-and-topological-one-hop-dag-anchor",
            "red-blue-adversarial-auditor-decoupled-minimax-verification-game",
            "pairwise-kernel-exchange-symmetry-and-intra-group-self-interaction-exclusion-verifier",
            "exact-hat-matrix-leverage-loocv-generalization-and-train-eval-feature-parity-verifier",
            "euler-scale-homogeneity-and-asymmetric-rank1-product-null-zero-point-calibrator",
            "autonomous-remediation-closed-loop-differential-pair-audit-and-pareto-candidate-selector",
            "bipolar-sign-reachability-and-multisource-delta-method-variance-propagation-verifier",
            "mesh-refinement-intensive-invariance-and-high-k-noise-floor-amplification-verifier",
            "euler-poincare-alternating-sum-digital-topology-6-vs-26-duality-and-supercover-homotopy-verifier",
            "cumulative-filtration-monotonicity-partition-of-unity-and-heterogeneous-radius-surface-clearance-verifier",
            "rp2-nematic-director-sign-gauge-lateral-slip-decoupling-and-reciprocal-space-conjugacy-verifier",
            "weighted-dispersion-mixed-degree-homogeneity-zero-weight-outlier-kish-invariance-and-debiasing-verifier",
            "nonorthogonal-operator-pencil-metric-shift-gauge-subspace-dominance-and-bipolar-spectral-parity-verifier",
            "coupled-operator-vector-local-sign-gauge-separated-cluster-locality-and-cauchy-schwarz-collective-bounds-verifier",
            "adaptive-runtime-execution-budget-evaluator-for-scientific-kernels",
            "command-receipt-edit-mtime-freshness-and-scope-narrowing-zero-test-detector",
            "turn-level-agent-claim-fact-checker-against-ast-git-diff-and-receipts",
            "five-state-epistemic-verdict-taxonomy-and-structured-fact-zero-fp-gate",
            "wall-of-refusals-vague-prose-evasion-detector",
            "risk-tiered-gate-escalation-tier0-sandbox-tier1-lightweight-tier2-production-seal",
            "second-order-anti-collusion-meta-guard-and-ast-orthogonality-audit",
            "information-asymmetry-boundary-seal-and-sealed-holdout-capsule",
            "anti-leak-abstract-diagnostic-sanitizer-for-iterative-retries",
            "three-zone-tristate-verdict-and-borderline-threshold-hugging-detection",
            "cleanroom-tempdir-execution-sandbox-against-local-cache-cheating",
            "deterministic-and-stochastic-dual-modality-verification",
            "post-escape-root-cause-and-gate-self-evolution-loop",
            "atomic-operator-capsule-granularity-80-to-150-line-pure-functional-core",
            "typed-physical-unit-and-symbolic-shape-contract-bus-decorator",
            "ast-call-graph-auto-dependency-discovery-and-bidirectional-dag-reconciliation",
            "atom-manifest-dag-index-and-o1-fault-isolation-hotswap-debugging",
            "standalone-cli-ast-pair-diff-turn-claim-benchmark-and-manifest-audit",
        ],
        "limitations": [
            "Tier-2 full 7-Gate verification requires instantiating a StationVerificationSpec and an algorithmically independent oracle on small inputs",
        ],
        "provenance": "7 Major Gates x 14 Orthogonal Universal Slots Consolidated Release 3.6.0-rc.1 of AWF Guard (`skill.anti-goodhart-verification@3.6.0-rc.1`): permanently bounds top-level receipt slots at 14 Orthogonal Universal Slots (`CANONICAL_14_UNIVERSAL_SLOTS`) while preserving all 74 concrete sub-checks in `slot_subchecks_verified`, and adds the open-ended declarative slot law evaluator (`evaluate_universal_declarative_slots`: `s1_1_regime_probes`, `s3_1_equivariance_laws`, `s5_1_manifold_laws`) so arbitrary new mathematical symmetries and conservation laws can be verified declaratively without adding new gate functions.",
    }


def build_workflow_doc(wf_id: str, rel_id: str, comp_id: str) -> Dict[str, Any]:
    return {
        "schema_version": 1,
        "id": wf_id,
        "release": rel_id,
        "status": "validated",
        "purpose": "Standalone 100% Domain-Agnostic, Self-Hosting & Scientific-Computing-Native Universal 7-Gate x 14-Slot Anti-Goodhart Verification Engine (14 Orthogonal Universal Slots consolidating 74 Automated Sub-Checks + Open-Ended Declarative Slot Law Injector v3.6.0-rc.1).",
        "entry_skills": [comp_id],
        "stages": [
            {
                "id": "tier0-premortem-boundary-seal-and-atomic-capsule-contract-definition",
                "required": True,
                "skill": comp_id,
            },
            {
                "id": "tier1-ast-dataflow-intent-ncc-pair-diff-base64-evilgenie-benchjack-agentverifier-falsegreen-mutmut-splitguard-pitfallsfp-and-cleanroom-audit",
                "required": True,
                "skill": comp_id,
            },
            {
                "id": "tier2-meta-guard-metamorphic-jaxtyping-dbc-mca-scientific-pack-sealed-holdout-receipt-trajectory-harness-goodhart-guardrails-impossiblebench-splitguard-selfhosting-and-turn-claim-7-gate-seal",
                "required": True,
                "skill": comp_id,
            },
            {
                "id": "ast-call-graph-atom-manifest-dag-and-post-escape-gate-evolution",
                "required": False,
                "skill": comp_id,
            },
        ],
        "engineering_gate": "Forbid 1,000+ line monolithic scripts, functions >160 lines, TODO/FIXME/placeholder stubs or unanchored magic numbers (`G5n`), multi-station leapfrogging or oversized McCabe/HALSTEAD/branch micro-steps (`G6o`), unreviewed single-agent reward self-grading without Red-Blue adversarial audit (`G7h`), intra-group self-interaction leakage (`G5o`), small-sample LOOCV over-parameterization or Train/Eval feature-extractor skew (`G7i`), unscaled hardcoded cutoffs or symmetric-only null baselines (`G3j`), watering-down code fixes (`G6p`), non-negative surrogates for bipolar physical quantities or single-source variance underestimation (`G5p`), grid-dependent intensive drift (`G1e`), violated Euler-Poincare or 6-vs-26 digital duality (`G5q`), point-to-center distance ignoring heterogeneous radii (`G5r`), director sign-flip sensitivity or center-to-center lateral-slip inflation (`G3k`), unweighted std or zero-weight outlier distortion (`G5s`), omitted Lowdin S^{-1/2} orthogonalization (`G5t`), unpaired basis sign flips or disconnected-cluster ghost delocalization (`G3l`), surviving AST mutants (`G5j`), loose tolerance inflation (`G5k`), in-place mutation (`G3g`), pre-split data leakage (`G6m`/`G7g`), ill-conditioned floating-point cancellation (`G5l`/`G1c`), and verbal over-claiming (`G7c`).",
        "scientific_gate": "All numerical and scientific operators must satisfy the 14 Canonical Orthogonal Universal Slots (`S1.1`..`S7.3`, consolidating 74 concrete sub-checks across G1-G7), with any domain-specific symmetries or manifold laws injected declaratively via `universal_slot_laws_spec` (`evaluate_universal_declarative_slots`).",
        "version_lock": "versions.lock",
    }


def main() -> int:
    comp_id = "skill.anti-goodhart-verification"
    wf_id = "anti-goodhart-verification"
    rel_id = "3.6.0-rc.1"

    source_rel = f"components/skills/anti-goodhart-verification/releases/{rel_id}/source"
    source_dir = AWF_ROOT / source_rel
    if not source_dir.is_dir():
        raise RuntimeError(f"Missing source directory: {source_dir}")

    legacy_hash = verify.tree_sha256(source_dir)
    v2_hash = verify.tree_sha256_v2(source_dir, "tree")
    v2_paths = verify.tree_v2_paths(source_dir, "tree")
    regular_bytes = sum(
        p.lstat().st_size for p in v2_paths if not p.is_symlink() and p.is_file()
    )
    symlink_count = sum(p.is_symlink() for p in v2_paths)

    release_meta = build_release_meta(source_rel, legacy_hash)
    comp_descriptor_rel = "components/skills/anti-goodhart-verification/component.yaml"
    comp_descriptor_path = AWF_ROOT / comp_descriptor_rel
    comp_doc = verify.read_manifest(comp_descriptor_path)
    comp_doc.setdefault("releases", {})[rel_id] = release_meta
    write_json_yaml(comp_descriptor_path, comp_doc)
    comp_desc_sha = verify.file_sha256(comp_descriptor_path)

    metadata_sha256 = verify.canonical_object_sha256(release_meta)
    attestation_rel = "attestations/release-integrity-20261108-anti-goodhart-verification-v3-6-rc1.yaml"
    attestation_path = AWF_ROOT / attestation_rel
    attestation_doc = {
        "schema_version": 1,
        "digest_contract": "awf-tree-v2",
        "observed_at": "2026-11-08",
        "owner": "awf-anti-goodhart-verification-release-20261108-v3-6-rc1",
        "provenance": "Validated 7 Major Gates x 14 Orthogonal Universal Slots Consolidated release 3.6.0-rc.1 of standalone AWF Guard (`skill.anti-goodhart-verification@3.6.0-rc.1` and workflow `anti-goodhart-verification@3.6.0-rc.1`, 14 universal slots consolidating 74 subchecks).",
        "releases": {
            f"{comp_id}@{rel_id}": {
                "coverage": "tree",
                "descriptor": comp_descriptor_rel,
                "descriptor_file_sha256": comp_desc_sha,
                "entry_count": len(v2_paths),
                "legacy_tree_sha256": legacy_hash,
                "metadata_sha256": metadata_sha256,
                "regular_file_bytes": regular_bytes,
                "root": source_rel,
                "symlink_count": symlink_count,
                "tree_sha256": v2_hash,
            }
        },
    }
    write_json_yaml(attestation_path, attestation_doc)

    wf_descriptor_rel = f"workflows/{wf_id}/releases/{rel_id}/workflow.yaml"
    wf_lock_rel = f"workflows/{wf_id}/releases/{rel_id}/versions.lock"
    wf_descriptor_path = AWF_ROOT / wf_descriptor_rel
    wf_lock_path = AWF_ROOT / wf_lock_rel

    write_json_yaml(wf_descriptor_path, build_workflow_doc(wf_id, rel_id, comp_id))
    lock_doc = {
        "schema_version": 1,
        "workflow": wf_id,
        "workflow_release": rel_id,
        "locked_at": "2026-11-08",
        "components": {comp_id: rel_id},
    }
    write_json_yaml(wf_lock_path, lock_doc)

    wf_desc_sha = verify.file_sha256(wf_descriptor_path)
    wf_lock_sha = verify.file_sha256(wf_lock_path)

    registry_path = AWF_ROOT / "registry.yaml"
    registry = verify.read_manifest(registry_path)

    components = registry.setdefault("components", [])
    existing_comp_idx = next((i for i, c in enumerate(components) if c.get("id") == comp_id), None)
    if existing_comp_idx is None:
        raise RuntimeError(f"Component {comp_id} not found in registry.yaml")
    components[existing_comp_idx]["latest_release"] = rel_id
    components[existing_comp_idx]["descriptor_sha256"] = comp_desc_sha

    registry.setdefault("global_components", {})[comp_id] = rel_id
    attestations = registry.setdefault("integrity_attestations", [])
    if attestation_rel not in attestations:
        attestations.append(attestation_rel)

    req_list = registry["integrity_policy"]["required_release_attestations"]
    ref_str = f"{comp_id}@{rel_id}"
    if ref_str not in req_list:
        req_list.append(ref_str)
        req_list.sort()

    workflows = registry.setdefault("workflows", [])
    existing_wf_idx = next((i for i, w in enumerate(workflows) if w.get("id") == wf_id), None)
    if existing_wf_idx is None:
        raise RuntimeError(f"Workflow {wf_id} not found in registry.yaml")

    wf_entry = workflows[existing_wf_idx]
    wf_entry["descriptor"] = wf_descriptor_rel
    wf_entry["descriptor_sha256"] = wf_desc_sha
    wf_entry["lock"] = wf_lock_rel
    wf_entry["lock_sha256"] = wf_lock_sha
    wf_entry["status"] = "validated"
    wf_entry.setdefault("releases", {})[rel_id] = {
        "descriptor": wf_descriptor_rel,
        "descriptor_sha256": wf_desc_sha,
        "lock": wf_lock_rel,
        "lock_sha256": wf_lock_sha,
        "status": "validated",
    }

    write_json_yaml(registry_path, registry)
    print(f"Registered {comp_id}@{rel_id}, advanced global_components pointer, and updated workflow {wf_id}@{rel_id} successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
