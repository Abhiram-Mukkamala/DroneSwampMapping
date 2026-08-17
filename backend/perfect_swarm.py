"""
perfect_swarm.py
-----------------
Vectorized Artificial Potential Field (APF) swarm engine.

Every follower drone feels exactly three superposed forces each tick:
    1. Attractive force  -> pulls it toward the red target drone
    2. Obstacle repulsion -> pushes it away from building/road AABBs
    3. Inter-drone separation -> pushes it away from swarm-mates closer
       than SEPARATION_DIST, so followers don't collide with each other
       while converging on the same target.

All math is NumPy-vectorized across the whole follower fleet at once --
there is no per-drone Python loop in the hot path, which is what lets this
scale to large swarms while keeping PyBullet's real-time step budget.

This module is intentionally pybullet-agnostic in its math: it operates on
plain NumPy position/velocity arrays. `master_sim.py` is the only place
that talks to the PyBullet C API (reading obstacle AABBs, writing drone
transforms). That separation is also why this file can be unit-tested
without a running PyBullet GUI.
"""

from __future__ import annotations
import numpy as np

from obstacle_map import obstacle_repulsion_force


# ------------------------------------------------------------------
# Formation protocol target generators
# ------------------------------------------------------------------

def generate_protocol_beta(
    n_drones: int,
    start_point: list,
    end_point: list,
    altitude: float = 20.0,
) -> np.ndarray:
    """
    Protocol Beta (Search & Rescue / Linear Sweep).

    Linear axis interpolation forming an evenly spaced horizontal sweep line
    between two endpoints, all at a fixed altitude.

    Parameters
    ----------
    n_drones : int
        Number of drones to distribute along the line.
    start_point : list
        Starting endpoint [x, y, ...] (only first two elements used).
    end_point : list
        Ending endpoint [x, y, ...] (only first two elements used).
    altitude : float
        Uniform flight altitude for the sweep line (axis 2).

    Returns
    -------
    np.ndarray of shape (n_drones, 3)
        Per-drone target positions suitable for VectorSwarm.step().
    """
    start_pt = np.array(start_point[:2], dtype=float)
    end_pt = np.array(end_point[:2], dtype=float)
    if n_drones == 1:
        points = np.array([start_pt])
    else:
        t = np.linspace(0, 1, n_drones)[:, None]
        points = start_pt + t * (end_pt - start_pt)
    altitudes = np.full((n_drones, 1), altitude)
    return np.hstack([points, altitudes])


def generate_protocol_gamma(
    n_drones: int,
    center: list,
    radius: float = 15.0,
    altitude: float = 20.0,
) -> np.ndarray:
    """
    Protocol Gamma (Dynamic Encirclement).

    Trigonometric distribution forming a 360° dynamic containment ring
    around target coordinates at a fixed altitude.

    Parameters
    ----------
    n_drones : int
        Number of drones to distribute around the ring.
    center : list
        Center of the encirclement ring [x, y].
    radius : float
        Radius of the containment ring.
    altitude : float
        Uniform flight altitude for the ring (axis 2).

    Returns
    -------
    np.ndarray of shape (n_drones, 3)
        Per-drone target positions suitable for VectorSwarm.step().
    """
    indices = np.arange(n_drones)
    angles = 2 * np.pi * indices / n_drones
    x = center[0] + radius * np.cos(angles)
    y = center[1] + radius * np.sin(angles)
    z = np.full(n_drones, altitude)
    return np.column_stack([x, y, z])


class VectorSwarm:
    """
    Holds the live physics state (position + velocity) for N follower
    drones and steps them forward under combined APF forces.
    """

    def __init__(
        self,
        num_drones: int,
        start_positions: np.ndarray,
        separation_dist: float = 2.0,
        max_speed: float = 4.0,
        attractive_gain: float = 3.0,
        separation_gain: float = 18.0,
        obstacle_influence_radius: float = 4.0,
        obstacle_gain: float = 25.0,
        damping: float = 0.90,
        noise_scale: float = 0.05,
    ):
        assert start_positions.shape == (num_drones, 3)

        self.n = num_drones
        self.positions = start_positions.astype(np.float32).copy()
        self.velocities = np.zeros((num_drones, 3), dtype=np.float32)

        self.separation_dist = separation_dist
        self.max_speed = max_speed
        self.attractive_gain = attractive_gain
        self.separation_gain = separation_gain
        self.obstacle_influence_radius = obstacle_influence_radius
        self.obstacle_gain = obstacle_gain
        self.damping = damping
        self.noise_scale = noise_scale

        # local-minima escape: tracks how many consecutive ticks each drone
        # has been almost stationary despite a nonzero attractive pull, so
        # we can inject stochastic noise to break out of APF dead zones
        # (e.g. trapped in a concave building corner).
        self._stuck_ticks = np.zeros(num_drones, dtype=np.int32)

    # ------------------------------------------------------------------
    # Dynamic Fleet Management
    # ------------------------------------------------------------------
    def add_drone(self, position: np.ndarray) -> int:
        """
        Dynamically append a new follower drone to the swarm.

        Parameters
        ----------
        position : (3,) array -- initial 3D position of the new drone

        Returns
        -------
        int : The index assigned to the newly added drone (self.n - 1).
        """
        pos_vec = np.asarray(position, dtype=np.float32).reshape(1, 3)
        self.positions = np.vstack([self.positions, pos_vec])
        self.velocities = np.vstack([self.velocities, np.zeros((1, 3), dtype=np.float32)])
        self._stuck_ticks = np.append(self._stuck_ticks, 0)
        self.n += 1
        return self.n - 1

    def remove_drone(self, index: int) -> None:
        """
        Dynamically remove a follower drone at the specified index.

        Parameters
        ----------
        index : int -- the index of the drone to remove (0 <= index < self.n)

        Notes
        -----
        Removing a drone shifts every subsequent drone's index down by one.
        Callers maintaining their own ID-to-index mapping must re-index
        remaining drones accordingly.
        """
        if not (0 <= index < self.n):
            raise IndexError(f"Drone index {index} out of bounds for swarm of size {self.n}")

        self.positions = np.delete(self.positions, index, axis=0)
        self.velocities = np.delete(self.velocities, index, axis=0)
        self._stuck_ticks = np.delete(self._stuck_ticks, index, axis=0)
        self.n -= 1

    # ------------------------------------------------------------------
    # Force components
    # ------------------------------------------------------------------
    def _attractive_force(self, target_pos: np.ndarray) -> np.ndarray:
        """Linear-spring pull toward the target, capped so it never
        overwhelms repulsion at close range (avoids overshoot/oscillation).

        Accepts either a single (3,) broadcast target or a (D, 3) per-drone target array.
        """
        if target_pos.ndim == 1:
            delta = target_pos[None, :] - self.positions          # (D, 3)
        else:
            delta = target_pos - self.positions                   # (D, 3)

        dist = np.linalg.norm(delta, axis=1, keepdims=True)
        dist_safe = np.maximum(dist, 1e-3)
        direction = delta / dist_safe
        # Clamp the effective pulling distance so attraction saturates
        # instead of growing unbounded far from the target.
        capped_dist = np.minimum(dist, 8.0)
        return (self.attractive_gain * capped_dist * direction).astype(np.float32)

    def _separation_force(self) -> np.ndarray:
        """Pairwise repulsion between follower drones, vectorized via
        broadcasting (D, D, 3) pairwise delta tensor)."""
        if self.n <= 1:
            return np.zeros((self.n, 3), dtype=np.float32)

        delta = self.positions[:, None, :] - self.positions[None, :, :]   # (D, D, 3)
        dist = np.linalg.norm(delta, axis=2)                              # (D, D)
        np.fill_diagonal(dist, np.inf)                                    # ignore self

        within = dist < self.separation_dist
        dist_safe = np.maximum(dist, 0.05)

        magnitude = np.zeros_like(dist)
        magnitude[within] = self.separation_gain * (
            1.0 / dist_safe[within] - 1.0 / self.separation_dist
        ) * (1.0 / (dist_safe[within] ** 2))

        direction = delta / dist_safe[..., None]
        force = (magnitude[..., None] * direction).sum(axis=1)           # (D, 3)
        return force.astype(np.float32)

    def _escape_noise(self) -> np.ndarray:
        """Stochastic noise vector applied only to drones flagged as stuck,
        so APF local minima (e.g. wedged in a concave building corner)
        get nudged out without perturbing well-behaved drones."""
        noise = np.zeros((self.n, 3), dtype=np.float32)
        stuck_mask = self._stuck_ticks > 15
        if np.any(stuck_mask):
            k = int(stuck_mask.sum())
            rand_dir = np.random.normal(size=(k, 3)).astype(np.float32)
            norms = np.linalg.norm(rand_dir, axis=1, keepdims=True)
            norms[norms < 1e-6] = 1.0
            noise[stuck_mask] = (rand_dir / norms) * self.noise_scale * 40.0
        return noise

    # ------------------------------------------------------------------
    # Main tick
    # ------------------------------------------------------------------
    def step(
        self,
        target_pos: np.ndarray,
        obstacle_boxes: np.ndarray,
        dt: float,
    ) -> np.ndarray:
        """
        Advance the swarm by one physics tick.

        Parameters
        ----------
        target_pos : (3,) or (D, 3) array
            Target position(s). If a single (3,) array is passed, it is
            broadcast as a shared target for all D drones (leader-follow).
            If a (D, 3) array is passed, target_pos[i] specifies the
            individual target for drone i.
        obstacle_boxes : (N, 6) array from obstacle_map.build_obstacle_aabbs
        dt : timestep in seconds

        Returns
        -------
        (D, 3) updated world positions, ready to write straight into
        PyBullet via resetBasePositionAndOrientation.
        """
        f_attr = self._attractive_force(target_pos)
        f_obs = obstacle_repulsion_force(
            self.positions,
            obstacle_boxes,
            influence_radius=self.obstacle_influence_radius,
            strength=self.obstacle_gain,
        )
        f_sep = self._separation_force()
        f_noise = self._escape_noise()

        total_force = f_attr + f_obs + f_sep + f_noise

        # semi-implicit Euler integration
        self.velocities = (self.velocities + total_force * dt) * self.damping

        # speed clamp
        speeds = np.linalg.norm(self.velocities, axis=1, keepdims=True)
        too_fast = speeds.squeeze(-1) > self.max_speed
        if np.any(too_fast):
            scale = self.max_speed / np.maximum(speeds[too_fast], 1e-6)
            self.velocities[too_fast] *= scale

        self.positions = self.positions + self.velocities * dt

        # simple floor clamp -- never let a follower fly through the ground
        self.positions[:, 2] = np.maximum(self.positions[:, 2], 0.5)

        # update stuck-tick counters for the noise escape mechanism
        moved = np.linalg.norm(self.velocities, axis=1) * dt
        target_diff = (target_pos[None, :] - self.positions) if target_pos.ndim == 1 else (target_pos - self.positions)
        near_target = np.linalg.norm(target_diff, axis=1) > 1.0
        self._stuck_ticks = np.where(
            (moved < 0.002) & near_target, self._stuck_ticks + 1, 0
        )

        return self.positions
