@echo off
REM ============================================================================
REM  TEST WORKFLOW - Complete End-to-End Test
REM  ============================================================================
REM  This script will:
REM  1. Create a test file in Needs_Action
REM  2. Wait for Gold Orchestrator to create draft in Pending_Approval
REM  3. Move draft to Approved folder
REM  4. Run Action Dispatcher to execute and move to Done
REM  ============================================================================

SET PROJECT_DIR=%~dp0
SET PYTHON_CMD=python

ECHO ============================================================================
ECHO   WORKFLOW TEST - Complete End-to-End
ECHO ============================================================================
ECHO.
ECHO   This will test the complete workflow:
ECHO   Needs_Action → Pending_Approval → Approved → Done
ECHO.
ECHO ============================================================================

REM Step 1: Create test file in Needs_Action
ECHO.
ECHO [STEP 1] Creating test file in Needs_Action...
SET TIMESTAMP=%DATE:~-4%%DATE:~3,2%%DATE:~0,2%_%TIME:~0,2%%TIME:~3,2%%TIME:~6,2%
SET TIMESTAMP=%TIMESTAMP: =0%
SET TIMESTAMP=%TIMESTAMP:=_%

(
ECHO ---
ECHO type: test_email
ECHO from: Test User
ECHO subject: URGENT Payment Follow Up
ECHO received: %DATE%
ECHO priority: high
ECHO status: pending
ECHO ---
ECHO.
ECHO ## Content
ECHO.
ECHO This is a URGENT payment follow up test message.
ECHO Customer needs invoice payment ASAP.
ECHO.
ECHO ---
ECHO *Test file*
) > "%PROJECT_DIR%Needs_Action\TEST_WORKFLOW_%TIMESTAMP%.md"

ECHO [STEP 1] Test file created
ECHO.

REM Step 2: Wait for Gold Orchestrator
ECHO [STEP 2] Waiting 10 seconds for Gold Orchestrator to process...
ECHO         (Make sure Gold Orchestrator is running!)
TIMEOUT /T 10 /NOBREAK
ECHO.

REM Step 3: Check if draft was created
ECHO [STEP 3] Checking for draft in Pending_Approval...
DIR "%PROJECT_DIR%Pending_Approval\DRAFT_TEST_WORKFLOW_*.md" /B
IF %ERRORLEVEL% EQU 0 (
    ECHO [STEP 3] Draft found!
) ELSE (
    ECHO [STEP 3] No draft found - Gold Orchestrator may not be running
    ECHO.
    ECHO To continue test, manually run Gold Orchestrator:
    ECHO   python gold\tools\gold_orchestrator.py
    ECHO.
    PAUSE
)
ECHO.

REM Step 4: Move draft to Approved
ECHO [STEP 4] Moving draft to Approved folder...
FOR %%F IN ("%PROJECT_DIR%Pending_Approval\DRAFT_TEST_WORKFLOW_*.md") DO (
    MOVE /Y "%%F" "%PROJECT_DIR%Pending_Approval\Approved\"
    ECHO [STEP 4] Moved: %%~nxF
)
ECHO.

REM Step 5: Run Action Dispatcher
ECHO [STEP 5] Running Action Dispatcher...
CD /D %PROJECT_DIR%
%PYTHON_CMD% test_action_dispatcher.py
ECHO.

REM Step 6: Check Done folder
ECHO [STEP 6] Checking Done folder for processed file...
DIR "%PROJECT_DIR%Done\done_DRAFT_TEST_WORKFLOW_*.md" /B
IF %ERRORLEVEL% EQU 0 (
    ECHO [STEP 6] SUCCESS! File processed and moved to Done
) ELSE (
    ECHO [STEP 6] File not in Done yet
    DIR "%PROJECT_DIR%Done\*.md" /B
)
ECHO.

ECHO ============================================================================
ECHO   TEST COMPLETE
ECHO ============================================================================
ECHO.
ECHO Check these folders:
ECHO   - Needs_Action: Should NOT have TEST_WORKFLOW file
ECHO   - Pending_Approval: Should NOT have DRAFT_TEST_WORKFLOW file
ECHO   - Pending_Approval/Approved: Should be empty (file moved to Done)
ECHO   - Done: Should have done_DRAFT_TEST_WORKFLOW_*.md
ECHO.
PAUSE
