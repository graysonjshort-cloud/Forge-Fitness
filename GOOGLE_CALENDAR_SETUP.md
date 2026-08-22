# Forge Fitness v14.12 — Google Calendar Setup

## What v14.12 adds

- Browser/device timezone detection using IANA timezone names.
- Live local clock in Calendar & Time settings.
- Local workout times stored separately from UTC timestamps.
- Google OAuth connection.
- Forge -> Google workout event creation/update/delete.
- Google -> Forge workout day/time imports when a linked event is moved.
- Automatic background sync every 2 minutes while Forge is open.
- Sync on app startup and when returning to Home or Plan.
- Google free/busy checks for AI Coach workout moves.
- Nearby alternate workout times when the preferred time is busy.

## Google Cloud setup

1. Create or select a Google Cloud project.
2. Enable the Google Calendar API.
3. Configure the OAuth consent screen.
4. Create an OAuth 2.0 Client ID for a Web application.
5. Add this redirect URI for local desktop development:

   http://127.0.0.1:8000/me/calendar/google/callback

6. Start the backend with these environment variables set:

   set GOOGLE_CLIENT_ID=YOUR_CLIENT_ID
   set GOOGLE_CLIENT_SECRET=YOUR_CLIENT_SECRET
   set GOOGLE_REDIRECT_URI=http://127.0.0.1:8000/me/calendar/google/callback
   set FORGE_APP_URL=http://127.0.0.1:5500

7. Start the API and UI as usual.
8. Open Forge -> Plan -> Training Settings -> Calendar & Time -> Connect Google Calendar.

For production, register the exact HTTPS callback URL for your deployed backend instead of the localhost callback.

## Local-phone testing note

The localhost OAuth callback is designed for the browser running on the same computer as the backend. If the Forge UI is opened from a phone while the backend is on a PC, use a deployed HTTPS backend/callback (or a properly configured development tunnel) and register that exact callback in Google Cloud.

## Security note

This prototype stores Google OAuth tokens in the local SQLite database so the integration can function during development. Before production release, encrypt tokens at rest or move them to a dedicated secrets/token store.
