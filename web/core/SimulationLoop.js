/**
 * SimulationLoop — fixed-timestep physics loop, decoupled from render rate.
 *
 * Uses an accumulator pattern: call update(renderDelta) each animation frame,
 * and it internally ticks physics at a fixed 60Hz regardless of how fast or
 * slow the renderer runs.
 *
 * Single source of truth: getDroneStates() returns the authoritative state
 * array that every other module (renderer, UI, swarm AI) reads from.
 *
 * Hook point for future AI: set onBeforeTick to a function that receives
 * (drones, dt) and can modify drone velocities before integration.
 */

import { Drone } from './Drone.js';

const FIXED_DT = 1 / 60;           // 60Hz physics tick (seconds)
const MAX_SUBSTEPS = 10;            // safety cap: don't spiral of death

// Spawn config: central 100×100 region of the 500×500 arena
const SPAWN = {
  minX: 200, maxX: 300,
  minY: 10,  maxY: 30,
  minZ: 200, maxZ: 300,
};

// Random initial velocity range (m/s) for demo movement
const INIT_SPEED = { min: 2, max: 8 };

/**
 * Returns a random float in [min, max).
 */
function rand(min, max) {
  return min + Math.random() * (max - min);
}

export class SimulationLoop {
  constructor() {
    /** @type {Drone[]} */
    this.drones = [];

    this._idCounter = 0; // Monotonically increasing ID for underlying physics drones

    /** Accumulated time not yet consumed by physics ticks (seconds). */
    this._accumulator = 0;

    /** Is the simulation running? */
    this._running = false;

    /** Total physics ticks elapsed since last reset. */
    this.tickCount = 0;

    /**
     * Hook for swarm AI / external controllers.
     * Called once per physics tick, BEFORE drone.update(dt).
     * Signature: (drones: Drone[], dt: number) => void
     *
     * In Phase 1 this is null (drones just coast on their initial velocity).
     * In Phase 2+ the swarm module will set this to inject APF / formation logic.
     * @type {Function|null}
     */
    this.onBeforeTick = null;
  }

  // ---- Drone management ----

  /**
   * Add N drones with specified or random positions in the spawn region.
   * @param {number} count
   * @param {Array<{x:number, y:number, z:number}>} [startPositions]
   */
  addDrones(count, startPositions = null) {
    for (let i = 0; i < count; i++) {
      const pos = (startPositions && startPositions[i]) ? {
        x: startPositions[i].x,
        y: startPositions[i].y,
        z: startPositions[i].z,
      } : {
        x: rand(SPAWN.minX, SPAWN.maxX),
        y: rand(SPAWN.minY, SPAWN.maxY),
        z: rand(SPAWN.minZ, SPAWN.maxZ),
      };
      const drone = new Drone(this._idCounter++, {
        position: pos,
        velocity: {
          x: rand(-INIT_SPEED.max, INIT_SPEED.max),
          y: rand(-1, 1),
          z: rand(-INIT_SPEED.max, INIT_SPEED.max),
        },
      });
      this.drones.push(drone);
    }
  }

  /**
   * Remove a drone by id.
   * @param {number} id
   */
  removeDrone(id) {
    this.drones = this.drones.filter(d => d.id !== id);
  }

  /**
   * Set the total drone count. Adds or removes drones to match.
   * @param {number} n
   */
  setDroneCount(n) {
    if (n > this.drones.length) {
      this.addDrones(n - this.drones.length);
    } else if (n < this.drones.length) {
      this.drones.length = n;
    }
  }

  // ---- Simulation control ----

  start() {
    this._running = true;
  }

  stop() {
    this._running = false;
  }

  get running() {
    return this._running;
  }

  /**
   * Reset: clear all drones, respawn the given count, reset tick counter.
   * @param {number} [droneCount=10]
   * @param {Array<{x:number, y:number, z:number}>} [startPositions]
   */
  reset(droneCount = 10, startPositions = null) {
    this.drones = [];
    this._accumulator = 0;
    this.tickCount = 0;
    this._idCounter = 0;
    this.addDrones(droneCount, startPositions);
  }

  // ---- Per-frame update (called from requestAnimationFrame) ----

  /**
   * Feed in the wall-clock delta from the render loop. Internally runs
   * as many fixed-timestep physics ticks as needed to stay in sync.
   *
   * @param {number} renderDelta — seconds since last render frame
   */
  update(renderDelta) {
    if (!this._running) return;

    // Clamp incoming delta to avoid spiral-of-death if tab was backgrounded
    const clamped = Math.min(renderDelta, FIXED_DT * MAX_SUBSTEPS);
    this._accumulator += clamped;

    let steps = 0;
    while (this._accumulator >= FIXED_DT && steps < MAX_SUBSTEPS) {
      this._tick(FIXED_DT);
      this._accumulator -= FIXED_DT;
      steps++;
    }
  }

  /**
   * Run a single physics tick at the fixed timestep.
   * @param {number} dt
   * @private
   */
  _tick(dt) {
    // Let external controllers (swarm AI) modify velocities first
    if (this.onBeforeTick) {
      this.onBeforeTick(this.drones, dt);
    }

    // Integrate all drones
    for (const drone of this.drones) {
      drone.update(dt);
    }

    this.tickCount++;
  }

  // ---- State access (single source of truth) ----

  /**
   * Returns an array of plain-object state snapshots for every drone.
   * This is what the renderer, UI, and future swarm modules read.
   * @returns {Array<object>}
   */
  getDroneStates() {
    return this.drones.map(d => d.getState());
  }

  /**
   * Direct access to the drone instances (for modules that need to
   * write velocities, e.g. swarm AI via onBeforeTick).
   * @returns {Drone[]}
   */
  getDrones() {
    return this.drones;
  }
}
