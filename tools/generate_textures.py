#!/usr/bin/env python
"""Generate the Ice and Fire: Schools of Dragonsteel item, block, effect and fire textures.

Deterministic and rerunnable:  python tools/generate_textures.py

Sources (read straight from jars, never committed):
  * Ice and Fire 2.1.13 (libs/iceandfire-*.jar, LGPL-3.0): dragonsteel ice tools, sword, ingot and blood bottle
    are palette-remapped per school, so school dragonsteel reads as part of the same family.
  * Minecraft 1.20.1 client assets (ForgeGradle cache): fire_0/fire_1, water_still and the fire resistance
    effect icon are recoloured for holy fire, the cauldron liquids and the Holy Fire effect.
Dawn and every glow/halo detail are drawn here. The staves (models and sheets) come from generate_staves.py.
See docs/art/CREDITS.md.
"""
import io
import math
import random
import zipfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "src/main/resources/assets/dragonsteel_schools"
IAF_JAR = next((ROOT / "libs").glob("iceandfire-*.jar"))
MC_JAR = Path.home() / ".gradle/caches/forge_gradle/minecraft_repo/versions/1.20.1/client-extra.jar"


def hexes(*cs):
    return [tuple(int(c.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)) + (255,) for c in cs]


R = {
    "silver": hexes("#2e303c", "#4b4f60", "#71778b", "#9aa1b4", "#c1c7d5", "#dde2eb", "#f2f4f8", "#ffffff"),
    "gold": hexes("#3f2306", "#6e400d", "#9c6715", "#c99022", "#e6b239", "#f6d259", "#ffe993", "#fff8d4"),
    "sun": hexes("#d99a24", "#f2bf40", "#ffd95c", "#ffe88f", "#fff4c2", "#fffdf0"),
    "obsid": hexes("#050308", "#0c0814", "#140e20", "#1d152d", "#281e3c", "#35294f", "#483968", "#64508e"),
    "void": hexes("#160a24", "#231139", "#331951", "#45226c", "#5a2d89", "#7240a6", "#9060c4", "#b38ade"),
    "violet": hexes("#6420c2", "#8838ec", "#a85fff", "#c58aff", "#e0baff", "#f5e6ff"),
    "purpur": hexes("#4a3150", "#664769", "#86618a", "#a57ca7", "#c19cc3", "#dbbedb"),
    "endst": hexes("#6c6a43", "#97955d", "#c1bf81", "#dbdb9f", "#ecedc0"),
    # Blood, Evocation, Nature, Eldritch
    "crimson": hexes("#1c0204", "#3a060b", "#5c0b13", "#82111c", "#a81a27", "#cc2a36", "#e8505a", "#ff8a8f"),
    "emerald": hexes("#05301a", "#0a4d2a", "#11703c", "#17944f", "#20b863", "#3ddb7a", "#7ff0a9", "#c4ffd9"),
    "slate": hexes("#141615", "#1f2321", "#2b302d", "#3a403c", "#4c534e", "#616963", "#7b847d", "#9aa29b"),
    "moss": hexes("#14200f", "#1f3217", "#2c4720", "#3d5f2a", "#527b34", "#6f9c40", "#95c25a", "#c2e584"),
    "bark": hexes("#1a120b", "#2a1d12", "#3b2a1a", "#4f3923", "#644a2e", "#7c5d3a", "#987449", "#b48d5c"),
    "sculk": hexes("#020a0d", "#051419", "#0a2027", "#0f2e37", "#154049", "#1d555f", "#2a6f78", "#3f8c93"),
    "cyan": hexes("#0b6b74", "#11949f", "#1fc0cc", "#29dfeb", "#7ff2f8", "#d4fdff"),
    "bone": hexes("#6f6a58", "#958f78", "#bab49b", "#d8d3bd", "#efebda"),
}

# Per-school colour roles. ramp names refer to R; ranges are (start, end) positions along the ramp.
TEX = {
    "holy": dict(metal=("silver", 0.3, 0.9), accent=("sun", 0.15, 1.0),
                 tempered=("silver", 0.1, 0.85), fleck=("gold", 0.55), fleck_rule=(7, 3, 11),
                 ingot_lo=("gold", 0.15, 1.0), ingot_hi=("sun", 0.2, 1.0), ingot_split=0.82,
                 blood=("sun", 0.0, 1.0), liquid=("sun", 2.2), spark=None),
    "ender": dict(metal=("obsid", 0.2, 0.95), accent=("violet", 0.1, 1.0),
                  tempered=("obsid", 0.25, 1.0), fleck=("purpur", 0.4), fleck_rule=(5, 7, 13),
                  ingot_lo=("void", 0.05, 1.0), ingot_hi=("violet", 0.3, 0.9), ingot_split=0.8,
                  blood=("void", 0.15, 1.0), liquid=("void", 2.0), spark="violet"),
    "blood": dict(metal=("crimson", 0.2, 0.9), accent=("gold", 0.3, 1.0),
                  tempered=("silver", 0.05, 0.7), fleck=("crimson", 0.6), fleck_rule=(3, 5, 11),
                  ingot_lo=("crimson", 0.05, 0.95), ingot_hi=("gold", 0.5, 0.95), ingot_split=0.84,
                  blood=("crimson", 0.1, 1.0), liquid=("crimson", 1.8), spark="gold"),
    "evocation": dict(metal=("slate", 0.25, 0.95), accent=("emerald", 0.2, 1.0),
                      tempered=("silver", 0.05, 0.75), fleck=("emerald", 0.6), fleck_rule=(5, 3, 13),
                      ingot_lo=("slate", 0.1, 1.0), ingot_hi=("emerald", 0.45, 1.0), ingot_split=0.78,
                      blood=("emerald", 0.15, 1.0), liquid=("emerald", 2.0), spark="gold"),
    "nature": dict(metal=("slate", 0.2, 0.9), accent=("moss", 0.35, 1.0),
                   tempered=("slate", 0.15, 0.9), fleck=("moss", 0.6), fleck_rule=(7, 5, 11),
                   ingot_lo=("bark", 0.05, 0.9), ingot_hi=("moss", 0.5, 1.0), ingot_split=0.78,
                   blood=("moss", 0.2, 1.0), liquid=("moss", 2.0), spark="moss"),
    "eldritch": dict(metal=("sculk", 0.2, 0.95), accent=("cyan", 0.1, 1.0),
                     tempered=("sculk", 0.25, 1.0), fleck=("bone", 0.6), fleck_rule=(5, 7, 13),
                     ingot_lo=("sculk", 0.05, 1.0), ingot_hi=("cyan", 0.3, 1.0), ingot_split=0.8,
                     blood=("sculk", 0.3, 1.0), liquid=("sculk", 2.0), spark="cyan"),
}
SCHOOLS = tuple(TEX)
SWORDS = {"ender": "elsewhere", "blood": "thirst", "evocation": "covenant", "nature": "briar", "eldritch": "hush"}


def along(spec, t):
    name, a, b = spec
    return ramp(name, a + (b - a) * t)


def ramp(name, t):
    """t in [0, 1] -> colour along the ramp."""
    r = R[name]
    return r[max(0, min(len(r) - 1, int(round(t * (len(r) - 1)))))]


def lum(p):
    return 0.299 * p[0] + 0.587 * p[1] + 0.114 * p[2]


def read_png(jar, path):
    with zipfile.ZipFile(jar) as z:
        return Image.open(io.BytesIO(z.read(path))).convert("RGBA")


def read_text(jar, path):
    with zipfile.ZipFile(jar) as z:
        return z.read(path).decode("utf-8")


def save(img, rel, mcmeta=None):
    path = ASSETS / "textures" / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, format="PNG")
    if mcmeta is not None:
        Path(str(path) + ".mcmeta").write_bytes((mcmeta.strip() + "\n").encode("utf-8"))


def remap(img, fn):
    out = Image.new("RGBA", img.size, (0, 0, 0, 0))
    src, dst = img.load(), out.load()
    for y in range(img.height):
        for x in range(img.width):
            p = src[x, y]
            if p[3] == 0:
                continue
            dst[x, y] = fn(p, x, y)
    return out


# ---------------------------------------------------------------------------------------------
# Dragonsteel tools, Elsewhere, ingots: remap Ice and Fire's ice dragonsteel
# ---------------------------------------------------------------------------------------------
def is_accent(p):
    return (p[2] > p[0] + 22 and lum(p) > 70) or lum(p) > 185


def steel_fn(school):
    c = TEX[school]

    def fn(p, x, y):
        L = lum(p)
        if L < 14:
            return R[c["metal"][0]][0]
        if is_accent(p):
            return along(c["accent"], min(1.0, max(0.0, (L - 70) / 185)))
        return along(c["metal"], min(1.0, max(0.0, (L - 14) / 80)))
    return fn


def ingot_fn(school, tempered=False):
    c = TEX[school]

    def fn(p, x, y):
        L = lum(p)
        t = min(1.0, max(0.0, (L - 20) / 235))
        if tempered:
            a, b, m = c["fleck_rule"]
            if (x * a + y * b) % m == 0 and 0.3 < t < 0.9:
                return ramp(*c["fleck"])
            return along(c["tempered"], t)
        split = c["ingot_split"]
        if t > split:
            return along(c["ingot_hi"], (t - split) / (1 - split))
        return along(c["ingot_lo"], t / split)
    return fn


def blood_fn(school):
    def fn(p, x, y):
        L = lum(p)
        if p[2] > p[0] + 30:   # the blue liquid
            t = min(1.0, max(0.0, (L - 40) / 200))
            return along(TEX[school]["blood"], t)
        return p               # glass, highlight and cork stay as they are
    return fn


# ---------------------------------------------------------------------------------------------
# Dawn: original 32x32 longsword, white-gold blade with a glowing fuller, sunburst guard
# ---------------------------------------------------------------------------------------------
def dawn():
    img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    px = img.load()
    # Sword axis runs from the pommel (bottom-left) to the tip (top-right) along the diagonal.
    # Parameterise each pixel by t (along the blade, 0 at the pommel) and s (across it).
    p0 = (3.0, 28.0)
    axis = (1 / math.sqrt(2), -1 / math.sqrt(2))
    perp = (1 / math.sqrt(2), 1 / math.sqrt(2))
    length = math.hypot(28.5 - 3.0, 28.0 - 3.5)

    def region(t, s):
        a = abs(s)
        if t < 1.6:                              # pommel: sun disc
            return ("pommel", a <= 1.9)
        if t < 6.2:                              # grip, wrapped gold
            return ("grip", a <= 0.75)
        if t < 7.9:                              # sunburst crossguard
            return ("guard", a <= 5.2 - abs(t - 7.05) * 1.4)
        blade_w = 1.75 if t < length - 4.5 else max(0.0, 1.75 * (length - t) / 4.5)
        return ("blade", a <= blade_w + 0.25 and t <= length)

    for y in range(32):
        for x in range(32):
            cx, cy = x + 0.5 - p0[0], y + 0.5 - p0[1]
            t = cx * axis[0] + cy * axis[1]
            s = cx * perp[0] + cy * perp[1]
            if t < -0.6:
                continue
            name, inside = region(t, s)
            if not inside:
                continue
            if name == "pommel":
                col = ramp("sun", 0.85) if abs(s) < 0.8 else ramp("gold", 0.6 if s < 0 else 0.4)
            elif name == "grip":
                col = ramp("gold", 0.45 if (int(t * 1.5)) % 2 else 0.3)
            elif name == "guard":
                edge = abs(s) > 3.4
                col = ramp("sun", 0.9) if abs(s) < 1.0 else ramp("gold", 0.8 if not edge else 0.55)
                if s > 0:
                    col = tuple(int(c * 0.86) for c in col[:3]) + (255,)
            else:
                a = abs(s)
                if a < 0.55:
                    col = ramp("sun", 0.55 + 0.45 * min(1.0, t / length + 0.2))     # glowing fuller
                elif s < 0:
                    col = ramp("silver", 0.95)                                       # lit edge
                else:
                    col = ramp("silver", 0.62)                                       # shaded edge
                if t > length - 1.2:
                    col = ramp("silver", 1.0)
            px[x, y] = col
    outline(img, R["gold"][0])
    return img


def outline(img, colour):
    """Vanilla-style dark 1px outline on the transparent side of every opaque edge."""
    px = img.load()
    w, h = img.size
    add = []
    for y in range(h):
        for x in range(w):
            if px[x, y][3]:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if 0 <= x + dx < w and 0 <= y + dy < h and px[x + dx, y + dy][3] and px[x + dx, y + dy] != colour:
                    add.append((x, y))
                    break
    for x, y in add:
        px[x, y] = colour


# ---------------------------------------------------------------------------------------------
# Holy fire, cauldron liquids, effect icon
# ---------------------------------------------------------------------------------------------
def holy_fire_frames(name):
    src = read_png(MC_JAR, f"assets/minecraft/textures/block/{name}.png")
    meta = read_text(MC_JAR, f"assets/minecraft/textures/block/{name}.png.mcmeta")

    def fn(p, x, y):
        L = lum(p) / 255
        # vanilla fire runs dark red -> orange -> yellow-white; holy fire runs gold -> pale gold -> white
        if L > 0.8:
            return ramp("sun", 1.0)
        if L > 0.55:
            return ramp("sun", 0.45 + (L - 0.55) * 2)
        return ramp("gold", 0.45 + L * 0.7)[:3] + (p[3],)
    return remap(src, fn), meta


def tinted_liquid(school):
    water = read_png(MC_JAR, "assets/minecraft/textures/block/water_still.png")
    meta = read_text(MC_JAR, "assets/minecraft/textures/block/water_still.png.mcmeta")
    rng = random.Random(f"liquid-{school}")

    def fn(p, x, y):
        L = lum(p) / 255     # vanilla water is grey and tinted per biome
        if school is None:   # dragon's breath: vanilla's pink-magenta cloud colours
            base = (0.86, 0.38, 0.76)
            return tuple(min(255, int(255 * (b * (0.55 + 0.75 * L)))) for b in base) + (235,)
        name, k = TEX[school]["liquid"]
        c = ramp(name, min(1.0, max(0.0, (L - 0.45) * k)))
        spark = TEX[school]["spark"]
        if spark and rng.random() < 0.012:
            c = ramp(spark, 0.9)
        return c[:3] + (245,)
    return remap(water, fn), meta


def effect_icon():
    """18x18: one frame of holy fire, gold-outlined so it reads on the inventory's grey."""
    fire, _ = holy_fire_frames("fire_0")
    frame = fire.crop((0, 0, 16, 16))
    img = Image.new("RGBA", (18, 18), (0, 0, 0, 0))
    img.paste(frame, (1, 1), frame)
    outline(img, R["gold"][1])
    return img


def main():
    for school in SCHOOLS:
        fn = steel_fn(school)
        for tool in ("pickaxe", "axe", "shovel", "hoe"):
            save(remap(read_png(IAF_JAR, f"assets/iceandfire/textures/item/dragonsteel_ice_{tool}.png"), fn),
                 f"item/{school}_dragonsteel_{tool}.png")
        ingot = read_png(IAF_JAR, "assets/iceandfire/textures/item/dragonsteel_ice_ingot.png")
        save(remap(ingot, ingot_fn(school)), f"item/{school}_dragonsteel_ingot.png")
        save(remap(ingot, ingot_fn(school, tempered=True)), f"item/tempered_{school}_steel.png")
        save(remap(read_png(IAF_JAR, "assets/iceandfire/textures/item/ice_dragon_blood.png"), blood_fn(school)),
             f"item/{school}_dragon_blood.png")
        liquid, meta = tinted_liquid(school)
        save(liquid, f"block/{school}_dragon_blood_still.png", meta)
    save(dawn(), "item/dawn.png")
    sword = read_png(IAF_JAR, "assets/iceandfire/textures/item/dragonsteel_ice_sword.png")
    for school, name in SWORDS.items():
        save(remap(sword, steel_fn(school)), f"item/{name}.png")
    liquid, meta = tinted_liquid(None)
    save(liquid, "block/dragons_breath_still.png", meta)
    for i in (0, 1):
        img, meta = holy_fire_frames(f"fire_{i}")
        save(img, f"block/holy_fire_{i}.png", meta)
    save(effect_icon(), "mob_effect/holy_fire.png")
    print("textures written under", ASSETS / "textures")


if __name__ == "__main__":
    main()
