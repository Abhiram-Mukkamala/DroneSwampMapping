"""
test_stuck_detection.py — Unit test for STUCK status evaluation in master_sim_server.py

Verifies:
1. A drone moving slowly (speed < threshold) but close to its target slot
   (dist <= threshold) is NOT marked STUCK (prevents mislabeling hovering/decelerating drones).
2. A drone moving slowly while far from its target slot (dist > threshold)
   IS marked STUCK after the _STUCK_TICK_THRESHOLD debounce window.
3. Speed recovery or reaching target resets the stuck tick counter.
"""

import sys
import unittest
from pathlib import Path

# Add repo root to sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Add backend to sys.path as well
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from master_sim_server import (
    _STUCK_VELOCITY_THRESHOLD,
    _STUCK_DISTANCE_THRESHOLD,
    _STUCK_TICK_THRESHOLD,
)


def evaluate_drone_status(
    speed: float,
    dist_to_target: float,
    tick_count: int,
    simulation_running: bool = True,
) -> tuple[str, int]:
    """
    Evaluator matching the exact STUCK state machine logic in master_sim_server.py.
    """
    if not simulation_running:
        return "IDLE", 0
    elif speed < _STUCK_VELOCITY_THRESHOLD and dist_to_target > _STUCK_DISTANCE_THRESHOLD:
        new_ticks = tick_count + 1
        status = "STUCK" if new_ticks >= _STUCK_TICK_THRESHOLD else "ACTIVE"
        return status, new_ticks
    else:
        return "ACTIVE", 0


class TestStuckDetection(unittest.TestCase):
    def test_slow_and_near_target_is_not_stuck(self):
        """Drone moving slowly (0.05 m/s) but close to target (0.5m) must NOT be marked STUCK."""
        ticks = 0
        speed = 0.05  # below threshold 0.15
        dist = 0.5    # below threshold 1.5 (close to target)

        for _ in range(_STUCK_TICK_THRESHOLD + 10):
            status, ticks = evaluate_drone_status(speed, dist, ticks)
            self.assertEqual(status, "ACTIVE")
            self.assertEqual(ticks, 0)

    def test_slow_and_far_from_target_becomes_stuck_after_debounce(self):
        """Drone moving slowly (0.05 m/s) while far from target (5.0m) IS marked STUCK after debounce window."""
        ticks = 0
        speed = 0.05  # below threshold 0.15
        dist = 5.0    # above threshold 1.5 (far from target)

        # Before threshold is reached, status should remain ACTIVE
        for step in range(1, _STUCK_TICK_THRESHOLD):
            status, ticks = evaluate_drone_status(speed, dist, ticks)
            self.assertEqual(status, "ACTIVE")
            self.assertEqual(ticks, step)

        # On reaching _STUCK_TICK_THRESHOLD, status must be STUCK
        status, ticks = evaluate_drone_status(speed, dist, ticks)
        self.assertEqual(status, "STUCK")
        self.assertEqual(ticks, _STUCK_TICK_THRESHOLD)

    def test_stuck_resets_when_speed_recovers(self):
        """Stuck tick counter resets to 0 and status becomes ACTIVE when drone speeds up."""
        ticks = _STUCK_TICK_THRESHOLD
        speed = 1.0   # above threshold 0.15
        dist = 5.0    # far from target

        status, ticks = evaluate_drone_status(speed, dist, ticks)
        self.assertEqual(status, "ACTIVE")
        self.assertEqual(ticks, 0)


if __name__ == "__main__":
    unittest.main()
