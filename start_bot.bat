@echo off
REM ============================================================
REM  AI Service Bot — One-Click Launcher (Backend + Flutter Web)
REM  Double-click this file to start the bot.
REM ============================================================

set BACKEND_PORT=8000
set FLUTTER_PORT=8080
set SCRIPT_DIR=%~dp0
cd /d %SCRIPT_DIR%

REM Load .env file if it exists
if exist .env (
    echo Loading .env configuration...
    for /f "usebackq tokens=1,* delims==" %%a in (".env") do (
        set "line=%%a"
        if not "!line:~0,1!"=="#" (
            set "%%a=%%b"
        )
    )
)

REM Enable delayed expansion (needed for .env parsing)
setlocal enabledelayedexpansion

REM Re-load .env with delayed expansion
if exist .env (
    for /f "usebackq tokens=1,* delims==" %%a in (".env") do (
        set "line=%%a"
        if not "%%a"=="" if not "!line:~0,1!"=="#" (
            endlocal
            set "%%a=%%b"
            setlocal enabledelayedexpansion
        )
    )
)
endlocal

REM Check prerequisites
where python >NUL 2>&1 || (echo Error: python not found. Install Python 3.10+ from python.org & pause & exit /b 1)
where flutter >NUL 2>&1 || (echo Error: flutter not found. Install Flutter from flutter.dev & pause & exit /b 1)

REM Check for API key
if "%OPENAI_API_KEY%"=="" (
    echo.
    echo WARNING: OPENAI_API_KEY not set!
    echo The bot will start but cannot answer questions.
    echo Set it in the .env file or in Flutter Settings after startup.
    echo.
)

REM Install backend dependencies
echo Installing backend dependencies...
cd service_bot_backend
pip install -r requirements.txt --quiet
cd ..

REM Start backend in a new window
echo Starting backend on port %BACKEND_PORT%...
start "ServiceBot-Backend" cmd /c "cd service_bot_backend && python -m uvicorn main:app --host 0.0.0.0 --port %BACKEND_PORT%"

REM Wait for backend
echo Waiting for backend...
ping 127.0.0.1 -n 5 > NUL

REM Start Flutter
echo Starting Flutter web on port %FLUTTER_PORT%...
cd service_bot_flutter
flutter pub get
start "ServiceBot-Frontend" cmd /c "flutter run -d chrome --web-hostname=localhost --web-port=%FLUTTER_PORT% --dart-define=API_BASE_URL=http://localhost:%BACKEND_PORT%"

echo.
echo ============================================================
echo   Bot is running!
echo   Web UI:   http://localhost:%FLUTTER_PORT%
echo   API Docs: http://localhost:%BACKEND_PORT%/docs
echo   Close this window to stop the backend.
echo ============================================================
echo.
pause
