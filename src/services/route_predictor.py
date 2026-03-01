"""
Athena — Route Predictor Service

Predicts the future path of a suspect vehicle based on historical sighting data.
Uses linear extrapolation for trajectory and OSRM (Open Source Routing Machine) 
for road-snapped route generation.
"""

from __future__ import annotations

import logging
import math
from datetime import datetime, timedelta
from typing import Any

import requests
from sqlalchemy.orm import Session
from sqlalchemy import desc

from src.database.models import VehicleSightingRecord
from src.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

OSRM_BASE_URL = "https://router.project-osrm.org/route/v1/driving"

class RoutePredictor:
    """Predicts future routes based on vehicle sighting history."""

    def predict_route(
        self, 
        db: Session, 
        vehicle_id: str, 
        prediction_minutes: int = 5
    ) -> list[dict[str, float]]:
        """
        Calculates a predicted route for a vehicle.
        1. Fetches recent sightings.
        2. Estimates current heading and velocity.
        3. Extrapolates a target destination.
        4. Fetches a road-snapped route from OSRM from current location to target.
        """
        # 1. Get last 5 sightings to estimate trajectory
        sightings = (
            db.query(VehicleSightingRecord)
            .filter(VehicleSightingRecord.vehicle_id == vehicle_id)
            .order_by(desc(VehicleSightingRecord.timestamp))
            .limit(5)
            .all()
        )

        if len(sightings) < 2:
            logger.info(f"Insufficient sightings for vehicle {vehicle_id} to predict route.")
            return []

        # Most recent sighting is our starting point
        current = sightings[0]
        previous = sightings[1]

        # 2. Simple trajectory estimation
        lat1, lon1 = previous.latitude, previous.longitude
        lat2, lon2 = current.latitude, current.longitude
        
        # Time delta in seconds
        dt = (current.timestamp - previous.timestamp).total_seconds()
        if dt <= 0:
            dt = 1.0 # Avoid division by zero

        # Approximate distance (Degrees to km - very rough for small distances)
        # 1 degree lat ~ 111km
        # 1 degree lon ~ 111km * cos(lat)
        d_lat = lat2 - lat1
        d_lon = lon2 - lon1
        
        # Velocity in degrees per second
        v_lat = d_lat / dt
        v_lon = d_lon / dt

        # 3. Extrapolate target location (e.g., where will they be in X minutes?)
        extrapolate_s = prediction_minutes * 60
        target_lat = lat2 + (v_lat * extrapolate_s)
        target_lon = lon2 + (v_lon * extrapolate_s)

        # 4. Fetch road-snapped route from OSRM
        # Format: {lon},{lat};{lon},{lat}
        coordinates = f"{lon2},{lat2};{target_lon},{target_lat}"
        url = f"{OSRM_BASE_URL}/{coordinates}?overview=full&geometries=polyline"
        
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get("routes"):
                    # For simplicity in the dashboard, we'll return the steps or coordinates
                    # OSRM returns encoded polyline or simple geometry. 
                    # Let's request 'geojson' for easier parsing in React.
                    geojson_url = f"{OSRM_BASE_URL}/{coordinates}?overview=full&geometries=geojson"
                    geo_response = requests.get(geojson_url, timeout=5)
                    if geo_response.status_code == 200:
                        geo_data = geo_response.json()
                        coords = geo_data["routes"][0]["geometry"]["coordinates"]
                        # Convert [lon, lat] pairs from GeoJSON to {lat, lng} for Leaflet
                        return [{"lat": c[1], "lng": c[0]} for c in coords]
            
            logger.warning(f"OSRM Route API returned error: {response.status_code}")
        except Exception as e:
            logger.error(f"Error calling OSRM API: {e}")

        # Fallback: simple line if OSRM fails
        return [
            {"lat": lat2, "lng": lon2},
            {"lat": target_lat, "lng": target_lon}
        ]

# Global singleton
route_predictor = RoutePredictor()
