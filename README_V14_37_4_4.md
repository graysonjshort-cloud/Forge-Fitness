# Forge Fitness v14.37.4.4

Clean generator reconstruction.

This build stops the incremental missing-function patch cycle. It restores the
known-good v14.37.4.1 helper API (`append_scene_objects`, `map_standard_rig`,
`equipment`, `scene`) and adds explicit adapters for the v14.37.4.2
skeleton-calibration pipeline.

Validated before packaging:
- Python syntax compilation
- all required pipeline functions exist
- all direct function calls made by `main()` resolve
