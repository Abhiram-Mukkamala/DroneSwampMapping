import React from 'react';
import './TopBar.css';
import { useMission } from '../../contexts/MissionContext';
import { useSimulation } from '../../contexts/SimulationContext';
import { Settings, Signal, Battery, Clock } from 'lucide-react';

const TopBar = () => {
  const { missionPhase, timer } = useMission();
  const { fps, isConnected } = useSimulation();

  return (
    <div className="topbar glass-panel">
      <div className="topbar-left">
        <h1 className="logo">SWARM<span className="accent">CTRL</span></h1>
        <div className="status-badge">
          <span className={`status-dot ${isConnected ? 'online' : 'offline'}`}></span>
          {isConnected ? 'SYS.ONLINE' : 'SYS.OFFLINE'}
        </div>
      </div>

      <div className="topbar-center">
        <div className="phase-indicator">
          PHASE: <span className="highlight">{missionPhase}</span>
        </div>
        <div className="mission-timer">
          <Clock className="icon" size={16} />
          T+{timer}s
        </div>
      </div>

      <div className="topbar-right">

      
      </div>
    </div>
  );
};

export default TopBar;
