# Forge Fitness v13 — Real LLM Coach

Forge Coach now supports the OpenAI Responses API.

Windows CMD:
    set OPENAI_API_KEY=YOUR_KEY_HERE
    set FORGE_LLM_MODEL=gpt-5.6-luna
    py -m uvicorn fitness_backend_api_v2_connected:app --host 0.0.0.0 --port 8000

In a second terminal:
    py -m http.server 5500 --bind 0.0.0.0

Keep OPENAI_API_KEY server-side. Never put it in app.js, index.html, or localStorage.

The LLM writes conversational answers, while Forge's tested rules remain authoritative for safety and app-changing actions. If the LLM/API is unavailable, Forge automatically falls back to the deterministic coach.
