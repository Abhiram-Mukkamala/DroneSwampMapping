import React, { useState } from 'react';
import { createPortal } from 'react-dom';
import { useDrones } from '../../contexts/DroneContext';
import './AddDroneModal.css';
import { X, Plus, Zap, ChevronDown, ChevronUp } from 'lucide-react';

const AddDroneModal = ({ isOpen, onClose, onSubmit }) => {
  const { drones } = useDrones();
  const existingCount = drones.length;
  
  const [droneCount, setDroneCount] = useState(1);
  const [droneEntries, setDroneEntries] = useState([
    { name: '', id: '' }
  ]);
  const [isDeploying, setIsDeploying] = useState(false);

  const handleCountChange = (val) => {
    const count = Math.max(1, Math.min(50, parseInt(val) || 1));
    setDroneCount(count);

    // Grow or shrink entries to match count
    setDroneEntries(prev => {
      if (count > prev.length) {
        const newEntries = Array.from({ length: count - prev.length }, () => ({
          name: '',
          id: ''
        }));
        return [...prev, ...newEntries];
      }
      return prev.slice(0, count);
    });
  };

  const updateEntry = (index, field, value) => {
    setDroneEntries(prev => {
      const updated = [...prev];
      updated[index] = { ...updated[index], [field]: value };
      return updated;
    });
  };

  const autoFillAll = () => {
    setDroneEntries(prev => prev.map((entry, i) => ({
      name: entry.name || `Drone ${existingCount + i + 1}`,
      id: entry.id || `DRN-${String(existingCount + i + 1).padStart(2, '0')}`
    })));
  };

  const handleSubmit = () => {
    setIsDeploying(true);

    // Auto-fill any empty fields before submitting
    const finalDrones = droneEntries.map((entry, i) => ({
      name: entry.name || `Drone ${existingCount + i + 1}`,
      id: entry.id || `DRN-${String(existingCount + i + 1).padStart(2, '0')}`,
      status: 'ACTIVE',
      battery: 100,
      task: 'IDLE'
    }));

    // Brief deploy animation before closing
    setTimeout(() => {
      onSubmit(finalDrones);
      setIsDeploying(false);
      // Reset modal state
      setDroneCount(1);
      setDroneEntries([{ name: '', id: '' }]);
      onClose();
    }, 600);
  };

  const handleClose = () => {
    if (isDeploying) return;
    setDroneCount(1);
    setDroneEntries([{ name: '', id: '' }]);
    onClose();
  };

  if (!isOpen) return null;

  return createPortal(
    <div className="modal-overlay" onClick={handleClose}>
      <div className={`modal-container glass-panel ${isDeploying ? 'deploying' : ''}`} onClick={e => e.stopPropagation()}>

        {/* Header */}
        <div className="modal-header">
          <div className="modal-title-group">
            <h2>DEPLOY DRONES</h2>
          </div>
          <button className="modal-close-btn" onClick={handleClose}>
            <X size={18} />
          </button>
        </div>

        {/* Drone Count */}
        <div className="modal-body">
          <div className="form-group">
            <label className="form-label">NUMBER OF DRONES</label>
            <div className="count-input-row">
              <button className="count-btn" onClick={() => handleCountChange(droneCount - 1)}>
                <ChevronDown size={16} />
              </button>
              <input
                type="number"
                className="count-input"
                value={droneCount}
                onChange={e => handleCountChange(e.target.value)}
                min="1"
                max="50"
              />
              <button className="count-btn" onClick={() => handleCountChange(droneCount + 1)}>
                <ChevronUp size={16} />
              </button>
            </div>
          </div>

          {/* Quick presets */}
          <div className="preset-row">
            {[1, 3, 5, 10, 20].map(n => (
              <button
                key={n}
                className={`preset-btn ${droneCount === n ? 'active' : ''}`}
                onClick={() => handleCountChange(n)}
              >
                {n}
              </button>
            ))}
          </div>

          {/* Auto-fill button */}
          <button className="auto-fill-btn" onClick={autoFillAll}>
            AUTO-FILL IDs & NAMES
          </button>

          {/* Drone Entry List */}
          <div className="drone-entries">
            {droneEntries.map((entry, i) => (
              <div className="drone-entry" key={i}>
                <span className="entry-index">#{i + 1}</span>
                <input
                  type="text"
                  className="entry-input"
                  placeholder={`DRN-${String(i + 1).padStart(2, '0')}`}
                  value={entry.id}
                  onChange={e => updateEntry(i, 'id', e.target.value)}
                />
                <input
                  type="text"
                  className="entry-input name-input"
                  placeholder={`Drone ${i + 1}`}
                  value={entry.name}
                  onChange={e => updateEntry(i, 'name', e.target.value)}
                />
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="modal-footer">
          <button className="modal-btn cancel" onClick={handleClose} disabled={isDeploying}>
            CANCEL
          </button>
          <button className="modal-btn deploy" onClick={handleSubmit} disabled={isDeploying}>
            {isDeploying ? (
              <>
                <span className="deploy-spinner" /> DEPLOYING...
              </>
            ) : (
              <>
                <Plus size={16} /> DEPLOY {droneCount} DRONE{droneCount > 1 ? 'S' : ''}
              </>
            )}
          </button>
        </div>

        {/* Deploy overlay flash */}
        {isDeploying && <div className="deploy-flash" />}
      </div>
    </div>,
    document.body
  );
};

export default AddDroneModal;
