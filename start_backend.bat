@echo off
REM ============================================================
REM  AI Service Bot — Backend Only (for WhatsApp / API usage)
REM  Double-click this file to start just the backend.
REM ============================================================

set SCRIPT_DIR=%~dp0
cd /d %SCRIPT_DIR%

REM Load .env file if it exists
if exist .env (
    echo Loading .env configuration...
    for /f "usebackq tokens=1,* delims==" %%a in (".env") do (
        set "line=%%a"
        if not "%%a"=="" if not "!line:~0,1!"=="#" (
            set "%%a=%%b"
        )
    )
)

REM Check prerequisites
where python >NUL 2>&1 || (echo Error: python not found. Install Python 3.10+ from python.org & pause & exit /b 1)

if "%OPENAI_API_KEY%"=="" (
    echo WARNING: OPENAI_API_KEY not set! Set it in .env
)

echo Installing dependencies...
cd service_bot_backend
pip install -r requirements.txt --quiet

echo.
echo Starting backend on http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo Press Ctrl+C to stop.
echo.

python -m uvicorn main:app --host 0.0.0.0 --port 8000
pause
