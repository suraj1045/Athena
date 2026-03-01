from src.database.session import SessionLocal
from src.database.models import CriticalVehicleRecord, VehicleSightingRecord
from src.services.route_predictor import route_predictor
from datetime import datetime, UTC, timedelta

db = SessionLocal()

try:
    print("--- Athena Route Predictor Logic Test ---")
    
    # 1. Setup test vehicle
    plate = "TEST-ROUTE-1"
    vehicle = db.query(CriticalVehicleRecord).filter_by(license_plate=plate).first()
    if not vehicle:
        vehicle = CriticalVehicleRecord(
            license_plate=plate,
            make="Toyota",
            model="Camry",
            case_type="STOLEN",
            case_number="T-001",
            priority="HIGH",
            registered_by="Test",
            status="ACTIVE"
        )
        db.add(vehicle)
        db.commit()
        db.refresh(vehicle)
    
    # 2. Add test sightings
    # Moving North-East
    now = datetime.now(tz=UTC)
    sightings = [
        {"lat": 12.9716, "lon": 77.5946, "ts": now - timedelta(minutes=10)},
        {"lat": 12.9730, "lon": 77.5960, "ts": now - timedelta(minutes=5)},
        {"lat": 12.9750, "lon": 77.5980, "ts": now}
    ]
    
    # Clear old sightings for this test vehicle
    db.query(VehicleSightingRecord).filter_by(vehicle_id=vehicle.id).delete()
    
    for s in sightings:
        record = VehicleSightingRecord(
            vehicle_id=vehicle.id,
            camera_id="CAM-TEST",
            latitude=s["lat"],
            longitude=s["lon"],
            timestamp=s["ts"],
            confidence=1.0
        )
        db.add(record)
    db.commit()
    
    # 3. Predict!
    print(f"Predicting route for {vehicle.id}...")
    prediction = route_predictor.predict_route(db, vehicle.id, prediction_minutes=10)
    
    if prediction:
        print(f"✅ Route predicted successfully! Points: {len(prediction)}")
        print(f"First point: {prediction[0]}")
        print(f"Last point: {prediction[-1]}")
    else:
        print("❌ Prediction failed to return a route.")

finally:
    db.close()
