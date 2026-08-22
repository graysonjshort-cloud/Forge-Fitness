# Forge Fitness v14.25.4 — Equipment Log Cleanup

Removed the **Conditioning** and **Recovery & Mobility** equipment sections from the actual app.

Removed conditioning equipment:
- Battle Ropes
- Agility Ladder
- Training Cones

Removed recovery/mobility equipment:
- Massage Gun
- Massage / Lacrosse Ball
- Mobility Stick / Dowel
- Stretching Strap
- Slant Board / Calf Wedge

The change is enforced at the backend catalog layer, so these items no longer appear in the
Equipment Log, are no longer automatically added by equipment presets, and are hidden even
for users who previously had them saved.

Cardio equipment remains available because it is a separate category from Conditioning.
