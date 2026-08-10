import React, { createContext, useRef, useContext, useCallback, useEffect, useState } from 'react';

const SimulationContext = createContext();

export const SimulationProvider = ({ children }) => {
  const listeners = useRef(new Set());
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef(null);

  // Keep this to prevent breaking existing SimulationContainer
  const setIframeRef = useCallback((ref) => {}, []);

  const connectWebSocket = useCallback(() => {
    const ws = new WebSocket('ws://localhost:8765');

    ws.onopen = () => {
      console.log('Connected to PyBullet V2 Backend');
      setIsConnected(true);
      listeners.current.forEach(listener => listener({ type: 'SIM_READY' }));
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type) {
          listeners.current.forEach(listener => listener(data));
        }
      } catch (err) {
        console.error("Failed to parse websocket message", err);
      }
    };

    ws.onclose = () => {
      console.log('Disconnected from backend');
      setIsConnected(false);
      // Try to reconnect every 3s
      setTimeout(connectWebSocket, 3000);
    };

    wsRef.current = ws;
  }, []);

  useEffect(() => {
    connectWebSocket();
    return () => {
      if (wsRef.current) wsRef.current.close();
    };
  }, [connectWebSocket]);

  const sendCommand = useCallback((type, payload = {}) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type, payload, timestamp: Date.now() }));
    }
  }, []);

  const subscribeToMessages = useCallback((callback) => {
    listeners.current.add(callback);
    return () => listeners.current.delete(callback);
  }, []);

  return (
    <SimulationContext.Provider value={{ setIframeRef, sendCommand, subscribeToMessages, isConnected }}>
      {children}
    </SimulationContext.Provider>
  );
};

export const useSimulation = () => useContext(SimulationContext);
