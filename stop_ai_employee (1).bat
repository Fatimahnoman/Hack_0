@echo off
REM ============================================================================
REM  AI Employee - Shutdown Script
REM  ============================================================================
REM  Stops all AI Employee components gracefully
REM
REM  Usage: stop_ai_employee.bat
REM ============================================================================

TITLE AI Employee - Stopping...
SET PROJECT_DIR=%~dp0

ECHO ============================================================================
ECHO   AI EMPLOYEE - SHUTDOWN SCRIPT
ECHO ============================================================================
ECHO.
ECHO   Stopping all components...
ECHO.

REM Stop PM2 processes (if running)
ECHO [1/4] Stopping PM2 watchers...
pm2 stop all >nul 2>nul
IF %ERRORLEVEL% EQU 0 (
    ECHO       ✓ PM2 watchers stopped
) ELSE (
    ECHO       - PM2 not running or not installed
)

REM Stop Docker containers
ECHO [2/4] Stopping Odoo Docker container...
docker-compose stop >nul 2>nul
IF %ERRORLEVEL% EQU 0 (
    ECHO       ✓ Odoo container stopped
) ELSE (
    ECHO       - Docker not running or not installed
)

REM Kill Python processes related to our scripts
ECHO [3/4] Stopping Python watchers...
TASKKILL /F /FI "WINDOWTITLE eq Gmail Watcher*" >nul 2>nul
TASKKILL /F /FI "WINDOWTITLE eq WhatsApp Watcher*" >nul 2>nul
TASKKILL /F /FI "WINDOWTITLE eq Ralph Loop*" >nul 2>nul
TASKKILL /F /FI "WINDOWTITLE eq Action Dispatcher*" >nul 2>nul
TASKKILL /F /FI "WINDOWTITLE eq Odoo Docker*" >nul 2>nul
ECHO       ✓ Python processes stopped

REM Kill any remaining Python processes in project
ECHO [4/4] Cleaning up...
FOR /F "tokens=2" %%i IN ('TASKLIST /FI "IMAGENAME eq python.exe" /FO CSV ^| FIND "python"') DO (
    TASKKILL /F /PID %%i >nul 2>nul
)
ECHO       ✓ Cleanup complete

ECHO.
ECHO ============================================================================
ECHO   ALL COMPONENTS STOPPED
ECHO ============================================================================
ECHO.
ECHO   You can restart anytime by running: start_ai_employee.bat
ECHO.
PAUSE
