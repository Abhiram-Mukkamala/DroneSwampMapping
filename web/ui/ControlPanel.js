/**
 * ControlPanel — UI for simulation control, POV feed stream,
 * and perception detection overlay.
 * Reads DOM elements from index.html, wires callbacks.
 */

import { SCENARIOS } from '../data/scenarios.js';

export class ControlPanel {
  /**
   * @param {object} callbacks
   * @param {function(number)} callbacks.onDroneCountChange
   * @param {function(string)} callbacks.onScenarioChange
   * @param {function()} callbacks.onPlayPause
   * @param {function()} callbacks.onReset
   * @param {function(number)} callbacks.onSelectDrone
   * @param {function(boolean)} callbacks.onTogglePOV
   */
  constructor(callbacks) {
    this.callbacks = callbacks;

    // Control panel DOM elements
    this.scenarioSelect = document.getElementById('scenario-select');
    this.droneSlider = document.getElementById('drone-slider');
    this.droneCountLabel = document.getElementById('drone-count');
    this.playPauseBtn = document.getElementById('play-pause-btn');
    this.resetBtn = document.getElementById('reset-btn');
    this.fpsDisplay = document.getElementById('stat-fps');
    this.physicsDisplay = document.getElementById('stat-physics');
    this.countDisplay = document.getElementById('stat-count');
    this.batteryDisplay = document.getElementById('stat-battery');

    // POV panel DOM elements
    this.povPanel = document.getElementById('pov-panel');
    this.povSelect = document.getElementById('pov-drone-select');
    this.povToggleBtn = document.getElementById('pov-toggle-btn');
    this.povCanvas = document.getElementById('pov-canvas');
    this.povDroneLabel = document.getElementById('pov-drone-id-label');

    // Detection overlay elements
    this.detectionOverlay = document.getElementById('pov-detection-overlay');
    this.detectionCtx = this.detectionOverlay ? this.detectionOverlay.getContext('2d') : null;
    this.perceptionDot = document.getElementById('perception-dot');
    this.perceptionLabel = document.getElementById('perception-label');
    this.detectionCountEl = document.getElementById('detection-count');
    this.inferenceTimeEl = document.getElementById('inference-time');

    this.povCtx = this.povCanvas ? this.povCanvas.getContext('2d') : null;
    this._isPlaying = true;
    this._povVisible = true;
    this.selectedDroneId = 0;

    // Populate scenario options
    this.populateScenarios(SCENARIOS);

    // Wire scenario selector
    if (this.scenarioSelect) {
      this.scenarioSelect.addEventListener('change', () => {
        const scenarioId = this.scenarioSelect.value;
        if (this.callbacks.onScenarioChange) {
          this.callbacks.onScenarioChange(scenarioId);
        }
      });
    }

    // Wire main controls
    this.droneSlider.addEventListener('input', () => {
      const val = parseInt(this.droneSlider.value, 10);
      this.droneCountLabel.textContent = val;
      this.updateDroneSelect(val);
      this.callbacks.onDroneCountChange(val);
    });

    this.playPauseBtn.addEventListener('click', () => {
      this._isPlaying = !this._isPlaying;
      this.playPauseBtn.textContent = this._isPlaying ? '⏸ Pause' : '▶ Play';
      this.playPauseBtn.classList.toggle('paused', !this._isPlaying);
      this.callbacks.onPlayPause();
    });

    this.resetBtn.addEventListener('click', () => {
      this._isPlaying = true;
      this.playPauseBtn.textContent = '⏸ Pause';
      this.playPauseBtn.classList.remove('paused');
      this.callbacks.onReset();
    });

    // Wire POV controls
    if (this.povSelect) {
      this.povSelect.addEventListener('change', () => {
        this.selectedDroneId = parseInt(this.povSelect.value, 10);
        if (this.povDroneLabel) {
          this.povDroneLabel.textContent = `Drone #${this.selectedDroneId}`;
        }
        if (this.callbacks.onSelectDrone) {
          this.callbacks.onSelectDrone(this.selectedDroneId);
        }
      });
    }

    if (this.povToggleBtn) {
      this.povToggleBtn.addEventListener('click', () => {
        this._povVisible = !this._povVisible;
        this.povPanel.classList.toggle('minimized', !this._povVisible);
        this.povToggleBtn.textContent = this._povVisible ? 'Hide' : 'Show';
        if (this.callbacks.onTogglePOV) {
          this.callbacks.onTogglePOV(this._povVisible);
        }
      });
    }

    this.updateDroneSelect(10);
  }

  /**
   * Populate the POV dropdown selector options matching drone count.
   * @param {number} count
   */
  updateDroneSelect(count) {
    if (!this.povSelect) return;
    const currentVal = this.selectedDroneId;
    this.povSelect.innerHTML = '';
    for (let i = 0; i < count; i++) {
      const opt = document.createElement('option');
      opt.value = i;
      opt.textContent = `Drone #${i}`;
      if (i === currentVal) opt.selected = true;
      this.povSelect.appendChild(opt);
    }

    if (currentVal >= count) {
      this.selectedDroneId = 0;
      this.povSelect.value = 0;
      if (this.povDroneLabel) {
        this.povDroneLabel.textContent = `Drone #0`;
      }
    }
  }

  /**
   * Blit an image or canvas onto the UI's POV viewport canvas.
   * @param {HTMLCanvasElement|CanvasImageSource} sourceCanvas
   */
  drawPOVFrame(sourceCanvas) {
    if (this.povCtx && sourceCanvas && this._povVisible) {
      this.povCtx.drawImage(sourceCanvas, 0, 0, this.povCanvas.width, this.povCanvas.height);
    }
  }

  /**
   * Draw detection bounding boxes on the transparent overlay canvas.
   * @param {Array<{class: string, bbox: number[], confidence: number}>} detections
   */
  drawDetectionOverlay(detections) {
    if (!this.detectionCtx) return;

    const ctx = this.detectionCtx;
    const cw = this.detectionOverlay.width;   // 320
    const ch = this.detectionOverlay.height;  // 240

    ctx.clearRect(0, 0, cw, ch);

    if (!detections || detections.length === 0) return;

    for (const det of detections) {
      const [x, y, w, h] = det.bbox;
      const conf = det.confidence;
      const label = `${det.class} ${(conf * 100).toFixed(0)}%`;

      // Box stroke
      ctx.strokeStyle = 'rgba(0, 255, 128, 0.9)';
      ctx.lineWidth = 2;
      ctx.strokeRect(x, y, w, h);

      // Label background
      ctx.font = 'bold 11px Inter, sans-serif';
      const textW = ctx.measureText(label).width;
      const labelH = 16;
      const labelY = y > labelH ? y - labelH : y;

      ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
      ctx.fillRect(x, labelY, textW + 8, labelH);

      // Label text
      ctx.fillStyle = 'rgba(0, 255, 128, 1.0)';
      ctx.fillText(label, x + 4, labelY + 12);
    }
  }

  /**
   * Update the perception status indicator (connected/disconnected).
   * @param {boolean} connected
   * @param {number} detectionCount
   * @param {number} inferenceMs
   */
  updatePerceptionStatus(connected, detectionCount = 0, inferenceMs = 0) {
    if (this.perceptionDot) {
      this.perceptionDot.classList.toggle('connected', connected);
      this.perceptionDot.classList.toggle('disconnected', !connected);
    }
    if (this.perceptionLabel) {
      this.perceptionLabel.textContent = connected ? 'Connected' : 'Disconnected';
    }
    if (this.detectionCountEl) {
      this.detectionCountEl.textContent = detectionCount;
    }
    if (this.inferenceTimeEl) {
      this.inferenceTimeEl.textContent = connected && inferenceMs > 0
        ? `${inferenceMs.toFixed(0)}ms`
        : '';
    }
  }

  get isPOVVisible() {
    return this._povVisible;
  }

  /**
   * Update the live stats display.
   * @param {object} stats
   */
  updateStats(stats) {
    this.fpsDisplay.textContent = stats.fps.toFixed(0);
    this.physicsDisplay.textContent = stats.physicsTicks;
    this.countDisplay.textContent = stats.droneCount;
    this.batteryDisplay.textContent = (stats.avgBattery * 100).toFixed(0) + '%';
  }

  /**
   * Populate the scenario dropdown selector.
   * @param {Array<object>} scenarios
   * @param {string} [activeId='open_field']
   */
  populateScenarios(scenarios, activeId = 'open_field') {
    if (!this.scenarioSelect) return;
    this.scenarioSelect.innerHTML = '';
    for (const sc of scenarios) {
      const opt = document.createElement('option');
      opt.value = sc.id;
      opt.textContent = sc.name;
      if (sc.id === activeId) opt.selected = true;
      this.scenarioSelect.appendChild(opt);
    }
  }
}

