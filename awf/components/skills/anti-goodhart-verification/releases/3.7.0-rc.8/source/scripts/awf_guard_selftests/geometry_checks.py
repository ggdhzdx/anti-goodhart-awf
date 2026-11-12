"""Positive scenarios grouped by functional responsibility."""
from __future__ import annotations
from typing import Any
from typing import Dict
from awf_guard_selftests.geometry_fixtures import digital_homology_betti_chi
import numpy as np
from awf_guard_selftests.geometry_fixtures import sphere_clearance_exact
from awf_guard_selftests.geometry_fixtures import sphere_clearance_specs
from awf_guard_selftests.geometry_fixtures import stack_diffraction_exact
from awf_guard_selftests.geometry_fixtures import stack_diffraction_specs
from awf_universal_anti_goodhart_gates import verify_euler_poincare_and_digital_duality
from awf_universal_anti_goodhart_gates import verify_filtration_monotonicity_and_heterogeneous_radius_clearance
from awf_universal_anti_goodhart_gates import verify_rp2_director_gauge_and_reciprocal_conjugacy

def _verify_geometry_checks() -> Dict[str, Any]:
    shell_g = np.zeros((5, 5, 5), dtype=np.float64)
    shell_g[1:4, 1:4, 1:4] = 1.0
    shell_g[2, 2, 2] = 0.0
    punc_g = shell_g.copy()
    punc_g[1, 1, 1] = 0.0
    curve_g = np.zeros((5, 5, 5), dtype=np.float64)
    curve_g[1:4, 2, 2] = 1.0
    g5q_spec = {'homology_fn': digital_homology_betti_chi, 'sealed_shell_kwargs': {'g': shell_g}, 'corner_punctured_shell_kwargs': {'g': punc_g}, 'contractible_path_kwargs': {'g': curve_g}}
    assert verify_euler_poincare_and_digital_duality(**g5q_spec)['status'] == 'PASS'
    clr = sphere_clearance_specs()
    g5r_spec = {'clearance_fn': sphere_clearance_exact, 'base_input_kwargs': clr['base'], 'heterogeneous_radius_probe_kwargs': clr['probe']}
    assert verify_filtration_monotonicity_and_heterogeneous_radius_clearance(**g5r_spec)['status'] == 'PASS'
    stk = stack_diffraction_specs()
    g3k_spec = {'diffraction_fn': stack_diffraction_exact, 'base_input_kwargs': stk['base'], 'slipped_stack_kwargs': stk['slipped'], 'short_stack_kwargs': stk['short']}
    assert verify_rp2_director_gauge_and_reciprocal_conjugacy(**g3k_spec)['status'] == 'PASS'
    return {'euler_poincare_and_duality_spec': g5q_spec, 'filtration_and_radius_clearance_spec': g5r_spec, 'rp2_director_and_reciprocal_spec': g3k_spec}
