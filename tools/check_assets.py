#!/usr/bin/env python
"""Static client-asset check (the GameTest server never loads models, textures or lang).

    python tools/check_assets.py build/gametest-run/ds_registry.txt

Every registered item needs a model whose textures exist and a lang name; every block needs a blockstate whose
models exist and a lang name; every effect needs an icon and a lang name. Every translatable key used in Java must
be in en_us.json. Exits 1 on any problem.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MOD = "dragonsteel_schools"
A = ROOT / "src/main/resources/assets" / MOD
problems = []


def texture_exists(ref):
    ns, path = ref.split(":", 1) if ":" in ref else ("minecraft", ref)
    if ns == "minecraft":
        return True   # vanilla textures (cauldron sides) are always there
    return (ROOT / "src/main/resources/assets" / ns / "textures" / f"{path}.png").exists()


def check_model(rel):
    path = A / "models" / f"{rel}.json"
    if not path.exists():
        problems.append(f"missing model {rel}")
        return
    model = json.loads(path.read_text(encoding="utf-8"))
    for key, ref in model.get("textures", {}).items():
        if not ref.startswith("#") and not texture_exists(ref):
            problems.append(f"model {rel}: texture {key} -> {ref} missing")
    parent = model.get("parent", "")
    if parent.startswith(MOD + ":"):
        check_model(parent.split(":", 1)[1])


def main():
    registry = [line.split() for line in Path(sys.argv[1]).read_text(encoding="utf-8").splitlines() if line.strip()]
    lang = json.loads((A / "lang/en_us.json").read_text(encoding="utf-8"))
    counts = {}
    for kind, name in registry:
        counts[kind] = counts.get(kind, 0) + 1
        if kind == "item":
            check_model(f"item/{name}")
            if f"item.{MOD}.{name}" not in lang:
                problems.append(f"no lang for item {name}")
        elif kind == "block":
            bs = A / "blockstates" / f"{name}.json"
            if not bs.exists():
                problems.append(f"missing blockstate {name}")
            else:
                for variant in json.loads(bs.read_text(encoding="utf-8"))["variants"].values():
                    check_model(variant["model"].split(":", 1)[1])
            if f"block.{MOD}.{name}" not in lang:
                problems.append(f"no lang for block {name}")
        elif kind == "effect":
            if not (A / "textures/mob_effect" / f"{name}.png").exists():
                problems.append(f"no icon for effect {name}")
            if f"effect.{MOD}.{name}" not in lang:
                problems.append(f"no lang for effect {name}")
    for school in ("holy", "ender"):
        for f in (f"geo/{school}_dragonsteel_plate.geo.json", f"textures/models/armor/{school}_dragonsteel_plate.png",
                  f"textures/models/armor/{school}_dragonsteel_plate_glowmask.png", "animations/dragonsteel_plate.animation.json"):
            if not (A / f).exists():
                problems.append(f"missing armour asset {f}")
    java = "\n".join(p.read_text(encoding="utf-8") for p in (ROOT / "src/main/java").rglob("*.java"))
    for key in sorted(set(re.findall(r'"((?:item|message|effect|block|itemGroup|death)\.dragonsteel_schools(?:\.[a-z_.]+)?)"', java))):
        if not key.endswith(".") and key not in lang:   # keys ending in "." are prefixes built at runtime
            problems.append(f"lang key used in Java but missing: {key}")
    print(f"checked {counts}")
    for p in problems:
        print("PROBLEM", p)
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
