@echo off
title Forge Fitness v14.28 - Phone PWA UI
cd /d "%~dp0"
echo.
echo Forge PWA development server
echo.
echo NOTE:
echo Phone installation requires HTTPS in normal mobile browsers.
echo For quick local testing, this server exposes Forge on your Wi-Fi,
echo but installation support depends on the browser/security context.
echo.
echo Find this computer's IPv4 address with: ipconfig
echo Then open http://YOUR-PC-IP:5500 on your phone.
echo.
python -m http.server 5500 --bind 0.0.0.0
pause
