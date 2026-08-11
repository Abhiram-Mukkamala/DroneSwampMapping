"""
test_swarm_controller.py — Integration unit test for SwarmController

Verifies:
1. SwarmController initializes VectorSwarm and synchronizes FollowerDrone objects.
2. add_follower and remove_follower keep VectorSwarm and followers list index-aligned.
3. step() computes per-drone target vectors and updates PyBullet base positions and velocities.
"""

import sys
import math
import unittest
from pathlib import Path
import numpy as np

# Add repo root & backend to sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

try:
    import pybullet as p
except ImportError:
    p = None

from backend.master_sim import FollowerDrone, create_drone
from backend.swarm_controller import SwarmController


@unittest.skipIf(p is None, "PyBullet not installed")
class TestSwarmController(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.physics_client = p.connect(p.DIRECT)

    @classmethod
    def tearDownClass(cls):
        if p.isConnected(cls.physics_client):
            p.disconnect(cls.physics_client)

    def setUp(self):
        p.resetSimulation()

    def test_swarm_controller_add_step_remove_sync(self):
        """Test adding drones, stepping swarm controller, and removing drones in sync."""
        controller = SwarmController()
        red_pos = np.array([0.0, 0.0, 35.0], dtype=np.float64)

        # Add 3 follower drones
        for i in range(3):
            start_p = [red_pos[0] + i * 2.0, red_pos[1], 35.0]
            b_id = create_drone(start_p, color=[0.1, 0.4, 0.9, 1.0], radius=0.4, mass=0.8)
            f = FollowerDrone(b_id, start_p, offset_angle=0.0)
            controller.add_follower(f, start_p)

        self.assertEqual(len(controller.followers), 3)
        self.assertEqual(controller.swarm.n, 3)

        # Step controller
        controller.step(red_pos, sim_time=0.1, dt=0.05)

        # Verify PyBullet velocity is updated and non-zero
        vel, _ = p.getBaseVelocity(controller.followers[0].drone_id)
        speed = math.hypot(vel[0], vel[1], vel[2])
        self.assertGreater(speed, 0.0)

        # Verify last_dist_to_target is populated
        self.assertGreater(controller.followers[0].last_dist_to_target, 0.0)

        # Remove middle drone (index 1)
        removed_f = controller.remove_follower(1)
        p.removeBody(removed_f.drone_id)

        self.assertEqual(len(controller.followers), 2)
        self.assertEqual(controller.swarm.n, 2)

        # Step controller again
        controller.step(red_pos, sim_time=0.2, dt=0.05)
        self.assertEqual(controller.swarm.positions.shape, (2, 3))


if __name__ == "__main__":
    unittest.main()
