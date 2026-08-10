import React, { useState } from 'react';
import './Sidebar.css';
import { useDrones } from '../../contexts/DroneContext';
import DroneCard from '../DroneCard/DroneCard';
import AddDroneModal from '../AddDroneModal/AddDroneModal';
import { Plus } from 'lucide-react';

const Sidebar = () => {
  const { drones, addDrones, removeDrone } = useDrones();
  const [isModalOpen, setIsModalOpen] = useState(false);

  const handleDeploy = (newDrones) => {
    addDrones(newDrones);
  };

  return (
    <div className="sidebar glass-panel">
      <div className="panel-header">
        <h2>SWARM OVERVIEW</h2>
      </div>
      <div className="panel-content">
        <div className="swarm-stats">
          <div className="stat-box">
            <span className="stat-label">ACTIVE</span>
            <span className="stat-value highlight">{drones.filter(d => d.status === 'ACTIVE').length}</span>
          </div>
          <div className="stat-box">
            <span className="stat-label">TOTAL</span>
            <span className="stat-value">{drones.length}</span>
          </div>
        </div>

        {/* Add Drones Button */}
        <button className="add-drone-btn" onClick={() => setIsModalOpen(true)}>
          <Plus size={16} />
          <span>ADD DRONES</span>
        </button>
        
        <div className="drone-list">
          {drones.length === 0 ? (
            <div className="empty-swarm">
              <span className="empty-icon">◇</span>
              <span className="empty-text">NO DRONES DEPLOYED</span>
              <span className="empty-hint">Click "ADD DRONES" to begin</span>
            </div>
          ) : (
            drones.map(drone => (
              <DroneCard key={drone.id} drone={drone} onRemove={() => removeDrone(drone.id)} />
            ))
          )}
        </div>
      </div>

      <AddDroneModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSubmit={handleDeploy}
      />
    </div>
  );
};

export default Sidebar;
