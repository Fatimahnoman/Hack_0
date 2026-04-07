@echo off
REM ============================================================================
REM  AI Employee - FIXED Startup Script (v2)
REM  ============================================================================
REM  Proper workflow: Watchers → Needs_Action → Pending_Approval → Approved → Done
REM
REM  Usage: start_fixed_ai_employee.bat
REM ============================================================================

TITLE AI Employee - FIXED Version
SET PROJECT_DIR=%~dp0
SET PYTHON_CMD=python
SET LOG_DIR=%PROJECT_DIR%Logs

REM Create log directory if not exists
IF NOT EXIST "%LOG_DIR%" MKDIR "%LOG_DIR%"

ECHO ============================================================================
ECHO   AI EMPLOYEE - FIXED VERSION
ECHO   Proper Workflow Enforcement
ECHO ============================================================================
ECHO.
ECHO   Workflow:
ECHO     Watchers → Needs_Action → Pending_Approval → Approved → Done
ECHO.
ECHO   Keywords Monitored:
ECHO     urgent, sales, payment, invoice, deal, order, client, customer,
ECHO     quotation, proposal, overdue, follow up, meeting, booking, asap
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
REM  STEP 1: Clean up old test files
REM ============================================================================
ECHO [STEP 1] Cleaning up old test files...
DEL /Q "%PROJECT_DIR%Needs_Action\TEST_*.md" 2>nul
DEL /Q "%PROJECT_DIR%Needs_Action\FILE_*.md" 2>nul
ECHO [STEP 1] Cleanup complete
ECHO.

REM ============================================================================
REM  STEP 2: Start Gmail Watcher
REM ============================================================================
ECHO [STEP 2] Starting Gmail Watcher...
START "Gmail Watcher" cmd /k "CD /D %PROJECT_DIR% && COLOR 0A && ECHO ==================================== && ECHO Gmail Watcher - Monitoring Inbox && ECHO ==================================== && ECHO. && ECHO Keywords: urgent, sales, payment, invoice, deal, order, client, customer, quotation, proposal, overdue, follow up, meeting, booking, asap && ECHO. && %PYTHON_CMD% watchers\gmail_watcher_browser.py"
TIMEOUT /T 5 /NOBREAK >nul
ECHO [STEP 2] Gmail Watcher started
ECHO.

REM ============================================================================
REM  STEP 3: Start WhatsApp Watcher
REM ============================================================================
ECHO [STEP 3] Starting WhatsApp Watcher...
START "WhatsApp Watcher" cmd /k "CD /D %PROJECT_DIR% && COLOR 0B && ECHO ==================================== && ECHO WhatsApp Watcher - Monitoring Messages && ECHO ==================================== && ECHO. && ECHO Keywords: urgent, sales, payment, invoice, deal, order, client, customer, quotation, proposal, overdue, follow up, meeting, booking, asap && ECHO. && %PYTHON_CMD% watchers\whatsapp_watcher_fixed.py"
TIMEOUT /T 5 /NOBREAK >nul
ECHO [STEP 3] WhatsApp Watcher started
ECHO.

REM ============================================================================
REM  STEP 4: Start LinkedIn Watcher
REM ============================================================================
ECHO [STEP 4] Starting LinkedIn Watcher...
START "LinkedIn Watcher" cmd /k "CD /D %PROJECT_DIR% && COLOR 0C && ECHO ==================================== && ECHO LinkedIn Watcher - Monitoring Network && ECHO ==================================== && ECHO. && ECHO Keywords: urgent, sales, payment, invoice, deal, order, client, customer, quotation, proposal, overdue, follow up, meeting, booking, asap && ECHO. && %PYTHON_CMD% watchers\linkedin_watcher_fixed.py"
TIMEOUT /T 5 /NOBREAK >nul
ECHO [STEP 4] LinkedIn Watcher started
ECHO.

REM ============================================================================
REM  STEP 5: Start Gold Orchestrator (The Brain)
REM ============================================================================
ECHO [STEP 5] Starting Gold Orchestrator (The Brain)...
START "Gold Orchestrator" cmd /k "CD /D %PROJECT_DIR% && COLOR 0E && ECHO ==================================== && ECHO Gold Orchestrator - AI Reasoning Engine && ECHO ==================================== && ECHO. && ECHO Monitoring: Needs_Action folder && ECHO Creating: Drafts in Pending_Approval && ECHO Moving: Processed files to Done && ECHO. && %PYTHON_CMD% gold\tools\gold_orchestrator.py"
TIMEOUT /T 5 /NOBREAK >nul
ECHO [STEP 5] Gold Orchestrator started
ECHO.

REM ============================================================================
REM  STEP 6: Start Action Dispatcher (The Hands)
REM ============================================================================
ECHO [STEP 6] Starting Action Dispatcher (The Hands)...
START "Action Dispatcher" cmd /k "CD /D %PROJECT_DIR% && COLOR 0D && ECHO ==================================== && ECHO Action Dispatcher - Executes Approved Actions && ECHO ==================================== && ECHO. && ECHO Monitoring: Pending_Approval/Approved folder && ECHO Executing: LinkedIn posts, Emails, WhatsApp messages && ECHO Moving: Completed actions to Done && ECHO. && %PYTHON_CMD% silver\tools\action_dispatcher.py --daemon --interval 10"
TIMEOUT /T 5 /NOBREAK >nul
ECHO [STEP 6] Action Dispatcher started
ECHO.

REM ============================================================================
REM  STARTUP COMPLETE
REM ============================================================================
ECHO.
ECHO ============================================================================
ECHO   ALL COMPONENTS STARTED!
ECHO ============================================================================
ECHO.
ECHO   Running Components:
ECHO   [1] Gmail Watcher - Monitoring inbox for important emails
ECHO   [2] WhatsApp Watcher - Monitoring messages
ECHO   [3] LinkedIn Watcher - Monitoring ^& auto-posting
ECHO   [4] Gold Orchestrator - Processing tasks and generating replies
ECHO   [5] Action Dispatcher - Executing approved actions every 10 seconds
ECHO.
ECHO   Workflow:
ECHO     Watchers → Needs_Action → Pending_Approval → Approved → Done
ECHO.
ECHO   IMPORTANT:
ECHO   - Watchers will ONLY create files for messages with KEYWORDS
ECHO   - Gold Orchestrator creates DRAFTS in Pending_Approval
ECHO   - Files move to Done ONLY after draft creation
ECHO   - Action Dispatcher executes from Approved folder
ECHO.
ECHO   To Stop: Close each window manually
ECHO.
ECHO   Logs: %LOG_DIR%
ECHO   Debug Screenshots: %PROJECT_DIR%debug_gmail\, %PROJECT_DIR%debug_linkedin\
ECHO.
ECHO ============================================================================
ECHO.
PAUSE
