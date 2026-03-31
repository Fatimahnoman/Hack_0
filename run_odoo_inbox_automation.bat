@echo off
echo ========================================
echo Odoo Inbox Automation - Sales Lead Importer
echo ========================================
echo.
echo Starting automation script...
echo.

cd /d "%~dp0"

python watchers\odoo_inbox_automation.py

pause
