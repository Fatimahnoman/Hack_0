@echo off
REM ============================================================
REM LinkedIn Auto Poster - Production Ready
REM ============================================================
REM Fully automated LinkedIn posting
REM First run: Login manually, session saved for future runs
REM ============================================================

echo.
echo ============================================================
echo LinkedIn Auto Poster
echo ============================================================
echo.

REM Kill Chrome
echo [1/4] Closing Chrome...
taskkill /F /IM chrome.exe >nul 2>&1
taskkill /F /IM msedge.exe >nul 2>&1
timeout /t 2 /nobreak >nul
echo   Done

REM Check for drafts
echo [2/4] Checking drafts...
if not exist "Pending_Approval\linkedin_post_*.md" (
    echo   ERROR: No drafts found!
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
echo [3/4] Posting to LinkedIn...
echo.
echo IMPORTANT:
echo   - First run: You must login manually (2 min timeout)
echo   - Future runs: Auto-login with saved session
echo   - Browser will stay open after posting
echo.

python tools\linkedin_auto_poster.py --post "%DRAFT:Pending_Approval\=%"

echo.
echo [4/4] Done!
echo ============================================================
pause
