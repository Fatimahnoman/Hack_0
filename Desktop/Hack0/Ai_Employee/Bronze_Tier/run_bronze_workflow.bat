@echo off
echo ============================================================
echo   BRONZE TIER WORKFLOW - Complete Setup
echo ============================================================
echo.
echo This will start:
echo 1. File System Watcher (monitors Inbox)
echo 2. Ralph Wiggum Loop Processor (Claude Code simulation)
echo.
echo Press Ctrl+C to stop all processes
echo ============================================================
echo.

cd /d "%~dp0"

echo [1/2] Starting File System Watcher...
start "FileWatcher" python watchers\filesystem_watcher.py

timeout /t 3 /nobreak >nul

echo [2/2] Starting Ralph Wiggum Loop Processor...
start "RalphWiggumLoop" python bronze_tier_processor.py

echo.
echo ============================================================
echo   Both processes started!
echo ============================================================
echo.
echo Workflow:
echo   Inbox/ -^> Watcher -^> Needs_Action/ -^> Ralph Wiggum Loop -^> Done/
echo.
echo Check Dashboard.md for status updates
echo ============================================================
echo.
pause
