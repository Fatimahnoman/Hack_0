@echo off
REM ================================================================
REM GOLD TIER - STOP ALL & RESTART
REM ================================================================

echo.
echo ================================================================
echo STOPPING ALL GOLD TIER COMPONENTS
echo ================================================================
echo.

echo Stopping Python processes...
taskkill /F /IM python.exe 2>nul
if errorlevel 1 (
    echo [INFO] No Python processes to stop
) else (
    echo [OK] Python processes stopped
)

timeout /t 2 /nobreak >nul

echo.
echo ================================================================
echo RESTARTING GOLD TIER
echo ================================================================
echo.
echo Starting fresh in 3 seconds...
timeout /t 3 /nobreak >nul

echo.
call start_gold_tier_debug.bat
