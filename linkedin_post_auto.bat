@echo off
REM LinkedIn Auto Poster - Production
REM Fully automated - no manual intervention

echo ============================================================
echo LinkedIn Auto Poster - Production
echo ============================================================
echo.

REM Kill Chrome
echo [1/4] Closing Chrome...
taskkill /F /IM chrome.exe >nul 2>&1
taskkill /F /IM msedge.exe >nul 2>&1
timeout /t 2 /nobreak >nul
echo   Done

REM Clean session for fresh login
echo [2/4] Cleaning session...
rmdir /s /q "session\linkedin" 2>nul
timeout /t 1 /nobreak >nul
mkdir "session\linkedin"
echo   Done

REM Check for drafts
echo [3/4] Checking drafts...
if not exist "Pending_Approval\linkedin_post_*.md" (
    echo   ERROR: No drafts found in Pending_Approval!
    echo   Run: python tools\auto_linkedin_poster.py --scan
    pause
    exit /b 1
)

REM Get first draft
for %%f in (Pending_Approval\linkedin_post_*.md) do (
    set "DRAFT=%%f"
    goto :found
)

:found
echo   Using: %DRAFT%

REM Post
echo [4/4] Posting to LinkedIn...
echo.
python tools\linkedin_auto_poster.py --post "%DRAFT:Pending_Approval\=%"

echo.
echo ============================================================
echo Done!
echo ============================================================
pause
