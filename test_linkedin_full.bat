@echo off
REM ============================================================================
REM  LINKEDIN - Complete Test Suite
REM  ============================================================================

SET PROJECT_DIR=%~dp0
SET PYTHON_CMD=python

ECHO ============================================================================
ECHO   LINKEDIN - Complete Test Suite
ECHO ============================================================================
ECHO.
ECHO   This will test:
ECHO   1. LinkedIn Watcher (Monitoring)
ECHO   2. LinkedIn Auto-Post (Direct Test)
ECHO   3. Check Screenshots
ECHO.
ECHO ============================================================================
ECHO.

REM Option 1: Test Auto-Post Directly
ECHO [TEST 1] Testing LinkedIn Auto-Post (Direct)...
ECHO.
CD /D %PROJECT_DIR%
%PYTHON_CMD% test_linkedin_auto_post.py
ECHO.

REM Option 2: Run Watcher
ECHO.
ECHO [TEST 2] Starting LinkedIn Watcher (Monitoring Mode)...
ECHO.
ECHO This will monitor LinkedIn for 60 seconds...
ECHO Press Ctrl+C to stop after testing
ECHO.
TIMEOUT /T 3 /NOBREAK
%PYTHON_CMD% watchers\linkedin_watcher_fixed.py

ECHO.
ECHO ============================================================================
ECHO   TEST COMPLETE
ECHO ============================================================================
ECHO.
ECHO Check these folders:
ECHO   - debug_linkedin\    : Screenshots of each step
ECHO   - Logs\linkedin.log  : Detailed logs
ECHO   - Needs_Action\      : Files created from notifications
ECHO   - Pending_Approval\  : Drafts created by Gold Orchestrator
ECHO.
PAUSE
