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
# The five drawn school swords. Every pixel is placed by hand on the sword's diagonal: the hilt is centred on
# x + y = 30, each blade row is the same run of pixels one step left per row down, and guards are drawn for the
# lit side and mirrored across the blade for the other. Formula-drawn versions (0.1.0-dev.11) came out ragged.
# ---------------------------------------------------------------------------------------------
def hx(code):
    return hexes(code)[0]


def plot_sword(pixels, edge, keep_open=None):
    """Draw the placed pixels and give them a 1 px outline tinted by what it borders (dark gold round gold, dark
    teal round a teal gem), as vanilla's swords have. Cells where keep_open(x, y) is true get no outline."""
    img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    px = img.load()
    for (x, y), colour in pixels.items():
        px[x, y] = colour
    for y in range(32):
        for x in range(32):
            if (x, y) in pixels or (keep_open and keep_open(x, y)):
                continue
            near = [pixels[q] for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)) if q in pixels]
            if near:
                px[x, y] = tuple(min(255, int(sum(c[i] for c in near) / len(near) * 0.22 + edge[i] * 0.6))
                                 for i in range(3)) + (255,)
    return img


def put(px, key, cells):
    """cells: {palette letter: [(x, y), ...]}"""
    for letter, spots in cells.items():
        for spot in spots:
            px[spot] = hx(key[letter])


def mirrored(cells):
    """The same cells reflected across the blade (x + y = 30), for the guard's far side."""
    return {letter: [(30 - y, 30 - x) for x, y in spots] for letter, spots in cells.items()}


def block3(px, x, y, codes):
    """A 3x3 gem or pommel, nine colours row by row."""
    for n, code in enumerate(codes):
        px[x + n % 3, y + n // 3] = hx(code)


def grip(px, rows):
    """Three pixels to a row down the hilt, rows 23 to 25."""
    for y, codes in zip((23, 24, 25), rows):
        for k, code in enumerate(codes):
            px[29 - y + k, y] = hx(code)


def elsewhere():
    """A blade of dusk with an edge of light: deep violet inside a bright rim. It is cut clean through in two
    places and the middle length has slid out of line; the cut faces blaze and a thread of light joins them.
    A crescent guard rimmed in the same light, its lit horn the taller, round an Eye of Ender."""
    px = {}
    body = ("#c58aff", "#5a2d89", "#331951", "#45226c", "#8838ec")
    cut = ("#e0baff", "#f5e6ff", "#f5e6ff", "#e0baff", "#c58aff")
    for top, bottom, slip in ((3, 7, 0), (10, 14, 2), (17, 20, 0)):           # tip, middle, base
        for y in range(top, bottom + 1):
            face = (y == bottom and bottom != 20) or (y == top and top != 3)
            for k, code in enumerate(cut if face else body):
                if 28 - y + k + slip <= 28:
                    px[28 - y + k + slip, y] = hx(code)
    for spot in ((25, 3), (26, 3), (27, 3)):                                  # the rim closes over the point
        px[spot] = hx("#c58aff")
    px[28, 3] = hx("#8838ec")
    for spot in ((23, 8), (23, 9), (17, 15), (16, 15), (15, 16), (14, 16)):   # the thread across each cut
        px[spot] = hx("#e0baff")
    put(px, {"1": "#c58aff", "3": "#45226c", "v": "#e0baff"},
        {"1": [(6, 20), (5, 19), (4, 18), (4, 17), (5, 16), (6, 15), (7, 14)],
         "3": [(7, 21), (7, 20), (6, 19), (5, 18), (5, 17), (6, 16), (7, 15), (8, 14)], "v": [(8, 13)]})
    put(px, {"3": "#8838ec", "5": "#281e3c", "w": "#a85fff"},
        {"3": [(9, 23), (10, 24), (11, 25), (12, 26)], "5": [(10, 23), (11, 24), (12, 25), (13, 25), (13, 26)], "w": [(14, 25)]})
    block3(px, 8, 20, ("#9af5dc", "#3fd8b0", "#3fd8b0", "#3fd8b0", "#041a16", "#1bb08d", "#1bb08d", "#1bb08d", "#12856c"))
    grip(px, (("#5a2d89", "#45226c", "#331951"), ("#c58aff", "#8838ec", "#6420c2"), ("#5a2d89", "#45226c", "#331951")))
    block3(px, 2, 26, ("#f5e6ff", "#c58aff", "#a85fff", "#c58aff", "#a85fff", "#8838ec", "#a85fff", "#8838ec", "#6420c2"))
    return plot_sword(px, R["obsid"][0], keep_open=lambda x, y: y in (8, 9, 15, 16) and x >= 11)


def thirst():
    """A flamberge: the blade snakes from side to side as it rises, a dark blood channel down its heart with
    beads of blood in it. The guard is a pair of small bat wings, two gold fingers to each with crimson skin
    between them, round a ruby set in gold; the pommel is a bone skull."""
    px = {}
    wave = (0, 0, 1, 1, 0, 0, -1, -1)
    for y in range(3, 21):
        slip = 0 if y < 6 else wave[(20 - y) % 8]
        row = ["#ff8a8f", "#cc2a36", "#3a060b", "#82111c", "#5c0b13"]
        if y % 4 == 2:
            row[2] = "#ff8a8f"                                               # a bead of blood in the channel
        if y in (7, 8, 9):
            row[1] = "#e8505a"                                               # the glint
        for k, code in enumerate(row):
            if 28 - y + k + slip <= 28:
                px[28 - y + k + slip, y] = hx(code)
    # each wing about 5 x 6 (dev.13's were 8 x 10, which Tad found too big)
    wing = {"g": [(7, 20), (6, 19),                                              # the arm, out from the ruby
                  (5, 18), (4, 17),                                              # the low finger, square to the blade
                  (6, 18), (6, 17), (7, 16)],                                    # the high finger, toward the point
            "h": [(3, 16), (7, 15)],                                             # claws
            "n": [(5, 17), (5, 16)],                                             # skin between the fingers
            "m": [(7, 17), (7, 18)]}                                             # skin back to the arm
    put(px, {"g": "#e6b239", "h": "#ffe993", "m": "#a81a27", "n": "#82111c"}, wing)
    put(px, {"g": "#c99022", "h": "#e6b239", "m": "#82111c", "n": "#5c0b13"}, mirrored(wing))
    block3(px, 8, 20, ("#ffe993", "#ff8a8f", "#e6b239", "#ff8a8f", "#cc2a36", "#a81a27", "#e6b239", "#a81a27", "#9c6715"))
    grip(px, (("#43434e", "#31313a", "#17171c"), ("#cc2a36", "#a81a27", "#5c0b13"), ("#43434e", "#31313a", "#17171c")))
    skull = {"o": [(2, 26), (3, 26), (1, 27), (2, 27), (3, 27)], "p": [(4, 26), (4, 27), (1, 28), (3, 28)],
             "r": [(5, 27), (5, 28), (2, 29), (4, 29)], "e": [(2, 28), (4, 28)], "m": [(3, 29)]}
    put(px, {"o": "#efebda", "p": "#d8d3bd", "r": "#bab49b", "e": "#1c0204", "m": "#3a060b"}, skull)
    return plot_sword(px, R["crimson"][0])


def covenant():
    """A broad spell-knight's blade of dark steel with a line of gold inlaid down it, its point parted into
    two ivory fangs. A gold ring guard holds an emerald, and each quillon ends in a fang; a purple sash binds
    the grip."""
    px = {}
    for y in range(6, 21):
        row = ["#9aa29b", "#7b847d", "#e6b239" if y % 4 else "#c99022", "#4c534e", "#3a403c"]
        if y in (9, 10):
            row[0] = "#dde2eb"
        for k, code in enumerate(row):
            px[28 - y + k, y] = hx(code)
    del px[24, 6]                                                            # the parting runs four rows deep
    put(px, {"i": "#efebda", "j": "#d8d3bd", "k": "#bab49b", "s": "#9aa29b", "t": "#7b847d"},
        {"i": [(26, 2), (25, 3), (24, 4)], "j": [(26, 3), (25, 4), (27, 4)], "k": [(28, 4), (26, 5), (27, 5)],
         "s": [(23, 5)], "t": [(24, 5)]})
    block3(px, 8, 20, ("#c4ffd9", "#7ff0a9", "#3ddb7a", "#7ff0a9", "#3ddb7a", "#20b863", "#3ddb7a", "#20b863", "#11703c"))
    put(px, {"h": "#ffe993", "g": "#f6d259", "d": "#c99022", "e": "#9c6715"},
        {"h": [(8, 19), (9, 19)], "g": [(10, 19), (7, 20), (7, 21)], "d": [(7, 22), (11, 20), (11, 21)],
         "e": [(9, 23), (10, 23), (11, 22)]})
    quillon = {"g": [(6, 20), (5, 19), (4, 18)], "d": [(6, 19), (5, 18)], "i": [(4, 17), (4, 16), (5, 15)], "j": [(5, 17), (5, 16)]}
    put(px, {"g": "#f6d259", "d": "#e6b239", "i": "#efebda", "j": "#d8d3bd"}, quillon)
    put(px, {"g": "#c99022", "d": "#9c6715", "i": "#d8d3bd", "j": "#bab49b"}, mirrored(quillon))
    grip(px, (("#7c5332", "#644025", "#382112"), ("#ad78d3", "#7741a3", "#48226c"), ("#7c5332", "#644025", "#382112")))
    px[8, 23] = hx("#c99022")                                                # the ring sits over the top of the grip
    block3(px, 2, 26, ("#ffe993", "#f6d259", "#e6b239", "#f6d259", "#3ddb7a", "#c99022", "#e6b239", "#c99022", "#9c6715"))
    return plot_sword(px, R["slate"][0])


def briar():
    """A living blade: a bough of dark thornwood that starts true and bows up to the point like a sabre, green
    along its cutting edge, three hooked thorns down its back. Two veined leaves, the lit one longer, make the
    guard round a red rose; vine binds the grip to a root-knot pommel."""
    px = {}
    back = {20: 8, 19: 9, 18: 10, 17: 11, 16: 12, 15: 13, 14: 14, 13: 15, 12: 16, 11: 17, 10: 17, 9: 18, 8: 18,
            7: 19, 6: 19, 5: 19, 4: 20, 3: 20, 2: 20, 1: 20}
    for y, x in back.items():
        row = ["#b48d5c" if y in (7, 8, 10) else "#987449", "#7c5d3a", "#4f3923", "#3d852c",
               "#a8de7c" if y % 3 == 0 else "#7cc456"]
        row = {4: row[:2] + row[3:], 3: [row[1], row[3], row[4]], 2: [row[3], row[4]], 1: ["#a8de7c"]}.get(y, row)
        for k, code in enumerate(row):
            px[x + k, y] = hx(code)
    for y in (17, 13, 9):                                                    # thorns, hooked back toward the hilt
        px[back[y] - 1, y] = hx("#4f3923")
        px[back[y] - 2, y] = hx("#c9a36b")
    leaf = {"v": [(7, 20), (6, 19), (5, 18), (4, 17)], "t": [(3, 16)], "u": [(7, 19), (6, 18), (5, 17)],
            "l": [(6, 20), (5, 19), (4, 18)]}                                  # long leaf, pale vein to its point
    put(px, {"v": "#a8de7c", "t": "#7cc456", "u": "#7cc456", "l": "#3d852c"}, leaf)
    short = {"v": [(7, 20), (6, 19), (5, 18)], "t": [(4, 17)], "u": [(7, 19), (6, 18)], "l": [(6, 20), (5, 19)]}
    put(px, {"v": "#7cc456", "t": "#57a53c", "u": "#57a53c", "l": "#2a6620"}, mirrored(short))
    block3(px, 8, 20, ("#ff9aa5", "#ee6274", "#d8344a", "#ee6274", "#5e0b1c", "#b51d36", "#d8344a", "#b51d36", "#8a1228"))
    grip(px, (("#987449", "#7c5d3a", "#4f3923"), ("#7cc456", "#57a53c", "#2a6620"), ("#987449", "#7c5d3a", "#4f3923")))
    block3(px, 2, 26, ("#b48d5c", "#987449", "#7c5d3a", "#987449", "#3b2a1a", "#644a2e", "#7c5d3a", "#644a2e", "#3b2a1a"))
    return plot_sword(px, R["bark"][0])


def hush():
    """A needle: sculk-black steel that narrows all the way from guard to point, a pulse of pale light running
    up its heart. The guard is one wide-open eye set across the hilt, bright whites round a cyan iris split by
    a black slit pupil, between dark lids; a feeler curls from each corner of it, the lit one longer."""
    px = {}
    pulse = ("#7ff2f8", "#1fc0cc", "#11949f", "#154049")
    for y in range(2, 19):                                                   # the eye's upper lid is row 19
        if y >= 9:
            row = ["#3f8c93", pulse[y % 4], "#0f2e37"]
        elif y >= 4:
            row = ["#3f8c93", pulse[y % 4]]
        else:
            row = [None, "#d4fdff" if y == 2 else "#7ff2f8"]
        for k, code in enumerate(row):
            if code:
                px[29 - y + k, y] = hx(code)
    grip(px, (("#2a6f78", "#154049", "#0a2027"), ("#858b98", "#535864", "#30333b"), ("#2a6f78", "#154049", "#0a2027")))
    # the eye: upright, nine pixels wide and five tall, so whites, iris and slit still show at inventory size
    eye = {"L": [(7, 19), (8, 19), (9, 19), (10, 19), (11, 19), (6, 20), (12, 20)], "M": [(5, 21), (13, 21)],
           "D": [(7, 23), (8, 23), (9, 23), (10, 23), (11, 23), (6, 22), (12, 22)],
           "W": [(7, 20), (6, 21), (7, 21), (7, 22)], "w": [(11, 20), (11, 21), (12, 21), (11, 22)],
           "i": [(8, 20), (10, 20)], "j": [(8, 21), (10, 21)], "k": [(8, 22), (10, 22)], "P": [(9, 20), (9, 21), (9, 22)]}
    put(px, {"L": "#2a6f78", "M": "#3f8c93", "D": "#1d555f", "W": "#efebda", "w": "#d8d3bd", "i": "#29dfeb",
             "j": "#1fc0cc", "k": "#11949f", "P": "#020608"}, eye)
    put(px, {"s": "#1fc0cc", "c": "#d4fdff"}, {"s": [(4, 20), (3, 19), (3, 18)], "c": [(4, 17)]})
    put(px, {"s": "#11949f", "c": "#7ff2f8"}, {"s": [(14, 22), (15, 23)], "c": [(15, 24)]})
    block3(px, 2, 26, ("#d4fdff", "#7ff2f8", "#29dfeb", "#7ff2f8", "#29dfeb", "#1fc0cc", "#29dfeb", "#1fc0cc", "#11949f"))
    return plot_sword(px, R["sculk"][0])


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
