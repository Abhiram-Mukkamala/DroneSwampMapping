# Swarm Robotics: 3D Physics Simulation & Perception Architecture

## Overview
This repository features a client-side **3D Web Drone Swarm Simulator** built with Three.js and a vectorized **Artificial Potential Fields (APF) formation engine**. It pairs interactive browser-based simulation with a containerized **FastAPI YOLOv8 Perception Service** for object detection on simulated drone camera feeds, alongside Python geospatial and APF physics reference engines.

> [!NOTE]
> The 3D Web Simulator and FastAPI Perception Microservice are fully functional. The legacy Python simulation pipeline is currently undergoing refactoring as legacy pathfinding scripts are being replaced.

---

## Architecture & System Components

```
droneswarm/
├── web/                           # Client-side 3D Web Simulator (Primary Flagship)
│   ├── core/                      # Fixed-timestep physics loop & drone state contract
│   ├── render/                    # Three.js scene manager, drone meshes & POV camera
│   ├── swarm/                     # VectorSwarm (APF) JS formation engine
│   ├── perception/                # Async web perception client & overlay renderer
│   ├── ui/                        # Control panel, scenario selector & HUD telemetry
│   └── tests/                     # Automated fixture verification suite
├── perception/                    # YOLOv8 Computer Vision Microservice
│   ├── main.py                    # FastAPI server (/detect & /health endpoints)
│   ├── Dockerfile                 # CPU-optimized PyTorch container environment
│   └── yolov8n.pt                 # YOLOv8 nano model weights
├── geo_engine.py                  # Mercator Web Projection (Pixel-to-GPS translator)
├── perfect_swarm.py               # Vectorized APF physics engine reference (NumPy)
├── swarm_mesh.py                  # Standalone 3D Matplotlib APF simulation demo
├── requirements.txt               # Standalone Python dependencies
└── docker-compose.yml             # Container orchestration for perception API
```

### 1. Browser-Based 3D Simulator (`web/`) — **[Working]**
* **3D Renderer & Scene Manager (`web/render/`):** Built on Three.js (r170), rendering multi-drone swarms, dynamic lighting, trajectory trails, and environmental obstacles.
* **Per-Drone POV Feed (`web/render/DroneCamera.js`):** Dedicated 320x240 cockpit viewport camera attached to individual drones (75° FOV) with frame extraction.
* **VectorSwarm APF Engine (`web/swarm/`):** High-performance JavaScript port of the NumPy Artificial Potential Fields (APF) physics engine running in a fixed-timestep loop.
* **Interactive Control Panel (`web/ui/`):** Live scenario selector, real-time drone count scaling (1–100), play/pause controls, HUD stats (FPS, physics ticks, battery), and perception overlay toggle.

### 2. YOLOv8 Perception Microservice (`perception/`) — **[Working]**
* **FastAPI Object Detection Service (`perception/main.py`):** Real-time object detection backend powered by YOLOv8 (`yolov8n.pt`) exposing POST `/detect` (accepts JPEG frames and returns detected bounding boxes, class labels, and confidence metrics) and GET `/health`.
* **Containerized Deployment (`docker-compose.yml`, `perception/Dockerfile`):** Lightweight CPU-optimized PyTorch environment configured with CORS support for browser access.
* **Web Perception Integration (`web/perception/`):** Asynchronous client featuring health polling, frame rate throttling, non-blocking upload queues, and 2D bounding box overlay rendering on top of the live drone POV stream.

### 3. Python Physics & Geospatial Reference Modules
* **Vectorized APF Physics (`perfect_swarm.py`):** Standalone NumPy implementation of attractive/repulsive swarm forces, obstacle avoidance, and stochastic noise trap escape.
* **3D Matplotlib Demo (`swarm_mesh.py`):** Interactive 3D visualization of a 6-drone swarm navigating around obstacle cylinders.
* **Mercator GeoTranslation Engine (`geo_engine.py`):** Converts 2D viewport pixel coordinates into real-world GPS Latitude and Longitude using Web Mercator projections.

---

## Swarm Mission Protocols

The simulator supports mathematical formation protocols for multi-agent coordination:

* **Protocol Beta (Sweep):** Linear axis interpolation spacing drones into a horizontal sweep line.
* **Protocol Gamma (Encirclement):** Trigonometric distribution (Sine/Cosine vectors) forming a 360° dynamic ring around target coordinates.

---

## Verification & Testing Suite

* **Fixture Verification (`web/tests/test_swarm.html`):** Automated browser verification suite comparing JS algorithm outputs against Python reference snapshot fixtures (`fixture_snapshot.json`, `fixture_stuck_snapshot.json`).
* **Perception API Harness (`tests/test_perception_endpoint.py`):** Endpoint integration test verifying backend responsiveness and response contracts.

---

## How to Run

### 1. 3D Web Simulator (Client-Side)
Serve the `web` directory using any static file server:
```bash
# Option A: Python Built-in HTTP Server
python -m http.server 3000 -d web

# Option B: npx serve
cd web
npx serve . -p 3000
```
Open **[http://localhost:3000](http://localhost:3000)** in your browser.

### 2. Perception Service (YOLOv8 Backend)
```bash
# Option A: Docker Compose (Recommended)
docker compose up

# Option B: Direct Python
cd perception
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```
Check status: `curl http://localhost:8000/health`

---

## Current Project Status & Next Steps

### What's Built & Fully Working
- ✅ **Three.js Web Simulator:** 3D scene rendering, viewport camera streams, scenario presets, and telemetry UI.
- ✅ **JS APF Swarm Engine:** Ported vector physics engine running in browser with fixture test verification.
- ✅ **FastAPI Perception Server:** Dockerized object detection backend using stock YOLOv8 weights with live client bounding box overlay.
- ✅ **Python APF & Geo Math:** Standalone `perfect_swarm.py`, `swarm_mesh.py`, and `geo_engine.py`.

### Next Steps & Technical Roadmap
- ⚠️ **Restore Python Decision Pipeline:** Re-implement or remove missing legacy dependencies (`path_planning.py`, `decision_engine.py`, and `best.onnx`) referenced by `master_sim.py` and `main.py`.
- ⚠️ **Offline Map Assets:** Supply default satellite imagery tiles for `map_engine.py` to prevent blank viewport fallback.
- 📋 **WebSockets Perception Bridge:** Upgrade HTTP frame upload polling to WebSocket streaming for sub-15ms latency.
- 📋 **Terrain Elevation Colliders:** Wire heightmap elevation data (`web/data/Heightmap.js`) into 3D drone collision physics.