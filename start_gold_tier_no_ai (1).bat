@echo off
REM ================================================================
REM GOLD TIER - WITHOUT AI (NO API KEY NEEDED)
REM ================================================================
REM This starts watchers WITHOUT Gold Orchestrator (legacy "no AI" layout).
REM For HITL (needs_action -^> pending_approval) use start_gold_tier.bat instead:
REM gold_orchestrator.py works without GEMINI_API_KEY (heuristic DRAFT_*.md fallback).
REM ================================================================

cd /d "%~dp0"
set PROJECT_ROOT=%~dp0
set PYTHON_CMD=python

echo.
echo ================================================================================
echo GOLD TIER - NO AI MODE (Bina API Key Ke)
echo ================================================================================
echo.
echo Starting components:
echo   1. Action Dispatcher  - Hands (executes approved actions)
echo   2. WhatsApp Watcher   - Eyes (WhatsApp Web)
echo   3. Gmail Watcher      - Eyes (Gmail API)
echo   4. LinkedIn Watcher   - Eyes (LinkedIn Feed)
echo   5. Twitter Watcher    - Eyes (Twitter scanner)
echo.
echo NOTE: Gold Orchestrator (AI Brain) skipped - needs Gemini API key
echo.
echo Starting in 3 seconds...
timeout /t 3 /nobreak >nul
echo.

REM 1. Action Dispatcher
echo [1/5] Starting Action Dispatcher...
start "Action Dispatcher" cmd /k "cd /d %PROJECT_ROOT% && echo === Action Dispatcher === && %PYTHON_CMD% silver\tools\action_dispatcher.py --daemon --interval 10"
timeout /t 2 /nobreak >nul

REM 2. WhatsApp Watcher
echo [2/5] Starting WhatsApp Watcher...
start "WhatsApp Watcher" cmd /k "cd /d %PROJECT_ROOT% && echo === WhatsApp Watcher === && %PYTHON_CMD% watchers\whatsapp_watcher_fixed.py"
timeout /t 2 /nobreak >nul

REM 3. Gmail Watcher
echo [3/5] Starting Gmail Watcher...
if exist "silver\watchers\gmail_watcher.py" (
    start "Gmail Watcher" cmd /k "cd /d %PROJECT_ROOT% && echo === Gmail Watcher === && %PYTHON_CMD% silver\watchers\gmail_watcher.py"
) else (
    echo [WARN] Gmail Watcher not found - skipping
)
timeout /t 2 /nobreak >nul

REM 4. LinkedIn Watcher
echo [4/5] Starting LinkedIn Watcher...
echo [INFO] Opening LinkedIn in browser...
start "LinkedIn Watcher" cmd /k "cd /d %PROJECT_ROOT% && echo === LinkedIn Watcher === && echo Opening LinkedIn... && %PYTHON_CMD% gold\watchers\linkedin_auto_poster.py --watch"
timeout /t 2 /nobreak >nul

REM 5. Twitter Watcher
echo [5/5] Starting Twitter Watcher...
if exist "watchers\twitter_watcher.py" (
    start "Twitter Watcher" cmd /k "cd /d %PROJECT_ROOT% && echo === Twitter Watcher === && %PYTHON_CMD% watchers\twitter_watcher.py"
) else (
    echo [WARN] Twitter Watcher not found - skipping
)
timeout /t 2 /nobreak >nul

echo.
echo ================================================================================
echo ALL COMPONENTS STARTED
echo ================================================================================
echo.
echo Check the opened windows for status
echo LinkedIn should be open in a browser window
echo.
echo Press any key to open logs folder...
pause >nul
explorer "%PROJECT_ROOT%gold\logs"
