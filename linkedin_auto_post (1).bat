@echo off
REM LinkedIn Auto Post - No prompts
REM Run this batch file directly

echo ============================================================
echo LinkedIn Auto Post
echo ============================================================
echo.

REM Kill Chrome
echo Closing Chrome...
taskkill /F /IM chrome.exe >nul 2>&1
taskkill /F /IM msedge.exe >nul 2>&1
timeout /t 2 /nobreak >nul

REM Clean session
echo Cleaning session...
rmdir /s /q "session\linkedin" 2>nul
timeout /t 1 /nobreak >nul
mkdir "session\linkedin"

echo.
echo Starting LinkedIn poster...
echo.
echo INSTRUCTIONS:
echo   1. Browser will open
echo   2. LOGIN to LinkedIn (you have 2 minutes)
echo   3. Click 'Start a post' button
echo   4. Script will auto-type and post
echo   5. Wait for confirmation
echo.
echo Starting in 3 seconds...
timeout /t 3 /nobreak >nul

python -c "import sys; sys.path.insert(0, '.'); from tools.linkedin_manual_post import main; main()"

echo.
echo Done!
pause
