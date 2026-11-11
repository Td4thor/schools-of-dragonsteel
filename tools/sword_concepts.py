#!/usr/bin/env python
"""Concept sprites for the five school swords that are still recolours of Ice and Fire's ice dragonsteel sword.

    python tools/sword_concepts.py            writes docs/art/concepts/*.png and docs/art/sword_concepts.png

CONCEPTS ONLY: nothing here is written into the mod's assets. Each sword is drawn the way Dawn is (see
generate_textures.dawn): every pixel is placed by t (along the sword from the pommel, bottom-left, to the tip)
and s (across it; negative is the lit upper-left side). When Tad approves a design, its function moves into
generate_textures.py and replaces that sword's remap.
"""
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_textures import R, hexes, outline, ramp  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
ITEMS = ROOT / "src/main/resources/assets/dragonsteel_schools/textures/item"
OUT = ROOT / "docs/art"

R.setdefault("iron", hexes("#0d0d10", "#17171c", "#23232a", "#31313a", "#43434e", "#585865", "#72727f", "#90909c"))
R.setdefault("leather", hexes("#24150c", "#382112", "#4d2f1a", "#644025", "#7c5332", "#966843", "#b08158"))
R.setdefault("sash", hexes("#1f0e33", "#33174f", "#48226c", "#5e2f88", "#7741a3", "#9258bd", "#ad78d3"))
R.setdefault("rose", hexes("#3d0612", "#5e0b1c", "#8a1228", "#b51d36", "#d8344a", "#ee6274", "#ff9aa5"))
R.setdefault("teal", hexes("#06382f", "#0b5c4c", "#12856c", "#1bb08d", "#3fd8b0", "#9af5dc"))
R.setdefault("deepslate", hexes("#15161a", "#22242a", "#30333b", "#40444e", "#535864", "#6a707d", "#858b98"))
R.setdefault("leaf", hexes("#12300f", "#1c4a17", "#2a6620", "#3d852c", "#57a53c", "#7cc456", "#a8de7c"))

P0 = (3.0, 28.0)
K = 1 / math.sqrt(2)
LENGTH = math.hypot(28.5 - 3.0, 28.0 - 3.5)   # 35.4, the same reach as Dawn


def c(name, t):
    return ramp(name, max(0.0, min(1.0, t)))


def draw(fn, edge, after=None):
    img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    px = img.load()
    for y in range(32):
        for x in range(32):
            cx, cy = x + 0.5 - P0[0], y + 0.5 - P0[1]
            t, s = (cx - cy) * K, (cx + cy) * K
            col = fn(t, s)
            if col is not None:
                px[x, y] = col
    outline(img, edge)
    if after:
        for y in range(32):
            for x in range(32):
                cx, cy = x + 0.5 - P0[0], y + 0.5 - P0[1]
                col = after((cx - cy) * K, (cx + cy) * K, px[x, y])
                if col is not None:
                    px[x, y] = col
    return img


def side(name, s, lit, shade):
    return c(name, lit if s < 0 else shade)


# ---------------------------------------------------------------------------------------------
def elsewhere():
    """A blade caught mid-step: three shards of night steel, each slipped a little out of line, held together
    by violet light. A crescent guard, one horn taller, round an Eye of Ender."""
    segs = ((8.0, 14.4, 0.0), (17.2, 23.4, -1.0), (26.2, LENGTH + 0.4, 0.8))

    def fn(t, s):
        a = abs(s)
        if t < -0.9:
            return None
        if t < 2.0:                                              # pommel: a small end crystal
            return c("violet", 0.75 if s < 0 else 0.35) if a + abs(t - 0.7) <= 1.7 else None
        if t < 6.0:                                              # grip: void cloth
            return c("void", 0.5 if int(t * 1.4) % 2 else 0.3) if a <= 0.75 else None
        if t < 7.4:                                              # crescent guard and its eye
            if a <= 1.4:
                return (4, 26, 22, 255) if a < 0.4 else c("teal", 0.9 if s < 0 else 0.6)
            return side("obsid", s, 0.95, 0.7) if a <= 4.7 and t > 6.1 else None
        if s < 0 and 3.7 <= a <= 4.7 and t < 11.2:               # the tall horn
            return c("violet", 0.45) if t > 10.2 else c("obsid", 0.95)
        if s > 0 and 3.7 <= a <= 4.7 and t < 8.9:                # the short horn
            return c("obsid", 0.7)
        for t0, t1, off in segs:
            if t0 <= t <= t1:
                ss = s - off
                w = 1.55 if t < LENGTH - 3.0 else max(0.0, 1.55 * (LENGTH + 0.4 - t) / 3.4)
                if abs(ss) > w + 0.2:
                    return None
                if abs(ss) < 0.5:
                    return c("violet", 0.45 + 0.5 * t / LENGTH)
                return side("obsid", ss, 0.82, 0.55)
        return None

    def glow(t, s, cur):                                         # a mote of light in each gap between shards
        for (_, t1, o1), (t0, _, o0) in zip(segs, segs[1:]):
            if t1 + 0.9 <= t <= t0 - 0.9 and abs(s - (o0 + o1) / 2) < 0.5:
                return c("violet", 0.9)
        return None
    return draw(fn, R["obsid"][0], glow)


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
            return c("crimson", 0.0) if abs(a - 0.8) < 0.42 and 0.7 < t < 1.7 else c("gold", 0.85 if s < 0 else 0.55)
        if t < 6.0:                                              # grip: black leather, crimson cord
            return (c("crimson", 0.55) if int(t * 1.4) % 3 == 0 else c("iron", 0.35)) if a <= 0.75 else None
        u = t - 6.7 - a * 0.5                                    # quillons swept up toward the blade
        if a <= 5.0 and -0.9 <= u <= 0.9:
            if a <= 1.0:
                return c("crimson", 0.95 if s < 0 else 0.7)      # the jewel
            return c("gold", 1.0) if a > 4.1 else side("gold", s, 0.8, 0.55)
        if t < 7.4:
            return None
        w = 1.45 + 0.75 * math.sin((t - 7.4) * 1.15)
        if t > LENGTH - 5.0:
            w = min(w, 1.9 * (LENGTH + 0.3 - t) / 5.3)
        if a > w + 0.2 or t > LENGTH + 0.3:
            return None
        if a < 0.5:
            return c("crimson", 0.86 + 0.14 * math.sin(t * 0.9))
        return side("crimson", s, 0.6, 0.32)
    return draw(fn, R["crimson"][0])


def covenant():
    """A broad spell-knight's blade of dark steel with a line of gold runes down the fuller, its point split
    into two ivory fangs. A gold ring guard holds an emerald; a purple sash trails from the pommel."""
    tc, length = 7.9, 33.5

    def fn(t, s):
        a = abs(s)
        if 0.0 <= t <= 1.5 and 1.3 <= s <= 3.2:                  # sash tuft at the pommel
            return c("sash", 0.7 if s < 2.3 else 0.45)
        if t < -0.8:
            return None
        if t < 1.8:                                              # pommel cap
            return side("gold", s, 0.8, 0.5) if a <= 1.35 else None
        if t < 5.2:                                              # grip: brown leather
            return c("leather", 0.55 if int(t * 1.4) % 2 else 0.35) if a <= 0.8 else None
        r = math.hypot(t - tc, s)
        if r <= 1.45:                                            # the emerald
            return c("emerald", 1.0 if (s < -0.2 and t > tc) else 0.75 if s < 0.3 else 0.5)
        if r <= 3.1:
            return side("gold", s, 0.85 if r > 2.4 else 0.65, 0.5)
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
            return c("bone", 1.0 if s < 0 else 0.7)              # ivory points
        if a < 0.55:
            return c("gold", 0.75) if int(t / 1.42) % 2 == 0 else c("slate", 0.25)
        return side("slate", s, 0.72, 0.42)
    return draw(fn, R["slate"][0])


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
            return side("bark", s, 0.7, 0.4) if math.hypot(t - 0.6, s) <= 1.6 else None
        if t < 5.4:                                              # grip: vine over bark
            return (c("leaf", 0.7) if int(t * 1.4) % 2 else c("bark", 0.45)) if a <= 0.75 else None
        r = math.hypot(t - 7.0, s)
        if r <= 1.5:                                             # the rose
            return c("rose", 0.15) if r < 0.6 else c("rose", 0.8 if s < 0 else 0.5)
        if 0.8 <= a <= 4.8:                                      # leaf guard
            half = 0.25 + 1.35 * max(0.0, math.sin(math.pi * (a - 0.8) / 4.0)) ** 0.7
            if abs(t - 7.0) <= half:
                return c("leaf", 0.95) if abs(t - 7.0) < 0.36 else c("leaf", 0.7 if s < 0 else 0.45)
        if t < 7.6 or t > length + 0.3:
            return None
        bend = -0.0065 * (t - 7.0) ** 2                          # bows toward the lit side
        ss = s - bend
        w = 1.5 if t < length - 5.0 else max(0.0, 1.5 * (length + 0.3 - t) / 5.3)
        for tk in thorns:                                        # thorns on the back of the bow
            h = -ss - w
            if 0 < h <= 2.5 and 0 <= (t - tk) - h * 0.3 <= 1.6 - h * 0.36:
                return c("bone", 0.9) if h > 1.3 else c("bark", 0.75)
        if abs(ss) > w + 0.15:
            return None
        if ss > w - 0.95:
            return c("leaf", 0.85 if int(t) % 3 else 0.6)        # the living edge
        return c("bark", 0.65 if ss < -0.4 else 0.45)
    return draw(fn, R["bark"][0])


def hush():
    """A needle of sculk-black steel that narrows all the way from guard to point, a thread of pale light down
    its heart. The guard is an open eye; a feeler rises from each corner, one longer than the other."""
    def fn(t, s):
        a = abs(s)
        if t < -0.7:
            return None
        if t < 2.0:                                              # pommel: a mote of cold light
            r = math.hypot(t - 0.7, s)
            return (c("cyan", 1.0) if r < 0.8 else c("cyan", 0.45)) if r <= 1.5 else None
        if t < 5.2:                                              # grip: sculk bound in stone
            return (c("deepslate", 0.7) if int(t * 1.4) % 3 == 0 else c("sculk", 0.55)) if a <= 0.72 else None
        lid = 2.0 * (1.0 - (a / 4.0) ** 1.6) if a <= 4.0 else -1.0   # the eye across the guard
        d = abs(t - 7.3)
        if d <= lid + 0.2:
            if d > lid - 0.55:
                return side("deepslate", s, 0.95, 0.7)           # lids
            r = math.hypot(t - 7.3, s * 0.85)
            if r < 0.9:
                return (2, 6, 8, 255)                            # pupil
            return c("cyan", 0.7) if r < 2.0 else c("bone", 0.9)
        if -4.0 <= s <= -3.0 and 7.3 < t <= 12.2:                # the long feeler
            return c("cyan", 0.9) if t > 11.0 else c("sculk", 0.9)
        if 3.0 <= s <= 4.0 and 7.3 < t <= 10.0:                  # the short one
            return c("cyan", 0.9) if t > 9.0 else c("sculk", 0.7)
        if t < 8.6 or t > LENGTH + 0.3:
            return None
        w = 0.3 + 1.1 * (1.0 - (t - 8.6) / (LENGTH - 8.6))
        if a > w + 0.1:
            return None
        if a < 0.4:
            return c("cyan", 0.75) if int(t * 0.9) % 3 == 0 else c("sculk", 0.9)
        return side("sculk", s, 1.0, 0.6)
    return draw(fn, R["sculk"][0])


CONCEPTS = (("elsewhere", "Elsewhere (Ender)", elsewhere), ("thirst", "Thirst (Blood)", thirst),
            ("covenant", "Covenant (Evocation)", covenant), ("briar", "Briar (Nature)", briar), ("hush", "Hush (Eldritch)", hush))


def main():
    (OUT / "concepts").mkdir(parents=True, exist_ok=True)
    zoom = 8
    cell = 32 * zoom
    sheet = Image.new("RGBA", (len(CONCEPTS) * (cell + 16) + 16, 2 * cell + 124), (40, 42, 50, 255))
    d = ImageDraw.Draw(sheet)
    d.text((16, 6), "Sword concepts (not in the mod yet). Top: now, a recolour of Ice and Fire's sword. Bottom: concept. "
                    "Small copies are inventory size.", fill=(235, 235, 235, 255))
    for i, (name, label, fn) in enumerate(CONCEPTS):
        img = fn()
        img.save(OUT / "concepts" / f"{name}_concept.png")
        if "--ascii" in sys.argv:
            print(name)
            for y in range(32):
                print("".join("#" if img.getpixel((x, y))[3] else "." for x in range(32)))
        x = 16 + i * (cell + 16)
        d.text((x, 22), label, fill=(235, 235, 235, 255))
        for row, pic in enumerate((Image.open(ITEMS / f"{name}.png").convert("RGBA"), img)):
            y = 38 + row * (cell + 10)
            d.rectangle((x, y, x + cell - 1, y + cell - 1), fill=(139, 139, 139, 255))
            sheet.alpha_composite(pic.resize((cell, cell), Image.NEAREST), (x, y))
        y = 38 + 2 * (cell + 10)
        for k, (pic, bg) in enumerate(((img, (139, 139, 139, 255)), (img, (198, 198, 198, 255)))):
            d.rectangle((x + k * 44, y, x + k * 44 + 35, y + 35), fill=bg)
            sheet.alpha_composite(pic, (x + k * 44 + 2, y + 2))
    sheet.save(OUT / "sword_concepts.png")
    print("wrote", OUT / "sword_concepts.png", sheet.size)


if __name__ == "__main__":
    main()
