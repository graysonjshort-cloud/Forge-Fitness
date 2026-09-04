# Forge Fitness v14.18.2 — Nutrition Lookup Fallback Fix

Fixes Smart Food Logging failures for common drinks and generic foods.

Changes:
- Added `fl oz`, `fluid ounce(s)`, `mL`, and liters to portion parsing.
- USDA lookup now retries progressively broader queries.
- Zero-sugar beverages retry as `diet` and generic beverage categories.
- Zero-calorie nutrition results are accepted as valid.
- If online providers fail for an obvious zero-sugar soft drink, Forge offers a clearly labeled generic estimate of 0 kcal / 0 macros instead of repeatedly asking for a restaurant or brand.
- Exact branded/restaurant matches still take priority when available.

Example:
`log a 12 fl oz zero sugar root beer`
can now resolve through an online match or a generic zero-sugar beverage fallback.
