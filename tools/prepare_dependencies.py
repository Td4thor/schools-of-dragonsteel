#!/usr/bin/env python
"""Copy the third-party jars this project builds and tests against into libs/ (they are never committed).

    python tools/prepare_dependencies.py [mods folder]

The default folder is Tad's "Dragonsteel Schools Test" CurseForge instance. Any folder holding these jars will do,
for example a fresh download of each from CurseForge. The Gradle build reads them from libs/ by these exact names
(flatDir, `local:<name>:<version>` in build.gradle), and tools/generate_textures.py reads Ice and Fire's textures
from its jar.
"""
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = Path("C:/Users/owner/curseforge/minecraft/Instances/Dragonsteel Schools Test/mods")

# libs/ name -> the CurseForge file name it comes from (gradle.properties pins the versions)
JARS = {
    "iceandfire-2.1.13b5.jar": "iceandfire-2.1.13-1.20.1-beta-5.jar",
    "citadel-2.6.3.jar": "citadel-2.6.3-1.20.1.jar",
    "ice_and_fire_spellbooks-2.3.2.jar": "ice_and_fire_spellbooks-2.3.2-1.20.1.jar",
    "grandsigil-1.3.0.jar": "grandsigil-1.20.1-forge-1.3.0.jar",
}


def main(folder: Path) -> int:
    libs = ROOT / "libs"
    libs.mkdir(exist_ok=True)
    missing = []
    for target, source in JARS.items():
        if (libs / target).exists():
            print(f"have    {target}")
            continue
        found = folder / source
        if not found.exists():
            stem = source.split("-")[0]
            candidates = sorted(folder.glob(f"{stem}*.jar"))
            found = candidates[0] if len(candidates) == 1 else None
        if found is None:
            missing.append(source)
            continue
        shutil.copy2(found, libs / target)
        print(f"copied  {found.name} -> libs/{target}")
    for source in missing:
        print(f"MISSING {source}: download it from CurseForge into {folder} or libs/")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT))
