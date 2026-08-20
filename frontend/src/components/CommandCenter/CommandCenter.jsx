import React from 'react';
import './CommandCenter.css';
import { useMission } from '../../contexts/MissionContext';
import { useDrones } from '../../contexts/DroneContext';
import { Play, Pause, Square } from 'lucide-react';

const CommandCenter = () => {
  const { missionPhase, startMission, pauseMission, stopMission } = useMission();
  const { clearDrones } = useDrones();

  const handleAbort = () => {
    stopMission();
    clearDrones();
  };

  return (
    <div className="command-center glass-panel">
      <div className="panel-header center">
        <h2>COMMAND UPLINK</h2>
      </div>
      <div className="panel-content cmd-content">
        <div className="btn-group">
          <button 
            className={`cmd-btn start ${missionPhase === 'ACTIVE' ? 'active' : ''}`}
            onClick={startMission}
          >
            <Play size={18} className="icon"/> EXECUTE
          </button>
          <button 
            className={`cmd-btn pause ${missionPhase === 'PAUSED' ? 'active' : ''}`}
            onClick={pauseMission}
          >
            <Pause size={18} className="icon"/> HOLD
          </button>
          <button 
            className={`cmd-btn stop ${missionPhase === 'STOPPED' ? 'active' : ''}`}
            onClick={handleAbort}
          >
            <Square size={18} className="icon"/> ABORT
          </button>
        </div>
      </div>
    </div>
  );
};

export default CommandCenter;
