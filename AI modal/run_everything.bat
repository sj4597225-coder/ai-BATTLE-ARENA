@echo off
echo Starting Backend Server...
start "Backend Server" cmd /k "python backend/app.py"
timeout /t 5

echo Starting Ngrok Tunnel...
echo Please ensure you have ngrok installed and authenticated.
start "Ngrok Tunnel" cmd /k "ngrok http 8000"

echo.
echo ========================================================
echo SYSTEM STARTED
echo 1. Backend is running in one window.
echo 2. Ngrok is running in another window.
echo.
echo COPY the URL from the Ngrok window (e.g. https://xyz.ngrok-free.app)
echo Then run: python verify_judgement.py
echo ========================================================
pause
