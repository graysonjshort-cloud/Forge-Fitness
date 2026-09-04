@echo off
title Forge Fitness v14.27.1 - Backend
cd /d "%~dp0"

REM ============================================================
REM Forge Fitness API / integration configuration
REM Replace ONLY the PASTE_* values below with your real keys.
REM Do not share this BAT file after adding private credentials.
REM ============================================================

REM ----- OpenAI / AI Coach -----
set "OPENAI_API_KEY=PASTE_OPENAI_API_KEY_HERE"
set "FORGE_LLM_ENABLED=1"
set "FORGE_LLM_MODEL=gpt-4o-mini"
set "FORGE_LLM_TIMEOUT=30"

REM ----- Google Calendar OAuth -----
set "GOOGLE_CLIENT_ID=PASTE_GOOGLE_CLIENT_ID_HERE"
set "GOOGLE_CLIENT_SECRET=PASTE_GOOGLE_CLIENT_SECRET_HERE"
set "GOOGLE_REDIRECT_URI=http://127.0.0.1:8000/me/calendar/google/callback"
set "FORGE_APP_URL=http://127.0.0.1:5500"

REM ----- USDA FoodData Central / smart nutrition lookup -----
set "FDC_API_KEY=PASTE_USDA_FOODDATA_CENTRAL_API_KEY_HERE"
set "NUTRITION_LOOKUP_ENABLED=1"

REM ----- Open Food Facts -----
REM Open Food Facts does not require a private API key in this build.
set "OPENFOODFACTS_ENABLED=1"

echo.
echo Starting Forge Fitness backend on http://127.0.0.1:8000
echo AI Coach: enabled
echo Google Calendar: configured from this BAT file
echo Nutrition lookup: enabled
echo.
python -m uvicorn fitness_backend_api_v2_connected:app --host 127.0.0.1 --port 8000 --reload
pause
