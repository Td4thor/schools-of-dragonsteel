#!/usr/bin/env python
"""Generate every Ice and Fire: Schools of Dragonsteel JSON: item models, blockstates, lang, recipes, tags, loot, damage type.

Deterministic and rerunnable:  python tools/generate_data.py

Adding a school later = one SCHOOLS entry here (+ the SchoolSteel constant and its art).
Porting to Ice and Fire 2 = edit IAF below (forge recipe type, dragon types, block and tag ids).
"""
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "src/main/resources"
MOD = "dragonsteel_schools"
A = RES / "assets" / MOD
D = RES / "data" / MOD

SCHOOLS = {
    "holy": {
        "name": "Holy", "sword": "dawn", "sword_name": "Dawn",
        "staff": "gilded_dragon_priest_staff", "staff_name": "Gilded Dragon Priest Staff",
        "rune": "irons_spellbooks:holy_rune",
    },
    "ender": {
        "name": "Ender", "sword": "elsewhere", "sword_name": "Elsewhere",
        "staff": "umbral_dragon_priest_staff", "staff_name": "Umbral Dragon Priest Staff",
        "rune": "irons_spellbooks:ender_rune",
    },
    "blood": {
        "name": "Blood", "sword": "thirst", "sword_name": "Thirst",
        "staff": "sanguine_dragon_priest_staff", "staff_name": "Sanguine Dragon Priest Staff",
        "rune": "irons_spellbooks:blood_rune",
        "sword_power": "Heals you for %s%% of the health its hits take",
    },
    "evocation": {
        "name": "Evocation", "sword": "covenant", "sword_name": "Covenant",
        "staff": "emerald_dragon_priest_staff", "staff_name": "Emerald Dragon Priest Staff",
        "rune": "irons_spellbooks:evocation_rune",
        "sword_power": "A fully charged hit calls %s evoker fangs at the foe (every %s s)",
    },
    "nature": {
        "name": "Nature", "sword": "briar", "sword_name": "Briar",
        "staff": "verdant_dragon_priest_staff", "staff_name": "Verdant Dragon Priest Staff",
        "rune": "irons_spellbooks:nature_rune",
        "sword_power": "Hits poison for %s s and slow for %s s",
    },
    "eldritch": {
        "name": "Eldritch", "sword": "hush", "sword_name": "Hush",
        "staff": "abyssal_dragon_priest_staff", "staff_name": "Abyssal Dragon Priest Staff",
        "rune": "minecraft:echo_shard",   # Iron's Spells has no Eldritch rune
        "sword_power": "Hits deal %s extra damage armour cannot stop, and blind players for %s s",
    },
}

# Everything that names Ice and Fire lives here.
IAF = {
    "modid": "iceandfire",
    "forge_recipe": "iceandfire:dragonforge",
    "dragon_types": ("fire", "ice", "lightning"),
    "cook_time": 1000,                                   # same as Ice and Fire's own dragonsteel
    "cores": [f"iceandfire:dragonforge_{t}_core{d}" for t in ("fire", "ice", "lightning") for d in ("", "_disabled")],
    "parts": [f"iceandfire:dragonforge_{t}_{p}" for t in ("fire", "ice", "lightning") for p in ("brick", "input")],
    "handle_tag": "forge:bones/wither",
    "scales_tag": "iceandfire:scales/dragon",
}
SPELLBOOKS = {"modid": "ice_and_fire_spellbooks", "base_staff": "ice_and_fire_spellbooks:dragon_priest_staff",
              "steel_tag": "ice_and_fire_spellbooks:dragon_steel"}

PIECES = ("helmet", "chestplate", "leggings", "boots")
TOOLS = ("pickaxe", "axe", "shovel", "hoe")

# Ice and Fire's big-sword display (32x32 sprite scaled up in hand)
BIG_SWORD_DISPLAY = {
    "thirdperson_righthand": {"rotation": [0, -90, 55], "translation": [0, 7.0, 0], "scale": [1.7, 1.7, 0.85]},
    "thirdperson_lefthand": {"rotation": [0, 90, -55], "translation": [0, 7.0, 0], "scale": [1.7, 1.7, 0.85]},
    "firstperson_righthand": {"rotation": [-20, -90, 10], "translation": [1.13, 5.2, -0.26], "scale": [1.36, 1.36, 0.68]},
    "firstperson_lefthand": {"rotation": [-20, -90, -80], "translation": [1.13, 5.2, -0.26], "scale": [1.36, 1.36, 0.68]},
    "gui": {"rotation": [0, 0, 0], "translation": [0, 0, 0], "scale": [1.1, 1.1, 1.1]},
}
# Ice and Fire's dragonsteel axe display: the 32x32 axe sprite drawn big in hand, like the sword
BIG_AXE_DISPLAY = {
    "thirdperson_righthand": {"rotation": [0, -90, 55], "translation": [0, 5.0, 0], "scale": [1.7, 1.7, 0.85]},
    "thirdperson_lefthand": {"rotation": [0, 90, -55], "translation": [0, 5.0, 0], "scale": [1.7, 1.7, 0.85]},
    "firstperson_righthand": {"rotation": [-20, -90, 10], "translation": [1.13, 5.2, -0.26], "scale": [1.36, 1.36, 0.68]},
    "firstperson_lefthand": {"rotation": [-20, -90, -80], "translation": [1.13, 5.2, -0.26], "scale": [1.36, 1.36, 0.68]},
    "gui": {"rotation": [0, 0, 0], "translation": [-1, -1, 0], "scale": [1.1, 1.1, 1.1]},
}
written = []


def write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((json.dumps(obj, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))
    written.append(path)


def mod_loaded(*mods):
    return [{"type": "forge:mod_loaded", "modid": m} for m in mods]


def item(i):
    return {"item": f"{MOD}:{i}"}


# ---------------------------------------------------------------------------------------------
def models():
    for s, cfg in SCHOOLS.items():
        flat = [f"{s}_dragon_blood", f"tempered_{s}_steel", f"{s}_dragonsteel_ingot"] + [f"{s}_dragonsteel_{p}" for p in PIECES]
        for name in flat:
            write(A / "models/item" / f"{name}.json", {"parent": "minecraft:item/generated", "textures": {"layer0": f"{MOD}:item/{name}"}})
        for t in TOOLS:
            name = f"{s}_dragonsteel_{t}"
            if t == "axe":   # Ice and Fire draws its dragonsteel axe big, from a 32x32 sprite
                write(A / "models/item" / f"{name}.json", {"parent": "minecraft:item/generated",
                                                          "textures": {"layer0": f"{MOD}:item/{name}"}, "display": BIG_AXE_DISPLAY})
            else:
                write(A / "models/item" / f"{name}.json", {"parent": "minecraft:item/handheld", "textures": {"layer0": f"{MOD}:item/{name}"}})
        write(A / "models/item" / f"{cfg['sword']}.json",
              {"parent": "minecraft:item/generated", "textures": {"layer0": f"{MOD}:item/{cfg['sword']}"}, "display": BIG_SWORD_DISPLAY})
    from generate_textures import elsewhere_model_names   # Elsewhere's shards and hilt (ElsewhereRenderer); no items
    for name in elsewhere_model_names():
        write(A / "models/item" / f"{name}.json", {"parent": "minecraft:item/generated", "textures": {"layer0": f"{MOD}:item/{name}"}})


def blocks():
    cauldrons = {"dragons_breath_cauldron": "dragons_breath_still"}
    cauldrons.update({f"{s}_dragon_blood_cauldron": f"{s}_dragon_blood_still" for s in SCHOOLS})
    for block, liquid in cauldrons.items():
        variants = {}
        for level, template in ((1, "template_cauldron_level1"), (2, "template_cauldron_level2"), (3, "template_cauldron_full")):
            model = f"{block}_level{level}" if level < 3 else f"{block}_full"
            write(A / "models/block" / f"{model}.json", {
                "parent": f"minecraft:block/{template}",
                "textures": {"bottom": "minecraft:block/cauldron_bottom", "content": f"{MOD}:block/{liquid}",
                             "inside": "minecraft:block/cauldron_inner", "particle": "minecraft:block/cauldron_side",
                             "side": "minecraft:block/cauldron_side", "top": "minecraft:block/cauldron_top"}})
            variants[f"level={level}"] = {"model": f"{MOD}:block/{model}"}
        write(A / "blockstates" / f"{block}.json", {"variants": variants})
        write(D / "loot_tables/blocks" / f"{block}.json", {
            "type": "minecraft:block",
            "pools": [{"bonus_rolls": 0.0, "conditions": [{"condition": "minecraft:survives_explosion"}],
                       "entries": [{"type": "minecraft:item", "name": "minecraft:cauldron"}], "rolls": 1.0}],
            "random_sequence": f"{MOD}:blocks/{block}"})
    return list(cauldrons)


# ---------------------------------------------------------------------------------------------
def lang(cauldrons):
    L = {
        "itemGroup.dragonsteel_schools": "Ice and Fire: Schools of Dragonsteel",
        "effect.dragonsteel_schools.holy_fire": "Holy Fire",
        "death.attack.dragonsteel_schools.holy_fire": "%1$s was purified by holy fire",
        "death.attack.dragonsteel_schools.holy_fire.player": "%1$s was purified by holy fire lit by %2$s",
        "block.dragonsteel_schools.dragons_breath_cauldron": "Cauldron of Dragon's Breath",
        "item.dragonsteel_schools.dragon_blood.lore": "Dragon's breath taken by the %s school",
        "item.dragonsteel_schools.tempered_steel.lore.legendary": "Breath-tempered. Finish it at the dragon forge with a %s spell of Legendary rarity",
        "item.dragonsteel_schools.tempered_steel.lore.apex": "Breath-tempered. Finish it at the dragon forge with a %s Apex spell",
        "item.dragonsteel_schools.dragonsteel_ingot.lore": "%s dragonsteel",
        "message.dragonsteel_schools.cauldron.attuned": "The dragon's breath takes the %s school",
        "message.dragonsteel_schools.forge.done": "Forged %s × %s",
        "message.dragonsteel_schools.forge.nothing": "No tempered %s steel in this forge",
        "message.dragonsteel_schools.forge.too_much": "Too much tempered %s steel: one cast finishes at most %s",
        "message.dragonsteel_schools.forge.needs.legendary": "Only a %s spell of Legendary rarity can finish this steel",
        "message.dragonsteel_schools.forge.needs.apex": "Only a %s Apex spell can finish this steel",
        "item.dragonsteel_schools.dawn.holy_fire": "Sets foes alight with holy fire for %s s (water will not quench it)",
        "item.dragonsteel_schools.dawn.undead": "+%s damage against undead",
        "item.dragonsteel_schools.elsewhere.dodge_all": "While held, step aside from arrows and spell projectiles",
        "item.dragonsteel_schools.elsewhere.dodge_arrows": "While held, step aside from arrows",
    }
    for s, cfg in SCHOOLS.items():
        n = cfg["name"]
        L[f"school.dragonsteel_schools.{s}"] = n
        L[f"item.dragonsteel_schools.{s}_dragon_blood"] = f"{n} Dragon Blood"
        L[f"item.dragonsteel_schools.tempered_{s}_steel"] = f"Tempered {n} Steel"
        L[f"item.dragonsteel_schools.{s}_dragonsteel_ingot"] = f"{n} Dragonsteel Ingot"
        for p in PIECES:
            L[f"item.dragonsteel_schools.{s}_dragonsteel_{p}"] = f"{n} Dragonsteel {p.capitalize()}"
        for t in TOOLS:
            L[f"item.dragonsteel_schools.{s}_dragonsteel_{t}"] = f"{n} Dragonsteel {t.capitalize()}"
        L[f"item.dragonsteel_schools.{cfg['sword']}"] = cfg["sword_name"]
        if "sword_power" in cfg:
            L[f"item.dragonsteel_schools.{cfg['sword']}.power"] = cfg["sword_power"]
        L[f"item.dragonsteel_schools.{cfg['staff']}"] = cfg["staff_name"]
        L[f"block.dragonsteel_schools.{s}_dragon_blood_cauldron"] = f"Cauldron of {n} Dragon Blood"
    for c in cauldrons:
        assert f"block.dragonsteel_schools.{c}" in L, c
    write(A / "lang/en_us.json", dict(sorted(L.items())))


# ---------------------------------------------------------------------------------------------
def recipes():
    R = D / "recipes"
    for s, cfg in SCHOOLS.items():
        blood, tempered, ingot = f"{s}_dragon_blood", f"tempered_{s}_steel", f"{s}_dragonsteel_ingot"
        # 1. The dragon's part: any dragon's breath tempers iron with school blood (Ice and Fire forge recipe).
        for t in IAF["dragon_types"]:
            write(R / "dragonforge" / f"{tempered}_{t}.json", {
                "type": IAF["forge_recipe"], "conditions": mod_loaded(IAF["modid"]),
                "dragon_type": t, "cook_time": IAF["cook_time"],
                "input": {"tag": "forge:ingots/iron"}, "blood": item(blood), "result": item(tempered)})
            # Spellbooks' base Dragon Priest staff + school blood -> the school staff (as Spellbooks does it)
            write(R / "dragonforge" / f"{cfg['staff']}_{t}.json", {
                "type": IAF["forge_recipe"], "conditions": mod_loaded(IAF["modid"], SPELLBOOKS["modid"]),
                "dragon_type": t, "cook_time": IAF["cook_time"],
                "input": {"item": SPELLBOOKS["base_staff"]}, "blood": item(blood), "result": item(cfg["staff"])})
        # 2. The Apex part: the school's Apex spell finishes tempered steel into dragonsteel.
        write(R / "apex" / f"{ingot}.json", {
            "type": f"{MOD}:apex_forging", "school": s, "input": item(tempered), "result": item(ingot)})
        # 3. Gear. Armour follows Spellbooks' Dragon Priest patterns (school rune, any dragon scales).
        d, r = item(ingot), {"item": cfg["rune"]}
        scales = {"tag": IAF["scales_tag"]}
        armour = {
            "helmet": (["drd", "d d"], {"d": d, "r": r}, False),
            "chestplate": (["d d", "drd", "sds"], {"d": d, "r": r, "s": scales}, True),
            "leggings": (["srs", "d d", "d d"], {"d": d, "r": r, "s": scales}, True),
            "boots": (["s s", "drd"], {"d": d, "r": r, "s": scales}, True),
        }
        for p, (pattern, key, needs_iaf) in armour.items():
            rec = {"type": "minecraft:crafting_shaped", "category": "equipment", "pattern": pattern, "key": key,
                   "result": item(f"{s}_dragonsteel_{p}"), "show_notification": True}
            if needs_iaf:
                rec = {"type": rec.pop("type"), "conditions": mod_loaded(IAF["modid"]), **rec}
            write(R / f"{s}_dragonsteel_{p}.json", rec)
        # Weapons and tools follow Ice and Fire's dragonsteel patterns (wither bone handles).
        h = {"tag": IAF["handle_tag"]}
        tools = {cfg["sword"]: ["M", "M", "H"], f"{s}_dragonsteel_pickaxe": ["MMM", " H ", " H "],
                 f"{s}_dragonsteel_axe": ["MM", "MH", " H"], f"{s}_dragonsteel_shovel": ["M", "H", "H"],
                 f"{s}_dragonsteel_hoe": ["MM", " H", " H"]}
        for name, pattern in tools.items():
            write(R / f"{name}.json", {"type": "minecraft:crafting_shaped", "conditions": mod_loaded(IAF["modid"]),
                                       "category": "equipment", "pattern": pattern, "key": {"M": d, "H": h},
                                       "result": item(name), "show_notification": True})


def tags(cauldrons):
    opt = lambda ids: [{"id": i, "required": False} for i in ids]
    write(D / "tags/blocks/dragon_forge_cores.json", {"replace": False, "values": opt(IAF["cores"])})
    write(D / "tags/blocks/dragon_forge_parts.json", {"replace": False, "values": opt(IAF["parts"])})
    write(D / "tags/blocks/needs_school_dragonsteel.json", {"replace": False, "values": []})
    ids = [f"{MOD}:{c}" for c in cauldrons]
    mc = RES / "data/minecraft"
    write(mc / "tags/blocks/cauldrons.json", {"replace": False, "values": ids})
    write(mc / "tags/blocks/mineable/pickaxe.json", {"replace": False, "values": ids})
    for kind, plural in (("pickaxe", "pickaxes"), ("axe", "axes"), ("shovel", "shovels"), ("hoe", "hoes")):
        write(mc / f"tags/items/{plural}.json", {"replace": False, "values": [f"{MOD}:{s}_dragonsteel_{kind}" for s in SCHOOLS]})
    write(mc / "tags/items/swords.json", {"replace": False, "values": [f"{MOD}:{c['sword']}" for c in SCHOOLS.values()]})
    write(RES / "data/ice_and_fire_spellbooks/tags/items/dragon_steel.json",
          {"replace": False, "values": [f"{MOD}:{s}_dragonsteel_ingot" for s in SCHOOLS]})
    write(RES / "data/forge/tags/items/ingots.json", {"replace": False, "values": [f"{MOD}:{s}_dragonsteel_ingot" for s in SCHOOLS]})
    for s in SCHOOLS:
        write(RES / f"data/forge/tags/items/ingots/{s}_dragonsteel.json", {"replace": False, "values": [f"{MOD}:{s}_dragonsteel_ingot"]})
    # Holy fire: ignores armour like ordinary burning, no knockback; not fire, so Fire Resistance does not help.
    for t in ("bypasses_armor", "no_impact"):
        write(mc / f"tags/damage_type/{t}.json", {"replace": False, "values": [f"{MOD}:holy_fire"]})
    write(D / "damage_type/holy_fire.json", {"exhaustion": 0.0, "message_id": f"{MOD}.holy_fire", "scaling": "never", "effects": "burning"})


def animations():
    """GeckoLib wants an animation file per model even for static plate (Iron's ships an empty 'idle' too)."""
    write(A / "animations/dragonsteel_plate.animation.json",
          {"format_version": "1.8.0", "animations": {"idle": {"loop": True}}, "geckolib_format_version": 2})


def main():
    for sub in ("models", "blockstates", "lang", "animations"):
        shutil.rmtree(A / sub, ignore_errors=True)
    shutil.rmtree(RES / "data", ignore_errors=True)
    models()
    import generate_staves   # the staff models and their sheets (needs Pillow); models/ was just wiped
    problems = generate_staves.generate()
    if problems:
        raise SystemExit("\n".join(problems))
    animations()
    cauldrons = blocks()
    lang(cauldrons)
    recipes()
    tags(cauldrons)
    print(f"{len(written)} JSON files written")


if __name__ == "__main__":
    main()
