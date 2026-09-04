# Forge v14.32 — Free persistence setup

Forge can now survive Render Free restarts/redeploys without a paid Render disk.

## 1. Create a free Supabase project
Create a Supabase project and keep its database password private.

## 2. Get the Session pooler connection string
In Supabase, click **Connect** and copy the **Session pooler** connection string (port 5432).
Use the pooler string for Render because Render is IPv4-only and Supabase's direct free connection is IPv6.

It resembles:
postgresql://postgres.PROJECT_REF:PASSWORD@aws-0-REGION.pooler.supabase.com:5432/postgres

## 3. Add it to Render
Render -> forge-fitness -> Environment:
SUPABASE_DB_URL = [the complete Session pooler connection string]
FORGE_PERSISTENCE_KEY = forge-production

Never commit SUPABASE_DB_URL to GitHub.

## 4. Deploy v14.32
On first boot:
- if Supabase already has a Forge snapshot, Forge restores it;
- otherwise Forge starts from the bundled seeded SQLite DB;
- after successful DB transactions Forge stores a consistent snapshot in Supabase Postgres.

## Why this bridge exists
v14.32 deliberately keeps Forge's existing SQLite query layer intact while moving durability off Render's ephemeral filesystem. This avoids a risky all-at-once rewrite of thousands of lines of proven SQLite queries. A later release can normalize the tables natively in Postgres without blocking free persistent accounts now.

## Verify
Open:
https://forge-fitness-cwdb.onrender.com/persistence/status

Expected after SUPABASE_DB_URL is configured:
{"mode":"supabase-postgres-snapshot","persistent":true,"key":"forge-production"}
