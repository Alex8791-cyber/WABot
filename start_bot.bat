@echo off
REM Launch the AI Service Bot (backend + Flutter web frontend).
REM Ensure Python and Flutter are in your PATH.

set BACKEND_PORT=8000
set FLUTTER_PORT=8080
set SCRIPT_DIR=%~dp0
cd /d %SCRIPT_DIR%

REM Check prerequisites
where python >NUL 2>&1 || (echo Error: python not found & exit /b 1)
where flutter >NUL 2>&1 || (echo Error: flutter not found & exit /b 1)

REM Install backend dependencies
echo Installing backend dependencies...
cd service_bot_backend
pip install -r requirements.txt --quiet
cd ..

REM Start backend in a new window so we can track its PID
echo Starting backend on port %BACKEND_PORT%...
start "ServiceBot-Backend" /B cmd /c "cd service_bot_backend && python -m uvicorn main:app --host 0.0.0.0 --port %BACKEND_PORT%"

REM Wait for backend
echo Waiting for backend...
ping 127.0.0.1 -n 5 > NUL

REM Start Flutter
echo Starting Flutter web on port %FLUTTER_PORT%...
cd service_bot_flutter
flutter pub get
flutter run -d chrome --web-hostname=localhost --web-port=%FLUTTER_PORT% --dart-define=API_BASE_URL=http://localhost:%BACKEND_PORT%

REM Cleanup: kill the backend window
echo Stopping backend...
taskkill /FI "WINDOWTITLE eq ServiceBot-Backend" /F >NUL 2>&1
echo Done.
