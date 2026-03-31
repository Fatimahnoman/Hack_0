@echo off
ECHO ============================================================================
ECHO   STOPPING ALL AI EMPLOYEE COMPONENTS
ECHO ============================================================================
ECHO.
ECHO [1] Stopping Python processes...
taskkill /F /IM python.exe /T 2>nul
ECHO [2] Stopping Playwright browser processes...
powershell -Command "Get-Process chrome -ErrorAction SilentlyContinue | Where-Object { $_.Path -like '*playwright*' } | Stop-Process -Force" 2>nul
ECHO.
ECHO ============================================================================
ECHO   ALL COMPONENTS STOPPED SUCCESSFULLY!
ECHO ============================================================================
TIMEOUT /T 3
