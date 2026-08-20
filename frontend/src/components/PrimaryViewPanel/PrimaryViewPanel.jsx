import React, { useRef } from 'react';
import './PrimaryViewPanel.css';
import useFullscreen from '../../hooks/useFullscreen';
import { Maximize, Minimize } from 'lucide-react';
import { useView, VIEW_SIMULATION, VIEW_SWARM_3D, VIEW_COVERAGE_MAP } from '../../contexts/ViewContext';
import SimulationContainer from '../SimulationContainer/SimulationContainer';
import SwarmView3D from '../SwarmView3D/SwarmView3D';
import CoverageMap from '../CoverageMap/CoverageMap';

const PrimaryViewMap = {
  [VIEW_SIMULATION]: <SimulationContainer />,
  [VIEW_SWARM_3D]: <SwarmView3D />,
  [VIEW_COVERAGE_MAP]: <CoverageMap />,
};

const PrimaryViewPanel = () => {
  const panelRef = useRef(null);
  const { isFullscreen, toggleFullscreen } = useFullscreen(panelRef);
  const { primaryView } = useView();

  return (
    <div className="primary-view-panel" ref={panelRef}>
      {PrimaryViewMap[primaryView] ?? <SimulationContainer />}
      
      <button 
        className="fullscreen-btn" 
        onClick={toggleFullscreen}
        title={isFullscreen ? "Exit Fullscreen" : "Enter Fullscreen"}
        aria-label={isFullscreen ? "Exit Fullscreen" : "Enter Fullscreen"}
      >
        {isFullscreen ? <Minimize size={18} /> : <Maximize size={18} />}
      </button>
    </div>
  );
};

export default PrimaryViewPanel;
