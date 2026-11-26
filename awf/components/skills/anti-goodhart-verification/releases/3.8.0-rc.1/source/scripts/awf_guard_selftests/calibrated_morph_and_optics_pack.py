"""Compatibility coordinator for the historical calibrated pack."""
from .geometry_checks import _verify_geometry_checks
from .statistical_checks import _verify_statistical_checks
from .matrix_checks import _verify_matrix_checks
from .coupled_declarative_scenario import _verify_coupled_declarative_scenario

def _verify_calibrated_morph_and_optics_pack_selftests():
    result = {}
    result.update(_verify_geometry_checks())
    result.update(_verify_statistical_checks())
    result.update(_verify_matrix_checks())
    result.update(_verify_coupled_declarative_scenario())
    assert set(result) == {'euler_poincare_and_duality_spec', 'filtration_and_radius_clearance_spec', 'rp2_director_and_reciprocal_spec', 'weighted_dispersion_kish_spec', 'nonorthogonal_pencil_gauge_spec', 'coupled_basis_sign_gauge_spec', 'universal_slot_laws_spec'}
    return result
