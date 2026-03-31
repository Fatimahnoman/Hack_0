@echo off
REM ========================================
REM GOLD TIER - QUICK TEST COMMANDS
REM ========================================
REM This script shows quick test commands
REM ========================================

cd /d "%~dp0"

:menu
cls
echo.
echo ========================================
echo GOLD TIER - QUICK TEST MENU
echo ========================================
echo.
echo Choose a test:
echo.
echo 1. Authorize Gmail (First time only)
echo 2. Start All Watchers
echo 3. Check Needs_Action Folder
echo 4. Check Pending_Approval Folder
echo 5. Check Approved Folder
echo 6. Check Done Folder
echo 7. View Action Dispatcher Logs
echo 8. View LinkedIn Logs
echo 9. View Gmail Watcher Logs
echo 10. View Dashboard
echo.
echo 11. Move ALL from Needs_Action to Pending_Approval
echo 12. Move ALL from Pending_Approval to Approved
echo 13. Create Test LinkedIn Post
echo 14. Create Test Sales Lead JSON
echo 15. Run Odoo Importer
echo.
echo 16. Full Email Test (Send test email instructions)
echo 17. Full LinkedIn Test (Create and approve post)
echo 18. Full Odoo Test (Create and import lead)
echo.
echo 0. Exit
echo.
echo ========================================
set /p choice="Enter your choice (0-18): "

if "%choice%"=="1" goto authorize_gmail
if "%choice%"=="2" goto start_watchers
if "%choice%"=="3" goto check_needs_action
if "%choice%"=="4" goto check_pending
if "%choice%"=="5" goto check_approved
if "%choice%"=="6" goto check_done
if "%choice%"=="7" goto view_ad_logs
if "%choice%"=="8" goto view_li_logs
if "%choice%"=="9" goto view_gmail_logs
if "%choice%"=="10" goto view_dashboard
if "%choice%"=="11" goto move_needs_to_pending
if "%choice%"=="12" goto move_pending_to_approved
if "%choice%"=="13" goto create_li_post
if "%choice%"=="14" goto create_sales_lead
if "%choice%"=="15" goto run_odoo_import
if "%choice%"=="16" goto test_email_instructions
if "%choice%"=="17" goto test_linkedin_full
if "%choice%"=="18" goto test_odoo_full
if "%choice%"=="0" goto end

echo Invalid choice!
pause
goto menu

:authorize_gmail
echo.
echo ========================================
echo Authorizing Gmail...
echo ========================================
del token.json 2>nul
python gmail_auth.py
pause
goto menu

:start_watchers
echo.
echo ========================================
echo Starting All Watchers...
echo ========================================
start_gold_tier.bat
pause
goto menu

:check_needs_action
echo.
echo ========================================
echo Needs_Action Folder:
echo ========================================
dir Needs_Action /od
pause
goto menu

:check_pending
echo.
echo ========================================
echo Pending_Approval Folder:
echo ========================================
dir Pending_Approval /od
pause
goto menu

:check_approved
echo.
echo ========================================
echo Approved Folder:
echo ========================================
dir Pending_Approval\Approved /od
pause
goto menu

:check_done
echo.
echo ========================================
echo Done Folder:
echo ========================================
dir Done /od
pause
goto menu

:view_ad_logs
echo.
echo ========================================
echo Action Dispatcher Logs:
echo ========================================
type Logs\action_dispatcher_*.log
pause
goto menu

:view_li_logs
echo.
echo ========================================
echo LinkedIn Logs:
echo ========================================
type Logs\linkedin_*.log
pause
goto menu

:view_gmail_logs
echo.
echo ========================================
echo Gmail Watcher Logs:
echo ========================================
type Logs\watcher.log
pause
goto menu

:view_dashboard
echo.
echo ========================================
echo Dashboard:
echo ========================================
type Dashboard.md
pause
goto menu

:move_needs_to_pending
echo.
echo ========================================
echo Moving files from Needs_Action to Pending_Approval...
echo ========================================
move Needs_Action\*.md Pending_Approval\
echo Done!
pause
goto menu

:move_pending_to_approved
echo.
echo ========================================
echo Moving files from Pending_Approval to Approved...
echo ========================================
move Pending_Approval\*.md Pending_Approval\Approved\
echo Done!
pause
goto menu

:create_li_post
echo.
echo ========================================
echo Creating Test LinkedIn Post...
echo ========================================
echo --- > Pending_Approval\test_linkedin_gold.md
echo type: linkedin_post_draft >> Pending_Approval\test_linkedin_gold.md
echo source: gold_tier_test >> Pending_Approval\test_linkedin_gold.md
echo created: %date% %time% >> Pending_Approval\test_linkedin_gold.md
echo status: pending_approval >> Pending_Approval\test_linkedin_gold.md
echo --- >> Pending_Approval\test_linkedin_gold.md
echo. >> Pending_Approval\test_linkedin_gold.md
echo ## LinkedIn Post Draft >> Pending_Approval\test_linkedin_gold.md
echo. >> Pending_Approval\test_linkedin_gold.md
echo Gold Tier automation is working perfectly! >> Pending_Approval\test_linkedin_gold.md
echo AI employees are the future. >> Pending_Approval\test_linkedin_gold.md
echo. >> Pending_Approval\test_linkedin_gold.md
echo #AI #Automation #GoldTier >> Pending_Approval\test_linkedin_gold.md
echo. >> Pending_Approval\test_linkedin_gold.md
echo --- >> Pending_Approval\test_linkedin_gold.md
echo *Test post* >> Pending_Approval\test_linkedin_gold.md
echo.
echo Created: Pending_Approval\test_linkedin_gold.md
echo.
echo Next: Move to Approved folder
echo   move Pending_Approval\test_linkedin_gold.md Pending_Approval\Approved\
echo.
pause
goto menu

:create_sales_lead
echo.
echo ========================================
echo Creating Test Sales Lead JSON...
echo ========================================
echo { > Inbox\test_lead_gold.json
echo   "type": "sales_lead", >> Inbox\test_lead_gold.json
echo   "customer_name": "Gold Tier Test Customer", >> Inbox\test_lead_gold.json
echo   "email": "test@goldtier.com", >> Inbox\test_lead_gold.json
echo   "phone": "+923001234567", >> Inbox\test_lead_gold.json
echo   "product": "Gold Tier Automation", >> Inbox\test_lead_gold.json
echo   "amount": 100000, >> Inbox\test_lead_gold.json
echo   "currency": "PKR", >> Inbox\test_lead_gold.json
echo   "notes": "Testing Gold Tier automation" >> Inbox\test_lead_gold.json
echo } >> Inbox\test_lead_gold.json
echo.
echo Created: Inbox\test_lead_gold.json
echo.
echo Next: Run Odoo Importer
echo   import_to_odoo.bat
echo.
pause
goto menu

:run_odoo_import
echo.
echo ========================================
echo Running Odoo Importer...
echo ========================================
import_to_odoo.bat
pause
goto menu

:test_email_instructions
cls
echo.
echo ========================================
echo FULL EMAIL TEST - INSTRUCTIONS
echo ========================================
echo.
echo STEP 1: Send test email to your Gmail
echo ----------------------------------------
echo From: Any email
echo To: Your Gmail account
echo Subject: urgent - Gold Tier Test
echo Body:
echo   This is a test email.
echo   Please send this to test@example.com
echo.
echo STEP 2: Wait 2 minutes
echo ----------------------------------------
echo Gmail Watcher will detect the email
echo.
echo STEP 3: Check Needs_Action folder
echo ----------------------------------------
echo File should appear: GMAIL_urgent_*.md
echo.
echo STEP 4: Move to Pending_Approval
echo ----------------------------------------
echo   move Needs_Action\GMAIL_*.md Pending_Approval\
echo.
echo STEP 5: Review the file
echo ----------------------------------------
echo   type Pending_Approval\GMAIL_*.md
echo.
echo STEP 6: Move to Approved
echo ----------------------------------------
echo   move Pending_Approval\GMAIL_*.md Pending_Approval\Approved\
echo.
echo STEP 7: Wait 30 seconds
echo ----------------------------------------
echo Action Dispatcher will:
echo   - Detect the file
echo   - Extract recipient
echo   - Send email via Gmail API
echo   - Move to Done folder
echo.
echo STEP 8: Verify
echo ----------------------------------------
echo   - Check Done folder
echo   - Check recipient inbox
echo   - Check Dashboard.md
echo.
echo ========================================
pause
goto menu

:test_linkedin_full
cls
echo.
echo ========================================
echo FULL LINKEDIN TEST - INSTRUCTIONS
echo ========================================
echo.
echo STEP 1: Create test post
echo ----------------------------------------
echo Already created in option 13
echo.
echo STEP 2: Move to Approved
echo ----------------------------------------
echo   move Pending_Approval\test_linkedin_gold.md Pending_Approval\Approved\
echo.
echo STEP 3: Wait 1 minute
echo ----------------------------------------
echo LinkedIn Auto Poster will:
echo   - Open browser
echo   - Navigate to LinkedIn
echo   - Click "Start a post"
echo   - Type content (slowly)
echo   - Click "Post"
echo   - Move to Done folder
echo.
echo STEP 4: Verify
echo ----------------------------------------
echo   - Check your LinkedIn profile
echo   - Check Done folder
echo   - Check Logs\linkedin_*.log
echo.
echo ========================================
pause
goto menu

:test_odoo_full
cls
echo.
echo ========================================
echo FULL ODOO TEST - INSTRUCTIONS
echo ========================================
echo.
echo STEP 1: Create test lead
echo ----------------------------------------
echo Already created in option 14
echo.
echo STEP 2: Run importer
echo ----------------------------------------
echo   import_to_odoo.bat
echo.
echo STEP 3: Watch the output
echo ----------------------------------------
echo Should see:
echo   - Connecting to Odoo...
echo   - Created new partner
echo   - Created CRM lead
echo   - File moved to Done
echo.
echo STEP 4: Verify in Odoo
echo ----------------------------------------
echo   - Open: http://localhost:8069
echo   - Go to: Contacts
echo   - Search: "Gold Tier Test Customer"
echo   - Go to: CRM → Leads
echo   - Should see the lead
echo.
echo STEP 5: Check Done folder
echo ----------------------------------------
echo   dir Done
echo   Should see: processed_test_lead_gold.json
echo.
echo ========================================
pause
goto menu

:end
echo.
echo ========================================
echo Gold Tier Testing Complete!
echo ========================================
echo.
