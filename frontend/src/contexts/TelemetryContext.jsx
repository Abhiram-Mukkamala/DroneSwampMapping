import React, { createContext, useState, useContext, useEffect } from 'react';
import { useSimulation } from './SimulationContext';

const TelemetryContext = createContext();

export const TelemetryProvider = ({ children }) => {
  const { subscribeToMessages } = useSimulation();

  const [telemetry, setTelemetry] = useState({
    fps: 0,
    droneCount: 0,
    avgBattery: 100,
    physicsTicks: 0,
    perceptionStatus: 'disconnected',
    detections: 0,
    inferenceMs: 0
  });

  useEffect(() => {
    return subscribeToMessages((message) => {
      if (message.type === 'TELEMETRY_UPDATE') {
        setTelemetry(prev => ({
          ...prev,
          ...message.payload
        }));
      }
    });
  }, [subscribeToMessages]);

  return (
    <TelemetryContext.Provider value={{ telemetry, setTelemetry }}>
      {children}
    </TelemetryContext.Provider>
  );
};

export const useTelemetry = () => useContext(TelemetryContext);
