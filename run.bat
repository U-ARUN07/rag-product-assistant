@echo off
echo ========================================================
echo Internship Application Agent - RAG Assistant
echo ========================================================

echo [1/3] Checking/building knowledge base vector store...
python scripts/build_knowledge_base.py

echo [2/3] Starting FastAPI backend on http://127.0.0.1:8000 ...
start "FastAPI Backend" cmd /k "uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

timeout /t 3 /nobreak >nul

echo [3/3] Starting Streamlit UI on http://localhost:8501 ...
start "Streamlit Frontend" cmd /k "streamlit run frontend/streamlit_app.py --server.port 8501"

echo ========================================================
echo System is running!
echo - Streamlit UI: http://localhost:8501
echo - FastAPI Docs: http://127.0.0.1:8000/docs
echo ========================================================
pause
