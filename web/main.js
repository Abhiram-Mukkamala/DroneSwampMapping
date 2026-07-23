/**
 * main.js — Application bootstrap and main render loop.
 *
 * Ties the simulation core (fixed-timestep physics) to the Three.js renderer
 * (variable-framerate visuals), keeping them properly decoupled.
 */

import { SimulationLoop } from './core/index.js';
import { SceneManager, DroneRenderer, CameraControls } from './render/index.js';
import { ControlPanel } from './ui/ControlPanel.js';

// ---- Bootstrap ----

const canvas = document.getElementById('viewport');
const sceneManager = new SceneManager(canvas);
const droneRenderer = new DroneRenderer(sceneManager.scene);
const cameraControls = new CameraControls(sceneManager.camera, canvas);

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
    sim.start();
  },
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

  // 5. Render
  sceneManager.render();

  // 6. Update stats panel
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
