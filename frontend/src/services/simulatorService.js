/**
 * simulatorService.js — Real WebSocket Simulator Service
 *
 * Provides a standalone WebSocket client for connecting to the PyBullet
 * backend at ws://localhost:8765.  Parses TELEMETRY_UPDATE messages and
 * delivers canonical DroneState arrays to subscribers.
 *
 * NOTE: SimulationContext.jsx already manages a shared WebSocket
 * connection used by the React component tree.  This service exists as
 * an importable, framework-agnostic alternative for non-React consumers
 * (tests, CLI tools, future modules).
 */

const WS_URL = 'ws://localhost:8765';

/** @type {WebSocket | null} */
let _socket = null;

/** @type {Set<(states: import('../../../shared/schemas/droneState').DroneState[]) => void>} */
const _telemetryListeners = new Set();

/** @type {Set<(data: any) => void>} */
const _detectionListeners = new Set();

/** @type {Set<(data: any) => void>} */
const _mapListeners = new Set();

/** @type {Set<(msg: any) => void>} */
const _rawListeners = new Set();

// ---------------------------------------------------------------------------
// Connection lifecycle
// ---------------------------------------------------------------------------

/**
 * Opens a WebSocket connection to the simulator backend.
 * Automatically reconnects on close (3 s delay).
 *
 * @returns {boolean} true if a new connection was initiated
 */
export const connect = () => {
  if (_socket && _socket.readyState <= WebSocket.OPEN) {
    return false; // already connected / connecting
  }

  _socket = new WebSocket(WS_URL);

  _socket.onopen = () => {
    console.log('[simulatorService] Connected to backend');
  };

  _socket.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);

      // Forward to raw listeners
      _rawListeners.forEach((cb) => cb(data));

      if (data.type === 'TELEMETRY_UPDATE' && data.payload?.droneStates) {
        _telemetryListeners.forEach((cb) => cb(data.payload.droneStates));
      } else if (data.type === 'DETECTION_UPDATE') {
        _detectionListeners.forEach((cb) => cb(data.payload));
      } else if (data.type === 'MAP_UPDATE') {
        _mapListeners.forEach((cb) => cb(data.payload));
      }
    } catch (err) {
      console.error('[simulatorService] Failed to parse message:', err);
    }
  };

  _socket.onclose = () => {
    console.log('[simulatorService] Disconnected — reconnecting in 3 s');
    _socket = null;
    setTimeout(connect, 3000);
  };

  _socket.onerror = (err) => {
    console.error('[simulatorService] WebSocket error:', err);
  };

  return true;
};

/**
 * Closes the WebSocket connection.  Does NOT auto-reconnect.
 */
export const disconnect = () => {
  if (_socket) {
    // Remove onclose handler to prevent auto-reconnect
    _socket.onclose = null;
    _socket.close();
    _socket = null;
    console.log('[simulatorService] Disconnected (manual)');
  }
};

// ---------------------------------------------------------------------------
// Commands
// ---------------------------------------------------------------------------

/**
 * Sends a command to the simulation backend.
 *
 * @param {string} command  - Message type (e.g. "START_SIMULATION")
 * @param {object} payload  - Optional payload data
 */
export const sendCommand = (command, payload = {}) => {
  if (_socket && _socket.readyState === WebSocket.OPEN) {
    _socket.send(JSON.stringify({ type: command, payload, timestamp: Date.now() }));
  } else {
    console.warn(`[simulatorService] Cannot send "${command}" — not connected`);
  }
};

// ---------------------------------------------------------------------------
// Subscriptions
// ---------------------------------------------------------------------------

/**
 * Subscribe to parsed TELEMETRY_UPDATE drone-state arrays.
 *
 * @param {(states: import('../../../shared/schemas/droneState').DroneState[]) => void} callback
 * @returns {() => void} unsubscribe function
 */
export const receiveTelemetry = (callback) => {
  _telemetryListeners.add(callback);
  return () => _telemetryListeners.delete(callback);
};

/**
 * Subscribe to DETECTION_UPDATE payloads (future — currently a stub).
 *
 * @param {(data: any) => void} callback
 * @returns {() => void} unsubscribe function
 */
export const receiveDetections = (callback) => {
  _detectionListeners.add(callback);
  return () => _detectionListeners.delete(callback);
};

/**
 * Subscribe to MAP_UPDATE payloads (future — currently a stub).
 *
 * @param {(data: any) => void} callback
 * @returns {() => void} unsubscribe function
 */
export const receiveMap = (callback) => {
  _mapListeners.add(callback);
  return () => _mapListeners.delete(callback);
};

/**
 * Subscribe to ALL raw parsed messages from the backend.
 *
 * @param {(msg: any) => void} callback
 * @returns {() => void} unsubscribe function
 */
export const onMessage = (callback) => {
  _rawListeners.add(callback);
  return () => _rawListeners.delete(callback);
};
