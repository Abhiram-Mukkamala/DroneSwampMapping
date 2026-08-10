import React, { useState } from 'react';
import './SimulationContainer.css';
import { useSimulation } from '../../contexts/SimulationContext';

const SimulationContainer = () => {
  const { isConnected } = useSimulation();
  const [streamError, setStreamError] = useState(false);

  return (
    <div className="simulation-container">
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
