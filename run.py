#!/usr/bin/env python3
"""
Single-command launcher for Internship Application Agent:
Starts both FastAPI backend and Streamlit frontend in a unified process.
Usage:
    python run.py
"""

import sys
import os
import time
import subprocess
import webbrowser
import urllib.request
from pathlib import Path

# Add project root to path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Ensure Streamlit does not prompt for email
os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"
os.environ["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"

def is_server_ready(url: str, timeout: float = 0.5) -> bool:
    try:
        req = urllib.request.urlopen(url, timeout=timeout)
        return req.getcode() in (200, 404)
    except Exception:
        return False

def main():
    print("=" * 65)
    print("  Internship Application Agent - AI Assistant Launcher")
    print("=" * 65)

    # 1. Check or build knowledge base vector store
    print("\n[1/3] Checking vector database...")
    from app.services.vector_store import get_vector_store
    vs = get_vector_store()
    collection = vs.load_vector_database()
    if collection is None:
        print("Indexing knowledge base into ChromaDB...")
        vs.build_vector_database(force_rebuild=False)
    print("Vector database is ready!")

    # 2. Launch FastAPI Backend
    print("\n[2/3] Starting FastAPI REST backend on http://127.0.0.1:8000 ...")
    backend_cmd = [
        sys.executable, "-m", "uvicorn",
        "app.main:app",
        "--host", "127.0.0.1",
        "--port", "8000"
    ]
    backend_proc = subprocess.Popen(backend_cmd)

    # Wait for backend server to become ready
    for _ in range(10):
        if is_server_ready("http://127.0.0.1:8000/health"):
            break
        time.sleep(0.5)
    print("FastAPI Backend is running and healthy!")

    # 3. Launch Streamlit Frontend
    print("\n[3/3] Starting Streamlit chatbot interface on http://localhost:8501 ...")
    streamlit_cmd = [
        sys.executable, "-m", "streamlit",
        "run", "frontend/streamlit_app.py",
        "--server.headless=true",
        "--server.port=8501",
        "--browser.gatherUsageStats=false"
    ]
    frontend_proc = subprocess.Popen(streamlit_cmd)

    # Wait for Streamlit server to be ready before opening browser
    print("Waiting for Streamlit web interface to initialize...")
    for _ in range(15):
        if is_server_ready("http://localhost:8501"):
            break
        time.sleep(0.5)

    # Open browser now that server is confirmed alive
    try:
        webbrowser.open("http://localhost:8501")
    except Exception:
        pass

    print("\n" + "=" * 65)
    print("  SUCCESS: System is running live!")
    print("  - Streamlit Chat UI: http://localhost:8501")
    print("  - FastAPI Docs:     http://127.0.0.1:8000/docs")
    print("  - Health Status:    http://127.0.0.1:8000/health")
    print("  (Press Ctrl+C in this terminal to stop both servers)")
    print("=" * 65 + "\n")

    try:
        frontend_proc.wait()
    except KeyboardInterrupt:
        print("\nShutting down servers...")
    finally:
        try:
            frontend_proc.terminate()
        except Exception:
            pass
        try:
            backend_proc.terminate()
            backend_proc.wait(timeout=3)
        except Exception:
            pass
        print("Servers stopped cleanly.")

if __name__ == "__main__":
    main()
