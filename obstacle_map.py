"""
obstacle_map.py
----------------
Builds a lightweight geometric map of every static obstacle body loaded into
PyBullet (city buildings, roads, fallback skyscraper boxes) and exposes a
vectorized repulsion-force helper that the APF engine (perfect_swarm.py)
calls once per physics tick.

Design notes
------------
* We deliberately do NOT re-query PyBullet's AABBs every tick for every
  drone/obstacle pair (that would mean hundreds of C calls per frame).
  Instead, `build_obstacle_aabbs()` is called ONCE after the city is loaded,
  producing a plain NumPy array of shape (N, 6): [xmin, ymin, zmin, xmax,
  ymax, zmax]. All later force computations are pure NumPy and vectorized
  over drones AND obstacles simultaneously.
* Repulsion uses the classic APF inverse-distance-squared law, but distance
  is measured to the *nearest point on the box surface* (clamped point),
  not to the box center -- this makes buildings behave like solid volumes
  rather than point masses, which is what lets a drone skim past a corner
  instead of being shoved away from the building's centroid.
"""

from __future__ import annotations
import numpy as np

try:
    import pybullet as p
except ImportError:  # allows unit-testing this module without pybullet installed
    p = None


def build_obstacle_aabbs(body_ids: list[int], padding: float = 0.0) -> np.ndarray:
    """
    Query PyBullet once for every static body's world-space AABB and pack
    the results into a single (N, 6) float32 array:
        [xmin, ymin, zmin, xmax, ymax, zmax]

    Parameters
    ----------
    body_ids : list of int
        PyBullet body unique IDs for every building / road / fallback box.
    padding : float
        Optional extra margin (meters) added around every box, useful for
        giving the drones a bit of extra breathing room beyond the literal
        mesh bounds.

    Returns
    -------
    np.ndarray of shape (N, 6), dtype float32. Empty array if body_ids is empty.
    """
    if not body_ids:
        return np.zeros((0, 6), dtype=np.float32)

    boxes = np.zeros((len(body_ids), 6), dtype=np.float32)
    for i, bid in enumerate(body_ids):
        aabb_min, aabb_max = p.getAABB(bid)
        boxes[i, 0:3] = np.array(aabb_min) - padding
        boxes[i, 3:6] = np.array(aabb_max) + padding
    return boxes


def closest_points_on_aabbs(positions: np.ndarray, boxes: np.ndarray) -> np.ndarray:
    """
    Vectorized closest-point-on-box computation.

    Parameters
    ----------
    positions : (D, 3) array of drone positions
    boxes     : (N, 6) array of obstacle AABBs

    Returns
    -------
    (D, N, 3) array: for every drone/obstacle pair, the closest point that
    lies on (or inside) the obstacle's box, relative to the drone.
    """
    if boxes.shape[0] == 0:
        return np.zeros((positions.shape[0], 0, 3), dtype=np.float32)

    # Broadcast: positions -> (D, 1, 3), boxes -> (1, N, 3)
    pts = positions[:, None, :]
    box_min = boxes[None, :, 0:3]
    box_max = boxes[None, :, 3:6]
    return np.clip(pts, box_min, box_max)


def obstacle_repulsion_force(
    positions: np.ndarray,
    boxes: np.ndarray,
    influence_radius: float = 4.0,
    strength: float = 25.0,
    min_dist: float = 0.15,
) -> np.ndarray:
    """
    Vectorized APF obstacle-repulsion force for every drone against every
    obstacle box, summed per-drone.

    F_rep = strength * (1/d - 1/influence_radius) * (1/d^2) * direction
    for d < influence_radius, else 0.  d is measured to the closest surface
    point of each AABB (so drones can fly close along a wall's flat face
    with zero force, and only feel pressure as they approach a corner/edge).

    Parameters
    ----------
    positions : (D, 3) drone positions
    boxes     : (N, 6) obstacle AABBs
    influence_radius : meters beyond which a building has zero effect
    strength   : force gain
    min_dist   : numerical floor to avoid singularities when clipped point == drone

    Returns
    -------
    (D, 3) net repulsion force per drone.
    """
    d = positions.shape[0]
    if boxes.shape[0] == 0:
        return np.zeros((d, 3), dtype=np.float32)

    closest = closest_points_on_aabbs(positions, boxes)         # (D, N, 3)
    delta = positions[:, None, :] - closest                     # (D, N, 3) drone - surface
    dist = np.linalg.norm(delta, axis=2)                        # (D, N)
    dist_safe = np.maximum(dist, min_dist)

    within = dist < influence_radius
    magnitude = np.zeros_like(dist)
    magnitude[within] = strength * (
        (1.0 / dist_safe[within]) - (1.0 / influence_radius)
    ) * (1.0 / (dist_safe[within] ** 2))

    direction = delta / dist_safe[..., None]
    # Where the drone center is exactly inside/on the box (dist == 0), push
    # straight up as a safe fallback instead of producing a NaN direction.
    degenerate = dist < 1e-6
    if np.any(degenerate):
        direction[degenerate] = np.array([0.0, 0.0, 1.0], dtype=np.float32)

    force = (magnitude[..., None] * direction).sum(axis=1)      # (D, 3)
    return force.astype(np.float32)
