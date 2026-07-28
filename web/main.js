/**
 * main.js — Application bootstrap and main render loop.
 *
 * Ties the simulation core (fixed-timestep physics) to the Three.js renderer
 * (variable-framerate visuals), keeping them properly decoupled.
 * Also renders per-drone POV stream and wires perception inference pipeline.
 */

import { SimulationLoop } from './core/index.js';
import { SceneManager, DroneRenderer, CameraControls, DroneCamera } from './render/index.js';
import { ControlPanel } from './ui/ControlPanel.js';
import {
  startPerceptionLoop,
  stopPerceptionLoop,
  isConnected,
  getLastDetections,
  getLastInferenceMs,
} from './perception/index.js';

// ---- Bootstrap ----

const canvas = document.getElementById('viewport');
const sceneManager = new SceneManager(canvas);
const droneRenderer = new DroneRenderer(sceneManager.scene);
const cameraControls = new CameraControls(sceneManager.camera, canvas);
const droneCamera = new DroneCamera(320, 240);

const sim = new SimulationLoop();
sim.reset(10);   // default: 10 drones
sim.start();

// ---- FPS tracking ----
let frameCount = 0;
let fpsAccum = 0;
let currentFps = 60;

// ---- Control Panel ----
const panel = new ControlPanel({
  onDroneCountChange(count) {
    sim.reset(count);
    droneRenderer.clear();
    panel.updateDroneSelect(count);
  },
  onPlayPause() {
    if (sim.running) {
      sim.stop();
    } else {
      sim.start();
    }
  },
  onReset() {
    const count = parseInt(document.getElementById('drone-slider').value, 10);
    sim.reset(count);
    droneRenderer.clear();
    panel.updateDroneSelect(count);
    sim.start();
  },
  onSelectDrone(droneId) {
    droneCamera.activeDroneId = droneId;
  },
  onTogglePOV(visible) {
    // POV visibility toggle handler
  },
});

// ---- Start Perception Pipeline ----
// Provides the active drone state getter for frame capture timing
startPerceptionLoop(droneCamera, sceneManager.scene, () => {
  const states = sim.getDroneStates();
  const activeId = panel.selectedDroneId;
  return states.find(s => s.id === activeId) || states[0] || null;
});

// ---- Main loop ----
let lastTime = performance.now();

function loop(now) {
  requestAnimationFrame(loop);

  const delta = (now - lastTime) / 1000; // seconds
  lastTime = now;

  // FPS counter (update every 0.5s)
  frameCount++;
  fpsAccum += delta;
  if (fpsAccum >= 0.5) {
    currentFps = frameCount / fpsAccum;
    frameCount = 0;
    fpsAccum = 0;
  }

  // 1. Physics ticks (fixed timestep, may run multiple ticks per frame)
  sim.update(delta);

  // 2. Read authoritative state
  const states = sim.getDroneStates();

  // 3. Sync visuals to state
  droneRenderer.syncWithState(states);

  // 4. Camera damping update
  cameraControls.update();

  // 5. Render main camera view
  sceneManager.render();

  // 6. Render selected drone POV if panel is open
  if (panel.isPOVVisible && states.length > 0) {
    const activeId = panel.selectedDroneId;
    const droneState = states.find(s => s.id === activeId) || states[0];
    const povCanvas = droneCamera.render(sceneManager.scene, droneState);
    panel.drawPOVFrame(povCanvas);
  }

  // 7. Update perception overlay + status (reads cached state, no async here)
  const connected = isConnected();
  const detections = getLastDetections();
  const inferenceMs = getLastInferenceMs();

  panel.drawDetectionOverlay(detections);
  panel.updatePerceptionStatus(connected, detections.length, inferenceMs);

  // 8. Update stats panel
  const avgBat = states.length > 0
    ? states.reduce((sum, s) => sum + s.battery, 0) / states.length
    : 0;

  panel.updateStats({
    fps: currentFps,
    physicsTicks: sim.tickCount,
    droneCount: states.length,
    avgBattery: avgBat,
  });
}

requestAnimationFrame(loop);
