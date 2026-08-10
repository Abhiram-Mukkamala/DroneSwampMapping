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

## 📁 Repository Structure

```text
├── master_sim.py       # Main simulation loop, FPS flight controller & swarm AI logic
├── city_layout.py     # Procedural 3D city generator with concave mesh collision bounds
├── vision_engine.py   # Synthetic camera engine (RGB, Depth, Segmentation Masks)
├── requirements.txt   # Required Python dependencies
└── README.md          # Project documentation