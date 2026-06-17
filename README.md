# Swarm Simulation Engine - Low Latency Offline Module

**Author:** Rahul Wadhwani  
**Performance:** < 15ms Latency | $0 Cost

## Overview
This module is the high-speed, fully offline backend simulation engine for the Multi-Drone Coordination System. It bypasses network latency by utilizing local maps and pure algorithmic computer vision.

* **Map Engine:** Reads a high-resolution local satellite image (`offline_campus.png`) and instantly crops a 600x600 viewport based on the drone's GPS coordinates.
* **Vision Engine:** Uses an ultra-fast OpenCV HSV color-masking algorithm to track targets and calculate their exact center pixels.
* **Geo Engine:** Translates 2D pixel coordinates back into real-world Latitude and Longitude using Earth curvature mathematics.

## Setup
1. Install the required dependencies:
   ```bash
   pip install opencv-python numpy