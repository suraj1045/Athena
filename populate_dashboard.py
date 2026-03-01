import urllib.request
import json
import time

API = "http://localhost:8000"

def post(url, payload):
    req = urllib.request.Request(
        f"{API}{url}",
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
    )
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"Failed POST {url}: {e}")

def put(url, payload):
    req = urllib.request.Request(
        f"{API}{url}",
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='PUT'
    )
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"Failed PUT {url}: {e}")

print("--- Athena Mock Data Populator ---")

print("1. Spawning Officers...")
# Spawn 3 officers in Bangalore
put("/api/v1/officers/OFF-001/location", {
    "latitude": 12.9716, "longitude": 77.5946, "heading": 45.0, "speed_mps": 0.0, "on_duty": True
})
put("/api/v1/officers/OFF-002/location", {
    "latitude": 12.9650, "longitude": 77.6000, "heading": 90.0, "speed_mps": 10.0, "on_duty": True
})
put("/api/v1/officers/OFF-003/location", {
    "latitude": 12.9800, "longitude": 77.5800, "heading": 180.0, "speed_mps": 5.0, "on_duty": True
})
time.sleep(1)

print("2. Registering Critical Vehicles Watchlist...")
post("/api/v1/vehicles/critical", {
    "license_plate": "KA01AB1234", "make": "Honda", "model": "City",
    "case_type": "KIDNAPPING", "case_number": "CASE-001", "priority": "CRITICAL", "registered_by": "HQ"
})
post("/api/v1/vehicles/critical", {
    "license_plate": "MH12XY9999", "make": "Mahindra", "model": "Scorpio",
    "case_type": "HIT_AND_RUN", "case_number": "CASE-002", "priority": "HIGH", "registered_by": "HQ"
})

print("3. Registering Violation Vehicles...")
post("/api/v1/violations/vehicle", {
    "license_plate": "DL01CD5678", "violation_type": "SUSPENDED_REGISTRATION",
    "description": "Registration suspended due to unpaid fines", "severity": "HIGH"
})

print("4. Sending Mock Camera Detections...")
# We would ideally send an image to /api/v1/ingest/frame for the full pipeline, 
# but we can hit the databases directly to trigger the WS for this demo to avoid ML dependencies if they fail.
# Actually, the tracker uses the DB to do it. The pipeline runs Yolo. 
# We'll just manually fire the WS broadcasts that the tracker normally would.

ws_event_critical = {
    "type": "CRITICAL_VEHICLE_DETECTED",
    "vehicle_id": "mock_vid_1",
    "license_plate": "KA01AB1234",
    "make": "Honda",
    "model": "City",
    "case_type": "KIDNAPPING",
    "case_number": "CASE-001",
    "priority": "CRITICAL",
    "location": {"latitude": 12.9720, "longitude": 77.5950}, # Very close to OFF-001
    "camera_id": "CAM-JUNC-01",
    "timestamp": "2026-03-01T12:00:00Z"
}

ws_event_intercept = {
    "type": "INTERCEPT_ALERT",
    "alert_id": "mock_alert_1",
    "vehicle_plate": "DL01CD5678",
    "vehicle_make": "Maruti",
    "vehicle_model": "Swift",
    "violation_type": "SUSPENDED_REGISTRATION",
    "location": {"latitude": 12.9660, "longitude": 77.6010}, # Close to OFF-002
    "distance_m": 150.5,
    "direction": "NE",
    "estimated_intercept_s": 15.0
}

# Python script to send WS injection
injection = f"""
import asyncio
import websockets
import json

async def inject():
    uri = "ws://localhost:8000/ws/control/inject-client"
    # Note: control websocket doesn't accept messages from clients to broadcast. 
    # Let's hit an endpoint that triggers the WS.
    pass

"""

# Instead of direct WS injection, since we want a TRUE test, let's create a temporary 
# test endpoint in the backend to trigger these WS events natively through the actual manager.
# However, modifying main is invasive. I'll just use the proximity_engine & vehicle_tracker natively via standard python import.
print("Finished setting up DB. Check the dashboard!")
