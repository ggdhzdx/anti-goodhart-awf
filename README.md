# AWF Anti-Goodhart Suite (`AWF DesignAG` + `AWF Guard` + `AWF Tutor`)

Public, portable distribution of the **Agent Workflow Foundry (AWF)** two-layer Anti-Goodhart verification and co-evolutionary tutoring suite:

1. **`AWF DesignAG` (`design-anti-goodhart@1.0.0-rc.1` / `skill.design-anti-goodhart@1.0.0-rc.1`)**:
   - **18 Automated Design & Pedagogical Gates (`D1`–`D18`)** and **7 Redlines (`R1`–`R7`)** for scientific presentations (`HTML-PPT` & editable `PPTX`).
   - **Dual Quantitative Rubric Scorer**:
     - *Mode 1 — Organic Optoelectronic / OLED Deep-Mechanism Rubric v3* (`01_optoelectronic_scoring_criteria_v3.md`, 100 pts + `R1`–`R7` up to `-15` pts, enforcing the multiplicative law $A_i = w_i \times C_{\text{clarity}} \times V_{\text{visual}}$ that caps `V0` pure-text slides at `30%`).
     - *Mode 2 — Supramolecular & Popular-Science 5-Dimension Rubric* (`02_supermolecule_SCORING_CRITERIA_5dim.md`, 100 pts calibrated against 39 real user feedback items).
2. **`AWF Guard` (`anti-goodhart-verification@3.4.0-rc.1` / `skill.anti-goodhart-verification@3.4.0-rc.1`)**:
   - **66 Automated Code & Scientific Computing Anti-Goodhart Gates (`G1`–`G7`)**: Static `-inf` placeholder/magic-number circuit-breaker (`G5n`), 6-Dimensional Micro-Step Sufficiency & 1-Hop Topological DAG Anchor (`G6o`), Red-Blue Adversarial Auditor Decoupled Game (`G7h`), Analytical Gradient vs. 4th-Order Richardson Finite-Difference (`G2b`), Asymptotic Convergence Order $O(h^p)$ (`G1d`), 3D $SE(3)$ + Triclinic PBC Minimum-Image + $S_N$ Permutation Equivariance (`G3i`), Physical Matrix Hermiticity/PSD/Detailed-Balance (`G5m`), Pairwise Exchange Symmetry & Self-Interaction Exclusion (`G5o`), Exact Hat-Matrix LOOCV (`G7i`), Euler Scale Homogeneity (`G3j`), Autonomous Remediation Closed-Loop (`G6p`), Bipolar Sign Reachability (`G5p`), Mutmut AST Mutation Kill-Rate (`G5j`), SplitGuard BLAKE2b Row-Taint Leakage (`G7g`), Monte Carlo Arithmetic Conditioning (`G1c`), and `@scientific_atom` Physical-Unit/Symbolic-Shape Contract Bus.
3. **`AWF Tutor V16` (`adaptive-interactive-tutor@1.0.0-rc.14` / `skill.adaptive-interactive-tutor@1.0.0-rc.14` + `skill.html-ppt@1.0.0-rc.3`)**:
   - Scale-Adaptive Fractal Curriculum (`Chapter -> Station -> 3-Gate Micro-Loop`), 7-Element Methodological Anatomy, Tutor-Driven Design (`TDD` / 以教代建), Human-Gated Multimedia Testbed, and Cognitive-Trajectory HTML-PPT synthesis delegating code verification to `AWF Guard` and visual/PPT verification to `AWF DesignAG`.

## Included Locked Closure

- `skill.design-anti-goodhart@1.0.0-rc.1` (`awf/components/skills/design-anti-goodhart/releases/1.0.0-rc.1/source/`)
- `skill.anti-goodhart-verification@3.4.0-rc.1` (`awf/components/skills/anti-goodhart-verification/releases/3.4.0-rc.1/source/`)
- `skill.adaptive-interactive-tutor@1.0.0-rc.14` (`awf/components/skills/adaptive-interactive-tutor/releases/1.0.0-rc.14/source/`)
- `skill.html-ppt@1.0.0-rc.3` (`awf/components/skills/html-ppt/releases/1.0.0-rc.3/source/`)
- Workflow descriptors & exact `versions.lock` files under `awf/workflows/`
- Mergeable registry fragment at `awf/registry.fragment.json`

## Quick Verification

```bash
# 1. Verify full repository manifest, hashes, locks, AST syntax, and run all 66 + 18 gate self-tests
python verify.py

# 2. Run AWF DesignAG 18-gate positive/negative self-test & self-hosting audit directly
python awf/components/skills/design-anti-goodhart/releases/1.0.0-rc.1/source/scripts/awf_design_anti_goodhart_gates.py --self-test
python awf/components/skills/design-anti-goodhart/releases/1.0.0-rc.1/source/scripts/awf_design_anti_goodhart_gates.py --audit-self

# 3. Run AWF Guard 66-gate self-test & self-hosting audit directly
python awf/components/skills/anti-goodhart-verification/releases/3.4.0-rc.1/source/scripts/awf_universal_anti_goodhart_gates.py --self-test
python awf/components/skills/anti-goodhart-verification/releases/3.4.0-rc.1/source/scripts/awf_universal_anti_goodhart_gates.py --audit-self
```
