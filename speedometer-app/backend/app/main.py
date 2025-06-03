import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import psycopg2
import paho.mqtt.client as mqtt
import json
import asyncio
from typing import List
from dotenv import load_dotenv

# Load env vars
load_dotenv()

# Init FastAPI app
app = FastAPI(title="Speedometer Backend", version="1.0.0")

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db_connection():
    """Create and return DB connection using env vars"""
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "db"),
        database=os.getenv("DB_NAME", "speeddb"),
        user=os.getenv("DB_USER", "speeduser"),
        password=os.getenv("DB_PASS", "speedpass")
    )

def init_db():
    """Initialize database tables and indexes"""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS speed_data (
                id SERIAL PRIMARY KEY,
                device_id VARCHAR(50),
                speed FLOAT,
                unit VARCHAR(10) DEFAULT 'km/h',
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_timestamp ON speed_data(timestamp);
        """)
        conn.commit()
    except Exception as e:
        print(f"DB init error: {e}")
    finally:
        if conn:
            conn.close()

# Data models
class SpeedData(BaseModel):
    """Speed data model"""
    device_id: str
    speed: float
    unit: str = "km/h"

class SimulatorConfig(BaseModel):
    """Simulator config model"""
    base_speed: float = 30.0
    speed_variation: float = 20.0
    change_interval: float = 1.0
    acceleration_factor: float = 0.2

class ConnectionManager:
    """Manage WebSocket connections"""
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """Add new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        """Remove disconnected WebSocket"""
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        """Send message to all active connections"""
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                print(f"WS error: {e}")
                self.disconnect(connection)

manager = ConnectionManager()

def on_mqtt_connect(client, userdata, flags, rc):
    """MQTT connection callback - subscribe to topic"""
    if rc == 0:
        print("Connected to MQTT!")
        client.subscribe("sensors/speed")
    else:
        print(f"MQTT connection failed: {rc}")

def on_mqtt_message(client, userdata, msg):
    """Process incoming MQTT messages"""
    try:
        data = json.loads(msg.payload.decode())
        if not all(k in data for k in ["device_id", "speed"]):
            raise ValueError("Invalid message")
        
        # Store in DB
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO speed_data (device_id, speed, unit) VALUES (%s, %s, %s)",
            (data.get("device_id"), data.get("speed"), data.get("unit", "km/h"))
        )
        conn.commit()
        
        # Broadcast via WS
        asyncio.run(manager.broadcast(json.dumps({
            "device_id": data["device_id"],
            "speed": data["speed"],
            "unit": data.get("unit", "km/h"),
            "timestamp": data.get("timestamp")
        })))
        
    except Exception as e:
        print(f"MQTT error: {e}")
    finally:
        if 'conn' in locals():
            cur.close()
            conn.close()

mqtt_client = mqtt.Client("speedometer_backend")
mqtt_client.on_connect = on_mqtt_connect
mqtt_client.on_message = on_mqtt_message

# App lifecycle events
@app.on_event("startup")
async def startup_event():
    """Initialize app on startup"""
    init_db()
    try:
        mqtt_client.connect(
            os.getenv("MQTT_BROKER", "mqtt"),
            int(os.getenv("MQTT_PORT", 1883)),
            60
        )
        mqtt_client.loop_start()
    except Exception as e:
        print(f"MQTT error: {e}")

@app.on_event("shutdown")
def shutdown_event():
    """Cleanup on shutdown"""
    mqtt_client.loop_stop()
    mqtt_client.disconnect()

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Handle WebSocket connections"""
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # Keep connection alive
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# REST endpoints
@app.post("/speed", response_model=SpeedData)
async def post_speed(speed_data: SpeedData):
    """Submit speed data"""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO speed_data (device_id, speed, unit) VALUES (%s, %s, %s) RETURNING id",
            (speed_data.device_id, speed_data.speed, speed_data.unit)
        )
        conn.commit()
        return speed_data
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        if conn:
            cur.close()
            conn.close()

@app.get("/current", response_model=SpeedData)
async def get_current_speed():
    """Get latest speed data"""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT device_id, speed, unit 
            FROM speed_data 
            ORDER BY timestamp DESC 
            LIMIT 1
        """)
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="No data")
        return {
            "device_id": row[0],
            "speed": row[1],
            "unit": row[2]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            cur.close()
            conn.close()

@app.get("/history")
async def get_history(hours: int = 24, limit: int = 1000):
    """Get historical speed data"""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT device_id, speed, unit, timestamp 
            FROM speed_data 
            WHERE timestamp > NOW() - INTERVAL '%s HOURS'
            ORDER BY timestamp DESC
            LIMIT %s
        """, (hours, limit))
        rows = cur.fetchall()
        return [{
            "device_id": row[0],
            "speed": row[1],
            "unit": row[2],
            "timestamp": row[3].isoformat()
        } for row in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            cur.close()
            conn.close()

# Simulator endpoints
@app.post("/simulator/start")
async def start_simulator(config: SimulatorConfig):
    """Start simulator with config"""
    print(f"Starting simulator: {config.dict()}")
    return {"status": "started", "config": config.dict()}

@app.post("/simulator/stop")
async def stop_simulator():
    """Stop simulator"""
    print("Stopping simulator")
    return {"status": "stopped"}

@app.get("/simulator/status")
async def get_simulator_status():
    """Get simulator status"""
    return {"status": "running"}

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}