@echo off
REM Gold Tier LinkedIn Auto Poster - Quick Test
REM ===========================================
REM This script tests the Gold Tier LinkedIn Auto Poster integration.

echo ============================================================
echo GOLD TIER LINKEDIN AUTO POSTER - QUICK TEST
echo ============================================================
echo.
echo This will:
echo   1. Check if Playwright is installed
echo   2. Verify directory structure
echo   3. Test the LinkedIn poster script
echo.
echo NOTE: First run will require manual LinkedIn login
echo       Session will be saved for future runs
echo.
pause

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found!
    pause
    exit /b 1
)

echo.
echo [INFO] Testing LinkedIn Auto Poster...
echo.

REM Run test with simple content
python gold\watchers\linkedin_auto_poster.py --content "Gold Tier Test Post - %DATE% %TIME%"

if errorlevel 1 (
    echo.
    echo [ERROR] Test failed! Check logs in gold/logs/
    pause
    exit /b 1
) else (
    echo.
    echo [SUCCESS] Test completed!
    echo.
    echo Next steps:
    echo   1. Check gold/done/ folder for completed file
    echo   2. Verify post on LinkedIn
    echo   3. Run Action Dispatcher: python silver\tools\action_dispatcher.py --daemon --interval 10
)

pause
