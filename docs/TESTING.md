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

`bash tools/run_client_qa.sh [save folder]` copies a save (by default Tad's test-instance world) to `run/saves/QA`
and runs `gradlew runClient -Pdsqa -PdsqaWorld=QA`. The client builds a sky platform at noon and puts each school's
armour on four armour stands: front, three-quarter, side and back. It shoots a lineup plus a close front and back at
FOV 30, then equips the full kit (sword main hand, axe off hand; Holy also burning with holy fire) and shoots first
and third person. Screenshots go to `run/screenshots/`, and the run quits logging `[DragonsteelSchools/qa] DONE`.
The script fails on any crash report or if the run never finishes. The harness lives in `src/qa` and never ships in the jar. The GameTest server cannot
catch client-only crashes (0.1.0-dev.1's armour crash was one), so run this after any client-side change.

## Blood, Evocation, Nature and Eldritch (0.1.0-dev.4)

Their forging works exactly like Holy and Ender. Blood (dev.4), Evocation (dev.5) and Nature (dev.6) have their own
armour; Eldritch wears plain placeholder plate in its colours until its art pass.

1. **Blood.** Cast any Blood spell (Heartstop works) at a cauldron of dragon's breath for Blood dragon blood. Temper
   it in a dragon forge, then finish it with The Colosseum or Crimson Threads. Evocation (Shield), Nature (Oakskin)
   and Eldritch (Abyssal Shroud, once learned) work the same way, finished by Grand Sigil or Thousand Blades,
   World Tree or Full Bloom, and Black Coffin or The Gaze.
2. **Thirst.** Take some damage, then hit a mob: you heal a fifth of the health each hit takes, sweeps included.
   Spells cast while holding it heal nothing.
3. **Covenant.** A fully charged hit sends a row of evoker fangs at the target; the sword then greys out for 3 s.
4. **Briar.** Hits poison (not undead, as in vanilla) and slow.
5. **Hush.** Hits deal 4 extra damage even through netherite. A player you hit goes dark for 3 s.
6. **Blood, Evocation and Nature armour.** Wear each in first and third person, walk, swing, and judge the look.
   The Evocation sash tail should swing with the left leg. Nature's leaves should be see-through like leaf blocks,
   and its vine sits on the left forearm only. Screenshots are welcome.
7. **Apex domains linger.** Two Apex spells cast in the same place within a few seconds can clash. If a second
   forging seems to do nothing, wait for the first spell's domain to fade.
