import React, { createContext, useState, useContext, useCallback, useEffect, useRef } from 'react';
import { useSimulation } from './SimulationContext';

const DroneContext = createContext();

export const DroneProvider = ({ children }) => {
  const [drones, setDrones] = useState([]);
  const { sendCommand, subscribeToMessages } = useSimulation();
  
  // Track the next sim-engine drone index so we can map dashboard drones to sim drones
  const nextSimIndex = useRef(0);

  const addDrones = useCallback((newDrones) => {
    const startIndex = nextSimIndex.current;
    const enrichedDrones = newDrones.map((drone, i) => ({
      ...drone,
      simIndex: startIndex + i, // maps to sim engine's internal array index
    }));
    nextSimIndex.current += newDrones.length;

    setDrones(prev => [...prev, ...enrichedDrones]);
    // Tell the simulation engine to add this many drones (incremental, not reset)
    sendCommand('ADD_DRONES', { count: newDrones.length });
  }, [sendCommand]);

  const removeDrone = useCallback((droneId) => {
    setDrones(prev => {
      const targetIndex = prev.findIndex(d => d.id === droneId);
      if (targetIndex === -1) return prev;

      const target = prev[targetIndex];
      // Send the current position in the list (which matches backend's followers array index)
      sendCommand('REMOVE_DRONE', { droneId: targetIndex });

      // Remove the drone and re-index all remaining drones so simIndex
      // stays in sync with the backend's followers array positions
      const remaining = prev.filter(d => d.id !== droneId);
      const reindexed = remaining.map((d, i) => ({ ...d, simIndex: i }));
      nextSimIndex.current = reindexed.length;
      return reindexed;
    });
  }, [sendCommand]);

  const clearDrones = useCallback(() => {
    setDrones([]);
    nextSimIndex.current = 0;
    sendCommand('RESET_SIMULATION', {});
  }, [sendCommand]);

  // Sync position, velocity, battery & status from telemetry updates
  useEffect(() => {
    return subscribeToMessages((message) => {
      if (message.type === 'TELEMETRY_UPDATE' && message.payload?.droneStates) {
        const simStates = message.payload.droneStates;
        setDrones(prev => prev.map(drone => {
          const simState = simStates.find(s => s.id === String(drone.simIndex));
          if (simState) {
            return {
              ...drone,
              battery: Math.round(simState.battery * 100),
              status: simState.status,  // backend sends canonical: ACTIVE | IDLE | STUCK | OFFLINE
              position: simState.position,   // { x, y, z }
              velocity: simState.velocity,   // { x, y, z }
              heading: simState.heading,
            };
          }
          return drone;
        }));
      }
    });
  }, [subscribeToMessages]);

  return (
    <DroneContext.Provider value={{ drones, setDrones, addDrones, removeDrone, clearDrones }}>
      {children}
    </DroneContext.Provider>
  );
};

export const useDrones = () => useContext(DroneContext);

