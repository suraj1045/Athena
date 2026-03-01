import urllib.request
import urllib.parse
import json
import time
import uuid

API_URL = "http://localhost:8000/api/v1"

def post_json(endpoint, data):
    req = urllib.request.Request(f"{API_URL}{endpoint}", method="POST")
    req.add_header('Content-Type', 'application/json')
    try:
        response = urllib.request.urlopen(req, data=json.dumps(data).encode('utf-8'))
        return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"Error posting to {endpoint}: {e}")
        return None

def put_json(endpoint, data):
    req = urllib.request.Request(f"{API_URL}{endpoint}", method="PUT")
    req.add_header('Content-Type', 'application/json')
    try:
        response = urllib.request.urlopen(req, data=json.dumps(data).encode('utf-8'))
        return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"Error putting to {endpoint}: {e}")
        return None

def get_json(endpoint):
    req = urllib.request.Request(f"{API_URL}{endpoint}", method="GET")
    try:
        response = urllib.request.urlopen(req)
        return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"Error getting from {endpoint}: {e}")
        return None

def main():
    print("🚀 --- Athena MVP Data Simulator ---")
    
    print("1. Registering Officer OFF-001 on duty...")
    put_json("/officers/OFF-001/location", {
        "latitude": 12.9716, "longitude": 77.5946, "heading": 90.0, "speed_mps": 15.0, "on_duty": True
    })
    
    time.sleep(1)
    print("2. Adding vehicles to the Critical Watchlist...")
    post_json("/vehicles/critical", {
        "license_plate": "KA-01-AB-1234", "make": "Honda", "model": "Civic",
        "case_type": "STOLEN", "case_number": "FIR-2026-001", "priority": "CRITICAL", "registered_by": "System"
    })
    post_json("/vehicles/critical", {
        "license_plate": "UP-32-CD-5678", "make": "Toyota", "model": "Innova",
        "case_type": "HIT_AND_RUN", "case_number": "FIR-2026-002", "priority": "HIGH", "registered_by": "System"
    })
    
    time.sleep(1)
    print("3. Adding a vehicle to the Violations Database...")
    post_json("/violations/vehicle", {
        "license_plate": "MH-12-EF-9012", "violation_type": "EXPIRED_PERMIT",
        "description": "Permit expired 3 months ago", "severity": "MEDIUM"
    })

    print("\n✅ Simulation Complete!")
    print("Check your dashboard again! You should see the officer registered on the map, and the watchlist updated.")
    print("\nNote: To trigger a live Intercept Alert on the screen, the system technically requires a real camera frame with a license plate to be uploaded to the `/api/v1/ingest/frame` endpoint, at which point the AI pipeline detects it and triggers the WebSocket alert.")

if __name__ == "__main__":
    main()
