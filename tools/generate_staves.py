#!/usr/bin/env python
"""Generate the six school Dragon Priest staves: 3D item models and their texture sheets.

    python tools/generate_staves.py

Each staff is a vanilla JSON item model (no client code), built from boxes at Iron's Spells staff scale and
display, with one head per school that echoes its armour:

    holy       Gilded    a sunburst: a thick rayed gold ring round a glowing star core
    ender      Umbral    an uneven obsidian crescent cradling a floating crystal over an Eye of Ender
    blood      Sanguine  a blood jewel under an iron spike, flanked by bat wings, on a gold skull
    evocation  Emerald   a great emerald in a basket of four fangs, inside a tilted sigil ring, with a sash
    nature     Verdant   antlers rising from moss round a red rose, with leaves and glowing berries
    eldritch   Abyssal   a lidded great eye between two tendril horns, with tendrils hanging down the shaft

Authoring space is centred on the shaft (x and z are offsets from 8), one texel per 0.5 model units. Every face
gets its own painted rectangle in a packed sheet; identical faces share one. Glowing parts use Forge's
`forge_data` block/sky light (full-bright quads), so gems glow in hand without a renderer.

Vanilla limits honoured and checked: coordinates within -16..32, one rotation axis per element, angles of
0, 22.5 or 45 degrees. `check()` also fails on any element that touches nothing (unless marked floating).
"""
import json
import math
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_textures import R, hexes, ramp  # noqa: E402  (shared school palettes)

ROOT = Path(__file__).resolve().parents[1]
MOD = "dragonsteel_schools"
A = ROOT / "src/main/resources/assets" / MOD
TEXEL = 2  # texels per model unit

STAVES = {
    "holy": "gilded_dragon_priest_staff", "ender": "umbral_dragon_priest_staff",
    "blood": "sanguine_dragon_priest_staff", "evocation": "emerald_dragon_priest_staff",
    "nature": "verdant_dragon_priest_staff", "eldritch": "abyssal_dragon_priest_staff",
}

# Iron's Spells staff display (graybeard_staff.json), so the staves sit in the hand like Iron's own.
STAFF_DISPLAY = {
    "thirdperson_righthand": {"translation": [0, 3, 1.25]},
    "thirdperson_lefthand": {"translation": [0, 3, 1.25]},
    "firstperson_righthand": {"translation": [1.5, 0, -2.75]},
    "firstperson_lefthand": {"translation": [1.5, 0, -2.75]},
    "ground": {"translation": [0, 9.5, 0], "scale": [0.5, 0.5, 0.5]},
    "gui": {"rotation": [-13, 128, 65], "translation": [0.75, 0.5, 0], "scale": [0.7, 0.7, 0.7]},   # Iron's uses 0.75
    "fixed": {"translation": [0, 1.75, -0.75], "scale": [0.55, 0.55, 0.55]},
}

R["ember"] = hexes("#7a1408", "#b3260c", "#e04a12", "#ff7a24", "#ffab52", "#ffd894")


def col(name, t):
    return ramp(name, max(0.0, min(1.0, t)))


# ---------------------------------------------------------------------------------------------
# Painters: (face, w, h) -> RGBA image of w x h texels. Side faces have v = 0 at the top.
# ---------------------------------------------------------------------------------------------
def bevel(face, u, v, w, h):
    """Plates lit from above: bright top rim, dark foot row, a lit near edge and a shaded far edge."""
    if face == "up":
        return 0.12
    if face == "down":
        return -0.2
    t = 0.0
    if h >= 3:
        t += 0.14 if v == 0 else -0.14 if v == h - 1 else 0.0
    if w >= 3:
        t += 0.07 if u == 0 else -0.1 if u == w - 1 else 0.0
    return t


def paint(w, h, fn):
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = img.load()
    for v in range(h):
        for u in range(w):
            c = fn(u, v)
            if c is not None:
                px[u, v] = c
    return img


def plain(name, base):
    def painter(face, w, h):
        return paint(w, h, lambda u, v: col(name, base + bevel(face, u, v, w, h)))
    return painter


def shaft(name, base, detail):
    """A long 3-texel column: lit middle, mid near side, dark far side. detail(u, v) may override a texel."""
    cols = (0.0, 0.16, -0.16)

    def painter(face, w, h):
        if face in ("up", "down"):
            return plain(name, base)(face, w, h)
        return paint(w, h, lambda u, v: detail(u, v) or col(name, base + cols[u % 3]))
    return painter


def wrap(name, base, cord):
    """Grip wrap: level windings with a shadow line between them and a cord at each end."""
    def painter(face, w, h):
        if face in ("up", "down"):
            return plain(name, base)(face, w, h)

        def fn(u, v):
            if v in (0, h - 1):
                return cord
            edge = 0.06 if u == 0 else -0.1 if u == w - 1 else 0.0
            return col(name, base + edge + (-0.2 if v % 3 == 2 else 0.1 if v % 3 == 0 else 0.0))
        return paint(w, h, fn)
    return painter


def gem(name, lo=0.45):
    """Faceted gem: a bright upper-left facet, a dark lower-right one and a single glint."""
    def painter(face, w, h):
        def fn(u, v):
            if face == "up":
                return col(name, 0.95)
            if face == "down":
                return col(name, lo - 0.2)
            t = lo + 0.5 * (1.0 - (u / max(1, w - 1) + v / max(1, h - 1)) / 2.0)
            if u == 0 and v == 0 and w * h > 2:
                return col(name, 1.0)
            return col(name, t)
        return paint(w, h, fn)
    return painter


SKULL_KEY = {"h": ("gold", 0.95), "g": ("gold", 0.7), "d": ("gold", 0.45), "s": ("gold", 0.25), "X": ("crimson", 0.0)}


def skull(face, w, h):
    """Blood's socket: a gold cranium with eye sockets and a nose on the front and back."""
    if face in ("north", "south") and (w, h) == (6, 5):
        rows = ["hggggd", "gggggd", "gXggXd", "gXggXd", "ggXXgd"]
        return paint(w, h, lambda u, v: col(*SKULL_KEY[rows[v][u]]))
    return plain("gold", 0.62)(face, w, h)


def jaw(face, w, h):
    """The jaw under it: a row of teeth over a dark chin."""
    if face in ("north", "south") and h == 2:
        return paint(w, h, lambda u, v: col("gold", 0.9 if u % 2 == 0 else 0.25) if v == 0 else col("gold", 0.45))
    return plain("gold", 0.5)(face, w, h)


def ender_eye(face, w, h):
    """An Eye of Ender: teal with a dark slit of a pupil on each side."""
    base = gem("teal", 0.5)(face, w, h)
    if face not in ("up", "down") and w >= 3:
        px = base.load()
        for v in range(h):
            px[w // 2, v] = (4, 26, 22, 255)
    return base


def eye(face, w, h):
    """Eldritch's great eye: pale corners, a ringed iris round a centred black pupil (no lid line, no slit)."""
    if face in ("north", "south") and (w, h) == (9, 5):
        key = {"p": col("bone", 0.85), "k": col("cyan", 0.0), "i": col("cyan", 0.55), "b": col("cyan", 0.95),
               "X": (2, 6, 8, 255)}
        rows = ["ppkiiikpp", "pkiXXXikp", "kibXXXbik", "pkiXXXikp", "ppkiiikpp"]
        return paint(w, h, lambda u, v: key[rows[v][u]])
    return plain("sculk", 0.55)(face, w, h)


def socket_eyes(face, w, h):
    """Eldritch's socket: deepslate with an uneven cluster of small eyes on the front and back."""
    base = plain("deepslate", 0.55)(face, w, h)
    if face in ("north", "south") and w >= 6 and h >= 3:
        px = base.load()
        for (u, v), t in {(1, 1): 0.9, (4, 0): 0.6, (3, 2): 0.75}.items():
            px[u, v] = col("cyan", t)
    return base


def rose(face, w, h):
    if face == "up":   # petals spiralling round a dark heart
        def fn(u, v):
            d = max(abs(u - w // 2), abs(v - h // 2))
            return col("rose", (0.15, 0.75, 0.5)[min(d, 2)] + (0.12 if (u + v) % 2 == 0 and d else 0.0))
        return paint(w, h, fn)
    if face == "down":
        return plain("leaf", 0.35)(face, w, h)
    return paint(w, h, lambda u, v: col("rose", 0.62 - 0.12 * v + (0.14 if (u + v) % 2 == 0 else 0.0)))


def leaf_blade(face, w, h):
    """A solid leaf: pale midrib, darker rim."""
    def fn(u, v):
        mid = (w - 1) / 2.0
        if abs(u - mid) < 0.6:
            return col("leaf", 0.9)
        return col("leaf", 0.6 - 0.12 * abs(u - mid) + (0.1 if v % 2 == 0 else 0.0))
    return paint(w, h, fn)


def engraved(face, w, h):
    """Evocation's gold: a darker engraved line inside the rim of any face big enough to hold one."""
    def fn(u, v):
        t = 0.66 + bevel(face, u, v, w, h)
        if w >= 5 and h >= 3 and 0 < u < w - 1 and v == h // 2:
            t = 0.34
        return col("gold", t)
    return paint(w, h, fn)


def prong(face, w, h):
    """Ender's crescent: night obsidian with an amethyst line down one edge."""
    def fn(u, v):
        if face not in ("up", "down") and w >= 2 and u == 0:
            return col("violet", 0.2)
        return col("obsid", 0.6 + bevel(face, u, v, w, h))
    return paint(w, h, fn)


def wingbone(face, w, h):
    return paint(w, h, lambda u, v: col("crimson", 0.72 + bevel(face, u, v, w, h)))


def membrane(face, w, h):
    """Bat-wing skin: near-black crimson with faint ribs along its length, so the bones stand off it."""
    return paint(w, h, lambda u, v: col("crimson", 0.14 + (0.1 if u % 2 == 0 else 0.0)))


def moss(face, w, h):
    def fn(u, v):
        return col("moss", 0.5 + (0.18 if (u * 3 + v * 5) % 4 == 0 else 0.0) + (0.12 if face == "up" else 0.0)
                   - (0.15 if face not in ("up", "down") and v == h - 1 else 0.0))
    return paint(w, h, fn)


def holy_shaft(u, v):
    return col("gold", (0.8, 0.95, 0.55)[u % 3] - (0.15 if v % 10 == 5 else 0.0)) if v % 10 in (4, 5) else None


def ender_shaft(u, v):
    if v % 9 == 4:
        return col("purpur", (0.6, 0.8, 0.4)[u % 3])
    return col("violet", 0.35) if (v * 7 + u * 3) % 23 == 0 else None


def blood_shaft(u, v):   # gold filigree winding up the lacquer
    return col("gold", (0.7, 0.9, 0.5)[u % 3]) if (v + u * 2) % 8 == 0 else None


def evocation_shaft(u, v):   # engraved gold panels between gold bands
    if v % 14 in (2, 9):
        return col("gold", (0.5, 0.65, 0.35)[u % 3])
    return col("gold", 0.7) if 3 <= v % 14 <= 8 and u % 3 == 1 else None


def nature_shaft(u, v):   # bark grain with moss in the creases
    if ((v // 3) * 5 + u) % 9 == 0:
        return col("moss", 0.55)
    return col("bark", 0.3) if (v * 5 + u * 11) % 7 == 0 else None


def eldritch_shaft(u, v):   # deepslate ribs and sculk pores
    if v % 8 == 3:
        return col("deepslate", (0.55, 0.75, 0.4)[u % 3])
    return col("cyan", 0.45) if (v * 3 + u * 5) % 17 == 0 else None


MATS = {
    # shared
    "gold": plain("gold", 0.66), "silver": plain("silver", 0.7), "iron": plain("iron", 0.5),
    "sun": plain("sun", 0.7), "sunorb": gem("sun", 0.6),
    # holy
    "holy_shaft": shaft("silver", 0.62, holy_shaft), "holy_grip": wrap("silver", 0.85, col("gold", 0.65)),
    # ender
    "ender_shaft": shaft("obsid", 0.72, ender_shaft), "ender_grip": wrap("void", 0.45, col("void", 0.8)),
    "purpur": plain("purpur", 0.6), "prong": prong, "crystal": gem("violet", 0.1), "endereye": ender_eye,
    # blood
    "blood_shaft": shaft("crimson", 0.58, blood_shaft), "blood_grip": wrap("iron", 0.4, col("crimson", 0.6)),
    "skull": skull, "jaw": jaw, "jewel": gem("crimson", 0.55),
    "wingbone": wingbone, "membrane": membrane,
    # evocation
    "evocation_shaft": shaft("slate", 0.6, evocation_shaft), "evocation_grip": wrap("leather", 0.5, col("leather", 0.15)),
    "engraved": engraved, "emerald": gem("emerald", 0.45), "sash": plain("sash", 0.6), "sash2": plain("sash", 0.35),
    "fangtip": plain("bone", 1.0),
    "steel": plain("slate", 0.6),
    # nature
    "nature_shaft": shaft("bark", 0.55, nature_shaft), "nature_grip": wrap("moss", 0.4, col("leaf", 0.8)),
    "bark": plain("bark", 0.45), "moss": moss, "antler": plain("bone", 0.6), "rose": rose, "leaf": leaf_blade,
    "sepal": plain("leaf", 0.45), "berry": gem("ember", 0.3),
    # eldritch
    "eldritch_shaft": shaft("sculk", 0.62, eldritch_shaft), "eldritch_grip": wrap("sculk", 0.5, col("deepslate", 0.7)),
    "deepslate": plain("deepslate", 0.55), "lid": plain("deepslate", 0.8), "sculk": plain("sculk", 0.62),
    "tendril": plain("sculk", 0.88), "eye": eye, "socket_eyes": socket_eyes,
    "cyantip": gem("cyan", 0.6),
}


# ---------------------------------------------------------------------------------------------
# Modelling
# ---------------------------------------------------------------------------------------------
FACES = ("north", "south", "east", "west", "up", "down")
VALID_ANGLES = (-45.0, -22.5, 0.0, 22.5, 45.0)


class Staff:
    def __init__(self, school):
        self.school = school
        self.elements = []

    def box(self, x0, y0, z0, x1, y1, z1, mat, rot=None, glow=False, glow_faces=(), floats=False, faces=FACES):
        lo = (min(x0, x1), min(y0, y1), min(z0, z1))
        hi = (max(x0, x1), max(y0, y1), max(z0, z1))
        self.elements.append(dict(lo=lo, hi=hi, mat=mat, rot=rot, glow=glow, glow_faces=tuple(glow_faces),
                                  floats=floats, faces=tuple(faces)))

    def bar_z(self, x, y, length, width, zh, angle, mat, **kw):
        """A bar rising from (x, y), turned about z at its foot. Positive angles lean toward -x."""
        self.box(x - width / 2, y, -zh, x + width / 2, y + length, zh, mat, rot=("z", angle, (x, y, 0)), **kw)

    def bar_x(self, z, y, length, width, xh, angle, mat, **kw):
        """A bar rising from (z, y), turned about x at its foot. Positive angles lean toward +z."""
        self.box(-xh, y, z - width / 2, xh, y + length, z + width / 2, mat, rot=("x", angle, (0, y, z)), **kw)


def end_z(x, y, length, angle):
    a = math.radians(angle)
    return x - length * math.sin(a), y + length * math.cos(a)


def end_x(z, y, length, angle):
    a = math.radians(angle)
    return z + length * math.sin(a), y + length * math.cos(a)


def common(s, collar=True):
    sc = s.school
    accent = {"holy": "gold", "ender": "purpur", "blood": "gold", "evocation": "engraved", "nature": "bark",
              "eldritch": "deepslate"}[sc]
    tip = {"holy": "sun", "ender": "crystal", "blood": "iron", "evocation": "emerald", "nature": "moss",
           "eldritch": "cyantip"}[sc]
    s.box(-0.75, -13, -0.75, 0.75, 15, 0.75, f"{sc}_shaft")
    s.box(-1, -15, -1, 1, -13, 1, "iron" if sc == "blood" else accent)
    s.box(-0.5, -16, -0.5, 0.5, -15, 0.5, tip, glow=sc in ("ender", "eldritch"))
    s.box(-1, 2, -1, 1, 9, 1, f"{sc}_grip")
    s.box(-1.25, 9, -1.25, 1.25, 9.5, 1.25, accent)
    s.box(-1.25, 1.5, -1.25, 1.25, 2, 1.25, accent)
    if collar:
        s.box(-1.25, 13.5, -1.25, 1.25, 14.5, 1.25, accent)
    return accent


def holy():
    """A sunburst: one thick rayed ring and a star core with a boss front and back. No second ring: seen from
    the front it drew a line through the star and, with the side rays, read as a cross."""
    s = Staff("holy")
    common(s)
    cy, ro, ri = 20.5, 4.0, 3.0
    s.box(-1.5, 15, -1.5, 1.5, 16.5, 1.5, "gold")
    s.box(-1.25, cy + ri, -0.75, 1.25, cy + ro, 0.75, "gold")
    s.box(-1.25, cy - ro, -0.75, 1.25, cy - ri, 0.75, "gold")
    s.box(-ro, cy - 1.25, -0.75, -ri, cy + 1.25, 0.75, "gold")
    s.box(ri, cy - 1.25, -0.75, ro, cy + 1.25, 0.75, "gold")
    for a in (45, -45):
        s.box(-1.75, cy + ri, -0.7, 1.75, cy + ro, 0.7, "gold", rot=("z", a, (0, cy, 0)))
        s.box(-1.75, cy - ro, -0.7, 1.75, cy - ri, 0.7, "gold", rot=("z", a, (0, cy, 0)))

    def ray(x0, y0, x1, y1, tx0, ty0, tx1, ty1, rot=None):   # seven equal rays; the shaft takes the eighth place
        s.box(x0, y0, -0.3, x1, y1, 0.3, "sun", rot=rot, glow=True)
        s.box(tx0, ty0, -0.2, tx1, ty1, 0.2, "sun", rot=rot, glow=True)
    ray(-0.5, cy + ro, 0.5, cy + ro + 1, -0.25, cy + ro + 1, 0.25, cy + ro + 1.75)
    ray(-ro - 1, cy - 0.5, -ro, cy + 0.5, -ro - 1.75, cy - 0.25, -ro - 1, cy + 0.25)
    ray(ro, cy - 0.5, ro + 1, cy + 0.5, ro + 1, cy - 0.25, ro + 1.75, cy + 0.25)
    for a in (45, -45):
        ray(-0.5, cy + ro, 0.5, cy + ro + 1, -0.25, cy + ro + 1, 0.25, cy + ro + 1.75, rot=("z", a, (0, cy, 0)))
        ray(-0.5, cy - ro - 1, 0.5, cy - ro, -0.25, cy - ro - 1.75, 0.25, cy - ro - 1, rot=("z", a, (0, cy, 0)))
    s.box(-1, cy - 1, -1.25, 1, cy + 1, 1.25, "sunorb", glow=True, floats=True)
    s.box(-1, cy - 1, -1, 1, cy + 1, 1, "sunorb", rot=("z", 45, (0, cy, 0)), glow=True, floats=True)
    s.box(-0.5, cy - 0.5, -1.75, 0.5, cy + 0.5, 1.75, "sunorb", glow=True, floats=True)
    return s


def ender():
    s = Staff("ender")
    common(s)
    s.box(-1.5, 15, -1.5, 1.5, 16.5, 1.5, "purpur")
    s.box(-0.75, 16.5, -0.75, 0.75, 17.5, 0.75, "endereye", glow=True)
    # right horn of the crescent, the shorter
    s.bar_z(1, 15.75, 3.5, 1, 0.5, -45, "prong")
    s.box(3, 18, -0.5, 4, 20.5, 0.5, "prong")
    s.bar_z(3.5, 20.25, 2.75, 0.75, 0.4, 22.5, "prong")
    # left horn, taller, curling in over the crystal
    s.bar_z(-1, 15.75, 3.5, 1, 0.5, 45, "prong")
    s.box(-4, 18, -0.5, -3, 22.5, 0.5, "prong")
    s.bar_z(-3.5, 22.25, 3.25, 0.75, 0.4, -22.5, "prong")
    tx, ty = end_z(-3.5, 22.25, 3.0, -22.5)
    s.bar_z(tx, ty, 1.5, 0.5, 0.3, -45, "prong")
    # a wider lip under the eye and a crystal growing front and back, for depth. Both sit off the centre line:
    # anything centred in front of the eye or the crystal hides it from the front.
    s.box(-2, 16, -2, 2, 16.5, 2, "purpur")
    for sg in (1, -1):
        s.box(sg * 1.25 - 0.25, 16.25, sg * 1.5 - 0.25, sg * 1.25 + 0.25, 18.5, sg * 1.5 + 0.25, "crystal",
              rot=("x", sg * 22.5, (sg * 1.25, 16.25, sg * 1.5)), glow=True)
    # the floating crystal
    for y0, y1, h in ((19.25, 22.25, 1.0), (22.25, 23.25, 0.5), (18.25, 19.25, 0.5)):
        s.box(-h, y0, -h, h, y1, h, "crystal", rot=("y", 45, (0, 20.75, 0)), glow=True, floats=True)
    # end crystals growing from the horns, as on the pauldron of the armour
    s.bar_z(-3.9, 19.5, 1.75, 0.75, 0.3, 45, "crystal", glow=True)
    s.bar_z(-3.9, 21.0, 1.25, 0.5, 0.25, 45, "crystal", glow=True)
    s.bar_z(3.9, 18.9, 1.25, 0.5, 0.25, -45, "crystal", glow=True)
    return s


def blood():
    s = Staff("blood")
    common(s)
    s.box(-1, 14.5, -1.25, 1, 15.5, 1.25, "jaw")
    s.box(-1.5, 15.5, -1.5, 1.5, 18, 1.5, "skull")
    s.box(-0.75, 18, -0.75, 0.75, 19, 0.75, "gold")
    s.box(-1.25, 19.25, -1, 1.25, 21.75, 1, "jewel", rot=("z", 45, (0, 20.5, 0)), glow=True)
    s.box(-0.75, 22, -0.75, 0.75, 22.5, 0.75, "gold")
    s.box(-0.5, 22, -0.5, 0.5, 25, 0.5, "iron")
    s.box(-0.25, 25, -0.25, 0.25, 27, 0.25, "iron")
    for sg in (1, -1):
        rx, ry = sg * 1.25, 18.0
        for angle, length, mz in ((22.5, 7.0, 0.2), (45, 6.0, 0.12)):     # two long fingers, each with its skin
            rot = ("z", -sg * angle, (rx, ry, 0))
            s.box(rx - 0.25, ry, -0.35, rx + 0.25, ry + length, 0.35, "wingbone", rot=rot)
            s.box(rx - 0.25, ry + length, -0.25, rx + 0.25, ry + length + 0.75, 0.25, "gold", rot=rot)
            s.box(rx, ry + 0.5, -mz, rx + sg * 2.0, ry + length - 1.5, mz, "membrane", rot=rot)
        s.box(rx, 17.75, -0.35, sg * 4.0, 18.25, 0.35, "wingbone")          # the thumb, along the lower edge of the skin
        s.box(sg * 4.0, 17.75, -0.25, sg * 4.6, 18.25, 0.25, "gold")
        for sz in (1, -1):                                                  # four gold prongs gripping the jewel's point
            s.box(sg * 0.75 - 0.2, 18, sz * 0.75 - 0.2, sg * 0.75 + 0.2, 19.5, sz * 0.75 + 0.2, "gold",
                  rot=("x", sz * 22.5, (sg * 0.75, 18, sz * 0.75)))
    return s


def evocation():
    s = Staff("evocation")
    common(s, collar=False)
    s.box(-1.5, 12.75, -1.5, 1.5, 14.25, 1.5, "sash")           # the sash knot and its two tails
    s.box(1.5, 8.75, -0.75, 2, 13.5, 0.25, "sash")
    s.box(1.5, 10.75, 0.25, 2, 13.5, 1.0, "sash2")
    s.box(-1.5, 15, -1.5, 1.5, 16.5, 1.5, "engraved")
    s.box(-1, 18, -1, 1, 21.5, 1, "emerald", glow=True, floats=True)
    s.box(-0.5, 21.5, -0.5, 0.5, 22.25, 0.5, "emerald", glow=True, floats=True)
    s.box(-0.5, 17.25, -0.5, 0.5, 18, 0.5, "emerald", glow=True, floats=True)
    s.box(-0.5, 16.5, -0.5, 0.5, 17.25, 0.5, "steel")           # the seat under the stone
    for sg in (1, -1):                                         # a basket of four fangs, ivory at the points
        s.bar_z(sg * 1, 16, 2.5, 0.75, 0.375, -sg * 45, "engraved")
        s.bar_z(sg * 2.75, 17.5, 3.0, 0.75, 0.375, sg * 22.5, "engraved")
        fx, fy = end_z(sg * 2.75, 17.5, 3.0, sg * 22.5)
        s.bar_z(fx, fy, 1.0, 0.5, 0.25, sg * 22.5, "fangtip")
        s.bar_x(sg * 1, 16, 2.5, 0.75, 0.375, sg * 45, "engraved")
        s.bar_x(sg * 2.75, 17.5, 3.0, 0.75, 0.375, -sg * 22.5, "engraved")
        fz, fy = end_x(sg * 2.75, 17.5, 3.0, -sg * 22.5)
        s.bar_x(fz, fy, 1.0, 0.5, 0.25, -sg * 22.5, "fangtip")
    # the sigil ring: a square frame hovering round the stone, tilted like an orbit so it never draws a crossbar
    y0, y1, o, i = 19.375, 20.125, 3.75, 3.25
    rot = ("z", 22.5, (0, 19.75, 0))
    s.box(-o, y0, -o, o, y1, -i, "engraved", rot=rot, floats=True)
    s.box(-o, y0, i, o, y1, o, "engraved", rot=rot, floats=True)
    s.box(-o, y0, -i, -i, y1, i, "engraved", rot=rot, floats=True)
    s.box(i, y0, -i, o, y1, i, "engraved", rot=rot, floats=True)
    for dx in (1, -1):                                         # an emerald at each corner of the ring
        for dz in (1, -1):
            s.box(dx * 3.5 - 0.5, 19.25, dz * 3.5 - 0.5, dx * 3.5 + 0.5, 20.25, dz * 3.5 + 0.5, "emerald", rot=rot,
                  glow=True, floats=True)
    return s


def nature():
    s = Staff("nature")
    common(s)
    s.box(-1.5, 15, -1.5, 1.5, 16.5, 1.5, "moss")
    s.box(-1.5, 16.5, -1.5, 1.5, 17, 1.5, "sepal")
    s.box(-1.25, 17, -1.25, 1.25, 19, 1.25, "rose")
    s.box(-0.75, 19, -0.75, 0.75, 19.5, 0.75, "rose")
    for sg in (1, -1):
        tall = sg == -1                                                     # the left antler stands taller
        s.bar_z(sg * 0.75, 15.75, 4.5, 1, 0.5, -sg * 45, "antler")          # beam, rooted inside the moss
        s.bar_z(sg * 3.7, 18.5, 4.0, 0.75, 0.375, -sg * 22.5, "antler")
        bx, by = end_z(sg * 3.7, 18.5, 3.8, -sg * 22.5)
        s.box(bx - 0.25, by, -0.25, bx + 0.25, by + (3.25 if tall else 2.0), 0.25, "antler")
        s.box(sg * 3.7 - 0.375, 18.7, -0.3, sg * 3.7 + 0.375, 21.5, 0.3, "antler")     # inner tine
        s.bar_z(sg * 3.7, 21.3, 1.75, 0.5, 0.25, sg * 22.5, "antler")
        s.bar_z(sg * 4.5, 20.3, 1.75, 0.5, 0.25, -sg * 45, "antler")                   # outer tine
        # a short brow tine front and back, kept below the rose so it never crosses the bloom
        s.bar_x(sg * 1.25, 15.25, 2.25, 0.75, 0.375, sg * 45, "antler")
        # a collar of leaves drooping from the moss, one to each side
        s.box(sg * 1.5 - 0.75, 13.25, -0.125, sg * 1.5 + 0.75, 15.5, 0.125, "leaf", rot=("z", sg * 45, (sg * 1.5, 15.5, 0)))
        s.box(-0.75, 13.25, sg * 1.5 - 0.125, 0.75, 15.5, sg * 1.5 + 0.125, "leaf", rot=("x", -sg * 45, (0, 15.5, sg * 1.5)))
    s.bar_z(0.75, 10.5, 2.25, 1.5, 0.125, -45, "leaf")                                 # and two on the shaft
    s.bar_z(-0.75, 11.75, 2.0, 1.5, 0.125, 45, "leaf")
    s.box(-6.3, 20.6, -0.375, -5.55, 21.35, 0.375, "berry", glow=True)                 # berries on the left outer tine
    s.box(-5.6, 19.95, -0.375, -4.85, 20.7, 0.375, "berry", glow=True)
    return s


def eldritch():
    s = Staff("eldritch")
    common(s, collar=False)
    cy = 19.75
    s.box(-1.5, 15, -1.5, 1.5, 16.5, 1.5, "socket_eyes")
    s.box(-1, 16.5, -1, 1, 18, 1, "sculk")
    s.box(-2.25, cy - 1.25, -0.75, 2.25, cy + 1.25, 0.75, "eye", glow_faces=("north", "south"))
    # four lids closing to an almond, with a keystone above and below
    s.box(-3.25, cy, -1, 0, cy + 1, 1, "lid", rot=("z", 22.5, (-3.25, cy, 0)))
    s.box(0, cy, -1, 3.25, cy + 1, 1, "lid", rot=("z", -22.5, (3.25, cy, 0)))
    s.box(-3.25, cy - 1, -1, 0, cy, 1, "lid", rot=("z", -22.5, (-3.25, cy, 0)))
    s.box(0, cy - 1, -1, 3.25, cy, 1, "lid", rot=("z", 22.5, (3.25, cy, 0)))
    s.box(-0.5, cy + 1.1, -1.1, 0.5, cy + 2.1, 1.1, "deepslate")
    s.box(-0.5, cy - 2.1, -1.1, 0.5, cy - 1.1, 1.1, "deepslate")
    # tendril horns rooted in the corners of the eye, the left one taller
    for sg, lean, rise in ((-1, 3.0, 2.5), (1, 2.25, 1.5)):
        s.bar_z(sg * 2.9, cy - 0.5, lean + 0.5, 1.0, 0.4, -sg * 22.5, "sculk")
        hx, hy = end_z(sg * 2.9, cy - 0.5, lean + 0.25, -sg * 22.5)
        s.box(hx - 0.25, hy, -0.25, hx + 0.25, hy + rise, 0.25, "sculk")
        s.box(hx - 0.25, hy + rise, -0.25, hx + 0.25, hy + rise + 0.5, 0.25, "cyantip", glow=True)
    # two short feelers front and back, from the upper keystone
    for sg, length in ((1, 2.25), (-1, 1.5)):
        s.bar_x(sg * 0.75, cy + 1.8, length, 0.5, 0.25, sg * 22.5, "sculk")
        fz, fy = end_x(sg * 0.75, cy + 1.8, length, sg * 22.5)
        s.bar_x(fz, fy, 0.5, 0.5, 0.25, sg * 22.5, "cyantip", glow=True)
    # tendrils hanging down the shaft, each a different length, each tipped with light
    for x, z, y0 in ((1.0, 0, 10.5), (-1.0, 0, 12.0), (0, 1.0, 9.75), (0, -1.0, 12.75)):
        s.box(x - 0.25, y0, z - 0.25, x + 0.25, 15, z + 0.25, "tendril")
        s.box(x - 0.25, y0 - 0.75, z - 0.25, x + 0.25, y0, z + 0.25, "cyantip", glow=True)
    return s


BUILDERS = {"holy": holy, "ender": ender, "blood": blood, "evocation": evocation, "nature": nature, "eldritch": eldritch}


# ---------------------------------------------------------------------------------------------
# Texture packing and JSON
# ---------------------------------------------------------------------------------------------
def face_size(e, face):
    dx, dy, dz = (e["hi"][i] - e["lo"][i] for i in range(3))
    w, h = {"north": (dx, dy), "south": (dx, dy), "east": (dz, dy), "west": (dz, dy), "up": (dx, dz), "down": (dx, dz)}[face]
    return max(1, round(w * TEXEL)), max(1, round(h * TEXEL))


def face_key(e, face):
    w, h = face_size(e, face)
    kind = face if face in ("up", "down") else ("front" if face in ("north", "south") else "side")
    return e["mat"], kind, w, h


def pack(staff):
    """Shelf-pack one rectangle per distinct (material, face kind, size). Returns (image, {key: (u, v, w, h)})."""
    keys = {}
    for e in staff.elements:
        for face in e["faces"]:
            keys.setdefault(face_key(e, face), face)
    order = sorted(keys, key=lambda k: (-k[3], -k[2], k[0], k[1]))
    for size in (64, 128):
        rects, x, y, shelf = {}, 0, 0, 0
        for k in order:
            w, h = k[2], k[3]
            if x + w > size:
                x, y, shelf = 0, y + shelf, 0
            if y + h > size:
                rects = None
                break
            rects[k] = (x, y, w, h)
            x, shelf = x + w, max(shelf, h)
        if rects is not None:
            break
    else:
        raise SystemExit(f"{staff.school}: faces do not fit a 128x128 sheet")
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    for k, (x, y, w, h) in rects.items():
        tile = MATS[k[0]](keys[k], w, h)
        assert tile.size == (w, h), (k, tile.size)
        img.paste(tile, (x, y))
    return img, rects


def to_json(staff, rects, size):
    elements = []
    for e in staff.elements:
        out = {"from": [e["lo"][0] + 8, e["lo"][1], e["lo"][2] + 8], "to": [e["hi"][0] + 8, e["hi"][1], e["hi"][2] + 8]}
        out["from"] = [round(v, 4) for v in out["from"]]
        out["to"] = [round(v, 4) for v in out["to"]]
        if e["rot"]:
            axis, angle, (ox, oy, oz) = e["rot"]
            out["rotation"] = {"angle": angle, "axis": axis, "origin": [round(ox + 8, 4), round(oy, 4), round(oz + 8, 4)]}
        faces = {}
        for face in e["faces"]:
            x, y, w, h = rects[face_key(e, face)]
            f = {"uv": [x * 16 / size, y * 16 / size, (x + w) * 16 / size, (y + h) * 16 / size], "texture": "#0"}
            if e["glow"] or face in e["glow_faces"]:
                f["forge_data"] = {"block_light": 15, "sky_light": 15}
            faces[face] = f
        out["faces"] = faces
        elements.append(out)
    tex = f"{MOD}:item/{staff.school}_staff"
    return {"credit": "Ice and Fire: Schools of Dragonsteel (tools/generate_staves.py)", "texture_size": [size, size],
            "textures": {"0": tex, "particle": tex}, "elements": elements, "display": STAFF_DISPLAY}


def rotate(p, rot):
    if not rot:
        return p
    axis, angle, o = rot
    a = math.radians(angle)
    c, s_ = math.cos(a), math.sin(a)
    x, y, z = (p[i] - o[i] for i in range(3))
    if axis == "x":
        y, z = y * c - z * s_, y * s_ + z * c
    elif axis == "y":
        x, z = x * c + z * s_, -x * s_ + z * c
    else:
        x, y = x * c - y * s_, x * s_ + y * c
    return x + o[0], y + o[1], z + o[2]


def unrotate(p, rot):
    return rotate(p, (rot[0], -rot[1], rot[2])) if rot else p


def contains(e, p, eps):
    q = unrotate(p, e["rot"])
    return all(e["lo"][i] - eps <= q[i] <= e["hi"][i] + eps for i in range(3))


def samples(e, n=4):
    lo, hi = e["lo"], e["hi"]
    for i in range(n + 1):
        for j in range(n + 1):
            for k in range(n + 1):
                yield rotate(tuple(lo[a] + (hi[a] - lo[a]) * t / n for a, t in zip(range(3), (i, j, k))), e["rot"])


def check(staff):
    problems = []
    for n, e in enumerate(staff.elements):
        for v in (e["lo"][0] + 8, e["hi"][0] + 8, e["lo"][1], e["hi"][1], e["lo"][2] + 8, e["hi"][2] + 8):
            if not -16 <= v <= 32:
                problems.append(f"{staff.school} element {n} ({e['mat']}): coordinate {v} outside -16..32")
        if e["rot"] and float(e["rot"][1]) not in VALID_ANGLES:
            problems.append(f"{staff.school} element {n} ({e['mat']}): angle {e['rot'][1]} not allowed")
        if e["mat"] not in MATS:
            problems.append(f"{staff.school} element {n}: unknown material {e['mat']}")
        if not e["floats"]:
            pts = list(samples(e))
            if not any(contains(o, p, 0.06) for m, o in enumerate(staff.elements) if m != n for p in pts):
                problems.append(f"{staff.school} element {n} ({e['mat']} {e['lo']}..{e['hi']}) touches nothing")
    return problems


def generate():
    """Write the six models and sheets. Returns a list of problems (empty when all is well)."""
    problems = []
    for school, name in STAVES.items():
        staff = BUILDERS[school]()
        problems += check(staff)
        img, rects = pack(staff)
        (A / "textures/item").mkdir(parents=True, exist_ok=True)
        img.save(A / "textures/item" / f"{school}_staff.png")
        path = A / "models/item" / f"{name}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((json.dumps(to_json(staff, rects, img.size[0]), indent=2) + "\n").encode("utf-8"))
        glow = sum(1 for e in staff.elements if e["glow"] or e["glow_faces"])
        print(f"{school:10} {name:30} {len(staff.elements):3} boxes, {glow:2} glowing, sheet {img.size[0]}x{img.size[1]}, {len(rects)} tiles")
    return problems


def main():
    problems = generate()
    for p in problems:
        print("PROBLEM", p)
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
