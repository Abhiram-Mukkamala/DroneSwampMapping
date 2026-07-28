/**
 * DroneCamera — per-drone point-of-view camera feed generator.
 *
 * Renders a 3D perspective view from a selected drone's position and orientation.
 * Uses an offscreen canvas and separate PerspectiveCamera.
 */

let instance = null;

export class DroneCamera {
  /**
   * @param {number} [width=320]
   * @param {number} [height=240]
   */
  constructor(width = 320, height = 240) {
    this.width = width;
    this.height = height;

    this.canvas = document.createElement('canvas');
    this.canvas.width = width;
    this.canvas.height = height;

    this.renderer = new THREE.WebGLRenderer({
      canvas: this.canvas,
      antialias: true,
      alpha: false,
      preserveDrawingBuffer: true, // required for toDataURL()
    });
    this.renderer.setSize(width, height);
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.2;

    this.camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 1000);
    this.activeDroneId = 0;

    instance = this;
  }

  /**
   * Render the point of view for a specific drone.
   * @param {THREE.Scene} scene
   * @param {object} droneState — { id, position: {x,y,z}, velocity: {x,y,z}, heading }
   * @returns {HTMLCanvasElement}
   */
  render(scene, droneState) {
    if (!droneState) return this.canvas;

    const { position, velocity, heading } = droneState;

    // Position camera at drone center (slightly offset forward and upward for realistic cockpit POV)
    this.camera.position.set(
      position.x,
      position.y,
      position.z
    );

    // Forward direction from heading angle (heading 0 = +Z)
    let dirX = Math.sin(heading);
    let dirZ = Math.cos(heading);
    let dirY = velocity ? velocity.y * 0.1 : 0;

    // If speed is very low, default to +Z forward
    const speedXZ = velocity ? Math.sqrt(velocity.x * velocity.x + velocity.z * velocity.z) : 0;
    if (speedXZ < 0.05) {
      dirX = Math.sin(heading || 0);
      dirZ = Math.cos(heading || 0);
    }

    const target = new THREE.Vector3(
      position.x + dirX * 50,
      position.y + dirY * 50,
      position.z + dirZ * 50
    );

    this.camera.lookAt(target);
    this.renderer.render(scene, this.camera);

    return this.canvas;
  }

  /**
   * Capture current frame as base64 JPEG data URL.
   * @returns {string}
   */
  getFrameDataURL() {
    return this.canvas.toDataURL('image/jpeg', 0.85);
  }

  /**
   * Capture current frame as Blob (for multipart HTTP upload).
   * @returns {Promise<Blob>}
   */
  getFrameBlob() {
    return new Promise(resolve => this.canvas.toBlob(resolve, 'image/jpeg', 0.85));
  }
}

/**
 * Global helper function to get the latest POV canvas for a drone ID.
 * @param {number} droneId
 * @returns {HTMLCanvasElement|null}
 */
export function getDronePOV(droneId) {
  if (instance && instance.activeDroneId === droneId) {
    return instance.canvas;
  }
  return null;
}
