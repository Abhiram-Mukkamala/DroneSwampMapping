/**
 * DroneRenderer — manages 3D drone meshes in the Three.js scene.
 *
 * Below 50 drones: individual cone meshes with unique emissive colors.
 * At 50+: InstancedMesh for performance.
 * 
 * Reads from the drone state array (single source of truth from SimulationLoop)
 * and updates mesh positions, rotations, and colors each render frame.
 */

// Shared geometry: cone pointing upward (tip = heading direction)
const CONE_RADIUS = 1.8;
const CONE_HEIGHT = 4.0;
const CONE_SEGMENTS = 8;

// Color palette for drones (HSL cycle)
function droneColor(index, battery) {
  if (battery <= 0) return new THREE.Color(0.3, 0.3, 0.3);        // dead = grey
  if (battery < 0.1) return new THREE.Color(1.0, 0.1, 0.1);       // critical = red
  if (battery < 0.3) return new THREE.Color(1.0, 0.6, 0.0);       // low = amber

  // Healthy: cycle through vibrant hues
  const hue = (index * 0.137) % 1.0; // golden ratio spread
  return new THREE.Color().setHSL(hue, 0.9, 0.55);
}

// Glow sprite texture (soft radial gradient)
function createGlowTexture() {
  const size = 64;
  const canvas = document.createElement('canvas');
  canvas.width = size;
  canvas.height = size;
  const ctx = canvas.getContext('2d');
  const gradient = ctx.createRadialGradient(size / 2, size / 2, 0, size / 2, size / 2, size / 2);
  gradient.addColorStop(0, 'rgba(255,255,255,0.6)');
  gradient.addColorStop(0.3, 'rgba(100,180,255,0.3)');
  gradient.addColorStop(1, 'rgba(0,0,0,0)');
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, size, size);
  return new THREE.CanvasTexture(canvas);
}

export class DroneRenderer {
  /**
   * @param {THREE.Scene} scene
   */
  constructor(scene) {
    this.scene = scene;

    /** @type {THREE.Mesh[]} Individual drone meshes (used when < 50 drones) */
    this.meshes = [];

    /** @type {THREE.Sprite[]} Glow sprites per drone */
    this.glows = [];

    /** @type {THREE.InstancedMesh|null} Used when >= 50 drones */
    this.instancedMesh = null;

    /** Trail lines per drone (last N positions) */
    this.trails = [];
    this.trailHistory = [];  // array of arrays of Vector3
    this.trailMaxLength = 80;

    this.glowTexture = createGlowTexture();
    this._useInstanced = false;
    this._lastCount = 0;

    // Shared geometry and dummy for instanced transforms
    this._coneGeo = new THREE.ConeGeometry(CONE_RADIUS, CONE_HEIGHT, CONE_SEGMENTS);
    this._coneGeo.rotateX(Math.PI / 2); // tip points along +Z (will be rotated to heading)
    this._dummy = new THREE.Object3D();
  }

  /**
   * Sync mesh state with the authoritative drone state array.
   * @param {Array<object>} states — from SimulationLoop.getDroneStates()
   */
  syncWithState(states) {
    const count = states.length;
    const shouldInstance = count >= 50;

    // Rebuild meshes if count changed or instancing mode changed
    if (count !== this._lastCount || shouldInstance !== this._useInstanced) {
      this._rebuild(count, shouldInstance);
    }

    if (this._useInstanced) {
      this._updateInstanced(states);
    } else {
      this._updateIndividual(states);
    }

    this._updateTrails(states);
    this._lastCount = count;
  }

  /**
   * Remove all drone visuals from the scene.
   */
  clear() {
    for (const m of this.meshes) this.scene.remove(m);
    for (const g of this.glows) this.scene.remove(g);
    for (const t of this.trails) this.scene.remove(t);
    if (this.instancedMesh) this.scene.remove(this.instancedMesh);

    this.meshes = [];
    this.glows = [];
    this.trails = [];
    this.trailHistory = [];
    this.instancedMesh = null;
    this._lastCount = 0;
  }

  // ---- Private: rebuild meshes ----

  _rebuild(count, useInstanced) {
    this.clear();
    this._useInstanced = useInstanced;

    if (useInstanced) {
      this._buildInstanced(count);
    } else {
      this._buildIndividual(count);
    }

    // Initialize trail history
    for (let i = 0; i < count; i++) {
      this.trailHistory.push([]);
    }
  }

  _buildIndividual(count) {
    for (let i = 0; i < count; i++) {
      const color = droneColor(i, 1.0);

      const mat = new THREE.MeshStandardMaterial({
        color,
        emissive: color,
        emissiveIntensity: 0.5,
        roughness: 0.3,
        metalness: 0.7,
      });
      const mesh = new THREE.Mesh(this._coneGeo, mat);
      mesh.castShadow = true;
      this.scene.add(mesh);
      this.meshes.push(mesh);

      // Glow sprite
      const spriteMat = new THREE.SpriteMaterial({
        map: this.glowTexture,
        color,
        transparent: true,
        blending: THREE.AdditiveBlending,
        depthWrite: false,
      });
      const sprite = new THREE.Sprite(spriteMat);
      sprite.scale.set(8, 8, 1);
      this.scene.add(sprite);
      this.glows.push(sprite);

      // Trail line
      const trailGeo = new THREE.BufferGeometry();
      const trailMat = new THREE.LineBasicMaterial({
        color,
        transparent: true,
        opacity: 0.4,
      });
      const trail = new THREE.Line(trailGeo, trailMat);
      this.scene.add(trail);
      this.trails.push(trail);
    }
  }

  _buildInstanced(count) {
    const mat = new THREE.MeshStandardMaterial({
      color: 0x44aaff,
      emissive: 0x2266aa,
      emissiveIntensity: 0.4,
      roughness: 0.3,
      metalness: 0.6,
    });
    this.instancedMesh = new THREE.InstancedMesh(this._coneGeo, mat, count);
    this.instancedMesh.castShadow = true;
    // Enable per-instance colors
    this.instancedMesh.instanceColor = new THREE.InstancedBufferAttribute(
      new Float32Array(count * 3), 3
    );
    this.scene.add(this.instancedMesh);

    // Trails for instanced mode too
    for (let i = 0; i < count; i++) {
      const trailGeo = new THREE.BufferGeometry();
      const trailMat = new THREE.LineBasicMaterial({
        color: droneColor(i, 1.0),
        transparent: true,
        opacity: 0.25,
      });
      const trail = new THREE.Line(trailGeo, trailMat);
      this.scene.add(trail);
      this.trails.push(trail);
    }
  }

  // ---- Private: per-frame updates ----

  _updateIndividual(states) {
    for (let i = 0; i < states.length; i++) {
      const s = states[i];
      const mesh = this.meshes[i];
      const glow = this.glows[i];

      // Position
      mesh.position.set(s.position.x, s.position.y, s.position.z);
      glow.position.set(s.position.x, s.position.y, s.position.z);

      // Rotation: cone tip points along heading (XZ plane)
      mesh.rotation.set(0, s.heading, 0);

      // Color based on battery
      const color = droneColor(i, s.battery);
      mesh.material.color.copy(color);
      mesh.material.emissive.copy(color);
      glow.material.color.copy(color);

      // Dim glow for dead drones
      glow.material.opacity = s.status === 'dead' ? 0.1 : 0.8;
    }
  }

  _updateInstanced(states) {
    const im = this.instancedMesh;
    for (let i = 0; i < states.length; i++) {
      const s = states[i];

      this._dummy.position.set(s.position.x, s.position.y, s.position.z);
      this._dummy.rotation.set(0, s.heading, 0);
      this._dummy.updateMatrix();
      im.setMatrixAt(i, this._dummy.matrix);

      const color = droneColor(i, s.battery);
      im.setColorAt(i, color);
    }
    im.instanceMatrix.needsUpdate = true;
    if (im.instanceColor) im.instanceColor.needsUpdate = true;
  }

  _updateTrails(states) {
    for (let i = 0; i < states.length; i++) {
      const s = states[i];
      const history = this.trailHistory[i];
      if (!history) continue;

      history.push(new THREE.Vector3(s.position.x, s.position.y, s.position.z));
      if (history.length > this.trailMaxLength) {
        history.shift();
      }

      // Update trail geometry
      if (this.trails[i] && history.length >= 2) {
        const positions = new Float32Array(history.length * 3);
        for (let j = 0; j < history.length; j++) {
          positions[j * 3] = history[j].x;
          positions[j * 3 + 1] = history[j].y;
          positions[j * 3 + 2] = history[j].z;
        }
        this.trails[i].geometry.dispose();
        this.trails[i].geometry = new THREE.BufferGeometry();
        this.trails[i].geometry.setAttribute(
          'position',
          new THREE.BufferAttribute(positions, 3)
        );
      }
    }
  }
}
