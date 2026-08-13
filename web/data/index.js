/**
 * Terrain & Hazard Data Module
 *
 * Integrates procedural heightmap elevation and hazard grid generation.
 */

import { getHeightAt, setTerrainSeed, MAX_TERRAIN_HEIGHT } from './Heightmap.js';

export { getHeightAt, setTerrainSeed, MAX_TERRAIN_HEIGHT };

/**
 * Generates and returns terrain hazard grid data matching TerrainRenderer expectations.
 * @param {number} [cellSize=10] — grid cell size in meters
 * @param {number} [threshold=4.0] — elevation height threshold in meters to mark hazard cell
 * @returns {{ grid: number[][], cellSize: number }}
 */
export function getTerrainData(cellSize = 10, threshold = 4.0) {
  const size = 500;
  const cols = Math.floor(size / cellSize);
  const rows = Math.floor(size / cellSize);
  const grid = [];

  for (let r = 0; r < rows; r++) {
    const row = [];
    for (let c = 0; c < cols; c++) {
      const worldX = (c + 0.5) * cellSize;
      const worldZ = (r + 0.5) * cellSize;
      const height = getHeightAt(worldX, worldZ);
      row.push(height >= threshold ? 1 : 0);
    }
    grid.push(row);
  }

  return { grid, cellSize };
}

/**
 * @returns {Array<object>} — obstacles [{position, radius, height, shape}]
 */
export function getObstacles() {
  return [];
}
