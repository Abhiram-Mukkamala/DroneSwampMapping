/**
 * TerrainRenderer — 3D visual renderer for terrain hazard grids & obstacles.
 *
 * Renders:
 *   1. Tinted, semi-transparent ground cell tiles matching occupied hazard grid cells
 *   2. Translucent 3D volumetric cylinder safety bubbles and ground rings for APF obstacles
 */

import { getHeightAt } from '../data/index.js';

export class TerrainRenderer {
  /**
   * @param {THREE.Scene} scene
   */
  constructor(scene) {
    this.scene = scene;
    this.meshGroup = new THREE.Group();
    this.scene.add(this.meshGroup);
  }

  /**
   * Render visual representation of terrain hazard grid and obstacles.
   * @param {{ grid: number[][], cellSize: number }} terrainData
   * @param {Array<{position:{x:number,y:number,z:number}, radius:number, height?:number}>} [obstacles]
   */
  renderTerrain(terrainData, obstacles = []) {
    this.clear();

    if (!terrainData || !terrainData.grid) return;

    const { grid, cellSize } = terrainData;
    const rows = grid.length;
    const cols = grid[0].length;

    // Material for ground hazard grid cells
    const cellGeo = new THREE.BoxGeometry(cellSize * 0.95, 0.3, cellSize * 0.95);
    const cellMat = new THREE.MeshStandardMaterial({
      color: 0xff3344,
      emissive: 0xaa1122,
      emissiveIntensity: 0.5,
      transparent: true,
      opacity: 0.45,
      roughness: 0.5,
    });

    // Render cells where grid value is 1 (hazard/obstacle)
    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        if (grid[r][c] === 1) {
          const mesh = new THREE.Mesh(cellGeo, cellMat);
          const worldX = (c + 0.5) * cellSize;
          const worldZ = (r + 0.5) * cellSize;
          const groundY = getHeightAt(worldX, worldZ);
          mesh.position.set(worldX, groundY + 0.15, worldZ);
          this.meshGroup.add(mesh);
        }
      }
    }

    // Render 3D cylinder safety bubbles for cluster obstacles
    for (const obs of obstacles) {
      const radius = obs.radius;
      const height = obs.height || 30.0;
      const groundY = getHeightAt(obs.position.x, obs.position.z);

      const cylGeo = new THREE.CylinderGeometry(radius, radius, height, 32);
      const cylMat = new THREE.MeshStandardMaterial({
        color: 0xff4455,
        emissive: 0x881122,
        emissiveIntensity: 0.3,
        transparent: true,
        opacity: 0.18,
        wireframe: false,
        side: THREE.DoubleSide,
      });

      const cyl = new THREE.Mesh(cylGeo, cylMat);
      cyl.position.set(obs.position.x, groundY + height / 2, obs.position.z);
      this.meshGroup.add(cyl);

      // Wireframe ground boundary ring
      const ringGeo = new THREE.RingGeometry(radius - 0.5, radius + 0.5, 32);
      const ringMat = new THREE.MeshBasicMaterial({
        color: 0xff6677,
        side: THREE.DoubleSide,
        transparent: true,
        opacity: 0.6,
      });
      const ring = new THREE.Mesh(ringGeo, ringMat);
      ring.rotation.x = -Math.PI / 2;
      ring.position.set(obs.position.x, groundY + 0.3, obs.position.z);
      this.meshGroup.add(ring);
    }
  }

  /**
   * Remove all terrain visual elements from the scene.
   */
  clear() {
    while (this.meshGroup.children.length > 0) {
      const obj = this.meshGroup.children.pop();
      if (obj.geometry) obj.geometry.dispose();
      if (obj.material) {
        if (Array.isArray(obj.material)) {
          obj.material.forEach(m => m.dispose());
        } else {
          obj.material.dispose();
        }
      }
    }
  }
}
