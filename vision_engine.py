import cv2
import numpy as np
import time
from typing import List, Tuple

class YOLOVisionEngine:
    """
    Production-grade object detection engine using OpenCV DNN with 
    optimized YOLOv8 Nano ONNX model running on CPU.
    """
    def __init__(self, model_path: str = "best.onnx") -> None:
        try:
            # Cleanly load the ONNX model
            self.net = cv2.dnn.readNetFromONNX(model_path)
            # Configure for maximum edge CPU hardware compatibility
            self.net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
            self.net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
            
            # Warm up the network to compile memory buffers and optimize subsequent runs
            dummy_blob = np.zeros((1, 3, 416, 416), dtype=np.float32)
            self.net.setInput(dummy_blob)
            self.net.forward()
        except Exception as e:
            raise RuntimeError(f"[YOLOVisionEngine] Failed to initialize network from '{model_path}': {e}")

    def detect_targets(self, frame: np.ndarray, conf_threshold: float = 0.4, nms_threshold: float = 0.45) -> List[Tuple[float, float]]:
        """
        Processes an input image (expected as a canvas, commonly 600x600),
        scales to 416x416 for model input, runs YOLOv8 ONNX inference, and
        maps bounding box center coordinates back to the native canvas space
        using the actual frame dimensions.

        Returns a list of target coordinates or an empty list if none are found.
        """
        if frame is None or frame.size == 0:
            return []

        # High-resolution performance profiler start
        start_time = time.perf_counter()

        try:
            h_orig, w_orig = frame.shape[:2]
            
            # Rescale and preprocess the image (600x600 -> 416x416)
            blob = cv2.dnn.blobFromImage(
                frame,
                scalefactor=1.0 / 255.0,
                size=(416, 416),
                mean=(0, 0, 0),
                swapRB=True,
                crop=False
            )
            
            self.net.setInput(blob)
            outputs = self.net.forward() # Shape format: [1, classes + 4, 3549]
            
            # Squeeze output to format: [classes + 4, 3549]
            predictions = np.squeeze(outputs)
            if len(predictions.shape) == 1:
                predictions = np.expand_dims(predictions, axis=0)
            predictions = predictions.T # Shape format: [3549, classes + 4]
            
            # Optimized Vectorized Parsing
            class_scores = predictions[:, 4:]
            class_ids = np.argmax(class_scores, axis=1)
            confidences = class_scores[np.arange(len(predictions)), class_ids]
            
            # Filter detections by confidence threshold
            conf_mask = confidences >= conf_threshold
            filtered_preds = predictions[conf_mask]
            filtered_confidences = confidences[conf_mask]
            filtered_class_ids = class_ids[conf_mask]
            
            boxes: List[List[int]] = []
            for pred in filtered_preds:
                cx, cy, w_box, h_box = pred[0:4]
                # Convert center-based coordinates to top-left for NMSBoxes
                x_min = cx - w_box / 2.0
                y_min = cy - h_box / 2.0
                boxes.append([int(x_min), int(y_min), int(w_box), int(h_box)])

            # Non-Maximum Suppression (NMS)
            indices = cv2.dnn.NMSBoxes(
                boxes,
                list(map(float, filtered_confidences)),
                score_threshold=conf_threshold,
                nms_threshold=nms_threshold
            )
            
            targets: List[Tuple[float, float]] = []
            
            # Coordinate scaling factors (grid 416x416 -> native canvas size)
            # Use the actual input frame size so arbitrary aerial images work
            # without requiring resizing on disk. h_orig, w_orig were captured
            # earlier from frame.shape.
            x_factor = float(w_orig) / 416.0
            y_factor = float(h_orig) / 416.0
            
            if len(indices) > 0:
                # Use high-precision float centers directly from filtered_preds
                for idx in indices:
                    if isinstance(idx, (list, np.ndarray)):
                        i = int(idx[0])
                    else:
                        i = int(idx)

                    # Defensive bounds check
                    if i < 0 or i >= len(filtered_preds):
                        continue

                    pred = filtered_preds[i]
                    # pred layout: [cx, cy, w, h, ...class scores]
                    try:
                        cx_416 = float(pred[0])
                        cy_416 = float(pred[1])
                    except Exception:
                        # Skip malformed prediction rows
                        continue

                    # Map 416-grid float centers directly to native 600x600 canvas
                    x_center = cx_416 * x_factor
                    y_center = cy_416 * y_factor

                    targets.append((float(x_center), float(y_center)))
                    
        except Exception as e:
            print(f"[YOLOVisionEngine] Runtime Exception during inference execution: {e}")
            return []

        # Profiler end & telemetry update
        end_time = time.perf_counter()
        latency_ms = (end_time - start_time) * 1000.0
        fps = 1.0 / (end_time - start_time) if (end_time - start_time) > 0.0 else 0.0
        
        print(f"[Vision Loop] Inference Latency (ms): {latency_ms:.2f} | Processing Framerate (FPS): {fps:.2f}")
        
        return targets

def detect_targets(image_path: str) -> List[Tuple[float, float]]:
    """
    Deprecated: Backward compatible function. Loads image from disk and 
    runs YOLOVisionEngine detection.
    """
    try:
        img = cv2.imread(image_path)
        if img is None:
            return []
        engine = YOLOVisionEngine()
        return engine.detect_targets(img)
    except Exception as e:
        print(f"[YOLOVisionEngine] Deprecated wrapper exception: {e}")
        return []

if __name__ == "__main__":
    import os
    # Local quick test
    IMAGE_PATH = "map_cache/map_18.4575_73.8508_18.png"
    if os.path.exists(IMAGE_PATH):
        img = cv2.imread(IMAGE_PATH)
        engine = YOLOVisionEngine("best.onnx")
        found = engine.detect_targets(img)
        print(f"Targets detected: {found}")
    else:
        print(f"Test image not found at {IMAGE_PATH}")