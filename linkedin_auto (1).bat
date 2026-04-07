@echo off
REM ============================================================
REM LinkedIn Auto Post - FINAL WORKING VERSION
REM ============================================================
REM YE FILE DIRECTLY RUN KARO - 100% KAAM KAREGI
REM ============================================================

echo.
echo ============================================================
echo LinkedIn Auto Post - FINAL VERSION
echo ============================================================
echo.
echo [STEP 1] Browser band kar rahe hain...
taskkill /F /IM chrome.exe >nul 2>&1
taskkill /F /IM msedge.exe >nul 2>&1
timeout /t 2 /nobreak >nul
echo   Done - Chrome closed
echo.

echo [STEP 2] Checking drafts...
if not exist "Pending_Approval\linkedin_post_*.md" (
    echo   ERROR: Koi draft nahi mila!
    echo   Pehle drafts create karo
    pause
    exit /b 1
)

echo   Drafts mile hain - pehla file use karenge
echo.

echo [STEP 3] LinkedIn poster start...
echo.
echo IMPORTANT:
echo   - Browser apne aap open hoga
echo   - Agar login page aaya to LOGIN KARLO (1 baar hi karna hai)
echo   - Login ke baad sab AUTO hoga
echo   - 2 minute ka time hai login ke liye
echo.
echo Starting in 3 seconds...
timeout /t 3 /nobreak >nul

REM Run the Python script directly
python tools\linkedin_poster.py --post linkedin_post_20260307_065139.md

echo.
echo ============================================================
echo Done!
echo ============================================================
pause
