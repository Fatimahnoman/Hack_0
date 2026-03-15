@echo off
echo ============================================================
echo LinkedIn Auto Poster - Quick Post
echo ============================================================
echo.

REM Kill Chrome
echo [1/3] Closing Chrome...
taskkill /F /IM chrome.exe >nul 2>&1
taskkill /F /IM msedge.exe >nul 2>&1
timeout /t 2 /nobreak >nul

REM Clean session
echo [2/3] Cleaning session folder...
rmdir /s /q "session\linkedin" 2>nul
timeout /t 1 /nobreak >nul
mkdir "session\linkedin"

echo [3/3] Starting LinkedIn poster...
echo.
echo IMPORTANT:
echo   - Browser will open FRESH (you need to LOGIN)
echo   - After login, post will be auto-typed and posted
echo   - Browser will stay open for verification
echo.
echo Starting in 3 seconds...
timeout /t 3 /nobreak >nul

REM Run poster with first draft
python tools\auto_linkedin_poster.py --post linkedin_post_20260307_065139.md

pause
