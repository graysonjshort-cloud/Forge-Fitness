# Forge Fitness v10 — Exercise Substitutions + Actionable Coach

New:
- Swap Exercise on the exercise screen
- approved substitutes from `exercise_substitutions`
- equipment compatibility filtering
- swaps persist to the current program and database
- real Coach API grounded in account plan/history/training state
- requests such as "I only have 25 minutes today" produce an actionable workout adjustment
- Apply Change persists the shortened workout

Important:
The v10 Coach is a deterministic Forge rules engine. It is not yet connected to a hosted generative AI model. This lets us safely test context + actions before adding an LLM.

Run:
1. py -m uvicorn fitness_backend_api_v2_connected:app --host 0.0.0.0 --port 8000
2. py -m http.server 5500 --bind 0.0.0.0
