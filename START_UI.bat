@echo off
title Forge Fitness v14.27 - UI
cd /d "%~dp0"
echo Starting Forge Fitness UI on http://127.0.0.1:5500
python -m http.server 5500
pause
