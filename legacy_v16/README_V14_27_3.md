# Forge Fitness v14.27.3 — Simplified Google Calendar Connection

This release simplifies Calendar connection for normal Forge users.

## User experience
Users now see a clean Google Calendar card with a single:
`Continue with Google`

They no longer see client IDs, client secrets, redirect URIs, environment variables, or backend
setup instructions in the normal Calendar UI.

After Google authorization:
- Forge enables Calendar sync automatically.
- Forge attempts the initial workout sync automatically.
- The user is returned to Calendar & Time.
- The card changes to `Google Calendar connected`.
- Forge Coach can use availability once the connection is active.

If the server has not been configured by the Forge developer, the user simply sees
`Google Calendar unavailable` and `No action needed`.

Developer OAuth configuration remains a one-time server-side responsibility.
