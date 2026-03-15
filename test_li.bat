@echo off
echo.
echo ============================================================
echo LinkedIn Auto Post - FINAL TEST
echo ============================================================
echo.

REM Kill Chrome
echo Closing Chrome...
taskkill /F /IM chrome.exe >nul 2>&1
taskkill /F /IM msedge.exe >nul 2>&1
timeout /t 2 /nobreak >nul

REM Run
echo Starting LinkedIn poster...
echo.
python tools\li_post.py

echo.
echo Done!
pause
