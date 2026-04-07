@echo off
REM ================================================================
REM LINKEDIN WATCHER - START (DIRECT)
REM ================================================================
REM This directly opens LinkedIn in a visible browser window
REM ================================================================

cd /d "%~dp0"

echo.
echo ================================================================
echo LINKEDIN WATCHER - STARTING
echo ================================================================
echo.
echo This will open LinkedIn in a browser window...
echo First time: Manual login required
echo Session saved to: session\linkedin\
echo.
echo Browser opening in 3 seconds...
timeout /t 3 /nobreak >nul

python gold\watchers\linkedin_auto_poster.py --watch

if errorlevel 1 (
    echo.
    echo [ERROR] LinkedIn Watcher failed!
    echo Check logs in: gold\logs\
    pause
)
