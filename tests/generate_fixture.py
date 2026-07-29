"""
Generates a deterministic reference snapshot from perfect_swarm.py's
VectorSwarm engine, for verifying the JS port produces matching behavior.

Coordinate convention here matches perfect_swarm.py as written: axes 0,1
are the horizontal plane (obstacle avoidance applies here), axis 2 is
"up". When porting to the Three.js sim (Y-up), map:
    python x -> three.js x
    python y -> three.js z
    python z -> three.js y (altitude)
"""
import os
import sys
import numpy as np
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from perfect_swarm import VectorSwarm, Obstacle

np.random.seed(42)  # deterministic - required since update() uses randomness when stuck

# 10 drones, two rows of 5, flying from x=10 to x=100, single obstacle in the middle
starts = [
    [10, 5, 20], [15, 5, 20], [20, 5, 20], [25, 5, 20], [30, 5, 20],
    [10, 10, 20], [15, 10, 20], [20, 10, 20], [25, 10, 20], [30, 10, 20],
]
targets = [
    [90, 5, 20], [95, 5, 20], [100, 5, 20], [105, 5, 20], [110, 5, 20],
    [90, 10, 20], [95, 10, 20], [100, 10, 20], [105, 10, 20], [110, 10, 20],
]
obstacles = [
    Obstacle(pos=[60, 7, 0], radius=8.0, height=30.0),
]

swarm = VectorSwarm(starts, targets)

TOTAL_STEPS = 300
CHECKPOINT_TICKS = [0, 50, 100, 150, 200, 250, 300]

snapshots = {}
for step in range(TOTAL_STEPS + 1):
    if step in CHECKPOINT_TICKS:
        snapshots[step] = {
            "positions": swarm.pos.round(6).tolist(),
            "velocities": swarm.vel.round(6).tolist(),
        }
    if step < TOTAL_STEPS:
        swarm.update(obstacles, step_size=0.18)

# Summary metrics useful for a coarse pass/fail check without comparing
# every single float
final_dist_to_target = np.linalg.norm(swarm.targets - swarm.pos, axis=1)

output = {
    "meta": {
        "seed": 42,
        "n_drones": len(starts),
        "step_size": 0.18,
        "total_steps": TOTAL_STEPS,
        "coordinate_note": "axes 0,1 = horizontal (obstacle avoidance plane), axis 2 = up",
    },
    "scenario": {
        "starts": starts,
        "targets": targets,
        "obstacles": [
            {"pos": o.pos.tolist(), "radius": o.radius, "height": o.height}
            for o in obstacles
        ],
    },
    "checkpoints": snapshots,
    "summary": {
        "final_positions": swarm.pos.round(6).tolist(),
        "final_distance_to_target": final_dist_to_target.round(6).tolist(),
        "max_final_distance_to_target": float(final_dist_to_target.max()),
        "mean_final_distance_to_target": float(final_dist_to_target.mean()),
    },
}

with open("fixture_snapshot.json", "w") as f:
    json.dump(output, f, indent=2)

print(f"Wrote fixture_snapshot.json")
print(f"Mean final distance to target: {output['summary']['mean_final_distance_to_target']:.3f}")
print(f"Max final distance to target: {output['summary']['max_final_distance_to_target']:.3f}")
