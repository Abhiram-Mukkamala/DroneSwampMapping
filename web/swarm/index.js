/**
 * Swarm Intelligence Module — integration layer.
 *
 * Bridges VectorSwarm (APF engine, Python coordinate convention) with
 * the Drone state objects and SimulationLoop (Three.js Y-up convention).
 *
 * Coordinate mapping (applied at the boundary, not inside VectorSwarm):
 *   Python axis 0 (x, horizontal)  →  Three.js X
 *   Python axis 1 (y, horizontal)  →  Three.js Z
 *   Python axis 2 (z, up)          →  Three.js Y
 *
 * The VectorSwarm manages its own internal pos/vel arrays and is the
 * authoritative source for drone positions while active. Each tick:
 *   1. VectorSwarm.update() runs APF physics with step_size=0.18
 *   2. Results are written back to Drone objects (with coord mapping)
 *   3. Drone._positionManagedExternally is set so Drone.update() skips
 *      its own kinematic integration (but still does heading/battery/status)
 */

import { VectorSwarm, Obstacle } from './VectorSwarm.js';

/** @type {VectorSwarm|null} */
let swarm = null;

/** @type {Obstacle[]} */
let obstacles = [];

/** @type {number[][]} Targets in Python coordinate convention */
let targetsPy = [];

/**
 * Initialize the swarm with starting positions, targets, and obstacles.
 * Call this after spawning drones (e.g., on reset).
 *
 * All inputs use Three.js coordinates (Y-up). Mapping to Python convention
 * is handled internally.
 *
 * @param {Array<{x:number, y:number, z:number}>} startPositions
 * @param {Array<{x:number, y:number, z:number}>} targetPositions
 * @param {Array<{position:{x:number,y:number,z:number}, radius:number, height?:number}>} obstacleList
 */
export function initSwarm(startPositions, targetPositions, obstacleList = []) {
  // Map Three.js (Y-up) → Python convention (axis 2 = up)
  const startsPy = startPositions.map(p => [p.x, p.z, p.y]);
  targetsPy = targetPositions.map(p => [p.x, p.z, p.y]);
  obstacles = obstacleList.map(o => new Obstacle(
    [o.position.x, o.position.z, o.position.y],
    o.radius,
    o.height || 30.0
  ));

  swarm = new VectorSwarm(startsPy, targetsPy);
}

/**
 * Per-tick update — called from SimulationLoop.onBeforeTick.
 * Runs one APF tick and writes results back to Drone objects.
 *
 * @param {import('../core/Drone.js').Drone[]} drones
 * @param {number} dt — the sim's fixed dt (unused; VectorSwarm uses step_size=0.18)
 */
export function updateSwarm(drones, dt) {
  if (!swarm || swarm.n !== drones.length) return;

  // Run one APF tick (step_size=0.18, fixed, not tied to dt)
  swarm.update(obstacles, 0.18);

  // Write VectorSwarm state back to Drone objects (Python → Three.js mapping)
  for (let i = 0; i < drones.length; i++) {
    const d = drones[i];

    // Position: Python [x, y, z] → Three.js {x, z, y}
    d.position.x = swarm.pos[i][0];
    d.position.z = swarm.pos[i][1];
    d.position.y = swarm.pos[i][2];

    // Velocity: same mapping (for heading calculation & display)
    d.velocity.x = swarm.vel[i][0];
    d.velocity.z = swarm.vel[i][1];
    d.velocity.y = swarm.vel[i][2];

    // Flag: skip Drone.update()'s own kinematic integration this tick
    d._positionManagedExternally = true;
  }
}

/**
 * Check if the swarm module is active.
 * @returns {boolean}
 */
export function isSwarmActive() {
  return swarm !== null;
}

/**
 * Reset / deactivate the swarm module.
 */
export function resetSwarm() {
  swarm = null;
  obstacles = [];
  targetsPy = [];
}
