import React from 'react';
import './RightPanel.css';
import { useTelemetry } from '../../contexts/TelemetryContext';
import { useDrones } from '../../contexts/DroneContext';

const RightPanel = () => {
  const { telemetry } = useTelemetry();
  const { drones } = useDrones();

  return (
    <div className="right-panel glass-panel">
      <div className="panel-header">
        <h2>TELEMETRY</h2>
      </div>
      <div className="panel-content">
        <div className="telemetry-grid">
          <div className="data-box">
            <span className="data-label">FPS</span>
            <span className="data-value">{telemetry.fps || '--'}</span>
          </div>
          <div className="data-box">
            <span className="data-label">DRONES</span>
            <span className="data-value">{drones.length}</span>
          </div>
          <div className="data-box">
            <span className="data-label">BATTERY</span>
            <span className="data-value">{telemetry.avgBattery ?? '--'}%</span>
          </div>
          <div className="data-box">
            <span className="data-label">PERCEPTION</span>
            <span className="data-value" style={{ color: telemetry.perceptionStatus === 'connected' ? 'var(--color-accent-green, #4ade80)' : 'var(--color-accent-red, #f87171)' }}>
              {telemetry.perceptionStatus === 'connected' ? 'ONLINE' : 'OFFLINE'}
            </span>
          </div>
          <div className="data-box">
            <span className="data-label">DETECTIONS</span>
            <span className="data-value">{telemetry.detections ?? 0}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RightPanel;

