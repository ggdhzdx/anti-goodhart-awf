"""AWF Guard build selftest atoms and oracle: cohesive definitions behind the compatibility interface."""
from __future__ import annotations

from typing import Any
from typing import Callable
from awf_universal_anti_goodhart_gates import TensorSpec
from typing import Tuple
import numpy as np
from awf_universal_anti_goodhart_gates import scientific_atom


def _build_selftest_atoms_and_oracle() -> Tuple[Callable[..., Any], Callable[..., Any], Callable[..., Any]]:
    @scientific_atom(
        atom_id="ATOM-SELFTEST-KERNEL-00",
        tutor_station="Station_00_Radial_Shell_Area",
        math_contract=r"A(r_i) = 4\pi r_i^2",
        inputs={"r": TensorSpec(shape=("N",), unit="nm", domain=(0.0, 100.0), allow_untagged_array=True)},
        outputs={"area": TensorSpec(shape=("N",), unit="nm^2", domain=(0.0, 2e5), allow_untagged_array=True)},
        pure_function=True,
    )
    def compute_shell_area(r: np.ndarray) -> np.ndarray:
        """Compute spherical radial shell surface area 4*pi*r^2."""
        return 4.0 * np.pi * (r ** 2)

    @scientific_atom(
        atom_id="ATOM-SELFTEST-MEASURE-01",
        tutor_station="Station_01_Spherical_Measure_Integral",
        math_contract=r"I_i = f(r_i) \cdot A(r_i) \Delta r \cdot \mathbb{I}(r_i \ge 0.5)",
        inputs={
            "r": TensorSpec(shape=("N",), unit="nm", domain=(0.0, 100.0), allow_untagged_array=True),
            "f": TensorSpec(shape=("N",), unit="nm^-3", domain=(-1e6, 1e6), allow_untagged_array=True),
        },
        outputs={
            "weighted_shell": TensorSpec(shape=("N",), unit="dimensionless", domain=(-1e6, 1e6)),
        },
        downstream_atoms=("ATOM-SELFTEST-DOWNSTREAM-02",),
        pure_function=True,
    )
    def fast_spherical_integral(r: np.ndarray, f: np.ndarray, use_mask: bool = True) -> np.ndarray:
        """Compute discrete spherical shell volume-weighted integrand."""
        dr = abs(float(r[1] - r[0]))
        mask = (r >= 0.5) if use_mask else np.ones_like(r, dtype=bool)
        weights = compute_shell_area(r) * dr * mask
        return f * weights

    def slow_textbook_oracle(r: np.ndarray, f: np.ndarray, use_mask: bool = True) -> np.ndarray:
        dr = abs(float(r[1] - r[0]))
        out = []
        for idx in range(len(r)):
            rv = float(r[idx])
            fv = float(f[idx])
            if use_mask and rv < 0.5:
                out.append(0.0)
            else:
                out.append(fv * 4.0 * 3.141592653589793 * rv * rv * dr)
        return np.array(out, dtype=np.float64)

    return compute_shell_area, fast_spherical_integral, slow_textbook_oracle
