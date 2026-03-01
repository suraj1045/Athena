import urllib.request
import json
import time

API = "http://localhost:8000"

def request(url, method="GET", payload=None):
    data = json.dumps(payload).encode('utf-8') if payload else None
    req = urllib.request.Request(
        f"{API}{url}",
        data=data,
        method=method,
        headers={'Content-Type': 'application/json'} if data else {},
    )
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode('utf-8'))

print("--- Athena Route Prediction Simulator ---")

# 1. Register a vehicle as Critical
print("1. Registering suspicious vehicle KA-05-PREDICT...")
vehicle = request("/api/v1/vehicles/critical", method="POST", payload={
    "license_plate": "KA05PREDICT",
    "make": "Toyota",
    "model": "Innova",
    "case_type": "STOLEN",
    "case_number": "SIM-456",
    "priority": "CRITICAL",
    "registered_by": "System-Simulator"
})
vehicle_id = vehicle["id"]
print(f"   Vehicle ID: {vehicle_id}")

# 2. Simulate sightings moving along a road (MG Road area)
# These points create a clear trajectory for the predictor
sightings = [
    (12.9750, 77.5900),
    (12.9755, 77.5950),
    (12.9760, 77.6000),
    (12.9765, 77.6050),
]

print("2. Simulating vehicle movement (injecting 4 sightings)...")
for lat, lon in sightings:
    print(f"   [SIGHTING] Lat: {lat}, Lon: {lon}")
    # Hit the new simulation endpoint
    # Note: query parameters are appended to the URL
    request(f"/api/v1/test/simulate-sighting?vehicle_id={vehicle_id}&latitude={lat}&longitude={lon}", method="POST")
    time.sleep(1.0)

print("\n--- Simulation Complete ---")
print("Open the dashboard ([http://localhost:5173](http://localhost:5173)).")
print("You should see KA-05-PREDICT and its predicted path (dashed line) appearing.")
print("If the line doesn't appear, wait a few seconds or refresh the map.")
