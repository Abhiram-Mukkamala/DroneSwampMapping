import React, { useState, useEffect, useRef } from 'react';
import './SimulationContainer.css';
import { useSimulation } from '../../contexts/SimulationContext';

const VALID_KEYS = ['w', 'a', 's', 'd', 'q', 'e', ' ', 'shift'];

const SimulationContainer = () => {
  const { isConnected, sendCommand } = useSimulation();
  const [streamError, setStreamError] = useState(false);
  const lastX = useRef(null);

  useEffect(() => {
    if (!isConnected) return;

    const handleKeyDown = (e) => {
      const key = e.key.toLowerCase();
      if (VALID_KEYS.includes(key)) {
        // Prevent default browser scrolling for Space and Shift when controlling drone
        if (key === ' ' || key === 'shift') {
          e.preventDefault();
        }
        sendCommand('KEY_DOWN', { key });
      }
    };

    const handleKeyUp = (e) => {
      const key = e.key.toLowerCase();
      if (VALID_KEYS.includes(key)) {
        sendCommand('KEY_UP', { key });
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('keyup', handleKeyUp);
    };
  }, [isConnected, sendCommand]);

  const handleMouseMove = (e) => {
    if (!isConnected) return;
    const dx = e.movementX !== undefined && e.movementX !== 0
      ? e.movementX
      : (lastX.current !== null ? e.clientX - lastX.current : 0);
    lastX.current = e.clientX;
    if (dx !== 0) {
      sendCommand('MOUSE_MOVE', { dx });
    }
  };

  const handleMouseLeave = () => {
    lastX.current = null;
  };

  return (
    <div 
      className="simulation-container"
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
    >
      <div className="reticle reticle-tl"></div>
      <div className="reticle reticle-tr"></div>
      <div className="reticle reticle-bl"></div>
      <div className="reticle reticle-br"></div>
      
      {/* Always render the img tag so it maintains the MJPEG connection */}
      <div className="video-stream-container">
        <img 
          src="http://localhost:5000/video_feed" 
          alt="3D Drone Vision Stream" 
          className="mjpeg-stream"
          onError={() => setStreamError(true)}
          onLoad={() => setStreamError(false)}
        />
      </div>

      {/* Overlay messages on top, don't replace the stream */}
      {!isConnected && (
        <div className="status-overlay">
          <h2>⚡ Connecting to PyBullet Engine...</h2>
          <p>Waiting for WebSocket on port 8765</p>
        </div>
      )}

      {streamError && isConnected && (
        <div className="status-overlay">
          <h2>📡 Video Stream Loading...</h2>
          <p>Camera feed starting on port 5000</p>
        </div>
      )}
    </div>
  );
};

export default SimulationContainer;
