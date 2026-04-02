@echo off
echo Starting Gmail Watcher - Silver Tier...
echo.
cd /d "%~dp0"
python watchers\gmail_watcher.py
pause
