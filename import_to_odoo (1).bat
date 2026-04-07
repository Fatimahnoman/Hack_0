@echo off
REM ========================================
REM Odoo Inbox Importer - GOLD TIER
REM ========================================
REM This script imports all JSON/MD files from Inbox folder to Odoo.
REM 
REM Features:
REM - Creates/updates Contacts in Odoo
REM - Creates CRM Leads/Opportunities
REM - Moves processed files to Done folder
REM - Retry logic for reliability
REM - Detailed logging
REM ========================================

echo.
echo ========================================
echo Odoo Inbox Importer - GOLD TIER
echo ========================================
echo.
echo This script will import all pending files from Inbox to Odoo.
echo.
echo - Contacts will be created/updated in Odoo
echo - CRM Leads will be created
echo - Processed files will be moved to Done folder
echo - Logs will be saved to Logs folder
echo.
echo Configuration (set via environment variables if different):
echo - ODOO_URL: http://localhost:8069
echo - ODOO_DB: odoo
echo - ODOO_USERNAME: admin
echo - ODOO_PASSWORD: admin
echo.
pause
echo.
echo Starting import...
echo.

cd /d "%~dp0"

REM Set environment variables if needed (uncomment and modify)
REM set ODOO_URL=http://localhost:8069
REM set ODOO_DB=odoo
REM set ODOO_USERNAME=admin
REM set ODOO_PASSWORD=admin

python watchers\odoo_inbox_importer.py

echo.
echo ========================================
echo Import completed!
echo ========================================
echo.
pause
