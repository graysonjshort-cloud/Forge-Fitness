# Forge Fitness v14.37.5.1

Fixes the v14.37.5.0 failure:

    RuntimeError: Missing required MPFB bones: chest

Changes:
- chest/spine detection now accepts more MPFB naming variants;
- if no named chest bone matches, Forge discovers the torso chain structurally;
- chest is no longer required for static Bench Press calibration because shoulder
  midpoint is sufficient for the current placement logic;
- if a truly required arm/root/head bone is missing, the script prints all
  available bone names to make the next mapping deterministic;
- the Windows-path example in the module docstring was changed to forward slashes,
  removing the harmless invalid-escape SyntaxWarning.

The v14.37.5.0 static-only calibration approach is otherwise unchanged.
