# 🛸 Autonomous Drone Swarm City Navigation & Vision Engine

An interactive, physics-driven 3D drone swarm simulation built on **PyBullet**. This project features an FPS-style piloted **Leader Drone (Red)** followed by an autonomous **Swarm (Blue Drones)** that uses 26-direction spherical raycasting for dynamic obstacle avoidance in a procedurally generated 3D city layout.

The simulation includes a real-time **Vision Engine** generating synthetic **RGB**, **Depth Maps**, and **Segmentation Masks** directly from the lead follower drone's onboard camera.

---

## 🚀 Features

* **FPS-Style Flight Controls**: Manual piloting of the Red Leader Drone using standard WASD movement, Space/Shift vertical control, and mouse yaw turning.
* **Autonomous 3D Swarm Intelligence**: 6 dynamic follower drones navigating via Artificial Potential Fields (APF) and 26-directional spherical raycast sensors for instant wall and skyscraper detection.
* **Exact Concave Mesh Collisions**: Full 3D structural collision support utilizing PyBullet's `GEOM_FORCE_CONCAVE_TRIMESH` flag—preventing drones from phasing through walls, balconies, or building facades.
* **High-Airspace Launch**: All drones spawn cleanly in open sky ($Z = 35.0\text{m}$) to eliminate startup mesh interpenetration and allow smooth street descent.
* **Onboard Computer Vision Engine**: Renders live RGB, depth perception, and semantic segmentation camera feeds from the lead blue drone for vision model training or real-time target tracking.

---

## 🎮 Flight Controls

| Key / Input | Action |
| :--- | :--- |
| **`W` / `S`** | Fly Forward / Backward |
| **`A` / `D`** | Strafe Left / Right |
| **`Space`** | Ascend (Fly Higher) |
| **`Left Shift`** | Descend (Lower into City Streets) |
| **`Mouse Move`** | Turn Yaw Heading (Look Left / Right) |

---


## Overview
This branch integrates the standalone WebSocket perception pipeline directly into the PyBullet physics backend (`master_sim_server.py`). It enables real-time Artificial Potential Fields (APF) repulsion by mathematically translating YOLOv8 bounding boxes into a 2D dynamic hazard grid.

## Architectural Modifications

| Module | Location | Implementation Details |
| :--- | :--- | :--- |
| `PipelineNode` | `backend/data_pipeline.py` | Converted from a standalone server to an importable module. Enforces canonical `DroneState` schema. Maps bounding boxes to grid coordinates. |
| `master_sim_server.py` | `backend/master_sim_server.py` | Ingests the pipeline node. Routes WebSocket `yolo_detections` directly to the `ObstacleMap` class. |
| `ObstacleMap` | `backend/obstacle_map.py` | Ingests the 2D grid. Applies a localized moat repulsion force when a drone's spatial coordinates intersect an active hazard cell. |
| `test_client.py` | `backend/test_client.py` | Mock WebSocket client that transmits synthetic perception payloads for end-to-end integration verification. |

---

## Mathematical Integration (APF Repulsion)
The `PipelineNode` extracts the bounding box parameters $(x, y, w, h)$ and normalizes them against the defined cell size ($c$) to populate the 2D grid:

$$gx=\left\lfloor\frac{x}{c}\right\rfloor,\quad gy=\left\lfloor\frac{y}{c}\right\rfloor$$

The `ObstacleMap` checks the drone's position vector $\vec{p}$ against the grid. If the discrete cell value equals $1$, the system applies a fixed repulsive vector $\vec{F}_{\text{rep}}$ to the horizontal axes:

$$\vec{F}_{\text{rep}}=\begin{bmatrix}-150.0\\-150.0\\0.0\end{bmatrix}$$

---

## Canonical Data Contracts

### Perception Payload (Input)
```json
{
  "type": "yolo_detections",
  "payload": [
    {
      "class": "obstacle",
      "bbox": [10.0, 10.0, 20.0, 20.0],
      "confidence": 0.99
    }
  ]
}

Hazard Grid (Internal Routing)

{
  "type": "hazard_map",
  "payload": {
    "grid": [[0, 0], [0, 1]],
    "cellSize": 5
  }
}
---
Integration Verification Procedures
Open the primary terminal and initialize the master simulation server.

Open the secondary terminal and execute the mock perception client.

Verify the primary terminal logs the calculated repulsion force.
---
Execution Commands

cd backend
python master_sim_server.py

cd backend
python test_client.py

---
Expected Output Log
🔥 PROOF: Dynamic Repulsion Force Calculated -> [-150. -150.   0.]