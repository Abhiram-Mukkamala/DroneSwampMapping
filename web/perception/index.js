/**
 * Perception Module — Phase 3+
 *
 * Will contain: YOLOv8 ONNX Runtime Web inference,
 * bounding-box → APF obstacle conversion pipeline.
 *
 * Receives the output of render/DroneCamera.js getDronePOV() — a canvas
 * or render-target texture representing a drone's simulated camera view.
 *
 * @param {HTMLCanvasElement|null} videoFrame — from getDronePOV(droneId)
 * @returns {Array<object>} — detected objects [{class, confidence, bbox}]
 */
export function processFrame(videoFrame) {
  return []; // no-op — no detections in Phase 1
}
