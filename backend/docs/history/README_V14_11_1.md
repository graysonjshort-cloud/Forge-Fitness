# Forge Fitness v14.11.1 — Onboarding Navigation Fix

Fixed the Preferences navigation bug that could send a new user into the Plan
screen before a plan had been generated.

Changes:
- Every onboarding preference picker now explicitly returns to Preferences.
- Back and Done use the same safe return logic.
- The picker return state is reset after leaving a picker, preventing stale
  Training Settings state from leaking into onboarding.
- Training Settings can only return to Plan when a plan actually exists.
- Cardio, Split, Sport, Core, and exercise/focus pickers are treated as
  onboarding screens while no plan exists, keeping bottom navigation hidden.
- Plan-dependent Back routes now have safe fallbacks when no plan exists.

Validated with Node JavaScript syntax checking and navigation regression checks.
