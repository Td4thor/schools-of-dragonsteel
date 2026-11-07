#!/usr/bin/env python
"""Generate the Dragonsteel Schools plate armour art (v2: Holy radiant full plate, Ender Voidwalker).

Deterministic and rerunnable:  python tools/generate_armor.py
Writes (paths relative to the project root):
  src/main/resources/assets/dragonsteel_schools/geo/<school>_dragonsteel_plate.geo.json
  src/main/resources/assets/dragonsteel_schools/textures/models/armor/<school>_dragonsteel_plate.png
  src/main/resources/assets/dragonsteel_schools/textures/models/armor/<school>_dragonsteel_plate_glowmask.png
  src/main/resources/assets/dragonsteel_schools/textures/item/<school>_dragonsteel_<piece>.png
for school in (holy, ender) and piece in (helmet, chestplate, leggings, boots).

Author space = Bedrock/Blockbench pixels: +Y up, the wearer faces -Z, the wearer's right is -X.
Bones follow Iron's Spells' GenericCustomArmorRenderer contract (see docs/art/armor/ART-NOTES.md).
Every cube uses box UV at 1 texel per unit (integer sizes; inflate only pads geometry).
Glowmask pixels copy the base RGB with alpha 255: GeckoLib 4.8.4's GeoGlowingTextureMeta draws the
*base* texture colour at every non-zero glowmask pixel, full-bright.
"""
import hashlib
import json
import math
import random
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "src/main/resources/assets/dragonsteel_schools"
TEX = 128

# ----------------------------------------------------------------------------------------------
# Palettes: ramps run darkest -> brightest.
# ----------------------------------------------------------------------------------------------
def _hex(c):
    c = c.lstrip("#")
    return (int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16), 255)

RAMPS = {
    # Holy: polished white steel with cool shadows, burnished gold, radiant sun glow
    "silver": ["#343747", "#515669", "#73798e", "#9aa1b5", "#bfc5d3", "#dce0e9", "#f1f3f8", "#ffffff"],
    "gold":   ["#4a2a08", "#74450f", "#a06a17", "#cc9324", "#e8b53a", "#f7d45a", "#ffeb94", "#fff9d6"],
    "sun":    ["#c27a12", "#e9a521", "#ffc833", "#ffd966", "#ffeaa0", "#fff6d6"],   # glowing gold
    "visor":  ["#1c1726", "#2e2638"],
    # Ender v2: blue-violet night steel, amethyst trim, void cloth, enderman-magenta eyes, pearl teal, pale blade steel
    "night":    ["#0e0b16", "#171223", "#211a31", "#2c2340", "#382e52", "#463b66", "#5a4e80", "#7468a0"],
    "amethyst": ["#2e1247", "#421a63", "#5a2482", "#7330a3", "#8e43c0", "#aa62d8", "#c88cec"],
    "cloth":    ["#0f0b17", "#181224", "#221a33", "#2d2343", "#3a2e55", "#4a3d6a"],
    "magenta":  ["#80109f", "#b022d6", "#d64cf7", "#ea8cff", "#f8cfff"],                # glowing
    "pearl":    ["#0b4a42", "#11705f", "#1d9c84", "#3fc7a8", "#86e6cf", "#d0fff2"],     # glowing
    "blade":    ["#3e3a52", "#615b7a", "#8c86a8", "#bbb6d4", "#e6e2f7"],
    "violet":   ["#6a22c9", "#8c3cf0", "#ab63ff", "#c88dff", "#e2bdff", "#f6e8ff"],     # glowing
    # Blood: deep crimson plate, blackened iron underlayer, dim ember glow
    "crimson":  ["#1a0306", "#2e060b", "#470a12", "#651019", "#841723", "#a3202e", "#c3343f", "#e05a62"],
    "iron":     ["#08080a", "#111114", "#1a1a1f", "#24242a", "#303038", "#3e3e48", "#50505c", "#686876"],
    "ember":    ["#5c0a0a", "#8f1414", "#c42020", "#ef3a30", "#ff7a5e"],                # glowing
    # Placeholder plate for schools still waiting on their art pass
    "evo_steel": ["#15171a", "#202328", "#2c3037", "#3a3f48", "#4b515c", "#606874", "#7a838f", "#99a2ad"],
    "emerald":   ["#0a4d2a", "#11703c", "#20b863", "#3ddb7a", "#7ff0a9", "#c4ffd9"],     # glowing
    "nat_steel": ["#141615", "#1f2321", "#2b302d", "#3a403c", "#4c534e", "#616963", "#7b847d", "#9aa29b"],
    "moss":      ["#1f3217", "#2c4720", "#3d5f2a", "#527b34", "#6f9c40", "#95c25a", "#c2e584"],
    "sculk":     ["#020a0d", "#051419", "#0a2027", "#0f2e37", "#154049", "#1d555f", "#2a6f78", "#3f8c93"],
    "cyan":      ["#0b6b74", "#11949f", "#1fc0cc", "#29dfeb", "#7ff2f8", "#d4fdff"],     # glowing
}
RAMPS = {k: [_hex(c) for c in v] for k, v in RAMPS.items()}


def seed_for(*parts):
    return int(hashlib.sha256("/".join(parts).encode()).hexdigest()[:12], 16)


# ----------------------------------------------------------------------------------------------
# Face canvas.  Coordinates are "as seen from outside the cube": x left->right, y top->bottom.
# For top/bottom faces x runs -X -> +X and y runs back(+Z) -> front(-Z) (GeckoLib box-UV layout).
# ----------------------------------------------------------------------------------------------
class Face:
    def __init__(self, w, h, kind, rng):
        self.w, self.h, self.kind, self.rng = w, h, kind, rng
        self.px = [[None] * w for _ in range(h)]       # (ramp, level) or rgba tuple
        self.glow = [[False] * w for _ in range(h)]

    def ok(self, x, y):
        return 0 <= x < self.w and 0 <= y < self.h

    def set(self, x, y, ramp, lvl, glow=False):
        if x < 0: x += self.w
        if y < 0: y += self.h
        if not self.ok(x, y):
            return
        r = RAMPS[ramp]
        self.px[y][x] = (ramp, max(0, min(len(r) - 1, lvl)))
        self.glow[y][x] = glow

    def shift(self, x, y, d):
        if not self.ok(x, y) or self.px[y][x] is None:
            return
        ramp, lvl = self.px[y][x]
        self.set(x, y, ramp, lvl + d, self.glow[y][x])

    def get(self, x, y):
        return self.px[y][x]

    def hflip(self):
        self.px = [row[::-1] for row in self.px]
        self.glow = [row[::-1] for row in self.glow]

    def rgba(self, x, y):
        v = self.px[y][x]
        ramp, lvl = v
        return RAMPS[ramp][lvl]


# ----------------------------------------------------------------------------------------------
# Base materials
# ----------------------------------------------------------------------------------------------
SIDES4 = ("front", "back", "left", "right")


def plate(f, ramp, base, sheen=True):
    """Polished plate lit from above: brighter top rows, darker foot, lit top rim, shaded far edge, one
    vertical sheen column on wide faces. No random speckle: noise read as dirt at armour scale."""
    w, h, k = f.w, f.h, f.kind
    for y in range(h):
        for x in range(w):
            lvl = base
            if k in SIDES4:
                if h >= 4:
                    t = y / (h - 1)
                    if t < 0.25:
                        lvl += 1
                    elif t > 0.75:
                        lvl -= 1
            elif k == "top":
                lvl += 1
            else:
                lvl -= 2
            f.set(x, y, ramp, lvl)
    if k in SIDES4:
        if h >= 2:
            for x in range(w):
                f.shift(x, 0, +1)
                if h >= 3:
                    f.shift(x, h - 1, -1)
        if w >= 4 and h >= 3:
            for y in range(1, h - 1):
                f.shift(w - 1, y, -1)
        if sheen and w >= 4 and h >= 4:
            sx = max(1, w // 4)
            for y in range(1, h - 1):
                f.shift(sx, y, +1)
    elif k == "top" and w >= 3 and h >= 3:
        for x in range(w):
            f.shift(x, h - 1, +1)       # front lip catches the light


def cloth(f, ramp, base):
    """Soft cloth: vertical folds every three texels, a shadow under the top lip, darker hem row."""
    w, h, k = f.w, f.h, f.kind
    for y in range(h):
        for x in range(w):
            lvl = base
            if k in SIDES4:
                lvl += {0: 0, 1: 1, 2: -1}[x % 3] if w >= 3 else 0
                if y == 0 and h >= 3:
                    lvl -= 1
                if y == h - 1 and h >= 3:
                    lvl -= 1
            elif k == "top":
                lvl += 1
            else:
                lvl -= 1
            f.set(x, y, ramp, lvl)


def glow_fill(f, ramp, side, top, bottom):
    for y in range(f.h):
        for x in range(f.w):
            if f.kind == "top":
                lvl = top
            elif f.kind == "bottom":
                lvl = bottom
            else:
                lvl = side + (1 if f.h >= 2 and y < f.h // 2 else 0)
            f.set(x, y, ramp, lvl, True)


MATERIALS = {
    "silver": lambda f: plate(f, "silver", 5),
    "silver_dim": lambda f: plate(f, "silver", 4),
    "gold": lambda f: plate(f, "gold", 4, sheen=False),
    "gold_hi": lambda f: plate(f, "gold", 5, sheen=False),
    "sun": lambda f: glow_fill(f, "sun", 3, 4, 1),
    "night": lambda f: plate(f, "night", 4),
    "night_hi": lambda f: plate(f, "night", 5),
    "night_dk": lambda f: plate(f, "night", 3, sheen=False),
    "amethyst": lambda f: plate(f, "amethyst", 3, sheen=False),
    "cloth": lambda f: cloth(f, "cloth", 3),
    "blade": lambda f: plate(f, "blade", 2, sheen=False),
    "crystal": lambda f: glow_fill(f, "violet", 2, 4, 1),
    "crimson": lambda f: plate(f, "crimson", 4),
    "crimson_hi": lambda f: plate(f, "crimson", 5),
    "crimson_dk": lambda f: plate(f, "crimson", 3, sheen=False),
    "iron": lambda f: plate(f, "iron", 3, sheen=False),
    "ember": lambda f: glow_fill(f, "ember", 2, 3, 1),
    "evocation_metal": lambda f: plate(f, "evo_steel", 4),
    "evocation_accent": lambda f: plate(f, "gold", 4, sheen=False),
    "evocation_glow": lambda f: glow_fill(f, "emerald", 2, 4, 1),
    "nature_metal": lambda f: plate(f, "nat_steel", 4),
    "nature_accent": lambda f: plate(f, "moss", 3, sheen=False),
    "nature_glow": lambda f: glow_fill(f, "moss", 4, 5, 2),
    "eldritch_metal": lambda f: plate(f, "sculk", 4),
    "eldritch_accent": lambda f: plate(f, "sculk", 6, sheen=False),
    "eldritch_glow": lambda f: glow_fill(f, "cyan", 2, 4, 1),
}

# ----------------------------------------------------------------------------------------------
# Decoration ops (closures over face-local coordinates; negative indices count from the far edge)
# ----------------------------------------------------------------------------------------------
def band(edge, ramp="gold", lvl=4, width=1, glow=False, bevel=True):
    def op(f):
        for i in range(width):
            if edge in ("top", "bottom"):
                y = i if edge == "top" else f.h - 1 - i
                for x in range(f.w):
                    l = lvl + (1 if bevel and i == 0 and edge == "top" else 0) - (1 if bevel and edge == "bottom" and i == 0 else 0)
                    f.set(x, y, ramp, l, glow)
            else:
                x = i if edge == "left" else f.w - 1 - i
                for y in range(f.h):
                    f.set(x, y, ramp, lvl, glow)
    return op


def hline(y, x0=0, x1=-1, ramp="gold", lvl=4, glow=False):
    def op(f):
        yy = y if y >= 0 else f.h + y
        a = x0 if x0 >= 0 else f.w + x0
        b = x1 if x1 >= 0 else f.w + x1
        for x in range(a, b + 1):
            f.set(x, yy, ramp, lvl, glow)
    return op


def vline(x, y0=0, y1=-1, ramp="gold", lvl=4, glow=False):
    def op(f):
        xx = x if x >= 0 else f.w + x
        a = y0 if y0 >= 0 else f.h + y0
        b = y1 if y1 >= 0 else f.h + y1
        for y in range(a, b + 1):
            f.set(xx, y, ramp, lvl, glow)
    return op


def shade_row(y, d):
    def op(f):
        yy = y if y >= 0 else f.h + y
        for x in range(f.w):
            f.shift(x, yy, d)
    return op


def rivets(row, ramp="gold", lvl=6, step=3, start=1, glow=False):
    """Row of 1px rivet heads with a 1px shadow underneath."""
    def op(f):
        yy = row if row >= 0 else f.h + row
        for x in range(start, f.w - 1, step):
            f.set(x, yy, ramp, lvl, glow)
            if yy + 1 < f.h and not f.glow[yy + 1][x]:
                f.shift(x, yy + 1, -2)
    return op


def stamp(art, legend, anchor="center", dx=0, dy=0):
    """Paint an ASCII pattern. legend: char -> (ramp, lvl, glow) or (op 'shift', d)."""
    def op(f):
        ah, aw = len(art), max(len(r) for r in art)
        if anchor == "center":
            ox, oy = (f.w - aw) // 2, (f.h - ah) // 2
        elif anchor == "topleft":
            ox, oy = 0, 0
        elif anchor == "top":
            ox, oy = (f.w - aw) // 2, 0
        elif anchor == "bottom":
            ox, oy = (f.w - aw) // 2, f.h - ah
        else:
            raise ValueError(anchor)
        ox += dx; oy += dy
        for j, row in enumerate(art):
            for i, ch in enumerate(row):
                if ch in " .":
                    continue
                spec = legend[ch]
                if spec[0] == "shift":
                    f.shift(ox + i, oy + j, spec[1])
                else:
                    f.set(ox + i, oy + j, spec[0], spec[1], spec[2] if len(spec) > 2 else False)
    return op


def seams(step, ramp, lvl, start=1, glow_ramp=None):
    """Horizontal lamellar seams every `step` rows: dark line with a lit row below."""
    def op(f):
        for y in range(start, f.h - 1, step):
            for x in range(f.w):
                if glow_ramp and 0 < x < f.w - 1 and (x + y) % 5 == 2:
                    f.set(x, y, glow_ramp, 2, True)
                else:
                    f.set(x, y, ramp, lvl)
            if y + 1 < f.h - 1:
                for x in range(f.w):
                    f.shift(x, y + 1, +1)
    return op


RUNES = [
    ["x.x", ".x.", "x.x"], ["xx.", ".x.", ".xx"], [".x.", "xxx", ".x."], ["x..", "xx.", "x.x"],
    ["xxx", "..x", ".x."], [".xx", "x..", ".xx"], ["x.x", "xxx", "..x"],
]


def runes(seedname, y=None, ramp="violet", lvl=2, count=1):
    """Small glowing End-glyphs (deterministic per name)."""
    def op(f):
        rng = random.Random(seed_for("rune", seedname))
        if f.w < 3 or f.h < 3:
            return
        for n in range(count):
            g = RUNES[rng.randrange(len(RUNES))]
            gx = (f.w - 3) // 2 if count == 1 else 1 + n * ((f.w - 4) // max(1, count - 1)) if count > 1 else 0
            gy = (f.h - 3) // 2 if y is None else y
            for j in range(3):
                for i in range(3):
                    if g[j][i] == "x":
                        f.set(gx + i, gy + j, ramp, lvl, True)
    return op


def rect(x0, y0, x1, y1, ramp, lvl, glow=False):
    """Fill an inclusive rectangle (negative indices count from the far edge)."""
    def op(f):
        a, b = (x0 if x0 >= 0 else f.w + x0), (x1 if x1 >= 0 else f.w + x1)
        c, d = (y0 if y0 >= 0 else f.h + y0), (y1 if y1 >= 0 else f.h + y1)
        for y in range(c, d + 1):
            for x in range(a, b + 1):
                f.set(x, y, ramp, lvl, glow)
    return op


def outline(ramp, lvl, glow=False):
    def op(f):
        for e in ("top", "bottom", "left", "right"):
            band(e, ramp, lvl, glow=glow, bevel=False)(f)
    return op


def ridge(col=None):
    """Raised vertical ridge: a lit column with its shadow beside it."""
    def op(f):
        c = (f.w - 1) // 2 if col is None else (col if col >= 0 else f.w + col)
        for y in range(1, f.h - 1):
            f.shift(c, y, +2)
            if c + 1 < f.w:
                f.shift(c + 1, y, -1)
    return op


def under_lip(row=0):
    """Shadow cast by the plate above onto this plate's top row."""
    return shade_row(row, -2)


def lames(rows):
    """Overlapping plate lines: a shadow row under each lip, then the lit edge of the next lame."""
    def op(f):
        for r in rows:
            r = r if r >= 0 else f.h + r
            for x in range(f.w):
                f.shift(x, r, -2)
                if r + 1 < f.h:
                    f.shift(x, r + 1, +1)
    return op


# ----------------------------------------------------------------------------------------------
# Cube model
# ----------------------------------------------------------------------------------------------
INFLATES = (0.0, 0.125, 0.25, 0.375, 0.5, 0.75)
SIDES = ("right", "front", "left", "back")


class Cube:
    def __init__(self, name, xb, yb, zb, mat, deco=None, inflate=None):
        self.name = name
        self.xb, self.yb, self.zb = tuple(xb), tuple(yb), tuple(zb)
        ext = (xb[1] - xb[0], yb[1] - yb[0], zb[1] - zb[0])
        for inf in ([inflate] if inflate is not None else INFLATES):
            size = [e - 2 * inf for e in ext]
            if all(abs(s - round(s)) < 1e-9 and round(s) >= 1 for s in size):
                break
        else:
            raise ValueError(f"{name}: extents {ext} need a common fractional part")
        self.inflate = inf
        self.size = [int(round(s)) for s in size]
        self.origin = [xb[0] + inf, yb[0] + inf, zb[0] + inf]
        self.mat = mat
        self.deco = {}
        for key, ops in (deco or {}).items():
            for face in (SIDES if key == "sides" else ("right", "front", "left", "back", "top", "bottom") if key == "all" else (key,)):
                self.deco.setdefault(face, []).extend(ops)
        self.mirror_of = None
        self.uv = None

    def mirrored(self, name):
        c = Cube.__new__(Cube)
        c.__dict__.update(self.__dict__)
        c.name = name
        c.xb = (-self.xb[1], -self.xb[0])
        c.origin = [c.xb[0] + self.inflate, self.origin[1], self.origin[2]]
        c.mirror_of = self
        c.uv = None
        return c

    def face_rects(self):
        w, h, d = self.size
        u, v = self.uv
        return {
            "right": (u, v + d, d, h), "front": (u + d, v + d, w, h), "left": (u + d + w, v + d, d, h),
            "back": (u + 2 * d + w, v + d, w, h), "top": (u + d, v, w, d), "bottom": (u + d + w, v, w, d),
        }

    def uv_box(self):
        w, h, d = self.size
        return 2 * (w + d), d + h


class Bone:
    def __init__(self, name, pivot, parent=None):
        self.name, self.pivot, self.parent, self.cubes = name, pivot, parent, []


def skeleton():
    b = {}
    def add(name, pivot, parent=None):
        b[name] = Bone(name, pivot, parent)
    add("bipedHead", [0, 24, 0]); add("armorHead", [0, 24, 0], "bipedHead")
    add("bipedBody", [0, 24, 0]); add("armorBody", [0, 24, 0], "bipedBody")
    add("armorLeggingTorsoLayer", [0, 24, 0], "bipedBody")
    add("bipedRightArm", [-4, 22, 0]); add("armorRightArm", [-5, 22, 0], "bipedRightArm")
    add("bipedLeftArm", [4, 22, 0]); add("armorLeftArm", [5, 22, 0], "bipedLeftArm")
    add("bipedRightLeg", [-2, 12, 0]); add("armorRightLeg", [-2, 12, 0], "bipedRightLeg")
    add("armorRightBoot", [-2, 12, 0], "bipedRightLeg")
    add("armorTorsoExtensionRightLeg", [-2, 12, 0], "bipedRightLeg")
    add("bipedLeftLeg", [2, 12, 0]); add("armorLeftLeg", [2, 12, 0], "bipedLeftLeg")
    add("armorLeftBoot", [2, 12, 0], "bipedLeftLeg")
    add("armorTorsoExtensionLeftLeg", [2, 12, 0], "bipedLeftLeg")
    return b


MIRROR_BONE = {
    "armorRightArm": "armorLeftArm", "armorRightLeg": "armorLeftLeg", "armorRightBoot": "armorLeftBoot",
    "armorTorsoExtensionRightLeg": "armorTorsoExtensionLeftLeg",
}

# ----------------------------------------------------------------------------------------------
# HOLY: radiant heavy full plate (white-silver + gold, sun/halo/wing motifs, no crosses)
# ----------------------------------------------------------------------------------------------
G = lambda l, glow=False: ("gold", l, glow)
S = lambda l, glow=False: ("silver", l, glow)
SUN = lambda l: ("sun", l, True)


def halo_cells():
    """Stepped pixel ring (radius ~6.3) behind the helm, merged into rectangles."""
    cx, cy = 0.0, 31.0
    cells = set()
    for i in range(-8, 8):
        for j in range(22, 40):
            d = math.hypot(i + 0.5 - cx, j + 0.5 - cy)
            if 5.55 <= d < 6.75:
                cells.add((i, j))
    # sun rays: 3 above, 2 at the sides, short diagonals
    rays = {(-1, 38), (0, 38), (-1, 39), (0, 39), (0, 40), (-1, 40),
            (-8, 30), (-9, 30), (7, 30), (8, 30), (-8, 31), (-9, 31), (7, 31), (8, 31),
            (-6, 36), (-7, 37), (5, 36), (6, 37)}
    runs = []
    for j in sorted({c[1] for c in cells}):
        xs = sorted(i for i, jj in cells if jj == j)
        start = prev = None
        for x in xs + [None]:
            if start is None:
                start = prev = x
            elif x is not None and x == prev + 1:
                prev = x
            else:
                runs.append((start, prev + 1, j, j + 1))
                start = prev = x
    # merge vertically stacked identical runs (the ring's flanks)
    merged = []
    for r in sorted(runs, key=lambda r: (r[0], r[1], r[2])):
        if merged and merged[-1][0] == r[0] and merged[-1][1] == r[1] and merged[-1][3] == r[2]:
            merged[-1] = (r[0], r[1], merged[-1][2], r[3])
        else:
            merged.append(r)
    ray_runs = []
    for j in sorted({c[1] for c in rays}):
        xs = sorted(i for i, jj in rays if jj == j)
        start = prev = None
        for x in xs + [None]:
            if start is None:
                start = prev = x
            elif x is not None and x == prev + 1:
                prev = x
            else:
                ray_runs.append((start, prev + 1, j, j + 1))
                start = prev = x
    rm = []
    for r in sorted(ray_runs, key=lambda r: (r[0], r[1], r[2])):
        if rm and rm[-1][0] == r[0] and rm[-1][1] == r[1] and rm[-1][3] == r[2]:
            rm[-1] = (r[0], r[1], rm[-1][2], r[3])
        else:
            rm.append(r)
    return merged, rm


SUNBURST_9x7 = [          # eight equal rays round the medallion, so it reads as a sun rather than a cross
    "r...r...r",
    ".r.....r.",
    "..r...r..",
    "rr.....rr",
    "..r...r..",
    ".r.....r.",
    "r...r...r",
]


def holy_model():
    """Radiant heavy full plate. v2: gold kept to edges that mean something (brow, breastplate rim, pauldron
    rims, cuffs, poleyns, toe caps); lames separate by shadow lines instead of gold stripes; domed pauldrons
    with an upstanding gardbrace."""
    bones = skeleton()
    H, B, T = bones["armorHead"].cubes, bones["armorBody"].cubes, bones["armorLeggingTorsoLayer"].cubes
    RA, RL, RB, RX = (bones["armorRightArm"].cubes, bones["armorRightLeg"].cubes,
                      bones["armorRightBoot"].cubes, bones["armorTorsoExtensionRightLeg"].cubes)
    slits = {"k": ("visor", 0)}

    # ---- great helm: gold brow, flank breathing slits, visor with glowing eye slit, keel, gorget, comb, halo ----
    H.append(Cube("helm", (-5, 5), (24, 33), (-5, 5), "silver", {
        "sides": [hline(0, ramp="gold", lvl=5), shade_row(1, -2)],
        "right": [stamp(["kk", "..", "kk", "..", "kk"], slits, anchor="topleft", dx=6, dy=3)],
        "left": [stamp(["kk", "..", "kk", "..", "kk"], slits, anchor="topleft", dx=2, dy=3)],
        "back": [stamp([".s.", "sws", ".s."], {"s": SUN(2), "w": SUN(4)}, anchor="topleft", dx=3, dy=3),
                 stamp(["g...g", ".g.g."], {"g": G(5)}, anchor="topleft", dx=2, dy=6)],
        "top": [vline(4, 0, -1, "gold", 5), vline(5, 0, -1, "gold", 3)],
    }))
    H.append(Cube("visor", (-4, 4), (25, 31), (-5.75, -4.75), "silver", {
        "front": [
            hline(0, 0, -1, "silver", 7),
            stamp(["sss..sss", "ggg..ggg", "ddd..ddd"],
                  {"s": ("silver", 4), "g": ("sun", 4, True), "d": ("visor", 1)}, anchor="topleft", dy=1),
            stamp(["k......k", ".k....k."], slits, anchor="topleft", dy=4),
        ],
        "top": [hline(0, ramp="gold", lvl=6)],
    }))
    H.append(Cube("bevor", (-5.5, 5.5), (22, 25), (-5.5, 5.5), "silver", {
        "sides": [band("top", "gold", 5)],
        "front": [stamp(["s"], {"s": SUN(4)}, anchor="topleft", dx=5, dy=1)],
        "top": [outline("gold", 5)],
    }))
    H.append(Cube("comb", (-0.5, 0.5), (33, 35), (-4, 4), "gold", {
        "sides": [hline(0, ramp="gold", lvl=6)], "top": [vline(0, ramp="gold", lvl=6)],
    }))
    H.append(Cube("comb_top", (-0.5, 0.5), (35, 36), (-2, 3), "gold_hi", {"sides": [hline(0, ramp="gold", lvl=6)]}))
    H.append(Cube("halo_rod", (-0.75, 0.75), (30.25, 31.75), (5.25, 6.75), "gold", {}, inflate=0.25))
    ring, rays = halo_cells()
    for n, (x0, x1, y0, y1) in enumerate(ring):
        H.append(Cube(f"halo{n}", (x0, x1), (y0, y1), (6.5, 7.5), "sun", {
            "front": [hline(0, ramp="sun", lvl=4, glow=True)], "back": [hline(0, ramp="sun", lvl=4, glow=True)],
            "top": [hline(0, ramp="sun", lvl=5, glow=True)],
        }))
    for n, (x0, x1, y0, y1) in enumerate(rays):
        H.append(Cube(f"ray{n}", (x0, x1), (y0, y1), (6.5, 7.5), "sun", {"all": [hline(0, ramp="sun", lvl=5, glow=True)]}))

    # ---- cuirass: sunburst breastplate, plackart lame, winged backplate ----
    B.append(Cube("cuirass", (-5.25, 5.25), (14.75, 24.25), (-3.25, 3.25), "silver", {
        "sides": [rivets(1, ramp="silver", lvl=7, step=3, start=1)],
        "right": [vline(2, 2, -2, "silver", 3)], "left": [vline(3, 2, -2, "silver", 3)],
        "top": [band("top", "gold", 5), band("bottom", "gold", 5)],
    }))
    B.append(Cube("breast", (-4.5, 4.5), (16, 23), (-4, -3), "silver", {
        "front": [stamp(SUNBURST_9x7, {"r": SUN(3)}), band("top", "gold", 5),
                  band("left", "silver", 7, bevel=False), band("right", "silver", 3, bevel=False)],
        "sides": [band("top", "gold", 5)], "top": [hline(0, ramp="gold", lvl=6)],
    }))
    B.append(Cube("sun_medallion", (-1.5, 1.5), (18, 21), (-4.75, -3.75), "sun", {
        "front": [stamp(["bcb", "cwc", "bcb"], {"b": SUN(2), "c": SUN(4), "w": SUN(5)})],
    }))
    B.append(Cube("plackart", (-4.5, 4.5), (12, 16), (-3, 3), "silver", {
        "sides": [under_lip(0), hline(2, ramp="silver", lvl=2), hline(3, ramp="silver", lvl=6)],
    }))
    B.append(Cube("backplate", (-4.5, 4.5), (16, 23), (3, 4), "silver", {
        "back": [stamp(["g...s...g", "gg.sws.gg", ".gg.s.gg.", "hhgg.gghh", ".hhg.ghh.", "..hh.hh..", "...h.h..."],
                       {"g": G(5), "h": G(3), "s": SUN(3), "w": SUN(5)}),
                 band("top", "gold", 5)],
        "sides": [band("top", "gold", 5)],
    }))
    # ---- belt + faulds (LEGS slot, follows the body) ----
    T.append(Cube("fauld", (-5.5, 5.5), (10.5, 13.5), (-3.5, 3.5), "silver", {
        "sides": [band("top", "gold", 4), rivets(0, lvl=7, step=2, start=1)],
    }))
    T.append(Cube("buckle", (-1.25, 1.25), (10.75, 13.25), (-4.5, -3), "gold_hi", {
        "front": [stamp(["cw", "wc"], {"c": SUN(3), "w": SUN(5)})],
    }))
    # ---- tassets (CHEST slot, follow the legs) ----
    RX.append(Cube("tasset_hi", (-4.75, 0.75), (9.25, 12.75), (-4.25, -2.75), "silver", {
        "front": [under_lip(0), rivets(1, ramp="silver", lvl=7, step=4, start=0), vline(2, 1, -2, "silver", 7)],
    }))
    RX.append(Cube("tasset_lo", (-4.25, 0.25), (6.5, 10), (-3.75, -2.25), "silver", {
        "front": [band("bottom", "gold", 5)],
        "sides": [band("bottom", "gold", 3)],
    }))
    RX.append(Cube("tasset_side", (-5.75, -4.25), (7.75, 12.25), (-2.25, 2.25), "silver", {
        "right": [band("bottom", "gold", 4), rivets(1, ramp="silver", lvl=7, step=3, start=1)],
    }))
    # ---- arms: domed pauldron with gardbrace, two flaring lames with a radiant hem; rerebrace, couter, vambrace ----
    RA.append(Cube("pauldron_dome", (-8.5, -4.0), (25.25, 26.75), (-3.25, 3.25), "silver", {
        "top": [outline("gold", 5), vline(1, 1, -2, "silver", 7)], "sides": [hline(0, ramp="silver", lvl=7)],
    }))
    RA.append(Cube("gardbrace", (-6.75, -5.25), (25, 28.5), (-2.75, 2.75), "silver", {
        "sides": [hline(0, ramp="gold", lvl=5)], "right": [stamp(["s"], {"s": SUN(4)}, anchor="topleft", dx=2, dy=1)],
        "top": [rect(0, 0, -1, -1, "gold", 5)],
    }))
    RA.append(Cube("pauldron_cap", (-9.5, -3.5), (22.5, 25.5), (-3.5, 3.5), "silver", {
        "right": [stamp([".g.", "gsg", ".g."], {"g": G(5), "s": SUN(4)})],
        "top": [vline(0, 0, -1, "gold", 5), hline(0, ramp="gold", lvl=4), hline(-1, ramp="gold", lvl=5)],
    }))
    RA.append(Cube("pauldron_lame1", (-10.25, -4.75), (20.25, 22.75), (-3.75, 3.75), "silver", {
        "sides": [under_lip(0)], "top": [vline(0, 0, -1, "gold", 5)],
    }))
    RA.append(Cube("pauldron_lame2", (-10.75, -5.25), (18.25, 20.75), (-4.25, 4.25), "silver", {
        "sides": [under_lip(0), band("bottom", "sun", 2, glow=True)], "top": [vline(0, 0, -1, "gold", 5)],
    }))
    RA.append(Cube("rerebrace", (-8.5, -3.5), (15.5, 20.5), (-2.5, 2.5), "silver_dim", {
        "sides": [hline(2, ramp="silver", lvl=2), hline(3, ramp="silver", lvl=6)],
    }))
    RA.append(Cube("couter", (-9.25, -8.25), (14.75, 17.75), (-1.5, 1.5), "gold", {
        "right": [stamp([".c.", "cwc", ".c."], {"c": G(6), "w": SUN(4)})],
    }))
    RA.append(Cube("vambrace", (-8.75, -3.25), (11.75, 16.25), (-2.75, 2.75), "silver", {
        "sides": [band("top", "gold", 5)],
        "right": [stamp(["s.s", ".s."], {"s": SUN(3)}, anchor="topleft", dx=1, dy=1)],
        "front": [vline(2, 1, -2, "silver", 7)],
    }))
    # ---- legs: cuisse with ridge, gold poleyn with a sun, knee fan ----
    RL.append(Cube("cuisse", (-4.75, 0.75), (5.75, 12.25), (-2.75, 2.75), "silver", {
        "front": [vline(2, 0, -1, "silver", 7), vline(3, 0, -1, "silver", 3)],
        "sides": [rivets(1, ramp="silver", lvl=7, step=4, start=0)],
    }))
    RL.append(Cube("poleyn", (-3.75, -0.25), (4.25, 7.75), (-3.75, -2.25), "gold", {
        "front": [stamp(["s"], {"s": SUN(4)})],
    }))
    RL.append(Cube("knee_fan", (-5.5, -4.5), (4.5, 7.5), (-2, 1), "silver", {
        "right": [stamp(["g.g", ".g.", "ggg"], {"g": G(5)})],
    }))
    # ---- boots: greave, gold cuff, laminated sabaton, gold toe cap ----
    RB.append(Cube("greave", (-5, 1), (0.5, 6.5), (-3, 3), "silver", {
        "front": [vline(2, 0, -1, "silver", 7), vline(3, 0, -1, "silver", 4), stamp(["s"], {"s": SUN(4)}, anchor="topleft", dx=2, dy=1)],
        "sides": [rivets(1, ramp="silver", lvl=7, step=4, start=1)], "back": [vline(2, 0, -1, "silver", 3)],
    }))
    RB.append(Cube("greave_cuff", (-5.25, 1.25), (5.75, 7.25), (-3.25, 3.25), "gold", {"sides": [hline(0, ramp="gold", lvl=6)]}))
    RB.append(Cube("sabaton", (-4.75, 0.75), (-0.75, 1.75), (-4.25, 2.25), "silver", {
        "top": [hline(1, ramp="silver", lvl=3), hline(3, ramp="silver", lvl=3), hline(5, ramp="silver", lvl=7)],
    }))
    RB.append(Cube("toecap", (-4.25, 0.25), (-0.25, 1.25), (-5.25, -3.75), "gold_hi", {}))

    mirror_limbs(bones)
    return bones


# ----------------------------------------------------------------------------------------------
# ENDER v2: the Voidwalker. Lean End-assassin plate in blue-violet night steel under a void-cloth hood:
# enderman-magenta eyes in a shadowed face, an Eye-of-Ender clasp at a V collar, hidden blades on both
# forearms, a heavy left pauldron growing violet end crystals, and split coat tails that move with the legs.
# Glow is kept to the eyes, the clasp and buckle, the crystals, the blade edges and one pauldron hem.
# ----------------------------------------------------------------------------------------------
N = lambda l: ("night", l)
AM = lambda l: ("amethyst", l)
MG = lambda l: ("magenta", l, True)
PE = lambda l: ("pearl", l, True)
VI = lambda l: ("violet", l, True)
EYE_GEM = (["aBa", "BkB", "aBa"], {"a": PE(2), "B": PE(4), "k": N(0)})
V_COLLAR = ["AddddddA", ".AddddA.", "..AddA..", "...AA..."]


def ender_model():
    bones = skeleton()
    H, B, T = bones["armorHead"].cubes, bones["armorBody"].cubes, bones["armorLeggingTorsoLayer"].cubes
    RA, RL, RB, RX = (bones["armorRightArm"].cubes, bones["armorRightLeg"].cubes,
                      bones["armorRightBoot"].cubes, bones["armorTorsoExtensionRightLeg"].cubes)
    LA = bones["armorLeftArm"].cubes

    # ---- hood: shadowed face with enderman eyes, shinobi mask, amethyst-rimmed opening, peak, tail and drape ----
    H.append(Cube("face", (-4.625, 4.625), (23.375, 32.625), (-4.625, 4.625), "night_dk", {
        "front": [rect(0, 0, -1, -1, "night", 1), rect(0, 0, -1, 2, "night", 0),
                  stamp([".mMm.mMm."], {"m": MG(1), "M": MG(3)}, anchor="topleft", dy=4)],
    }))
    H.append(Cube("hood_top", (-5.25, 5.25), (32.0, 33.5), (-5.25, 5.25), "cloth", {
        "top": [hline(-1, ramp="amethyst", lvl=4)],
        "front": [hline(0, ramp="amethyst", lvl=4)],
    }))
    H.append(Cube("hood_crown", (-3.75, 3.75), (33.0, 34.5), (-4.25, 4.25), "cloth", {
        "top": [vline(3, ramp="cloth", lvl=5)], "back": [vline(3, ramp="cloth", lvl=5)],
    }))
    side = Cube("hood_side", (-5.5, -4.0), (25.25, 32.75), (-5.25, 5.25), "cloth", {
        "right": [vline(-1, ramp="amethyst", lvl=4), vline(-2, ramp="amethyst", lvl=2)],
        "front": [vline(0, ramp="amethyst", lvl=4)],
        "left": [rect(0, 0, -1, -1, "cloth", 1)],
    })
    H.append(side)
    H.append(side.mirrored("hood_side_l"))
    H.append(Cube("hood_back", (-4.75, 4.75), (23.75, 33.25), (4.25, 5.75), "cloth", {
        "back": [stamp(["..a..", ".a.a.", "a.M.a", ".a.a.", "..a.."], {"a": AM(3), "M": MG(2)}, anchor="top", dy=1),
                 vline(0, ramp="amethyst", lvl=1), vline(-1, ramp="amethyst", lvl=1), hline(-1, ramp="amethyst", lvl=3)],
    }))
    H.append(Cube("hood_peak", (-1.75, 1.75), (32.75, 34.25), (-6.25, -4.75), "night_hi", {
        "front": [hline(0, ramp="amethyst", lvl=5)], "top": [hline(-1, ramp="amethyst", lvl=4)],
    }))
    H.append(Cube("hood_tail", (-1.25, 1.25), (31.25, 33.75), (5.25, 6.75), "cloth", {}))
    H.append(Cube("hood_drape", (-4.25, 4.25), (22.25, 24.75), (4.75, 6.25), "cloth", {
        "back": [hline(-1, ramp="amethyst", lvl=3)],
    }))
    H.append(Cube("mask", (-3.75, 3.75), (23.75, 27.25), (-5.0, -3.5), "night_hi", {
        "front": [hline(0, ramp="night", lvl=5), vline(3, 1, -1, "night", 6),
                  stamp([".k...k.", ".k...k."], {"k": N(1)}, anchor="topleft", dy=1)],
        "top": [hline(0, ramp="night", lvl=6)],
    }))

    # ---- cuirass: V-collared breastplate with an Eye-of-Ender clasp, stepped lames, segmented spine ----
    B.append(Cube("cuirass", (-4.75, 4.75), (13.75, 24.25), (-2.75, 2.75), "night", {
        "right": [vline(2, 1, -2, "night", 2), vline(3, 1, -2, "night", 5)],
        "left": [vline(1, 1, -2, "night", 5), vline(2, 1, -2, "night", 2)],
        "top": [hline(0, ramp="amethyst", lvl=3), hline(-1, ramp="amethyst", lvl=3)],
    }))
    B.append(Cube("collar", (-3.75, 3.75), (23.75, 25.25), (-0.25, 3.25), "amethyst", {}))
    B.append(Cube("breastplate", (-4.25, 4.25), (18.25, 23.75), (-3.75, -2.25), "night_hi", {
        "front": [stamp(V_COLLAR, {"A": AM(4), "d": N(1)}, anchor="topleft")],
        "top": [hline(0, ramp="amethyst", lvl=4)],
    }))
    B.append(Cube("eye_clasp", (-1.75, 1.75), (19.0, 22.5), (-4.25, -2.75), "amethyst", {
        "front": [stamp(*EYE_GEM)],
    }))
    B.append(Cube("lame0", (-4.25, 4.25), (16.25, 18.75), (-3.25, -1.75), "night", {}))
    B.append(Cube("lame1", (-4.25, 4.25), (14.25, 16.75), (-3.0, -1.5), "night", {}))
    B.append(Cube("lame2", (-3.75, 3.75), (12.75, 15.25), (-2.9, -1.4), "night_dk", {}))
    B.append(Cube("spine", (-1.25, 1.25), (13.25, 23.75), (2.25, 3.75), "night_hi", {
        "back": [shade_row(1, -2), shade_row(3, -2), shade_row(5, -2), shade_row(7, -2), hline(0, ramp="amethyst", lvl=4)],
    }))
    blade_r = Cube("shoulder_blade", (-4.5, -1.0), (18.25, 23.75), (2.0, 3.5), "night", {
        "back": [hline(0, ramp="amethyst", lvl=4), under_lip(1)],
    })
    B.append(blade_r)
    B.append(blade_r.mirrored("shoulder_blade_l"))
    # ---- belt with a pearl buckle (LEGS slot, follows the body) ----
    T.append(Cube("belt", (-5, 5), (11.5, 13.5), (-3, 3), "night_dk", {
        "sides": [hline(0, ramp="amethyst", lvl=3)],
    }))
    T.append(Cube("buckle", (-1.25, 1.25), (11.25, 13.75), (-3.75, -2.25), "amethyst", {
        "front": [stamp(["bA", "AA"], {"b": AM(6), "A": AM(4)})],
    }))
    # ---- tasset and split coat tails (CHEST slot, follow the legs) ----
    RX.append(Cube("tasset", (-4.25, -0.75), (8.75, 12.25), (-3.25, -1.75), "night_hi", {
        "front": [ridge(1)],
    }))
    RX.append(Cube("coat_back", (-4.5, 0.0), (3.75, 12.25), (2.25, 3.75), "cloth", {
        "back": [vline(0, ramp="cloth", lvl=0), vline(-1, ramp="amethyst", lvl=2),
                 hline(-1, ramp="amethyst", lvl=3), stamp(["a.a."], {"a": ("cloth", 0)}, anchor="bottom")],
    }))
    RX.append(Cube("coat_side", (-5.0, -3.5), (5.75, 12.25), (-2.25, 2.25), "cloth", {
        "right": [hline(-1, ramp="amethyst", lvl=3), vline(-1, 0, -2, "amethyst", 2)],
    }))
    # ---- right arm: light cap, plated sleeve, hidden blade on the forearm ----
    RA.append(Cube("cap", (-9.0, -3.5), (22.25, 24.75), (-3.25, 3.25), "night_hi", {
        "sides": [hline(-1, ramp="amethyst", lvl=3)], "top": [vline(0, ramp="amethyst", lvl=4)],
    }))
    RA.append(Cube("cap_top", (-8.75, -5.75), (24.5, 25.5), (-2.5, 2.5), "night_hi", {}))
    sleeve = [
        Cube("upper", (-8.5, -3.5), (16.5, 22.5), (-2.5, 2.5), "night_dk", {"sides": [shade_row(3, -1)]}),
        Cube("elbow", (-9.25, -8.25), (16.0, 18.0), (-1.0, 1.0), "amethyst", {}),
        Cube("bracer", (-8.75, -3.25), (11.75, 16.25), (-2.75, 2.75), "night_hi", {"sides": [hline(0, ramp="amethyst", lvl=4)]}),
        Cube("blade_housing", (-9.75, -8.25), (13.25, 15.75), (-1.25, 1.25), "amethyst", {}),
        Cube("hidden_blade", (-9.5, -8.5), (9.25, 13.25), (-0.5, 0.5), "blade", {
            "front": [vline(0, ramp="violet", lvl=2, glow=True)], "back": [vline(0, ramp="violet", lvl=1, glow=True)],
            "bottom": [rect(0, 0, -1, -1, "blade", 4)]}),
    ]
    RA.extend(sleeve)
    LA.extend(c.mirrored(c.name + "_l") for c in sleeve)
    # ---- left arm: heavy layered pauldron growing violet end crystals ----
    LA.append(Cube("pauldron_cap", (3.75, 9.25), (22.25, 24.75), (-3.75, 3.75), "night_hi", {
        "top": [vline(-1, ramp="amethyst", lvl=4), hline(0, ramp="amethyst", lvl=3), hline(-1, ramp="amethyst", lvl=3)],
    }))
    LA.append(Cube("pauldron_dome", (5.5, 9.5), (24.5, 25.5), (-2.5, 2.5), "night_hi", {}))
    LA.append(Cube("pauldron_lame1", (4.75, 10.25), (20.25, 22.75), (-3.75, 3.75), "night", {
        "sides": [under_lip(0), band("bottom", "violet", 1, glow=True)],
    }))
    LA.append(Cube("pauldron_lame2", (5.75, 10.75), (18.5, 20.5), (-3.5, 3.5), "night_dk", {
        "sides": [under_lip(0), hline(-1, ramp="amethyst", lvl=3)],
    }))
    for n, (xb, yb, zb) in enumerate((((6.75, 7.75), (25.5, 29.5), (-1.75, -0.75)),
                                      ((8.0, 9.0), (25.5, 28.5), (0.25, 1.25)),
                                      ((5.75, 6.75), (25.5, 27.5), (1.5, 2.5)),
                                      ((8.5, 9.5), (25.5, 26.5), (-2.5, -1.5)))):
        LA.append(Cube(f"crystal{n}", xb, yb, zb, "crystal", {}))
    # ---- legs: cuisse with a ridge and side seam, amethyst knee cop ----
    RL.append(Cube("cuisse", (-4.5, 0.5), (5.5, 12.5), (-2.5, 2.5), "night", {
        "front": [ridge(2)], "right": [vline(2, 1, -2, "night", 2)],
    }))
    RL.append(Cube("knee", (-3.25, -0.75), (5.25, 7.75), (-3.5, -2.0), "night_hi", {
        "front": [hline(0, ramp="amethyst", lvl=4)], "top": [rect(0, 0, -1, -1, "amethyst", 4)]}))
    # ---- boots: slim greave, raised shin guard, amethyst cuff, pointed sabaton ----
    RB.append(Cube("greave", (-4.75, 0.75), (0.25, 6.75), (-2.75, 2.75), "night", {"back": [ridge(2)]}))
    RB.append(Cube("shin", (-3.25, -0.75), (1.75, 6.25), (-3.25, -1.75), "night_hi", {
        "front": [vline(0, 0, -1, "night", 7)],
    }))
    RB.append(Cube("foot", (-4.5, 0.5), (-0.5, 1.5), (-3.5, 2.5), "night", {
        "top": [shade_row(2, -1), shade_row(4, -1)],
    }))
    RB.append(Cube("toe", (-3.25, -0.75), (-0.25, 1.25), (-4.75, -3.25), "night_hi", {}))
    RB.append(Cube("toe_tip", (-2.5, -1.5), (-0.25, 0.75), (-5.5, -4.5), "blade", {}))

    for src, dst in (("armorRightLeg", "armorLeftLeg"), ("armorRightBoot", "armorLeftBoot"),
                     ("armorTorsoExtensionRightLeg", "armorTorsoExtensionLeftLeg")):
        for c in bones[src].cubes:
            bones[dst].cubes.append(c.mirrored(c.name + "_l"))
    return bones


# ----------------------------------------------------------------------------------------------
# BLOOD: the Blood Knight. Crimson heavy plate with gold filigree over blackened iron: a closed helm with a
# pointed visor, swept bat-wing crests and a crest fin; layered spiked pauldrons; a gold chevron and blood
# jewel on the breast, a black winged device on the back, a gold skull at the belt. Glow is only the eye slit.
# ----------------------------------------------------------------------------------------------
CR = lambda l: ("crimson", l)
IR = lambda l: ("iron", l)
EMB = lambda l: ("ember", l, True)
CHEVRON = ["g.......g", "gg.....gg", ".gg...gg.", "..gg.gg..", "...gdg...", "....g....", "........."]
BAT_DEVICE = ["k.......k", "kk..k..kk", ".kkkkkkk.", "..kkkkk..", "...kkk...", "....k....", "...k.k...", "..k...k.."]
SKULL = [".GGG.", "GkGkG", "GGkGG", ".gGg."]


def blood_model():
    bones = skeleton()
    H, B, T = bones["armorHead"].cubes, bones["armorBody"].cubes, bones["armorLeggingTorsoLayer"].cubes
    RA, RL, RB, RX = (bones["armorRightArm"].cubes, bones["armorRightLeg"].cubes,
                      bones["armorRightBoot"].cubes, bones["armorTorsoExtensionRightLeg"].cubes)

    # ---- helm: crimson great helm, pointed visor with a dim ember eye slit, bat-wing crests, crest fin ----
    H.append(Cube("helm", (-5, 5), (24, 33), (-5, 5), "crimson", {
        "sides": [hline(0, ramp="gold", lvl=5), shade_row(1, -2), lames([6])],
        "back": [vline(4, 1, -1, "iron", 2), vline(5, 1, -1, "iron", 1)],
        "top": [vline(4, 0, -1, "iron", 3), vline(5, 0, -1, "iron", 2)],
    }))
    H.append(Cube("visor", (-4, 4), (25, 31), (-5.75, -4.75), "crimson", {
        "front": [hline(0, 0, -1, "crimson", 7),
                  stamp(["kkk..kkk", "EEE..EEE", "kkk..kkk", "........", "k.k..k.k"],
                        {"k": IR(0), "E": EMB(1)}, anchor="topleft", dy=1)],
        "top": [hline(0, ramp="gold", lvl=6)],
    }))
    H.append(Cube("visor_beak", (-1.5, 1.5), (24.5, 30.5), (-6.75, -5.75), "crimson_hi", {
        "front": [vline(1, 0, -1, "crimson", 7), vline(2, 0, -1, "crimson", 3), band("bottom", "gold", 4)],
        "top": [rect(0, 0, -1, -1, "gold", 6)],
    }))
    H.append(Cube("bevor", (-5.5, 5.5), (22, 25), (-5.5, 5.5), "crimson", {
        "sides": [band("top", "gold", 5)], "top": [outline("gold", 5)],
    }))
    H.append(Cube("crest_fin", (-0.5, 0.5), (33, 35), (-4, 4), "iron", {
        "sides": [hline(0, ramp="gold", lvl=5)], "top": [vline(0, ramp="gold", lvl=5)],
    }))
    H.append(Cube("crest_horn", (-0.5, 0.5), (35, 37), (-3, 1), "crimson_hi", {"sides": [hline(0, ramp="gold", lvl=6)]}))
    H.append(Cube("crest_tip", (-0.5, 0.5), (37, 38), (-3, -1), "gold_hi", {}))
    # bat wings: membrane panels stepping up, out and back from the temples, gold along the leading edge
    membrane = {"front": [hline(0, ramp="gold", lvl=5), vline(-1, 1, -1, "crimson", 1)],
                "back": [hline(0, ramp="gold", lvl=4), vline(0, 1, -1, "crimson", 1)],
                "top": [rect(0, 0, -1, -1, "gold", 5)]}
    wing = [Cube("wing_root", (-6.0, -5.0), (28, 31), (-1, 2), "iron", {"right": [hline(0, ramp="gold", lvl=5)]}),
            Cube("wing_inner", (-8.0, -5.0), (29, 34), (0, 1), "crimson_dk", {
                **membrane, "front": [hline(0, ramp="gold", lvl=5), vline(1, 1, -1, "crimson", 1), stamp(["k.k"], {"k": CR(1)}, anchor="bottom")]}),
            Cube("wing_outer", (-10.0, -7.0), (32, 37), (1, 2), "crimson_dk", {
                **membrane, "front": [hline(0, ramp="gold", lvl=5), vline(1, 1, -1, "crimson", 1), stamp(["k.k"], {"k": CR(1)}, anchor="bottom")]}),
            Cube("wing_spar", (-11.0, -9.0), (36, 39), (2, 3), "crimson_hi", {"front": [hline(0, ramp="gold", lvl=5)], "top": [rect(0, 0, -1, -1, "gold", 5)]}),
            Cube("wing_claw", (-12.0, -11.0), (38, 40), (2, 3), "gold_hi", {})]
    H.extend(wing)
    H.extend(c.mirrored(c.name + "_l") for c in wing)

    # ---- cuirass: gold chevron and blood jewel on the breast, plackart lames, black winged device on the back ----
    B.append(Cube("cuirass", (-5.25, 5.25), (14.75, 24.25), (-3.25, 3.25), "crimson", {
        "sides": [rivets(1, ramp="gold", lvl=6, step=3, start=1)],
        "right": [vline(2, 2, -2, "crimson", 2)], "left": [vline(3, 2, -2, "crimson", 2)],
        "top": [band("top", "gold", 5), band("bottom", "gold", 5)],
    }))
    B.append(Cube("breast", (-4.5, 4.5), (16, 23), (-4, -3), "crimson_hi", {
        "front": [stamp(CHEVRON, {"g": G(5), "d": EMB(2)}), band("top", "gold", 5), ridge(4),
                  band("left", "crimson", 7, bevel=False), band("right", "crimson", 2, bevel=False)],
        "sides": [band("top", "gold", 5)], "top": [hline(0, ramp="gold", lvl=6)],
    }))
    B.append(Cube("plackart", (-4.5, 4.5), (12, 16), (-3, 3), "crimson", {
        "sides": [under_lip(0), hline(2, ramp="crimson", lvl=1), hline(3, ramp="crimson", lvl=6), band("bottom", "gold", 4)],
    }))
    B.append(Cube("backplate", (-4.5, 4.5), (15, 23), (3, 4), "crimson", {
        "back": [stamp(BAT_DEVICE, {"k": IR(1)}), band("top", "gold", 5), band("bottom", "gold", 3)],
        "sides": [band("top", "gold", 5)],
    }))
    # ---- belt, faulds and gold skull (LEGS slot, follows the body) ----
    T.append(Cube("fauld", (-5.5, 5.5), (10.5, 13.5), (-3.5, 3.5), "crimson_dk", {
        "sides": [band("top", "gold", 4)],
    }))
    T.append(Cube("skull", (-2.5, 2.5), (9.75, 13.75), (-4.5, -3.5), "gold", {
        "front": [stamp(SKULL, {"g": G(2), "G": G(5), "k": IR(0)}, anchor="topleft")],
    }))
    # ---- tassets (CHEST slot, follow the legs) ----
    RX.append(Cube("tasset_hi", (-4.75, 0.75), (9.25, 12.75), (-4.25, -2.75), "crimson", {
        "front": [under_lip(0), band("bottom", "gold", 4)], "sides": [band("bottom", "gold", 3)],
    }))
    RX.append(Cube("tasset_lo", (-4.25, 0.25), (6.5, 10), (-3.75, -2.25), "crimson_dk", {
        "front": [band("bottom", "gold", 5), vline(2, 0, -2, "crimson", 5)], "sides": [band("bottom", "gold", 3)],
    }))
    RX.append(Cube("tasset_side", (-5.75, -4.25), (7.75, 12.25), (-2.25, 2.25), "crimson", {
        "right": [band("bottom", "gold", 4), lames([2])],
    }))
    # ---- arms: three-tier spiked pauldrons, blackened rerebrace, spiked couter, crimson vambrace ----
    RA.append(Cube("pauldron_cap", (-9.5, -3.5), (22.5, 25.5), (-3.5, 3.5), "crimson", {
        "right": [stamp([".g.", "gdg", ".g."], {"g": G(5), "d": EMB(1)})],
        "top": [outline("gold", 5), vline(1, 1, -2, "crimson", 7)],
    }))
    RA.append(Cube("pauldron_lame1", (-10.25, -4.75), (20.25, 22.75), (-3.75, 3.75), "crimson", {
        "sides": [under_lip(0)], "top": [vline(0, 0, -1, "gold", 5)],
    }))
    RA.append(Cube("pauldron_lame2", (-10.75, -5.25), (18.25, 20.75), (-4.25, 4.25), "crimson_dk", {
        "sides": [under_lip(0), band("bottom", "gold", 5)], "top": [vline(0, 0, -1, "gold", 5)],
    }))
    RA.append(Cube("spike_base", (-8.75, -6.75), (25.5, 27.5), (-1, 1), "crimson_hi", {"sides": [band("bottom", "gold", 4)]}))
    RA.append(Cube("spike_tip", (-8.25, -7.25), (27.5, 29.5), (-0.5, 0.5), "gold_hi", {}))
    RA.append(Cube("rerebrace", (-8.5, -3.5), (15.5, 20.5), (-2.5, 2.5), "iron", {
        "sides": [hline(2, ramp="iron", lvl=1), hline(3, ramp="iron", lvl=5)],
    }))
    RA.append(Cube("couter", (-9.25, -8.25), (14.75, 17.75), (-1.5, 1.5), "gold", {
        "right": [stamp([".c.", "cGc", ".c."], {"c": G(6), "G": G(3)})],
    }))
    RA.append(Cube("couter_spike", (-10.25, -9.25), (15.75, 16.75), (-0.5, 0.5), "gold_hi", {}))
    RA.append(Cube("vambrace", (-8.75, -3.25), (11.75, 16.25), (-2.75, 2.75), "crimson", {
        "sides": [band("top", "gold", 5), band("bottom", "gold", 3)], "front": [vline(2, 1, -2, "crimson", 7)],
    }))
    # ---- legs: crimson cuisse, gold poleyn with a forward knee spike ----
    RL.append(Cube("cuisse", (-4.75, 0.75), (5.75, 12.25), (-2.75, 2.75), "crimson", {
        "front": [vline(2, 0, -1, "crimson", 7), vline(3, 0, -1, "crimson", 2)], "sides": [lames([3])],
    }))
    RL.append(Cube("poleyn", (-3.75, -0.25), (4.25, 7.75), (-3.75, -2.25), "gold", {
        "front": [stamp([".g.", "gdg", ".g."], {"g": G(6), "d": CR(3)})],
    }))
    RL.append(Cube("knee_spike", (-2.5, -1.5), (5.5, 6.5), (-4.75, -3.75), "gold_hi", {}))
    RL.append(Cube("knee_wing", (-5.5, -4.5), (4.5, 7.5), (-2, 1), "crimson_dk", {"right": [band("top", "gold", 5)]}))
    # ---- boots: crimson greave, gold cuff, blackened sabaton, pointed toe ----
    RB.append(Cube("greave", (-5, 1), (0.5, 6.5), (-3, 3), "crimson", {
        "front": [vline(2, 0, -1, "crimson", 7), vline(3, 0, -1, "crimson", 3)], "back": [vline(2, 0, -1, "crimson", 2)],
    }))
    RB.append(Cube("greave_cuff", (-5.25, 1.25), (5.75, 7.25), (-3.25, 3.25), "gold", {"sides": [hline(0, ramp="gold", lvl=6)]}))
    RB.append(Cube("sabaton", (-4.75, 0.75), (-0.75, 1.75), (-4.25, 2.25), "iron", {
        "top": [hline(1, ramp="iron", lvl=1), hline(3, ramp="iron", lvl=1), hline(5, ramp="iron", lvl=5)],
    }))
    RB.append(Cube("toecap", (-3.75, -0.25), (-0.25, 1.25), (-5.25, -3.75), "crimson_hi", {"top": [hline(-1, ramp="gold", lvl=5)]}))
    RB.append(Cube("toe_point", (-2.5, -1.5), (-0.25, 0.75), (-6.25, -5.25), "gold", {}))

    mirror_limbs(bones)
    return bones


def placeholder_model(school):
    """Plain plate in the school's colours, standing in until the school's own art pass."""
    def factory():
        bones = skeleton()
        H, B, T = bones["armorHead"].cubes, bones["armorBody"].cubes, bones["armorLeggingTorsoLayer"].cubes
        RA, RL, RB = bones["armorRightArm"].cubes, bones["armorRightLeg"].cubes, bones["armorRightBoot"].cubes
        m, a, g = f"{school}_metal", f"{school}_accent", f"{school}_glow"
        H.append(Cube("helm", (-5, 5), (24, 33), (-5, 5), m, {"sides": [shade_row(1, -2)]}))
        H.append(Cube("visor", (-4, 4), (26, 30), (-5.75, -4.75), m, {"front": [hline(1, 1, -2, "iron", 0)]}))
        H.append(Cube("brow", (-4.5, 4.5), (30, 31), (-6, -5), a, {}))
        H.append(Cube("eyes", (-2.5, 2.5), (27, 28), (-6, -5), g, {}))
        H.append(Cube("bevor", (-5.5, 5.5), (22, 25), (-5.5, 5.5), m, {}))
        B.append(Cube("cuirass", (-5.25, 5.25), (14.75, 24.25), (-3.25, 3.25), m, {"sides": [lames([5])]}))
        B.append(Cube("gem", (-1, 1), (19, 21), (-4, -3), g, {}))
        T.append(Cube("fauld", (-5.5, 5.5), (10.5, 13.5), (-3.5, 3.5), m, {}))
        T.append(Cube("belt", (-5.75, 5.75), (12.75, 14.25), (-3.75, 3.75), a, {}))
        RA.append(Cube("pauldron", (-9.5, -3.5), (22.5, 25.5), (-3.5, 3.5), m, {"sides": [band("bottom", "iron", 2)]}))
        RA.append(Cube("pauldron_trim", (-9.75, -3.25), (21.75, 23.25), (-3.75, 3.75), a, {}))
        RA.append(Cube("vambrace", (-8.75, -3.25), (11.75, 16.25), (-2.75, 2.75), m, {}))
        RL.append(Cube("cuisse", (-4.75, 0.75), (5.75, 12.25), (-2.75, 2.75), m, {}))
        RL.append(Cube("poleyn", (-3.75, -0.25), (4.25, 7.75), (-3.75, -2.25), a, {}))
        RB.append(Cube("greave", (-5, 1), (0.5, 6.5), (-3, 3), m, {}))
        RB.append(Cube("cuff", (-5.25, 1.25), (5.75, 7.25), (-3.25, 3.25), a, {}))
        mirror_limbs(bones)
        return bones
    return factory


BUILDERS = {"holy": holy_model, "ender": ender_model, "blood": blood_model,
            "evocation": placeholder_model("evocation"), "nature": placeholder_model("nature"),
            "eldritch": placeholder_model("eldritch")}


def mirror_limbs(bones):
    for src, dst in MIRROR_BONE.items():
        for c in bones[src].cubes:
            bones[dst].cubes.append(c.mirrored(c.name + "_l"))


# ----------------------------------------------------------------------------------------------
# Atlas packing + painting
# ----------------------------------------------------------------------------------------------
def all_cubes(bones):
    for b in bones.values():
        for c in b.cubes:
            yield b, c


def pack(bones, size=TEX):
    cubes = [c for _, c in all_cubes(bones)]
    order = sorted(cubes, key=lambda c: (-c.uv_box()[1], -c.uv_box()[0], c.name))
    x = y = shelf = 0
    for c in order:
        w, h = c.uv_box()
        if x + w > size:
            x, y, shelf = 0, y + shelf, 0
        if y + h > size:
            raise SystemExit(f"atlas overflow at {c.name}")
        c.uv = (x, y)
        x += w
        shelf = max(shelf, h)
    return y + shelf


FACE_SRC = {"right": "left", "left": "right"}


def paint_face(cube, face, school):
    """Paint one face; mirrored cubes reuse the source cube's opposite face, flipped."""
    src, src_face, flip = cube, face, False
    if cube.mirror_of is not None:
        src, src_face, flip = cube.mirror_of, FACE_SRC.get(face, face), True
    w, h, d = src.size
    fw, fh = {"right": (d, h), "left": (d, h), "front": (w, h), "back": (w, h), "top": (w, d), "bottom": (w, d)}[src_face]
    f = Face(fw, fh, src_face, random.Random(seed_for(school, src.name, src_face)))
    MATERIALS[src.mat](f)
    for op in src.deco.get(src_face, []):
        op(f)
    if flip:
        f.hflip()
    return f


def paint(bones, school):
    base = Image.new("RGBA", (TEX, TEX), (0, 0, 0, 0))
    glow = Image.new("RGBA", (TEX, TEX), (0, 0, 0, 0))
    bp, gp = base.load(), glow.load()
    for _, c in all_cubes(bones):
        for face, (u, v, fw, fh) in c.face_rects().items():
            f = paint_face(c, face, school)
            assert (f.w, f.h) == (fw, fh), (c.name, face)
            for y in range(fh):
                for x in range(fw):
                    if f.px[y][x] is None:
                        raise SystemExit(f"unpainted texel {c.name}/{face} {x},{y}")
                    if bp[u + x, v + y][3] != 0:
                        raise SystemExit(f"UV overlap at {c.name}/{face}")
                    col = f.rgba(x, y)
                    bp[u + x, v + y] = col
                    if f.glow[y][x]:
                        gp[u + x, v + y] = col
    return base, glow


def geo_json(bones, ident):
    out_bones = []
    for b in bones.values():
        e = {"name": b.name}
        if b.parent:
            e["parent"] = b.parent
        e["pivot"] = b.pivot
        if b.cubes:
            cl = []
            for c in b.cubes:
                ce = {"origin": [round(v, 4) for v in c.origin], "size": c.size}
                if c.inflate:
                    ce["inflate"] = c.inflate
                ce["uv"] = list(c.uv)
                cl.append(ce)
            e["cubes"] = cl
        out_bones.append(e)
    return {
        "format_version": "1.12.0",
        "minecraft:geometry": [{
            "description": {
                "identifier": ident, "texture_width": TEX, "texture_height": TEX,
                "visible_bounds_width": 3, "visible_bounds_height": 3.5, "visible_bounds_offset": [0, 1.25, 0],
            },
            "bones": out_bones,
        }],
    }


def resolve_coplanar(bones, step=0.05, passes=8):
    """Nudge cubes so no two armour faces share a plane where they overlap (in-game z-fighting).

    Origins may be any float (only sizes must stay whole texels), so the later cube of each clashing pair
    slides 0.05 px inward along the shared face's normal; the earlier cube keeps the visible surface.
    """
    for _ in range(passes):
        clashes = [i for i in coplanar_report(bones, armour_only=True)]
        if not clashes:
            return
        moved = set()
        for (_, _, axis, direction, _, _), cube in clashes:
            if id(cube) in moved:
                continue
            moved.add(id(cube))
            d = -direction * step
            k = "xyz".index(axis)
            if k == 0:
                cube.xb = (cube.xb[0] + d, cube.xb[1] + d)
            elif k == 1:
                cube.yb = (cube.yb[0] + d, cube.yb[1] + d)
            else:
                cube.zb = (cube.zb[0] + d, cube.zb[1] + d)
            cube.origin[k] += d
    left = coplanar_report(bones, armour_only=True)
    if left:
        raise SystemExit(f"could not resolve {len(left)} coplanar armour faces")


def coplanar_report(bones, armour_only=False):
    """Same-facing coplanar overlapping faces inside the armour (true z-fighting risks).

    armour_only=True returns [(face_tuple, cube_to_move)] for armour-vs-armour clashes only.
    """
    faces = []
    cube_by_key = {}
    for b, c in all_cubes(bones):
        cube_by_key[(b.name, c.name)] = c
        x0, x1 = c.xb; y0, y1 = c.yb; z0, z1 = c.zb
        faces += [(b.name, c.name, "x", -1, x0, (y0, y1, z0, z1)), (b.name, c.name, "x", 1, x1, (y0, y1, z0, z1)),
                  (b.name, c.name, "y", -1, y0, (x0, x1, z0, z1)), (b.name, c.name, "y", 1, y1, (x0, x1, z0, z1)),
                  (b.name, c.name, "z", -1, z0, (x0, x1, y0, y1)), (b.name, c.name, "z", 1, z1, (x0, x1, y0, y1))]
    if armour_only:
        out = []
        for i in range(len(faces)):
            for j in range(i + 1, len(faces)):
                a, b = faces[i], faces[j]
                if a[2] != b[2] or a[3] != b[3] or abs(a[4] - b[4]) > 1e-6 or a[1] == b[1] and a[0] == b[0]:
                    continue
                ra, rb = a[5], b[5]
                if min(ra[1], rb[1]) - max(ra[0], rb[0]) > 1e-6 and min(ra[3], rb[3]) - max(ra[2], rb[2]) > 1e-6:
                    out.append((b, cube_by_key[(b[0], b[1])]))
        return out
    # vanilla body skin and overlay planes (skin, +0.25 jacket/sleeve/pants, +0.5 hat)
    body = {"head": ((-4, 4), (24, 32), (-4, 4), (0, 0.5)), "body": ((-4, 4), (12, 24), (-2, 2), (0, 0.25)),
            "rarm": ((-8, -4), (12, 24), (-2, 2), (0, 0.25)), "larm": ((4, 8), (12, 24), (-2, 2), (0, 0.25)),
            "rleg": ((-4, 0), (0, 12), (-2, 2), (0, 0.25)), "lleg": ((0, 4), (0, 12), (-2, 2), (0, 0.25))}
    for n, (xb, yb, zb, infl) in body.items():
        for i in infl:
            x0, x1, y0, y1, z0, z1 = xb[0] - i, xb[1] + i, yb[0] - i, yb[1] + i, zb[0] - i, zb[1] + i
            faces += [("player", f"{n}+{i}", "x", -1, x0, (y0, y1, z0, z1)), ("player", f"{n}+{i}", "x", 1, x1, (y0, y1, z0, z1)),
                      ("player", f"{n}+{i}", "y", -1, y0, (x0, x1, z0, z1)), ("player", f"{n}+{i}", "y", 1, y1, (x0, x1, z0, z1)),
                      ("player", f"{n}+{i}", "z", -1, z0, (x0, x1, y0, y1)), ("player", f"{n}+{i}", "z", 1, z1, (x0, x1, y0, y1))]
    issues = []
    for i in range(len(faces)):
        for j in range(i + 1, len(faces)):
            a, b = faces[i], faces[j]
            if a[2] != b[2] or a[3] != b[3] or abs(a[4] - b[4]) > 1e-6:
                continue
            if a[0] == "player" and b[0] == "player":
                continue
            if a[1] == b[1]:
                continue
            ra, rb = a[5], b[5]
            ou = min(ra[1], rb[1]) - max(ra[0], rb[0])
            ov = min(ra[3], rb[3]) - max(ra[2], rb[2])
            if ou > 1e-6 and ov > 1e-6:
                issues.append(f"{a[0]}/{a[1]} vs {b[0]}/{b[1]} plane {a[2]}={a[4]} dir {a[3]:+d} overlap {ou:.2f}x{ov:.2f}")
    return issues


# ----------------------------------------------------------------------------------------------
# 16x16 inventory icons (vanilla-icon style: dark outline, top-left light)
# ----------------------------------------------------------------------------------------------
ICONS = {
    "helmet": {
        "holy": [
            ".....GGGGGG.....",
            "...GG......GG...",
            "..G.oooooooo.G..",
            "..G.o554443o.G..",
            "..G.obbbbbbo.G..",
            "...Go544443oG...",
            "....okGkkGko....",
            "....o544443o....",
            "....o554433o....",
            "....o544443o....",
            "...obbbbbbbbo...",
            "...o55444433o...",
            "...oooooooooo...",
            "................",
            "................",
            "................",
        ],
        "blood": [
            "..a..........a..",
            ".ab....oo....ba.",
            ".ab..oo55oo..ba.",
            "..abo554443oba..",
            "...ao544443oa...",
            "....obbbbbbo....",
            "....okGkkGko....",
            "....o544443o....",
            "....o54kk43o....",
            "....o544443o....",
            "...obbbbbbbbo...",
            "...o55444433o...",
            "...oooooooooo...",
            "................",
            "................",
            "................",
        ],
        "ender": [
            "................",
            ".......oo.......",
            "......o3bo......",
            ".....o3322o.....",
            "....o332222o....",
            "...o33222221o...",
            "...o3baaaaa1o...",
            "...o3adddda1o...",
            "...o3aMddMa1o...",
            "...o3abbbba1o...",
            "...o3a2222a1o...",
            "....o3a22a1o....",
            ".....o3221o.....",
            "......oooo......",
            "................",
            "................",
        ],
    },
    "chestplate": {
        "holy": [
            "................",
            "..oooo....oooo..",
            ".o5bbo....obb4o.",
            ".o55bboooobb43o.",
            ".obb5544445bb3o.",
            ".oo.o44GG44o.oo.",
            "....o4GccG3o....",
            "....o4GccG3o....",
            "....o44GG43o....",
            "....obbbbbbo....",
            "....o544443o....",
            "....o544443o....",
            "....obbbbbbo....",
            "....oooooooo....",
            "................",
            "................",
        ],
        "ender": [
            "................",
            "............v...",
            "..ooo......ovvo.",
            ".o3bao....oabb1o",
            ".o322aooooa2221o",
            ".oo22aAddAa221oo",
            "...o32aGGa21o...",
            "...o322GG221o...",
            "...o33333321o...",
            "...o22222211o...",
            "...o333v3321o...",
            "...o22222211o...",
            "...oaaaaaaaao...",
            "...oooooooooo...",
            "................",
            "................",
        ],
    },
    "leggings": {
        "holy": [
            "................",
            "...oooooooooo...",
            "...obbbGGbbbo...",
            "...o55544443o...",
            "...obbboobbbo...",
            "...o543oo543o...",
            "...o543oo543o...",
            "...obGbo obGbo..",
            "...o543oo543o...",
            "...o543oo543o...",
            "...o543oo543o...",
            "...obbbo.obbbo..",
            "...oooo..oooo...",
            "................",
            "................",
            "................",
        ],
        "ender": [
            "................",
            "...oooooooooo...",
            "...occcccccco...",
            "...o22222222o...",
            "...o322oo223o...",
            "...o32o..o23o...",
            "...o32o..o23o...",
            "...oc2o..o2co...",
            "...o32o..o23o...",
            "...o32o..o23o...",
            "...o32o..o23o...",
            "...occo..occo...",
            "...oooo..oooo...",
            "................",
            "................",
            "................",
        ],
    },
    "boots": {
        "holy": [
            "................",
            "................",
            "................",
            "................",
            "..oooo....oooo..",
            "..obbo....obbo..",
            "..o54o....o54o..",
            "..o5Go....oG4o..",
            "..o54o....o54o..",
            ".o554o...o5543o.",
            "o55443o..o55443o",
            "obbbbbo..obbbbbo",
            "ooooooo..ooooooo",
            "................",
            "................",
            "................",
        ],
        "ender": [
            "................",
            "................",
            "................",
            "................",
            "..oooo....oooo..",
            "..occo....occo..",
            "..o32o....o32o..",
            "..oc2o....o2co..",
            "..o32o....o32o..",
            ".o322o....o322o.",
            "o3222o...o3222o.",
            "occcco..occcco..",
            "oooooo..oooooo..",
            "................",
            "................",
            "................",
        ],
    },
}

ICON_LEGEND = {
    "holy": {"o": ("silver", 0), "1": ("silver", 2), "2": ("silver", 3), "3": ("silver", 4), "4": ("silver", 5),
             "5": ("silver", 7), "a": ("gold", 4), "b": ("gold", 4), "c": ("gold", 6), "G": ("sun", 2),
             "k": ("visor", 0)},
    "ender": {"o": ("night", 0), "1": ("night", 2), "2": ("night", 4), "3": ("night", 6), "4": ("night", 7),
              "a": ("amethyst", 3), "b": ("amethyst", 5), "c": ("amethyst", 4), "A": ("amethyst", 5),
              "d": ("night", 1), "G": ("pearl", 3), "M": ("magenta", 3), "v": ("violet", 3), "k": ("night", 1)},
    "blood": {"o": ("iron", 0), "1": ("crimson", 2), "2": ("crimson", 3), "3": ("crimson", 4), "4": ("crimson", 5),
              "5": ("crimson", 7), "a": ("gold", 4), "b": ("iron", 3), "c": ("gold", 6), "G": ("ember", 3), "k": ("iron", 0)},
    "evocation": {"o": ("evo_steel", 0), "1": ("evo_steel", 2), "2": ("evo_steel", 3), "3": ("evo_steel", 4),
                  "4": ("evo_steel", 5), "5": ("evo_steel", 7), "a": ("gold", 4), "b": ("gold", 4), "c": ("gold", 6),
                  "G": ("emerald", 3), "k": ("iron", 0)},
    "nature": {"o": ("nat_steel", 0), "1": ("nat_steel", 2), "2": ("nat_steel", 3), "3": ("nat_steel", 4),
               "4": ("nat_steel", 5), "5": ("nat_steel", 7), "a": ("moss", 3), "b": ("moss", 3), "c": ("moss", 5),
               "G": ("moss", 6), "k": ("iron", 0)},
    "eldritch": {"o": ("sculk", 0), "1": ("sculk", 2), "2": ("sculk", 3), "3": ("sculk", 4), "4": ("sculk", 5),
                 "5": ("sculk", 7), "a": ("sculk", 6), "b": ("sculk", 6), "c": ("sculk", 7), "G": ("cyan", 3), "k": ("sculk", 0)},
}


def icon(piece, school):
    art = ICONS[piece].get(school)
    if art is None:   # schools awaiting their art pass borrow the Holy shapes, without the halo
        art = [row.replace("G", ".") if piece == "helmet" and i < 6 else row for i, row in enumerate(ICONS[piece]["holy"])]
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    p = img.load()
    for y, row in enumerate(art[:16]):
        row = row.replace("о", "c")  # guard against a homoglyph
        row = (row + "." * 16)[:16]
        for x, ch in enumerate(row):
            if ch in ". ":
                continue
            ramp, lvl = ICON_LEGEND[school][ch]
            p[x, y] = RAMPS[ramp][lvl]
    return img


# ----------------------------------------------------------------------------------------------
def write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((json.dumps(obj, indent=2) + "\n").encode("utf-8"))


def save_png(img, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, format="PNG", optimize=False)


def main():
    report = {}
    for school, build in BUILDERS.items():
        bones = build()
        resolve_coplanar(bones)
        used_rows = pack(bones)
        base, glow = paint(bones, school)
        name = f"{school}_dragonsteel_plate"
        write_json(ASSETS / "geo" / f"{name}.geo.json", geo_json(bones, f"geometry.dragonsteel_schools.{name}"))
        save_png(base, ASSETS / "textures/models/armor" / f"{name}.png")
        save_png(glow, ASSETS / "textures/models/armor" / f"{name}_glowmask.png")
        for piece in ("helmet", "chestplate", "leggings", "boots"):
            save_png(icon(piece, school), ASSETS / "textures/item" / f"{school}_dragonsteel_{piece}.png")
        counts = {b.name: len(b.cubes) for b in bones.values() if b.cubes}
        issues = coplanar_report(bones)
        glow_px = sum(1 for px in glow.getdata() if px[3])
        report[school] = {"cubes": sum(counts.values()), "per_bone": counts, "atlas_rows_used": used_rows,
                          "glow_pixels": glow_px, "coplanar_issues": issues}
        print(f"{school}: {sum(counts.values())} cubes, atlas rows used {used_rows}/{TEX}, glow px {glow_px}")
        for k, v in counts.items():
            print(f"   {k:30s} {v}")
        print(f"   coplanar with the player's own skin/overlay planes (armour draws last, LEQUAL): {len(issues)}")
    return report


if __name__ == "__main__":
    main()
