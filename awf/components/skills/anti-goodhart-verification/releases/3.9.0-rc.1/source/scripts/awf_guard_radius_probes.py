"""Gate-owned paired geometries for the documented point/sphere interface."""
import copy
import numpy as np

SEMANTIC_FIELDS = ("points", "centers", "radii", "c_min")
PROBE_ORIGINS = ((0, 0, 0), (3, -2, 1))
PROBE_SCALES = (1, 2)
SMALL_RADIUS = 0.25
FAR_RADIUS = 3


def radius_probe_violations(function, base, names, extract, void_index, total, tol):
    """Only parameter names are configurable; geometry and expected results are not."""
    mapping = dict(zip(SEMANTIC_FIELDS, SEMANTIC_FIELDS)) if names is None else names
    if set(mapping) != set(SEMANTIC_FIELDS):
        return ["G5r requires a complete points/centers/radii/c_min argument-name contract"]
    if any(not isinstance(name, str) for name in mapping.values()) or len(set(mapping.values())) != len(mapping):
        return ["G5r geometry argument names must be distinct strings"]
    if any(name not in base for name in mapping.values()):
        return ["G5r geometry contract is unavailable; cannot certify caller-only probes"]
    violations = []
    for origin, scale in zip(PROBE_ORIGINS, PROBE_SCALES):
        point = np.asarray(origin, dtype=float)
        centers = point + scale * np.asarray(((1, 0, 0), (2, 0, 0)))
        results = []
        for far_radius in (SMALL_RADIUS, FAR_RADIUS):
            kwargs = copy.deepcopy(base)
            kwargs.update({mapping["points"]: point[None, :].copy(),
                           mapping["centers"]: centers.copy(),
                           mapping["radii"]: scale * np.asarray((SMALL_RADIUS, far_radius)),
                           mapping["c_min"]: 0})
            result = extract(function(**kwargs)).reshape(-1)
            results.append(float(result[void_index]))
        if abs(results[0] - total) > tol or abs(results[1]) > tol:
            violations.append("Heterogeneous-radius G5r gate-owned pair must change void fraction from total to zero")
    return violations
