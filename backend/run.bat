@echo off
cd /d "%~dp0"

if not exist "venv\Scripts\python.exe" (
    echo Creating virtual environment...
    python -m venv venv
    venv\Scripts\python.exe -m pip install -r requirements.txt
)

REM If port 8000 is taken, stop the old backend first
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000" ^| findstr "LISTENING"') do (
    echo Port 8000 busy - stopping old process PID %%a ...
    taskkill /F /PID %%a >nul 2>&1
    timeout /t 3 /nobreak >nul
)

echo Starting backend on http://localhost:8000
venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
pause
