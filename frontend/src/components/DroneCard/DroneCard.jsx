import React from 'react';
import './DroneCard.css';
import { Battery, X, Wifi, WifiOff } from 'lucide-react';

const DroneCard = ({ drone, onRemove }) => {
  const statusClass = drone.status?.toLowerCase() || 'idle';
  const batteryLevel = drone.battery ?? 100;
  const isLow = batteryLevel < 20;
  const isOffline = drone.status === 'OFFLINE';

  return (
    <div className={`drone-card ${statusClass} ${isOffline ? 'dead' : ''}`}>
      <div className="card-header">
        <div className="card-identity">
          <span className="drone-id">{drone.id}</span>
          <span className="drone-name">{drone.name}</span>
        </div>
        <div className="card-header-right">
          <span className={`drone-status status-${statusClass}`}>{drone.status}</span>
          {onRemove && (
            <button className="remove-drone-btn" onClick={onRemove} title="Remove drone">
              <X size={12} />
            </button>
          )}
        </div>
      </div>
      <div className="card-body">
        <div className="card-stat">
          <Battery size={14} className={`icon ${isLow ? 'low' : ''}`} />
          <div className="battery-bar-container">
            <div
              className={`battery-bar-fill ${isLow ? 'low' : ''} ${isOffline ? 'dead' : ''}`}
              style={{ width: `${batteryLevel}%` }}
            />
          </div>
          <span className={`battery-text ${isLow ? 'low' : ''}`}>{batteryLevel}%</span>
        </div>
        <div className="card-stat">
          <span className="task-label">TASK:</span>
          <span className="task-value">{drone.task || 'IDLE'}</span>
        </div>
      </div>
    </div>
  );
};

export default DroneCard;
