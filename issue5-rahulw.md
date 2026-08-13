## Implement real-time 2D GIS coverage grid & trajectory trail tracking in `frontend/`

### Context

`CoverageMap.jsx` (in `frontend/src/components/CoverageMap/`) currently renders live drone blips over a static CSS grid. However, it lacks spatial coverage visualization (heatmaps / visited grid cells scanned by the swarm) and drone trajectory trails (breadcrumbs). This means operators cannot visually see which parts of the map have been explored or trace drone flight paths.

### Scope

1. **Breadcrumb Trajectory Trails:** Track the last N positions (e.g., 20–50 points) for each active drone in `CoverageMap.jsx` and render flight path trails connecting past points to current positions.
2. **2D Coverage Grid / Heatmap:** Divide the map area into a grid (e.g. 20x20 or 30x30 cells) and mark cells as "scanned" when a drone passes within sensor range ($R \approx 3.0\text{m}$). Render visited cells with a subtle overlay color.
3. **Coverage Metrics:** Compute and display the overall scanned coverage percentage (e.g., `% of total grid area explored`) dynamically in the `CoverageMap` header/footer.
4. **Clean up & Performance:** Ensure past trajectory history and grid cell updates do not cause unnecessary React re-renders or performance drops at high telemetry broadcast rates.

### Branch

`rahulw-gis-coverage-view`, based on current `phase0-foundation` tip.

### Acceptance Criteria

- Launch the live sim, open the frontend, and verify that drone movement leaves visible flight path trails on the `CoverageMap`.
- Grid cells turn "scanned" as drones fly over them, updating the exploration coverage % metric in real time.

### Dependencies

- Purely frontend UI/state addition to `frontend/src/components/CoverageMap/`.
- No backend changes required; consumes live `DroneState` array already provided by `DroneContext.jsx`.

### Workflow

- Push to `rahulw-gis-coverage-view`.
- Open a PR into `phase0-foundation` — do **not** merge it yourself.
