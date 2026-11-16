#!/usr/bin/env python3
"""
Single-command launcher for Internship Application Agent:
Starts both FastAPI backend and Streamlit frontend in a unified process.
Usage:
    python run.py
"""

import sys
import time
import subprocess
import webbrowser
from pathlib import Path

# Add project root to path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

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

    # Allow backend server 2 seconds to initialize
    time.sleep(2)

    # 3. Launch Streamlit Frontend
    print("[3/3] Starting Streamlit chatbot interface on http://localhost:8501 ...")
    streamlit_cmd = [
        sys.executable, "-m", "streamlit",
        "run", "frontend/streamlit_app.py",
        "--server.port", "8501"
    ]

    try:
        # Open browser automatically
        webbrowser.open("http://localhost:8501")
        print("\n" + "=" * 65)
        print("  System running successfully!")
        print("  - Streamlit UI: http://localhost:8501")
        print("  - FastAPI Docs: http://127.0.0.1:8000/docs")
        print("  (Press Ctrl+C in this terminal to stop both servers)")
        print("=" * 65 + "\n")
        
        frontend_proc = subprocess.Popen(streamlit_cmd)
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
