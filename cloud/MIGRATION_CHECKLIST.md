# Forge Render → Cloud API checklist

1. Create/select a Google Cloud project.
2. Put the Supabase connection string in Secret Manager as `FORGE_SUPABASE_DB_URL`.
3. If AI Coach is enabled, put the OpenAI key in Secret Manager as `FORGE_OPENAI_API_KEY`.
4. Deploy `backend/` using `cloud/deploy_cloud_run.ps1` on Windows or `.sh` on macOS/Linux.
5. Open the returned `/healthz`, `/readyz`, and `/release`.
6. Run `node scripts/set-api-base.mjs <returned HTTPS URL>`.
7. Run `npm install` if dependencies are not installed.
8. Run `npm run cap:sync`.
9. Build/install Android and verify login, current plan, one set write, offline replay, and completion.
10. Update Google OAuth redirect URI if Calendar integration is enabled.
11. Only after verification, delete/suspend the Render service.

Keep Cloud Run max instances at 1 until Forge's data layer is migrated from SQLite+snapshot compatibility mode to native Postgres.
