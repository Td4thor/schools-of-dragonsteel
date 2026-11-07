#!/usr/bin/env python
"""Software preview of the plate armour, drawn from quads baked by the real GeckoLib 4.8.4.

    python tools/render_armor.py <school> <dump.json> [out_dir]

The dump comes from the BakeProbe (GeckoLib's own GeometryTree + BakedModelFactory, rest pose).
Orthographic, z-buffered, simple directional light; glowmask texels drawn full-bright. A plain
vanilla-proportioned body stands inside the armour. These are previews, NOT in-game screenshots.
"""
import json
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
ARMOR_TEX = ROOT / "src/main/resources/assets/dragonsteel_schools/textures/models/armor"
SCALE = 10
BG = (54, 57, 66, 255)
LIGHT = (0.35, 0.75, -0.55)

# Bedrock author space: +Y up, wearer faces -Z, wearer's right arm at -X.
BODY = [
    ((-4, 4), (24, 32), (-4, 4), (205, 168, 140)),   # head
    ((-4, 4), (12, 24), (-2, 2), (70, 110, 150)),    # torso
    ((-8, -4), (12, 24), (-2, 2), (205, 168, 140)),  # right arm
    ((4, 8), (12, 24), (-2, 2), (205, 168, 140)),    # left arm
    ((-4, 0), (0, 12), (-2, 2), (60, 60, 120)),      # right leg
    ((0, 4), (0, 12), (-2, 2), (60, 60, 120)),       # left leg
]

SLOT_BONES = {
    "helmet": {"armorHead"},
    "chestplate": {"armorBody", "armorRightArm", "armorLeftArm", "armorTorsoExtensionRightLeg", "armorTorsoExtensionLeftLeg"},
    "leggings": {"armorRightLeg", "armorLeftLeg", "armorLeggingTorsoLayer"},
    "boots": {"armorRightBoot", "armorLeftBoot"},
}
ALL = set().union(*SLOT_BONES.values())


def norm(v):
    length = math.sqrt(sum(c * c for c in v)) or 1.0
    return tuple(c / length for c in v)


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def body_quads():
    quads = []
    for (x0, x1), (y0, y1), (z0, z1), col in BODY:
        c = [(x, y, z) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]
        faces = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
        for f in faces:
            quads.append({"pts": [c[i] for i in f], "color": col})
    return quads


def project(p, yaw):
    """Rotate about Y by yaw (radians), then orthographic: screen x right, y down, depth toward viewer."""
    x, y, z = p
    c, s = math.cos(yaw), math.sin(yaw)
    rx = x * c - z * s
    rz = x * s + z * c
    return rx, -y, rz


def render(quads, base, glow, yaw, title):
    tw, th = base.size
    bp, gp = base.load(), glow.load()
    W, H = 30 * SCALE, 46 * SCALE
    ox, oy = W / 2, 42.5 * SCALE
    img = Image.new("RGBA", (W, H), BG)
    px = img.load()
    zbuf = [[math.inf] * W for _ in range(H)]
    for q in quads:
        pts = q["pts"]
        n = norm(cross(tuple(pts[1][i] - pts[0][i] for i in range(3)), tuple(pts[2][i] - pts[0][i] for i in range(3))))
        light = abs(sum(n[i] * LIGHT[i] for i in range(3)))
        shade = 0.55 + 0.45 * light
        proj = [project(p, yaw) for p in pts]
        scr = [(ox + p[0] * SCALE, oy + p[1] * SCALE, p[2]) for p in proj]
        uvs = q.get("uv")
        for tri in ((0, 1, 2), (0, 2, 3)):
            (ax, ay, az), (bx, by, bz), (cx, cy, cz) = (scr[i] for i in tri)
            den = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
            if abs(den) < 1e-9:
                continue
            minx, maxx = int(max(0, math.floor(min(ax, bx, cx)))), int(min(W - 1, math.ceil(max(ax, bx, cx))))
            miny, maxy = int(max(0, math.floor(min(ay, by, cy)))), int(min(H - 1, math.ceil(max(ay, by, cy))))
            for yy in range(miny, maxy + 1):
                sy = yy + 0.5
                for xx in range(minx, maxx + 1):
                    sx = xx + 0.5
                    w0 = ((by - cy) * (sx - cx) + (cx - bx) * (sy - cy)) / den
                    w1 = ((cy - ay) * (sx - cx) + (ax - cx) * (sy - cy)) / den
                    w2 = 1 - w0 - w1
                    if w0 < -1e-6 or w1 < -1e-6 or w2 < -1e-6:
                        continue
                    depth = w0 * az + w1 * bz + w2 * cz   # smaller = closer to the viewer
                    if depth >= zbuf[yy][xx]:
                        continue
                    if uvs is not None:
                        u = w0 * uvs[tri[0]][0] + w1 * uvs[tri[1]][0] + w2 * uvs[tri[2]][0]
                        v = w0 * uvs[tri[0]][1] + w1 * uvs[tri[1]][1] + w2 * uvs[tri[2]][1]
                        tx = min(tw - 1, max(0, int(u * tw)))
                        ty = min(th - 1, max(0, int(v * th)))
                        r, g, b, a = bp[tx, ty]
                        if a < 128:
                            continue
                        if gp[tx, ty][3]:
                            col = (min(255, int(r * 1.08 + 12)), min(255, int(g * 1.08 + 12)), min(255, int(b * 1.08 + 12)), 255)
                        else:
                            col = (int(r * shade), int(g * shade), int(b * shade), 255)
                    else:
                        r, g, b = q["color"]
                        col = (int(r * shade), int(g * shade), int(b * shade), 255)
                    zbuf[yy][xx] = depth
                    px[xx, yy] = col
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 14], fill=(0, 0, 0, 200))
    d.text((4, 2), f"SOFTWARE RENDER - not in-game | {title}", fill=(255, 255, 255, 255))
    return img


def main():
    school, dump_path = sys.argv[1], Path(sys.argv[2])
    out = Path(sys.argv[3]) if len(sys.argv) > 3 else ROOT / "docs/art/armor"
    out.mkdir(parents=True, exist_ok=True)
    dump = json.loads(dump_path.read_text(encoding="utf-8"))
    base = Image.open(ARMOR_TEX / f"{school}_dragonsteel_plate.png").convert("RGBA")
    glow = Image.open(ARMOR_TEX / f"{school}_dragonsteel_plate_glowmask.png").convert("RGBA")
    armour = [{"bone": q["bone"], "pts": [tuple(v[:3]) for v in q["v"]], "uv": [tuple(v[3:5]) for v in q["v"]]}
              for q in dump["quads"]]
    # Author space is Bedrock's mirrored X (GeckoLib negates it in game); yaw 0 looks at the wearer's face.
    views = [("front", 0.0), ("back", math.pi), ("right side", math.pi / 2), ("three-quarter", math.pi / 4)]
    sheet_parts = []
    for name, yaw in views:
        img = render(body_quads() + [q for q in armour if q["bone"] in ALL], base, glow, yaw, f"{school} full set, {name}")
        sheet_parts.append(img)
    sheet = Image.new("RGBA", (sum(i.width for i in sheet_parts), sheet_parts[0].height), BG)
    x = 0
    for i in sheet_parts:
        sheet.paste(i, (x, 0))
        x += i.width
    sheet.save(out / f"{school}_full_set.png")
    slots = []
    for slot, bones in SLOT_BONES.items():
        slots.append(render(body_quads() + [q for q in armour if q["bone"] in bones], base, glow, math.pi / 4, f"{school} {slot}"))
    sheet = Image.new("RGBA", (sum(i.width for i in slots), slots[0].height), BG)
    x = 0
    for i in slots:
        sheet.paste(i, (x, 0))
        x += i.width
    sheet.save(out / f"{school}_slots.png")
    print(out / f"{school}_full_set.png")
    print(out / f"{school}_slots.png")


if __name__ == "__main__":
    main()
