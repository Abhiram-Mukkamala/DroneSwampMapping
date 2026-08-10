import React from 'react';
import './CoverageMap.css';
import { useDrones } from '../../contexts/DroneContext';

const CoverageMap = () => {
  const { drones } = useDrones();
  
  // The pybullet city stretches ~ [-26, 26]. Set 30 as a safe map bounding box.
  const mapBound = 30;

  return (
    <div className="coverage-map glass-panel">
      <div className="panel-header">
        <h2>GIS MAP</h2>
      </div>
      <div className="panel-content map-content">
        <div className="mock-map">
          <div className="map-grid"></div>
          {drones.map(drone => {
            const x = drone.x || 0;
            const y = drone.y || 0;
            
            // Map coordinates to percentage (0% to 100%)
            const left = Math.max(0, Math.min(100, ((x + mapBound) / (mapBound * 2)) * 100));
            // y in pybullet points 'up/north', in CSS top points 'down/south'
            const top = Math.max(0, Math.min(100, 100 - ((y + mapBound) / (mapBound * 2)) * 100));

            return (
              <div 
                key={drone.id} 
                className={`drone-blip ${drone.status === 'DEAD' ? 'dead' : ''}`}
                style={{ top: `${top}%`, left: `${left}%` }}
                title={`ID: ${drone.id} | Pos: (${x.toFixed(1)}, ${y.toFixed(1)})`}
              />
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default CoverageMap;
