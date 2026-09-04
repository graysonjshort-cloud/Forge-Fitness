@echo off
title Forge Fitness v14.27 - Validation
cd /d "%~dp0"
echo.
echo [1/2] Static UI and equipment validation
python tests\run_static_validation.py
if errorlevel 1 goto :fail
echo.
echo [2/2] End-to-end API workflow
python tests\run_e2e_flow.py
if errorlevel 1 goto :fail
echo.
echo All Forge v14.27 validation passed.
pause
exit /b 0
:fail
echo.
echo Validation failed. Review the error above.
pause
exit /b 1
