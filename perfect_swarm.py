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
    # Force components
    # ------------------------------------------------------------------
    def _attractive_force(self, target_pos: np.ndarray) -> np.ndarray:
        """Linear-spring pull toward the target, capped so it never
        overwhelms repulsion at close range (avoids overshoot/oscillation)."""
        delta = target_pos[None, :] - self.positions          # (D, 3)
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
        target_pos : (3,) array -- world position of the red target drone
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
        near_target = np.linalg.norm(target_pos[None, :] - self.positions, axis=1) > 1.0
        self._stuck_ticks = np.where(
            (moved < 0.002) & near_target, self._stuck_ticks + 1, 0
        )

        return self.positions
