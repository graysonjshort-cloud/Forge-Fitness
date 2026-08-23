# Forge Fitness v14.35 — Exercise Intelligence

v14.35 upgrades Forge's exercise system from a basic directory/substitution layer into an
exercise-intelligence system.

## Exercise intelligence
- Derives fatigue cost, stability demand, joint-stress estimate, skill demand, hypertrophy rating,
  strength rating, unilateral/support status, and selection tags from the existing exercise library.
- Directory detail pages expose those ratings to the user.
- Exercise cards show saved Favorite / Avoid / Painful state.

## User learning
Users can mark any exercise:
- Favorite
- Avoid
- Painful
- Neutral

These choices are persisted and synchronized into the existing plan-generator preference fields.
Favorites are preferred during future generation. Avoid/Painful movements are excluded from new plans.

## Smarter substitutions
Substitutions are now ranked instead of alphabetized. Forge scores:
- movement-pattern match;
- primary-muscle match;
- exercise-type similarity;
- fatigue/skill similarity;
- equipment compatibility;
- user favorites/avoid/painful status;
- recovery level.

## Smarter plan selection
The generator now:
- considers stimulus-to-fatigue cost;
- favors manageable exercises during short sessions or low recovery;
- gives beginners a stability/support bias;
- penalizes redundant movement patterns and repeated primary muscles;
- retains existing performance/recovery adaptation.

## PWA delivery
v14.35 has a new service-worker cache and cache-busted frontend references so installed Android/iOS
PWAs can receive the update.
