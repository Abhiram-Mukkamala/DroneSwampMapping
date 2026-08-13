/**
 * Heightmap — Procedural terrain elevation generator.
 *
 * Generates smooth 2D procedural elevation across the 500x500m arena
 * using multi-octave Perlin noise.
 * Range: 0.0m to 8.0m elevation.
 *
 * Exposes getHeightAt(x, z) query function for renderers and physics layers.
 */

// Standard 2D Perlin Noise implementation
class PerlinNoise {
  constructor(seed = 42) {
    this.p = new Uint8Array(512);
    const perm = new Uint8Array(256);
    for (let i = 0; i < 256; i++) perm[i] = i;

    // Linear Congruential Generator for deterministic perm shuffle
    let s = seed;
    for (let i = 255; i > 0; i--) {
      s = (s * 1664525 + 1013904223) % 4294967296;
      const j = Math.floor((s / 4294967296) * (i + 1));
      const tmp = perm[i];
      perm[i] = perm[j];
      perm[j] = tmp;
    }
    for (let i = 0; i < 512; i++) {
      this.p[i] = perm[i & 255];
    }
  }

  fade(t) {
    return t * t * t * (t * (t * 6 - 15) + 10);
  }

  lerp(t, a, b) {
    return a + t * (b - a);
  }

  grad(hash, x, z) {
    const h = hash & 7;
    const u = h < 4 ? x : z;
    const v = h < 4 ? z : x;
    return ((h & 1) ? -u : u) + ((h & 2) ? -2.0 * v : 2.0 * v);
  }

  noise(x, z) {
    const X = Math.floor(x) & 255;
    const Z = Math.floor(z) & 255;
    const xf = x - Math.floor(x);
    const zf = z - Math.floor(z);
    const u = this.fade(xf);
    const v = this.fade(zf);

    const aa = this.p[this.p[X] + Z];
    const ab = this.p[this.p[X] + Z + 1];
    const ba = this.p[this.p[X + 1] + Z];
    const bb = this.p[this.p[X + 1] + Z + 1];

    const x1 = this.lerp(u, this.grad(aa, xf, zf), this.grad(ba, xf - 1, zf));
    const x2 = this.lerp(u, this.grad(ab, xf, zf - 1), this.grad(bb, xf - 1, zf - 1));
    return this.lerp(v, x1, x2);
  }
}

let currentSeed = 42;
let currentHeightScale = 1.0;
let perlin = new PerlinNoise(42);

/** Max base elevation height in meters (hills, modest terrain). */
export const MAX_TERRAIN_HEIGHT = 8.0;

/**
 * Configure active terrain heightmap seed and elevation scale multiplier.
 * @param {number} seed
 * @param {number} [heightScale=1.0]
 */
export function setTerrainSeed(seed, heightScale = 1.0) {
  currentSeed = seed;
  currentHeightScale = heightScale;
  perlin = new PerlinNoise(seed);
}

/**
 * Returns ground elevation (height in meters, Y >= 0) at world coordinates (x, z).
 * @param {number} x — world X coordinate [0..500]
 * @param {number} z — world Z coordinate [0..500]
 * @returns {number} ground elevation in meters [0.0..8.0]
 */
export function getHeightAt(x, z) {
  const cx = Math.max(0, Math.min(500, x));
  const cz = Math.max(0, Math.min(500, z));

  // Multi-octave Fractional Brownian Motion (FBM)
  const scale1 = 0.008;
  const scale2 = 0.022;
  const scale3 = 0.055;

  const n1 = perlin.noise(cx * scale1, cz * scale1);
  const n2 = perlin.noise(cx * scale2, cz * scale2) * 0.5;
  const n3 = perlin.noise(cx * scale3, cz * scale3) * 0.25;

  const raw = (n1 + n2 + n3 + 1.2) / 2.4;
  const clamped = Math.max(0, Math.min(1, raw));

  const elevation = clamped * MAX_TERRAIN_HEIGHT * currentHeightScale;
  return parseFloat(elevation.toFixed(3));
}
