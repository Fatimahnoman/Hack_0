@echo off
REM LinkedIn Watcher + Auto Poster - Silver Tier (Fixed)
REM Run: run_linkedin_watcher.bat

echo ============================================================
echo LinkedIn Watcher + Auto Poster - Silver Tier
echo ============================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.11+
    pause
    exit /b 1
)

REM Check if Playwright is installed
python -c "from playwright.sync_api import sync_playwright" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing Playwright...
    pip install playwright
    playwright install chromium
)

REM Run the watcher
echo [INFO] Starting LinkedIn Watcher...
echo.
python watchers\linkedin_watcher_fixed.py

pause
