/**
 * Drone — the core state object for a single drone.
 *
 * Every module in the system (swarm AI, perception, renderer) reads and
 * writes to instances of this class. The state shape is the contract:
 *
 *   { id, position: {x,y,z}, velocity: {x,y,z}, heading, battery, status }
 *
 * This class handles only kinematic integration and boundary enforcement.
 * Movement decisions (what velocity to set) are NOT made here — the swarm
 * module (or any other controller) sets velocity externally, and update()
 * just integrates it.
 */

// World bounds (meters). Y is altitude (Three.js Y-up convention).
const WORLD = {
  minX: 0, maxX: 500,
  minY: 0.5, maxY: 100,   // min altitude 0.5m (ground clearance)
  minZ: 0, maxZ: 500,
};

// Battery drain rate: fraction per second of active flight.
// At 0.001/s a drone lasts ~16.7 minutes before hitting 0.
const BATTERY_DRAIN_RATE = 0.001;

export class Drone {
  /**
   * @param {number} id   — unique drone identifier
   * @param {object} [opts] — optional overrides
   * @param {object} [opts.position]  — { x, y, z } spawn position
   * @param {object} [opts.velocity]  — { x, y, z } initial velocity
   * @param {number} [opts.battery]   — initial battery (0–1), default 1.0
   */
  constructor(id, opts = {}) {
    this.id = id;

    this.position = {
      x: opts.position?.x ?? 250,
      y: opts.position?.y ?? 20,
      z: opts.position?.z ?? 250,
    };

    this.velocity = {
      x: opts.velocity?.x ?? 0,
      y: opts.velocity?.y ?? 0,
      z: opts.velocity?.z ?? 0,
    };

    this.heading = 0;          // radians, derived from XZ velocity
    this.battery = opts.battery ?? 1.0;
    this.status = 'idle';      // 'idle' | 'active' | 'low_battery' | 'dead'

    /**
     * When true, update() skips kinematic integration (pos += vel * dt)
     * because an external module (e.g., swarm AI) has already set the
     * position directly. Auto-resets to false after each update() call.
     * Heading, battery, and status logic still runs.
     */
    this._positionManagedExternally = false;
  }

  /**
   * Advance one physics tick.
   * @param {number} dt — fixed timestep in seconds (e.g. 1/60)
   */
  update(dt) {
    if (this.status === 'dead') return;

    // --- Kinematic integration (skip if swarm module set position directly) ---
    if (!this._positionManagedExternally) {
      this.position.x += this.velocity.x * dt;
      this.position.y += this.velocity.y * dt;
      this.position.z += this.velocity.z * dt;
    }
    this._positionManagedExternally = false;

    // --- Boundary clamping with velocity kill on collision ---
    if (this.position.x < WORLD.minX) {
      this.position.x = WORLD.minX;
      this.velocity.x = Math.abs(this.velocity.x);   // bounce inward
    } else if (this.position.x > WORLD.maxX) {
      this.position.x = WORLD.maxX;
      this.velocity.x = -Math.abs(this.velocity.x);
    }

    if (this.position.z < WORLD.minZ) {
      this.position.z = WORLD.minZ;
      this.velocity.z = Math.abs(this.velocity.z);
    } else if (this.position.z > WORLD.maxZ) {
      this.position.z = WORLD.maxZ;
      this.velocity.z = -Math.abs(this.velocity.z);
    }

    // Ground and ceiling
    if (this.position.y < WORLD.minY) {
      this.position.y = WORLD.minY;
      this.velocity.y = 0;    // no ground bounce, just stop falling
    } else if (this.position.y > WORLD.maxY) {
      this.position.y = WORLD.maxY;
      this.velocity.y = 0;
    }

    // --- Heading (derived from XZ velocity) ---
    const vx = this.velocity.x;
    const vz = this.velocity.z;
    if (Math.abs(vx) > 0.01 || Math.abs(vz) > 0.01) {
      this.heading = Math.atan2(vx, vz);
    }

    // --- Battery drain ---
    const speed = Math.sqrt(vx * vx + this.velocity.y * this.velocity.y + vz * vz);
    if (speed > 0.1) {
      this.battery -= BATTERY_DRAIN_RATE * dt;
      this.status = 'active';
    } else {
      this.status = 'idle';
    }

    if (this.battery <= 0.1 && this.battery > 0) {
      this.status = 'low_battery';
    }

    if (this.battery <= 0) {
      this.battery = 0;
      this.status = 'dead';
      this.velocity.x = 0;
      this.velocity.y = 0;
      this.velocity.z = 0;
    }
  }

  /**
   * Returns a plain-object snapshot of the current state.
   * This is what getDroneStates() exposes to every other module.
   */
  getState() {
    return {
      id: this.id,
      position: { ...this.position },
      velocity: { ...this.velocity },
      heading: this.heading,
      battery: this.battery,
      status: this.status,
    };
  }
}
