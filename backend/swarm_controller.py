"""
swarm_controller.py
-------------------
Bridge between VectorSwarm APF physics engine and PyBullet simulation environment.

Manages a list of FollowerDrone objects in sync with an authoritative VectorSwarm
instance. Computes per-drone target vectors for circular orbit formation, executes
VectorSwarm.step(), updates PyBullet rigid body transforms via resetBasePositionAndOrientation
and resetBaseVelocity, and syncs telemetry properties (such as last_dist_to_target).
"""

from __future__ import annotations
import math
import numpy as np

try:
    import pybullet as p
except ImportError:
    pass

from master_sim import FollowerDrone
from perfect_swarm import VectorSwarm


class SwarmController:
    """
    Coordinates VectorSwarm physics state with PyBullet bodies for a fleet of FollowerDrones.
    """
    def __init__(self, obstacle_boxes: np.ndarray | None = None):
        self.followers: list[FollowerDrone] = []
        self.swarm = VectorSwarm(num_drones=0, start_positions=np.zeros((0, 3), dtype=np.float32))
        self.obstacle_boxes = obstacle_boxes if obstacle_boxes is not None else np.zeros((0, 6), dtype=np.float32)

    def set_obstacle_boxes(self, obstacle_boxes: np.ndarray):
        """Set or update the obstacle AABB bounding boxes array."""
        self.obstacle_boxes = obstacle_boxes

    def add_follower(self, follower: FollowerDrone, start_pos: list[float] | np.ndarray) -> int:
        """
        Add a FollowerDrone and register its start position in VectorSwarm.
        """
        pos = np.asarray(start_pos, dtype=np.float32)
        idx = self.swarm.add_drone(pos)
        self.followers.append(follower)
        assert idx == len(self.followers) - 1
        return idx

    def remove_follower(self, index: int) -> FollowerDrone:
        """
        Remove a FollowerDrone at index, removing its body from VectorSwarm.
        """
        if not (0 <= index < len(self.followers)):
            raise IndexError(f"Follower index {index} out of range for count {len(self.followers)}")

        self.swarm.remove_drone(index)
        removed = self.followers.pop(index)
        return removed

    def clear(self) -> list[FollowerDrone]:
        """
        Remove all followers and reset VectorSwarm to empty state.
        """
        removed_list = list(self.followers)
        self.followers.clear()
        self.swarm = VectorSwarm(num_drones=0, start_positions=np.zeros((0, 3), dtype=np.float32))
        return removed_list

    def step(self, red_pos: np.ndarray, sim_time: float, dt: float):
        """
        Advance swarm physics by one tick.

        1. Computes per-drone target positions in circular orbit formation around red_pos.
        2. Steps VectorSwarm with (D, 3) per-drone targets and obstacle_boxes.
        3. Writes updated positions & velocities into PyBullet bodies via
           resetBasePositionAndOrientation and resetBaseVelocity.
        4. Updates last_dist_to_target on each FollowerDrone object for telemetry.
        """
        n = len(self.followers)
        if n == 0:
            return

        # 1. Build (D, 3) per-drone target orbit array
        targets = np.zeros((n, 3), dtype=np.float32)
        for i, follower in enumerate(self.followers):
            angle = follower.offset_angle + sim_time * 0.35
            targets[i] = [
                red_pos[0] + follower.orbit_radius * math.cos(angle),
                red_pos[1] + follower.orbit_radius * math.sin(angle),
                red_pos[2] + 0.5 * math.sin(sim_time + follower.offset_angle),
            ]

        # 2. Step VectorSwarm engine
        new_positions = self.swarm.step(targets, self.obstacle_boxes, dt)
        new_velocities = self.swarm.velocities

        # 3. Update PyBullet bodies & FollowerDrone properties
        for i, follower in enumerate(self.followers):
            pos = new_positions[i].tolist()
            vel = new_velocities[i].tolist()
            heading = follower.get_heading_angle()

            # Kinematic position override + velocity reset (crucial for stuck detection telemetry)
            p.resetBasePositionAndOrientation(
                follower.drone_id,
                pos,
                p.getQuaternionFromEuler([0, 0, heading])
            )
            p.resetBaseVelocity(
                follower.drone_id,
                linearVelocity=vel,
                angularVelocity=[0.0, 0.0, 0.0]
            )

            # 4. Update last_dist_to_target for 0.1b stuck check
            target_diff = targets[i] - new_positions[i]
            follower.last_dist_to_target = float(np.linalg.norm(target_diff))
