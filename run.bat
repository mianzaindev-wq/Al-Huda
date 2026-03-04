@echo off
:: Al-Huda Islamic AI Assistant - Launcher
:: Must be run from the project root (the folder containing app\, venv\, .env)

echo.
echo ============================================================
echo         Al-Huda Islamic AI Assistant v4.0
echo ============================================================
echo.

:: Verify venv exists
if not exist "venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found.
    echo         Please run setup.bat first.
    pause
    exit /b 1
)

echo [INFO]  Using venv Python...
echo [INFO]  Starting server at http://127.0.0.1:8000
echo [INFO]  Browser will open automatically in 4 seconds
echo [INFO]  Press CTRL+C to stop
echo.
echo ============================================================
echo.

:: Open browser after 4-second delay (runs in background while server starts)
start /b cmd /c "timeout /t 4 /nobreak >nul && start http://127.0.0.1:8000"

:: Always run from project root with the venv Python so package imports resolve
venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000

pause
