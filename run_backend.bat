@echo off
cd /d "%~dp0backend"
echo ===================================================
echo Starting LPU Campus Assistant Backend...
echo API and Web App: http://localhost:8000
echo ===================================================
call .venv\Scripts\activate.bat
uvicorn app.main:app --reload --port 8000
pause
