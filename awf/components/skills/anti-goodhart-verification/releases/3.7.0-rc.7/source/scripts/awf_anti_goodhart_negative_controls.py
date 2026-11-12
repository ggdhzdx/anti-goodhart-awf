"""
Negative-control suite for AWF Guard (`skill.anti-goodhart-verification@3.7.0-rc.2`).

The v3.7.0-rc.1 force-PASS mutation audit showed that 24 of 55 public gate functions could be replaced by
an always-PASS stub without the self-test noticing, because their self-tests only asserted PASS on good
inputs. Every such gate gets at least one known-wrong implementation here that MUST be rejected, plus the
real-operator fixtures (digital homology, sphere clearance, stacked-director diffraction) shared with the
positive self-test. All checks use explicit `raise AssertionError` so they survive `python -O`.
"""
from __future__ import annotations
import json
import tempfile
from collections import deque
from pathlib import Path
from typing import Any, Callable, Dict, List, Sequence
import numpy as np
from awf_universal_anti_goodhart_gates import SecondOrderCollusionError, AntiGoodhartGateError, StationVerificationSpec, audit_ast_path, audit_benchmark_directory, audit_engine_self_hosting_integrity, audit_parameter_update_trajectory, audit_spec_integrity, evaluate_universal_declarative_slots, scan_ast_for_hardcoded_short_loops, scan_ast_for_pre_split_preprocessing_leakage, verify_bipolar_reachability_and_multisource_variance, verify_coupled_basis_sign_gauge_and_locality_bounds, verify_euler_poincare_and_digital_duality, verify_filtration_monotonicity_and_heterogeneous_radius_clearance, verify_loocv_generalization_and_train_eval_parity, verify_mesh_refinement_invariance_and_noise_floor, verify_nonorthogonal_pencil_gauge_and_spectral_parity, verify_pairwise_no_self_interaction_and_symmetry, verify_remediation_closed_loop_and_pareto_candidates, verify_rp2_director_gauge_and_reciprocal_conjugacy, verify_scale_homogeneity_and_rank1_null_calibration, verify_verity_receipt_payload, verify_weighted_dispersion_kish_and_scale_invariance
from awf_guard_selftests.geometry_fixtures import _OFFSETS_26, _OFFSETS_6, _component_labels, _euler_characteristic_6_complex, _stack_observables, _void_spectrum, digital_homology_betti_chi, sphere_clearance_exact, sphere_clearance_specs, stack_diffraction_exact, stack_diffraction_specs

def digital_homology_6_6_bug(g: np.ndarray) -> np.ndarray:
    return digital_homology_betti_chi(g, background_offsets=tuple(_OFFSETS_6))

def sphere_clearance_nearest_center_bug(points: np.ndarray, centers: np.ndarray, radii: np.ndarray, c_min: float) -> np.ndarray:
    raw = np.linalg.norm(points[:, None, :] - centers[None, :, :], axis=2)
    idx = np.argmin(raw, axis=1)
    return _void_spectrum(raw[np.arange(len(points)), idx] - radii[idx], c_min)

def stack_diffraction_center_to_center_bug(centers: np.ndarray, sub_normals: np.ndarray) -> np.ndarray:
    n_hat = sub_normals / np.linalg.norm(sub_normals, axis=1, keepdims=True)
    d_c = float(np.mean(np.linalg.norm(np.diff(centers, axis=0), axis=1)))
    return _stack_observables(d_c, n_hat, float(np.mean(np.abs(n_hat[:, 2]))))

def stack_diffraction_sign_sensitive_bug(centers: np.ndarray, sub_normals: np.ndarray) -> np.ndarray:
    n_hat = sub_normals / np.linalg.norm(sub_normals, axis=1, keepdims=True)
    d_perp = float(np.mean(np.abs(np.sum(np.diff(centers, axis=0) * n_hat[:-1], axis=1))))
    return _stack_observables(d_perp, n_hat, float(np.mean(n_hat[:, 2])))

def _gate_fail_issue(label: str, result: Dict[str, Any], needle: str) -> str:
    """Return "" when `result` is a non-PASS verdict whose violations mention `needle`, else a diagnostic."""
    text = json.dumps(result.get('violations', result.get('pair_regression_violations', [])), default=str)
    if result.get('status') == 'PASS' or (needle and needle not in text):
        return f"[{label}] expected FAIL mentioning `{needle}`, got status={result.get('status')}: {text[:240]}"
    return ''

def _raises_issue(label: str, fn: Callable[[], Any], exc_type: type, needle: str) -> str:
    try:
        fn()
    except exc_type as exc:
        return '' if needle in str(exc) else f'[{label}] raised but message lacks `{needle}`: {exc}'
    return f'[{label}] expected {exc_type.__name__} containing `{needle}`, but call returned normally'

def _kish_dispersion(vals: np.ndarray, weights: np.ndarray) -> np.ndarray:
    wn = weights / float(np.sum(weights))
    mu = float(np.sum(wn * vals))
    eff_n = 1.0 / float(np.sum(wn ** 2))
    sd = float(np.sqrt(float(np.sum(wn * (vals - mu) ** 2)) * (eff_n / (eff_n - 1.0))))
    g_raw = sd / mu * 100.0
    return np.array([mu, sd, g_raw, g_raw / float(np.sqrt(2.0 * np.pi))], dtype=np.float64)

def _coupled_sr_fixture(full_system: bool, coherent: bool) -> Callable[..., np.ndarray]:
    sl = slice(0, 4) if full_system else slice(0, 2)

    def sr_operator(h_ex_ev: np.ndarray, mu_vecs_debye: np.ndarray, coords_ang: np.ndarray) -> np.ndarray:
        _, evecs = np.linalg.eigh(h_ex_ev[sl, sl])
        c0 = evecs[:, 0]
        p0 = c0 ** 2
        pr0 = 1.0 / float(np.sum(p0 ** 2))
        incoh = float(p0 @ np.sum(mu_vecs_debye[sl] ** 2, axis=1))
        m_sq = float(np.sum((c0 @ mu_vecs_debye[sl]) ** 2)) if coherent else incoh
        eta = m_sq / max(incoh, 1e-12)
        r_mean = p0 @ coords_ang[sl]
        rg = float(np.sqrt(max(float(p0 @ np.sum((coords_ang[sl] - r_mean) ** 2, axis=1)), 0.0)))
        return np.array([pr0, pr0, eta, 0.85 * eta, eta, rg], dtype=np.float64)
    return sr_operator

def coupled_sr_inputs() -> Dict[str, np.ndarray]:
    h_sr = np.array([[1.8, -0.04, 1e-05, 0.0], [-0.04, 1.8, 0.0, 1e-05], [1e-05, 0.0, 1.8, -0.04], [0.0, 1e-05, -0.04, 1.8]])
    mu_sr = np.tile(np.array([[10.0, 0.0, 0.0]]), (4, 1))
    c_sr1 = np.array([[0.0, 0.0, 0.0], [4.0, 0.0, 0.0], [40.0, 0.0, 0.0], [44.0, 0.0, 0.0]])
    c_sr2 = np.array([[0.0, 0.0, 0.0], [4.0, 0.0, 0.0], [90.0, 0.0, 0.0], [94.0, 0.0, 0.0]])
    return {'h': h_sr, 'mu': mu_sr, 'c1': c_sr1, 'c2': c_sr2}

def _verify_negative_pairwise_loocv_scale() -> int:
    """G5o / G7i / G3j: asymmetric kernels, intra-group leakage, over-fit LOOCV, train/eval skew, biases, null drift."""
    pts_a = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]])
    pts_b = np.array([[0.0, 0.0, 3.0], [1.0, 0.0, 3.0]])

    def sym_kernel(pa: np.ndarray, pb: np.ndarray) -> float:
        return float(np.exp(-np.linalg.norm(np.mean(pa, axis=0) - np.mean(pb, axis=0))))

    def leaky_aggregator(groups: List[np.ndarray], gids: List[int]) -> float:
        return float(sum((sym_kernel(groups[i], groups[j]) for i in range(len(groups)) for j in range(i + 1, len(groups)))))
    rng = np.random.default_rng(7)
    x_good = np.array([[1.0], [2.0], [3.0], [4.0], [5.0], [6.0]])
    y_good = np.array([2.1, 3.9, 6.1, 8.0, 9.9, 12.1])
    centered_svd = lambda m: float(np.linalg.svd(m - np.outer(np.mean(m, axis=1), np.ones(m.shape[1])), compute_uv=False)[0])
    issues = [_gate_fail_issue('G5o asymmetric kernel', verify_pairwise_no_self_interaction_and_symmetry(lambda pa, pb: float(np.sum(pa) - 2.0 * np.sum(pb)), pts_a, pts_b), 'exchange symmetry'), _gate_fail_issue('G5o intra-group leakage', verify_pairwise_no_self_interaction_and_symmetry(sym_kernel, pts_a, pts_b, grouped_aggregator_fn=leaky_aggregator), 'Intra-group'), _gate_fail_issue('G7i over-fit noise regression', verify_loocv_generalization_and_train_eval_parity(rng.normal(size=(6, 5)), rng.normal(size=6)), 'LOOCV'), _gate_fail_issue('G7i train/eval skew', verify_loocv_generalization_and_train_eval_parity(x_good, y_good, calibrate_feature_fn=lambda arr: arr * 2.0, eval_feature_fn=lambda arr: arr * 2.0 + 0.001, parity_test_inputs=[np.array([1.0, 2.0])]), 'skew'), _gate_fail_issue('G3j additive bias', verify_scale_homogeneity_and_rank1_null_calibration(lambda m: centered_svd(m) + 0.1, np.array([[1.0, -1.0], [-1.0, 1.0]]), homogeneity_degree=1.0), 'homogeneity'), _gate_fail_issue('G3j uncalibrated rank-1 null', verify_scale_homogeneity_and_rank1_null_calibration(lambda m: float(np.max(m)), np.array([[1.0, 2.0], [3.0, 4.0]]), homogeneity_degree=1.0, rank1_null_input_builder_fn=lambda p: np.outer(np.full(6, p), np.ones(6)), null_metric_extractor_fn=lambda val: float(val)), 'rank-1')]
    bad = [msg for msg in issues if msg]
    if bad:
        raise AssertionError('Negative controls (G5o/G7i/G3j) not rejected:\n' + '\n'.join(bad))
    return len(issues)

def _verify_negative_remediation_bipolar_mesh() -> int:
    """G6p / G5p / G1e: watered-down fixes, oracle-failing candidates, non-negative surrogates, extensive drift."""
    pre_src = "def f(d, x):\n    if x > 3:\n        return d['a'] * x\n    if x > 2:\n        return d['b'] * x\n    if x > 1:\n        return d['c'] * x\n    if x > 0:\n        return d['d'] * x\n    return -d['a'] * x\n"
    collapsed_src = "def f(d, x):\n    return d['a'] * x\n"
    evals = [{'x': np.array([1.0, 2.0])}, {'x': np.array([3.0, 4.0])}]
    good = {'cand_best': lambda x: x * 2.0}
    g6p_collapse = verify_remediation_closed_loop_and_pareto_candidates(pre_src, collapsed_src, good, lambda x: x * 2.0, evals)
    g6p_wrong = verify_remediation_closed_loop_and_pareto_candidates(pre_src, pre_src, {'bad': lambda x: x + 1.0}, lambda x: x * 2.0, evals)
    g6p_loosen = verify_remediation_closed_loop_and_pareto_candidates(pre_src, pre_src, good, lambda x: x * 2.0, evals, tolerance_loosened=True)

    def ramp_builder(n_g: int) -> Dict[str, Any]:
        return {'grid': np.tile(np.linspace(0.0, 1.0, n_g)[:, None], (1, n_g)), 'h': 4.0 / float(n_g)}

    def minmax_integral(grid: np.ndarray, h: float) -> float:
        return float(np.sum((grid - grid.min()) / (np.ptp(grid) + 1e-300)) * h ** 2)
    noisy = np.ones((16, 16)) + 1e-08 * np.random.default_rng(3).normal(size=(16, 16))
    issues = [_gate_fail_issue('G6p complexity collapse', g6p_collapse, 'ComplexityCollapse'), '' if g6p_wrong['status'] != 'PASS' and g6p_wrong['selected_pareto_candidate'] is None else '[G6p oracle-failing candidate accepted]', '' if g6p_loosen['status'] == 'ESCALATE_TO_HUMAN' else '[G6p tolerance loosening not escalated]', _gate_fail_issue('G5p non-negative surrogate', verify_bipolar_reachability_and_multisource_variance(lambda x: float(x) ** 2, -2.5, 3.2), 'negative-regime'), _gate_fail_issue('G5p single-source variance', verify_bipolar_reachability_and_multisource_variance(lambda x: float(x), -2.5, 3.2, variance_propagator_fn=lambda v_obs, means, v_ref: float(v_obs), baseline_fn=lambda theta: float(0.5 * theta[0] + 0.5 * theta[1])), 'Single-source'), _gate_fail_issue('G1e extensive voxel-count drift', verify_mesh_refinement_invariance_and_noise_floor(lambda grid, h: float(np.sum(grid)), ramp_builder, max_refinement_rel_drift=1e-06), 'Mesh-refinement'), _gate_fail_issue('G1e min-max noise stretching', verify_mesh_refinement_invariance_and_noise_floor(minmax_integral, ramp_builder, max_refinement_rel_drift=0.2, noisy_null_input_kwargs={'grid': noisy, 'h': 0.25}, expected_null_output=0.0), 'noise-floor')]
    bad = [msg for msg in issues if msg]
    if bad:
        raise AssertionError('Negative controls (G6p/G5p/G1e) not rejected:\n' + '\n'.join(bad))
    return len(issues)

def _verify_negative_topology_clearance_director() -> int:
    """G5q / G5r / G3k: (6,6) adjacency bug, memorized homology, k=1 center trap, slip inflation, vacuous probes."""
    shell = np.zeros((5, 5, 5))
    shell[1:4, 1:4, 1:4] = 1.0
    shell[2, 2, 2] = 0.0
    punct = shell.copy()
    punct[1, 1, 1] = 0.0
    curve = np.zeros((5, 5, 5))
    curve[1:4, 2, 2] = 1.0
    table = {'s': [1.0, 0.0, 1.0, 2.0], 'p': [1.0, 0.0, 0.0, 1.0], 'c': [1.0, 0.0, 0.0, 1.0]}
    sum_memorizer = lambda g: np.array([1.0, 0.0, 1.0, 2.0]) if float(np.sum(g)) == 26.0 else np.array([1.0, 0.0, 0.0, 1.0])
    clr = sphere_clearance_specs()
    stk = stack_diffraction_specs()
    g3k = verify_rp2_director_gauge_and_reciprocal_conjugacy
    issues = [_gate_fail_issue('G5q (6,6) adjacency bug', verify_euler_poincare_and_digital_duality(digital_homology_6_6_bug, {'g': shell}, {'g': punct}, {'g': curve}), 'homology mismatch'), _gate_fail_issue('G5q label lookup table', verify_euler_poincare_and_digital_duality(lambda tag: np.array(table[tag]), {'tag': 's'}, {'tag': 'p'}, {'tag': 'c'}), '3-D ndarray'), _gate_fail_issue('G5q voxel-sum memorizer', verify_euler_poincare_and_digital_duality(sum_memorizer, {'g': shell}, {'g': punct}, {'g': curve}), 'Gate-generated'), _gate_fail_issue('G5r k=1 nearest-center trap', verify_filtration_monotonicity_and_heterogeneous_radius_clearance(sphere_clearance_nearest_center_bug, clr['base'], clr['probe']), 'Heterogeneous-radius'), _gate_fail_issue('G5r vacuous probe', verify_filtration_monotonicity_and_heterogeneous_radius_clearance(sphere_clearance_exact, clr['base'], dict(clr['base'])), 'Vacuous probe'), _gate_fail_issue('G3k center-to-center slip inflation', g3k(stack_diffraction_center_to_center_bug, stk['base'], slipped_stack_kwargs=stk['slipped'], short_stack_kwargs=stk['short']), 'Lateral-slip'), _gate_fail_issue('G3k director sign sensitivity', g3k(stack_diffraction_sign_sensitive_bug, stk['base'], slipped_stack_kwargs=stk['slipped'], short_stack_kwargs=stk['short']), 'headless-director'), _gate_fail_issue('G3k slipped probe equals base', g3k(stack_diffraction_center_to_center_bug, stk['base'], slipped_stack_kwargs=dict(stk['base']), short_stack_kwargs=stk['short']), 'Vacuous probe'), _gate_fail_issue('G3k probes omitted', g3k(stack_diffraction_center_to_center_bug, stk['base']), 'Required probe')]
    bad = [msg for msg in issues if msg]
    if bad:
        raise AssertionError('Negative controls (G5q/G5r/G3k) not rejected:\n' + '\n'.join(bad))
    return len(issues)

def _verify_negative_dispersion_pencil_coupled() -> int:
    """G5s / G5t / G3l: unweighted dispersion, missing Lowdin S^-1/2, incoherent sums, cross-cluster delocalization."""
    vals = np.array([3.45, 3.5, 3.55, 3.6])
    base_w = {'vals': vals, 'weights': np.ones(4)}
    padded = {'vals': np.append(vals, [25.0, 50.0]), 'weights': np.array([1.0, 1.0, 1.0, 1.0, 0.0, 0.0])}
    s_toy = np.array([[1.0, 0.0, 0.05, -0.02], [0.0, 1.0, 0.03, 0.04], [0.05, 0.03, 1.0, 0.0], [-0.02, 0.04, 0.0, 1.0]])
    f_toy = np.array([[-8.0, 0.0, 0.12, -0.08], [0.0, -7.5, 0.09, 0.15], [0.12, 0.09, -8.0, 0.0], [-0.08, 0.15, 0.0, -7.5]])
    j_toy = np.array([[-0.02, 0.0], [0.0, -0.01]])

    def no_lowdin_diabat(s_mat: np.ndarray, f_mat: np.ndarray, j_coul: np.ndarray) -> np.ndarray:
        t_sub = f_mat[0:2, 2:4]
        j_val = float(j_coul[0, 0]) * 1000.0
        return np.array([abs(float(t_sub[1, 1])), float(np.linalg.norm(t_sub)), 0.1, 0.25, j_val, -j_val])
    sr = coupled_sr_inputs()
    sr_base = {'h_ex_ev': sr['h'], 'mu_vecs_debye': sr['mu'], 'coords_ang': sr['c1']}
    sr_far = {'h_ex_ev': sr['h'], 'mu_vecs_debye': sr['mu'], 'coords_ang': sr['c2']}
    g3l = verify_coupled_basis_sign_gauge_and_locality_bounds
    issues = [_gate_fail_issue('G5s unweighted dispersion', verify_weighted_dispersion_kish_and_scale_invariance(lambda vals, weights: _kish_dispersion(vals, np.ones_like(vals)), base_w, 'vals', zero_weight_padded_kwargs=padded), 'Zero-weight'), _gate_fail_issue('G5t missing Lowdin orthogonalization', verify_nonorthogonal_pencil_gauge_and_spectral_parity(no_lowdin_diabat, {'s_mat': s_toy, 'f_mat': f_toy, 'j_coul': j_toy}, (('f_mat', 's_mat'),)), 'metric-shift'), _gate_fail_issue('G3l incoherent sum', g3l(_coupled_sr_fixture(False, False), sr_base, separated_cluster_shifted_kwargs=sr_far, max_cluster_size=2), 'Insensitive'), _gate_fail_issue('G3l cross-cluster delocalization', g3l(_coupled_sr_fixture(True, True), sr_base, separated_cluster_shifted_kwargs=sr_far, max_cluster_size=2), ''), _gate_fail_issue('G3l vacuous locality probe', g3l(_coupled_sr_fixture(False, True), sr_base, separated_cluster_shifted_kwargs=dict(sr_base), max_cluster_size=2), 'Vacuous probe')]
    bad = [msg for msg in issues if msg]
    if bad:
        raise AssertionError('Negative controls (G5s/G5t/G3l) not rejected:\n' + '\n'.join(bad))
    return len(issues)

def _verify_negative_declarative_slots() -> int:
    """S1.1 / S3.1 / S5.1 declarative injector: empty, diluted, identity, tautological and wrong laws."""

    def wrong_parity(x: np.ndarray) -> np.ndarray:
        return np.asarray(x) + 1.0
    base = {'x': np.array([1.0, 2.0])}
    flip = {'x': np.array([-1.0, -2.0])}
    ev = evaluate_universal_declarative_slots
    eq = lambda **kw: {'s3_1_equivariance_laws': [dict({'name': 'parity', 'transformed_kwargs': flip}, **kw)]}
    issues = [_gate_fail_issue('Decl empty laws', ev(wrong_parity, base, {}), 'nothing was verified'), _gate_fail_issue('Decl wrong invariance', ev(wrong_parity, base, eq()), 'EquivarianceLaw'), _gate_fail_issue('Decl tol dilution', ev(wrong_parity, base, eq(tol=1000000000.0)), 'hard ceiling'), _gate_fail_issue('Decl vacuous sensitivity floor', ev(wrong_parity, base, eq(mode='sensitivity', tol=0.0)), 'Sensitivity floor'), _gate_fail_issue('Decl identity transform', ev(wrong_parity, base, {'s3_1_equivariance_laws': [{'name': 'id', 'transformed_kwargs': dict(base)}]}), 'identity transform'), _gate_fail_issue('Decl tautological predicate', ev(wrong_parity, base, {'s1_1_regime_probes': [{'name': 'p', 'input_kwargs': flip, 'predicate_fn': lambda out: True}]}), 'tautological predicate'), _gate_fail_issue('Decl NaN-swallowing residual', ev(wrong_parity, base, {'s5_1_manifold_laws': [{'name': 'bound', 'residual_fn': lambda out: max(0.0, float(out[0]) - 5.0), 'tol': 1e-09}]}), 'tautological residual')]
    bad = [msg for msg in issues if msg]
    if bad:
        raise AssertionError('Negative controls (declarative slots) not rejected:\n' + '\n'.join(bad))
    return len(issues)

def _write_long_function_source(n_body_lines: int) -> str:
    body = ''.join((f'    acc = acc + x * {i + 2}\n' for i in range(n_body_lines)))
    return 'def long_kernel(x):\n    acc = x\n' + body + '    return acc\n'

def _verify_negative_meta_and_static_gates() -> int:
    """Self-audit, Meta-Guard spec integrity, AST path, BenchJack directory, trajectory, loop, leakage, Verity."""

    def kernel(x: np.ndarray) -> np.ndarray:
        return x * 2.0
    spec_collusive = StationVerificationSpec(station_id='NC-1', station_name='collusive', target_fn=kernel, tier=2, orthogonal_oracle_fn=kernel, small_input_kwargs={'x': np.ones(3)})
    spec_diluted = StationVerificationSpec(station_id='NC-2', station_name='diluted', target_fn=kernel, tier=1, limit_tol=1.0)
    frozen = np.zeros((6, 4))
    frozen[:, 0] = np.arange(6, dtype=np.float64)
    with tempfile.TemporaryDirectory(prefix='ag_negctl_') as tmp:
        root = Path(tmp)
        (root / 'bad_engine.py').write_text('def f(x):\n    # TODO finish this\n    return x\n\n\n' + _write_long_function_source(201), encoding='utf-8')
        (root / 'bench').mkdir()
        (root / 'bench' / 'evaluate.py').write_text('def evaluate(pred, gold):\n    try:\n        return float(pred == gold)\n    except Exception:\n        return 1.0\n', encoding='utf-8')
        (root / 'nan_mask.py').write_text('import numpy as np\n\ndef f(x):\n    return np.nan_to_num(x)\n', encoding='utf-8')
        self_audit = audit_engine_self_hosting_integrity(root / 'bad_engine.py', max_fn_lines=200)
        bench = audit_benchmark_directory(root / 'bench')
        ast_res = audit_ast_path(root / 'nan_mask.py')
    issues = ['' if self_audit['status'] == 'FAIL' and self_audit['oversized_functions'] and (self_audit['g5n_finding_count'] > 0) else f'[Self-audit accepted TODO + over-200-line function] {self_audit}', '' if bench['status'] == 'FAIL' else f'[BenchJack directory accepted except->1.0 evaluator] {bench}', _gate_fail_issue('AST path nan_to_num', ast_res, 'nan_to_num'), _raises_issue('Meta-Guard collusive oracle', lambda: audit_spec_integrity(spec_collusive), SecondOrderCollusionError, 'Collusive'), _raises_issue('Meta-Guard threshold dilution', lambda: audit_spec_integrity(spec_diluted), SecondOrderCollusionError, 'Dilution'), _raises_issue('Frozen-DoF trajectory', lambda: audit_parameter_update_trajectory(frozen, 4), AntiGoodhartGateError, 'Frozen-DoF'), _raises_issue('Short loop', lambda: scan_ast_for_hardcoded_short_loops('for it in range(3):\n    x = it\n'), AntiGoodhartGateError, 'Loop-Truncation'), '' if scan_ast_for_pre_split_preprocessing_leakage('scaler.fit(X)\nX_tr, X_te = train_test_split(X)\n') else '[Pre-split fit before train_test_split not detected]', '' if verify_verity_receipt_payload('{not json')['accepted'] is False else '[Verity accepted malformed JSON]', '' if verify_verity_receipt_payload({'schema': 'wrong.v0', 'accepted': True})['accepted'] is False else '[Verity accepted wrong schema]']
    bad = [msg for msg in issues if msg]
    if bad:
        raise AssertionError('Negative controls (meta/static) not rejected:\n' + '\n'.join(bad))
    return len(issues)

def run_negative_controls() -> Dict[str, int]:
    """Run every negative-control group; raises AssertionError on the first group with an accepted wrong case."""
    groups = (_verify_negative_pairwise_loocv_scale, _verify_negative_remediation_bipolar_mesh, _verify_negative_topology_clearance_director, _verify_negative_dispersion_pencil_coupled, _verify_negative_declarative_slots, _verify_negative_meta_and_static_gates)
    counts = {grp.__name__: grp() for grp in groups}
    if sum(counts.values()) < len(groups):
        raise AssertionError(f'Negative-control registry is empty or truncated: {counts}')
    return counts
