#!/usr/bin/env python
"""Generate the Ice and Fire: Schools of Dragonsteel item, block, effect and fire textures.

Deterministic and rerunnable:  python tools/generate_textures.py

Sources (read straight from jars, never committed):
  * Ice and Fire 2.1.13 (libs/iceandfire-*.jar, LGPL-3.0): dragonsteel ice tools, ingot and blood bottle
    are palette-remapped per school, so school dragonsteel reads as part of the same family.
  * Minecraft 1.20.1 client assets (ForgeGradle cache): fire_0/fire_1, water_still and the fire resistance
    effect icon are recoloured for holy fire, the cauldron liquids and the Holy Fire effect.
All six swords and every glow/halo detail are drawn here. The staves (models and sheets) come from generate_staves.py.
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
    # Shared by the drawn swords and the staves
    "iron": hexes("#0d0d10", "#17171c", "#23232a", "#31313a", "#43434e", "#585865", "#72727f", "#90909c"),
    "leather": hexes("#24150c", "#382112", "#4d2f1a", "#644025", "#7c5332", "#966843", "#b08158"),
    "sash": hexes("#1f0e33", "#33174f", "#48226c", "#5e2f88", "#7741a3", "#9258bd", "#ad78d3"),
    "rose": hexes("#3d0612", "#5e0b1c", "#8a1228", "#b51d36", "#d8344a", "#ee6274", "#ff9aa5"),
    "teal": hexes("#06382f", "#0b5c4c", "#12856c", "#1bb08d", "#3fd8b0", "#9af5dc"),
    "deepslate": hexes("#15161a", "#22242a", "#30333b", "#40444e", "#535864", "#6a707d", "#858b98"),
    "leaf": hexes("#12300f", "#1c4a17", "#2a6620", "#3d852c", "#57a53c", "#7cc456", "#a8de7c"),
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
# The five drawn school swords (0.1.0-dev.11). Like Dawn, every pixel is placed by t (along the sword from the
# pommel, bottom-left, to the tip) and s (across it; negative is the lit upper-left side), then outlined.
# ---------------------------------------------------------------------------------------------
SWORD_P0 = (3.0, 28.0)
SWORD_K = 1 / math.sqrt(2)
SWORD_LENGTH = math.hypot(28.5 - 3.0, 28.0 - 3.5)   # 35.4, the same reach as Dawn


def tone(name, t):
    return ramp(name, max(0.0, min(1.0, t)))


def draw_sword(fn, edge, after=None):
    img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    px = img.load()
    for y in range(32):
        for x in range(32):
            cx, cy = x + 0.5 - SWORD_P0[0], y + 0.5 - SWORD_P0[1]
            t, s = (cx - cy) * SWORD_K, (cx + cy) * SWORD_K
            col = fn(t, s)
            if col is not None:
                px[x, y] = col
    outline(img, edge)
    if after:
        for y in range(32):
            for x in range(32):
                cx, cy = x + 0.5 - SWORD_P0[0], y + 0.5 - SWORD_P0[1]
                col = after((cx - cy) * SWORD_K, (cx + cy) * SWORD_K, px[x, y])
                if col is not None:
                    px[x, y] = col
    return img


def lit_side(name, s, lit, shade):
    return tone(name, lit if s < 0 else shade)


# ---------------------------------------------------------------------------------------------
def elsewhere():
    """A blade caught mid-step: three shards of night steel, each slipped a little out of line, held together
    by violet light. A crescent guard, one horn taller, round an Eye of Ender."""
    segs = ((8.0, 14.4, 0.0), (17.2, 23.4, -1.0), (26.2, SWORD_LENGTH + 0.4, 0.8))

    def fn(t, s):
        a = abs(s)
        if t < -0.9:
            return None
        if t < 2.0:                                              # pommel: a small end crystal
            return tone("violet", 0.75 if s < 0 else 0.35) if a + abs(t - 0.7) <= 1.7 else None
        if t < 6.0:                                              # grip: void cloth
            return tone("void", 0.5 if int(t * 1.4) % 2 else 0.3) if a <= 0.75 else None
        if t < 7.4:                                              # crescent guard and its eye
            if a <= 1.4:
                return (4, 26, 22, 255) if a < 0.4 else tone("teal", 0.9 if s < 0 else 0.6)
            return lit_side("obsid", s, 0.95, 0.7) if a <= 4.7 and t > 6.1 else None
        if s < 0 and 3.7 <= a <= 4.7 and t < 11.2:               # the tall horn
            return tone("violet", 0.45) if t > 10.2 else tone("obsid", 0.95)
        if s > 0 and 3.7 <= a <= 4.7 and t < 8.9:                # the short horn
            return tone("obsid", 0.7)
        for t0, t1, off in segs:
            if t0 <= t <= t1:
                ss = s - off
                w = 1.55 if t < SWORD_LENGTH - 3.0 else max(0.0, 1.55 * (SWORD_LENGTH + 0.4 - t) / 3.4)
                if abs(ss) > w + 0.2:
                    return None
                if abs(ss) < 0.5:
                    return tone("violet", 0.45 + 0.5 * t / SWORD_LENGTH)
                return lit_side("obsid", ss, 0.82, 0.55)
        return None

    def glow(t, s, cur):                                         # a mote of light in each gap between shards
        for (_, t1, o1), (t0, _, o0) in zip(segs, segs[1:]):
            if t1 + 0.9 <= t <= t0 - 0.9 and abs(s - (o0 + o1) / 2) < 0.5:
                return tone("violet", 0.9)
        return None
    return draw_sword(fn, R["obsid"][0], glow)


def thirst():
    """A flamberge: a waving blade with a blood channel down its heart, raised bat-wing quillons with gold
    claws, a blood jewel in the guard and a gold skull for a pommel."""
    def fn(t, s):
        a = abs(s)
        if t < -1.2:
            return None
        if t < 2.4:                                              # skull pommel
            r = math.hypot(t - 0.8, s)
            if r > 2.0:
                return None
            return tone("crimson", 0.0) if abs(a - 0.8) < 0.42 and 0.7 < t < 1.7 else tone("gold", 0.85 if s < 0 else 0.55)
        if t < 6.0:                                              # grip: black leather, crimson cord
            return (tone("crimson", 0.55) if int(t * 1.4) % 3 == 0 else tone("iron", 0.35)) if a <= 0.75 else None
        u = t - 6.7 - a * 0.5                                    # quillons swept up toward the blade
        if a <= 5.0 and -0.9 <= u <= 0.9:
            if a <= 1.0:
                return tone("crimson", 0.95 if s < 0 else 0.7)      # the jewel
            return tone("gold", 1.0) if a > 4.1 else lit_side("gold", s, 0.8, 0.55)
        if t < 7.4:
            return None
        w = 1.45 + 0.75 * math.sin((t - 7.4) * 1.15)
        if t > SWORD_LENGTH - 5.0:
            w = min(w, 1.9 * (SWORD_LENGTH + 0.3 - t) / 5.3)
        if a > w + 0.2 or t > SWORD_LENGTH + 0.3:
            return None
        if a < 0.5:
            return tone("crimson", 0.86 + 0.14 * math.sin(t * 0.9))
        return lit_side("crimson", s, 0.6, 0.32)
    return draw_sword(fn, R["crimson"][0])


def covenant():
    """A broad spell-knight's blade of dark steel with a line of gold runes down the fuller, its point split
    into two ivory fangs. A gold ring guard holds an emerald; a purple sash trails from the pommel."""
    tc, length = 7.9, 33.5

    def fn(t, s):
        a = abs(s)
        if 0.0 <= t <= 1.5 and 1.3 <= s <= 3.2:                  # sash tuft at the pommel
            return tone("sash", 0.7 if s < 2.3 else 0.45)
        if t < -0.8:
            return None
        if t < 1.8:                                              # pommel cap
            return lit_side("gold", s, 0.8, 0.5) if a <= 1.35 else None
        if t < 5.2:                                              # grip: brown leather
            return tone("leather", 0.55 if int(t * 1.4) % 2 else 0.35) if a <= 0.8 else None
        r = math.hypot(t - tc, s)
        if r <= 1.45:                                            # the emerald
            return tone("emerald", 1.0 if (s < -0.2 and t > tc) else 0.75 if s < 0.3 else 0.5)
        if r <= 3.1:
            return lit_side("gold", s, 0.85 if r > 2.4 else 0.65, 0.5)
        if t < tc + 2.2 or t > length + 0.3:
            return None
        w = 2.3
        far = t - (length - 6.5)
        if far > 0:                                              # the point parts into two fangs that spread
            notch = far * 0.36 + max(0.0, far - 5.5) * 0.5
            if a < notch:
                return None
            w = 2.3 + far * 0.16
        if a > w + 0.15:
            return None
        if far > 3.2:
            return tone("bone", 1.0 if s < 0 else 0.7)              # ivory points
        if a < 0.55:
            return tone("gold", 0.75) if int(t / 1.42) % 2 == 0 else tone("slate", 0.25)
        return lit_side("slate", s, 0.72, 0.42)
    return draw_sword(fn, R["slate"][0])


def briar():
    """A living blade: a bough of dark thornwood bent like a sabre, green along its cutting edge, thorns down
    its back. Two leaves make the guard round a red rose; vine binds the grip to a root-knot pommel."""
    length = 33.0
    thorns = (11.5, 15.5, 19.5, 23.5, 27.0)

    def fn(t, s):
        a = abs(s)
        if t < -0.8:
            return None
        if t < 1.9:                                              # root-knot pommel
            return lit_side("bark", s, 0.7, 0.4) if math.hypot(t - 0.6, s) <= 1.6 else None
        if t < 5.4:                                              # grip: vine over bark
            return (tone("leaf", 0.7) if int(t * 1.4) % 2 else tone("bark", 0.45)) if a <= 0.75 else None
        r = math.hypot(t - 7.0, s)
        if r <= 1.5:                                             # the rose
            return tone("rose", 0.15) if r < 0.6 else tone("rose", 0.8 if s < 0 else 0.5)
        if 0.8 <= a <= 4.8:                                      # leaf guard
            half = 0.25 + 1.35 * max(0.0, math.sin(math.pi * (a - 0.8) / 4.0)) ** 0.7
            if abs(t - 7.0) <= half:
                return tone("leaf", 0.95) if abs(t - 7.0) < 0.36 else tone("leaf", 0.7 if s < 0 else 0.45)
        if t < 7.6 or t > length + 0.3:
            return None
        bend = -0.0065 * (t - 7.0) ** 2                          # bows toward the lit side
        ss = s - bend
        w = 1.5 if t < length - 5.0 else max(0.0, 1.5 * (length + 0.3 - t) / 5.3)
        for tk in thorns:                                        # thorns on the back of the bow
            h = -ss - w
            if 0 < h <= 2.5 and 0 <= (t - tk) - h * 0.3 <= 1.6 - h * 0.36:
                return tone("bone", 0.9) if h > 1.3 else tone("bark", 0.75)
        if abs(ss) > w + 0.15:
            return None
        if ss > w - 0.95:
            return tone("leaf", 0.85 if int(t) % 3 else 0.6)        # the living edge
        return tone("bark", 0.65 if ss < -0.4 else 0.45)
    return draw_sword(fn, R["bark"][0])


def hush():
    """A needle of sculk-black steel that narrows all the way from guard to point, a thread of pale light down
    its heart. The guard is an open eye; a feeler rises from each corner, one longer than the other."""
    def fn(t, s):
        a = abs(s)
        if t < -0.7:
            return None
        if t < 2.0:                                              # pommel: a mote of cold light
            r = math.hypot(t - 0.7, s)
            return (tone("cyan", 1.0) if r < 0.8 else tone("cyan", 0.45)) if r <= 1.5 else None
        if t < 5.2:                                              # grip: sculk bound in stone
            return (tone("deepslate", 0.7) if int(t * 1.4) % 3 == 0 else tone("sculk", 0.55)) if a <= 0.72 else None
        lid = 2.0 * (1.0 - (a / 4.0) ** 1.6) if a <= 4.0 else -1.0   # the eye across the guard
        d = abs(t - 7.3)
        if d <= lid + 0.2:
            if d > lid - 0.55:
                return lit_side("deepslate", s, 0.95, 0.7)           # lids
            r = math.hypot(t - 7.3, s * 0.85)
            if r < 0.9:
                return (2, 6, 8, 255)                            # pupil
            return tone("cyan", 0.7) if r < 2.0 else tone("bone", 0.9)
        if -4.0 <= s <= -3.0 and 7.3 < t <= 12.2:                # the long feeler
            return tone("cyan", 0.9) if t > 11.0 else tone("sculk", 0.9)
        if 3.0 <= s <= 4.0 and 7.3 < t <= 10.0:                  # the short one
            return tone("cyan", 0.9) if t > 9.0 else tone("sculk", 0.7)
        if t < 8.6 or t > SWORD_LENGTH + 0.3:
            return None
        w = 0.3 + 1.1 * (1.0 - (t - 8.6) / (SWORD_LENGTH - 8.6))
        if a > w + 0.1:
            return None
        if a < 0.4:
            return tone("cyan", 0.75) if int(t * 0.9) % 3 == 0 else tone("sculk", 0.9)
        return lit_side("sculk", s, 1.0, 0.6)
    return draw_sword(fn, R["sculk"][0])


SWORD_ART = {"elsewhere": elsewhere, "thirst": thirst, "covenant": covenant, "briar": briar, "hush": hush}


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
    for name, art in SWORD_ART.items():
        save(art(), f"item/{name}.png")
    liquid, meta = tinted_liquid(None)
    save(liquid, "block/dragons_breath_still.png", meta)
    for i in (0, 1):
        img, meta = holy_fire_frames(f"fire_{i}")
        save(img, f"block/holy_fire_{i}.png", meta)
    save(effect_icon(), "mob_effect/holy_fire.png")
    print("textures written under", ASSETS / "textures")


if __name__ == "__main__":
    main()
