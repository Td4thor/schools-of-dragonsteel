# Porting Ice and Fire: Schools of Dragonsteel to Ice and Fire 2

Main code never imports Ice and Fire. Everything that names it sits in two places:

1. **`tools/generate_data.py`, the `IAF` dict.** The forge recipe type (`iceandfire:dragonforge`), the dragon types
   (`fire`, `ice`, `lightning`), the forge cook time, the core and part block ids, the wither-bone handle tag and the
   dragon-scale tag. Edit them, run `python tools/generate_data.py`, and the tempering, staff and gear recipes plus
   the `dragon_forge_cores`/`dragon_forge_parts` block tags are rewritten.
2. **`dev.dragonsteelschools.forge.DragonForges`.** Finds the forge core through those two block tags and uses its
   slots through Minecraft's `Container` (Ice and Fire 2.1.13: 0 input, 1 blood, 2 output). If Ice and Fire 2's
   forge keeps a vanilla container, only the slot numbers might change. If it drops the container (capabilities only),
   this is the one class to adapt.

The dragon's part of the work is an ordinary Ice and Fire forge recipe, so Ice and Fire itself decides when a dragon
is breathing. Nothing reads its internals. If Ice and Fire 2 has no recipe-driven forge at all, the fallback is to
temper in a different way (for example, breath on a cauldron) and keep the finishing step (Legendary or Apex cast) as it is.

Test fixtures (`src/gametest/.../ForgeFixtures.java`) build the 2.1.13 forge from registry names and call
`onHitWithFlame` reflectively; they need the same update.

The JEI pages (`compat/jei`, 1.0.0) take the forge cores from the same `dragon_forge_cores` tag for their catalysts
(skipping ids ending in `_disabled`), so they follow step 1 with no change. Ice and Fire's own JEI plugin shows the
tempering and staff recipes; if Ice and Fire 2 drops it, those recipes would need a category here.
