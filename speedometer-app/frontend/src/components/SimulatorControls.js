import React from 'react';

function SimulatorControls({ config, isRunning, onConfigChange, onStart, onStop }) {
  return (
    <>
      <h2>Simulator Controls</h2>
      
      <div className="control-group">
        <label>Base Speed (km/h): </label>
        <input 
          type="number" 
          name="baseSpeed"
          value={config.baseSpeed}
          onChange={onConfigChange}
          disabled={isRunning}
        />
      </div>
      
      <div className="control-group">
        <label>Speed Variation (km/h): </label>
        <input 
          type="number" 
          name="speedVariation"
          value={config.speedVariation}
          onChange={onConfigChange}
          disabled={isRunning}
        />
      </div>
      
      <div className="control-group">
        <label>Change Interval (s): </label>
        <input 
          type="number" 
          step="0.1"
          name="changeInterval"
          value={config.changeInterval}
          onChange={onConfigChange}
          disabled={isRunning}
        />
      </div>
      
      <div className="control-group">
        <label>Acceleration Factor: </label>
        <input 
          type="number" 
          step="0.05"
          name="accelerationFactor"
          value={config.accelerationFactor}
          onChange={onConfigChange}
          disabled={isRunning}
        />
      </div>
      
      {!isRunning ? (
        <button 
          className="simulator-button"
          style={{ backgroundColor: '#4CAF50' }}
          onClick={onStart}
        >
          Start Simulator
        </button>
      ) : (
        <button 
          className="simulator-button"
          style={{ backgroundColor: '#f44336' }}
          onClick={onStop}
        >
          Stop Simulator
        </button>
      )}
    </>
  );
}

export default SimulatorControls;