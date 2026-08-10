import React, { createContext, useState, useContext, useEffect } from 'react';
import { useSimulation } from './SimulationContext';

const MissionContext = createContext();

export const MissionProvider = ({ children }) => {
  const [missionPhase, setMissionPhase] = useState('PRE-FLIGHT');
  const [timer, setTimer] = useState(0);
  
  const { sendCommand } = useSimulation();

  useEffect(() => {
    let interval = null;
    if (missionPhase === 'ACTIVE') {
      interval = setInterval(() => {
        setTimer(t => t + 1);
      }, 1000);
    } else {
      if (interval) clearInterval(interval);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [missionPhase]);

  const startMission = () => {
    setMissionPhase('ACTIVE');
    sendCommand('START_SIMULATION');
  };
  
  const pauseMission = () => {
    setMissionPhase('PAUSED');
    sendCommand('PAUSE_SIMULATION');
  };
  
  const stopMission = () => {
    setMissionPhase('STOPPED');
    sendCommand('EMERGENCY_STOP');
  };

  return (
    <MissionContext.Provider value={{ missionPhase, timer, setTimer, startMission, pauseMission, stopMission }}>
      {children}
    </MissionContext.Provider>
  );
};

export const useMission = () => useContext(MissionContext);
