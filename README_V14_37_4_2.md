# Forge Fitness v14.37.4.2

Skeleton-calibrated MPFB bench-press review generator.

Changes:
- Aligns the MPFB athlete from actual hips/chest/head/shoulder bone landmarks.
- Places the bar relative to shoulder width and chest position rather than fixed scene coordinates.
- Directly poses MPFB upper-arm/lower-arm bones for bottom and lockout positions.
- Adds a static bent-leg bench setup when compatible MPFB leg bones are found.
- Hides rig/camera/light helper clutter in the review viewport.
- Keeps Blender 5.2 Action/channelbag compatibility from v14.37.4.1.
- Retains the previous generator as LEGACY_build_bench_press_mpfb_v14_37_4_1.py.

This is still a review/calibration build. Inspect frames 1, 45, 58 and 100 before rendering.
