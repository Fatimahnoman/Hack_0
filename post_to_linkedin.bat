@echo off
REM Auto LinkedIn Poster - Easy Runner
REM Just double-click this file to run

cd /d "%~dp0"

echo ============================================================
echo Auto LinkedIn Poster - Silver Tier
echo ============================================================
echo.

REM Find the latest LinkedIn post file
for %%f in (Pending_Approval\linkedin_post_*.md) do (
    set "LATEST_FILE=%%f"
    goto :found
)

echo [ERROR] No LinkedIn post files found in Pending_Approval folder!
echo.
pause
exit /b 1

:found
echo [INFO] Found file: %LATEST_FILE%
echo.
echo Starting LinkedIn poster...
echo.

python tools\auto_linkedin_poster.py --post "%LATEST_FILE%"

echo.
pause
