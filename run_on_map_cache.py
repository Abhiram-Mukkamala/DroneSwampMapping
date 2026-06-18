#!/usr/bin/env python3
"""Run YOLOVisionEngine on images from map_cache/ and print detections + timing.

Usage:
  python3 run_on_map_cache.py            # runs on the first image found in map_cache/
  python3 run_on_map_cache.py <image>    # runs on specified image path

This script is memory-only and performs no writes.
"""
from typing import List, Tuple, Optional
import time
import os
import sys
import glob

try:
    import cv2
except Exception:
    print("Missing dependency 'cv2'. Install with: python3 -m pip install opencv-python-headless")
    sys.exit(1)

import numpy as np
from vision_engine import YOLOVisionEngine

MAP_CACHE_DIR = os.path.join(os.path.dirname(__file__), "map_cache")


def find_images_in_map_cache() -> List[str]:
    patterns = ["*.png", "*.jpg", "*.jpeg"]
    files_all: List[str] = []
    for pat in patterns:
        files = sorted(glob.glob(os.path.join(MAP_CACHE_DIR, pat)))
        files_all.extend(files)
    return files_all


def run_on_image(engine: YOLOVisionEngine, image_path: str) -> List[Tuple[float, float]]:
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    img = cv2.imread(image_path)
    if img is None:
        raise RuntimeError(f"Failed to load image as BGR array: {image_path}")

    start = time.perf_counter()
    results = engine.detect_targets(img, conf_threshold=0.05)
    end = time.perf_counter()

    latency_ms = (end - start) * 1000.0

    print("\n=== run_on_map_cache results ===")
    print(f"Image: {image_path}")
    print(f"Detected {len(results)} target(s):")
    for i, (x, y) in enumerate(results):
        print(f"  [{i}] x={x:.4f}, y={y:.4f}")
    print(f"Single-run latency (ms): {latency_ms:.2f}")

    return results


if __name__ == "__main__":
    # CLI: optional path or --all to process all images in map_cache
    args = sys.argv[1:]
    all_flag = False
    supplied_path: Optional[str] = None
    if len(args) > 0:
        if args[0] in ("--all", "-a"):
            all_flag = True
        else:
            supplied_path = args[0]

    # Gather target files
    images: List[str] = []
    if supplied_path:
        if os.path.isdir(supplied_path):
            images = find_images_in_map_cache()
        else:
            images = [supplied_path]
    else:
        images = find_images_in_map_cache()

    if not images:
        print(f"No images found in {MAP_CACHE_DIR}. Add images or pass a path as an argument.")
        sys.exit(1)

    # Instantiate the model once for efficiency
    try:
        engine = YOLOVisionEngine("best.onnx")
    except Exception as e:
        print(f"Failed to initialize model: {e}")
        sys.exit(1)

    # If not all_flag and multiple images exist, process sequentially by default
    for img_path in images:
        try:
            run_on_image(engine, img_path)
        except Exception as exc:
            print(f"Error processing {img_path}: {exc}")
