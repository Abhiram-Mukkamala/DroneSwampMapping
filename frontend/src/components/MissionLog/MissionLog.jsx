import React, { useState, useEffect, useRef } from 'react';
import './MissionLog.css';
import { useMission } from '../../contexts/MissionContext';
import { useSimulation } from '../../contexts/SimulationContext';
import { useDrones } from '../../contexts/DroneContext';

const MissionLog = () => {
  const { missionPhase } = useMission();
  const { isConnected, subscribeToMessages } = useSimulation();
  const { drones } = useDrones();
  const [logs, setLogs] = useState([
    { id: 1, time: new Date().toLocaleTimeString(), msg: 'SYSTEM BOOT SEQUENCE INITIATED', type: 'INFO' }
  ]);
  const logEndRef = useRef(null);
  const prevDroneCount = useRef(0);

  // Auto-scroll inside SYS_LOG panel when new log arrives
  useEffect(() => {
    if (logEndRef.current) {
      logEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs]);

  // Log mission phase changes
  useEffect(() => {
    const newLog = {
      id: Date.now(),
      time: new Date().toLocaleTimeString(),
      msg: `MISSION PHASE CHANGED TO ${missionPhase}`,
      type: 'WARN'
    };
    setLogs(prev => [...prev, newLog].slice(-100));
  }, [missionPhase]);

  // Log simulation connection state
  useEffect(() => {
    return subscribeToMessages((message) => {
      if (message.type === 'SIM_READY') {
        setLogs(prev => [...prev, {
          id: Date.now(),
          time: new Date().toLocaleTimeString(),
          msg: 'PYBULLET V2 SIMULATION CONNECTED',
          type: 'INFO'
        }].slice(-100));
      }
    });
  }, [subscribeToMessages]);

  // Log drone count changes
  useEffect(() => {
    const currentCount = drones.length;
    if (currentCount !== prevDroneCount.current) {
      if (currentCount > prevDroneCount.current) {
        const added = currentCount - prevDroneCount.current;
        setLogs(prev => [...prev, {
          id: Date.now(),
          time: new Date().toLocaleTimeString(),
          msg: `DEPLOYED +${added} DRONE(S) (TOTAL: ${currentCount})`,
          type: 'INFO'
        }].slice(-100));
      } else if (currentCount < prevDroneCount.current) {
        setLogs(prev => [...prev, {
          id: Date.now(),
          time: new Date().toLocaleTimeString(),
          msg: `SWARM RE-INDEXED (TOTAL: ${currentCount})`,
          type: 'WARN'
        }].slice(-100));
      }
      prevDroneCount.current = currentCount;
    }
  }, [drones.length]);

  return (
    <div className="mission-log glass-panel">
      <div className="panel-header">
        <h2>SYS_LOG</h2>
      </div>
      <div className="panel-content log-content">
        <ul className="log-list">
          {logs.map(log => (
            <li key={log.id} className={`log-entry ${log.type.toLowerCase()}`}>
              <span className="log-time">[{log.time}]</span>
              <span className="log-msg">{log.msg}</span>
            </li>
          ))}
          <div ref={logEndRef} />
        </ul>
      </div>
    </div>
  );
};

export default MissionLog;
