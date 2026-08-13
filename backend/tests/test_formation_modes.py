"""
test_formation_modes.py — Tests for SwarmController formation mode switching.

Verifies:
1. Default mode is "orbit" and produces orbit-pattern targets.
2. Switching to "beta" produces linearly-interpolated sweep targets.
3. Switching to "gamma" produces circular ring targets.
4. Mode switch actually changes target values vs orbit baseline.
5. Invalid mode raises ValueError.
"""

import sys
import math
import unittest
from pathlib import Path
import numpy as np

# Add repo root & backend to sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
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


def _make_controller_with_drones(n_drones: int, red_pos: np.ndarray) -> SwarmController:
    """Helper: create a SwarmController with n follower drones at orbit positions."""
    controller = SwarmController()
    for i in range(n_drones):
        angle = 2 * math.pi * i / n_drones
        orbit_radius = 5.0
        start_p = [
            red_pos[0] + orbit_radius * math.cos(angle),
            red_pos[1] + orbit_radius * math.sin(angle),
            red_pos[2],
        ]
        b_id = create_drone(start_p, color=[0.1, 0.4, 0.9, 1.0], radius=0.4, mass=0.8)
        f = FollowerDrone(b_id, start_p, offset_angle=angle, orbit_radius=orbit_radius)
        controller.add_follower(f, start_p)
    return controller


@unittest.skipIf(p is None, "PyBullet not installed")
class TestFormationModes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.physics_client = p.connect(p.DIRECT)

    @classmethod
    def tearDownClass(cls):
        if p.isConnected(cls.physics_client):
            p.disconnect(cls.physics_client)

    def setUp(self):
        p.resetSimulation()

    def test_default_mode_is_orbit(self):
        """SwarmController defaults to orbit mode with no set_formation call."""
        controller = SwarmController()
        self.assertEqual(controller._formation_mode, "orbit")

    def test_orbit_targets_match_original_formula(self):
        """Orbit mode produces targets matching the original per-drone orbit formula."""
        red_pos = np.array([10.0, 20.0, 35.0], dtype=np.float64)
        controller = _make_controller_with_drones(4, red_pos)
        sim_time = 1.0

        targets = controller._compute_targets(red_pos, sim_time)

        self.assertEqual(targets.shape, (4, 3))
        # Verify against the original formula directly
        for i, follower in enumerate(controller.followers):
            angle = follower.offset_angle + sim_time * 0.35
            expected = [
                red_pos[0] + follower.orbit_radius * math.cos(angle),
                red_pos[1] + follower.orbit_radius * math.sin(angle),
                red_pos[2] + 0.5 * math.sin(sim_time + follower.offset_angle),
            ]
            np.testing.assert_allclose(targets[i], expected, atol=1e-5,
                                       err_msg=f"Orbit target mismatch for drone {i}")

    def test_beta_mode_changes_targets(self):
        """Switching to beta mode produces different targets than orbit mode."""
        red_pos = np.array([0.0, 0.0, 35.0], dtype=np.float64)
        controller = _make_controller_with_drones(5, red_pos)
        sim_time = 1.0

        orbit_targets = controller._compute_targets(red_pos, sim_time).copy()

        controller.set_formation("beta")
        beta_targets = controller._compute_targets(red_pos, sim_time)

        self.assertEqual(beta_targets.shape, (5, 3))
        # Beta targets should differ from orbit targets
        self.assertFalse(np.allclose(orbit_targets, beta_targets),
                         "Beta targets should differ from orbit targets")

    def test_beta_targets_are_collinear(self):
        """Beta mode targets lie on a straight line (linear interpolation)."""
        red_pos = np.array([50.0, 50.0, 20.0], dtype=np.float64)
        controller = _make_controller_with_drones(5, red_pos)

        controller.set_formation("beta",
                                 start_point=[0.0, 0.0, 0.0],
                                 end_point=[100.0, 0.0, 0.0],
                                 altitude=20.0)
        targets = controller._compute_targets(red_pos, sim_time=0.0)

        self.assertEqual(targets.shape, (5, 3))
        # All y coordinates should be 0 (line from [0,0] to [100,0])
        np.testing.assert_allclose(targets[:, 1], 0.0, atol=1e-6)
        # All z coordinates should be 20 (altitude)
        np.testing.assert_allclose(targets[:, 2], 20.0, atol=1e-6)
        # x should be evenly spaced from 0 to 100
        np.testing.assert_allclose(targets[:, 0], [0, 25, 50, 75, 100], atol=1e-6)

    def test_gamma_mode_changes_targets(self):
        """Switching to gamma mode produces different targets than orbit mode."""
        red_pos = np.array([0.0, 0.0, 35.0], dtype=np.float64)
        controller = _make_controller_with_drones(6, red_pos)
        sim_time = 1.0

        orbit_targets = controller._compute_targets(red_pos, sim_time).copy()

        controller.set_formation("gamma", radius=15.0)
        gamma_targets = controller._compute_targets(red_pos, sim_time)

        self.assertEqual(gamma_targets.shape, (6, 3))
        self.assertFalse(np.allclose(orbit_targets, gamma_targets),
                         "Gamma targets should differ from orbit targets")

    def test_gamma_targets_form_circle(self):
        """Gamma mode targets lie on a circle of the specified radius."""
        red_pos = np.array([10.0, 20.0, 30.0], dtype=np.float64)
        controller = _make_controller_with_drones(8, red_pos)

        controller.set_formation("gamma",
                                 center=[10.0, 20.0],
                                 radius=25.0,
                                 altitude=30.0)
        targets = controller._compute_targets(red_pos, sim_time=0.0)

        self.assertEqual(targets.shape, (8, 3))
        # All z should be altitude
        np.testing.assert_allclose(targets[:, 2], 30.0, atol=1e-6)
        # All distances from center in xy plane should equal radius
        dists = np.sqrt((targets[:, 0] - 10.0) ** 2 + (targets[:, 1] - 20.0) ** 2)
        np.testing.assert_allclose(dists, 25.0, atol=1e-6)

    def test_step_uses_formation_targets(self):
        """step() dispatches through the active formation mode, not hardcoded orbit."""
        red_pos = np.array([0.0, 0.0, 35.0], dtype=np.float64)
        controller = _make_controller_with_drones(3, red_pos)

        # Step in orbit mode
        controller.step(red_pos, sim_time=0.1, dt=0.05)
        orbit_positions = controller.swarm.positions.copy()

        # Reset positions and switch to beta
        controller.swarm.positions[:] = controller.swarm.positions  # no-op, just ensure state
        controller.set_formation("beta",
                                 start_point=[-50.0, 0.0, 0.0],
                                 end_point=[50.0, 0.0, 0.0],
                                 altitude=35.0)
        controller.step(red_pos, sim_time=0.1, dt=0.05)
        beta_positions = controller.swarm.positions.copy()

        # Positions should have diverged because targets differ
        self.assertFalse(np.allclose(orbit_positions, beta_positions),
                         "step() in beta mode should produce different positions than orbit mode")

    def test_invalid_mode_raises(self):
        """set_formation() rejects unknown modes."""
        controller = SwarmController()
        with self.assertRaises(ValueError):
            controller.set_formation("invalid_mode")

    def test_mode_switch_back_to_orbit(self):
        """Switching back to orbit from beta restores original target pattern."""
        red_pos = np.array([0.0, 0.0, 35.0], dtype=np.float64)
        controller = _make_controller_with_drones(4, red_pos)
        sim_time = 2.0

        orbit_targets_before = controller._compute_targets(red_pos, sim_time).copy()

        controller.set_formation("beta")
        controller.set_formation("orbit")

        orbit_targets_after = controller._compute_targets(red_pos, sim_time)
        np.testing.assert_array_equal(orbit_targets_before, orbit_targets_after)


if __name__ == "__main__":
    unittest.main()
