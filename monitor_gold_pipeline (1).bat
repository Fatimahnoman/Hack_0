@echo off
cd /d "%~dp0"
title Gold Pipeline Monitor
echo Starting live log monitor (10s refresh). Close window to stop.
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0monitor_gold_pipeline.ps1"
