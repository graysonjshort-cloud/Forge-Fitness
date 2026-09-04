# Forge Fitness v14.17 — AI Nutrition Coach

Forge Coach can now help with nutrition in two new ways.

## Goal-based nutrition targets

The Coach can recommend starting calorie and macro targets from the user's
training goal and present them as a confirmation action before changing anything.

Supported goal presets:
- Build Muscle
- Lose Fat
- Get Stronger
- Improve Fitness
- General Fitness

These are explicitly treated as starting targets, not medical nutrition advice.

## Online meal lookup + logging

Users can tell Forge Coach what they ate, for example:

`I had 2 eggs, 2 slices of toast, and a banana for breakfast.`

Forge searches USDA FoodData Central over the internet, estimates the meal's
calories, protein, carbs, and fat, shows the estimate and source, then offers a
`Log Meal` action. The meal is only written to the Nutrition tab after the user
confirms.

For better estimates, users should include amounts or serving sizes.

## Online provider

By default Forge uses USDA FoodData Central with its `DEMO_KEY`.

Optional environment variables:

    set FDC_API_KEY=YOUR_FOODDATA_CENTRAL_API_KEY
    set NUTRITION_LOOKUP_ENABLED=1

A personal FoodData Central API key is recommended for heavier use because the
public demo key is rate-limited.

The existing OpenAI-powered Forge Coach remains optional. If `OPENAI_API_KEY`
is configured, the LLM rewrites the verified Forge nutrition result naturally;
the calories and macros still come from the deterministic online nutrition
lookup rather than being invented by the model.
