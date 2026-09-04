# Forge Fitness v14.61.0 — Split Builder & Full Plan Regeneration

v14.59 overhauls plan generation so the selected workout structure is explicit, customizable, and always kept in sync with training settings.

## Split generation
- Push / Pull / Legs is always visible in the split picker.
- PPL is enabled for 3–6 training days and no longer disappears from the UI when unavailable; schedules below 3 days explain the requirement.
- PPL rotations now stay PPL-based: 3 days = Push/Pull/Legs, 4 = Push/Pull/Legs/Push B, 5 adds Pull B, 6 adds Legs B.
- Existing Full Body, Upper/Lower, Body Part, Hybrid, sport-aware, and Forge Recommended modes remain available.

## Custom Split Builder
- New `custom` workout split type.
- Users assign muscle groups independently to every training day.
- Supported groups: Chest, Back, Shoulders, Biceps, Triceps, Quads, Hamstrings, Glutes, Calves, Core.
- Every day requires at least one muscle group.
- Custom day names are generated from their selected groups.
- The generator converts chosen muscles into compatible movement slots, then still applies goal, experience, equipment, recovery, exercise preferences, rep ranges, volume rules, and session-time trimming.
- Custom split configuration persists in `user_profiles.custom_split_json`.

## Full Plan Regeneration
- Saving a generation-impacting profile setting while an active plan exists now replaces the entire active plan.
- Generation-impacting inputs include goal, experience, days/week, session length, equipment, exercise preferences/exclusions, focus muscles, recovery, cardio, split/custom split, sport, core/cardio frequency, and seed.
- Existing preferred schedule days are preserved when the workout count remains unchanged.
- Schedule/session-length changes through Adjust Plan continue to rebuild the complete plan.
- Equipment eligibility changes also rebuild the complete plan.
- Rebuild failures restore the previous profile/settings so Forge does not leave a half-applied training configuration.
- Manual Workout Builder edits remain intentional workout-level edits and are not immediately erased by automatic regeneration.

## Version / PWA
- Backend system version: 14.61.0.
- Frontend version labels synchronized to v14.61.0.
- Service-worker cache bumped so installed PWAs receive the new plan-generation UI and logic.
