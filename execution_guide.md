# 🏛️ Athena — Full Feature Execution Guide (Windows)

This guide walks you through setting up and running **all** features of the Athena platform, including real-time incident detection, critical vehicle tracking, officer dispatch, and the new **Route Prediction** engine.

---

## 🏗️ 1. Infrastructure Setup
Athena requires a local FOSS stack. Ensure **Docker Desktop** is running.

1. Open a terminal in the project root.
2. Start the database, cache, and storage:
   ```powershell
   docker-compose up -d
   ```
   *Verify with `docker ps` that `athena_db`, `athena_redis`, and `athena_minio` are healthy.*

---

## 🐍 2. Backend & AI Setup
Set up the Python environment for the FastAPI engine and YOLO/ANPR models.

1. **Initialize Virtual Environment**:
   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```
2. **Install All Dependencies**:
   ```powershell
   # Core & Web
   pip install -r requirements.txt
   # AI Models (YOLOv8, EasyOCR)
   pip install -r requirements-ml.txt
   # Development tools
   pip install -e ".[dev]"
   ```

---

## ⚛️ 3. Control Dashboard Setup
Prepare the React-based Command Center.

1. Navigate to the dashboard:
   ```powershell
   cd dashboard/control-dashboard
   ```
2. **Install Packages**:
   ```powershell
   npm install
   ```

---

## 🚀 4. Running the Full System
You will need **three** terminal windows active.

### Terminal 1: The Athena Engine
From the project root (ensure venv is active):
```powershell
uvicorn src.services.main:app --host 0.0.0.0 --port 8000 --reload
```
- **API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)

### Terminal 2: The Command Center
From `dashboard/control-dashboard`:
```powershell
npm run dev
```
- **Live Map**: Open the URL provided by Vite (usually [http://localhost:5173](http://localhost:5173)).

### Terminal 3: Feature Demonstration (Mock Data)
Once the backend and frontend are running, use the simulation scripts to see the app in action:

1. **Populate Standard Data**:
   ```powershell
   python populate_dashboard.py
   ```
   *This spawns 3 police officers and registers critical vehicles. Watch them appear on the map!*

2. **Trigger Route Prediction (Step-by-Step)**:
   The predictive engine requires a history of movement for a **Critical Vehicle**. 
   
   **Step 1**: Ensure Terminal 1 (Backend) and Terminal 2 (Frontend) are running.
   **Step 2**: Open a new terminal and run the simulation script:
     ```powershell
     python simulate_vehicle.py
     ```
   **Step 3**: Refresh the Control Dashboard map ([http://localhost:5173](http://localhost:5173)).
   **Step 4**: Locate the red vehicle icon labeled **KA-05-PREDICT**.
   **Step 5**: Observe the **dashed line** extending forward. This is the OSRM-based prediction of where the vehicle will likely be in the next 10-15 minutes.

---

## 🎯 5. Core Features to Explore
- **🚦 Incident Detection**: Simulated incidents appear on the map. Use the "Clear" button in the dashboard to resolve them.
- **🚔 Officer Tracking**: Watch police units move in real-time as they report GPS updates.
- **🚗 Critical Watchlist**: Track specifically flagged vehicles across the city.
- **⚡ Proximity Alerts**: Look for intercept notifications when a suspect vehicle is near a police unit.
- **🔮 Route Prediction**: Observe the dashed "future path" lines that project where a vehicle is likely heading based on its speed and direction.

---

## 💡 All-in-One Quick Start (Legacy Mode)
If you don't want to set up Node.js, run the simplified Python demo:
```powershell
python run_demo.py
```
*This serves local HTML versions of the dashboard on port 3000.*
