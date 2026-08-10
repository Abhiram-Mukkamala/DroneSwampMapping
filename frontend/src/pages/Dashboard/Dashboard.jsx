import React from 'react';
import './Dashboard.css';
import TopBar from '../../components/TopBar/TopBar';
import Sidebar from '../../components/Sidebar/Sidebar';
import SimulationContainer from '../../components/SimulationContainer/SimulationContainer';
import RightPanel from '../../components/RightPanel/RightPanel';
import CoverageMap from '../../components/CoverageMap/CoverageMap';
import CommandCenter from '../../components/CommandCenter/CommandCenter';
import MissionLog from '../../components/MissionLog/MissionLog';
import BottomStats from '../../components/BottomStats/BottomStats';

const Dashboard = () => {
  return (
    <div className="dashboard-layout">
      <div className="topbar-area">
        <TopBar />
      </div>
      
      <div className="sidebar-area">
        <Sidebar />
      </div>
      
      <div className="center-area">
        <SimulationContainer />
      </div>
      
      <div className="rightpanel-area">
        {/* Combining RightPanel features into a stack */}
        <div style={{ display: 'flex', flexDirection: 'column', height: '100%', gap: '2px', minHeight: 0, overflow: 'hidden' }}>
          <div style={{ flex: 1, minHeight: 0, overflow: 'hidden' }}>
            <RightPanel />
          </div>
          <div style={{ flex: 1, minHeight: 0, overflow: 'hidden' }}>
            <BottomStats />
          </div>
        </div>
      </div>
      
      <div className="bottombar-area">
        <CoverageMap />
        <CommandCenter />
        <MissionLog />
      </div>
    </div>
  );
};

export default Dashboard;
