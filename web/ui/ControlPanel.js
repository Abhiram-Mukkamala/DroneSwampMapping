/**
 * ControlPanel — minimal UI for simulation control.
 * Reads DOM elements from index.html, wires callbacks.
 */

export class ControlPanel {
  /**
   * @param {object} callbacks
   * @param {function(number)} callbacks.onDroneCountChange
   * @param {function()} callbacks.onPlayPause
   * @param {function()} callbacks.onReset
   */
  constructor(callbacks) {
    this.callbacks = callbacks;

    // DOM elements
    this.droneSlider = document.getElementById('drone-slider');
    this.droneCountLabel = document.getElementById('drone-count');
    this.playPauseBtn = document.getElementById('play-pause-btn');
    this.resetBtn = document.getElementById('reset-btn');
    this.fpsDisplay = document.getElementById('stat-fps');
    this.physicsDisplay = document.getElementById('stat-physics');
    this.countDisplay = document.getElementById('stat-count');
    this.batteryDisplay = document.getElementById('stat-battery');

    this._isPlaying = true;

    // Wire events
    this.droneSlider.addEventListener('input', () => {
      const val = parseInt(this.droneSlider.value, 10);
      this.droneCountLabel.textContent = val;
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
  }

  /**
   * Update the live stats display.
   * @param {object} stats
   * @param {number} stats.fps
   * @param {number} stats.physicsTicks
   * @param {number} stats.droneCount
   * @param {number} stats.avgBattery — 0–1
   */
  updateStats(stats) {
    this.fpsDisplay.textContent = stats.fps.toFixed(0);
    this.physicsDisplay.textContent = stats.physicsTicks;
    this.countDisplay.textContent = stats.droneCount;
    this.batteryDisplay.textContent = (stats.avgBattery * 100).toFixed(0) + '%';
  }
}
