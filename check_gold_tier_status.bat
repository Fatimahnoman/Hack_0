@echo off
REM ================================================================
REM GOLD TIER - STATUS CHECK
REM ================================================================

echo.
echo ================================================================
echo GOLD TIER - STATUS CHECK
echo ================================================================
echo.

REM Check Python processes
echo [1] Checking Python Processes...
tasklist | findstr python.exe
if errorlevel 1 (
    echo [!] No Python processes found
) else (
    echo [OK] Python processes running
)
echo.

REM Check Chrome processes
echo [2] Checking Chrome Processes...
tasklist | findstr chrome.exe >nul
if errorlevel 1 (
    echo [!] No Chrome processes found
) else (
    echo [OK] Chrome is running
)
echo.

REM Check CMD windows
echo [3] Checking CMD Windows...
tasklist | findstr cmd.exe >nul
if errorlevel 1 (
    echo [!] No CMD windows found
) else (
    echo [OK] CMD windows open
)
echo.

REM Check session folders
echo [4] Checking Session Folders...
if exist "session\linkedin" (
    echo [OK] LinkedIn session exists
) else (
    echo [!] LinkedIn session NOT found
)

if exist "session\whatsapp_chrome" (
    echo [OK] WhatsApp session exists
) else (
    echo [!] WhatsApp session NOT found
)
echo.

REM Check log files
echo [5] Checking Recent Logs...
dir /B gold\logs\*.log 2>nul | findstr /C:"linkedin" >nul
if errorlevel 1 (
    echo [!] No LinkedIn logs found
) else (
    echo [OK] LinkedIn logs exist
)

dir /B gold\logs\*.log 2>nul | findstr /C:"action" >nul
if errorlevel 1 (
    echo [!] No Action Dispatcher logs found
) else (
    echo [OK] Action Dispatcher logs exist
)
echo.

REM Check if scripts exist
echo [6] Checking Script Files...
if exist "gold\watchers\linkedin_auto_poster.py" (
    echo [OK] LinkedIn Auto Poster exists
) else (
    echo [!] LinkedIn Auto Poster NOT found
)

if exist "silver\tools\action_dispatcher.py" (
    echo [OK] Action Dispatcher exists
) else (
    echo [!] Action Dispatcher NOT found
)

if exist "watchers\whatsapp_watcher_fixed.py" (
    echo [OK] WhatsApp Watcher exists
) else (
    echo [!] WhatsApp Watcher NOT found
)
echo.

echo ================================================================
echo STATUS COMPLETE
echo ================================================================
echo.
echo If all checks are OK but you don't see windows:
echo   1. Check taskbar for minimized windows
echo   2. Press Alt+Tab to cycle through windows
echo   3. Run: start_gold_tier_debug.bat (for detailed view)
echo.
pause
