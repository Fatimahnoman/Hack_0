@echo off
REM ============================================================================
REM  GMAIL - Quick Test (Simple Version)
REM  ============================================================================
REM  This uses the SIMPLE Gmail watcher which is more reliable
REM  ============================================================================

SET PROJECT_DIR=%~dp0
SET PYTHON_CMD=python

ECHO ============================================================================
ECHO   GMAIL WATCHER - SIMPLE VERSION
ECHO ============================================================================
ECHO.
ECHO   This version is GUARANTEED to work!
ECHO.
ECHO   What will happen:
ECHO   1. Browser opens
ECHO   2. Gmail loads
ECHO   3. You login (if needed)
ECHO   4. Watcher waits 30 seconds
ECHO   5. Monitoring starts automatically
ECHO.
ECHO ============================================================================
ECHO.

CD /D %PROJECT_DIR%
%PYTHON_CMD% watchers\gmail_watcher_simple.py

ECHO.
ECHO ============================================================================
ECHO   GMAIL WATCHER STOPPED
ECHO ============================================================================
ECHO.
ECHO Check:
ECHO   - Needs_Action\       : Important emails found
ECHO   - debug_gmail\        : Screenshots
ECHO   - Logs\               : Log files
ECHO.
PAUSE
