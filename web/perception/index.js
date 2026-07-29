/**
 * Perception Module — Phase 3 Step 3
 *
 * Sends captured per-drone POV frames (320x240 JPEG) to the YOLOv8
 * inference backend at /detect, returns parsed detections, and streams
 * detections to the Pipeline Lead's WebSocket server at ws://localhost:8765.
 *
 * Detection contract (matches backend POST /detect response):
 *   { detections: [{ class, bbox: [x,y,w,h], confidence }],
 *     inference_time_ms, image_size }
 *
 * WebSocket payload contract (sent to ws://localhost:8765):
 *   {
 *     "type": "yolo_detections",
 *     "droneId": 1,
 *     "payload": [ { "class": "obstacle", "bbox": [10, 20, 50, 80], "confidence": 0.91 } ]
 *   }
 */

// ---- Configuration ----
const BACKEND_URL = 'http://localhost:8000';
const DETECT_ENDPOINT = `${BACKEND_URL}/detect`;
const HEALTH_ENDPOINT = `${BACKEND_URL}/health`;
const WS_URL = 'ws://localhost:8765';

/** Minimum ms between inference requests (tunable). */
export const INFERENCE_INTERVAL_MS = 800;

/** How often to poll /health when disconnected (ms). */
const HEALTH_POLL_MS = 3000;

/** WebSocket reconnect interval (ms). */
const WS_RECONNECT_MS = 5000;

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

// ---- WebSocket state ----
let _ws = null;
let _wsConnected = false;
let _wsReconnectTimer = null;

/**
 * Initialize auto-reconnecting WebSocket connection to Pipeline Lead server.
 */
function initWebSocket() {
  if (_ws && (_ws.readyState === WebSocket.CONNECTING || _ws.readyState === WebSocket.OPEN)) {
    return;
  }

  try {
    _ws = new WebSocket(WS_URL);

    _ws.onopen = () => {
      _wsConnected = true;
      console.log(`[Perception WS] Connected to ${WS_URL}`);
      if (_wsReconnectTimer) {
        clearTimeout(_wsReconnectTimer);
        _wsReconnectTimer = null;
      }
    };

    _ws.onmessage = (event) => {
      // Handle incoming messages from pipeline server if needed
    };

    _ws.onerror = (err) => {
      // Fail gracefully without crashing
      _wsConnected = false;
    };

    _ws.onclose = () => {
      _wsConnected = false;
      _ws = null;
      // Schedule graceful reconnect
      if (!_wsReconnectTimer) {
        _wsReconnectTimer = setTimeout(initWebSocket, WS_RECONNECT_MS);
      }
    };
  } catch (err) {
    _wsConnected = false;
    _ws = null;
    if (!_wsReconnectTimer) {
      _wsReconnectTimer = setTimeout(initWebSocket, WS_RECONNECT_MS);
    }
  }
}

/**
 * Stream detections to the Pipeline Lead's WebSocket server.
 * @param {number} droneId
 * @param {Array<object>} detections
 */
function sendWebSocketDetections(droneId, detections) {
  if (_ws && _ws.readyState === WebSocket.OPEN) {
    try {
      const message = {
        type: 'yolo_detections',
        droneId: droneId !== undefined && droneId !== null ? droneId : 1,
        payload: detections,
      };
      _ws.send(JSON.stringify(message));
    } catch (err) {
      console.warn('[Perception WS] Error sending detections:', err.message);
    }
  }
}

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
 * store results, and stream over WebSocket.
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
    // Determine active drone state
    const droneState = _getDroneState ? _getDroneState() : null;
    const droneId = droneState ? droneState.id : 1;

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

    // Forward detections payload over WebSocket to Pipeline Lead server
    sendWebSocketDetections(droneId, _lastDetections);

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
 * Start the throttled perception polling loop and WebSocket stream.
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

  // Connect to Pipeline Lead WebSocket server
  initWebSocket();

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
 * Stop the perception polling loop and close WebSocket.
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
  if (_wsReconnectTimer) {
    clearTimeout(_wsReconnectTimer);
    _wsReconnectTimer = null;
  }
  if (_ws) {
    _ws.close();
    _ws = null;
  }
  _wsConnected = false;
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
 * Get WebSocket connection status.
 * @returns {boolean}
 */
export function isWSConnected() {
  return _wsConnected;
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
