# Forge Fitness v17.3.0 — Cloud Backend Migration

v17.3 removes Render from Forge's application architecture.

## Production topology

Android APK
→ HTTPS Forge API (containerized FastAPI)
→ Supabase-hosted durable persistence snapshot
→ OpenAI / Google Calendar integrations as configured

The APK contains the UI/assets and local-first workout runtime. The backend serves API traffic only by default.

## Provider-neutral backend
`backend/Dockerfile` packages the existing FastAPI application into a standard OCI container. The service listens on `$PORT`, so the same image can run on Cloud Run or another normal container platform without changing Forge code.

## First production target: Google Cloud Run
The `cloud/` directory contains deployment helpers for Cloud Run. Cloud Run is the first supported target because it can run Forge's existing Python/FastAPI stack without a rewrite.

Important: while Forge still uses its mature SQLite data layer plus Supabase durable snapshot bridge, the deployment is intentionally limited to one cloud instance. Multiple independent instances could otherwise hold different SQLite copies. Moving the entire data layer to native Postgres remains a future scalability improvement; it is not required to eliminate Render.

## API-only runtime
`FORGE_SERVE_FRONTEND=0` is now the production default. PWA static mounting and PWA-only manifest/service-worker endpoints are disabled unless explicitly opted back in.

## Android API binding
The installed app no longer needs the API to share its origin. Configure the deployed HTTPS API before Android sync:

`node scripts/set-api-base.mjs https://YOUR-NEW-API-URL`

`npm run cap:sync`

The production verification rejects an empty API URL and rejects `onrender.com`, preventing an accidental regression back to Render.

## Persistence

On a brand-new deployment with no Supabase snapshot yet, Forge seeds the writable runtime database from the bundled canonical SQLite baseline before applying migrations. This prevents an empty ephemeral filesystem from starting without the exercise directory.
Production should set:
- `SUPABASE_DB_URL`
- `FORGE_PERSISTENCE_KEY`

Forge restores the SQLite snapshot from Supabase when a fresh cloud instance starts and persists successful writes back to the Supabase snapshot store.

## Secrets
Do not commit API keys or database passwords. The Cloud Run deployment expects secrets to be stored in the cloud secret manager and exposed to the container as environment variables.

## Render retirement criterion
Render can be deleted after:
1. the replacement API returns `/healthz` and `/readyz`;
2. Android is configured to the replacement HTTPS URL;
3. login + plan load succeeds;
4. an offline workout can reconnect and replay successfully;
5. Calendar/AI integrations are verified if enabled.

No v17.3 application code requires Render.
