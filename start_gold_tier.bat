@echo off
REM =============================================================================
REM GOLD TIER - MASTER STARTUP (STABILIZED v10)
REM =============================================================================

cd /d "%~dp0"
set PROJECT_ROOT=%~dp0
set PYTHON_CMD=python

title GOLD TIER - MASTER CONSOLE
color 0A

echo.
echo ================================================================================
echo GOLD TIER - INITIALIZING (CHROME FIXED)
echo ================================================================================
echo.

REM 1. FOLDER SETUP
if not exist "gold\logs" mkdir "gold\logs"
if not exist "gold\needs_action" mkdir "gold\needs_action"
if not exist "gold\pending_approval\approved" mkdir "gold\pending_approval\approved"

REM 2. STARTING COMPONENTS
echo [PROCESS] Launching autonomous components in separate windows...
echo.

REM -----------------------------------------------------------------------------
REM SECTION 1: LINKEDIN UNIFIED (Eyes + Hands) - PORT 9222
REM -----------------------------------------------------------------------------
echo [1/4] Starting: LinkedIn Unified (Gold Tier)...
if exist "gold\watchers\unified_linkedin_poster.py" (
    start "LinkedIn Unified" cmd /k "title LinkedIn Unified && echo ---------------------------------------- && echo Starting LinkedIn (Gold Tier)... && echo LinkedIn will open in browser shortly... && echo ---------------------------------------- && %PYTHON_CMD% gold\watchers\unified_linkedin_poster.py --watch"
    echo [OK] LinkedIn background process launched successfully.
) else (
    echo [ERROR] gold\watchers\unified_linkedin_poster.py not found!
)
timeout /t 3 /nobreak >nul

REM -----------------------------------------------------------------------------
REM SECTION 2: ACTION DISPATCHER (The Executor)
REM -----------------------------------------------------------------------------
echo [2/4] Starting: Action Dispatcher...
if exist "silver\tools\action_dispatcher.py" (
    start "Action Dispatcher" cmd /k "title Action Dispatcher && echo Starting Dispatcher... && %PYTHON_CMD% silver\tools\action_dispatcher.py --daemon --interval 10"
    echo [OK] Action Dispatcher launched successfully.
)
timeout /t 1 /nobreak >nul

REM -----------------------------------------------------------------------------
REM SECTION 3: WHATSAPP WATCHER (The Eyes) - PORT 9223
REM -----------------------------------------------------------------------------
echo [3/4] Starting: WhatsApp Watcher (Gold Tier)...
if exist "watchers\whatsapp_watcher_fixed.py" (
    start "WhatsApp Watcher" cmd /k "title WhatsApp Watcher && echo Starting WhatsApp... && %PYTHON_CMD% watchers\whatsapp_watcher_fixed.py"
    echo [OK] WhatsApp background process launched successfully.
)
timeout /t 2 /nobreak >nul

REM -----------------------------------------------------------------------------
REM SECTION 4: GMAIL WATCHER (API)
REM -----------------------------------------------------------------------------
echo [4/4] Starting: Gmail Watcher...
if exist "silver\watchers\gmail_watcher.py" (
    start "Gmail Watcher" cmd /k "title Gmail Watcher && echo Starting Gmail... && %PYTHON_CMD% silver\watchers\gmail_watcher.py"
    echo [OK] Gmail background process launched successfully.
)
timeout /t 1 /nobreak >nul

echo.
echo ================================================================================
echo GOLD TIER STARTUP COMPLETE
echo ================================================================================
echo.
echo ✓ All 4 windows should be open now.
echo ✓ Keep the Browser windows OPEN to maintain the session.
echo ✓ Logs: gold\logs\
echo.
echo ================================================================================
echo Press any key to finish and open logs folder...
pause >nul
explorer "%PROJECT_ROOT%gold\logs"
