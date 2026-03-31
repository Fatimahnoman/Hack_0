@echo off
REM ============================================================================
REM  AI Employee - Master Startup Script
REM  ============================================================================
REM  Starts all components for 24/7 autonomous operation:
REM  - Watchers (Gmail, WhatsApp, Twitter, LinkedIn) - The Eyes
REM  - Odoo Docker Container - Business ERP
REM  - Gold Orchestrator (The Brain) - Reasoning engine
REM  - Action Dispatcher (The Hands) - Executes approved actions
REM
REM  Usage: start_ai_employee.bat
REM  Stop: Press Ctrl+C in each window, or run: stop_ai_employee.bat
REM ============================================================================

TITLE AI Employee - Starting...
SET PROJECT_DIR=%~dp0
SET PYTHON_CMD=python
SET LOG_DIR=%PROJECT_DIR%Logs

REM Create log directory if not exists
IF NOT EXIST "%LOG_DIR%" MKDIR "%LOG_DIR%"

ECHO ============================================================================
ECHO   AI EMPLOYEE - MASTER STARTUP SCRIPT
ECHO   Personal AI Employee - Silver/Gold Tier
ECHO ============================================================================
ECHO.
ECHO   Project Directory: %PROJECT_DIR%
ECHO   Log Directory: %LOG_DIR%
ECHO.
ECHO   Starting components:
ECHO   [1] Gmail Watcher (The Eyes - Email)
ECHO   [2] WhatsApp Watcher (The Eyes - Messages)
ECHO   [3] Twitter Watcher (The Eyes - Social Media)
ECHO   [4] LinkedIn Watcher (The Eyes - Networking)
ECHO   [5] Odoo Docker Container (Business ERP)
ECHO   [6] Gold Orchestrator (The Brain - Reasoning Engine)
ECHO   [7] Action Dispatcher (The Hands - Execution)
ECHO.
ECHO ============================================================================
ECHO.

REM Check if Python is available
WHERE %PYTHON_CMD% >nul 2>nul
IF %ERRORLEVEL% NEQ 0 (
    ECHO [ERROR] Python not found in PATH!
    ECHO Please install Python 3.11+ and add to PATH
    PAUSE
    EXIT /B 1
)

ECHO [INFO] Python found: %PYTHON_CMD%
%PYTHON_CMD% --version
ECHO.

REM ============================================================================
REM  COMPONENT 1: Gmail Watcher
REM ============================================================================
ECHO [1/7] Starting Gmail Watcher...
START "Gmail Watcher" cmd /k "CD /D %PROJECT_DIR% && ECHO Starting Gmail Watcher... && %PYTHON_CMD% watchers\gmail_watcher_browser.py"
TIMEOUT /T 3 /NOBREAK >nul

REM ============================================================================
REM  COMPONENT 2: WhatsApp Watcher
REM ============================================================================
ECHO [2/7] Starting WhatsApp Watcher...
START "WhatsApp Watcher" cmd /k "CD /D %PROJECT_DIR% && ECHO Starting WhatsApp Watcher... && %PYTHON_CMD% watchers\whatsapp_watcher_fixed.py"
TIMEOUT /T 3 /NOBREAK >nul

REM ============================================================================
REM  COMPONENT 3: Twitter Watcher
REM ============================================================================
ECHO [3/7] Starting Twitter Watcher...
START "Twitter Watcher" cmd /k "CD /D %PROJECT_DIR% && ECHO Starting Twitter Watcher... && %PYTHON_CMD% watchers\twitter_watcher.py"
TIMEOUT /T 3 /NOBREAK >nul

REM ============================================================================
REM  COMPONENT 4: LinkedIn Watcher
REM ============================================================================
ECHO [4/7] Starting LinkedIn Watcher...
START "LinkedIn Watcher" cmd /k "CD /D %PROJECT_DIR% && ECHO Starting LinkedIn Watcher... && %PYTHON_CMD% watchers\linkedin_watcher_fixed.py"
TIMEOUT /T 3 /NOBREAK >nul

REM ============================================================================
REM  COMPONENT 5: Odoo Docker Container
REM ============================================================================
ECHO [5/7] Starting Odoo Docker Container...
ECHO       Checking Docker status...
docker-compose ps >nul 2>nul
IF %ERRORLEVEL% NEQ 0 (
    ECHO       Starting Docker Compose...
    START "Odoo Docker" cmd /k "CD /D %PROJECT_DIR% && docker-compose up -d && ECHO Odoo started. Access at http://localhost:8069"
) ELSE (
    ECHO       Docker already running. Checking status...
    docker-compose ps
)
TIMEOUT /T 5 /NOBREAK >nul

REM ============================================================================
REM  COMPONENT 6: Gold Orchestrator (The Brain)
REM ============================================================================
ECHO [6/7] Starting Gold Orchestrator (The Brain)...
START "Gold Orchestrator - The Brain" cmd /k "CD /D %PROJECT_DIR% && ECHO Starting Gold Orchestrator - AI Reasoning Engine... && %PYTHON_CMD% gold\tools\gold_orchestrator.py"
TIMEOUT /T 3 /NOBREAK >nul

REM ============================================================================
REM  COMPONENT 7: Action Dispatcher (The Hands)
REM ============================================================================
ECHO [7/7] Starting Action Dispatcher (The Hands)...
START "Action Dispatcher" cmd /k "CD /D %PROJECT_DIR% && ECHO Starting Action Dispatcher - Executes approved actions... && %PYTHON_CMD% silver\tools\action_dispatcher.py --daemon --interval 10"
TIMEOUT /T 3 /NOBREAK >nul

REM ============================================================================
REM  STARTUP COMPLETE
REM ============================================================================
ECHO.
ECHO ============================================================================
ECHO   ALL COMPONENTS STARTED!
ECHO ============================================================================
ECHO.
ECHO   Running Components:
ECHO   ✓ Gmail Watcher - Monitoring inbox for important emails
ECHO   ✓ WhatsApp Watcher - Monitoring messages
ECHO   ✓ Twitter Watcher - Monitoring social media tasks
ECHO   ✓ LinkedIn Watcher - Monitoring & auto-posting
ECHO   ✓ Odoo Docker - Business ERP running at http://localhost:8069
ECHO   ✓ Gold Orchestrator - Processing tasks and generating replies
ECHO   ✓ Action Dispatcher - Executing approved actions every 10 seconds
ECHO.
ECHO   Workflow:
ECHO     Inbox → Needs_Action → Pending_Approval → Approved → Done
ECHO.
ECHO   To Stop:
ECHO     Close each window manually, or run: stop_ai_employee.bat
ECHO.
ECHO   Logs:
ECHO     - Gmail: %LOG_DIR%\watcher.log
ECHO     - Twitter: %LOG_DIR%\watcher.log
ECHO     - LinkedIn: %LOG_DIR%\linkedin.log
ECHO     - Gold Orchestrator: %LOG_DIR%\gold_orchestrator_*.log
ECHO     - Action Dispatcher: %LOG_DIR%\action_dispatcher_*.log
ECHO.
ECHO ============================================================================
ECHO.
ECHO   Dashboard: %PROJECT_DIR%Dashboard.md
ECHO.
PAUSE
