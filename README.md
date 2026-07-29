# Swarm Robotics: 3D Physics Simulation & Perception Architecture

## Overview

**DroneSwampMapping** is a full-stack, offline-capable 3D physics simulation and perception pipeline for drone swarm kinematics, real-time computer vision, and geo-spatial coordinate mapping. The architecture pairs a **Hybrid AI Decision Engine** (combining grid-based $A^*$ global routing with continuous Artificial Potential Fields micro-kinematics) with a **Three.js 3D Web Visualizer**, a containerized **FastAPI YOLOv8 Perception Microservice**, and an auto-reconnecting **WebSocket Data Streaming Interface**.

---

## Team Role Boundaries & Module Ownership

| Role | Module Scope | Responsibilities & Data Contracts |
| :--- | :--- | :--- |
| **YOLOv8 / Perception Lead** | `perception/`, `vision_engine.py`, `web/perception/` | • Captures synthetic $320 \times 240$ JPEG drone cockpit POV frames.<br>• Runs YOLOv8 / OpenCV DNN ONNX inference (`POST /detect`).<br>• Streams JSON detections payload over WebSocket to `ws://localhost:8765`. |
| **Frontend / Simulator Lead** | `web/core/`, `web/render/`, `web/ui/` | • Manages Three.js r170 3D renderer, drone meshes, and trajectory trails.<br>• Exposes offscreen per-drone POV perspective camera (`DroneCamera.js`).<br>• Hosts fixed-timestep physics loop ($\Delta t = 1/60\text{ s}$) and live HUD panel. |
| **Kinematics & Swarm Lead** | `perfect_swarm.py`, `web/swarm/` | • Implements continuous APF physics (attraction, repulsion, speed clamp).<br>• Maintains tactical formation protocol generators (Beta & Gamma).<br>• Ensures numerical convergence between Python and JS ports. |
| **Pipeline & Mapping Lead** | `geo_engine.py`, `map_engine.py` | • Translates viewport pixel coordinates into WGS84 GPS (Latitude, Longitude).<br>• Listens to WebSocket (`ws://localhost:8765`) for `yolo_detections` payloads.<br>• Builds global hazard maps and target tracking logs. |

---

## Directory & Architecture Layout

```
DroneSwampMapping/
├── web/                           # Client-side 3D Web Simulator & Visualizer
│   ├── core/                      # Fixed-timestep physics loop (SimulationLoop.js) & Drone model (Drone.js)
│   ├── render/                    # Three.js 3D scene manager (SceneManager.js), drone meshes (DroneRenderer.js) & POV camera (DroneCamera.js)
│   ├── swarm/                     # VectorSwarm (APF) physics engine & Tactical Protocols (Beta/Gamma)
│   ├── perception/                # Async web perception client & WebSocket stream to ws://localhost:8765
│   ├── ui/                        # Control panel & live HUD telemetry (ControlPanel.js)
│   └── tests/                     # Automated browser fixture verification suite (test_swarm.html)
├── perception/                    # YOLOv8 Computer Vision Microservice
│   ├── main.py                    # FastAPI server exposing GET /health & POST /detect
│   ├── Dockerfile                 # CPU-optimized PyTorch container build definition
│   └── yolov8n.pt                 # YOLOv8 nano model weights
├── geo_engine.py                  # Mercator Web Projection (Pixel-to-GPS translator)
├── map_engine.py                  # In-memory synthetic satellite viewport extraction
├── perfect_swarm.py               # Vectorized APF physics engine & Tactical Protocols (NumPy)
├── master_sim.py                  # Python simulation & Matplotlib 3D visualizer
├── vision_engine.py               # CPU-optimized OpenCV DNN ONNX inference engine
├── main.py                        # End-to-end Python pipeline (Map -> Vision -> GPS)
├── tests/                         # Test suite
│   ├── test_perception_endpoint.py# Perception HTTP endpoint & WebSocket connection verification
│   └── generate_fixture.py        # Reference snapshot fixture generator (fixture_snapshot.json)
└── docker-compose.yml             # Perception service container orchestration
```

---

## 1. Perception Microservice & AI Pipeline

### A. FastAPI Server (`perception/main.py`)
Hosted via Uvicorn with CORS middleware enabled for cross-origin browser access (`http://localhost:3000`).

- **`GET /health`**: Returns service status and model metadata:
  ```json
  { "status": "ok", "service": "perception", "model": "yolov8n.pt", "timestamp": 1770000000.0 }
  ```
- **`POST /detect`**: Accepts $320 \times 240$ JPEG/PNG frame uploads (`multipart/form-data` with field name `file`) and returns bounding box detections:
  ```json
  {
    "detections": [
      {
        "class": "obstacle",
        "bbox": [10.0, 20.0, 50.0, 80.0],
        "confidence": 0.91
      }
    ],
    "inference_time_ms": 14.2,
    "image_size": [320, 240]
  }
  ```

### B. CPU-Optimized Vision Engine (`vision_engine.py`)
- **Engine:** OpenCV DNN (`cv2.dnn.readNetFromONNX`) configured for CPU execution.
- **Pipeline:** Pre-warms memory tensors $\to$ Rescales input to $416 \times 416$ tensor $\to$ Filters confidence scores ($\ge 0.4$) $\to$ Non-Maximum Suppression (NMS, threshold $0.45$) $\to$ Maps bounding box coordinates back to original frame dimensions.

### C. Web Perception & WebSocket Client (`web/perception/index.js`)
- Grabs $320 \times 240$ JPEG frame blobs periodically ($800\text{ ms}$ interval) from `DroneCamera.js`.
- Posts frame blobs to `POST http://localhost:8000/detect`.
- **WebSocket Streaming:** Auto-reconnecting WebSocket client forwards detection payloads to `ws://localhost:8765` using this format:
  ```json
  {
    "type": "yolo_detections",
    "droneId": 1,
    "payload": [
      { "class": "obstacle", "bbox": [10.0, 20.0, 50.0, 80.0], "confidence": 0.91 }
    ]
  }
  ```

---

## 2. Kinematics & Artificial Potential Fields (APF) Engine

The physics engine is implemented in both [perfect_swarm.py](file:///Users/rahuldattasutar/Desktop/Swamp%20Drone/DroneSwampMapping/perfect_swarm.py) (Python) and [VectorSwarm.js](file:///Users/rahuldattasutar/Desktop/Swamp%20Drone/DroneSwampMapping/web/swarm/VectorSwarm.js) (JavaScript).

### Force Integration Equations
1. **Attractive Force ($F_{\text{att}}$):** Pulls drone toward target position $\vec{p}_{\text{target}}$:
   $$F_{\text{att}} = 0.15 \cdot \left(\vec{p}_{\text{target}} - \vec{p}_{\text{drone}}\right)$$
2. **Inter-Drone Repulsion ($F_{\text{rep, drone}}$):** Evaluated when inter-drone distance $d < 5.0\text{ m}$:
   $$F_{\text{rep, drone}} = 150.0 \cdot \left(\frac{1}{d} - \frac{1}{5.0}\right) \cdot \frac{1}{d^2} \cdot \frac{\vec{p}_i - \vec{p}_j}{d}$$
3. **Obstacle Surface Repulsion ($F_{\text{rep, obs}}$):** Evaluated on horizontal plane $(x, y)$ when surface distance $d_{\text{surf}} < 5.0\text{ m}$:
   $$F_{\text{rep, obs}} = 800.0 \cdot \left(\frac{1}{d_{\text{surf}}} - \frac{1}{5.0}\right) \cdot \frac{1}{d_{\text{surf}}^2} \cdot \frac{\vec{p}_{\text{xy}} - \vec{o}_{\text{xy}}}{d_{\text{center}}}$$
4. **Momentum & Position Integration:**
   $$\vec{v}_{t+1} = 0.85 \cdot \vec{v}_t + 0.15 \cdot (F_{\text{att}} + F_{\text{rep}})$$
   $$\vec{p}_{t+1} = \vec{p}_t + \vec{v}_{t+1} \cdot s \quad (s = 0.18\text{ s})$$
5. **Speed Clamping:** Bounded to $v_{\max} = 3.5\text{ m/s}$.
6. **Stochastic Escape Vector:** If $\|\vec{v}\| < 0.1\text{ m/s}$ and target distance $> 3.0\text{ m}$, uniform random perturbation noise $\vec{\eta} \in [-1.0, 1.0]^2$ is added to horizontal axes to break force equilibrium.

---

## 3. Geo-Spatial Projection Engine (`geo_engine.py`)

Translates local 2D viewport pixel coordinates $(x, y)$ into WGS84 GPS Latitude ($\phi$) and Longitude ($\lambda$):

$$\text{Resolution} = \frac{2\pi \cdot R_{\text{Earth}} \cdot \cos(\phi_0)}{W \cdot 2^Z} \quad (R_{\text{Earth}} = 6,378,137\text{ m})$$
$$\Delta x_{\text{meters}} = \left(x - \frac{W}{2}\right) \cdot \text{Resolution}, \quad \Delta y_{\text{meters}} = \left(\frac{H}{2} - y\right) \cdot \text{Resolution}$$
$$\Delta \phi = \frac{\Delta y_{\text{meters}}}{R_{\text{Earth}}} \cdot \left(\frac{180}{\pi}\right), \quad \Delta \lambda = \frac{\Delta x_{\text{meters}}}{R_{\text{Earth}} \cdot \cos(\phi_0)} \cdot \left(\frac{180}{\pi}\right)$$
$$\phi_{\text{target}} = \phi_0 + \Delta \phi, \quad \lambda_{\text{target}} = \lambda_0 + \Delta \lambda$$

---

## 4. Swarm Tactical Formation Protocols

Available via `generate_protocol_beta` / `generate_protocol_gamma` (Python) and `generateProtocolBeta` / `generateProtocolGamma` (JS):

- **Protocol Beta (Linear Sweep):** Linear axis interpolation mapping $N$ drones into an evenly spaced horizontal sweep line for systematic region inspection.
- **Protocol Gamma (Dynamic Encirclement):** Trigonometric distribution forming a $360^\circ$ containment ring surrounding target coordinates:
  $$x_i = x_{\text{target}} + R \cdot \cos\left(\frac{2\pi \cdot i}{N}\right), \quad y_i = y_{\text{target}} + R \cdot \sin\left(\frac{2\pi \cdot i}{N}\right)$$

---

## 5. Verification & Testing Suite

* **Perception Verification ([tests/test_perception_endpoint.py](file:///Users/rahuldattasutar/Desktop/Swamp%20Drone/DroneSwampMapping/tests/test_perception_endpoint.py)):** Tests `GET /health`, `POST /detect` schema validation, and graceful WebSocket connection checks to `ws://localhost:8765`.
* **Browser Fixture Verification ([web/tests/test_swarm.html](file:///Users/rahuldattasutar/Desktop/Swamp%20Drone/DroneSwampMapping/web/tests/test_swarm.html)):** Automated browser test suite verifying JS `VectorSwarm` outputs against Python reference snapshot fixtures.
* **Snapshot Generator ([tests/generate_fixture.py](file:///Users/rahuldattasutar/Desktop/Swamp%20Drone/DroneSwampMapping/tests/generate_fixture.py)):** Deterministic snapshot generator producing `fixture_snapshot.json`.

---

## How to Run

### 1. Web Simulator (Client-Side)
```bash
# Option A: Python Built-in HTTP Server
python3 -m http.server 3000 -d web

# Option B: Node / npx serve
cd web
npx serve . -p 3000
```
Open **[http://localhost:3000](http://localhost:3000)** in your browser.

### 2. Perception Service (FastAPI / YOLOv8 Backend)
```bash
# Option A: Docker Compose (Recommended)
docker compose up --build

# Option B: Direct Uvicorn Launch
cd perception
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```
Check health status: `curl http://localhost:8000/health`

### 3. Verification & Simulation Scripts
```bash
# Run Perception Endpoint & WebSocket Test Suite
python3 tests/test_perception_endpoint.py

# Run 3D Matplotlib Swarm Master Simulation
python3 master_sim.py

# Run End-to-End Pipeline (Map -> Vision -> GPS)
python3 main.py

# Run Geo-Engine Mercator Projection Test
python3 geo_engine.py

# Regenerate Reference Fixture Snapshot
python3 tests/generate_fixture.py
```