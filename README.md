<div align="center">

# DroneSwampMapping

**A unified drone-swarm simulation platform: real PyBullet physics, a zero-install browser preview, and one shared swarm-intelligence engine driving both.**

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![Node](https://img.shields.io/badge/node-22%2B-green)](https://nodejs.org/)
[![React](https://img.shields.io/badge/react-19-61dafb)](https://react.dev/)
[![PyBullet](https://img.shields.io/badge/physics-PyBullet-orange)](https://pybullet.org/)
[![License](https://img.shields.io/badge/license-unspecified-lightgrey)]()

[Overview](#overview) • [Architecture](#architecture) • [Quickstart](#quickstart) • [Repository Layout](#repository-layout) • [Formation Protocols](#formation-protocols) • [Roadmap](#roadmap) • [Contributing](#contributing)

</div>

---

## Overview

DroneSwampMapping is a swarm-robotics simulation project built around one
core idea: **one physics/swarm-intelligence engine, two ways to view it.**

- **PyBullet showcase** (`backend/`) — real rigid-body physics, a
  procedurally generated 3D city, FPS-style piloting of a lead drone, and
  an onboard RGB/depth/segmentation vision pipeline. This is the
  high-fidelity reference simulation.
- **Browser preview** (`web/`) — a lightweight, dependency-free Three.js
  simulation that runs the *same* Artificial Potential Fields (APF) swarm
  algorithm, verified byte-for-byte against the Python reference via
  fixture tests. No install required — open `web/index.html` and it runs.
- **React control app** (`frontend/`) — a live dashboard consuming real
  WebSocket telemetry from the PyBullet backend: per-drone stats, a
  coverage map, and a live camera POV feed with perception overlays.

Both simulation surfaces are driven by the same swarm-physics core
(`VectorSwarm` — an Artificial Potential Fields engine with attraction,
inter-drone separation, obstacle repulsion, and stuck/escape-noise
recovery), implemented in parallel in Python and JavaScript and kept in
sync with cross-language fixture tests, not just "looks similar."

> **Project status:** the PyBullet backend, browser preview, and React
> frontend are wired together on real, live data — not mocked. Formation
> protocols (linear sweep, dynamic encirclement) work in both simulation
> surfaces. See [Roadmap](#roadmap) for what's still in progress.

---

## Architecture

```
┌─────────────────────────────┐        WebSocket (ws://localhost:8765)
│   backend/  — PyBullet sim  │◄───────────────────────────────┐
│                              │        MJPEG (http://localhost:5000)
│  master_sim_server.py       │◄───────────────────────────┐   │
│    ├─ SwarmController ──────┼── owns ──► VectorSwarm      │   │
│    │    (perfect_swarm.py)  │            (APF physics)    │   │
│    ├─ obstacle_map.py       │  (3D AABB obstacle volumes)  │   │
│    ├─ city_layout.py        │  (procedural city generation)│   │
│    └─ vision_engine.py      │  (RGB/depth/seg camera)       │   │
└─────────────────────────────┘                               │   │
                                                                │   │
┌─────────────────────────────┐                                │   │
│   frontend/  — React app    ├────────────────────────────────┘   │
│    SimulationContext.jsx (WS)                                    │
│    DroneContext.jsx (canonical DroneState)                       │
│    Live POV + detections ─────────────────────────────────────────┘
└─────────────────────────────┘

┌─────────────────────────────┐
│   web/  — Browser preview   │   Independent, self-contained
│                              │   Three.js simulation, no backend
│  main.js ── SimulationLoop  │   dependency. Runs entirely
│    └─ swarm/VectorSwarm.js  │   client-side.
│         (JS port of the APF │
│          engine, fixture-   │
│          verified vs Python)│
│    └─ render/TerrainRenderer│   Procedural heightmap terrain
│    └─ perception/           │   Optional: talks to the Dockerized
│         (YOLOv8 client)     │   YOLOv8 perception service below
└─────────────────────────────┘

┌─────────────────────────────┐
│   perception/ — Docker svc  │   FastAPI + YOLOv8n, containerized.
│   (optional, for web/'s     │   Runs object detection on drone POV
│    live detection overlay)  │   frames sent from the browser sim.
└─────────────────────────────┘
```

### Canonical data contracts

Every module that produces or consumes drone/world state uses the same
shape, defined once in Python and once in JavaScript and kept in sync:

**`DroneState`** (`backend/schemas/drone_state.py`, `shared/schemas/droneState.js`)
```json
{
  "id": "0",
  "position": { "x": 0.0, "y": 0.0, "z": 0.0 },
  "velocity": { "x": 0.0, "y": 0.0, "z": 0.0 },
  "heading": 0.0,
  "battery": 1.0,
  "status": "ACTIVE"
}
```
`status` is one of `ACTIVE | IDLE | STUCK | OFFLINE`. A drone is marked
`STUCK` only when it is both moving slowly **and** meaningfully far from
its current target, sustained for a short debounce window — a single
velocity check isn't enough to distinguish "stuck" from "correctly
decelerating on arrival."

**Hazard/terrain grid**
```json
{ "grid": [[0, 1, 0, ...], ...], "cellSize": 10 }
```

**Perception detection**
```json
[{ "class": "obstacle", "bbox": [x, y, w, h], "confidence": 0.87 }]
```

---

## Quickstart

### 1. Browser preview (no install, no backend needed)

```bash
# from the repo root
open web/index.html
# or serve it locally, e.g.:
python -m http.server 8000 --directory web
```

This runs the full APF swarm simulation client-side. Use the scenario
selector to switch between preset environments (open field, dense
obstacles, search-and-rescue formation, etc.) and formation protocols.

### 2. PyBullet backend + React dashboard

```bash
# Backend
cd backend
pip install -r requirements.txt
python master_sim_server.py
# → WebSocket telemetry on ws://localhost:8765
# → MJPEG camera stream on http://localhost:5000/video_feed

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
# → opens the live dashboard, connects to the backend automatically
```

### 3. (Optional) YOLOv8 perception service, for the browser preview's live detection overlay

```bash
cd perception
docker build -t droneswarm-perception .
docker run -p 8001:8001 droneswarm-perception
```

The browser preview's perception client (`web/perception/`) polls this
service for object detections on the active drone's POV frame.

---

## Repository Layout

```
DroneSwampMapping/
├── backend/                 PyBullet showcase simulation
│   ├── master_sim.py          Standalone local entry point (GUI window)
│   ├── master_sim_server.py   Headless-capable server: WebSocket telemetry
│   │                          + MJPEG camera stream, drives the React frontend
│   ├── swarm_controller.py    Bridges PyBullet rigid bodies ↔ VectorSwarm
│   ├── perfect_swarm.py       VectorSwarm APF engine + formation generators
│   ├── obstacle_map.py        Builds 3D AABB obstacle volumes from city geometry
│   ├── city_layout.py         Procedural city generation (Kenney asset kits)
│   ├── vision_engine.py       RGB/depth/segmentation camera rendering
│   └── schemas/                Canonical DroneState (Python)
│
├── frontend/                 React dashboard (Vite)
│   └── src/
│       ├── contexts/            SimulationContext (WebSocket), DroneContext
│       ├── components/          BottomStats, CoverageMap, DroneCard, ...
│       └── services/            simulatorService.js (framework-agnostic WS client)
│
├── web/                      Browser-only Three.js preview (zero install)
│   ├── main.js                 Bootstrap + render loop
│   ├── core/                   Fixed-timestep physics loop, Drone state
│   ├── swarm/                  VectorSwarm.js (JS port) + formation generators
│   ├── render/                 SceneManager, DroneRenderer, TerrainRenderer
│   ├── data/                   Heightmap generation, preset scenarios
│   ├── ui/                     ControlPanel (scenario/formation/drone-count UI)
│   └── perception/              YOLOv8 client for the optional detection overlay
│
├── perception/                Dockerized FastAPI + YOLOv8n detection service
│
├── shared/schemas/            Canonical DroneState (JavaScript)
│
└── tests/, backend/tests/, web/tests/
    Cross-language fixture tests (Python ↔ JS parity for the swarm engine
    and formation generators), unit tests for swarm physics, formation
    modes, and the PyBullet integration layer.
```

---

## Formation Protocols

The swarm supports pluggable formation modes, implemented identically
(fixture-verified) in both `backend/perfect_swarm.py` and
`web/swarm/VectorSwarm.js`:

| Mode | Behavior |
|---|---|
| **Orbit** *(default)* | Followers circle the lead drone at a fixed radius, each at its own angular offset. |
| **Beta** — Linear Sweep | Drones distribute evenly along a line between two points — a search/coverage sweep formation. |
| **Gamma** — Dynamic Encirclement | Drones distribute evenly around a circle at a given radius — a containment/encirclement formation. |

In the PyBullet backend, switch modes live over the WebSocket connection:

```json
{ "type": "SET_FORMATION", "payload": { "mode": "beta", "start_point": [0, 0], "end_point": [100, 0] } }
```

In the browser preview, formations are selected via the scenario
dropdown or by calling `generateProtocolBeta()` / `generateProtocolGamma()`
directly from `web/swarm/VectorSwarm.js`.

All drones use a shared Artificial Potential Fields core regardless of
formation mode: attraction toward the current target, inter-drone
separation, obstacle repulsion (from real 3D geometry in the PyBullet
backend, from precomputed obstacle shapes in the browser preview), and
stuck-detection with escape-noise recovery.

---

## Roadmap

**Done:**
- Canonical `DroneState` schema, unified across backend, frontend, and browser preview
- One APF swarm engine driving both the PyBullet showcase and the browser preview, cross-language fixture-verified
- Dynamic drone count (add/remove live, in both simulation surfaces)
- Formation protocols (orbit, linear sweep, dynamic encirclement) in both surfaces
- Procedural terrain (Perlin-noise heightmap) and preset scenarios in the browser preview
- Real-time React dashboard with live telemetry and camera POV

**In progress / planned:**
- **Map/environment builder** — construct scenes from real GPS coordinates, Google Earth imports, or live sensor feeds, using a shared structure library
- **Autonomous mission generator** — pathfinding (A*), automatic lead-drone assignment, and formation generation from a target region, with code/visual output. A working A* planner and hierarchical decision engine exist and are being adapted to the current 3D obstacle representation.
- **Hardware compatibility bridge** — sim-first, controller-next: the same mission/command interface that drives the simulation will drive real hardware later
- **3D formation view in the React dashboard** — currently only available in the browser preview and the PyBullet GUI

---

## Contributing

This project uses a branch-per-owner workflow, consolidated into `main`
by the integration lead. If you're picking up an open task:

1. Branch off current `main`.
2. Keep changes scoped — small, verifiable commits over large batched
   ones. This project has a real history of work being reported complete
   without being committed; verified, working commits are what count.
3. Open a PR into `main` when ready. Include how you verified your
   change actually works (test output, a description of manual testing
   performed), not just that it "should" work.

---

## License

*(Not yet specified — add a LICENSE file to make usage terms explicit.)*
