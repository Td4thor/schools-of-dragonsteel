#!/usr/bin/env python
"""Software preview of a held 32x32 item sprite as the first-person camera sees it (no game needed).

    python tools/preview_held.py briar dawn            -> build/preview/held_<name>.png (rest and mid-swing)

Replays the client's own maths: ItemInHandRenderer's arm and swing transforms, the item model's display transform,
ItemRenderer's -0.5 centring, and the hand's fixed 70 degree projection. Each sprite pixel is drawn as its front and
back face (painter's order). It shows where the blade points and which side faces the viewer; lighting, view bobbing
and the extruded edge faces are left out. A preview, not a substitute for Tad's look in game.

render(layers, display, swing): layers are (RGBA image, 4x4 model-space matrix) pairs, so a moving item's pieces
(ElsewhereRenderer) can be previewed too; see elsewhere_motion.py.
"""
import json
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
A = ROOT / "src/main/resources/assets/dragonsteel_schools"
W, H = 960, 540


def mul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]


def chain(*ms):
    out = ms[0]
    for m in ms[1:]:
        out = mul(out, m)
    return out


def T(x, y, z):
    return [[1, 0, 0, x], [0, 1, 0, y], [0, 0, 1, z], [0, 0, 0, 1]]


def S(x, y, z):
    return [[x, 0, 0, 0], [0, y, 0, 0], [0, 0, z, 0], [0, 0, 0, 1]]


def Rx(d):
    c, s = math.cos(math.radians(d)), math.sin(math.radians(d))
    return [[1, 0, 0, 0], [0, c, -s, 0], [0, s, c, 0], [0, 0, 0, 1]]


def Ry(d):
    c, s = math.cos(math.radians(d)), math.sin(math.radians(d))
    return [[c, 0, s, 0], [0, 1, 0, 0], [-s, 0, c, 0], [0, 0, 0, 1]]


def Rz(d):
    c, s = math.cos(math.radians(d)), math.sin(math.radians(d))
    return [[c, -s, 0, 0], [s, c, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]


def Raxis(d, ax, ay, az):
    """Rotation by d degrees about a unit axis (JOML rotateAxis)."""
    c, s = math.cos(math.radians(d)), math.sin(math.radians(d))
    k = 1 - c
    return [[c + ax * ax * k, ax * ay * k - az * s, ax * az * k + ay * s, 0],
            [ay * ax * k + az * s, c + ay * ay * k, ay * az * k - ax * s, 0],
            [az * ax * k - ay * s, az * ay * k + ax * s, c + az * az * k, 0], [0, 0, 0, 1]]


def apply(m, p):
    x, y, z = p
    return tuple(m[i][0] * x + m[i][1] * y + m[i][2] * z + m[i][3] for i in range(3))


IDENTITY = T(0, 0, 0)


def first_person_pose(display, swing=0.0):
    """ItemInHandRenderer.renderArmWithItem (right arm, fully equipped) then ItemTransform.apply and the -0.5."""
    r = math.sqrt(swing)
    pre = T(-0.4 * math.sin(r * math.pi), 0.2 * math.sin(r * 2 * math.pi), -0.2 * math.sin(swing * math.pi))
    arm = T(0.56, -0.52, -0.72)
    f = math.sin(swing * swing * math.pi)
    f1 = math.sin(r * math.pi)
    attack = chain(Ry(45 - 20 * f), Rz(-20 * f1), Rx(-80 * f1), Ry(-45))
    rot, tr, sc = display["rotation"], display["translation"], display["scale"]
    disp = chain(T(tr[0] / 16, tr[1] / 16, tr[2] / 16), Rx(rot[0]), Ry(rot[1]), Rz(rot[2]), S(*sc))
    return chain(pre, arm, attack, disp, T(-0.5, -0.5, -0.5))


def render(layers, display, swing=0.0, extra=None, bg=(46, 52, 64)):
    """extra: optional callable(draw, project) to overlay beams etc."""
    pose = first_person_pose(display, swing)
    f = 1 / math.tan(math.radians(35))

    def project(p):
        x, y, z = apply(pose, p)
        z = min(z, -0.01)
        return ((f * H / W * x / -z + 1) / 2 * W, (1 - f * y / -z) / 2 * H), z

    quads = []
    for img, model in layers:
        px = img.convert("RGBA").load()
        for v in range(32):
            for u in range(32):
                c = px[u, v]
                if c[3] < 128:
                    continue
                for z, shade in ((8.5 / 16, 1.0), (7.5 / 16, 0.62)):
                    corners = [apply(model, (uu / 32, 1 - vv / 32, z)) for uu, vv in ((u, v), (u + 1, v), (u + 1, v + 1), (u, v + 1))]
                    pts = [project(p) for p in corners]
                    depth = sum(p[1] for p in pts) / 4
                    quads.append((depth, [p[0] for p in pts], tuple(int(ch * shade) for ch in c[:3])))
    quads.sort(key=lambda q: q[0])
    im = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(im)
    d.line((W / 2 - 8, H / 2, W / 2 + 8, H / 2), fill=(220, 220, 220))
    d.line((W / 2, H / 2 - 8, W / 2, H / 2 + 8), fill=(220, 220, 220))
    for _, pts, col in quads:
        d.polygon(pts, fill=col)
    if extra:
        extra(d, lambda p: project(p)[0])
    return im


def display_of(name):
    model = json.loads((A / "models/item" / f"{name}.json").read_text(encoding="utf-8"))
    return model["display"]["firstperson_righthand"]


def main(names):
    out = ROOT / "build/preview"
    out.mkdir(parents=True, exist_ok=True)
    for name in names:
        img = Image.open(A / "textures/item" / f"{name}.png")
        disp = display_of(name)
        sheet = Image.new("RGB", (W * 2, H), (0, 0, 0))
        for i, sw in enumerate((0.0, 0.5)):
            sheet.paste(render([(img, IDENTITY)], disp, sw), (i * W, 0))
        ImageDraw.Draw(sheet).text((8, 8), f"{name}: first person at rest | mid-swing (software preview)", fill=(255, 255, 255))
        sheet.save(out / f"held_{name}.png")
        print(out / f"held_{name}.png")


if __name__ == "__main__":
    main(sys.argv[1:] or ["dawn"])
