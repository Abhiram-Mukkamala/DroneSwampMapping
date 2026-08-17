/**
 * SceneManager — Three.js scene setup: renderer, camera, ground plane, lights, fog.
 * 
 * Arena: 500 × 500m ground plane with grid, Y-up coordinate system.
 */

import { TerrainRenderer } from './TerrainRenderer.js';
import { getTerrainData, getObstacles } from '../data/index.js';

export class SceneManager {
  constructor(canvas) {
    // --- Renderer ---
    this.renderer = new THREE.WebGLRenderer({
      canvas,
      antialias: true,
      alpha: false,
    });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.setSize(window.innerWidth, window.innerHeight);
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.2;

    // --- Scene ---
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x070b15);
    this.scene.fog = new THREE.FogExp2(0x070b15, 0.0012);

    // --- Camera ---
    this.camera = new THREE.PerspectiveCamera(
      55, window.innerWidth / window.innerHeight, 0.5, 2000
    );
    this.camera.position.set(250, 250, 550);
    this.camera.lookAt(250, 0, 250);

    // --- Ground plane ---
    this._createGround();

    // --- Terrain Renderer ---
    this.terrainRenderer = new TerrainRenderer(this.scene);
    this.updateTerrain();

    // --- Lighting ---
    this._createLights();

    // --- Resize handler ---
    window.addEventListener('resize', () => this._onResize());
  }

  /**
   * Render or regenerate terrain meshes in scene using terrainData & obstacles.
   * Defaults to pulling from data module if omitted.
   * @param {{ grid: number[][], cellSize: number }} [terrainData]
   * @param {Array<object>} [obstacles]
   */
  updateTerrain(terrainData, obstacles) {
    const data = terrainData || getTerrainData();
    const obs = obstacles || getObstacles();
    this.terrainRenderer.renderTerrain(data, obs);
  }

  _createGround() {
    // Main ground surface
    const groundGeo = new THREE.PlaneGeometry(500, 500);
    const groundMat = new THREE.MeshStandardMaterial({
      color: 0x0d1117,
      roughness: 0.9,
      metalness: 0.1,
    });
    const ground = new THREE.Mesh(groundGeo, groundMat);
    ground.rotation.x = -Math.PI / 2;
    ground.position.set(250, 0, 250);
    ground.receiveShadow = true;
    this.scene.add(ground);

    // Grid lines every 50m for scale reference
    const gridHelper = new THREE.GridHelper(500, 10, 0x1a2332, 0x111a27);
    gridHelper.position.set(250, 0.01, 250);
    this.scene.add(gridHelper);

    // Subtle outer boundary lines
    const borderGeo = new THREE.EdgesGeometry(
      new THREE.BoxGeometry(500, 0.1, 500)
    );
    const borderMat = new THREE.LineBasicMaterial({ color: 0x1e90ff, opacity: 0.3, transparent: true });
    const border = new THREE.LineSegments(borderGeo, borderMat);
    border.position.set(250, 0.05, 250);
    this.scene.add(border);
  }

  _createLights() {
    // Soft ambient fill
    const ambient = new THREE.AmbientLight(0x2a3050, 0.8);
    this.scene.add(ambient);

    // Hemisphere light for natural sky/ground gradient
    const hemi = new THREE.HemisphereLight(0x4488cc, 0x112244, 0.5);
    this.scene.add(hemi);

    // Main directional sun
    const sun = new THREE.DirectionalLight(0xffeedd, 1.2);
    sun.position.set(200, 300, 150);
    sun.castShadow = true;
    sun.shadow.mapSize.width = 2048;
    sun.shadow.mapSize.height = 2048;
    sun.shadow.camera.left = -300;
    sun.shadow.camera.right = 300;
    sun.shadow.camera.top = 300;
    sun.shadow.camera.bottom = -300;
    sun.shadow.camera.near = 1;
    sun.shadow.camera.far = 800;
    this.scene.add(sun);

    // Subtle blue rim light from below/behind
    const rim = new THREE.DirectionalLight(0x1e90ff, 0.3);
    rim.position.set(-100, 50, -100);
    this.scene.add(rim);
  }

  _onResize() {
    this.camera.aspect = window.innerWidth / window.innerHeight;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(window.innerWidth, window.innerHeight);
  }

  render() {
    this.renderer.render(this.scene, this.camera);
  }
}
