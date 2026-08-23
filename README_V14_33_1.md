# Forge Fitness v14.33.1

Stability patch for v14.33.

- A Supabase connection/authentication failure no longer aborts FastAPI startup.
- Forge falls back to its local SQLite database when remote persistence is unavailable.
- Render logs now include the parsed Supabase username, host, port, and database for diagnostics.
- Database passwords are never intentionally logged by Forge's diagnostic line.
- Snapshot sync failures are non-fatal and later write transactions can retry.
- All v14.33 UI, PWA, Calendar, equipment, nutrition, coach, and training features are retained.

Important: local SQLite on a free Render instance is ephemeral. This patch keeps Forge online during
a Supabase problem, but durable cross-restart persistence still requires a working Supabase connection.
