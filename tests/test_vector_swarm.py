"""
test_vector_swarm.py — Unit tests for generalized VectorSwarm.step()

Verifies:
(a) (3,) broadcast target produces identical output to pre-change behavior.
(b) (D, 3) per-drone targets move different drones toward different targets.
(c) (D, 3) stuck-detection correctly compares each drone against its OWN target.
"""

import sys
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

from backend.perfect_swarm import VectorSwarm


class TestVectorSwarmDualMode(unittest.TestCase):
    def test_single_target_backward_compatibility(self):
        """(a) Confirm passing a (3,) target produces identical output to pre-change snapshot."""
        np.random.seed(42)
        starts = np.array([[0, 0, 10], [5, 5, 10]], dtype=np.float32)
        target = np.array([20, 20, 10], dtype=np.float32)
        obs = np.zeros((0, 6), dtype=np.float32)

        swarm = VectorSwarm(2, starts)
        for _ in range(10):
            swarm.step(target, obs, 0.05)

        # Expected pre-change snapshot values on seed 42, 10 ticks, dt=0.05
        expected_pos = np.array([[1.194053, 1.194053, 10.0], [6.1940527, 6.1940527, 10.0]], dtype=np.float32)
        expected_vel = np.array([[2.828427, 2.828427, 0.0], [2.828427, 2.828427, 0.0]], dtype=np.float32)

        np.testing.assert_allclose(swarm.positions, expected_pos, rtol=1e-5, atol=1e-5)
        np.testing.assert_allclose(swarm.velocities, expected_vel, rtol=1e-5, atol=1e-5)

    def test_per_drone_targets_diverge(self):
        """(b) Confirm (D, 3) per-drone targets move different drones toward different target points."""
        starts = np.array([[0, 0, 10], [0, 0, 10]], dtype=np.float32)
        targets = np.array([[100, 0, 10], [-100, 0, 10]], dtype=np.float32)
        obs = np.zeros((0, 6), dtype=np.float32)

        swarm = VectorSwarm(2, starts, separation_gain=0.0)  # disable separation force for clean divergence check
        swarm.step(targets, obs, 0.1)

        # Drone 0 should move positive X direction (+), Drone 1 should move negative X direction (-)
        self.assertGreater(swarm.velocities[0, 0], 1.0)
        self.assertLess(swarm.velocities[1, 0], -1.0)
        self.assertGreater(swarm.positions[0, 0], 0.0)
        self.assertLess(swarm.positions[1, 0], 0.0)

    def test_per_drone_stuck_detection(self):
        """(c) Confirm stuck detection with (D, 3) targets checks each drone against its OWN target."""
        # Drone 0 is at [0, 0, 10] with target [0.2, 0.2, 10] (near target, dist < 1.0)
        # Drone 1 is at [0, 0, 10] with target [100, 100, 10] (far from target, dist > 1.0)
        starts = np.array([[0, 0, 10], [0, 0, 10]], dtype=np.float32)
        targets = np.array([[0.2, 0.2, 10], [100, 100, 10]], dtype=np.float32)
        obs = np.zeros((0, 6), dtype=np.float32)

        swarm = VectorSwarm(2, starts, max_speed=0.0001)  # force velocity ~ 0 so moved < 0.002
        for _ in range(20):
            swarm.step(targets, obs, 0.1)

        # Drone 0 is near its own target -> _stuck_ticks should be 0
        self.assertEqual(swarm._stuck_ticks[0], 0)

        # Drone 1 is far from its own target and stationary -> _stuck_ticks should increment (> 15 after 20 ticks)
        self.assertGreater(swarm._stuck_ticks[1], 15)

    def test_dynamic_add_and_remove_drone(self):
        """Confirm add_drone and remove_drone dynamically resize swarm arrays and shift indices cleanly."""
        starts = np.zeros((0, 3), dtype=np.float32)
        swarm = VectorSwarm(0, starts)
        self.assertEqual(swarm.n, 0)

        # Add 3 drones
        idx0 = swarm.add_drone(np.array([10.0, 0.0, 5.0]))
        idx1 = swarm.add_drone(np.array([20.0, 0.0, 5.0]))
        idx2 = swarm.add_drone(np.array([30.0, 0.0, 5.0]))

        self.assertEqual(idx0, 0)
        self.assertEqual(idx1, 1)
        self.assertEqual(idx2, 2)
        self.assertEqual(swarm.n, 3)

        np.testing.assert_allclose(swarm.positions[0], [10.0, 0.0, 5.0])
        np.testing.assert_allclose(swarm.positions[1], [20.0, 0.0, 5.0])
        np.testing.assert_allclose(swarm.positions[2], [30.0, 0.0, 5.0])

        # Remove middle drone (index 1)
        swarm.remove_drone(1)

        self.assertEqual(swarm.n, 2)
        self.assertEqual(swarm.positions.shape, (2, 3))
        self.assertEqual(swarm.velocities.shape, (2, 3))
        self.assertEqual(len(swarm._stuck_ticks), 2)

        # Remaining two should be Drone 0 [10.0, 0.0, 5.0] at index 0, and Drone 2 [30.0, 0.0, 5.0] shifted to index 1
        np.testing.assert_allclose(swarm.positions[0], [10.0, 0.0, 5.0])
        np.testing.assert_allclose(swarm.positions[1], [30.0, 0.0, 5.0])


if __name__ == "__main__":
    unittest.main()
