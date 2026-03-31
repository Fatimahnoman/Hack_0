@echo off
REM LinkedIn Watcher - Gold Tier - Start
REM =====================================
REM This script starts the LinkedIn Watcher in monitor mode.
REM It will open LinkedIn in a browser window and monitor for messages/notifications.

cd /d "%~dp0"

echo ============================================================
echo LINKEDIN WATCHER - GOLD TIER
echo ============================================================
echo.
echo This will:
echo   1. Launch Chrome with persistent session
echo   2. Navigate to LinkedIn
echo   3. Monitor for important messages and notifications
echo.
echo First time: Manual login required
echo Session saved to: session\linkedin\
echo.
echo Press Ctrl+C to stop
echo.
pause

python gold\watchers\linkedin_auto_poster.py --watch

pause
