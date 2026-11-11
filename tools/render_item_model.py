#!/usr/bin/env python
"""Software preview of vanilla JSON item models (the staves). NOT in-game screenshots.

    python tools/render_item_model.py out.png name [name ...]        turnaround: front, three-quarter, side, head
    python tools/render_item_model.py --gui out.png name [name ...]  the inventory icon through the gui transform

Orthographic and z-buffered. Vertex order, UV corners and element rotation follow vanilla's FaceBakery; faces with
Forge `forge_data` light are drawn full-bright.
"""
import json
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
A = ROOT / "src/main/resources/assets/dragonsteel_schools"
BG = (54, 57, 66, 255)
SLOT = (198, 198, 198, 255)
LIGHT = (0.35, 0.8, 0.5)

# vanilla FaceInfo: corner order per face as min (0) or max (1) picks; UVs go (u1,v1), (u1,v2), (u2,v2), (u2,v1)
FACE_VERTS = {
    "down": ((0, 0, 1), (0, 0, 0), (1, 0, 0), (1, 0, 1)),
    "up": ((0, 1, 0), (0, 1, 1), (1, 1, 1), (1, 1, 0)),
    "north": ((1, 1, 0), (1, 0, 0), (0, 0, 0), (0, 1, 0)),
    "south": ((0, 1, 1), (0, 0, 1), (1, 0, 1), (1, 1, 1)),
    "west": ((0, 1, 0), (0, 0, 0), (0, 0, 1), (0, 1, 1)),
    "east": ((1, 1, 1), (1, 0, 1), (1, 0, 0), (1, 1, 0)),
}


def rot_axis(p, axis, deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    x, y, z = p
    if axis == "x":
        return x, y * c - z * s, y * s + z * c
    if axis == "y":
        return x * c + z * s, y, -x * s + z * c
    return x * c - y * s, x * s + y * c, z


def quads(model, tex):
    size = tex.size[0]
    out = []
    for e in model["elements"]:
        lo, hi = e["from"], e["to"]
        r = e.get("rotation")
        for face, f in e["faces"].items():
            u1, v1, u2, v2 = (c * size / 16 for c in f["uv"])
            uvs = ((u1, v1), (u1, v2), (u2, v2), (u2, v1))
            pts = []
            for pick in FACE_VERTS[face]:
                p = tuple((lo, hi)[pick[i]][i] for i in range(3))
                if r and r["angle"]:
                    o = r["origin"]
                    q = rot_axis(tuple(p[i] - o[i] for i in range(3)), r["axis"], r["angle"])
                    p = tuple(q[i] + o[i] for i in range(3))
                pts.append(tuple(p[i] - 8 for i in range(3)))
            out.append((pts, uvs, "forge_data" in f or "forge_data" in e))
    return out


def draw(img, zbuf, qs, tex, xf, scale, cx, cy):
    px, tp = img.load(), tex.load()
    W, H = img.size
    tw, th = tex.size
    ln = math.sqrt(sum(c * c for c in LIGHT))
    for pts, uvs, glow in qs:
        v = [xf(p) for p in pts]
        e1 = tuple(v[1][i] - v[0][i] for i in range(3))
        e2 = tuple(v[3][i] - v[0][i] for i in range(3))
        n = (e1[1] * e2[2] - e1[2] * e2[1], e1[2] * e2[0] - e1[0] * e2[2], e1[0] * e2[1] - e1[1] * e2[0])
        if n[2] <= 1e-9:
            continue   # faces away from the camera (items are drawn with culling)
        nl = math.sqrt(sum(c * c for c in n)) or 1.0
        lit = sum(n[i] * LIGHT[i] for i in range(3)) / (nl * ln)
        shade = 1.0 if glow else 0.55 + 0.45 * max(0.0, lit)
        s = [(cx + p[0] * scale, cy - p[1] * scale, p[2]) for p in v]
        for a, b, c in ((0, 1, 2), (0, 2, 3)):
            (x0, y0, z0), (x1, y1, z1), (x2, y2, z2) = s[a], s[b], s[c]
            den = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
            if abs(den) < 1e-9:
                continue
            for yy in range(max(0, int(min(y0, y1, y2))), min(H, int(max(y0, y1, y2)) + 1)):
                for xx in range(max(0, int(min(x0, x1, x2))), min(W, int(max(x0, x1, x2)) + 1)):
                    fx, fy = xx + 0.5, yy + 0.5
                    w0 = ((y1 - y2) * (fx - x2) + (x2 - x1) * (fy - y2)) / den
                    w1 = ((y2 - y0) * (fx - x2) + (x0 - x2) * (fy - y2)) / den
                    w2 = 1 - w0 - w1
                    if w0 < -1e-6 or w1 < -1e-6 or w2 < -1e-6:
                        continue
                    z = w0 * z0 + w1 * z1 + w2 * z2
                    if z <= zbuf[yy][xx]:
                        continue
                    u = w0 * uvs[a][0] + w1 * uvs[b][0] + w2 * uvs[c][0]
                    t = w0 * uvs[a][1] + w1 * uvs[b][1] + w2 * uvs[c][1]
                    col = tp[min(tw - 1, max(0, int(u))), min(th - 1, max(0, int(t)))]
                    if col[3] == 0:
                        continue
                    zbuf[yy][xx] = z
                    px[xx, yy] = tuple(min(255, int(col[i] * shade)) for i in range(3)) + (255,)


def view(yaw, pitch):
    return lambda p: rot_axis(rot_axis(p, "y", yaw), "x", pitch)


def gui_xf(display):
    g = display.get("gui", {})
    rx, ry, rz = g.get("rotation", (0, 0, 0))
    tx, ty, tz = g.get("translation", (0, 0, 0))
    sx, sy, sz = g.get("scale", (1, 1, 1))

    def xf(p):
        q = (p[0] * sx, p[1] * sy, p[2] * sz)
        q = rot_axis(rot_axis(rot_axis(q, "z", rz), "y", ry), "x", rx)
        return q[0] + tx, q[1] + ty, q[2] + tz
    return xf


def load(name):
    model = json.loads((A / "models/item" / f"{name}.json").read_text(encoding="utf-8"))
    tex = Image.open(A / "textures" / (model["textures"]["0"].split(":", 1)[1] + ".png")).convert("RGBA")
    return model, tex


def panel(qs, tex, xf, scale, w, h, cx, cy, bg=BG):
    img = Image.new("RGBA", (w, h), bg)
    zbuf = [[-1e9] * w for _ in range(h)]
    draw(img, zbuf, qs, tex, xf, scale, cx, cy)
    return img


def gui_sheet(out, names):
    zoom = 8
    sheet = Image.new("RGBA", (len(names) * (16 * zoom + 12) + 12, 16 * zoom + 60), (139, 139, 139, 255))
    d = ImageDraw.Draw(sheet)
    for i, name in enumerate(names):
        model, tex = load(name)
        qs = quads(model, tex)
        xf = gui_xf(model.get("display", {}))
        x = 12 + i * (16 * zoom + 12)
        sheet.paste(panel(qs, tex, xf, zoom, 16 * zoom, 16 * zoom, 8 * zoom, 8 * zoom, SLOT), (x, 12))
        sheet.paste(panel(qs, tex, xf, 2, 32, 32, 16, 16, SLOT).resize((16, 16), Image.LANCZOS), (x, 16 * zoom + 18))
        d.text((x + 22, 16 * zoom + 20), name.split("_")[0], fill=(0, 0, 0, 255))
        pts = [xf(p) for q in qs for p in q[0]]
        print(name, "gui extent x %.1f..%.1f  y %.1f..%.1f  (slot is -8..8)" % (
            min(p[0] for p in pts), max(p[0] for p in pts), min(p[1] for p in pts), max(p[1] for p in pts)))
    sheet.save(out)


def turnaround(out, names):
    scale, hs = 9, 22
    pw, ph, hw, hh = 16 * scale, 46 * scale, 15 * hs, 15 * hs
    sheet = Image.new("RGBA", (3 * pw + 2 * hw + 30, len(names) * (ph + 26) + 6), (30, 32, 38, 255))
    d = ImageDraw.Draw(sheet)
    for i, name in enumerate(names):
        model, tex = load(name)
        qs = quads(model, tex)
        y = 6 + i * (ph + 26)
        d.text((8, y), f"{name}  (software preview: front, three-quarter, side; head front and three-quarter)",
               fill=(230, 230, 230, 255))
        for k, (yaw, pitch) in enumerate(((0, 0), (35, 14), (90, 0))):
            sheet.paste(panel(qs, tex, view(yaw, pitch), scale, pw, ph, pw // 2, int(ph * 0.63)), (6 + k * (pw + 4), y + 16))
        for k, (yaw, pitch) in enumerate(((0, 0), (35, 14))):
            sheet.paste(panel(qs, tex, view(yaw, pitch), hs, hw, hh, hw // 2, int(hh * 0.5 + 12.5 * hs)),
                        (3 * pw + 22 + k * (hw + 4), y + 16))
    sheet.save(out)


def main():
    args = sys.argv[1:]
    if args[0] == "--gui":
        gui_sheet(args[1], args[2:])
    else:
        turnaround(args[0], args[1:])


if __name__ == "__main__":
    main()
