@echo off
title Viral Shorts AI - Bootstrapper
echo ====================================================
echo             Welcome to Viral Shorts AI
echo       Automated Local Installation & Setup
echo ====================================================
echo.

:: Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not added to your Windows PATH.
    echo Please install Python 3.10+ and run this script again.
    pause
    exit /b
)

:: Check for Node.js
node -v >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not installed or not added to PATH.
    echo Please install Node.js (LTS recommended) and run again.
    pause
    exit /b
)

echo [1/4] Configuring Python Backend environment...
cd backend
if not exist venv (
    echo Creating virtual env...
    python -m venv venv
)
call venv\Scripts\activate
echo Upgrading pip and installing requirements...
python -m pip install --upgrade pip
pip install -r requirements.txt
cd ..

echo.
echo [2/4] Configuring React Frontend package...
cd frontend
echo Installing npm dependencies...
call npm install
cd ..

echo.
echo [3/4] Configuring Electron Desktop shell...
cd desktop
echo Installing Electron runtime...
call npm install
cd ..

echo.
echo [4/4] Starting all services concurrently...
echo.
echo Launching Backend FastAPI server in background...
start "Viral Shorts AI - Backend API" cmd /c "cd backend && call venv\Scripts\activate && uvicorn app.main:app --port 8000 --reload"

echo.
echo Launching React frontend client...
start "Viral Shorts AI - Web Client" cmd /c "cd frontend && npm run dev"

echo.
echo Waiting 5 seconds for web client to boot up...
timeout /t 5 >nul

echo.
echo Launching Electron desktop window...
cd desktop
npm start

echo.
echo ====================================================
echo   All systems started successfully!
echo   Web dashboard: http://localhost:3000
echo   API endpoint:  http://localhost:8000
echo ====================================================
pause
