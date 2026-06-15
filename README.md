# Swarm Simulation Engine - Backend Module

**Author:** Rahul Wadhwani  
**Module:** Geospatial Translation & Vision AI  

## Overview
This module acts as the backend simulation engine for the Multi-Drone Coordination System. Since physical drones cannot be flown for every software test, this engine fakes the drone's telemetry and visual feeds. 

It executes a 3-step pipeline:
1. **Map Engine:** Bypasses local caching to download a top-down synthetic camera viewport (satellite tile) from Mapbox based on the drone's current GPS location.
2. **Vision Engine:** Scans the synthetic viewport using a YOLOv8 AI model to detect targets and calculate their exact center-pixel coordinates.
3. **Geo Engine:** Translates the target's 2D pixel coordinates $(X,Y)$ into real-world Latitude and Longitude coordinates using the Earth's curvature and camera scale.

## Prerequisites
Ensure you have Python installed, then install the required AI and Vision libraries. *(Note: The Map Engine uses Python's built-in `urllib` to prevent environment conflicts, so `requests` is not required).*

```bash
pip install ultralytics opencv-python