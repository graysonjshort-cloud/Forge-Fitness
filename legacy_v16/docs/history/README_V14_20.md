# Forge Fitness v14.20 — Nutrition Stabilization + Saved Foods

v14.20 makes nutrition tracking faster and less dependent on live provider availability.

## New nutrition workflow

- Every confirmed/manual nutrition entry is remembered as a reusable recent food.
- Recent & Saved foods appear in the Nutrition tab.
- Foods can be favorited for faster access.
- Saved foods can be logged again with one tap.
- Logged nutrition entries can be edited after the fact.
- Editing an entry refreshes the remembered calories/macros for future reuse.
- The AI Coach checks confirmed saved foods before doing another internet lookup.
- When the Coach finds a strong saved-food match, it proposes the previously confirmed values and can log them without USDA/Open Food Facts being available.

## Reliability behavior

The provider stabilization from v14.19 remains in place. USDA and Open Food Facts are still used for new foods, while confirmed foods form a local reliability layer for repeat meals.

This means a food that was successfully confirmed once can be reused even during a temporary provider outage.

## Validation

Passed:

- Python syntax checks
- JavaScript syntax check
- Saved-food persistence
- Favorite/unfavorite persistence
- One-tap quick logging
- Nutrition entry editing
- Remembered macro refresh after editing
- Saved-food matching
- Full API flow for saved foods
- AI Coach reuse of confirmed food with live nutrition providers disabled
