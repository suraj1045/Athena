# Athena Project — Execution Guide (Windows)

Follow these steps to set up and run the Athena Urban Intelligence platform on your local machine.

## 1. Prerequisites
Ensure you have the following installed:
- **Docker Desktop**: For running PostgreSQL, Redis, and MinIO.
- **Python 3.11+**: For the backend and AI logic.
- **Node.js & npm**: For the React control dashboard.

---

## 2. Infrastructure Setup
Start the local FOSS services (Postgres, Redis, and MinIO) using Docker Compose.

1. Open a terminal in the project root.
2. Run:
   ```powershell
   docker-compose up -d
   ```
   *Note: Use `docker ps` to verify that the containers are running.*

---

## 3. Backend Setup
Set up the Python environment and install dependencies.

1. **Create a virtual environment**:
   ```powershell
   python -m venv .venv
   ```
2. **Activate the virtual environment**:
   ```powershell
   .venv\Scripts\Activate.ps1
   ```
3. **Install dependencies**:
   ```powershell
   # Core dependencies
   pip install -r requirements.txt
   # ML dependencies (YOLO, ANPR)
   pip install -r requirements-ml.txt
   # Dev dependencies (Ruff, Pytest)
   pip install -e ".[dev]"
   ```

---

## 4. Frontend Setup
Set up the React Control Dashboard.

1. Navigate to the dashboard directory:
   ```powershell
   cd dashboard/control-dashboard
   ```
2. **Install dependencies**:
   ```powershell
   npm install
   ```

---

## 5. Running the Project
You will need two separate terminal windows (with the backend venv activated in the first one).

### Terminal 1: Backend API
From the project root:
```powershell
uvicorn src.services.main:app --host 0.0.0.0 --port 8000 --reload
```
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)

### Terminal 2: Control Dashboard
From `dashboard/control-dashboard`:
```powershell
npm run dev
```
- **Login/View Dashboard**: Follow the local URL provided by Vite (usually [http://localhost:5173](http://localhost:5173)).

---

## 6. Simulating Mock Data
To see the dashboard in action with live-updating markers, run the population script while the backend and frontend are active.

1. Open a new terminal.
2. Activate the venv: `.venv\Scripts\Activate.ps1`.
3. Run:
   ```powershell
   python populate_dashboard.py
   ```
   This will register officers, tracked vehicles, and trigger mock alerts that appear instantly on your map!

---

## 💡 Alternative: All-in-One Demo Launcher
If you want to quickly see the project running with simplified HTML views without setting up Node.js for the dashboard:
```powershell
python run_demo.py
```
This serves the dashboard as static HTML on [http://localhost:3000](http://localhost:3000).
