# Forge Fitness v8 — Account/Auth MVP

v8 replaces browser-only user IDs with persistent email/password accounts.

Run API:
py -m uvicorn fitness_backend_api_v2_connected:app --host 0.0.0.0 --port 8000

Run UI:
py -m http.server 5500 --bind 0.0.0.0

Open http://127.0.0.1:5500

New flow:
Welcome → Create Account / Sign In → Onboarding → Generate Plan

MVP security:
- PBKDF2-SHA256 password hashing with unique salts
- 30-day random bearer sessions
- session tokens stored only as SHA-256 hashes
- logout revokes the active token

Before public deployment add HTTPS, rate limiting, email verification, password reset, and production database hosting.
