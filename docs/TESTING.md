# Manual test plan (Dragonsteel Schools Test instance)

Instance: `C:/Users/owner/curseforge/minecraft/Instances/Dragonsteel Schools Test` (Ice and Fire beta-5, Spellbooks
2.3.2, Iron's 3.16.3, Apex Arcana 1.3.0, JEI, this mod). Make a new creative world with cheats on.

1. **Cauldron.** `/give @s minecraft:dragon_breath 3`, place a cauldron, right-click it three times: pink liquid,
   glass bottles back. Look at it and cast Heal (any Holy spell): gold liquid. Draw three Holy Dragon Blood with glass
   bottles. Repeat with Evasion (any Ender spell) for violet Ender blood. A Fire spell should change nothing.
2. **Tempering.** Build any dragon forge, load iron ingots and Holy blood, and have a dragon of that element breathe
   on it: Tempered Holy Steel, one per 50 s of breath. JEI lists the recipe under the forge.
3. **Apex.** With tempered steel in the forge (`/give @s dragonsteel_schools:tempered_holy_steel 16` saves time), cast
   Reckoning or Gates of Heaven at the forge. All of it turns into Holy Dragonsteel Ingots. Try looking away during
   Reckoning's windup; it should still work. Ender: Dimension Cut or Grip of the Void on tempered Ender steel. A Holy
   Apex must leave Ender steel alone.
4. **Gear.** Craft armour (ingots, the school rune, any dragon scales), Dawn/Elsewhere and the tools (ingots and
   wither bones), and the staff (Spellbooks' base Dragon Priest staff plus school blood in the forge).
5. **Dawn.** Hit a zombie: gold flames on it, big damage. Knock it into water: the flames stay. Milk cures a player.
6. **Elsewhere.** Hold it (either hand) and let a skeleton shoot you: you step away instead. Melee still hits.
7. **Screenshots for the art pass.** Both armour sets front, back and side (and each piece alone), Dawn and Elsewhere
   in hand (first and third person), both staves, holy fire on a mob and on yourself in first person, the three
   cauldron liquids, and the Holy Fire effect icon.

## Dev client smoke test (Hastur)

`gradlew runClient -Pdsqa -PdsqaWorld=<save in run/saves>` loads that save, equips each school's full kit, lights holy
fire, screenshots first person, third person front and back into `run/screenshots/`, and quits, logging
`[DragonsteelSchools/qa] DONE`. The harness lives in `src/qa` and never ships in the jar. The GameTest server cannot
catch client-only crashes (0.1.0-dev.1's armour crash was one), so run this after any client-side change.
