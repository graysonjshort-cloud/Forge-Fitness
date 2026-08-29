# Forge Fitness v14.58.0 — Session Intelligence

Turns the workout logger into a live session coach. Forge now evaluates each completed set and adjusts the current exercise without permanently rewriting the saved training program.

## What changed
- Dynamic rest recommendations after every logged set.
- Rest length reacts to RPE, within-exercise rep/duration drop, accumulated fatigue, and movement demands.
- Live fatigue scoring from 0–10 for the active exercise.
- Session-only volume management can trim one set when fatigue rises too quickly.
- Severe fatigue can end an exercise early to avoid low-quality volume.
- Strong, low-fatigue performance can unlock one optional bonus set after planned work is complete.
- Normal performance explicitly tells the athlete to stay on plan and move on when planned work is complete.
- The workout UI applies the recommended session set count immediately while leaving the underlying saved program untouched.
- Persistent rest timers now use Forge's recommended recovery duration instead of always using the programmed default.
- System/PWA versioning updated to v14.58.0.

## Decision signals
Session Intelligence combines:
- latest and average RPE
- consecutive high-RPE sets
- rep or timed-duration decay from the first productive set
- completed vs programmed sets
- programmed rest duration
- movement pattern

## Safety behavior
The engine is conservative by design. Extra work is optional and capped to one bonus set. High fatigue reduces volume before it recommends more work, and session adaptations do not permanently modify the training plan.
