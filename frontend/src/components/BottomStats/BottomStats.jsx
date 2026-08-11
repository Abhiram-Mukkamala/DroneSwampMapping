import React from 'react';
import './BottomStats.css';
import { useDrones } from '../../contexts/DroneContext';

const statusColor = (status) => {
  switch (status) {
    case 'ACTIVE':  return 'var(--color-accent-green)';
    case 'STUCK':   return 'var(--color-accent-yellow)';
    case 'OFFLINE': return 'var(--color-accent-red)';
    case 'IDLE':    return 'var(--color-text-secondary)';
    default:        return 'var(--color-text-secondary)';
  }
};

const batteryColor = (pct) => {
  if (pct <= 20) return 'var(--color-accent-red)';
  if (pct <= 50) return 'var(--color-accent-yellow)';
  return 'var(--color-accent-green)';
};

const DroneTelemCard = ({ drone }) => {
  const pos = drone.position || { x: 0, y: 0, z: 0 };
  const vel = drone.velocity || { x: 0, y: 0, z: 0 };
  const speed = Math.hypot(vel.x, vel.y);

  return (
    <div className="drone-telem-card">
      <div className="drone-telem-header">
        <span className="drone-telem-id">DRONE {drone.id}</span>
        <span className="drone-telem-status" style={{ color: statusColor(drone.status) }}>
          ● {drone.status || 'IDLE'}
        </span>
      </div>
      <div className="drone-telem-grid">
        <div className="telem-cell">
          <span className="telem-label">SPEED</span>
          <span className="telem-value">{speed.toFixed(1)}<small> m/s</small></span>
        </div>
        <div className="telem-cell">
          <span className="telem-label">ALT</span>
          <span className="telem-value">{pos.z.toFixed(1)}<small> m</small></span>
        </div>
        <div className="telem-cell">
          <span className="telem-label">HEADING</span>
          <span className="telem-value">{(drone.heading || 0).toFixed(0)}<small>°</small></span>
        </div>
        <div className="telem-cell">
          <span className="telem-label">BATTERY</span>
          <span className="telem-value" style={{ color: batteryColor(drone.battery ?? 100) }}>
            {drone.battery ?? 100}<small>%</small>
          </span>
        </div>
        <div className="telem-cell telem-cell--wide">
          <span className="telem-label">POSITION</span>
          <span className="telem-value telem-mono">
            X:{pos.x.toFixed(1)} Y:{pos.y.toFixed(1)}
          </span>
        </div>
      </div>
    </div>
  );
};

const BottomStats = () => {
  const { drones } = useDrones();

  return (
    <div className="bottom-stats glass-panel">
      <div className="panel-header">
        <h2>DRONE TELEMETRY</h2>
      </div>
      <div className="stats-scroll-area">
        {drones.length === 0 ? (
          <div className="no-drones-msg">NO DRONES DEPLOYED</div>
        ) : (
          drones.map(drone => <DroneTelemCard key={drone.id} drone={drone} />)
        )}
      </div>
    </div>
  );
};

export default BottomStats;
