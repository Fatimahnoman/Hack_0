@echo off
echo ============================================================
echo   GMAIL WATCHER - Test Run
echo ============================================================
echo.
echo This will test the Gmail Watcher setup
echo.
echo STEP 1: Check for credentials.json
echo STEP 2: If missing, show setup instructions
echo STEP 3: If exists, start the watcher
echo ============================================================
echo.

cd /d "%~dp0"

if not exist "credentials.json" (
    echo [ERROR] credentials.json NOT FOUND!
    echo.
    echo ============================================================
    echo   SETUP INSTRUCTIONS
    echo ============================================================
    echo.
    echo 1. Go to: https://console.cloud.google.com/
    echo 2. Create a new project or select existing
    echo 3. Enable Gmail API
    echo 4. Create OAuth 2.0 credentials (Desktop app)
    echo 5. Download credentials.json
    echo 6. Place it in: %CD%\credentials.json
    echo.
    echo ============================================================
    echo   AFTER ADDING CREDENTIALS
    echo ============================================================
    echo.
    echo Run authentication:
    echo   python gmail_auth.py
    echo.
    echo Then run watcher:
    echo   python Silver_Tier\watchers\gmail_watcher.py
    echo.
    echo ============================================================
    pause
    exit /b 1
)

echo [OK] credentials.json found!
echo.
echo Starting Gmail Watcher...
echo.
python Silver_Tier\watchers\gmail_watcher.py

if errorlevel 1 (
    echo.
    echo ============================================================
    echo   AUTHENTICATION ERROR
    echo ============================================================
    echo.
    echo Please run authentication first:
    echo   python gmail_auth.py
    echo.
    pause
)

pause
