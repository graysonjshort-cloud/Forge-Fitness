# Forge Fitness v14.61.0 — Precision Plan Generation

v14.61 makes the plan generator more explicit and anatomically precise.

## Push / Pull / Legs naming
When Push / Pull / Legs is selected, generated workout display names are always `Push`, `Pull`, or `Legs`. Internal A/B rotation can still vary exercise order and selection without leaking A/B labels into the workout name.

## Exercises per workout
A new `exercises_per_day` profile setting lets the athlete target 3–10 strength exercises per workout. It is available during onboarding and in Adjust Plan. Because it is a generation input, changing it triggers the existing atomic full-plan regeneration flow. Forge reduces sets before dropping exercises when fitting the requested count into the session time budget.

## Detailed muscle taxonomy
The original broad groups remain available and now contain anatomical subsections:
- Chest: Upper, Mid, Lower Chest
- Back: Lats, Upper Back, Traps, Spinal Erectors
- Shoulders: Front, Side, Rear Delts
- Biceps: Long Head, Short Head, Brachialis
- Triceps: Long Head, Lateral/Medial Heads
- Quads: Rectus Femoris, Vastus Lateralis, Vastus Medialis
- Hamstrings: Biceps Femoris, Semitendinosus/Semimembranosus
- Glutes: Glute Max, Glute Med/Min, Adductors
- Calves/lower leg: Gastrocnemius, Soleus, Tibialis Anterior
- Core: Rectus Abdominis, Obliques, Deep Core, Hip Flexors
- Forearms: Wrist Flexors, Wrist Extensors, Grip

## Exercise-to-muscle links
The database now maintains normalized `muscle_taxonomy` and `exercise_muscles` tables. Every exercise in the bundled directory is linked to the broad groups and detailed muscle sections it trains, with primary/secondary roles. The current directory validates at 220/220 linked exercises and 759 exercise-muscle relationships.

## Precision custom splits
Custom split days preserve their broad muscle selections and may optionally specify sub-muscles. If no subsection is chosen, Forge selects across the whole broad muscle group. If sections are chosen, exact anatomical matches receive strong selection priority. The generator also interleaves selected muscle groups so a daily exercise-count limit does not starve later muscle selections.

## Validation
- Static validation: passed
- Frontend API contract validation: passed
- Full E2E flow: passed
- Precision plan validation: passed
- 220/220 exercises linked to normalized muscle targets
- PPL display naming verified
- 3–10 exercise target support verified
- Upper Chest, Side Delts, Lats, and Soleus precision selection verified
