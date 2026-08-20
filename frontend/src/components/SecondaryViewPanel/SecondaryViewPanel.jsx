import React from 'react';
import './SecondaryViewPanel.css';
import { useView, VIEW_SIMULATION, VIEW_SWARM_3D, VIEW_COVERAGE_MAP } from '../../contexts/ViewContext';
import SwarmView3D   from '../SwarmView3D/SwarmView3D';
import CoverageMap   from '../CoverageMap/CoverageMap';
import SimulationContainer from '../SimulationContainer/SimulationContainer';

// ── Toggle config ────────────────────────────────────────────────────────────
// When the simulation feed is in the secondary slot we offer all three choices.
// Normally the toggle only shows SWARM_3D and COVERAGE_MAP.
const NORMAL_TOGGLE = [
  { view: VIEW_SWARM_3D,     label: '3D' },
  { view: VIEW_COVERAGE_MAP, label: 'GIS' },
];

const ALL_TOGGLE = [
  { view: VIEW_SIMULATION,   label: 'CAM' },
  { view: VIEW_SWARM_3D,     label: '3D'  },
  { view: VIEW_COVERAGE_MAP, label: 'GIS' },
];

// ── Component map ────────────────────────────────────────────────────────────
const ViewComponents = {
  [VIEW_SIMULATION]:   () => <SimulationContainer />,
  [VIEW_SWARM_3D]:     () => <SwarmView3D />,
  [VIEW_COVERAGE_MAP]: () => <CoverageMap />,
};

/**
 * SecondaryViewPanel
 *
 * Renders the view currently assigned to the secondary (bottom-left) slot.
 * Contains:
 *  - A slide toggle to switch between SWARM_3D and COVERAGE_MAP
 *  - A ⇄ swap button to promote the secondary view to primary
 */
const SecondaryViewPanel = () => {
  const { primaryView, secondaryView, swapViews, setSecondaryView } = useView();

  // If the camera feed has been swapped to secondary, show all three toggle options
  const toggleOptions = primaryView === VIEW_SIMULATION ? NORMAL_TOGGLE : ALL_TOGGLE;

  const ActiveView = ViewComponents[secondaryView] ?? (() => null);

  return (
    <div className="secondary-view-panel">
      {/* ── Header ── */}
      <div className="secondary-view-header">
        {/* Slide toggle */}
        <div className="view-toggle" role="group" aria-label="Switch secondary view">
          {toggleOptions.map(({ view, label }) => (
            <button
              key={view}
              className={`view-toggle-btn${secondaryView === view ? ' active' : ''}`}
              onClick={() => setSecondaryView(view)}
              aria-pressed={secondaryView === view}
            >
              {label}
            </button>
          ))}
        </div>

        {/* Swap with primary */}
        <button
          className="secondary-swap-btn"
          onClick={swapViews}
          title="Swap with main view"
          aria-label="Swap secondary view with primary"
        >
          ⇄
        </button>
      </div>

      {/* ── Content ── */}
      <div className="secondary-view-content">
        <ActiveView />
      </div>
    </div>
  );
};

export default SecondaryViewPanel;
