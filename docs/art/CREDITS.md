# Art credits and provenance

| Asset | Source | Licence |
|---|---|---|
| School dragonsteel tools (pickaxe, axe, shovel, hoe), Elsewhere, ingots, tempered steel, blood bottles | Palette remap of Ice and Fire 2.1.13 `dragonsteel_ice_*` and `ice_dragon_blood` textures (`tools/generate_textures.py`) | Ice and Fire is LGPL-3.0 |
| Holy fire sprites, cauldron liquids, Holy Fire effect icon | Recolour of Minecraft 1.20.1 `fire_0`, `fire_1`, `water_still` | Mojang assets, used the way most mods use them |
| Dawn, armour models/textures/glowmasks/icons | Drawn by `tools/generate_textures.py`, `tools/generate_armor.py` | Original |
| Staff models and their texture sheets (0.1.0-dev.10) | Built and painted by `tools/generate_staves.py` | Original |

The source textures are read from the jars at generation time and are never committed. To drop the LGPL-derived
sprites, replace the `remap(...)` calls in `generate_textures.py` with drawn art; nothing else depends on them.
