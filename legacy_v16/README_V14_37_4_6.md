# Forge Fitness v14.37.4.6

Fixes the v14.37.4.5 crash:

    ValueError: not enough values to unpack (expected 2, got 1)

The v14.37.4.5 calibration rewrite intentionally changed
`calibrate_athlete_to_bench()` to return one calibration object, but the
reconstructed `main()` still expected the older two-value `(L, B)` contract.

v14.37.4.6 updates `main()` and the pose-solver signature to use the single
calibration object consistently.

The Blender 5.2 compatibility, translation-only athlete calibration, and
two-bone IK pose solver remain unchanged.
