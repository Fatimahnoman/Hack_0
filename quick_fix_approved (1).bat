@echo off
REM ============================================================================
REM  Quick Fix - Move file to Approved and trigger Action Dispatcher
REM  ============================================================================

SET PROJECT_DIR=%~dp0
SET PYTHON_CMD=python

ECHO ============================================================================
ECHO   Quick Fix - Processing Pending Files
ECHO ============================================================================
ECHO.

REM Check if file exists in Pending_Approval
IF EXIST "%PROJECT_DIR%Pending_Approval\TEST_GMAIL_*.md" (
    ECHO [1] Found TEST_GMAIL file in Pending_Approval
    ECHO [2] Moving to Approved folder...
    MOVE /Y "%PROJECT_DIR%Pending_Approval\TEST_GMAIL_*.md" "%PROJECT_DIR%Pending_Approval\Approved\"
    ECHO [3] File moved to Approved folder
) ELSE (
    ECHO [INFO] No TEST_GMAIL file found in Pending_Approval
)

ECHO.
ECHO [4] Running Action Dispatcher...
CD /D %PROJECT_DIR%
%PYTHON_CMD% silver\tools\action_dispatcher.py

ECHO.
ECHO [5] Checking Done folder...
DIR "%PROJECT_DIR%Done\TEST_*.md" /B

ECHO.
ECHO ============================================================================
ECHO   Complete!
ECHO ============================================================================
PAUSE
