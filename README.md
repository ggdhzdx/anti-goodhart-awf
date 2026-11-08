# AWF Anti-Goodhart Suite (`AWF DesignAG` + `AWF Guard` + `AWF HTML-PPT` + `AWF Tutor`)

Public, portable distribution of the **Agent Workflow Foundry (AWF)** two-layer Anti-Goodhart verification, Station-to-Slide `TDD-Slide` 1-Slide-Per-Step HTML-PPT, and co-evolutionary tutoring suite:

1. **`AWF DesignAG` (`design-anti-goodhart@1.0.0-rc.3` / `skill.design-anti-goodhart@1.0.0-rc.3`)**:
   - **18 Automated Design & Pedagogical Gates (`D1`–`D18`)** and **7 Redlines (`R1`–`R7`)** for scientific presentations (`HTML-PPT` & editable `PPTX`), including **strict 1-Slide-Per-Step micro-step enforcement (`max_slides_generated_per_step == 1`)**, **1-Hop Slide Topological Locking (`unverified_slide_hop_distance == 1`)**, and **Station-to-Slide Tutor-Driven Design (`tdd_station_capsule`) completeness verification** in `D16`.
   - **Dual Quantitative Rubric Scorer**:
     - *Mode 1 — Organic Optoelectronic / OLED Deep-Mechanism Rubric v3* (`01_optoelectronic_scoring_criteria_v3.md`, 100 pts + `R1`–`R7` up to `-15` pts, enforcing the multiplicative law $A_i = w_i \times C_{\text{clarity}} \times V_{\text{visual}}$ that caps `V0` pure-text slides at `30%`).
     - *Mode 2 — Supramolecular & Popular-Science 5-Dimension Rubric* (`02_supermolecule_SCORING_CRITERIA_5dim.md`, 100 pts calibrated against 39 real user feedback items).
2. **`AWF HTML-PPT V3` (`html-ppt@1.0.0-rc.2` / `skill.html-ppt@1.0.0-rc.5`)**:
   - **1-Slide-Per-Step + Station-to-Slide `TDD-Slide` + Human-in-the-Loop Enforcer (`audit_single_slide_step.py`)**: Physically forbids batch-generating `>1` slide in a single step, binds each slide 1-to-1 to a Tutor Station cognitive capsule (`--record-tdd-capsule`), enforces sequential 1-hop unlocking via `slide_manifest.json`, supports optional per-slide human sign-off (`--human-approve-slide`), and couples every slide to `AWF DesignAG` 18-Gate + Red-Blue visual adversarial verification.
3. **`AWF Guard` (`anti-goodhart-verification@3.5.0-rc.1` / `skill.anti-goodhart-verification@3.5.0-rc.1`)**:
   - **66 Automated Code & Scientific Computing Anti-Goodhart Gates (`G1`–`G7`)**: Static `-inf` placeholder/magic-number circuit-breaker (`G5n`), 6-Dimensional Micro-Step Sufficiency & 1-Hop Topological DAG Anchor (`G6o`), Red-Blue Adversarial Auditor Decoupled Game (`G7h`), Analytical Gradient vs. 4th-Order Richardson Finite-Difference (`G2b`), Asymptotic Convergence Order $O(h^p)$ (`G1d`), 3D $SE(3)$ + Triclinic PBC Minimum-Image + $S_N$ Permutation Equivariance (`G3i`), Physical Matrix Hermiticity/PSD/Detailed-Balance (`G5m`), Pairwise Exchange Symmetry & Self-Interaction Exclusion (`G5o`), Exact Hat-Matrix LOOCV (`G7i`), Euler Scale Homogeneity (`G3j`), Autonomous Remediation Closed-Loop (`G6p`), Bipolar Sign Reachability (`G5p`), Mutmut AST Mutation Kill-Rate (`G5j`), SplitGuard BLAKE2b Row-Taint Leakage (`G7g`), Monte Carlo Arithmetic Conditioning (`G1c`), and `@scientific_atom` Physical-Unit/Symbolic-Shape Contract Bus.
4. **`AWF Tutor V16` (`adaptive-interactive-tutor@1.0.0-rc.16` / `skill.adaptive-interactive-tutor@1.0.0-rc.16`)**:
   - Scale-Adaptive Fractal Curriculum (`Chapter -> Station -> 3-Gate Micro-Loop`), 7-Element Methodological Anatomy, Tutor-Driven Design (`TDD` / 以教代建), Human-Gated Multimedia Testbed, and Station-to-Slide Isomorphic TDD HTML-PPT synthesis (`1 Tutor Station == 1 TDD Capsule == 1 Slide`) delegating code verification to `AWF Guard`, 1-Slide-Per-Step TDD generation to `AWF HTML-PPT`, and visual/PPT verification to `AWF DesignAG`.

## Included Locked Closure

- `skill.design-anti-goodhart@1.0.0-rc.3` (`awf/components/skills/design-anti-goodhart/releases/1.0.0-rc.3/source/`)
- `skill.html-ppt@1.0.0-rc.5` (`awf/components/skills/html-ppt/releases/1.0.0-rc.5/source/`)
- `skill.anti-goodhart-verification@3.5.0-rc.1` (`awf/components/skills/anti-goodhart-verification/releases/3.5.0-rc.1/source/`)
- `skill.adaptive-interactive-tutor@1.0.0-rc.16` (`awf/components/skills/adaptive-interactive-tutor/releases/1.0.0-rc.16/source/`)
- Workflow descriptors & exact `versions.lock` files under `awf/workflows/`
- Mergeable registry fragment at `awf/registry.fragment.json`

## Quick Verification

```bash
# 1. Verify full repository manifest, hashes, locks, AST syntax, and run all 66 + 18 + TDD 1-Slide-Per-Step self-tests
python verify.py

# 2. Run AWF DesignAG 18-gate positive/negative self-test & self-hosting audit directly
python awf/components/skills/design-anti-goodhart/releases/1.0.0-rc.3/source/scripts/awf_design_anti_goodhart_gates.py --self-test
python awf/components/skills/design-anti-goodhart/releases/1.0.0-rc.3/source/scripts/awf_design_anti_goodhart_gates.py --audit-self

# 3. Run AWF HTML-PPT V3 (1-Slide-Per-Step + TDD Station Capsule + Human Gate) self-test directly
python awf/components/skills/html-ppt/releases/1.0.0-rc.5/source/scripts/audit_single_slide_step.py --self-test

# 4. Run AWF Guard 66-gate self-test & self-hosting audit directly
python awf/components/skills/anti-goodhart-verification/releases/3.5.0-rc.1/source/scripts/awf_universal_anti_goodhart_gates.py --self-test
python awf/components/skills/anti-goodhart-verification/releases/3.5.0-rc.1/source/scripts/awf_universal_anti_goodhart_gates.py --audit-self
```
