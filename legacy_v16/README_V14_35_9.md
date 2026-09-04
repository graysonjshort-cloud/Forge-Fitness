# Forge Fitness v14.35.9

Core circuits are now sequential.

Instead of displaying every exercise/set as independently completable, Forge guides the athlete through
one set at a time in circuit order:

Round 1: Exercise 1 → rest → Exercise 2 → rest → Exercise 3 → rest → Exercise 4 → round rest
Round 2: Exercise 1 → rest → Exercise 2 → rest → Exercise 3 → rest → Exercise 4 → finish

- Only the current core set is shown as actionable.
- The next exercise is previewed beneath the active set.
- Timed movements retain their dedicated timer.
- Effort/RIR is still recorded per set.
- Normal transition rest and longer round rest are automatic.
- Each set is saved immediately.
- Reopening an active Core Circuit restores completed sets from the backend and resumes at the next incomplete step.
- Progression history from v14.35.6 remains intact.
- Fresh PWA cache for installed phone updates.
