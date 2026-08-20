import './Dashboard.css';
import TopBar from '../../components/TopBar/TopBar';
import Sidebar from '../../components/Sidebar/Sidebar';
import RightPanel from '../../components/RightPanel/RightPanel';
import CommandCenter from '../../components/CommandCenter/CommandCenter';
import MissionLog from '../../components/MissionLog/MissionLog';
import BottomStats from '../../components/BottomStats/BottomStats';
import PrimaryViewPanel from '../../components/PrimaryViewPanel/PrimaryViewPanel';
import SecondaryViewPanel from '../../components/SecondaryViewPanel/SecondaryViewPanel';

const Dashboard = () => {
  return (
    <div className="dashboard-layout">
      <div className="topbar-area">
        <TopBar />
      </div>

      <div className="sidebar-area">
        <Sidebar />
      </div>

      {/* Primary (center) view — driven by ViewContext & wrapped for fullscreen */}
      <div className="center-area">
        <PrimaryViewPanel />
      </div>

      <div className="rightpanel-area">
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            height: '100%',
            gap: '2px',
            minHeight: 0,
            overflow: 'hidden',
          }}
        >
          <div style={{ flex: 1, minHeight: 0, overflow: 'hidden' }}>
            <RightPanel />
          </div>
          <div style={{ flex: 1, minHeight: 0, overflow: 'hidden' }}>
            <BottomStats />
          </div>
        </div>
      </div>

      <div className="bottombar-area">
        {/* Secondary (bottom-left) slot — toggle & swap owned by SecondaryViewPanel */}
        <SecondaryViewPanel />

        <CommandCenter />
        <MissionLog />
      </div>
    </div>
  );
};

export default Dashboard;
