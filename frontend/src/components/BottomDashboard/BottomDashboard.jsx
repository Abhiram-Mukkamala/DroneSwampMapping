/**
 * BottomDashboard — Assembles the entire bottom section.
 *
 * Layout (left → right):
 *   CoverageMap | BottomStats | CommandCenter | MissionLog
 *
 * Uses react-resizable-panels for user-resizable columns.
 */
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels';
import BottomStats   from '../BottomStats/BottomStats';
import CoverageMap   from '../CoverageMap/CoverageMap';
import CommandCenter from '../CommandCenter/CommandCenter';
import MissionLog    from '../MissionLog/MissionLog';
import './BottomDashboard.css';

export default function BottomDashboard() {
  return (
    <div className="bottom-dashboard">
      {/* TOP: Stats Charts Row */}
      <div className="bd-stats-row">
        <BottomStats />
      </div>

      {/* BOTTOM: Coverage | Command | Log */}
      <div className="bd-bottom-row">
        <PanelGroup direction="horizontal">
          <Panel defaultSize={22} minSize={16}>
            <CoverageMap />
          </Panel>

          <PanelResizeHandle className="bd-handle" />

          <Panel defaultSize={44} minSize={30}>
            <CommandCenter />
          </Panel>

          <PanelResizeHandle className="bd-handle" />

          <Panel defaultSize={34} minSize={20}>
            <MissionLog />
          </Panel>
        </PanelGroup>
      </div>
    </div>
  );
}
