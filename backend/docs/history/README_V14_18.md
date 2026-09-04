# Forge Fitness v14.18 — Smart Food Logging

Forge Coach now supports restaurant- and brand-aware food logging.

Examples:
- `I had a large turkey sub from Subway for lunch.`
- `Log a chicken bowl from Chipotle.`
- `I had a Fairlife Core Power 26g shake.`
- `I had a New York Style sub and zero sugar root beer from Nutrition Hub.`

## Smart lookup flow

1. Forge parses the meal, meal type, restaurant/brand, quantities, and serving sizes.
2. If a restaurant item is size-sensitive and the size is missing, Forge asks one short clarification.
3. Forge searches USDA FoodData Central with the restaurant/brand included in the query.
4. It prioritizes branded matches whose brand/description matches the named source.
5. OpenFoodFacts is available as a fallback for packaged/branded foods.
6. Forge aggregates calories, protein, carbs, and fat across all meal items.
7. The user sees the matched foods, source provider, estimated totals, and an estimate warning.
8. Nothing is logged until the user presses `Log Meal`.
9. The Nutrition entry keeps its lookup source so it can be reviewed later.

## Follow-up corrections

After a clarification, the user can simply answer things like:
- `Large`
- `It was a footlong`
- `It was 12 oz`

Forge re-runs the lookup using the original meal plus the correction.

## Provider settings

USDA FoodData Central is enabled by default using `DEMO_KEY`.

Optional:

    set FDC_API_KEY=YOUR_FOODDATA_CENTRAL_API_KEY
    set NUTRITION_LOOKUP_ENABLED=1
    set OPENFOODFACTS_ENABLED=1

A personal USDA API key is recommended for regular use.

## Reliability

External nutrition-provider failures are converted into a normal Coach response
instead of crashing the request. The Coach asks the user to include the brand,
restaurant, or size when a reliable match cannot be found.
