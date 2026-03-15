@echo off
echo Starting Gmail Watcher - Silver Tier...
echo.
cd /d "%~dp0"
python silver/watchers/gmail_watcher.py
pause
