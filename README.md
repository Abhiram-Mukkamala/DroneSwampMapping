# Swarm Robotics: Hybrid A* & Artificial Potential Fields (APF) Architecture

## Overview
This repository contains a locally hosted, offline-capable 3D physics simulation for drone swarm kinematics. The system utilizes a **Hybrid AI Decision Engine** that bridges discrete grid-based global routing with continuous, real-time physics and vector math.

Our architecture successfully solves the "Rubber Band" deadlock and Local Minima traps often found in swarm robotics by cleanly separating Macro-navigation from Micro-kinematics.

## Core Architecture

### 1. The Macro Brain (A* Global Planner)
* **File:** `path_planning.py`
* **Function:** Analyzes the global 2D grid and generates a safe, optimal list of rigid 3D waypoints. 
* **Update:** We increased the obstacle `safety_margin` to force the global pathing to route completely outside of the APF forcefields, preventing algorithm crossfire.

### 2. The Orchestrator (Decision Engine)
* **File:** `decision_engine.py`
* **Function:** Acts as the bridge between the A* grid and the continuous physics engine.
* **Update:** Stripped out legacy Reynolds Boids math (which violently conflicted with APF repulsion). Implemented **Pure Pursuit Lookahead Logic** (`curr_idx + 2`). Instead of panicking when a drone gets bumped off the exact grid path, the engine dynamically re-anchors the drone to the next upcoming waypoint, allowing for smooth, sweeping aerodynamic turns.

### 3. The Reflexes (APF Kinematics)
* **File:** `perfect_swarm.py`
* **Function:** Calculates real-time velocity, inertia smoothing, and surface-boundary repulsion. 
* **Update:** Replaced hardcoded collision detection with a mathematically guaranteed 2.0m repulsion safety bubble. Injected **Stochastic Noise (Escape Vectors)** to automatically break drones out of zero-velocity Local Minima dead zones. 

### 4. Vision & Telemetry (The Network)
* **Integration:** Converts live VisDrone ONNX bounding boxes into dynamic APF obstacles in real-time. The swarm uses a mock telemetry mesh to share target and obstacle coordinates, ensuring unified swarm intelligence without relying on external APIs.

## How to Run the Simulation
Ensure all core files are in the same directory. To launch the Matplotlib 3D kinematic visualizer and test the Hybrid Engine:

```bash
python master_sim.py