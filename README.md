# DroneSwampMapping — Offline Aerial Target Detection Pipeline

**Author:** Rahul Datta Sutar
**Performance:** ~19–24 ms inference latency | 41–52 FPS throughput | $0 API cost

---

## Overview

DroneSwampMapping is a fully offline, CPU-only aerial target detection pipeline built for drone swarm coordination. It combines a custom-trained **YOLOv8 Nano ONNX** model with a lightweight map engine and a geodetic translation layer to detect targets in satellite / orthomosaic imagery and report their real-world GPS coordinates — all in memory, with no network calls.

---

## Architecture

```
map_cache/  (aerial images)
      │
      ▼
SyntheticMapEngine        ← map_engine.py
  Loads & crops viewport (600×600 px) from offline satellite image or map cache
      │
      ▼
YOLOVisionEngine          ← vision_engine.py
  Resizes frame to 416×416, runs ONNX inference via OpenCV DNN,
  applies NMS, maps detections back to native canvas coordinates
      │
      ▼
GeoTranslationEngine      ← geo_engine.py
  Converts pixel (x, y) → real-world (Latitude, Longitude)
  using Web Mercator projection + Earth-radius math
      │
      ▼
Tracker output / GPS coordinates
```

### Core Modules

| File | Class / Role |
|---|---|
| `vision_engine.py` | `YOLOVisionEngine` — ONNX inference, NMS, latency profiling |
| `map_engine.py` | `SyntheticMapEngine` — In-memory viewport extraction from offline map |
| `geo_engine.py` | `GeoTranslationEngine` — Pixel-to-GPS coordinate translation |
| `main.py` | Simulation orchestrator (end-to-end pipeline entry point) |
| `run_on_map_cache.py` | Batch inference runner on all images in `map_cache/` |
| `run_local_test.py` | Synthetic canvas unit test for model sanity check |

### Model

- **`best.onnx`** — YOLOv8 Nano, custom-trained for aerial target detection
- Input size: `416×416` (images are scaled internally; native resolution is preserved for output coordinates)
- Backend: OpenCV DNN (`DNN_BACKEND_OPENCV`, `DNN_TARGET_CPU`)
- Confidence threshold: `0.05` (map cache runs) / `0.4` (default)
- NMS threshold: `0.45`

---

## Setup

### 1. Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install opencv-python-headless numpy
```

> Use `opencv-python` instead of `opencv-python-headless` if you need GUI windows.

### 3. Place your model

Ensure `best.onnx` is in the project root. The model is loaded automatically by all entry-point scripts.

---

## Usage

### Run inference on `map_cache/` images

Processes all `.png`, `.jpg`, `.jpeg` images found in `map_cache/` sequentially:

```bash
python3 run_on_map_cache.py
```

Run on a specific image:

```bash
python3 run_on_map_cache.py map_cache/orthomosaic_3.png
```

### Run the full simulation pipeline

Loads the offline map, extracts a 600×600 viewport at the configured GPS coordinates, runs YOLO detection, and prints real-world GPS positions of all targets:

```bash
python3 main.py
```

Edit `DRONE_LAT`, `DRONE_LON`, and `ZOOM` at the bottom of `main.py` to change the simulation location.

### Run the local synthetic canvas test

Verifies model loading and inference correctness using a synthetic in-memory canvas (no image file required):

```bash
python3 run_local_test.py
```

---

## Sample Output

```
[Vision Loop] Inference Latency (ms): 21.23 | Processing Framerate (FPS): 47.11

=== run_on_map_cache results ===
Image: map_cache/map_18.4575_73.8508_18.png
Detected 2 target(s):

  [0] x=233.1627, y=241.5093
  [1] x=337.5576, y=151.6360
Single-run latency (ms): 21.31

=== run_on_map_cache results ===
Image: map_cache/orthomosaic_3.png
Detected 4 target(s):

  [0] x=643.6283, y=146.9586
  [1] x=575.0607, y=929.5382
  [2] x=219.1907, y=250.8185
  [3] x=90.6124, y=222.8723
Single-run latency (ms): 23.96
```

---

## Performance

| Metric | Observed Range |
|---|---|
| Inference latency | 19 – 24 ms |
| Processing framerate | 41 – 52 FPS |
| API cost | $0 (fully offline) |
| Hardware requirement | CPU only (no GPU needed) |

---

## Project Structure

```
DroneSwampMapping/
├── best.onnx               # Custom YOLOv8 Nano ONNX model
├── main.py                 # End-to-end simulation pipeline
├── vision_engine.py        # YOLOVisionEngine — inference & NMS
├── map_engine.py           # SyntheticMapEngine — viewport generation
├── geo_engine.py           # GeoTranslationEngine — pixel → GPS
├── run_on_map_cache.py     # Batch inference runner on map_cache/
├── run_local_test.py       # Synthetic canvas unit test
├── map_cache/              # Directory of aerial / orthomosaic images
│   ├── map_18.4575_73.8508_18.png
│   ├── orthomosaic_3.png
│   └── orthomosaic_4.jpg
└── yolov8n.pt              # YOLOv8 Nano PyTorch weights (training reference)
```

---

## Notes

- The pipeline is **fully in-memory** — no intermediate files are written during inference.
- `SyntheticMapEngine` falls back to `map_cache/` if no `offline_campus.png` source is present.
- Coordinate outputs from `run_on_map_cache.py` are in **native image pixel space**; GPS translation requires running through `main.py` with a known center lat/lon and zoom.
- `get_map_image()` in `map_engine.py` and `pixel_to_gps()` in `geo_engine.py` are deprecated legacy wrappers kept for backward compatibility.