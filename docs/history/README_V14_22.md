# Forge Fitness v14.22 — Training + Nutrition Integration

## Implemented
- AI Coach now combines today's real workout schedule with today's nutrition totals and remaining targets.
- New training-day nutrition intent for pre-workout fuel, post-workout recovery food, workout-day nutrition, and rest-day nutrition questions.
- Training days identify the scheduled workout and scheduled time when available.
- Rest days receive recovery-focused guidance without inventing extra workout fuel needs.
- Guidance uses the user's actual remaining calories, protein, carbs, and fat from Forge.
- New `GET /me/nutrition/training-guidance` endpoint exposes the integrated daily context.
- Nutrition tab includes a Training + Nutrition card with Training Fuel and Recovery Food actions.
- AI Coach quick prompts now include Training Fuel.
- v14.21 daily nutrition coaching and v14.20 saved-food behavior remain intact.

## Safety / behavior
Forge does not automatically increase or decrease calorie targets simply because a workout exists. It uses the user's established targets and schedule to give practical fueling guidance. This avoids silently changing nutrition goals.
