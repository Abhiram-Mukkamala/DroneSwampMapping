import time
from typing import List, Tuple

import sys
try:
    import cv2
except Exception as e:
    print("Missing dependency 'cv2' (OpenCV). Please install it in your Python environment:")
    print("  python3 -m pip install --upgrade pip")
    print("  python3 -m pip install opencv-python-headless")
    # Exit early since further execution requires cv2
    sys.exit(1)

import numpy as np

from vision_engine import YOLOVisionEngine


def build_test_canvas(width: int = 600, height: int = 600) -> np.ndarray:
    """Create a blank RGB canvas and draw a solid white rectangle at specified bounds.

    Rectangle top-left: (100, 250)
    Rectangle bottom-right: (200, 350)
    """
    if width <= 0 or height <= 0:
        raise ValueError("Canvas width and height must be positive integers")

    canvas = np.zeros((height, width, 3), dtype=np.uint8)

    top_left = (100, 250)
    bottom_right = (200, 350)

    # Validate bounds
    for (x, y) in (top_left, bottom_right):
        if not (0 <= x <= width and 0 <= y <= height):
            raise ValueError("Rectangle coordinates are out of canvas bounds")

    # Draw filled white rectangle
    cv2.rectangle(canvas, top_left, bottom_right, color=(255, 255, 255), thickness=-1)

    return canvas


def run_test(model_path: str = "best.onnx") -> None:
    """Instantiate YOLOVisionEngine and run detection on the synthetic canvas.

    Prints returned absolute centers and latency metrics.
    """
    canvas = build_test_canvas()

    try:
        engine = YOLOVisionEngine(model_path)
    except Exception as e:
        print(f"Failed to initialize YOLOVisionEngine: {e}")
        return

    # Warm run + timed run
    try:
        start = time.perf_counter()
        results = engine.detect_targets(canvas)
        end = time.perf_counter()
    except Exception as e:
        print(f"Runtime error during detection: {e}")
        return

    latency_ms = (end - start) * 1000.0

    print("\n===== Local Verification Test =====")
    print(f"Synthetic rectangle center (expected): (150.0, 300.0)")
    print(f"Detection returned {len(results)} target(s):")

    if len(results) == 0:
        print("No targets detected. Check model confidence thresholds or model correctness.")
    else:
        for i, (x, y) in enumerate(results):
            print(f"  [{i}] -> x={x:.4f}, y={y:.4f}")

    print(f"Single-run latency (ms): {latency_ms:.2f}")
    if latency_ms <= 25.0:
        print("Performance: within target sub-25ms latency")
    else:
        print("Performance: exceeded sub-25ms target")


if __name__ == "__main__":
    run_test()
