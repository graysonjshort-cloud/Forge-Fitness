# Forge Fitness v15.10.1 — UI & Pathway Cleanup

This patch cleans visual rhythm and text density across the workout experience, restores active-workout set controls, fixes the duplicate legacy rest-timer function that was overriding the newer timer, fixes the Nutrition Favorites pathway, and synchronizes visible version labels.

Set controls persist through the existing workout exercise-set endpoint. During an active session, Forge will not allow removing sets below the set currently being performed, and a manual set choice takes precedence over Session Intelligence for that exercise during the current session.
