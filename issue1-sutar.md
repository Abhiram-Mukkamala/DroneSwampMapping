## Port A\*/decision-engine onto the current 3D SwarmController architecture

### Context

`origin/sutar-recovered-decision-engine` has a genuinely working `AStarPlanner` (`path_planning.py`) and `DecisionEngine` (`decision_engine.py`) — 8/8 tests pass, independently verified. It's built on a 2D grid/occupancy-map model though, and `phase0-foundation` now runs on `SwarmController`'s 3D AABB obstacle representation (`backend/obstacle_map.py`) and per-drone-target `VectorSwarm.step()`. This is a genuine adaptation, not a copy-paste merge.

### Scope

1. **Replace the 2D grid planner's input** with a 2D projection of `obstacle_map.build_obstacle_aabbs()`'s output at a fixed flight altitude (document the altitude assumption clearly).
2. **Adapt `DecisionEngine`'s output** (currently a steering vector for external integration) to feed into `VectorSwarm.step()`'s per-drone target array — you'll likely want the decision engine to emit a target *position* each tick rather than a raw steering vector, since that's what `step()` consumes. Your call on the exact interface, but state your reasoning.
3. **Replace `MockTelemetryNetwork`** with the real WebSocket telemetry infrastructure from `master_sim_server.py` (canonical `DroneState` schema from Phase 0.1 — nested `position`/`velocity`, not flat).
4. **Keep all 8 existing tests passing** in some form — port/adapt them alongside the code, don't drop coverage.

### Branch

`sutar-decision-engine-v2`, based on current `phase0-foundation` tip.

### Acceptance Criteria

- A\* actually plans a path around a real AABB obstacle in a live `master_sim_server.py` run — not just unit-test-level correctness.
- Include a short clip/description of a drone navigating around an obstacle it wouldn't have avoided with orbit-mode alone.

### Dependencies

- Nothing from Track A/B.
- **Do NOT** touch `backend/swarm_controller.py`'s `set_formation` method if Track A has landed by the time you start — check first, coordinate if there's overlap.

### Workflow

- Push to `sutar-decision-engine-v2`.
- Open a PR into `phase0-foundation` — do **not** merge it yourself.
