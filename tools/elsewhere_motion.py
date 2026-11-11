#!/usr/bin/env python
"""Software preview of Elsewhere's moving blade in first person: python tools/elsewhere_motion.py

Writes build/preview/elsewhere_swing.png and elsewhere_scatter.png, filmstrips a tick apart.

This mirrors the motion in ElsewhereRenderer and the envelopes in ElsewhereClient so a change can be judged before
a build. The Java is the source of truth: change a number there, change it here.
"""
import math
from pathlib import Path

from PIL import Image, ImageDraw

from preview_held import IDENTITY, Raxis, Rz, T, apply, chain, display_of, render

ROOT = Path(__file__).resolve().parents[1]
TEX = ROOT / "src/main/resources/assets/dragonsteel_schools/textures/item"
PX = 1 / 32
R2 = math.sqrt(0.5)
SWING_TICKS, SCATTER_TICKS = 16, 22


def ease_out(x):
    return 1 - (1 - x) ** 3


def ease_in(x):
    return x ** 3


def ease_in_out(x):
    return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


def swing_env(a):
    """Out in 2 ticks, held while the arm swings back, snapped together by tick 12, a small overshoot to 16."""
    if a < 0 or a >= SWING_TICKS:
        return 0.0
    if a < 2:
        return ease_out(a / 2)
    if a < 7:
        return 1.0
    if a < 12:
        return 1 - ease_in((a - 7) / 5)
    return -0.15 * math.sin(math.pi * (a - 12) / 4)


def scatter_env(a):
    if a < 0 or a >= SCATTER_TICKS:
        return 0.0
    if a < 2:
        return ease_out(a / 2)
    if a < 6:
        return 1.0
    if a < 18:
        return 1 - ease_in_out((a - 6) / 12)
    return -0.12 * math.sin(math.pi * (a - 18) / 4)


def motion(t, sw, sc, side=1):
    """(tip, middle) as (cx, cy, along, across, slip, out, roll, tilt); sprite pixels and degrees.

    side (+1/-1, alternating swing to swing) flips only the twists: in first person a piece moved sideways in the
    sprite plane toward the blade's edge (-across, +slip) comes at the camera until it fills the view."""
    s = sw * side
    sin = math.sin
    tip = (25.0, 5.5,
           1.0 + 0.6 * sin(0.07 * t) + 2.0 * sw + 3.0 * sc,
           0.8 * sin(0.043 * t + 1.3) + 5.0 * sw + 7.0 * sc,
           0.0,
           0.8 * sin(0.055 * t) + 3.0 * sw + 5.0 * sc,
           3.5 * sin(0.05 * t + 0.4) + 25.0 * s + 140.0 * sc,
           6.0 * sin(0.037 * t + 2.0) + 20.0 * s + 50.0 * sc)
    # the middle swings out the other way through depth (out), never sideways in the plane (slip, -across): in
    # first person those carry it toward the camera until it fills the view
    middle = (20.0, 12.5,
              0.5 + 0.4 * sin(0.07 * t + 1.2) + 1.5 * sw + 3.0 * sc,
              0.0,
              1.0 * sin(0.031 * t + 0.6),
              -0.6 * sin(0.055 * t + 0.9) - 3.0 * sw - 5.0 * sc,
              -2.5 * sin(0.045 * t + 1.7) - 14.0 * s - 100.0 * sc,
              -4.5 * sin(0.041 * t) - 10.0 * s - 30.0 * sc)
    return tip, middle


def placement(cx, cy, along, across, slip, out, roll, tilt):
    px, py, pz = cx * PX, 1 - cy * PX, 0.5
    dx = ((along - across) * R2 + slip) * PX
    dy = (along + across) * R2 * PX
    rot = chain(Rz(roll), Raxis(tilt, -R2, R2, 0))
    return chain(T(px + dx, py + dy, pz + out * PX), rot, T(-px, -py, -pz))


def frame(t, sw, sc, arm_swing, side=1):
    tip, middle = motion(t, sw, sc, side)
    mt, mm = placement(*tip), placement(*middle)
    img = {n: Image.open(TEX / f"elsewhere_{n}.png") for n in ("tip", "tip_glow", "middle", "middle_glow", "hilt", "hilt_glow")}
    layers = [(img["hilt"], IDENTITY), (img["hilt_glow"], IDENTITY), (img["middle"], mm), (img["middle_glow"], mm),
              (img["tip"], mt), (img["tip_glow"], mt)]

    def beams(draw, project):
        for (ma, a), (mb, b) in (((mt, (23.5, 8.0)), (mm, (23.5, 10.0))), ((mm, (17.5, 15.0)), (IDENTITY, (14.5, 17.0)))):
            pa = project(apply(ma, (a[0] * PX, 1 - a[1] * PX, 0.5)))
            pb = project(apply(mb, (b[0] * PX, 1 - b[1] * PX, 0.5)))
            draw.line((pa, pb), fill=(168, 95, 255), width=7)
            draw.line((pa, pb), fill=(245, 230, 255), width=3)

    return render(layers, display_of("elsewhere"), arm_swing, extra=beams)


def strip(name, ticks, env, label):
    w, h = 480, 270
    out = Image.new("RGB", (w * len(ticks), h + 18), (0, 0, 0))
    d = ImageDraw.Draw(out)
    for i, a in enumerate(ticks):
        arm = a / 6 if 0 <= a < 6 and label == "swing" else 0.0
        e = env(a)
        im = frame(40.0 + a, e if label == "swing" else 0.0, e if label == "scatter" else 0.0, arm).resize((w, h))
        out.paste(im, (i * w, 18))
        d.text((i * w + 4, 3), f"{label} tick {a}: spread {e:+.2f}", fill=(255, 255, 255))
    path = ROOT / "build/preview" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    out.save(path)
    print(path)


def nearest(ticks, env, kind):
    """Closest any piece corner comes to the first-person camera at rest arm (blocks)."""
    pose_disp = display_of("elsewhere")
    from preview_held import first_person_pose
    pose = first_person_pose(pose_disp, 0.0)
    best = 9.0
    for a in ticks:
        e = env(a)
        for side in (1, -1):
            tip, middle = motion(40.0 + a, e if kind == "swing" else 0, e if kind == "scatter" else 0, side)
            for name, pc in (("tip", tip), ("middle", middle)):
                m = placement(*pc)
                for u, v in MASK[name]:
                    best = min(best, -apply(pose, apply(m, (u * PX, 1 - v * PX, 0.5)))[2])
    return best


def _mask(name):
    body = Image.open(TEX / f"elsewhere_{name}.png").convert("RGBA")
    glow = Image.open(TEX / f"elsewhere_{name}_glow.png").convert("RGBA")
    return [(u + du, v + dv) for u in range(32) for v in range(32)
            if body.getpixel((u, v))[3] or glow.getpixel((u, v))[3] for du in (0, 1) for dv in (0, 1)]


MASK = {}


if __name__ == "__main__":
    MASK.update({n: _mask(n) for n in ("tip", "middle")})
    print("nearest to the camera: swing %.2f, scatter %.2f (rest pose 0.44)" % (
        nearest(range(0, SWING_TICKS), swing_env, "swing"), nearest(range(0, SCATTER_TICKS), scatter_env, "scatter")))
    strip("elsewhere_swing.png", [0, 1, 3, 6, 9, 11, 13], swing_env, "swing")
    strip("elsewhere_scatter.png", [0, 2, 5, 9, 13, 17, 20], scatter_env, "scatter")
