@echo off
cd /d %~dp0
git add .
git commit -m "Initial commit: Todo app with Dapr, Kafka, and OKE deployment"
git push -u origin main
pause
