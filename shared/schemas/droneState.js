/**
 * droneState.js — Canonical Drone State Schema
 *
 * This is the single source of truth for the shape of a drone's
 * telemetry state as transmitted over WebSocket from the PyBullet
 * backend and consumed by every frontend component.
 *
 * The matching Python definition lives at backend/schemas/drone_state.py.
 * Both MUST stay in sync — any field added/removed/renamed here must be
 * mirrored there.
 */

/**
 * Valid drone status values.
 * @readonly
 * @enum {string}
 */
export const DRONE_STATUS = Object.freeze({
  ACTIVE: 'ACTIVE',
  IDLE: 'IDLE',
  STUCK: 'STUCK',
  OFFLINE: 'OFFLINE',
});

/**
 * @typedef {Object} Vec3
 * @property {number} x
 * @property {number} y
 * @property {number} z
 */

/**
 * @typedef {Object} DroneState
 * @property {string}  id        - Unique drone identifier (stringified index in sim)
 * @property {Vec3}    position  - World-space position in metres
 * @property {Vec3}    velocity  - Linear velocity in m/s (x, y, z components)
 * @property {number}  heading   - Yaw heading in degrees [0, 360)
 * @property {number}  battery   - Charge level, 0.0 (dead) to 1.0 (full)
 * @property {'ACTIVE'|'IDLE'|'STUCK'|'OFFLINE'} status
 */

/**
 * Validates that an object conforms to the DroneState schema.
 *
 * @param {*} obj - The object to validate.
 * @returns {{ valid: boolean, errors: string[] }}
 */
export function validateDroneState(obj) {
  const errors = [];

  if (typeof obj !== 'object' || obj === null) {
    return { valid: false, errors: ['DroneState must be a non-null object'] };
  }

  // id
  if (typeof obj.id !== 'string') {
    errors.push(`id must be a string, got ${typeof obj.id}`);
  }

  // position
  if (!_isVec3(obj.position)) {
    errors.push('position must be { x: number, y: number, z: number }');
  }

  // velocity
  if (!_isVec3(obj.velocity)) {
    errors.push('velocity must be { x: number, y: number, z: number }');
  }

  // heading
  if (typeof obj.heading !== 'number') {
    errors.push(`heading must be a number, got ${typeof obj.heading}`);
  }

  // battery
  if (typeof obj.battery !== 'number' || obj.battery < 0 || obj.battery > 1) {
    errors.push('battery must be a number in [0.0, 1.0]');
  }

  // status
  if (!Object.values(DRONE_STATUS).includes(obj.status)) {
    errors.push(`status must be one of ${Object.values(DRONE_STATUS).join(', ')}, got "${obj.status}"`);
  }

  return { valid: errors.length === 0, errors };
}

/**
 * Creates a default/empty DroneState.
 *
 * @param {string} id
 * @returns {DroneState}
 */
export function createDefaultDroneState(id) {
  return {
    id: String(id),
    position: { x: 0, y: 0, z: 0 },
    velocity: { x: 0, y: 0, z: 0 },
    heading: 0,
    battery: 1.0,
    status: DRONE_STATUS.IDLE,
  };
}

/** @param {*} v @returns {boolean} */
function _isVec3(v) {
  return (
    v !== null &&
    typeof v === 'object' &&
    typeof v.x === 'number' &&
    typeof v.y === 'number' &&
    typeof v.z === 'number'
  );
}
