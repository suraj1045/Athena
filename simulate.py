"""
Athena — City Simulation Script

Generates synthetic camera events to demo the full Athena pipeline
without real CCTV feeds. Simulates:
  - Random traffic incidents (stalled vehicles, accidents, breakdowns)
  - Officers moving around the city
  - Violation vehicle intercept alerts
  - Critical vehicle sightings

Usage:
  python simulate.py                        # Bangalore, normal speed
  python simulate.py --city Mumbai          # Mumbai feed
  python simulate.py --city Delhi --fast    # Delhi, compressed for demos
  python simulate.py --city Chennai --seed-only  # Seed only, no loop

Available cities:
  Bangalore, Mumbai, Delhi, Chennai, Hyderabad,
  Kolkata, Pune, Ahmedabad, Jaipur, Kochi

Requires the backend to be running: python run_demo.py
"""

import argparse
import random
import signal
import sys
import time
from datetime import datetime

import requests

# ── Config ────────────────────────────────────────────────────────────────────

API = "http://localhost:8000"

INCIDENT_TYPES   = ["STALLED_VEHICLE", "BREAKDOWN", "ACCIDENT", "PEDESTRIAN_VIOLATION"]
INCIDENT_WEIGHTS = [0.40,              0.30,         0.20,       0.10]

# ── City Definitions ──────────────────────────────────────────────────────────

CITIES = {
    "Bangalore": {
        "lat": 12.9716, "lng": 77.5946, "spread": 0.05,
        "state_code": "KA",
        "cameras": [
            "CAM-MG-ROAD-01", "CAM-INDIRANAGAR-02", "CAM-KORAMANGALA-03",
            "CAM-WHITEFIELD-04", "CAM-JAYANAGAR-05", "CAM-HEBBAL-06",
            "CAM-MARATHAHALLI-07", "CAM-ELECTRONIC-CITY-08",
        ],
        "officers": [
            {"id": "OFF-001", "name": "Officer Rajan",  "lat": 12.9716, "lng": 77.5946},
            {"id": "OFF-002", "name": "Officer Priya",  "lat": 12.9780, "lng": 77.6080},
            {"id": "OFF-003", "name": "Officer Kiran",  "lat": 12.9650, "lng": 77.5850},
        ],
        "violation_plates": ["KA01BX2244", "KA05HG9921", "KA09ZZ3310"],
    },
    "Mumbai": {
        "lat": 19.0760, "lng": 72.8777, "spread": 0.06,
        "state_code": "MH",
        "cameras": [
            "CAM-MARINE-DRIVE-01", "CAM-BANDRA-02", "CAM-ANDHERI-03",
            "CAM-KURLA-04", "CAM-COLABA-05", "CAM-DADAR-06",
            "CAM-BORIVALI-07", "CAM-THANE-08",
        ],
        "officers": [
            {"id": "OFF-001", "name": "Officer Desai",  "lat": 19.0760, "lng": 72.8777},
            {"id": "OFF-002", "name": "Officer Patil",  "lat": 19.0820, "lng": 72.8840},
            {"id": "OFF-003", "name": "Officer Mehta",  "lat": 19.0700, "lng": 72.8700},
        ],
        "violation_plates": ["MH04YZ5567", "MH12AB3390", "MH01CD7788"],
    },
    "Delhi": {
        "lat": 28.6139, "lng": 77.2090, "spread": 0.07,
        "state_code": "DL",
        "cameras": [
            "CAM-CP-01", "CAM-KAROL-BAGH-02", "CAM-LAJPAT-NAGAR-03",
            "CAM-ROHINI-04", "CAM-DWARKA-05", "CAM-SAKET-06",
            "CAM-NOIDA-BORDER-07", "CAM-GURGAON-BORDER-08",
        ],
        "officers": [
            {"id": "OFF-001", "name": "Officer Sharma",  "lat": 28.6139, "lng": 77.2090},
            {"id": "OFF-002", "name": "Officer Singh",   "lat": 28.6200, "lng": 77.2150},
            {"id": "OFF-003", "name": "Officer Verma",   "lat": 28.6050, "lng": 77.2000},
        ],
        "violation_plates": ["DL01AA1234", "DL05CC9900", "DL08EE4421"],
    },
    "Chennai": {
        "lat": 13.0827, "lng": 80.2707, "spread": 0.05,
        "state_code": "TN",
        "cameras": [
            "CAM-ANNA-NAGAR-01", "CAM-T-NAGAR-02", "CAM-ADYAR-03",
            "CAM-VELACHERY-04", "CAM-PORUR-05", "CAM-PERAMBUR-06",
            "CAM-TAMBARAM-07", "CAM-SHOLINGANALLUR-08",
        ],
        "officers": [
            {"id": "OFF-001", "name": "Officer Murugan", "lat": 13.0827, "lng": 80.2707},
            {"id": "OFF-002", "name": "Officer Ravi",    "lat": 13.0900, "lng": 80.2800},
            {"id": "OFF-003", "name": "Officer Priya",   "lat": 13.0750, "lng": 80.2600},
        ],
        "violation_plates": ["TN09CD8801", "TN22EF1234", "TN07GH5566"],
    },
    "Hyderabad": {
        "lat": 17.3850, "lng": 78.4867, "spread": 0.05,
        "state_code": "TS",
        "cameras": [
            "CAM-HITECH-CITY-01", "CAM-BANJARA-HILLS-02", "CAM-SECUNDERABAD-03",
            "CAM-LB-NAGAR-04", "CAM-KUKATPALLY-05", "CAM-GACHIBOWLI-06",
            "CAM-MADHAPUR-07", "CAM-UPPAL-08",
        ],
        "officers": [
            {"id": "OFF-001", "name": "Officer Reddy",   "lat": 17.3850, "lng": 78.4867},
            {"id": "OFF-002", "name": "Officer Rao",     "lat": 17.3920, "lng": 78.4940},
            {"id": "OFF-003", "name": "Officer Kumar",   "lat": 17.3780, "lng": 78.4790},
        ],
        "violation_plates": ["TS09AB1122", "TS07CD3344", "TS11EF5566"],
    },
    "Kolkata": {
        "lat": 22.5726, "lng": 88.3639, "spread": 0.05,
        "state_code": "WB",
        "cameras": [
            "CAM-PARK-STREET-01", "CAM-HOWRAH-02", "CAM-SALT-LAKE-03",
            "CAM-ESPLANADE-04", "CAM-NEW-TOWN-05", "CAM-DUMDUM-06",
            "CAM-TOLLYGUNGE-07", "CAM-BEHALA-08",
        ],
        "officers": [
            {"id": "OFF-001", "name": "Officer Banerjee", "lat": 22.5726, "lng": 88.3639},
            {"id": "OFF-002", "name": "Officer Das",      "lat": 22.5800, "lng": 88.3700},
            {"id": "OFF-003", "name": "Officer Ghosh",    "lat": 22.5650, "lng": 88.3560},
        ],
        "violation_plates": ["WB01AB2233", "WB06CD5544", "WB14EF7788"],
    },
    "Pune": {
        "lat": 18.5204, "lng": 73.8567, "spread": 0.05,
        "state_code": "MH",
        "cameras": [
            "CAM-KOREGAON-PARK-01", "CAM-HINJEWADI-02", "CAM-SHIVAJINAGAR-03",
            "CAM-KOTHRUD-04", "CAM-HADAPSAR-05", "CAM-AUNDH-06",
            "CAM-WAKAD-07", "CAM-VIMAN-NAGAR-08",
        ],
        "officers": [
            {"id": "OFF-001", "name": "Officer Kulkarni", "lat": 18.5204, "lng": 73.8567},
            {"id": "OFF-002", "name": "Officer Joshi",    "lat": 18.5270, "lng": 73.8630},
            {"id": "OFF-003", "name": "Officer Patil",    "lat": 18.5130, "lng": 73.8490},
        ],
        "violation_plates": ["MH12PQ1122", "MH14RS3344", "MH20TU5566"],
    },
    "Ahmedabad": {
        "lat": 23.0225, "lng": 72.5714, "spread": 0.05,
        "state_code": "GJ",
        "cameras": [
            "CAM-SG-HIGHWAY-01", "CAM-CG-ROAD-02", "CAM-NAVRANGPURA-03",
            "CAM-BODAKDEV-04", "CAM-MANINAGAR-05", "CAM-VASTRAPUR-06",
            "CAM-SATELLITE-07", "CAM-BOPAL-08",
        ],
        "officers": [
            {"id": "OFF-001", "name": "Officer Patel",  "lat": 23.0225, "lng": 72.5714},
            {"id": "OFF-002", "name": "Officer Shah",   "lat": 23.0290, "lng": 72.5780},
            {"id": "OFF-003", "name": "Officer Modi",   "lat": 23.0160, "lng": 72.5640},
        ],
        "violation_plates": ["GJ01AA1234", "GJ05BB5678", "GJ18CC9900"],
    },
    "Jaipur": {
        "lat": 26.9124, "lng": 75.7873, "spread": 0.05,
        "state_code": "RJ",
        "cameras": [
            "CAM-MI-ROAD-01", "CAM-VAISHALI-NAGAR-02", "CAM-MALVIYA-NAGAR-03",
            "CAM-TONK-ROAD-04", "CAM-MANSAROVAR-05", "CAM-CIVIL-LINES-06",
            "CAM-SANGANER-07", "CAM-VIDYADHAR-NAGAR-08",
        ],
        "officers": [
            {"id": "OFF-001", "name": "Officer Meena",  "lat": 26.9124, "lng": 75.7873},
            {"id": "OFF-002", "name": "Officer Gupta",  "lat": 26.9190, "lng": 75.7940},
            {"id": "OFF-003", "name": "Officer Sharma", "lat": 26.9050, "lng": 75.7800},
        ],
        "violation_plates": ["RJ14AB1234", "RJ45CD5678", "RJ01EF9900"],
    },
    "Kochi": {
        "lat":  9.9312, "lng": 76.2673, "spread": 0.04,
        "state_code": "KL",
        "cameras": [
            "CAM-MG-ROAD-KOCHI-01", "CAM-EDAPPALLY-02", "CAM-KAKKANAD-03",
            "CAM-FORT-KOCHI-04", "CAM-ALUVA-05", "CAM-VYTTILA-06",
            "CAM-KALOOR-07", "CAM-THRIPPUNITHURA-08",
        ],
        "officers": [
            {"id": "OFF-001", "name": "Officer Nair",    "lat":  9.9312, "lng": 76.2673},
            {"id": "OFF-002", "name": "Officer Menon",   "lat":  9.9380, "lng": 76.2740},
            {"id": "OFF-003", "name": "Officer Pillai",  "lat":  9.9240, "lng": 76.2600},
        ],
        "violation_plates": ["KL07AB1234", "KL39CD5678", "KL01EF9900"],
    },
}

CRITICAL_VEHICLES = [
    {
        "license_plate": "KA03MJ4721",
        "make": "Maruti", "model": "Swift",
        "case_type": "KIDNAPPING", "case_number": "KID-2026-0041",
        "priority": "CRITICAL", "registered_by": "Inspector Sharma",
    },
    {
        "license_plate": "MH12AB3390",
        "make": "Honda", "model": "City",
        "case_type": "HIT_AND_RUN", "case_number": "HTR-2026-0112",
        "priority": "HIGH", "registered_by": "Inspector Nair",
    },
    {
        "license_plate": "TN09CD8801",
        "make": "Toyota", "model": "Innova",
        "case_type": "STOLEN", "case_number": "STL-2026-0078",
        "priority": "HIGH", "registered_by": "Inspector Gupta",
    },
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def rand_location(city: dict) -> tuple:
    return (
        city["lat"] + random.uniform(-city["spread"], city["spread"]),
        city["lng"] + random.uniform(-city["spread"], city["spread"]),
    )


def log(tag: str, msg: str) -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    colours = {
        "INCIDENT": "\033[91m", "OFFICER": "\033[94m", "INTERCEPT": "\033[93m",
        "CRITICAL": "\033[95m", "SEED": "\033[92m", "ERROR": "\033[90m",
    }
    col = colours.get(tag, "")
    print(f"  {col}[{ts}] [{tag}]\033[0m {msg}")


def post(path: str, payload: dict) -> dict | None:
    try:
        r = requests.post(f"{API}{path}", json=payload, timeout=5)
        if r.status_code in (200, 201):
            return r.json()
        log("ERROR", f"POST {path} → {r.status_code}: {r.text[:80]}")
    except requests.exceptions.ConnectionError:
        log("ERROR", f"Backend not reachable at {API}. Is it running?")
    except Exception as e:
        log("ERROR", str(e))
    return None


def put(path: str, payload: dict) -> bool:
    try:
        r = requests.put(f"{API}{path}", json=payload, timeout=5)
        return r.status_code in (200, 201)
    except Exception:
        return False


# ── Simulation phases ─────────────────────────────────────────────────────────

def seed_data(city_name: str, city: dict) -> None:
    print(f"\n\033[1m  ── Seeding data for {city_name} ──\033[0m")

    for v in CRITICAL_VEHICLES:
        result = post("/api/v1/vehicles/critical", v)
        if result:
            log("SEED", f"Critical vehicle: {v['license_plate']} ({v['case_type']})")
        time.sleep(0.3)

    violation_vehicles = [
        {
            "license_plate": plate,
            "violation_type": random.choice(["EXPIRED_PERMIT", "UNPAID_FINE", "SUSPENDED_REGISTRATION"]),
            "description": f"Violation registered in {city_name}",
            "severity": random.choice(["LOW", "MEDIUM", "HIGH"]),
        }
        for plate in city["violation_plates"]
    ]
    for v in violation_vehicles:
        result = post("/api/v1/violations/vehicle", v)
        if result:
            log("SEED", f"Violation vehicle: {v['license_plate']} ({v['violation_type']})")
        time.sleep(0.3)

    for o in city["officers"]:
        ok = put(f"/api/v1/officers/{o['id']}/location", {
            "latitude": o["lat"], "longitude": o["lng"],
            "heading": random.uniform(0, 360), "speed_mps": 0.0, "on_duty": True,
        })
        if ok:
            log("SEED", f"Officer online: {o['id']} ({o['name']}) in {city_name}")
        time.sleep(0.3)

    print()


def simulate_incident(city_name: str, city: dict) -> None:
    inc_type = random.choices(INCIDENT_TYPES, weights=INCIDENT_WEIGHTS)[0]
    lat, lng = rand_location(city)
    cam = random.choice(city["cameras"])
    payload = {
        "type": inc_type,
        "latitude": lat,
        "longitude": lng,
        "camera_id": cam,
        "confidence": round(random.uniform(0.82, 0.99), 2),
        "city": city_name,
    }
    result = post("/api/v1/simulate/incident", payload)
    if result:
        log("INCIDENT", f"[{city_name}] {inc_type.replace('_', ' ')} @ {lat:.4f},{lng:.4f} "
                        f"[{cam}] conf={payload['confidence']:.0%}")


def simulate_officer_movement(city_name: str, city: dict) -> None:
    for o in city["officers"]:
        o["lat"] += random.uniform(-0.002, 0.002)
        o["lng"] += random.uniform(-0.002, 0.002)
        put(f"/api/v1/officers/{o['id']}/location", {
            "latitude": o["lat"], "longitude": o["lng"],
            "heading": random.uniform(0, 360),
            "speed_mps": round(random.uniform(0, 12), 1),
            "on_duty": True,
        })
    log("OFFICER", f"[{city_name}] Updated {len(city['officers'])} officer locations")


def simulate_intercept(city_name: str, city: dict) -> None:
    officer = random.choice(city["officers"])
    plate = random.choice(city["violation_plates"])
    lat, lng = rand_location(city)
    directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    payload = {
        "officer_id": officer["id"],
        "vehicle_plate": plate,
        "vehicle_make": random.choice(["Toyota", "Maruti", "Honda", "Hyundai", "Tata"]),
        "vehicle_model": random.choice(["Swift", "Innova", "City", "i20", "Nexon"]),
        "violation_type": random.choice(["EXPIRED_PERMIT", "UNPAID_FINE", "SUSPENDED_REGISTRATION"]),
        "latitude": lat,
        "longitude": lng,
        "distance_m": round(random.uniform(80, 490), 1),
        "direction": random.choice(directions),
        "estimated_intercept_s": round(random.uniform(15, 120), 0),
    }
    result = post("/api/v1/simulate/intercept", payload)
    if result:
        log("INTERCEPT", f"[{city_name}] {plate} → {officer['id']} "
                         f"({payload['distance_m']}m {payload['direction']}, "
                         f"ETA {payload['estimated_intercept_s']:.0f}s)")


def simulate_critical_sighting(city_name: str, city: dict) -> None:
    vehicle = random.choice(CRITICAL_VEHICLES)
    lat, lng = rand_location(city)
    cam = random.choice(city["cameras"])
    log("CRITICAL", f"[{city_name}] SIGHTING: {vehicle['license_plate']} "
                    f"({vehicle['case_type']}) @ {lat:.4f},{lng:.4f} [{cam}]")


# ── Main loop ─────────────────────────────────────────────────────────────────

def run(city_name: str, city: dict, fast: bool = False) -> None:
    scale = 0.15 if fast else 1.0
    tick = 0
    print(f"\033[1m  ── Simulation running for {city_name} (Ctrl+C to stop) ──\033[0m\n")

    while True:
        tick += 1
        simulate_incident(city_name, city)
        if tick % 2 == 0:
            simulate_officer_movement(city_name, city)
        if tick % 5 == 0:
            simulate_intercept(city_name, city)
        if tick % 10 == 0:
            simulate_critical_sighting(city_name, city)
        time.sleep(10 * scale)


def check_backend() -> bool:
    try:
        r = requests.get(f"{API}/health", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Athena City Simulator")
    parser.add_argument(
        "--city", default="Bangalore",
        choices=list(CITIES.keys()),
        help="Indian city to simulate (default: Bangalore)",
    )
    parser.add_argument("--fast",      action="store_true", help="Compressed intervals for live demos")
    parser.add_argument("--seed-only", action="store_true", help="Seed data then exit")
    args = parser.parse_args()

    city_name = args.city
    city = CITIES[city_name]

    print("\n\033[1m\033[94m  ╔═══════════════════════════════════╗")
    print("  ║  🏛️  ATHENA CITY SIMULATOR        ║")
    print("  ╚═══════════════════════════════════╝\033[0m")
    print(f"  Target: {API}")
    print(f"  City:   {city_name}, India ({city['lat']}, {city['lng']})")
    print(f"  Cams:   {len(city['cameras'])} cameras")
    print(f"  Mode:   {'FAST' if args.fast else 'NORMAL'}\n")

    if not check_backend():
        print(f"\033[91m  ✗ Backend not reachable at {API}")
        print("    Run 'python run_demo.py' first.\033[0m\n")
        sys.exit(1)

    print(f"  \033[92m✓ Backend connected\033[0m\n")

    def _handle_exit(sig, frame):
        print("\n\n  Simulation stopped.\n")
        sys.exit(0)

    signal.signal(signal.SIGINT, _handle_exit)

    seed_data(city_name, city)

    if args.seed_only:
        print("  Seed complete.\n")
        return

    run(city_name, city, fast=args.fast)


if __name__ == "__main__":
    main()
