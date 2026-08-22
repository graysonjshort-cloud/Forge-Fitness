# Forge Fitness v7.2 — User creation repair

Fixed the "User not found" error after onboarding.

Root cause:
The frontend validated a stored browser user ID using /progress. That endpoint can return a default training state even when the user row no longer exists, so stale localStorage IDs could survive validation.

Fix:
- Added GET /users/{user_id} to validate the actual users table.
- ensureUser() now validates against the real user row.
- A stale user ID is cleared and a new user is automatically created.
- generatePlan() also self-recovers if the user disappears between validation and profile save.

Validated:
- stale user ID returns 404
- new user creation works
- new user lookup works
- profile save works
- plan generation works
