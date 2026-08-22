# Forge Fitness v14.29 — HTTPS Deployment on Render

Forge now supports a **single-origin production deployment**: the FastAPI backend and installable
PWA are served from one Render Web Service. This avoids mixed-content problems on phones and means
the installed PWA talks to the same HTTPS origin as the API.

## Why Render
Render Web Services support Python/FastAPI and receive an HTTPS `onrender.com` URL. Render also
automatically provisions and renews TLS for custom domains.

## Deploy

### 1. Put Forge in GitHub
Create a GitHub repository and upload the contents of this folder.

Do **not** commit real API keys or secrets. Keep the placeholder values in local BAT files.

### 2. Create the Render service
In Render:
1. Click **New → Blueprint** or **New → Web Service**.
2. Connect the Forge GitHub repository.
3. If using Blueprint, Render will detect `render.yaml`.
4. Deploy the service.

The production start command is:

`uvicorn fitness_backend_api_v2_connected:app --host 0.0.0.0 --port $PORT`

After deployment Render will give you a URL similar to:

`https://forge-fitness.onrender.com`

Open that URL directly. Both the Forge PWA and API are served from the same HTTPS address.

### 3. Add secrets in Render
In the Render service's **Environment** page, add:

- `OPENAI_API_KEY`
- `FDC_API_KEY`
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`

Then add:

- `FORGE_APP_URL=https://YOUR-RENDER-DOMAIN`
- `GOOGLE_REDIRECT_URI=https://YOUR-RENDER-DOMAIN/me/calendar/google/callback`

Example:

`FORGE_APP_URL=https://forge-fitness.onrender.com`

`GOOGLE_REDIRECT_URI=https://forge-fitness.onrender.com/me/calendar/google/callback`

Never include a trailing slash after the callback.

### 4. Update Google OAuth
In Google Cloud Console, add the production redirect URI from above to the same OAuth Web Client's
**Authorized redirect URIs**.

You can keep the local development callback too:

`http://127.0.0.1:8000/me/calendar/google/callback`

Then Google Calendar works both locally and from the hosted phone app.

### 5. Install on your phone

**Android / Chrome**
1. Open the HTTPS Forge URL.
2. Sign in.
3. Open **Training Settings**.
4. Tap **Install Forge**, or use Chrome's **Install app** menu item.

**iPhone / Safari**
1. Open the HTTPS Forge URL in Safari.
2. Tap **Share**.
3. Tap **Add to Home Screen**.
4. Tap **Add**.

Forge launches in standalone app mode from the home screen.

## Custom domain
A custom domain is optional. You can use the free Render HTTPS domain first. Later, add a custom
domain such as `app.forgefitness.com` in Render Settings → Custom Domains. Render handles the TLS
certificate automatically.

After changing domains, update both:
- `FORGE_APP_URL`
- `GOOGLE_REDIRECT_URI`

and add the new redirect URI in Google Cloud.

## Database note
This build still uses the local SQLite database file. That is fine for initial testing, but a
production multi-user deployment should move persistent user data to a managed database before
relying on it for real users.
