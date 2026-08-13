## Build the live 3D swarm formation view in `frontend/`

### Context

`frontend/` (the React/Vite app) currently shows telemetry stats and the camera POV feed, but has no 3D spatial view — you can't currently see the swarm's formation shape, only numbers. `web/` (the separate Three.js browser preview) already has working 3D rendering logic (`SceneManager`, `DroneRenderer`) that can serve as a reference for camera/scene setup patterns, though it's a different rendering stack (vanilla Three.js vs. what you'd use in React).

### Scope

1. **Add `@react-three/fiber` + `@react-three/drei`** to `frontend/`'s dependencies.
2. **Build a `SwarmView3D` component** consuming live `DroneState` data (already flowing correctly through `SimulationContext.jsx` → `DroneContext.jsx` as of Phase 0.1) — render each drone as a simple mesh at `drone.position`, oriented by `drone.heading`, colored by `drone.status` (reuse the same status-color mapping already in `BottomStats.jsx`/`DroneCard.jsx` for consistency).
3. **Basic orbit camera controls** (`OrbitControls` from drei) — don't need custom controls, the library default is fine.
4. This is **purely additive** to `frontend/` — no backend changes, should not conflict with Track A/B or Issues 1–3 at all.

### Branch

`ayaan-3d-formation-view`, based on current `phase0-foundation` tip.

### Acceptance Criteria

- Run the live sim, open the frontend, watch drones move in the 3D view in real time matching what `BottomStats` reports numerically.
- **Not** a static/mock render.

### Workflow

- Push to `ayaan-3d-formation-view`.
- Open a PR into `phase0-foundation` — do **not** merge it yourself.
