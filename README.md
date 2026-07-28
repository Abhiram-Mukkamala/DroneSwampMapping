# Swarm Robotics: 3D Physics Simulation & Perception Architecture

## Overview
This repository contains a full-stack, offline-capable 3D physics simulation and perception pipeline for drone swarm kinematics, real-time computer vision, and geo-spatial coordinate mapping. The system pairs a **Hybrid AI Decision Engine** (combining grid-based global routing with continuous Artificial Potential Fields micro-kinematics) with a **Three.js Web Visualizer** and a containerized **FastAPI YOLOv8 Perception Service**.

---

## Architecture & System Components

```
droneswarm/
├── web/                           # Client-side 3D Web Simulator
│   ├── core/                      # Fixed-timestep physics loop & drone state contract
│   ├── render/                    # Three.js 3 scene manager, drone meshes & POV camera
│   ├── swarm/                     # VectorSwarm (APF) formation control engine
│   ├── perception/                # Async web perception client & bounding-box overlay
│   ├── ui/                        # Control panel & live HUD telemetry
│   └── tests/                     # Automated fixture verification suite
├── perception/                    # YOLOv8 Computer Vision Microservice
│   ├── main.py                    # FastAPI server (/detect & /health endpoints)
│   ├── Dockerfile                 # CPU-optimized PyTorch container environment
│   └── yolov8n.pt                 # YOLOv8 nano model weights
├── geo_engine.py                  # Mercator Web Projection (Pixel-to-GPS translator)
├── perfect_swarm.py               # Vectorized APF physics engine (NumPy)
├── master_sim.py                  # Python simulation & Matplotlib 3D visualizer
└── docker-compose.yml             # Perception service container orchestration
```

### 1. Browser-Based 3D Simulator (`web/`)
* **3D Renderer & Scene Manager (`web/render/`):** Built on Three.js, rendering multi-drone swarms, dynamic lighting, trajectory trails, and environmental obstacles.
* **Per-Drone POV Feed (`web/render/DroneCamera.js`):** Generates dedicated 320x240 cockpit viewport camera streams attached directly to individual drones (75° FOV) with frame export (`getFrameBlob`).
* **VectorSwarm APF Engine (`web/swarm/`, `web/core/`):** High-performance JavaScript port of the Artificial Potential Fields (APF) physics engine running fixed-timestep simulation loops.
* **Interactive Control Panel (`web/ui/ControlPanel.js`):** Provides live drone count controls, pause/reset state management, drone POV dropdown selector, HUD statistics (FPS, physics ticks, average battery), and live perception overlay rendering.

### 2. YOLOv8 Perception Microservice (`perception/`)
* **FastAPI Object Detection Service (`perception/main.py`):** Real-time object detection backend powered by YOLOv8 (`yolov8n.pt`) exposing POST `/detect` (accepts JPEG frames and returns detected bounding boxes, class labels, and confidence metrics) and GET `/health`.
* **Containerized Deployment (`docker-compose.yml`, `perception/Dockerfile`):** Lightweight CPU-optimized PyTorch environment configured with CORS support for browser access.
* **Web Perception Integration (`web/perception/`):** Asynchronous client featuring auto-reconnecting health polling, frame rate throttling, non-blocking upload queues, and 2D bounding box overlay rendering on top of the live drone POV stream.

### 3. Core Physics & Geo-Spatial Engine
* **Hybrid Decision Engine (`decision_engine.py`, `perfect_swarm.py`):** Bridges A* discrete global pathfinding with continuous APF micro-kinematics. Incorporates Pure Pursuit lookahead navigation (`curr_idx + 2`), 2.0m repulsion safety bubbles, and Stochastic Noise escape vectors to eliminate local minima traps.
* **Mercator GeoTranslation Engine (`geo_engine.py`):** Converts 2D viewport pixel coordinates into real-world GPS Latitude and Longitude using Web Mercator projections scaled by Earth radius, latitude radians, zoom level, and viewport dimensions.

---

## Swarm Mission Protocols

The orchestrator supports mathematical tactical formation protocols for multi-agent coordination:

* **Protocol Beta (Search & Rescue):** Linear axis interpolation that untangles drone trajectories and forms a perfectly spaced horizontal sweep line to inspect targets.
* **Protocol Gamma (Encirclement):** Trigonometric distribution (Sine/Cosine vectors) forming a 360° dynamic containment ring around target coordinates.

---

## Verification & Testing Suite

* **Fixture Verification (`web/tests/test_swarm.html`):** Automated browser verification suite comparing JS algorithm outputs against Python reference snapshot fixtures (`fixture_snapshot.json`, `fixture_stuck_snapshot.json`).
* **Perception API Harness (`tests/test_perception_endpoint.py`):** Endpoint integration test verifying backend responsiveness and response contracts.

---

## How to Run

### 1. Web Simulator (Client-Side)
Start a local web server serving the `web` directory:
```bash
# Option A: Python Built-in HTTP Server
python -m http.server 3000 -d web

# Option B: Node / npx serve
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

### 3. Python Master Simulation Engine
```bash
python master_sim.py
```