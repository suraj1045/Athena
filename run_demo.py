"""
Athena MVP — Hackathon Demo Launcher

Since the environment lacks npm/Node.js for the React frontends,
this script launches the FastAPI backend and serves the zero-install
vanilla HTML dashboards on a simple Python HTTP server.

Usage:
  python run_demo.py
"""

import os
import subprocess
import sys
import threading
import time
import webbrowser
from http.server import SimpleHTTPRequestHandler, HTTPServer


def run_backend():
    print("🚀 Starting Athena Backend (FastAPI)...")
    subprocess.run(
        [sys.executable, "-m", "uvicorn", "src.services.main:app", "--host", "0.0.0.0", "--port", "8000"],
        env=os.environ.copy()
    )


def run_frontend():
    print("🌐 Starting Athena Frontend Server on port 3000...")
    # Change dir to where the HTML files are
    os.chdir(os.path.join(os.path.dirname(__file__), "dashboard"))
    
    class Handler(SimpleHTTPRequestHandler):
        def end_headers(self):
            # Disable caching for the demo
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            super().end_headers()

    httpd = HTTPServer(('0.0.0.0', 3000), Handler)
    httpd.serve_forever()


if __name__ == "__main__":
    # Ensure dependencies
    try:
        import uvicorn, fastapi, sqlalchemy, cv2, easyocr
    except ImportError as e:
        print(f"❌ Missing dependency: {e}. Please run: pip install -r requirements.txt (or check pyproject.toml)")
        sys.exit(1)

    # Launch threads
    threading.Thread(target=run_backend, daemon=True).start()
    threading.Thread(target=run_frontend, daemon=True).start()

    print("\n" + "="*50)
    print("✅ Athena MVP Services Started!")
    print("="*50)
    print("Backend API:       http://localhost:8000/docs")
    print("Control Dashboard: http://localhost:3000/control_dashboard_web.html")
    print("Officer App:       http://localhost:3000/officer_app_web.html")
    print("Press Ctrl+C to stop.\n")

    # Wait a second for servers to bind, then open Control Dashboard
    time.sleep(2)
    webbrowser.open("http://localhost:3000/control_dashboard_web.html")
    webbrowser.open("http://localhost:3000/officer_app_web.html")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down Athena...")
        sys.exit(0)
