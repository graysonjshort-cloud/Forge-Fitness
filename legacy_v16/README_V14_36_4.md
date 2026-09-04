# Forge Fitness v14.36.4

This starts the real animation-production stage.

- Added a 20-exercise production manifest with deterministic asset paths.
- Added asset registration support in the database layer.
- Added review state/versioning for real demo assets.
- Added an in-app Demo Library Coverage screen.
- Added a backend audit endpoint.
- Added a manifest validator so a demo cannot be marked ready/reviewed while its file or review checklist is incomplete.
- Added `/assets/exercise_demos/` as the production delivery location.
- Existing v14.36.3 offline caching automatically works with these assets once added.

This build intentionally contains no fabricated form animations. The next production task is to create/import the first reviewed animation files and map them to their exercise IDs.
