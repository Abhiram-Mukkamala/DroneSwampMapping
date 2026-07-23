/**
 * CameraControls — OrbitControls wrapper for mouse + touch interaction.
 *
 * - Mouse: left-drag orbit, right-drag pan, scroll zoom
 * - Touch: one-finger orbit, two-finger pinch zoom + pan
 * - Smooth damping for inertia feel
 */

export class CameraControls {
  /**
   * @param {THREE.Camera} camera
   * @param {HTMLElement} domElement
   */
  constructor(camera, domElement) {
    this.controls = new THREE.OrbitControls(camera, domElement);

    // Target: center of arena
    this.controls.target.set(250, 10, 250);

    // Damping for smooth feel
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.08;

    // Zoom limits
    this.controls.minDistance = 20;
    this.controls.maxDistance = 1200;

    // Prevent going underground
    this.controls.maxPolarAngle = Math.PI / 2 - 0.05;

    // Pan limits (keep arena in view)
    this.controls.minPan = new THREE.Vector3(0, 0, 0);
    this.controls.maxPan = new THREE.Vector3(500, 100, 500);

    // Enable touch gestures
    this.controls.touches = {
      ONE: THREE.TOUCH.ROTATE,
      TWO: THREE.TOUCH.DOLLY_PAN,
    };

    // Reasonable rotation speed
    this.controls.rotateSpeed = 0.8;
    this.controls.panSpeed = 0.8;

    this.controls.update();
  }

  update() {
    this.controls.update();
  }
}
