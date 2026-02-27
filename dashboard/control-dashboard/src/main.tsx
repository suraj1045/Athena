/**
 * Athena Control Dashboard — Entry Point
 *
 * React web application for the central Dispatch / Command Center.
 * Displays a city-wide incident map, camera grid, and analytics.
 */

import React from 'react';
import ReactDOM from 'react-dom/client';

const App: React.FC = () => {
  return (
    <div style={{ 
      minHeight: '100vh', 
      backgroundColor: '#0D1117', 
      color: '#C9D1D9',
      fontFamily: "'Inter', system-ui, sans-serif" 
    }}>
      <header style={{
        padding: '16px 24px',
        borderBottom: '1px solid #21262D',
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
      }}>
        <h1 style={{ fontSize: '20px', color: '#58A6FF', margin: 0 }}>
          🏛️ ATHENA
        </h1>
        <span style={{ color: '#8B949E', fontSize: '14px' }}>
          Control Dashboard — Command Center
        </span>
      </header>

      <main style={{ 
        display: 'grid', 
        gridTemplateColumns: '1fr 1fr', 
        gap: '16px', 
        padding: '24px' 
      }}>
        <div style={panelStyle}>
          <h2 style={panelTitleStyle}>🗺️ City Incident Map</h2>
          <p style={{ color: '#8B949E' }}>Mapbox GL integration — live incident overlay</p>
        </div>
        <div style={panelStyle}>
          <h2 style={panelTitleStyle}>📹 Camera Health Grid</h2>
          <p style={{ color: '#8B949E' }}>Real-time status of all 150 camera feeds</p>
        </div>
        <div style={panelStyle}>
          <h2 style={panelTitleStyle}>🚨 Critical Vehicle Tracker</h2>
          <p style={{ color: '#8B949E' }}>Active watch-list with movement trails</p>
        </div>
        <div style={panelStyle}>
          <h2 style={panelTitleStyle}>📊 System Analytics</h2>
          <p style={{ color: '#8B949E' }}>Recharts-powered performance metrics</p>
        </div>
      </main>
    </div>
  );
};

const panelStyle: React.CSSProperties = {
  backgroundColor: '#161B22',
  borderRadius: '12px',
  padding: '20px',
  border: '1px solid #21262D',
  minHeight: '200px',
};

const panelTitleStyle: React.CSSProperties = {
  fontSize: '16px',
  color: '#E6EDF3',
  marginBottom: '8px',
};

const root = ReactDOM.createRoot(document.getElementById('root')!);
root.render(<App />);

export default App;
