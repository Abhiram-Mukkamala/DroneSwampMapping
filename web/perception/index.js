/**
 * Perception Module — Phase 3 Step 3
 *
 * Sends captured per-drone POV frames (320x240 JPEG) to the YOLOv8
 * inference backend at /detect, returns parsed detections.
 *
 * Detection contract (matches backend POST /detect response):
 *   { detections: [{ class, bbox: [x,y,w,h], confidence }],
 *     inference_time_ms, image_size }
 */

// ---- Configuration ----
const BACKEND_URL = 'http://localhost:8000';
const DETECT_ENDPOINT = `${BACKEND_URL}/detect`;
const HEALTH_ENDPOINT = `${BACKEND_URL}/health`;

/** Minimum ms between inference requests (tunable). */
export const INFERENCE_INTERVAL_MS = 800;

/** How often to poll /health when disconnected (ms). */
const HEALTH_POLL_MS = 3000;

// ---- Internal state ----
let _inflight = false;
let _connected = false;
let _lastDetections = [];
let _lastInferenceMs = 0;
let _intervalId = null;
let _healthIntervalId = null;
let _droneCamera = null;
let _scene = null;
let _getDroneState = null; // () => droneState for active drone

/**
 * Check if the perception backend is reachable.
 * @returns {Promise<boolean>}
 */
async function checkHealth() {
  try {
    const resp = await fetch(HEALTH_ENDPOINT, {
      method: 'GET',
      signal: AbortSignal.timeout(2000),
    });
    const wasConnected = _connected;
    _connected = resp.ok;
    if (_connected && !wasConnected) {
      console.log('[Perception] Backend connected');
    }
    return _connected;
  } catch {
    if (_connected) {
      console.warn('[Perception] Backend disconnected');
    }
    _connected = false;
    return false;
  }
}

/**
 * Send a single frame to the backend for inference.
 * @param {Blob} frameBlob — JPEG blob from DroneCamera.getFrameBlob()
 * @returns {Promise<Array<object>>} — detections array
 */
async function sendFrame(frameBlob) {
  const form = new FormData();
  form.append('file', frameBlob, 'frame.jpg');

  const resp = await fetch(DETECT_ENDPOINT, {
    method: 'POST',
    body: form,
    signal: AbortSignal.timeout(5000),
  });

  if (!resp.ok) {
    throw new Error(`Backend returned ${resp.status}`);
  }

  return resp.json();
}

/**
 * Process a single frame: capture from DroneCamera, send to backend,
 * store results. Called by the polling interval.
 *
 * If a request is already in flight, this call is a no-op (skip, don't queue).
 * If the backend is unreachable, returns empty detections without crashing.
 *
 * @param {Blob|null} frameBlob — optional pre-captured blob; if null, uses _droneCamera
 * @returns {Promise<Array<object>>} — detections array
 */
export async function processFrame(frameBlob = null) {
  if (_inflight) return _lastDetections;

  _inflight = true;
  try {
    // If no blob passed, capture from DroneCamera
    if (!frameBlob && _droneCamera) {
      frameBlob = await _droneCamera.getFrameBlob();
    }
    if (!frameBlob) {
      return _lastDetections;
    }

    const data = await sendFrame(frameBlob);
    _lastDetections = data.detections || [];
    _lastInferenceMs = data.inference_time_ms || 0;

    if (!_connected) {
      _connected = true;
      console.log('[Perception] Backend connected');
    }

    return _lastDetections;
  } catch (err) {
    if (_connected) {
      console.warn('[Perception] Inference request failed:', err.message);
      _connected = false;
    }
    return [];
  } finally {
    _inflight = false;
  }
}

/**
 * Start the throttled perception polling loop.
 * @param {object} droneCamera — DroneCamera instance
 * @param {THREE.Scene} scene
 * @param {function} getDroneState — returns current active drone state
 */
export function startPerceptionLoop(droneCamera, scene, getDroneState) {
  _droneCamera = droneCamera;
  _scene = scene;
  _getDroneState = getDroneState;

  // Initial health check
  checkHealth();

  // Periodic health check (catches reconnection after Docker restart)
  if (_healthIntervalId) clearInterval(_healthIntervalId);
  _healthIntervalId = setInterval(checkHealth, HEALTH_POLL_MS);

  // Inference polling
  if (_intervalId) clearInterval(_intervalId);
  _intervalId = setInterval(async () => {
    if (!_connected) return; // don't spam if backend is down
    await processFrame();
  }, INFERENCE_INTERVAL_MS);

  console.log(`[Perception] Polling started (interval: ${INFERENCE_INTERVAL_MS}ms)`);
}

/**
 * Stop the perception polling loop.
 */
export function stopPerceptionLoop() {
  if (_intervalId) {
    clearInterval(_intervalId);
    _intervalId = null;
  }
  if (_healthIntervalId) {
    clearInterval(_healthIntervalId);
    _healthIntervalId = null;
  }
  console.log('[Perception] Polling stopped');
}

/**
 * Get current connection status.
 * @returns {boolean}
 */
export function isConnected() {
  return _connected;
}

/**
 * Get the most recent detections array.
 * @returns {Array<object>}
 */
export function getLastDetections() {
  return _lastDetections;
}

/**
 * Get the most recent inference round-trip time (ms).
 * @returns {number}
 */
export function getLastInferenceMs() {
  return _lastInferenceMs;
}
