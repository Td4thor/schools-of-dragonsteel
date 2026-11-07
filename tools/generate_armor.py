#!/usr/bin/env python
"""Generate the Dragonsteel Schools 'mage plate' armour art.

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
    # Holy: polished white-silver and warm gold
    "silver": ["#3a3d4b", "#575b6c", "#7b8195", "#a2a8ba", "#c4c9d6", "#dfe3eb", "#f3f5f9", "#ffffff"],
    "gold":   ["#4a2a08", "#74450f", "#a06a17", "#cc9324", "#e8b53a", "#f7d45a", "#ffeb94", "#fff9d6"],
    "sun":    ["#c98a1c", "#f0b93a", "#ffd95a", "#ffe98c", "#fff4bf", "#fffbe8"],   # glowing gold
    "visor":  ["#1c1726", "#2e2638"],
    # Ender: obsidian / void plate, deep purple, purpur + end stone accents, violet glow
    "obsid":  ["#060409", "#0d0915", "#150f21", "#1e162e", "#291f3e", "#372a51", "#4a3a6a", "#655290"],
    "void":   ["#170b26", "#24123b", "#341a54", "#46236f", "#5b2e8c", "#7340a8", "#9160c6", "#b48ae0"],
    "purpur": ["#4a3150", "#664769", "#86618a", "#a57ca7", "#c19cc3", "#dbbedb", "#efdfee"],
    "endst":  ["#6c6a43", "#97955d", "#c1bf81", "#dbdb9f", "#ecedc0", "#fafae0"],
    "violet": ["#6a22c9", "#8c3cf0", "#ab63ff", "#c88dff", "#e2bdff", "#f6e8ff"],   # glowing violet
    "star":   ["#5a4880", "#7e69ad", "#b3a3dc"],
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
def plate(f, ramp, base, noise=0.07, streak=True, speckle=None):
    w, h, k = f.w, f.h, f.kind
    for y in range(h):
        for x in range(w):
            lvl = base
            if k in ("front", "back", "left", "right"):
                if h >= 4:
                    t = y / (h - 1)
                    if t < 0.28: lvl += 1
                    elif t > 0.78: lvl -= 1
            elif k == "top":
                lvl += 1
            elif k == "bottom":
                lvl -= 2
            f.set(x, y, ramp, lvl)
    # bevelled plate edges: lit top/left rim, shadowed bottom/right rim
    if k in ("front", "back", "left", "right"):
        if h >= 2:
            for x in range(w):
                f.shift(x, 0, +1)
                f.shift(x, h - 1, -1 if h < 3 else -2)
        if w >= 3 and h >= 3:
            for y in range(1, h - 1):
                f.shift(0, y, +1)
                f.shift(w - 1, y, -1)
    elif k == "top" and w >= 3 and h >= 3:
        for x in range(w):
            f.shift(x, h - 1, +1)       # front lip catches the light
        for y in range(h):
            f.shift(0, y, -1 if y else 0)
            f.shift(w - 1, y, -1 if y else 0)
    # hand-placed looking wear: sparse +-1 texels (seeded per cube face)
    rng = f.rng
    if w >= 3 and h >= 3:
        for y in range(1, h - 1):
            for x in range(1, w - 1):
                r = rng.random()
                if r < noise * 0.5: f.shift(x, y, -1)
                elif r < noise: f.shift(x, y, +1)
    # polished diagonal streak
    if streak and w >= 4 and h >= 4 and k != "bottom":
        off = rng.randrange(0, max(1, w // 2))
        for y in range(h):
            x = off + (y * 2) // 3
            if 0 < x < w - 1 and 0 < y < h - 1:
                f.shift(x, y, +1)
    if speckle:
        sramp, prob = speckle
        for y in range(1, h - 1):
            for x in range(1, w - 1):
                r = rng.random()
                if r < prob * 0.12: f.set(x, y, sramp, 2, glow=(r < prob * 0.03))
                elif r < prob * 0.45: f.set(x, y, sramp, 1)
                elif r < prob: f.set(x, y, sramp, 0)


MATERIALS = {
    "silver": lambda f: plate(f, "silver", 5),
    "silver_dim": lambda f: plate(f, "silver", 4),
    "gold": lambda f: plate(f, "gold", 4, streak=False),
    "gold_hi": lambda f: plate(f, "gold", 5, streak=False),
    "sun": lambda f: [f.set(x, y, "sun", 3 if f.kind != "bottom" else 1, True) for y in range(f.h) for x in range(f.w)],
    "obsid": lambda f: plate(f, "obsid", 3, noise=0.05, streak=False, speckle=("star", 0.10)),
    "void": lambda f: plate(f, "void", 3, noise=0.06, streak=False, speckle=("star", 0.04)),
    "purpur": lambda f: plate(f, "purpur", 3, noise=0.05, streak=False),
    "endst": lambda f: plate(f, "endst", 3, noise=0.04, streak=False),
    "violet": lambda f: [f.set(x, y, "violet", 3 if f.kind != "bottom" else 1, True) for y in range(f.h) for x in range(f.w)],
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


SUNBURST_9x7 = [
    "r...a...r",
    ".r..a..r.",
    "..r.....r",
    "aaa...aaa",
    "..r...r..",
    ".r..a..r.",
    "r...a...r",
]
WINGS_9x7 = [
    "hgg.c.ggh",
    "shgg.ggh s",
    ".shg.ghs.",
    "..sh.hs..",
    "...s.s...",
    ".........",
    ".........",
]


def holy_model():
    bones = skeleton()
    H, B, T = bones["armorHead"].cubes, bones["armorBody"].cubes, bones["armorLeggingTorsoLayer"].cubes
    RA, RL, RB, RX = (bones["armorRightArm"].cubes, bones["armorRightLeg"].cubes,
                      bones["armorRightBoot"].cubes, bones["armorTorsoExtensionRightLeg"].cubes)
    LA = bones["armorLeftArm"].cubes

    # ---- helm (great helm with visor, crest comb, bevor/gorget and a sunburst halo) ----
    H.append(Cube("helm", (-5, 5), (24, 33), (-5, 5), "silver", {
        "sides": [hline(1, ramp="gold", lvl=4), hline(2, ramp="gold", lvl=2), rivets(4, step=3, start=1)],
        "right": [stamp(["kk", "..", "kk", "..", "kk"], {"k": ("visor", 0)}, anchor="topleft", dx=6, dy=4)],
        "left": [stamp(["kk", "..", "kk", "..", "kk"], {"k": ("visor", 0)}, anchor="topleft", dx=2, dy=4)],
        "back": [vline(4, 2, -1, "gold", 3), vline(5, 2, -1, "gold", 2)],
        "top": [vline(4, 0, -1, "gold", 5), vline(5, 0, -1, "gold", 4), rivets(1, step=7, start=1), rivets(-2, step=7, start=1)],
    }))
    H.append(Cube("visor", (-4, 4), (25, 31), (-5.75, -4.75), "silver", {
        "front": [
            hline(1, 0, -1, "silver", 7),
            stamp(["sss..sss", "ggg..ggg", "ddd..ddd"],
                  {"s": ("silver", 3), "g": ("sun", 4, True), "d": ("visor", 1)}, anchor="topleft", dy=1),
            stamp(["k......k", ".k....k."], {"k": ("visor", 0)}, anchor="topleft", dy=4),
            band("left", "gold", 4), band("right", "gold", 3), band("bottom", "gold", 3),
        ],
        "top": [hline(0, ramp="gold", lvl=6)], "right": [band("left", "gold", 4)], "left": [band("left", "gold", 4)],
    }))
    H.append(Cube("keel", (-0.5, 0.5), (24.5, 32.5), (-6.25, -5.25), "gold_hi", {
        "front": [vline(0, 0, -1, "gold", 6), stamp(["s"], {"s": SUN(4)}, anchor="topleft", dy=3)],
    }))
    H.append(Cube("bevor", (-5.5, 5.5), (22, 25), (-5.5, 5.5), "silver", {
        "sides": [band("top", "gold", 5), band("bottom", "gold", 3), rivets(1, step=2, start=1, lvl=6)],
        "front": [stamp(["s"], {"s": SUN(5)}, anchor="topleft", dx=5, dy=1)],
        "top": [band("top", "gold", 5), band("bottom", "gold", 5), band("left", "gold", 5), band("right", "gold", 5)],
    }))
    H.append(Cube("comb", (-0.5, 0.5), (33, 35), (-4, 4), "gold", {
        "sides": [hline(0, ramp="gold", lvl=6)], "top": [vline(0, ramp="gold", lvl=6)],
        "right": [rivets(1, step=2, start=1, ramp="gold", lvl=2)], "left": [rivets(1, step=2, start=1, ramp="gold", lvl=2)],
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

    # ---- cuirass ----
    B.append(Cube("cuirass", (-5.25, 5.25), (14.75, 24.25), (-3.25, 3.25), "silver", {
        "sides": [band("top", "gold", 5), band("bottom", "gold", 3), rivets(1, step=3, start=1)],
        "right": [vline(2, 2, -2, "silver", 3)], "left": [vline(3, 2, -2, "silver", 3)],
        "top": [band("top", "gold", 5), band("bottom", "gold", 5)],
    }))
    B.append(Cube("breast", (-4.5, 4.5), (16, 23), (-4, -3), "silver", {
        "front": [stamp(SUNBURST_9x7, {"r": SUN(3), "a": SUN(4)}), band("top", "gold", 5),
                  band("left", "gold", 4), band("right", "gold", 3)],
        "sides": [band("top", "gold", 5)], "top": [hline(0, ramp="gold", lvl=6)],
    }))
    B.append(Cube("sun_medallion", (-1.5, 1.5), (18, 21), (-4.75, -3.75), "sun", {
        "front": [stamp(["bcb", "cwc", "bcb"], {"b": SUN(2), "c": SUN(4), "w": SUN(5)})],
    }))
    B.append(Cube("plackart", (-4.5, 4.5), (12, 16), (-3, 3), "silver", {
        "sides": [hline(1, ramp="silver", lvl=2), hline(2, ramp="silver", lvl=6), band("bottom", "gold", 4)],
    }))
    B.append(Cube("backplate", (-4.5, 4.5), (16, 23), (3, 4), "silver", {
        "back": [stamp(["g...s...g", "gg.sws.gg", ".gg.s.gg.", "hhgg.gghh", ".hhg.ghh.", "..hh.hh..", "...h.h..."],
                       {"g": G(5), "h": G(3), "s": SUN(3), "w": SUN(5)}),
                 band("top", "gold", 5)],
        "sides": [band("top", "gold", 5)],
    }))
    # ---- belt + faulds (LEGS slot, follows the body) ----
    T.append(Cube("fauld", (-5.5, 5.5), (10.5, 13.5), (-3.5, 3.5), "silver", {
        "sides": [band("top", "gold", 5), band("bottom", "gold", 3), rivets(0, step=2, start=1, lvl=7)],
    }))
    T.append(Cube("buckle", (-1.25, 1.25), (10.75, 13.25), (-4.5, -3), "gold_hi", {
        "front": [stamp(["cw", "wc"], {"c": SUN(3), "w": SUN(5)})],
    }))
    # ---- tassets (CHEST slot, follow the legs) ----
    RX.append(Cube("tasset_hi", (-4.75, 0.75), (9.25, 12.75), (-4.25, -2.75), "silver", {
        "front": [band("bottom", "gold", 4), rivets(0, step=4, start=0, lvl=7), vline(2, 1, -2, "silver", 7)],
        "sides": [band("bottom", "gold", 3)],
    }))
    RX.append(Cube("tasset_lo", (-4.25, 0.25), (6.5, 10), (-3.75, -2.25), "silver", {
        "front": [band("bottom", "gold", 5, glow=False), stamp(["s"], {"s": SUN(4)}, anchor="topleft", dx=1, dy=1),
                  stamp(["s"], {"s": SUN(4)}, anchor="topleft", dx=2, dy=1)],
        "sides": [band("bottom", "gold", 3)],
    }))
    RX.append(Cube("tasset_side", (-5.75, -4.25), (7.75, 12.25), (-2.25, 2.25), "silver", {
        "right": [band("bottom", "gold", 4), band("top", "gold", 5), rivets(1, step=3, start=1, lvl=7)],
        "sides": [band("bottom", "gold", 3)],
    }))
    # ---- arms: big layered pauldrons, rerebrace, couter, vambrace ----
    RA.append(Cube("pauldron_cap", (-9.5, -3.5), (22.5, 25.5), (-3.5, 3.5), "silver", {
        "sides": [band("bottom", "gold", 4)],
        "right": [stamp(["s"], {"s": SUN(5)}, anchor="topleft", dx=3, dy=1), rivets(1, step=6, start=0, lvl=7)],
        "top": [vline(1, 0, -1, "gold", 5), vline(2, 0, -1, "silver", 7), hline(0, ramp="gold", lvl=4), hline(-1, ramp="gold", lvl=5)],
    }))
    RA.append(Cube("pauldron_lame1", (-10.25, -4.75), (20.25, 22.75), (-3.75, 3.75), "silver", {
        "sides": [band("bottom", "gold", 4)], "top": [band("bottom", "gold", 5), vline(0, 0, -1, "gold", 5)],
    }))
    RA.append(Cube("pauldron_lame2", (-10.75, -5.25), (18.25, 20.75), (-4.25, 4.25), "silver", {
        "sides": [band("bottom", "sun", 2, glow=True)], "top": [vline(0, 0, -1, "gold", 5)],
        "right": [stamp(["g.g.g"], {"g": G(6)}, anchor="topleft", dx=1, dy=0)],
    }))
    RA.append(Cube("rerebrace", (-8.5, -3.5), (15.5, 20.5), (-2.5, 2.5), "silver_dim", {
        "sides": [hline(2, ramp="silver", lvl=2), hline(3, ramp="silver", lvl=6)],
    }))
    RA.append(Cube("couter", (-9.25, -8.25), (14.75, 17.75), (-1.5, 1.5), "gold", {
        "right": [stamp([".c.", "cwc", ".c."], {"c": G(6), "w": SUN(4)})],
    }))
    RA.append(Cube("vambrace", (-8.75, -3.25), (11.75, 16.25), (-2.75, 2.75), "silver", {
        "sides": [band("top", "gold", 5), band("bottom", "gold", 3)],
        "right": [stamp(["s.s", ".s."], {"s": SUN(3)}, anchor="topleft", dx=1, dy=1)],
        "front": [vline(2, 1, -2, "silver", 7)],
    }))
    # ---- legs: cuisse + poleyn + knee fan ----
    RL.append(Cube("cuisse", (-4.75, 0.75), (5.75, 12.25), (-2.75, 2.75), "silver", {
        "front": [vline(2, 0, -1, "silver", 7), vline(3, 0, -1, "silver", 3)],
        "sides": [band("bottom", "gold", 3), rivets(1, step=4, start=0, lvl=6)],
    }))
    RL.append(Cube("poleyn", (-3.75, -0.25), (4.25, 7.75), (-3.75, -2.25), "gold", {
        "front": [stamp(["gcg", "cwc", "gcg"], {"g": G(6), "c": S(6), "w": SUN(4)})],
    }))
    RL.append(Cube("knee_fan", (-5.5, -4.5), (4.5, 7.5), (-2, 1), "silver", {
        "right": [stamp(["g.g", ".g.", "ggg"], {"g": G(5)})], "sides": [band("bottom", "gold", 3)],
    }))
    # ---- boots: greave, cuff, sabaton, toe cap ----
    RB.append(Cube("greave", (-5, 1), (0.5, 6.5), (-3, 3), "silver", {
        "front": [vline(2, 0, -1, "silver", 7), vline(3, 0, -1, "silver", 4), stamp(["s"], {"s": SUN(4)}, anchor="topleft", dx=2, dy=1)],
        "sides": [rivets(1, step=4, start=1, lvl=6)], "back": [vline(2, 0, -1, "silver", 3)],
    }))
    RB.append(Cube("greave_cuff", (-5.25, 1.25), (5.75, 7.25), (-3.25, 3.25), "gold", {"sides": [hline(0, ramp="gold", lvl=6)]}))
    RB.append(Cube("sabaton", (-4.75, 0.75), (-0.75, 1.75), (-4.25, 2.25), "silver", {
        "top": [hline(1, ramp="silver", lvl=3), hline(3, ramp="silver", lvl=3), hline(5, ramp="silver", lvl=7)],
        "front": [band("bottom", "gold", 3)], "sides": [band("bottom", "gold", 3)],
    }))
    RB.append(Cube("toecap", (-4.25, 0.25), (-0.25, 1.25), (-5.25, -3.75), "gold_hi", {}))

    mirror_limbs(bones)
    return bones


# ----------------------------------------------------------------------------------------------
# ENDER: lean End-assassin plate (obsidian/void black, deep purple, purpur + end stone, violet glow)
# ----------------------------------------------------------------------------------------------
O = lambda l, glow=False: ("obsid", l, glow)
P = lambda l, glow=False: ("purpur", l, glow)
V = lambda l: ("violet", l, True)
VD = lambda l, glow=False: ("void", l, glow)


def ender_model():
    bones = skeleton()
    H, B, T = bones["armorHead"].cubes, bones["armorBody"].cubes, bones["armorLeggingTorsoLayer"].cubes
    RA, RL, RB, RX = (bones["armorRightArm"].cubes, bones["armorRightLeg"].cubes,
                      bones["armorRightBoot"].cubes, bones["armorTorsoExtensionRightLeg"].cubes)
    LA = bones["armorLeftArm"].cubes

    # ---- cowl helm: closed mask, plated hood, peak, spine, neck guard ----
    H.append(Cube("shell", (-4.625, 4.625), (23.375, 32.625), (-4.625, 4.625), "obsid", {
        "sides": [band("bottom", "purpur", 3)],
    }))
    H.append(Cube("hood", (-5.25, 5.25), (25.25, 33.75), (-4.25, 5.25), "void", {
        "front": [band("left", "purpur", 4), band("right", "purpur", 3), band("top", "purpur", 4)],
        "right": [seams(2, "obsid", 1), runes("hoodR", y=3), band("left", "purpur", 4)],
        "left": [seams(2, "obsid", 1), runes("hoodL", y=3), band("right", "purpur", 4)],
        "back": [seams(2, "obsid", 1), vline(4, 0, -1, "violet", 1), vline(5, 0, -1, "obsid", 1)],
        "top": [hline(-1, ramp="purpur", lvl=4), hline(2, ramp="obsid", lvl=1), hline(5, ramp="obsid", lvl=1)],
    }))
    H.append(Cube("mask", (-3.5, 3.5), (24, 31), (-5.25, -4.25), "obsid", {
        "front": [
            stamp(["ppppppp",
                   ".......",
                   "ddddddd",
                   "vvvvvvv",
                   "p.d.d.p",
                   ".p.d.p.",
                   "..p.p.."],
                  {"p": P(3), "d": O(0), "v": V(3)}),
            band("left", "purpur", 4), band("right", "purpur", 2),
        ],
        "sides": [band("top", "purpur", 4)], "top": [hline(-1, ramp="purpur", lvl=5)],
    }))
    H.append(Cube("peak", (-2.5, 2.5), (32.5, 33.5), (-5.5, -3.5), "purpur", {"front": [hline(0, ramp="purpur", lvl=5)]}))
    H.append(Cube("peak_tip", (-0.5, 0.5), (31.5, 33.5), (-6, -5), "purpur", {"front": [vline(0, ramp="purpur", lvl=5)]}))
    H.append(Cube("spine", (-0.5, 0.5), (33.5, 34.5), (-3.5, 4.5), "purpur", {
        "top": [stamp(["v", ".", ".", "v", ".", ".", "v", "."], {"v": V(3)}, anchor="topleft")],
        "sides": [stamp(["v..v..v."], {"v": V(2)}, anchor="topleft")],
    }))
    H.append(Cube("neck_guard", (-4.5, 4.5), (22.5, 27.5), (3.75, 5.75), "obsid", {
        "back": [seams(2, "void", 1), band("bottom", "purpur", 3)], "sides": [band("bottom", "purpur", 3)],
    }))
    H.append(Cube("chin", (-1.5, 1.5), (22.5, 23.5), (-5, -3), "obsid", {"front": [hline(0, ramp="purpur", lvl=4)]}))

    # ---- lean lamellar cuirass ----
    B.append(Cube("cuirass", (-4.75, 4.75), (13.75, 24.25), (-2.75, 2.75), "obsid", {
        "sides": [seams(2, "void", 1, start=2), band("top", "purpur", 3)],
    }))
    B.append(Cube("chest", (-4.5, 4.5), (18.25, 23.25), (-3.5, -2.5), "void", {
        "front": [stamp(["..pv.....", "ooopv....", "ooo.pv...", "oooo.pv..", "ooooo.pv."],
                        {"p": P(4), "v": V(2), "o": O(3)}, anchor="topleft"),
                  band("top", "purpur", 4)],
        "sides": [band("top", "purpur", 4)],
    }))
    B.append(Cube("lame_a", (-4.25, 4.25), (16.25, 18.75), (-3.25, -1.75), "void", {
        "front": [hline(-1, ramp="violet", lvl=1, glow=True), hline(0, ramp="void", lvl=6)],
    }))
    B.append(Cube("lame_b", (-4, 4), (14, 17), (-3, -2), "obsid", {
        "front": [band("bottom", "purpur", 3), hline(-2, ramp="violet", lvl=0, glow=True)],
    }))
    B.append(Cube("backplate", (-3.5, 3.5), (15, 23), (2.5, 3.5), "obsid", {
        "back": [seams(2, "void", 1), vline(3, 0, -1, "violet", 1, glow=True)],
    }))
    T.append(Cube("belt", (-5, 5), (11.5, 13.5), (-3, 3), "void", {
        "sides": [rivets(0, ramp="purpur", lvl=5, step=3, start=1), band("bottom", "purpur", 2)],
    }))
    T.append(Cube("gem_buckle", (-1, 1), (11.25, 13.25), (-3.5, -2.5), "violet", {
        "front": [stamp(["bc", "cb"], {"b": V(4), "c": V(2)})],
    }))
    RX.append(Cube("tasset_hi", (-5.25, -4.25), (9, 12), (-2, 2), "obsid", {
        "right": [band("bottom", "purpur", 3), stamp(["v"], {"v": V(2)}, anchor="topleft", dx=1, dy=1)],
    }))
    RX.append(Cube("tasset_lo", (-5, -4), (6.5, 9.5), (-1.5, 1.5), "void", {
        "right": [band("bottom", "endst", 3)],
    }))
    # ---- arms: asymmetric (small right cap, layered left pauldron with an end-stone fin) ----
    RA.append(Cube("cap", (-8.75, -3.75), (22.5, 24.5), (-3, 3), "obsid", {
        "sides": [band("bottom", "purpur", 3)], "top": [hline(-1, ramp="purpur", lvl=4)],
    }))
    RA.append(Cube("upper", (-8.5, -3.5), (16.5, 22.5), (-2.5, 2.5), "obsid", {"sides": [seams(2, "void", 1)]}))
    RA.append(Cube("bracer", (-8.75, -3.25), (11.75, 16.25), (-2.75, 2.75), "void", {
        "sides": [band("top", "purpur", 4), band("bottom", "purpur", 2)],
        "right": [vline(2, 1, 2, "violet", 2, glow=True)], "front": [vline(2, 1, 2, "violet", 1, glow=True)],
    }))
    RA.append(Cube("fin", (-9.75, -8.75), (12.5, 15.5), (-1, 1), "endst", {"right": [vline(0, 0, -1, "endst", 5)]}))
    RA.append(Cube("elbow", (-9.25, -8.25), (16, 18), (-1, 1), "purpur", {}))
    LA.append(Cube("pauldron_cap", (3.75, 8.75), (22.5, 25.5), (-3.5, 3.5), "obsid", {
        "sides": [band("bottom", "purpur", 3)], "left": [runes("pauldL", y=0)],
        "top": [vline(-2, 0, -1, "purpur", 4)],
    }))
    LA.append(Cube("pauldron_lame1", (4.25, 9.75), (20.25, 22.75), (-3.75, 3.75), "void", {
        "sides": [band("bottom", "violet", 1, glow=True)],
    }))
    LA.append(Cube("pauldron_lame2", (5.75, 9.25), (18.25, 20.75), (-3.25, 3.25), "obsid", {
        "sides": [band("bottom", "purpur", 3)],
    }))
    LA.append(Cube("shard", (5.5, 6.5), (25, 27), (-1.5, 0.5), "endst", {
        "sides": [hline(0, ramp="violet", lvl=3, glow=True)], "top": [hline(0, ramp="violet", lvl=4, glow=True)],
    }))
    # ---- legs and boots ----
    RL.append(Cube("cuisse", (-4.5, 0.5), (5.5, 12.5), (-2.5, 2.5), "obsid", {
        "sides": [seams(3, "void", 1, start=2)], "right": [vline(1, 1, 4, "violet", 1, glow=True)],
    }))
    RL.append(Cube("knee", (-3.5, -0.5), (4.5, 7.5), (-3.25, -2.25), "void", {
        "front": [stamp(["p.p", ".v.", "p.p"], {"p": P(4), "v": V(3)})],
    }))
    RL.append(Cube("knee_point", (-2.5, -1.5), (3.5, 4.5), (-3, -2), "endst", {}))
    RB.append(Cube("greave", (-4.75, 0.75), (0.25, 6.75), (-2.75, 2.75), "obsid", {
        "sides": [band("top", "purpur", 3)], "right": [runes("greaveR", y=2)],
    }))
    RB.append(Cube("shin", (-2.5, -1.5), (1.5, 6.5), (-3.25, -2.25), "void", {
        "front": [vline(0, 1, 3, "violet", 2, glow=True)],
    }))
    RB.append(Cube("foot", (-4.5, 0.5), (-0.5, 1.5), (-3.5, 2.5), "obsid", {
        "top": [hline(2, ramp="void", lvl=1), hline(4, ramp="void", lvl=1)], "front": [hline(0, ramp="purpur", lvl=3)],
    }))
    RB.append(Cube("toe", (-3, -1), (-0.25, 0.75), (-4.5, -3.5), "endst", {}))

    # left-arm extras that mirror the right forearm (asymmetry lives in the shoulders only)
    for c in list(RA):
        if c.name in ("upper", "bracer", "fin", "elbow"):
            LA.append(c.mirrored(c.name + "_l"))
    for src, dst in (("armorRightLeg", "armorLeftLeg"), ("armorRightBoot", "armorLeftBoot"),
                     ("armorTorsoExtensionRightLeg", "armorTorsoExtensionLeftLeg")):
        for c in bones[src].cubes:
            bones[dst].cubes.append(c.mirrored(c.name + "_l"))
    return bones


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
            "....aabbbbaa....",
            "...a........a...",
            "..a...occo...a..",
            "..a.oo4cc4oo.a..",
            "..ao44455444oa..",
            "...o45555554o...",
            "...obbbbbbbbo...",
            "...o4GGooGG3o...",
            "...o4kkook k3o..",
            "...o45434543o...",
            "...o4k4334k3o...",
            "...obbbbbbbbo...",
            "....oooooooo....",
            "................",
            "................",
            "................",
        ],
        "ender": [
            "................",
            "......occo......",
            "....oo3cc3oo....",
            "...o32344232o...",
            "..o3234cc4323o..",
            "..o32o4444o23o..",
            "..o3o222222o3o..",
            "..o3o2GGGG2o3o..",
            "..o3o221122o3o..",
            "..o32o2112o23o..",
            "..o322o11o2223o.",
            "...o222oo2222o..",
            "....oo2222ooo...",
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
            "................",
            "..ooo......oooo.",
            ".o33oo....occ3o.",
            ".o2222oooo2c32o.",
            ".oo222cG2222ooo.",
            "....o22cG22o....",
            "....o222cG2o....",
            "....oGGGGGGo....",
            "....o333333o....",
            "....oGGGGGGo....",
            "....o222222o....",
            "....occccccо....",
            "....oooooooo....",
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
            "...occcGGccco...",
            "...o22222222o...",
            "...o322oo223o...",
            "...o32o..o23o...",
            "...o32o..o23o...",
            "...oG2o..o2Go...",
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
            "..oG2o....o2Go..",
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
             "5": ("silver", 7), "a": ("gold", 4), "b": ("gold", 4), "c": ("gold", 6), "G": ("sun", 4),
             "k": ("visor", 0)},
    "ender": {"o": ("obsid", 0), "1": ("obsid", 2), "2": ("obsid", 4), "3": ("void", 5), "4": ("void", 6),
              "5": ("void", 7), "a": ("purpur", 3), "b": ("purpur", 3), "c": ("purpur", 4), "G": ("violet", 3),
              "k": ("obsid", 1)},
}


def icon(piece, school):
    art = ICONS[piece][school]
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
    for school, build in (("holy", holy_model), ("ender", ender_model)):
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
