#!/usr/bin/env python
"""Software preview of Elsewhere's moving blade in first person: python tools/elsewhere_motion.py

Writes build/preview/elsewhere_swing.png, elsewhere_shatter.png and elsewhere_idle.png (filmstrips) and prints how
near any shard comes to the first-person camera.

This mirrors ElsewhereRenderer (rest drift, blinks, swing spread, the shatter, afterimages, the camera margin) and
the envelopes in ElsewhereClient, so a change can be judged before a build. The Java is the source of truth: change
a number there, change it here. The shard table comes from generate_textures.elsewhere_shards(), which also writes
ElsewhereShards.java, so the two cannot drift apart.
"""
import math
from pathlib import Path

from PIL import Image, ImageDraw

from generate_textures import elsewhere_shards
from preview_held import IDENTITY, Raxis, Rz, T, apply, chain, display_of, first_person_pose, mul, render

ROOT = Path(__file__).resolve().parents[1]
TEX = ROOT / "src/main/resources/assets/dragonsteel_schools/textures/item"
PX = 1 / 32
R2 = math.sqrt(0.5)
SWING_TICKS, SCATTER_TICKS = 17, 28
BURST, HANG, RETURN = 3.0, 8.0, 6.0
CAMERA_MARGIN = 0.26
FOCAL, SCREEN_REACH, SCREEN_WIDE, SCREEN_DRIFT, SCREEN_EDGE, ASPECT = 1.4281, 0.42, 0.9, 0.25, 0.95, 16 / 9
GHOST_STEP, GHOST_ALPHA = 0.9, (0.36, 0.22, 0.13)
EYE = (9.5, 21.5)
SHARDS = [p for p in elsewhere_shards() if p["segment"] != "hilt"]
SEGMENT = [{"tip": 0, "middle": 1, "base": 2}[p["segment"]] for p in SHARDS]


def holder(xy):
    return next(n for n, p in enumerate(SHARDS) if xy in p["own"])


UPPER_TIP, UPPER_MIDDLE, LOWER_MIDDLE, LOWER_BASE = holder((23, 7)), holder((23, 10)), holder((17, 14)), holder((14, 17))


def ease_out(x):
    return 1 - (1 - x) ** 3


def ease_in_out(x):
    return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


def swing_env(a, s0=0.0):
    if a < 0:
        return s0
    if a < 2:
        return s0 + (1 - s0) * ease_out(a / 2)
    if a < 6:
        return 1.0
    if a < 11:
        u = (a - 6) / 5
        return 1 - u * u * (1.6 - 0.6 * u)
    if a < SWING_TICKS:
        r = a - 11
        return -0.224 * math.exp(-r / 2.2) * math.sin(1.25 * r) * (1 - (r / 6) ** 4)
    return 0.0


def flight(a, stagger):
    if a <= 0:
        return 0.0
    if a < BURST:
        return ease_out(a / BURST)
    drift_end = HANG + stagger
    if a < drift_end:
        return 1 + 0.012 * (a - BURST)
    r = a - drift_end
    if r < RETURN:
        return (1 + 0.012 * (drift_end - BURST)) * (1 - ease_in_out(r / RETURN))
    return 0.0


def recall(a, stagger):
    r = a - (HANG + stagger)
    return 0.0 if r <= 0 else 1.0 if r >= RETURN else ease_in_out(r / RETURN)


def world_flight(fl, f, swirl):
    d = [fl[0] * fl[3] * PX * f, fl[1] * fl[3] * PX * f, fl[2] * fl[3] * PX * f]
    c, s = math.cos(swirl), math.sin(swirl)
    return [d[0] * c - d[1] * s, d[0] * s + d[1] * c, d[2]]


def inverse(m):
    """General 4x4 inverse (Gauss-Jordan); the hand pose carries the display's non-uniform scale."""
    a = [list(map(float, row)) + [1.0 if i == j else 0.0 for j in range(4)] for i, row in enumerate(m)]
    for c in range(4):
        piv = max(range(c, 4), key=lambda r: abs(a[r][c]))
        a[c], a[piv] = a[piv], a[c]
        k = a[c][c]
        a[c] = [v / k for v in a[c]]
        for r in range(4):
            if r != c:
                f = a[r][c]
                a[r] = [v - f * w for v, w in zip(a[r], a[c])]
    return [row[4:] for row in a]


def screen_flight(view, home, fl, f, swirl):
    eh = apply(view, home)
    depth = max(0.05, -eh[2])
    hx, hy = FOCAL / ASPECT * eh[0] / depth, FOCAL * eh[1] / depth
    ang = math.radians(fl[9]) + swirl
    reach = SCREEN_REACH * fl[3] / 12 * f * (1 + 0.5 * max(0.0, -math.cos(ang)))
    sx = hx + math.cos(ang) * reach * SCREEN_WIDE - SCREEN_DRIFT * f
    sy = hy + math.sin(ang) * reach
    hold = min(1.0, f)
    sx += (max(-SCREEN_EDGE, min(SCREEN_EDGE, sx)) - sx) * hold
    sy += (max(-SCREEN_EDGE, min(SCREEN_EDGE, sy)) - sy) * hold
    z = max(CAMERA_MARGIN, depth * (1 - 0.25 * fl[2] * f))
    m = apply(inverse(view), (sx * z * ASPECT / FOCAL, sy * z / FOCAL, -z))
    return [m[k] - home[k] for k in range(3)]


def wobble(a, stagger):
    r = a - (HANG + stagger + RETURN)
    if r < 0 or r > 6:
        return 0.0
    return 12 * math.exp(-r / 1.6) * math.sin(2.4 * r)


def tether(a, stagger):
    recall = HANG + stagger
    if a <= 0 or a >= recall + RETURN:
        return 0.0
    if a < recall:
        return 0.3 * min(1.0, a / 1.5)
    return 0.3 + 0.6 * (a - recall) / RETURN


def hsh(x):
    v = math.sin(x * 12.9898) * 43758.5453
    return v - math.floor(v)


def blink(tt):
    k = math.floor(tt / 100)
    u = (tt - (100 * k + 15 + 55 * hsh(k))) / 14
    if u < 0 or u >= 1:
        return (-1, 0.0, 0.0, 0.0)
    return (0 if hsh(k + 0.37) < 0.5 else 1, 1 - ease_in_out(u), 1 if hsh(k + 0.71) < 0.5 else -1, 1 if hsh(k + 0.53) < 0.5 else -1)


def segment(cx, cy, along, across, slip, out, roll, tilt):
    px, py = cx * PX, 1 - cy * PX
    dx = ((along - across) * R2 + slip) * PX
    dy = (along + across) * R2 * PX
    return chain(T(px + dx, py + dy, 0.5 + out * PX), Rz(roll), Raxis(tilt, -R2, R2, 0), T(-px, -py, -0.5))


def frame_mats(t, swing_age, scatter_age, side=1, back=0.0, view=None, s0=(0.0, 0.0)):
    """Every shard's matrix at t - back (ElsewhereRenderer.Frame.at). Returns (mats, max flight, swing)."""
    tt = t - back
    sw_tip = swing_env(swing_age - back - 0.7, s0[0])
    sw_mid = swing_env(swing_age - back, s0[1])
    b = blink(tt)
    b_tip = b[1] if b[0] == 0 else 0.0
    b_mid = b[1] if b[0] == 1 else 0.0
    s = math.sin
    tip = segment(25.0, 5.5,
                  1.0 + 0.45 * s(tt * 0.07) + 0.2 * s(tt * 0.173 + 2.1) + 2.0 * sw_tip,
                  0.6 * s(tt * 0.043 + 1.3) + 0.25 * s(tt * 0.131) + 5.0 * sw_tip + 1.6 * b_tip,
                  0.0,
                  0.6 * s(tt * 0.055) + 0.25 * s(tt * 0.149 + 0.7) + 3.0 * sw_tip + 1.3 * b[2] * b_tip,
                  3.0 * s(tt * 0.05 + 0.4) + 1.2 * s(tt * 0.161 + 1.9) + 25.0 * side * sw_tip + 7.0 * b[3] * b_tip,
                  5.0 * s(tt * 0.037 + 2.0) + 2.0 * s(tt * 0.113) + 20.0 * side * sw_tip)
    middle = segment(20.0, 12.5,
                     0.5 + 0.3 * s(tt * 0.07 + 1.2) + 0.15 * s(tt * 0.19) + 1.5 * sw_mid,
                     1.6 * b_mid,
                     0.8 * s(tt * 0.031 + 0.6),
                     -0.5 * s(tt * 0.055 + 0.9) - 0.2 * s(tt * 0.137 + 2.4) - 3.0 * sw_mid + 1.3 * b[2] * b_mid,
                     -2.2 * s(tt * 0.045 + 1.7) - 0.9 * s(tt * 0.157) - 14.0 * side * sw_mid + 7.0 * b[3] * b_mid,
                     -4.0 * s(tt * 0.041) - 1.5 * s(tt * 0.121 + 1.1) - 10.0 * side * sw_mid)
    segs = (tip, middle, IDENTITY)
    a = scatter_age - back
    mats, max_flight = [], 0.0
    for i, p in enumerate(SHARDS):
        seg = segs[SEGMENT[i]]
        fl = p["flight"]
        f = flight(a, fl[8])
        rock = wobble(a, fl[8])
        max_flight = max(max_flight, f)
        if f == 0 and rock == 0:
            mats.append(seg)
            continue
        cx, cy = p["centre"]
        home = apply(seg, (cx * PX, 1 - cy * PX, 0.5))
        swirl = math.radians(80) * recall(a, fl[8]) * (1 if i % 2 == 0 else -1)
        d = world_flight(fl, f, swirl) if view is None else screen_flight(view, home, fl, f, swirl)
        turn = f if f <= 1 else 1 + 4 * (f - 1)
        spin = Raxis(fl[7] * turn + rock, fl[4], fl[5], fl[6])
        mats.append(chain(T(home[0] + d[0], home[1] + d[1], home[2] + d[2]), spin, T(-home[0], -home[1], -home[2]), seg))
    return mats, max_flight, max(abs(sw_tip), abs(sw_mid))


IMAGES = {}


def img(name):
    if name not in IMAGES:
        path = TEX / f"{name}.png"
        IMAGES[name] = Image.open(path).convert("RGBA") if path.exists() else None
    return IMAGES[name]


def ghost_of(im, alpha):
    """An afterimage: the sprite tinted violet; render() draws pixels at alpha >= 128, so fade by dimming."""
    out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    src, dst = im.load(), out.load()
    for y in range(im.size[1]):
        for x in range(im.size[0]):
            c = src[x, y]
            if c[3] >= 128:
                k = alpha * 2.2
                dst[x, y] = (int(46 + (c[0] * 0.8 - 46) * k), int(52 + (c[1] * 0.58 - 52) * k), int(64 + (c[2] - 64) * k), 255)
    return out


def frame(t, swing_age, scatter_age, arm_swing, side=1, ghosts=True):
    disp = display_of("elsewhere")
    view = first_person_pose(disp, arm_swing)
    now, max_flight, sw = frame_mats(t, swing_age, scatter_age, side, 0.0, view)
    layers = [(img("elsewhere_hilt"), IDENTITY), (img("elsewhere_hilt_glow"), IDENTITY)]
    if ghosts:
        for k, alpha in reversed(list(enumerate(GHOST_ALPHA))):
            then, _, _ = frame_mats(t, swing_age, scatter_age, side, GHOST_STEP * (k + 1), view)
            for i, p in enumerate(SHARDS):
                c = (p["centre"][0] * PX, 1 - p["centre"][1] * PX, 0.5)
                c2 = ((p["centre"][0] + 2.5) * PX, 1 - p["centre"][1] * PX, 0.5)
                moved = max(math.dist(apply(now[i], q), apply(then[i], q)) for q in (c, c2)) / PX
                strength = alpha * max(0.0, min(1.0, (moved - 0.8) / 2.5))
                if strength >= 0.01:
                    for name in (p["name"], p["name"] + "_glow"):
                        if img(name) is not None:
                            layers.append((ghost_of(img(name), strength), then[i]))
    for i, p in enumerate(SHARDS):
        for name in (p["name"], p["name"] + "_glow"):
            if img(name) is not None:
                layers.append((img(name), now[i]))
    fade = 1 - min(1.0, max(0.0, max_flight * 5))

    def light(draw, project):
        def pt(m, sx, sy):
            return project(apply(m, (sx * PX, 1 - sy * PX, 0.5)))
        if fade > 0:
            for a, b in (((now[UPPER_TIP], 23.5, 8.0), (now[UPPER_MIDDLE], 23.5, 10.0)),
                         ((now[LOWER_MIDDLE], 17.5, 15.0), (now[LOWER_BASE], 14.5, 17.0))):
                pa, pb = pt(*a), pt(*b)
                draw.line((pa, pb), fill=tuple(int(46 + (c - 46) * fade) for c in (168, 95, 255)), width=7)
                draw.line((pa, pb), fill=tuple(int(46 + (c - 46) * fade) for c in (245, 230, 255)), width=3)
        eye = pt(IDENTITY, *EYE)
        for i, p in enumerate(SHARDS):
            al = tether(scatter_age, p["flight"][8]) * min(1.0, 2 * flight(scatter_age, p["flight"][8]))
            if al > 0:
                draw.line((eye, pt(now[i], *p["centre"])), fill=tuple(int(46 + (c - 46) * al) for c in (240, 220, 255)), width=2)

    return render(layers, disp, arm_swing, extra=light)


def strip(name, shots, title):
    """shots: (label, t, swing_age, scatter_age, arm_swing)."""
    w, h = 480, 270
    cols = min(len(shots), 4)
    rows = (len(shots) + cols - 1) // cols
    out = Image.new("RGB", (w * cols, (h + 18) * rows + 18), (0, 0, 0))
    d = ImageDraw.Draw(out)
    d.text((4, 3), title, fill=(255, 255, 255))
    for i, (label, t, sa, ca, arm) in enumerate(shots):
        x, y = (i % cols) * w, 18 + (i // cols) * (h + 18)
        out.paste(frame(t, sa, ca, arm).resize((w, h)), (x, y + 18))
        d.text((x + 4, y + 3), label, fill=(255, 255, 255))
    path = ROOT / "build/preview" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    out.save(path)
    print(path)


def mask(name):
    m = []
    for layer in (name, name + "_glow"):
        im = img(layer)
        if im is not None:
            m += [(u + du, v + dv) for u in range(32) for v in range(32) if im.getpixel((u, v))[3] for du in (0, 1) for dv in (0, 1)]
    return m


def nearest():
    """Closest any shard corner comes to the camera (blocks): over the swing (both sides) and the shatter."""
    view = first_person_pose(display_of("elsewhere"), 0.0)
    masks = [mask(p["name"]) for p in SHARDS]
    out = {}
    for kind, ticks in (("swing", [x * 0.5 for x in range(2 * SWING_TICKS)]), ("shatter", [x * 0.5 for x in range(2 * SCATTER_TICKS)])):
        best = 9.0
        for a in ticks:
            for side in (1, -1):
                mats, _, _ = frame_mats(40.0 + a, a if kind == "swing" else 1e9, a if kind == "shatter" else 1e9, side, 0.0, view)
                for i, m in enumerate(mats):
                    full = mul(view, m)
                    for u, v in masks[i]:
                        best = min(best, -apply(full, (u * PX, 1 - v * PX, 0.5))[2])
        out[kind] = best
    rest, _, _ = frame_mats(40.0, 1e9, 1e9, 1, 0.0, view)
    out["rest"] = min(-apply(mul(view, m), (u * PX, 1 - v * PX, 0.5))[2] for i, m in enumerate(rest) for u, v in masks[i])
    return out


def on_screen(ticks):
    """Per shatter tick: how many shards have their centre on screen (|ndc| <= 1), out of all."""
    view = first_person_pose(display_of("elsewhere"), 0.0)
    out = []
    for a in ticks:
        mats, _, _ = frame_mats(40.0 + a, 1e9, a, 1, 0.0, view)
        n = 0
        for i, m in enumerate(mats):
            x, y, z = apply(mul(view, m), (SHARDS[i]["centre"][0] * PX, 1 - SHARDS[i]["centre"][1] * PX, 0.5))
            n += abs(FOCAL / ASPECT * x / -z) <= 1 and abs(FOCAL * y / -z) <= 1
        out.append((a, n))
    return out


if __name__ == "__main__":
    print("shards on screen (tick, count of %d): %s" % (len(SHARDS), on_screen([0, 1.5, 3, 6, 9, 12, 15, 18, 21])))
    print("nearest to the camera (blocks): " + ", ".join(f"{k} {v:.2f}" for k, v in nearest().items()))
    N = 1e9
    strip("elsewhere_swing.png", [(f"swing tick {a}", 40.0 + a, a, N, a / 6 if a < 6 else 0.0) for a in (0, 1.5, 3, 6, 9, 11, 13, 15)],
          "Elsewhere swing (software preview, first person)")
    strip("elsewhere_shatter.png", [(f"shatter tick {a}", 40.0 + a, N, a, 0.0) for a in (1, 3, 7, 10, 12.5, 15, 18, 22)],
          "Elsewhere shatter on dodge (software preview, first person; the world burst is not drawn)")
    strip("elsewhere_idle.png", [(f"rest t={t}", t, N, N, 0.0) for t in (0, 25, 50, 75)],
          "Elsewhere at rest (software preview)")
