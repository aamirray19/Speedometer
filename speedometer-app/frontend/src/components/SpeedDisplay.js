import React, { useState, useEffect } from 'react';

function SpeedDisplay({ onSpeedUpdate, latestSpeed }) {
  const [currentSpeed, setCurrentSpeed] = useState(latestSpeed);
  const [isRunning, setIsRunning] = useState(true);

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws');

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      const newSpeed = {
        speed: data.speed,
        unit: data.unit || 'km/h'
      };
      onSpeedUpdate(newSpeed);
      if (isRunning) {
        setCurrentSpeed(newSpeed);
      }
    };

    return () => {
      ws.close();
    };
  }, [isRunning, onSpeedUpdate]);

  const toggleRunning = () => {
    setIsRunning(prev => !prev);
    if (!isRunning) {
      setCurrentSpeed(latestSpeed);
    }
  };

  return (
    <div className="speed-display-container">
      <div className="speed-control">
        <button 
          className="control-button"
          style={{
            backgroundColor: isRunning ? '#f44336' : '#4CAF50'
          }}
          onClick={toggleRunning}
        >
          {isRunning ? 'Pause' : 'Resume'}
        </button>
      </div>
      
      <div style={{ 
        fontSize: '1rem',
        color: '#666',
        marginBottom: '5px'
      }}>
        {isRunning ? 'Live Speed' : 'Paused'}
      </div>
      
      <div className="speed-value" style={{
        color: isRunning ? '#000' : '#888'
      }}>
        {currentSpeed.speed.toFixed(1)} {currentSpeed.unit}
      </div>
      
      {!isRunning && (
        <div style={{
          fontSize: '0.8rem',
          color: '#888',
          marginTop: '5px'
        }}>
          Last recorded: {latestSpeed.speed.toFixed(1)} {latestSpeed.unit}
        </div>
      )}
    </div>
  );
}

export default SpeedDisplay;