@echo off
REM =============================================================================
REM GOLD TIER - START ALL WATCHERS (DEBUG VERSION)
REM =============================================================================
REM This version shows errors and keeps windows open for debugging
REM =============================================================================

cd /d "%~dp0"
set PROJECT_ROOT=%~dp0
set PYTHON_CMD=python

REM =============================================================================
REM CHECK PYTHON
REM =============================================================================

%PYTHON_CMD% --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found!
    pause
    exit /b 1
)

echo.
echo ================================================================================
echo GOLD TIER - STARTING (DEBUG MODE)
echo ================================================================================
echo.

REM =============================================================================
REM START COMPONENTS ONE BY ONE WITH DELAYS
REM =============================================================================

REM 1. Gold Orchestrator
echo [1/6] Starting Gold Orchestrator...
if exist "gold\tools\gold_orchestrator.py" (
    start "Gold Orchestrator" cmd /k "cd /d %PROJECT_ROOT% && echo === Gold Orchestrator === && echo Starting... && %PYTHON_CMD% gold\tools\gold_orchestrator.py"
    echo [OK] Gold Orchestrator started
    timeout /t 3 /nobreak >nul
) else (
    echo [ERROR] gold_orchestrator.py NOT FOUND!
)

REM 2. Action Dispatcher
echo [2/6] Starting Action Dispatcher...
if exist "silver\tools\action_dispatcher.py" (
    start "Action Dispatcher" cmd /k "cd /d %PROJECT_ROOT% && echo === Action Dispatcher === && echo Starting... && %PYTHON_CMD% silver\tools\action_dispatcher.py --daemon --interval 10"
    echo [OK] Action Dispatcher started
    timeout /t 3 /nobreak >nul
) else (
    echo [ERROR] action_dispatcher.py NOT FOUND!
)

REM 3. WhatsApp Watcher
echo [3/6] Starting WhatsApp Watcher...
if exist "watchers\whatsapp_watcher_fixed.py" (
    start "WhatsApp Watcher" cmd /k "cd /d %PROJECT_ROOT% && echo === WhatsApp Watcher === && echo Starting... && %PYTHON_CMD% watchers\whatsapp_watcher_fixed.py"
    echo [OK] WhatsApp Watcher started
    timeout /t 3 /nobreak >nul
) else (
    echo [ERROR] whatsapp_watcher_fixed.py NOT FOUND!
)

REM 4. Gmail Watcher
echo [4/6] Starting Gmail Watcher...
if exist "silver\watchers\gmail_watcher.py" (
    start "Gmail Watcher" cmd /k "cd /d %PROJECT_ROOT% && echo === Gmail Watcher === && echo Starting... && %PYTHON_CMD% silver\watchers\gmail_watcher.py"
    echo [OK] Gmail Watcher started
    timeout /t 3 /nobreak >nul
) else (
    echo [WARN] gmail_watcher.py NOT FOUND - Skipping
)

REM 5. LinkedIn Watcher
echo [5/6] Starting LinkedIn Watcher...
if exist "gold\watchers\linkedin_auto_poster.py" (
    start "LinkedIn Watcher" cmd /k "cd /d %PROJECT_ROOT% && echo === LinkedIn Watcher === && echo Starting... && echo LinkedIn will open in browser... && %PYTHON_CMD% gold\watchers\linkedin_auto_poster.py --watch"
    echo [OK] LinkedIn Watcher started
    timeout /t 3 /nobreak >nul
) else (
    echo [ERROR] linkedin_auto_poster.py NOT FOUND!
)

REM 6. Twitter Watcher
echo [6/6] Starting Twitter Watcher...
if exist "watchers\twitter_watcher.py" (
    start "Twitter Watcher" cmd /k "cd /d %PROJECT_ROOT% && echo === Twitter Watcher === && echo Starting... && %PYTHON_CMD% watchers\twitter_watcher.py"
    echo [OK] Twitter Watcher started
    timeout /t 3 /nobreak >nul
) else (
    echo [ERROR] twitter_watcher.py NOT FOUND!
)

REM =============================================================================
REM COMPLETE
REM =============================================================================

echo.
echo ================================================================================
echo ALL COMPONENTS STARTED
echo ================================================================================
echo.
echo Check the opened windows for status
echo Logs: gold\logs\
echo.
echo Press any key to open logs folder...
pause >nul
explorer "%PROJECT_ROOT%gold\logs"
