# 1.0.0 release verification

Built 2026-11-17 from the tree tagged `v1.0.0`, JDK 17.0.20, ForgeGradle 6, Forge 1.20.1-47.4.10.

| Check | Result | Evidence |
|---|---|---|
| `gradlew clean build verifyGameTests` | BUILD SUCCESSFUL; **All 27 required tests passed** | `gametest.log` |
| Resource scan (`tools/check_assets.py`) | OK: 78 item, 7 block, 1 effect models checked | run before the gate |
| Plain Forge server, the jar alone (plus its mandatory closure: Iron's Spells 3.16.3, irons_lib, Curios, GeckoLib, playerAnimator) | `Done`, clean stop; Ice and Fire, Spellbooks and Apex Arcana reported absent; rule LEGENDARY | `server_smoke_jar_alone.txt` |
| Plain Forge server with every optional dependency (Ice and Fire beta-5, Citadel, Ice and Fire: Spellbooks 2.3.2, Apex Arcana 1.3.0, JEI 15.56) and the Apex Only add-on | `Done`, clean stop; all loaded; rule APEX_ONLY (forced by the add-on) | `server_smoke_all_optional.txt` |
| Dev client with JEI 15.56 (`run_client_qa.sh`, no schools) | 81 Dragonsteel Finishing pages, 6 School Dragon Blood pages, information pages open; no plugin errors | `jei_pages.png` |

SHA-256:

- `schools_of_dragonsteel-1.20.1-1.0.0.jar` `4966bcb801f4e664670e393139fcd3708680b96cb0fe53afae8cb283f318ecce`
- `schools_of_dragonsteel_apex_only-1.20.1-1.0.0.jar` `5224d92a999d8cb0c75fff11b035ddb74521253ef0e81dca2edc2bc2fcb21309`
- `schools_of_dragonsteel-1.20.1-1.0.0-sources.jar` `6803f3175aa8a1baf1c7ac9c7377964f49dd2e31c323dc4e5ea56d94de509909`

The sources jar was rebuilt once after the gate, when its include list was trimmed (art and verification images
left out). That edit to `build.gradle` touches only the `releaseSourcesJar` task, so the main and add-on jars are the
gate's own.

Not run: a production client (Tad's own instance), multiplayer with two clients, shaders. No JUnit tests exist in
this project.
