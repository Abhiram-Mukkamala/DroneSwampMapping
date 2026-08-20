import './CoverageMap.css';
import { useDrones } from '../../contexts/DroneContext';

const CoverageMap = () => {
  const { drones } = useDrones();

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
            const pos = drone.position || {
              x: 0,
              y: 0,
              z: 0
            };

            const x = pos.x;
            const y = pos.y;

            const left = Math.max(
              0,
              Math.min(
                100,
                ((x + mapBound) / (mapBound * 2)) * 100
              )
            );

            const top = Math.max(
              0,
              Math.min(
                100,
                100 -
                  ((y + mapBound) / (mapBound * 2)) * 100
              )
            );

            return (
              <div
                key={drone.id}
                className={`drone-blip ${
                  drone.status === 'OFFLINE' ? 'dead' : ''
                }`}
                style={{
                  top: `${top}%`,
                  left: `${left}%`
                }}
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