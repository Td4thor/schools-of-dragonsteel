# Manual test plan: Ice and Fire: Schools of Dragonsteel (Dragonsteel Schools Test instance)

Instance: `C:/Users/owner/curseforge/minecraft/Instances/Dragonsteel Schools Test` (Ice and Fire beta-5, Spellbooks
2.3.2, Iron's 3.16.3, Apex Arcana 1.3.0, JEI, this mod). Make a new creative world with cheats on.

1. **Cauldron.** `/give @s minecraft:dragon_breath 3`, place a cauldron, right-click it three times: pink liquid,
   glass bottles back. Look at it and cast Heal (any Holy spell): gold liquid. Draw three Holy Dragon Blood with glass
   bottles. Repeat with Evasion (any Ender spell) for violet Ender blood. A Fire spell should change nothing.
2. **Tempering.** Build any dragon forge, load iron ingots and Holy blood, and have a dragon of that element breathe
   on it: Tempered Holy Steel, one per 50 s of breath. JEI lists the recipe under the forge.
3. **Finishing.** With tempered steel in the forge (`/give @s dragonsteel_schools:tempered_holy_steel 16` saves time),
   cast a Holy spell of Legendary rarity at it (Heal at level 7 or 8, or Angel Wings at any level). All of it turns
   into Holy Dragonsteel Ingots. A lower-rarity Holy spell only shows "Only a Holy spell of Legendary rarity can finish
   this steel". Apex spells still work: Reckoning or Gates of Heaven (try looking away during Reckoning's windup).
   Ender: Black Hole, or Dimension Cut / Grip of the Void. A Holy cast must leave Ender steel alone.
   **Apex Only add-on:** put `schools_of_dragonsteel_apex_only-*.jar` in `mods/` too. Now only the Apex spells work,
   a Legendary Heal shows "Only a Holy Apex spell can finish this steel", and the tempered steel's tooltip says
   "...with a Holy Apex spell". The log says `finishing rule APEX_ONLY (forced by the Apex Only add-on)`.
4. **Gear.** Craft armour (ingots, the school rune, any dragon scales), Dawn/Elsewhere and the tools (ingots and
   wither bones), and the staff (Spellbooks' base Dragon Priest staff plus school blood in the forge).
5. **Dawn.** Hit a zombie: gold flames on it, big damage. Knock it into water: the flames stay. Milk cures a player.
6. **Elsewhere.** Hold it (either hand) and let a skeleton shoot you: you step away instead. Melee still hits.
   In the hand (0.1.0-dev.17) the tip and middle length hover apart on slow layered drifts, and every few seconds
   one blinks a little way off and drifts home. Each swing flings them apart (the tip about a quarter-block, out to
   the left in first person; the middle the other way); they stay apart while the arm comes back, ease home and
   settle with a small wobble, about 0.85 s in all, leaving faint violet afterimages while they move fast. Swing
   again quickly and they carry on from where they were (no pop). A dodge shatters the whole blade: ten shards burst
   out every way (in first person a ring round the blade, all of it on screen), spin and hang, then are drawn home
   along flickering threads from the Eye, spiralling in, guard first and point last, with a glassy break at the
   start and a chime as the point returns (about 1.1 s). Where you stood, the blade's fragments, white sparks and
   violet motes burst every way (needs particles above Minimal); portal motes swirl where you land. Pulsing beams
   with a running glint span both cuts at rest. Inventory, dropped item and item frames still show the flat sprite.
7. **JEI (1.0.0).** With JEI installed, look up a school's blood (School Dragon Blood page), its tempered steel
   (Dragonsteel Finishing: one page per spell that finishes it, Apex spells first) and any item's information page.
   With the Apex Only add-on on the server, the Legendary pages say they do not apply.
8. **Screenshots for the art pass.** Both armour sets front, back and side (and each piece alone), Dawn and Elsewhere
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

Their forging works exactly like Holy and Ender. Every school has its own armour: Blood (dev.4), Evocation (dev.5),
Nature (dev.6) and Eldritch (dev.7).

1. **Blood.** Cast any Blood spell (Heartstop works) at a cauldron of dragon's breath for Blood dragon blood. Temper
   it in a dragon forge, then finish it with a Legendary Blood spell, The Colosseum or Crimson Threads. Evocation
   (Shield), Nature (Oakskin) and Eldritch (Abyssal Shroud, once learned) work the same way, finished by a Legendary
   spell of the school (every Eldritch spell is Legendary at any level; Wololo never counts) or by Grand Sigil or
   Thousand Blades, World Tree or Full Bloom, and Black Coffin or The Gaze.
2. **Thirst.** Take some damage, then hit a mob: you heal a fifth of the health each hit takes, sweeps included.
   Spells cast while holding it heal nothing.
3. **Covenant.** A fully charged hit sends a row of evoker fangs at the target; the sword then greys out for 3 s.
4. **Briar.** Hits poison (not undead, as in vanilla) and slow.
5. **Hush.** Hits deal 4 extra damage even through netherite. A player you hit goes dark for 3 s.
6. **Blood, Evocation, Nature and Eldritch armour.** Wear each in first and third person, walk, swing, and judge
   the look. The Evocation sash tail should swing with the left leg. Nature's leaves should be see-through like leaf
   blocks, and its vine sits on the left forearm only. Eldritch's sculk grows on the left shoulder only. With a full
   set on, no skin should show at the waist. Screenshots are welcome.
7. **Apex domains linger.** Two Apex spells cast in the same place within a few seconds can clash. If a second
   forging seems to do nothing, wait for the first spell's domain to fade.

## Staves (0.1.0-dev.10)

The six Dragon Priest staves are rebuilt as full 3D models (`tools/generate_staves.py`; software previews with
`tools/render_item_model.py`, sheet in `docs/art/staves_preview.png`). `/give @s dragonsteel_schools:gilded_dragon_priest_staff`
(also `umbral_`, `sanguine_`, `emerald_`, `verdant_`, `abyssal_`). Check each in the inventory, in first person and
in third person (F5, both views), by day and at night: the sun core and rays, the crystal and Eye of Ender, the blood
jewel, the emeralds, the berries, and the great eye with every tendril tip should glow in the dark. Look for
flicker where parts overlap, parts that seem to hang loose, and whether the heads sit well in the hand next to
Spellbooks' Crimson, Silver and Thunderous staves.

## Swords (0.1.0-dev.11)

Elsewhere, Thirst, Covenant, Briar and Hush have their own drawn sprites now (they were recolours of Ice and Fire's
ice dragonsteel sword). `/give @s dragonsteel_schools:elsewhere` (also `thirst`, `covenant`, `briar`, `hush`). Check
each in the inventory and the hotbar, in first person, in third person (F5) and in an item frame. The hand should
close on the grip, as it does on Dawn; the sprites share Dawn's hilt position and reach. Covenant and Briar are a
little shorter than the others by design (a forked point and a bowed blade). The powers are unchanged.
