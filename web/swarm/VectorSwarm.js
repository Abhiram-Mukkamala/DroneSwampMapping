/**
 * VectorSwarm — faithful numerical port of perfect_swarm.py's VectorSwarm.
 *
 * This is the Artificial Potential Field (APF) engine: attraction toward
 * target + repulsion between drones + repulsion from obstacles. Nothing
 * else — no A*, no DecisionEngine, no named formation protocols.
 *
 * COORDINATE CONVENTION:
 *   Internally uses the SAME convention as perfect_swarm.py:
 *     axis 0 = horizontal (Python x)
 *     axis 1 = horizontal (Python y)
 *     axis 2 = up          (Python z)
 *   Obstacle avoidance operates on axes [0,1] only.
 *   The integration layer in index.js handles mapping to/from Three.js (Y-up).
 *
 * STEP SIZE NOTE:
 *   step_size=0.18 is a tuning parameter, NOT a real-time dt. All force
 *   constants (150, 800), attraction gain (0.15), momentum coefficients
 *   (0.85/0.15), and the speed clamp (3.5) were balanced together with
 *   this step_size. Changing it would alter convergence, stability, and
 *   oscillation behavior. It stays fixed at 0.18 regardless of render
 *   framerate or the simulation loop's fixed dt.
 *
 * Every magic number below matches perfect_swarm.py exactly.
 */

export class Obstacle {
  /**
   * @param {number[]} pos — [x, y, z] in Python coordinate convention
   * @param {number} radius
   * @param {number} [height=30.0]
   */
  constructor(pos, radius, height = 30.0) {
    this.pos = [...pos];
    this.radius = radius;
    this.height = height;
  }
}

export class VectorSwarm {
  /**
   * @param {number[][]} starts  — array of [x, y, z] start positions
   * @param {number[][]} targets — array of [x, y, z] target positions
   * @param {object} [opts]
   * @param {function} [opts.random] — custom RNG returning [0,1), default Math.random
   */
  constructor(starts, targets, opts = {}) {
    this.n = starts.length;
    this.pos = starts.map(s => [s[0], s[1], s[2]]);
    this.targets = targets.map(t => [t[0], t[1], t[2]]);
    this.vel = Array.from({ length: this.n }, () => [0, 0, 0]);
    this.history = [this.pos.map(p => [...p])];
    this._random = opts.random || Math.random;
  }

  /**
   * Run one APF physics tick. Matches perfect_swarm.py VectorSwarm.update() exactly.
   *
   * @param {Obstacle[]} obstacles
   * @param {number} [stepSize=0.18]
   */
  update(obstacles, stepSize = 0.18) {
    const n = this.n;
    const pos = this.pos;
    const vel = this.vel;
    const targets = this.targets;

    // ----------------------------------------------------------------
    // 1. Attractive force toward target: f_att = 0.15 * (target - pos)
    //    Python: f_att = np.where(dists > 0, 0.15 * dirs, 0)
    // ----------------------------------------------------------------
    const fAtt = new Array(n);
    const distToTarget = new Array(n);  // scalar distance per drone (for stuck check later)

    for (let i = 0; i < n; i++) {
      const dx = targets[i][0] - pos[i][0];
      const dy = targets[i][1] - pos[i][1];
      const dz = targets[i][2] - pos[i][2];
      const d = Math.sqrt(dx * dx + dy * dy + dz * dz);
      distToTarget[i] = d;
      if (d > 0) {
        fAtt[i] = [0.15 * dx, 0.15 * dy, 0.15 * dz];
      } else {
        fAtt[i] = [0, 0, 0];
      }
    }

    // ----------------------------------------------------------------
    // 2. Repulsive force from other drones (pairwise, 3D, range < 5.0)
    //    Python: 150.0 * (1/safe_d - 1/5.0) * (1/safe_d**2) * (diffs/safe_d)
    //    = 150 * (1/d - 0.2) * diff / d^3
    // ----------------------------------------------------------------
    const fRep = Array.from({ length: n }, () => [0, 0, 0]);

    for (let i = 0; i < n; i++) {
      for (let j = 0; j < n; j++) {
        if (i === j) continue;

        const dx = pos[i][0] - pos[j][0];
        const dy = pos[i][1] - pos[j][1];
        const dz = pos[i][2] - pos[j][2];
        const d = Math.sqrt(dx * dx + dy * dy + dz * dz);

        if (d > 0 && d < 5.0) {
          // 150 * (1/d - 1/5) * (1/d^2) * (diff/d) = 150 * (1/d - 0.2) * diff / d^3
          const invD = 1 / d;
          const factor = 150.0 * (invD - 0.2) * (invD * invD) * invD;
          fRep[i][0] += factor * dx;
          fRep[i][1] += factor * dy;
          fRep[i][2] += factor * dz;
        }
      }
    }

    // ----------------------------------------------------------------
    // 3. Repulsive force from obstacles — HORIZONTAL PLANE ONLY (axes 0,1)
    //    Python: 800.0 * (1/d_surf - 1/5.0) * (1/d_surf**2) * (diffs_2d/d_center)
    //    Note: normalized by d_center (distance to center), not d_surf — intentional.
    // ----------------------------------------------------------------
    for (const obs of obstacles) {
      for (let i = 0; i < n; i++) {
        const dx = pos[i][0] - obs.pos[0];
        const dy = pos[i][1] - obs.pos[1];
        const dCenter = Math.sqrt(dx * dx + dy * dy);

        // Guard: at obstacle center, direction is undefined — skip
        if (dCenter < 1e-10) continue;

        const dSurf = Math.max(0.1, dCenter - obs.radius);

        if (dSurf < 5.0) {
          const invDSurf = 1 / dSurf;
          const factor = 800.0 * (invDSurf - 0.2) * (invDSurf * invDSurf);
          // Direction: normalized by d_center (not d_surf)
          fRep[i][0] += factor * (dx / dCenter);
          fRep[i][1] += factor * (dy / dCenter);
          // axis 2 (up) is NOT affected by obstacle repulsion
        }
      }
    }

    // ----------------------------------------------------------------
    // 4. Combine and apply momentum
    //    Python: self.vel = (self.vel * 0.85) + (total_f * 0.15)
    // ----------------------------------------------------------------
    for (let i = 0; i < n; i++) {
      vel[i][0] = vel[i][0] * 0.85 + (fAtt[i][0] + fRep[i][0]) * 0.15;
      vel[i][1] = vel[i][1] * 0.85 + (fAtt[i][1] + fRep[i][1]) * 0.15;
      vel[i][2] = vel[i][2] * 0.85 + (fAtt[i][2] + fRep[i][2]) * 0.15;
    }

    // ----------------------------------------------------------------
    // 5. Stuck detection — if speed < 0.1 AND dist-to-target > 3.0,
    //    add random noise to axes 0,1 only (not axis 2)
    //
    //    Python generates noise for ALL drones (n*3 values from RNG),
    //    then only applies where stuck. We generate all values too to
    //    keep RNG advancement consistent.
    // ----------------------------------------------------------------
    const noise = new Array(n);
    for (let i = 0; i < n; i++) {
      noise[i] = [
        this._random() * 2 - 1,   // axis 0
        this._random() * 2 - 1,   // axis 1
        0,                         // axis 2 — always 0
      ];
      this._random();  // consume 3rd value to match Python's n*3 RNG pattern
    }

    for (let i = 0; i < n; i++) {
      const speed = Math.sqrt(vel[i][0] ** 2 + vel[i][1] ** 2 + vel[i][2] ** 2);
      if (speed < 0.1 && distToTarget[i] > 3.0) {
        vel[i][0] += noise[i][0];
        vel[i][1] += noise[i][1];
        // vel[i][2] not affected (noise[i][2] is 0)
      }
    }

    // ----------------------------------------------------------------
    // 6. Speed clamp — max speed 3.5
    //    Python: vel = where(speed > 3.5, (vel/speed)*3.5, vel)
    // ----------------------------------------------------------------
    for (let i = 0; i < n; i++) {
      const speed = Math.sqrt(vel[i][0] ** 2 + vel[i][1] ** 2 + vel[i][2] ** 2);
      if (speed > 3.5) {
        const scale = 3.5 / speed;
        vel[i][0] *= scale;
        vel[i][1] *= scale;
        vel[i][2] *= scale;
      }
    }

    // ----------------------------------------------------------------
    // 7. Integrate position: pos += vel * step_size
    // ----------------------------------------------------------------
    for (let i = 0; i < n; i++) {
      pos[i][0] += vel[i][0] * stepSize;
      pos[i][1] += vel[i][1] * stepSize;
      pos[i][2] += vel[i][2] * stepSize;
    }

    this.history.push(pos.map(p => [...p]));
  }
}

/**
 * Protocol Beta (Linear Sweep):
 * Linear axis interpolation mapping nDrones into an evenly spaced horizontal line.
 * @param {number} nDrones
 * @param {number[]} startPoint - [x, y]
 * @param {number[]} endPoint - [x, y]
 * @param {number} [altitude=20.0]
 * @returns {number[][]} array of [x, y, z] target positions
 */
export function generateProtocolBeta(nDrones, startPoint, endPoint, altitude = 20.0) {
  const targets = [];
  for (let i = 0; i < nDrones; i++) {
    const t = nDrones > 1 ? i / (nDrones - 1) : 0;
    const x = startPoint[0] + t * (endPoint[0] - startPoint[0]);
    const y = startPoint[1] + t * (endPoint[1] - startPoint[1]);
    targets.push([x, y, altitude]);
  }
  return targets;
}

/**
 * Protocol Gamma (Dynamic Encirclement):
 * Trigonometric distribution forming a 360° dynamic containment ring around target coordinates.
 * @param {number} nDrones
 * @param {number[]} center - [x, y]
 * @param {number} [radius=15.0]
 * @param {number} [altitude=20.0]
 * @returns {number[][]} array of [x, y, z] target positions
 */
export function generateProtocolGamma(nDrones, center, radius = 15.0, altitude = 20.0) {
  const targets = [];
  for (let i = 0; i < nDrones; i++) {
    const angle = (2 * Math.PI * i) / nDrones;
    const x = center[0] + radius * Math.cos(angle);
    const y = center[1] + radius * Math.sin(angle);
    targets.push([x, y, altitude]);
  }
  return targets;
}
