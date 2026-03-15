@echo off
REM ============================================================
REM LinkedIn Auto Post - FINAL USER PROOF
REM ============================================================

echo.
echo ============================================================
echo LinkedIn Auto Post
echo ============================================================
echo.
echo [1/3] Closing Chrome...
taskkill /F /IM chrome.exe >nul 2>&1
taskkill /F /IM msedge.exe >nul 2>&1
timeout /t 2 /nobreak >nul
echo   Done
echo.

echo [2/3] Checking drafts...
if not exist "Pending_Approval\linkedin_post_*.md" (
    echo   ERROR: No drafts found!
    pause
    exit /b 1
)
echo   Found drafts - using first one
echo.

echo [3/3] Starting LinkedIn poster...
echo.
echo ============================================================
echo IMPORTANT INSTRUCTIONS:
echo ============================================================
echo 1. Browser will open
echo 2. If you see login page:
echo    - Login with your LinkedIn credentials
echo    - You have 3 minutes
echo    - After login, everything is automatic
echo 3. If already logged in:
echo    - Post will be created automatically
echo 4. Browser will stay open after posting
echo ============================================================
echo.
echo Starting in 3 seconds...
timeout /t 3 /nobreak >nul

python tools\li_auto.py

echo.
echo Done!
pause
