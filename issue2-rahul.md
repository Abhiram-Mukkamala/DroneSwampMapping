## Wire the WebSocket mainframe hazard pipeline into the live PyBullet backend

### Context

`origin/rahul-simulation-engine`'s `data_pipeline.py` (the `PipelineNode`/`communication_router`) is a real, working, standalone WebSocket server producing the documented hazard-grid contract (`{grid, cellSize}`) from YOLO detections, and aggregating telemetry by `droneId`. It has never been connected to `master_sim_server.py` — two separate WebSocket servers currently exist with no bridge between them.

### Scope

1. **Decide (and document the decision)** whether `data_pipeline.py` becomes a second server `master_sim_server.py` forwards detections to, or whether its `PipelineNode` logic gets imported directly into `master_sim_server.py` as a module. Recommendation: the latter, to avoid yet another standalone server — but your call given you own this contract.
2. **Update `process_drone_telemetry`** to consume/emit the canonical `DroneState` schema (`backend/schemas/drone_state.py`) instead of the current ad-hoc `telemetry_stream` dict keyed loosely by `droneId`.
3. **Feed the resulting hazard grid into `backend/obstacle_map.py`** as a supplementary dynamic-obstacle source alongside the static AABBs — this is what lets the swarm react to obstacles YOLO detects live, not just the ones baked into the city at startup. Coordinate with whoever's working Issue 1 (Sutar) since the decision engine will want to consume this too eventually — not blocking, just be aware.
4. **Clean up `map_cache/`** — it currently has one hardcoded cached map PNG for a specific lat/lng, worth a comment explaining what it's for and whether it's meant to be regenerated per-scenario or is a fixed dev fixture.

### Branch

`rahul-hazard-integration`, based on current `phase0-foundation` tip.

### Acceptance Criteria

- Send a mock YOLO detection payload through the live pipeline and show the resulting hazard grid actually reaching `obstacle_map`'s repulsion force calculation.
- **Trace the full path** — not just that each piece works in isolation.

### Dependencies

- Nothing from Track A/B.
- Coordinate with Issue 1 (Sutar) — the decision engine will eventually consume the hazard grid. Not blocking, but be aware.

### Workflow

- Push to `rahul-hazard-integration`.
- Open a PR into `phase0-foundation` — do **not** merge it yourself.
