import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App.jsx';
import './styles/index.css';

import { MissionProvider } from './contexts/MissionContext';
import { DroneProvider } from './contexts/DroneContext';
import { TelemetryProvider } from './contexts/TelemetryContext';
import { SimulationProvider } from './contexts/SimulationContext';
import { ViewProvider } from './contexts/ViewContext';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <SimulationProvider>
        <ViewProvider>
          <MissionProvider>
            <DroneProvider>
              <TelemetryProvider>
                <App />
              </TelemetryProvider>
            </DroneProvider>
          </MissionProvider>
        </ViewProvider>
      </SimulationProvider>
    </BrowserRouter>
  </React.StrictMode>,
);
