@echo off
REM =============================================================================
REM GOLD TIER - MASTER STARTUP (STABILIZED v12)
REM =============================================================================
REM Flow: needs_action (watchers) -> pending_approval (orchestrator + Gemini/fallback)
REM       -> you approve -> pending_approval/approved -> dispatcher -> done
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
REM SECTION 1: GOLD ORCHESTRATOR (Brain: needs_action -^> pending_approval)
REM Without this, WhatsApp/Gmail files never become HITL drafts.
REM -----------------------------------------------------------------------------
echo [1/6] Starting: Gold Orchestrator (needs_action -^> pending_approval)...
if exist "gold\tools\gold_orchestrator.py" (
    start "Gold Orchestrator" cmd /k "cd /d %PROJECT_ROOT% && title Gold Orchestrator && echo ---------------------------------------- && echo Gold Orchestrator: watches gold\needs_action && echo Creates DRAFT_*.md in gold\pending_approval && echo (Set GEMINI_API_KEY for AI; else heuristic fallback) && echo ---------------------------------------- && %PYTHON_CMD% gold\tools\gold_orchestrator.py"
    echo [OK] Gold Orchestrator launched.
) else (
    echo [ERROR] gold\tools\gold_orchestrator.py not found!
)
timeout /t 2 /nobreak >nul

REM -----------------------------------------------------------------------------
REM SECTION 2: LINKEDIN UNIFIED (Eyes + Hands) - PORT 9222
REM -----------------------------------------------------------------------------
echo [2/6] Starting: LinkedIn Unified (Gold Tier)...
if exist "gold\watchers\unified_linkedin_poster.py" (
    start "LinkedIn Unified" cmd /k "title LinkedIn Unified && echo ---------------------------------------- && echo Starting LinkedIn (Gold Tier)... && echo LinkedIn will open in browser shortly... && echo ---------------------------------------- && %PYTHON_CMD% gold\watchers\unified_linkedin_poster.py --watch"
    echo [OK] LinkedIn background process launched successfully.
) else (
    echo [ERROR] gold\watchers\unified_linkedin_poster.py not found!
)
timeout /t 3 /nobreak >nul

REM -----------------------------------------------------------------------------
REM SECTION 3: ACTION DISPATCHER (The Executor)
REM -----------------------------------------------------------------------------
echo [3/6] Starting: Action Dispatcher...
if exist "silver\tools\action_dispatcher.py" (
    start "Action Dispatcher" cmd /k "cd /d %PROJECT_ROOT% && title Action Dispatcher && echo Monitors gold\pending_approval\approved && %PYTHON_CMD% silver\tools\action_dispatcher.py --daemon --interval 10"
    echo [OK] Action Dispatcher launched successfully.
)
timeout /t 1 /nobreak >nul

REM -----------------------------------------------------------------------------
REM SECTION 4: WHATSAPP WATCHER (The Eyes) - PORT 9223
REM -----------------------------------------------------------------------------
echo [4/6] Starting: WhatsApp Watcher (Gold Tier)...
if exist "watchers\whatsapp_watcher_fixed.py" (
    start "WhatsApp Watcher" cmd /k "title WhatsApp Watcher && echo Starting WhatsApp... && %PYTHON_CMD% watchers\whatsapp_watcher_fixed.py"
    echo [OK] WhatsApp background process launched successfully.
)
timeout /t 2 /nobreak >nul

REM -----------------------------------------------------------------------------
REM SECTION 5: GMAIL WATCHER (API)
REM -----------------------------------------------------------------------------
echo [5/6] Starting: Gmail Watcher...
if exist "silver\watchers\gmail_watcher.py" (
    start "Gmail Watcher" cmd /k "cd /d %PROJECT_ROOT% && title Gmail Watcher && echo Gmail: credentials.json + token.json in project root && echo OAuth uses http://localhost:8090 - if browser does not open, use the URL printed below. && echo. && %PYTHON_CMD% silver\watchers\gmail_watcher.py"
    echo [OK] Gmail background process launched successfully.
)
timeout /t 1 /nobreak >nul

REM -----------------------------------------------------------------------------
REM SECTION 6: LIVE PIPELINE MONITOR (log tails)
REM -----------------------------------------------------------------------------
echo [6/6] Starting: Gold Pipeline Monitor (live logs)...
if exist "monitor_gold_pipeline.bat" (
    start "Gold Pipeline Monitor" cmd /k "cd /d %PROJECT_ROOT% && title Gold Pipeline Monitor && monitor_gold_pipeline.bat"
    echo [OK] Monitor window opened (refresh every 10s).
) else (
    echo [WARN] monitor_gold_pipeline.bat not found - skip
)

echo.
echo ================================================================================
echo GOLD TIER STARTUP COMPLETE
echo ================================================================================
echo.
echo   1) Gold Orchestrator  - needs_action -^> pending_approval (DRAFT files)
echo   2) LinkedIn Unified   - feed monitor / post
echo   3) Action Dispatcher  - approved -^> send/post -^> done
echo   4) WhatsApp Watcher   - drops tasks into needs_action
echo   5) Gmail Watcher      - drops tasks into needs_action
echo   6) Pipeline Monitor   - live whatsapp / orchestrator / dispatcher / sender logs
echo.
echo   HITL: Review DRAFT_*.md in gold\pending_approval, then move to approved\
echo.
echo   Logs: gold\logs\  (gold_orchestrator_YYYYMMDD.log)
echo   Or run: monitor_gold_pipeline.bat
echo.
echo ================================================================================
echo Press any key to finish and open logs folder...
pause >nul
explorer "%PROJECT_ROOT%gold\logs"
