#!/usr/bin/env python3
"""
Co-located AWF Release Registration Script for AWF Guard
(skill.anti-goodhart-verification@3.4.0-rc.1 & workflow anti-goodhart-verification@3.4.0-rc.1).
Strictly follows ADR 0012 (rolling current pointer) and ADR 0022 (co-located scripts
inside the target Release source/ tree prior to execution).
Preserves `1.0.0` .. `3.3.0-rc.1` immutably and registers `3.4.0-rc.1` (Calibrated
Scientific Operator Invariant & Remediation Closed-Loop Pack, 66 automated gates).
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
            "six-mode-degenerate-shortcut-taxonomy-defense",
            "pre-execution-intra-function-parameter-taint-fixed-point-dataflow",
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
        "provenance": "Calibrated Scientific Operator Invariant & Remediation Closed-Loop Release 3.4.0-rc.1 of AWF Guard (`skill.anti-goodhart-verification@3.4.0-rc.1`, 66 automated gates): merges Tutor Implementation-Goodhart gates (`G5n`, `G6o`, `G7h`) with 5 domain-agnostic scientific computing gates and 4 AST/engine calibrations (`AG-Calib-01`..`AG-Calib-09`): `verify_pairwise_no_self_interaction_and_symmetry` (`G5o`), `verify_loocv_generalization_and_train_eval_parity` (`G7i`), `verify_scale_homogeneity_and_rank1_null_calibration` (`G3j`), `verify_remediation_closed_loop_and_pareto_candidates` (`G6p`), and `verify_bipolar_reachability_and_multisource_variance` (`G5p`).",
    }


def build_workflow_doc(wf_id: str, rel_id: str, comp_id: str) -> Dict[str, Any]:
    return {
        "schema_version": 1,
        "id": wf_id,
        "release": rel_id,
        "status": "validated",
        "purpose": "Standalone 100% Domain-Agnostic, Self-Hosting & Scientific-Computing-Native Universal 7-Gate Anti-Goodhart Verification Engine (66 Automated Sub-Gates across 17 Integrated Projects + Self-Hosting Dogfood Audit + Scientific Computing Method Development Pack + Tutor-Driven Implementation-Layer Anti-Goodhart Pack + Calibrated Scientific Operator Invariant Pack) incorporating AST Guard, Truth, Reward-Hack-Bench, EvilGenie, GemTest, BenchJack, Goodhart, Jaxtyping, Agent-Guardrails, Aurite Agent-Verifier, ImpossibleBench, FalseGreen/PyNose, Mutmut, Icontract/Deal/CrossHair, SplitGuard/DataLeakage, PitfallsFP/MCA Conditioning, Self-Hosting Dogfood Governance, Analytic Gradient/FD (`G2b`), Convergence Order (`G1d`), SE(3)/Triclinic-PBC/Permutation (`G3i`), Physical Matrix/Unit Invariants (`G5m`), Static -inf Circuit-Breaker (`G5n`), 6D Micro-Step Topological Anchor (`G6o`), Red-Blue Adversarial Decoupling (`G7h`), Pairwise Exchange Symmetry & Self-Interaction Exclusion (`G5o`), Exact LOOCV & Train/Eval Feature Parity (`G7i`), Euler Scale Homogeneity & Asymmetric Rank-1 Null Calibration (`G3j`), Autonomous Remediation Closed-Loop & Pareto Selection (`G6p`), and Bipolar Sign Reachability & Multi-Source Delta-Method Variance (`G5p`).",
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
        "engineering_gate": "Forbid 1,000+ line monolithic scripts, functions >160 lines, TODO/FIXME/placeholder stubs or unanchored magic numbers (`G5n`), multi-station leapfrogging or oversized McCabe/HALSTEAD/branch micro-steps (`G6o`), unreviewed single-agent reward self-grading without Red-Blue adversarial audit (`G7h`), intra-group self-interaction leakage (`G5o`), small-sample LOOCV over-parameterization or Train/Eval feature-extractor skew (`G7i`), unscaled hardcoded cutoffs or symmetric-only null baselines (`G3j`), watering-down code fixes (`G6p`), non-negative surrogates for bipolar physical quantities or single-source variance underestimation (`G5p`), hardcoded short optimization loops, unbounded loops/retries, hallucinated tools, LangGraph dead cycles, hardcoded secrets, bare/silent except-pass, silent numeric .get() defaults, dynamic eval/exec sinks, stateful call-counter cheating, conflicting canary spoofing, false-green hollow tests, self-mocking target functions, surviving AST mutants, loose tolerance inflation, in-place mutation of caller input arrays, boundary corner-case failures, pre-split fit/fit_transform data leakage, train/test duplicate row or group/conformer overlap (`splitguard`), explicit matrix inverse multiplication (`inv(A) @ b`), unstabilized `log(sum(exp(x)))`, ill-conditioned floating-point cancellation (`PitfallsFP` / MCA), wrong analytical gradients/forces (`G2b`), degraded numerical convergence orders (`G1d`), broken triclinic PBC minimum-image wrapping (`G3i`), non-Hermitian/non-PSD physical matrices or cross-atom unit mismatches (`G5m`), harness tampering, evaluator logic gaps, friendly-fire verifier over-tightening, symbolic/variadic tensor shape mismatches, out-of-scope file drift, parallel abstraction sprawl, invalid Verity receipts, external solution smuggling, and verbal over-claiming.",
        "scientific_gate": "All numerical and scientific operators must satisfy all 66 automated gates across G1-G7, including static -inf placeholder/magic-number circuit breaking (`G5n`), 6D micro-step topological anchoring (`G6o`), Red-Blue adversarial audit (`G7h`), pairwise exchange symmetry & intra-group self-interaction exclusion (`G5o`), exact hat-matrix leverage LOOCV & train/eval feature parity (`G7i`), Euler scale homogeneity & asymmetric rank-1 null calibration (`G3j`), autonomous remediation closed-loop & Pareto selection (`G6p`), bipolar sign reachability & multi-source Delta-method variance propagation (`G5p`), 4th-order Richardson finite-difference gradient consistency (`G2b`), asymptotic convergence order O(h^p) (`G1d`), 3D SE(3) rotation/translation + triclinic PBC minimum-image + S_N permutation equivariance (`G3i`), physical matrix Hermiticity/PSD/detailed-balance & cross-atom unit homogeneity (`G5m`), zero-violation self-hosting dogfood integrity (`G6n`), Monte Carlo Arithmetic (MCA) stochastic rounding stability (`G1c`), zero BLAKE2b row-taint leakage (`G7g`), Design-by-Contract input immutability (`G3g`), clean-room AST mutation kill-rate (`G5j`), and dual-path orthogonal oracle verification (`G2`).",
        "version_lock": "versions.lock",
    }


def main() -> int:
    comp_id = "skill.anti-goodhart-verification"
    wf_id = "anti-goodhart-verification"
    rel_id = "3.4.0-rc.1"

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
    attestation_rel = "attestations/release-integrity-20261108-anti-goodhart-verification-v3-4-rc1.yaml"
    attestation_path = AWF_ROOT / attestation_rel
    attestation_doc = {
        "schema_version": 1,
        "digest_contract": "awf-tree-v2",
        "observed_at": "2026-11-08",
        "owner": "awf-anti-goodhart-verification-release-20261108-v3-4-rc1",
        "provenance": "Validated Calibrated Scientific Operator Invariant & Remediation Closed-Loop release 3.4.0-rc.1 of standalone AWF Guard (`skill.anti-goodhart-verification@3.4.0-rc.1` and workflow `anti-goodhart-verification@3.4.0-rc.1`, 66 automated gates).",
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
