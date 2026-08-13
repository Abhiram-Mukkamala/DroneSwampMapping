/**
 * Scenarios Data Module — Preset sandbox scenario configurations.
 *
 * Each scenario defines:
 *   - id: string
 *   - name: string
 *   - description: string
 *   - droneCount: number
 *   - seed: number (heightmap noise seed)
 *   - heightScale: number (elevation scaling multiplier, e.g. 0.3 to 1.0)
 *   - hazardRegions: array of [{ minX, maxX, minZ, maxZ }]
 *   - getStarts: (count) => Array<{x, y, z}>
 *   - getTargets: (count) => Array<{x, y, z}>
 */

export const SCENARIOS = [
  {
    id: 'open_field',
    name: 'Open Field',
    description: 'Flat-ish terrain with minimal obstacles. High-speed formation flight baseline.',
    droneCount: 10,
    seed: 12,
    heightScale: 0.25,
    hazardRegions: [
      { minX: 230, maxX: 270, minZ: 230, maxZ: 270 },
    ],
    getStarts(count) {
      const starts = [];
      const cols = 5;
      for (let i = 0; i < count; i++) {
        const r = Math.floor(i / cols);
        const c = i % cols;
        starts.push({ x: 60 + c * 15, y: 20, z: 60 + r * 15 });
      }
      return starts;
    },
    getTargets(count) {
      const targets = [];
      const cols = 5;
      for (let i = 0; i < count; i++) {
        const r = Math.floor(i / cols);
        const c = i % cols;
        targets.push({ x: 400 + c * 15, y: 20, z: 400 + r * 15 });
      }
      return targets;
    },
  },
  {
    id: 'dense_obstacles',
    name: 'Dense Obstacle Field',
    description: 'Heavy hazard grid with 5 obstacle structures. Tests multi-body APF avoidance.',
    droneCount: 12,
    seed: 101,
    heightScale: 0.6,
    hazardRegions: [
      { minX: 120, maxX: 160, minZ: 200, maxZ: 240 },
      { minX: 330, maxX: 370, minZ: 280, maxZ: 320 },
      { minX: 230, maxX: 270, minZ: 100, maxZ: 140 },
      { minX: 350, maxX: 390, minZ: 120, maxZ: 160 },
      { minX: 180, maxX: 220, minZ: 330, maxZ: 370 },
    ],
    getStarts(count) {
      const starts = [];
      for (let i = 0; i < count; i++) {
        starts.push({ x: 50, y: 20, z: 80 + i * 28 });
      }
      return starts;
    },
    getTargets(count) {
      const targets = [];
      for (let i = 0; i < count; i++) {
        targets.push({ x: 450, y: 20, z: 80 + i * 28 });
      }
      return targets;
    },
  },
  {
    id: 'narrow_corridor',
    name: 'Narrow Corridor',
    description: 'Parallel hazard walls force drones through a tight 40m choke point.',
    droneCount: 10,
    seed: 303,
    heightScale: 0.4,
    hazardRegions: [
      { minX: 210, maxX: 270, minZ: 0, maxZ: 230 },
      { minX: 210, maxX: 270, minZ: 270, maxZ: 500 },
    ],
    getStarts(count) {
      const starts = [];
      for (let i = 0; i < count; i++) {
        starts.push({ x: 60, y: 20, z: 100 + i * 32 });
      }
      return starts;
    },
    getTargets(count) {
      const targets = [];
      const cols = 4;
      for (let i = 0; i < count; i++) {
        const r = Math.floor(i / cols);
        const c = i % cols;
        targets.push({ x: 420 + c * 15, y: 20, z: 220 + r * 15 });
      }
      return targets;
    },
  },
  {
    id: 'steep_terrain',
    name: 'Steep Terrain',
    description: 'Exaggerated 0–8m elevation profile with 360° tactical encirclement targets.',
    droneCount: 15,
    seed: 777,
    heightScale: 1.0,
    hazardRegions: [
      { minX: 150, maxX: 190, minZ: 150, maxZ: 190 },
      { minX: 310, maxX: 350, minZ: 310, maxZ: 350 },
    ],
    getStarts(count) {
      const starts = [];
      for (let i = 0; i < count; i++) {
        const angle = (i / count) * Math.PI * 2;
        starts.push({
          x: 100 + Math.cos(angle) * 30,
          y: 25,
          z: 100 + Math.sin(angle) * 30,
        });
      }
      return starts;
    },
    getTargets(count) {
      const targets = [];
      const center = { x: 350, z: 350 };
      const radius = 65;
      for (let i = 0; i < count; i++) {
        const angle = (i / count) * Math.PI * 2;
        targets.push({
          x: center.x + Math.cos(angle) * radius,
          y: 25,
          z: center.z + Math.sin(angle) * radius,
        });
      }
      return targets;
    },
  },
  {
    id: 'search_rescue',
    name: 'Search & Rescue Sweep',
    description: 'Protocol Beta sweep formation traversing obstacles in a synchronized line.',
    droneCount: 12,
    seed: 505,
    heightScale: 0.5,
    hazardRegions: [
      { minX: 180, maxX: 210, minZ: 120, maxZ: 180 },
      { minX: 280, maxX: 310, minZ: 300, maxZ: 360 },
    ],
    getStarts(count) {
      const starts = [];
      for (let i = 0; i < count; i++) {
        starts.push({ x: 50 + (i % 3) * 20, y: 20, z: 80 + i * 28 });
      }
      return starts;
    },
    getTargets(count) {
      const targets = [];
      const stepZ = 380 / (count - 1);
      for (let i = 0; i < count; i++) {
        targets.push({ x: 440, y: 20, z: 60 + i * stepZ });
      }
      return targets;
    },
  },
];

/**
 * Get scenario definition by ID.
 * @param {string} id
 * @returns {object}
 */
export function getScenario(id) {
  return SCENARIOS.find(s => s.id === id) || SCENARIOS[0];
}
