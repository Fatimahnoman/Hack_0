@echo off
REM LinkedIn feed watcher only (same engine as start_gold_tier LinkedIn step)
cd /d "%~dp0"
title LinkedIn Unified Watch
echo Running: unified_linkedin_poster.py --watch
echo Logs: gold\logs\linkedin_unified_YYYYMMDD.log
echo.
python gold\watchers\unified_linkedin_poster.py --watch
pause
