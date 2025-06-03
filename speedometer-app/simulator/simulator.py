import paho.mqtt.client as mqtt
import time
import json
import random
import signal
import sys
import os

# MQTT and simulation configuration
MQTT_BROKER = "mqtt"
MQTT_PORT = 1883
TOPIC = "sensors/speed"

# Simulation parameters (env var overrides)
BASE_SPEED = float(os.getenv("BASE_SPEED", 30.0))
SPEED_VARIATION = float(os.getenv("SPEED_VARIATION", 20.0))
CHANGE_INTERVAL = float(os.getenv("CHANGE_INTERVAL", 1.0))
ACCELERATION_FACTOR = float(os.getenv("ACCELERATION_FACTOR", 0.2))

class SpeedSimulator:
    """
    Simulates vehicle speed data and publishes to MQTT.
    Handles graceful shutdown on signals.
    """
    def __init__(self):
        """Initialize MQTT client and simulation state"""
        self.client = mqtt.Client("SpeedSimulator")
        self.running = False
        self.current_speed = BASE_SPEED
        self.target_speed = BASE_SPEED
        
        # Setup MQTT and signal handlers
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def on_connect(self, client, userdata, flags, rc):
        """MQTT connection callback"""
        print("Connected!" if rc == 0 else f"Connection failed: {rc}")
    
    def on_disconnect(self, client, userdata, rc):
        """MQTT disconnection callback"""
        print(f"Disconnected with code {rc}")
    
    def signal_handler(self, sig, frame):
        """Handle shutdown signals"""
        print("Shutting down...")
        self.running = False
        self.client.disconnect()
        sys.exit(0)
    
    def generate_new_target(self):
        """Generate random target speed within variation range"""
        return BASE_SPEED + random.uniform(-SPEED_VARIATION, SPEED_VARIATION)
    
    def run(self):
        """
        Main simulation loop:
        - Connects to MQTT
        - Continuously adjusts speed
        - Publishes data at intervals
        """
        self.client.connect(MQTT_BROKER, MQTT_PORT)
        self.client.loop_start()
        self.running = True
        
        print(f"Simulator started\nBase: {BASE_SPEED} km/h\nVariation: ±{SPEED_VARIATION} km/h")
        
        try:
            while self.running:
                # Occasionally update target speed
                if random.random() < 0.05:
                    self.target_speed = self.generate_new_target()
                
                # Smooth speed adjustment
                self.current_speed += (self.target_speed - self.current_speed) * ACCELERATION_FACTOR
                self.current_speed = max(0, self.current_speed + random.uniform(-1, 1))
                
                # Publish data
                payload = {
                    "device_id": "simulated_car",
                    "speed": round(self.current_speed, 1),
                    "unit": "km/h",
                    "timestamp": int(time.time())
                }
                self.client.publish(TOPIC, json.dumps(payload))
                print(f"Speed: {self.current_speed:.1f} km/h", end='\r')
                
                time.sleep(CHANGE_INTERVAL)
        
        except KeyboardInterrupt:
            self.running = False
            self.client.disconnect()

if __name__ == "__main__":
    SpeedSimulator().run()