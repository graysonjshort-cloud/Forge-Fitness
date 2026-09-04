# Repair v3

Fixed user creation after changing/replacing the local SQLite database.

Cause:
The browser kept `forge_user_id` in localStorage. The frontend assumed that ID still existed, even when the new database did not contain that user.

Fix:
- Stored user IDs are now validated against the API.
- If the stored user no longer exists, the app clears it and creates a fresh user automatically.
- The new user ID is stored back into localStorage.
- Startup now reports initialization errors instead of failing silently.

If you want to force a completely fresh user manually, open the browser console and run:
localStorage.removeItem("forge_user_id")
Then refresh the page.
