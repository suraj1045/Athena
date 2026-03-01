import urllib.request
import json
import time
from datetime import datetime, UTC

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

def get(url):
    try:
        with urllib.request.urlopen(f"{API}{url}") as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"Failed GET {url}: {e}")

print("--- Athena Route Prediction Verification ---")

# 1. Register a critical vehicle
print("1. Registering suspicious vehicle KA-01-TRACE...")
vehicle = post("/api/v1/vehicles/critical", {
    "license_plate": "KA01TRACE",
    "make": "Tesla",
    "model": "Model S",
    "case_type": "STOLEN",
    "case_number": "TR-999",
    "priority": "CRITICAL",
    "registered_by": "Special Branch"
})
vehicle_id = vehicle["id"]

# 2. Simulate 3 sightings to create a trajectory
sightings = [
    {"lat": 12.9750, "lon": 77.5900},
    {"lat": 12.9752, "lon": 77.5950},
    {"lat": 12.9754, "lon": 77.6000}
]

print("2. Simulating vehicle movement for trajectory...")
import requests
for i, pos in enumerate(sightings):
    print(f"   Sighting {i+1}: {pos['lat']}, {pos['lon']}")
    # Use requests for multipart/form-data
    url = f"{API}/api/v1/ingest/frame?camera_id=CAM-VERIFY-{i}&latitude={pos['lat']}&longitude={pos['lon']}"
    with open("requirements.txt", "rb") as f: # just a dummy file
        files = {"file": ("dummy.jpg", f, "image/jpeg")}
        resp = requests.post(url, files=files)
        if resp.status_code != 202:
            print(f"   ⚠️ Frame ingestion failed: {resp.status_code} {resp.text}")
    
    time.sleep(1)

# 3. Check predicted route
print("3. Fetching predicted route...")
prediction = get(f"/api/v1/vehicles/critical/{vehicle_id}/predicted-route")

if prediction:
    print(f"✅ Success! Predicted route has {len(prediction)} points.")
    print(f"   First point: {prediction[0]}")
    print(f"   Last point:  {prediction[-1]}")
else:
    print("❌ Failure: No predicted route returned.")

print("\nFinished verification.")
