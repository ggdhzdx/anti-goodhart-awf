"""Independent reference operators and inputs shared by positive and negative geometry cases."""
from __future__ import annotations
from collections import deque
from typing import Any, Dict, Sequence
import numpy as np
_OFFSETS_6 = [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)]
_OFFSETS_26 = [(i, j, k) for i in (-1, 0, 1) for j in (-1, 0, 1) for k in (-1, 0, 1) if (i, j, k) != (0, 0, 0)]

def _component_labels(mask: np.ndarray, offsets: Sequence[tuple]) -> np.ndarray:
    labels = np.zeros(mask.shape, dtype=np.int64)
    current = 0
    for seed in zip(*np.nonzero(mask)):
        if labels[seed]:
            continue
        current += 1
        labels[seed] = current
        queue = deque([seed])
        while queue:
            x, y, z = queue.popleft()
            for dx, dy, dz in offsets:
                nb = (x + dx, y + dy, z + dz)
                if all((0 <= nb[a] < mask.shape[a] for a in range(3))) and mask[nb] and (not labels[nb]):
                    labels[nb] = current
                    queue.append(nb)
    return labels

def _euler_characteristic_6_complex(fg: np.ndarray) -> int:
    """chi = V - E + F - C of the 6-adjacency voxel complex (voxels as vertices, filled squares / cubes)."""
    v = int(fg.sum())
    e = int(np.sum(fg[1:, :, :] & fg[:-1, :, :]) + np.sum(fg[:, 1:, :] & fg[:, :-1, :]) + np.sum(fg[:, :, 1:] & fg[:, :, :-1]))
    f_xy = np.sum(fg[1:, 1:, :] & fg[:-1, 1:, :] & fg[1:, :-1, :] & fg[:-1, :-1, :])
    f_xz = np.sum(fg[1:, :, 1:] & fg[:-1, :, 1:] & fg[1:, :, :-1] & fg[:-1, :, :-1])
    f_yz = np.sum(fg[:, 1:, 1:] & fg[:, :-1, 1:] & fg[:, 1:, :-1] & fg[:, :-1, :-1])
    cube = np.ones(tuple((s - 1 for s in fg.shape)), dtype=bool)
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                cube &= fg[dx:fg.shape[0] - 1 + dx, dy:fg.shape[1] - 1 + dy, dz:fg.shape[2] - 1 + dz]
    return v - e + int(f_xy + f_xz + f_yz) - int(cube.sum())

def digital_homology_betti_chi(g: np.ndarray, background_offsets: Sequence[tuple]=tuple(_OFFSETS_26)) -> np.ndarray:
    """(beta_0, beta_1, beta_2, chi) for 6-adjacency foreground / 26-adjacency background (Jordan-Brouwer pair)."""
    fg = np.pad(np.asarray(g) > 0.5, 1)
    b0 = int(_component_labels(fg, _OFFSETS_6).max())
    bg_labels = _component_labels(~fg, background_offsets)
    border = set(np.unique(np.concatenate([bg_labels[0].ravel(), bg_labels[-1].ravel(), bg_labels[:, 0].ravel(), bg_labels[:, -1].ravel(), bg_labels[:, :, 0].ravel(), bg_labels[:, :, -1].ravel()])).tolist())
    b2 = len(set(np.unique(bg_labels).tolist()) - border - {0})
    chi = _euler_characteristic_6_complex(fg)
    return np.array([b0, b0 + b2 - chi, b2, chi], dtype=np.float64)

def _void_spectrum(clearance: np.ndarray, c_min: float) -> np.ndarray:
    taus = float(c_min) + np.array([0.0, 0.25, 0.5])
    void = np.array([100.0 * float(np.mean(clearance > t)) for t in taus])
    return np.array([100.0 - void[0], void[0], void[1], void[2]])

def sphere_clearance_exact(points: np.ndarray, centers: np.ndarray, radii: np.ndarray, c_min: float) -> np.ndarray:
    surf = np.linalg.norm(points[:, None, :] - centers[None, :, :], axis=2) - radii[None, :]
    return _void_spectrum(np.min(surf, axis=1), c_min)

def sphere_clearance_specs() -> Dict[str, Dict[str, Any]]:
    centers = np.array([[0.0, 0.0, 0.0], [2.0, 0.0, 0.0]])
    radii = np.array([0.5, 1.8])
    grid_pts = np.column_stack([np.linspace(-1.5, 4.5, 13), np.full(13, 0.4), np.zeros(13)])
    return {'base': {'points': grid_pts, 'centers': centers, 'radii': radii, 'c_min': 0.2}, 'probe': {'points': np.array([[0.7, 0.0, 0.0]]), 'centers': centers, 'radii': radii, 'c_min': 0.0}}

def _stack_observables(d_perp: float, n_hat: np.ndarray, coherence_weight: float) -> np.ndarray:
    n_layers = float(len(n_hat))
    return np.array([d_perp, 2.0 * np.pi / d_perp, (n_layers - 1.0) * d_perp, n_layers * d_perp * coherence_weight])

def stack_diffraction_exact(centers: np.ndarray, sub_normals: np.ndarray) -> np.ndarray:
    n_hat = sub_normals / np.linalg.norm(sub_normals, axis=1, keepdims=True)
    d_perp = float(np.mean(np.abs(np.sum(np.diff(centers, axis=0) * n_hat[:-1], axis=1))))
    return _stack_observables(d_perp, n_hat, float(np.mean(np.abs(n_hat[:, 2]))))

def stack_diffraction_specs() -> Dict[str, Dict[str, Any]]:
    layer = np.arange(6, dtype=np.float64)
    normals = np.tile(np.array([[0.0, 0.0, 1.0]]), (6, 1))
    aligned = np.column_stack([np.zeros(6), np.zeros(6), 3.5 * layer])
    slipped = np.column_stack([1.2 * layer, np.zeros(6), 3.5 * layer])
    return {'base': {'centers': aligned, 'sub_normals': normals}, 'slipped': {'centers': slipped, 'sub_normals': normals.copy()}, 'short': {'centers': aligned[:2].copy(), 'sub_normals': normals[:2].copy()}}
