import React, { useState, useEffect, useRef } from 'react';
import SpeedDisplay from './components/SpeedDisplay';
import HistoryChart from './components/HistoryChart';
import SimulatorControls from './components/SimulatorControls';

function App() {
  const [history, setHistory] = useState([]);
  const [simulatorConfig, setSimulatorConfig] = useState({
    baseSpeed: 30,
    speedVariation: 20,
    changeInterval: 1,
    accelerationFactor: 0.2
  });
  const [isSimulatorRunning, setIsSimulatorRunning] = useState(false);
  const latestSpeed = useRef({ speed: 0, unit: 'km/h' });

  useEffect(() => {
    // Load initial history
    fetchHistory();
    
    // Check simulator status
    fetch('http://localhost:8000/simulator/status')
      .then(res => res.json())
      .then(data => setIsSimulatorRunning(data.status === 'running'));
  }, []);

  const fetchHistory = () => {
    fetch('http://localhost:8000/history?hours=24')
      .then(res => res.json())
      .then(data => setHistory(data));
  };

  const startSimulator = () => {
    fetch('http://localhost:8000/simulator/start', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(simulatorConfig)
    })
    .then(() => setIsSimulatorRunning(true));
  };

  const stopSimulator = () => {
    fetch('http://localhost:8000/simulator/stop', {
      method: 'POST'
    })
    .then(() => setIsSimulatorRunning(false));
  };

  const handleConfigChange = (e) => {
    const { name, value } = e.target;
    setSimulatorConfig(prev => ({
      ...prev,
      [name]: parseFloat(value)
    }));
  };

  const handleSpeedUpdate = (newSpeed) => {
    latestSpeed.current = newSpeed;
  };

  return (
    <div className="app-container">
      <h1>Speedometer App</h1>
      
      <SpeedDisplay 
        onSpeedUpdate={handleSpeedUpdate} 
        latestSpeed={latestSpeed.current} 
      />

      <div className="main-content">
        <div className="chart-container">
          <h2>Speed History (Last 24 Hours)</h2>
          <HistoryChart data={history} />
        </div>
        
        <div className="controls-container">
          <SimulatorControls 
            config={simulatorConfig}
            isRunning={isSimulatorRunning}
            onConfigChange={handleConfigChange}
            onStart={startSimulator}
            onStop={stopSimulator}
          />
        </div>
      </div>
    </div>
  );
}

export default App;