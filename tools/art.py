"""Original vector illustrations for Property Rent Hub.

Draws ordinary furnished offices (desks, office chairs and laptops) as SVG
files in art/: the homepage strip (panorama.svg), one office scene for each
location page, a private office interior and the logo mark.
tools/make_images.py turns them into WebP/AVIF images.

The drawings are generic on purpose. They show the kind of office on offer,
not a particular office, building or landmark, and the site labels them as
illustrations wherever they appear.
"""
import math
import os
import random

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "art")

NAVY900 = "#0A1A31"
NAVY800 = "#0E2240"
NAVY700 = "#16305A"
NAVY600 = "#22406B"
NAVY500 = "#3A5A86"
NAVY400 = "#5E7BA3"
NAVY300 = "#93A7C3"
MIST = "#E7EDF5"
MIST2 = "#F3F6FA"
BRASS = "#B58A3C"
BRASS_LIGHT = "#D9B76E"
WOOD = "#8C6A42"
WOOD_TOP = "#E6D6BC"
LEAF = "#2F6B4F"
LEAF2 = "#3F8462"
SILVER = "#C7D1DF"
SILVER_DARK = "#A8B5C8"
DESK_TOP = "#F6F8FB"
PANEL = "#D6DFEB"


# ------------------------------------------------------------------ helpers

def f(v):
    s = f"{v:.1f}"
    return s[:-2] if s.endswith(".0") else s


def rect(x, y, w, h, fill, rx=0, extra=""):
    r = f' rx="{f(rx)}"' if rx else ""
    return f'<rect x="{f(x)}" y="{f(y)}" width="{f(w)}" height="{f(h)}"{r} fill="{fill}"{extra}/>'


def poly(points, fill, extra=""):
    pts = " ".join(f"{f(x)},{f(y)}" for x, y in points)
    return f'<polygon points="{pts}" fill="{fill}"{extra}/>'


def circle(cx, cy, r, fill, extra=""):
    return f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(r)}" fill="{fill}"{extra}/>'


def ellipse(cx, cy, rx, ry, fill, extra=""):
    return f'<ellipse cx="{f(cx)}" cy="{f(cy)}" rx="{f(rx)}" ry="{f(ry)}" fill="{fill}"{extra}/>'


def opa(v):
    return f' fill-opacity="{v}"'


def far_skyline(x0, x1, base, rng, op=0.3, hmin=30, hmax=110, wmin=14, wmax=34):
    """Distant, generic buildings seen through a window."""
    d = []
    x = x0
    while x < x1:
        w = rng.uniform(wmin, wmax)
        h = rng.uniform(hmin, hmax)
        d.append(f"M{f(x)},{f(base)}V{f(base-h)}h{f(w)}V{f(base)}Z")
        x += w + rng.uniform(2, 14)
    return f'<path d="{"".join(d)}" fill="{NAVY300}" fill-opacity="{op}"/>'


class Scene:
    """A room seen from the front and slightly above: wall, floor and skirting."""

    def __init__(self, W, H, floor_y, prefix="", seed=1, cls="", standalone=True, preserve=""):
        self.W, self.H, self.floor_y, self.p = W, H, floor_y, prefix
        self.rng = random.Random(seed)
        self.standalone, self.cls, self.preserve = standalone, cls, preserve
        self.n = 0
        p = prefix
        self.defs = [
            f'<linearGradient id="{p}wall" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#FFFFFF"/><stop offset="1" stop-color="{MIST2}"/></linearGradient>',
            f'<linearGradient id="{p}floor" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#DCE3ED"/><stop offset="1" stop-color="#C8D3E1"/></linearGradient>',
            f'<linearGradient id="{p}glass" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#F9FBFD"/><stop offset="1" stop-color="#E1E9F3"/></linearGradient>',
            f'<linearGradient id="{p}disp" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{NAVY500}"/><stop offset="1" stop-color="{NAVY700}"/></linearGradient>',
        ]
        self.body = [rect(0, 0, W, floor_y, f"url(#{p}wall)"),
                     rect(0, floor_y, W, H - floor_y, f"url(#{p}floor)"),
                     rect(0, floor_y - 12, W, 12, "#E0E7F0"),
                     rect(0, floor_y, W, 2, "#C2CDDB")]

    def add(self, *parts):
        self.body.extend(parts)

    def uid(self, base):
        self.n += 1
        return f"{self.p}{base}{self.n}"

    def svg(self):
        attrs = 'xmlns="http://www.w3.org/2000/svg" ' if self.standalone else ""
        cls = f'class="{self.cls}" ' if self.cls else ""
        pa = f' preserveAspectRatio="{self.preserve}"' if self.preserve else ""
        hidden = "" if self.standalone else ' aria-hidden="true" focusable="false"'
        return (f'<svg {attrs}{cls}viewBox="0 0 {self.W} {self.H}"{pa}{hidden}>'
                f'<defs>{"".join(self.defs)}</defs>{"".join(self.body)}</svg>')


# --------------------------------------------------------------- the room

def window(sc, x, y, w, h, panes=3, view=0.3, blinds=(), transom=True, sill=True):
    cid = sc.uid("win")
    sc.defs.append(f'<clipPath id="{cid}"><rect x="{f(x)}" y="{f(y)}" width="{f(w)}" height="{f(h)}"/></clipPath>')
    out = [rect(x, y, w, h, f"url(#{sc.p}glass)")]
    if view:
        out.append(f'<g clip-path="url(#{cid})">'
                   + far_skyline(x - 30, x + w + 30, y + h, sc.rng, op=view, hmin=h * 0.14, hmax=h * 0.46,
                                 wmin=max(14, w * 0.022), wmax=max(28, w * 0.05)) + '</g>')
    pw = w / panes
    for i, frac in blinds:
        bx, bh = x + i * pw, h * frac
        out.append(rect(bx, y, pw, bh, MIST2))
        yy = y + 10
        while yy < y + bh - 8:
            out.append(rect(bx, yy, pw, 1.5, NAVY300, extra=opa(".55")))
            yy += 10
        out.append(rect(bx + 3, y + bh - 7, pw - 6, 7, NAVY400, rx=2))
    if transom:
        out.append(rect(x, y + h * 0.72, w, 6, NAVY700))
    for k in range(1, panes):
        out.append(rect(x + k * pw - 4, y, 8, h, NAVY700))
    out.append(f'<rect x="{f(x-6)}" y="{f(y-6)}" width="{f(w+12)}" height="{f(h+12)}" fill="none" stroke="{NAVY800}" stroke-width="12"/>')
    if sill:
        out.append(rect(x - 20, y + h + 6, w + 40, 10, NAVY800, rx=2))
    return "".join(out)


def pendant(cx, drop, s=1.0):
    return (rect(cx - 1.5 * s, 0, 3 * s, drop, NAVY800)
            + poly([(cx - 15 * s, drop), (cx + 15 * s, drop), (cx + 42 * s, drop + 38 * s), (cx - 42 * s, drop + 38 * s)], NAVY800)
            + rect(cx - 42 * s, drop + 36 * s, 84 * s, 5 * s, BRASS, rx=2 * s)
            + ellipse(cx, drop + 43 * s, 24 * s, 5 * s, "#FFF3D6"))


def clock(cx, cy, r):
    out = [circle(cx, cy, r, "#FFFFFF", extra=f' stroke="{NAVY800}" stroke-width="{f(r*0.16)}"')]
    for k in range(12):
        a = math.radians(k * 30)
        r1, r2 = r * (0.66 if k % 3 == 0 else 0.74), r * 0.84
        out.append(f'<path d="M{f(cx+math.cos(a)*r1)},{f(cy+math.sin(a)*r1)}L{f(cx+math.cos(a)*r2)},{f(cy+math.sin(a)*r2)}" '
                   f'stroke="{NAVY400}" stroke-width="{f(r*0.06)}" stroke-linecap="round"/>')
    for ang, ln, wd in ((-150, 0.42, 0.1), (-30, 0.62, 0.07)):
        a = math.radians(ang)
        out.append(f'<path d="M{f(cx)},{f(cy)}L{f(cx+math.cos(a)*r*ln)},{f(cy+math.sin(a)*r*ln)}" stroke="{NAVY900}" '
                   f'stroke-width="{f(r*wd)}" stroke-linecap="round"/>')
    out.append(circle(cx, cy, r * 0.08, BRASS))
    return "".join(out)


def whiteboard(x, y, w, h):
    out = [rect(x, y, w, h, "#FFFFFF", extra=f' stroke="{NAVY300}" stroke-width="8"')]
    bx, by = x + 44, y + h - 46
    for k, bh in enumerate((52, 84, 66, 112)):
        out.append(rect(bx + k * 36, by - bh, 24, bh, BRASS if k == 3 else BRASS_LIGHT))
    out.append(rect(bx - 10, by, 160, 3, NAVY400))
    out.append(f'<path d="M{f(bx-4)},{f(by-120)} C{f(bx+40)},{f(by-150)} {f(bx+90)},{f(by-112)} {f(bx+150)},{f(by-160)}" '
               f'stroke="{NAVY500}" stroke-width="4" fill="none" stroke-linecap="round"/>')
    tx = x + w * 0.5
    for k in range(4):
        out.append(rect(tx, y + 46 + k * 26, w * 0.4 - k * 22, 7, NAVY400, rx=3.5))
    for k, col in enumerate((BRASS_LIGHT, "#BFD8C9", "#F2DDB0")):
        out.append(rect(tx + k * 52, y + h - 96, 40, 40, col, extra=f' transform="rotate({(-4, 3, -2)[k]} {f(tx+k*52+20)} {f(y+h-76)})"'))
    out.append(rect(x + w * 0.3, y + h + 4, w * 0.4, 9, NAVY400, rx=3))
    out.append(rect(x + w * 0.34, y + h - 2, 34, 7, BRASS, rx=2))
    return "".join(out)


def binder_shelf(x, y, w, rng):
    out = []
    bx = x + 12
    cols = [NAVY600, NAVY500, NAVY700, BRASS, NAVY400, NAVY600]
    while bx < x + w - 34:
        bw, bh = rng.uniform(20, 28), rng.uniform(66, 90)
        out.append(rect(bx, y - bh, bw, bh, rng.choice(cols)))
        out.append(rect(bx + bw * 0.22, y - bh + 12, bw * 0.56, 14, "#FFFFFF", extra=opa(".75")))
        bx += bw + 3
    out.append(rect(x, y, w, 10, NAVY800))
    for kx in (x + 20, x + w - 34):
        out.append(rect(kx, y + 10, 14, 22, NAVY800))
    return "".join(out)


def wall_art(x, y, w, h, variant=0):
    out = [rect(x, y, w, h, MIST2, extra=f' stroke="{NAVY800}" stroke-width="8"')]
    if variant == 0:
        out.append(circle(x + w * 0.62, y + h * 0.4, min(w, h) * 0.22, BRASS_LIGHT))
        out.append(rect(x + w * 0.16, y + h * 0.5, w * 0.36, h * 0.34, NAVY500))
        out.append(f'<path d="M{f(x+w*0.12)},{f(y+h*0.86)} Q{f(x+w*0.5)},{f(y+h*0.58)} {f(x+w*0.88)},{f(y+h*0.86)}" stroke="{LEAF2}" stroke-width="{f(w*0.05)}" fill="none"/>')
    else:
        for k in range(3):
            out.append(rect(x + w * 0.18, y + h * (0.18 + k * 0.22), w * (0.64 - k * 0.14), h * 0.12, (NAVY500, BRASS_LIGHT, NAVY300)[k]))
    return "".join(out)


def cabinet(x, base_y, w, h, drawers=3):
    out = [rect(x, base_y - h, w, h, NAVY600)]
    dh = (h - 8) / drawers
    for k in range(drawers):
        dy = base_y - h + 8 + k * dh
        out.append(rect(x + 8, dy, w - 16, dh - 8, NAVY500))
        out.append(rect(x + w / 2 - 16, dy + (dh - 8) / 2 - 3, 32, 6, BRASS_LIGHT, rx=3))
    out.append(rect(x - 4, base_y - h - 8, w + 8, 10, NAVY800, rx=2))
    return "".join(out)


def glass_partition(x, w, top_y, base_y):
    band = top_y + (base_y - top_y) * 0.42
    return (rect(x, top_y, w, base_y - top_y, "#D9E4F1", extra=opa(".6"))
            + rect(x, band, w, 48, "#FFFFFF", extra=opa(".75"))
            + rect(x, band + 21, w, 4, BRASS)
            + rect(x - 4, top_y, 8, base_y - top_y, NAVY400) + rect(x + w - 4, top_y, 8, base_y - top_y, NAVY400)
            + rect(x - 4, top_y - 6, w + 8, 8, NAVY400) + rect(x - 4, base_y - 6, w + 8, 8, NAVY400))


def wall_screen(sc, x, y, w, h):
    out = [rect(x, y, w, h, NAVY900, rx=8), rect(x + 10, y + 10, w - 20, h - 20, f"url(#{sc.p}disp)", rx=3)]
    out.append(rect(x + 28, y + 26, w * 0.34, 9, "#FFFFFF", extra=opa(".75"), rx=4.5))
    base = y + h - 34
    bars = (0.34, 0.5, 0.42, 0.66, 0.58, 0.8)
    bw = (w * 0.52) / len(bars)
    for k, v in enumerate(bars):
        bh = (h - 96) * v
        out.append(rect(x + 30 + k * bw, base - bh, bw * 0.66, bh, BRASS_LIGHT if k == len(bars) - 1 else "#FFFFFF", extra="" if k == len(bars) - 1 else opa(".45")))
    rx0 = x + w * 0.64
    out.append(circle(rx0 + w * 0.14, y + h * 0.56, h * 0.2, "#FFFFFF", extra=opa(".22")))
    out.append(f'<path d="M{f(rx0+w*0.14)},{f(y+h*0.56)} L{f(rx0+w*0.14)},{f(y+h*0.56-h*0.2)} A{f(h*0.2)},{f(h*0.2)} 0 0 1 {f(rx0+w*0.14+h*0.2)},{f(y+h*0.56)} Z" fill="{BRASS_LIGHT}"/>')
    out.append(rect(x + w / 2 - 6, y + h, 12, 16, NAVY800))
    return "".join(out)


def rug(cx, cy, w, h):
    return rect(cx - w / 2, cy - h / 2, w, h, NAVY300, extra=opa(".28"), rx=h / 2)


def plant(cx, base_y, s=1.0, pot=NAVY800, kind="fan", seed=3):
    out = []
    ph, pt, pb = 70 * s, 74 * s, 58 * s
    top = base_y - ph
    if kind == "fan":
        for k in range(11):
            a = math.radians(-165 + k * 15)
            L = (150 + (k % 3) * 24) * s
            ex, ey = cx + math.cos(a) * L * 0.8, top + math.sin(a) * L
            qx, qy = cx + math.cos(a) * L * 0.22, top + math.sin(a) * L * 0.78
            out.append(f'<path d="M{f(cx)},{f(top+6*s)} Q{f(qx)},{f(qy)} {f(ex)},{f(ey)}" stroke="{LEAF if k % 2 else LEAF2}" '
                       f'stroke-width="{f(13*s)}" fill="none" stroke-linecap="round"/>')
    else:
        rng = random.Random(seed)
        n = 16 if kind == "bush" else 9
        spread, lift = (54, 96) if kind == "bush" else (34, 48)
        for k in range(n):
            lx = cx + rng.uniform(-spread, spread) * s
            ly = top - rng.uniform(6, lift) * s
            rx_, ry_ = rng.uniform(16, 26) * s, rng.uniform(8, 13) * s
            out.append(f'<ellipse cx="{f(lx)}" cy="{f(ly)}" rx="{f(rx_)}" ry="{f(ry_)}" transform="rotate({rng.uniform(-55, 55):.0f} {f(lx)} {f(ly)})" '
                       f'fill="{LEAF if k % 2 else LEAF2}"/>')
    out.append(poly([(cx - pt / 2, top), (cx + pt / 2, top), (cx + pb / 2, base_y), (cx - pb / 2, base_y)], pot))
    out.append(rect(cx - pt / 2 - 3 * s, top - 6 * s, pt + 6 * s, 9 * s, pot, rx=3 * s))
    return "".join(out)


# --------------------------------------------------------------- furniture

def desk(x, w, front_y, feet_y, depth=44, top=DESK_TOP, edge=NAVY800, legs=NAVY800, pedestal=None, panel=True):
    """A desk seen from the front and a little above: the top shows as a band."""
    out = [rect(x, front_y - depth, w, depth, top),
           rect(x, front_y - depth, w, 3, "#D2DBE7"),
           rect(x - 4, front_y, w + 8, 12, edge, rx=2)]
    leg_top = front_y + 12
    if panel:
        out.append(rect(x + 26, leg_top, w - 52, (feet_y - leg_top) * 0.45, NAVY300, extra=opa(".3")))
    for lx in (x + 8, x + w - 20):
        out.append(rect(lx, leg_top, 12, feet_y - leg_top, legs))
        out.append(rect(lx - 6, feet_y - 4, 24, 6, legs, rx=2))
    if pedestal is not None:
        ph = feet_y - leg_top - 10
        out.append(rect(pedestal, leg_top, 120, ph, NAVY600))
        for k in range(3):
            dy = leg_top + 8 + k * ph / 3
            out.append(rect(pedestal + 8, dy, 104, ph / 3 - 12, NAVY500))
            out.append(rect(pedestal + 44, dy + (ph / 3 - 12) / 2 - 3, 32, 6, BRASS_LIGHT, rx=3))
    return "".join(out)


def back_panel(x, w, bottom, h=58, dividers=()):
    """Fabric screen along the back of a bench desk, with low side dividers."""
    out = [rect(x, bottom - h, w, h, PANEL), rect(x, bottom - h, w, 5, BRASS)]
    for dx in dividers:
        out.append(rect(dx - 5, bottom - h, 10, h + 30, "#C9D4E3"))
        out.append(rect(dx - 5, bottom - h, 10, 5, BRASS))
    return "".join(out)


def laptop(sc, cx, y, s=1.0, screen_cls=""):
    """Open laptop seen from the user's side; y is the hinge line on the desk."""
    sw, sh = 124 * s, 80 * s
    out = [rect(cx - sw / 2, y - sh, sw, sh, NAVY900, rx=6 * s)]
    ix, iy, iw = cx - sw / 2 + 13 * s, y - sh + 14 * s, sw - 26 * s
    disp = [rect(cx - sw / 2 + 6 * s, y - sh + 6 * s, sw - 12 * s, sh - 13 * s, f"url(#{sc.p}disp)", rx=2 * s),
            rect(ix, iy, iw * 0.55, 5 * s, "#FFFFFF", extra=opa(".7"), rx=2.5 * s),
            rect(ix, iy + 12 * s, iw, 3.5 * s, "#FFFFFF", extra=opa(".32"), rx=1.75 * s),
            rect(ix, iy + 20 * s, iw * 0.78, 3.5 * s, "#FFFFFF", extra=opa(".32"), rx=1.75 * s),
            rect(ix, iy + 32 * s, iw * 0.34, 20 * s, BRASS_LIGHT, rx=2 * s),
            rect(ix + iw * 0.4, iy + 32 * s, iw * 0.6, 20 * s, "#FFFFFF", extra=opa(".2"), rx=2 * s)]
    cls = f' class="{screen_cls}"' if screen_cls else ""
    out.append(f'<g{cls}>{"".join(disp)}</g>')
    bb, bf, bh = sw, sw * 1.14, 13 * s
    out.append(poly([(cx - bb / 2, y), (cx + bb / 2, y), (cx + bf / 2, y + bh), (cx - bf / 2, y + bh)], SILVER))
    out.append(poly([(cx - bb * 0.42, y + 2.5 * s), (cx + bb * 0.42, y + 2.5 * s), (cx + bf * 0.4, y + bh * 0.6), (cx - bf * 0.4, y + bh * 0.6)], SILVER_DARK))
    out.append(rect(cx - bf / 2, y + bh, bf, 3 * s, NAVY400, rx=1.5 * s))
    return "".join(out)


def laptop_back(cx, y, s=1.0):
    """Open laptop seen from behind its screen."""
    sw, sh = 118 * s, 76 * s
    return (rect(cx - sw / 2, y - sh, sw, sh, SILVER, rx=6 * s)
            + rect(cx - sw / 2, y - sh, sw, 4 * s, "#FFFFFF", extra=opa(".55"), rx=2 * s)
            + circle(cx, y - sh / 2, 6.5 * s, "#FFFFFF", extra=opa(".8"))
            + rect(cx - sw * 0.56, y - 3 * s, sw * 1.12, 6 * s, NAVY400, rx=3 * s))


def monitor(sc, cx, y, s=1.0):
    sw, sh = 186 * s, 112 * s
    top = y - 42 * s - sh
    out = [rect(cx - 8 * s, y - 44 * s, 16 * s, 44 * s, NAVY800), rect(cx - 42 * s, y - 6 * s, 84 * s, 8 * s, NAVY800, rx=3 * s),
           rect(cx - sw / 2, top, sw, sh, NAVY900, rx=6 * s),
           rect(cx - sw / 2 + 7 * s, top + 7 * s, sw - 14 * s, sh - 14 * s, f"url(#{sc.p}disp)", rx=2 * s)]
    px, py = cx - sw / 2 + 22 * s, top + sh - 24 * s
    pts = [(0, 0.1), (0.18, 0.32), (0.34, 0.24), (0.52, 0.5), (0.7, 0.44), (0.88, 0.72)]
    d = "M" + " L".join(f"{f(px + a * (sw - 44 * s))},{f(py - b * (sh - 50 * s))}" for a, b in pts)
    out.append(f'<path d="{d}" stroke="{BRASS_LIGHT}" stroke-width="{f(4*s)}" fill="none" stroke-linejoin="round"/>')
    out.append(rect(cx - sw / 2 + 20 * s, top + 18 * s, sw * 0.4, 6 * s, "#FFFFFF", extra=opa(".7"), rx=3 * s))
    return "".join(out)


def chair_back(cx, top_y, feet_y, s=1.0, color=NAVY700, seat=NAVY800, frame=NAVY900, tall=False):
    """Office chair seen from behind, pushed up to a desk."""
    bw, bh = 104 * s, (124 if tall else 100) * s
    seat_y = top_y + bh + 6 * s
    out = []
    for side in (-1, 1):
        ax = cx + side * 57 * s
        out.append(rect(ax - 5 * s, seat_y - 34 * s, 10 * s, 36 * s, frame, rx=3 * s))
        out.append(rect(ax - 15 * s, seat_y - 40 * s, 30 * s, 9 * s, frame, rx=4.5 * s))
    out.append(rect(cx - 8 * s, top_y + bh - 8 * s, 16 * s, 20 * s, frame))
    out.append(rect(cx - bw / 2, top_y, bw, bh, color, rx=26 * s))
    out.append(rect(cx - bw / 2 + 11 * s, top_y + 15 * s, 7 * s, bh - 36 * s, "#FFFFFF", extra=opa(".16"), rx=3.5 * s))
    out.append(rect(cx - 62 * s, seat_y, 124 * s, 22 * s, seat, rx=11 * s))
    base_y = feet_y - 16 * s
    out.append(rect(cx - 6 * s, seat_y + 20 * s, 12 * s, base_y - seat_y - 20 * s, frame))
    out.append(rect(cx - 15 * s, seat_y + 20 * s, 30 * s, 10 * s, frame, rx=3 * s))
    out.append(poly([(cx - 76 * s, base_y + 8 * s), (cx - 8 * s, base_y - 3 * s), (cx + 8 * s, base_y - 3 * s),
                     (cx + 76 * s, base_y + 8 * s), (cx + 76 * s, base_y + 13 * s), (cx - 76 * s, base_y + 13 * s)], frame))
    for dx in (-72, 0, 72):
        out.append(circle(cx + dx * s, base_y + 16 * s, 7.5 * s, frame))
    return "".join(out)


def chair_front(cx, top_y, s=1.0, color=NAVY700):
    """Office chair on the far side of a table, facing the viewer (its lower half is hidden)."""
    bw, bh = 104 * s, 100 * s
    out = [rect(cx - bw / 2, top_y, bw, bh, color, rx=26 * s),
           rect(cx - bw / 2 + 9 * s, top_y + 9 * s, bw - 18 * s, bh - 24 * s, NAVY600, rx=20 * s)]
    for side in (-1, 1):
        out.append(rect(cx + side * 57 * s - 15 * s, top_y + bh - 4 * s, 30 * s, 9 * s, NAVY900, rx=4.5 * s))
    return "".join(out)


def sofa(x, base_y, w, s=1.0):
    h = 150 * s
    out = [rect(x + 22 * s, base_y - h, w - 44 * s, h * 0.62, NAVY600, rx=20 * s)]
    n = 3
    cw = (w - 92 * s) / n
    for k in range(n):
        out.append(rect(x + 46 * s + k * cw + 4 * s, base_y - h + 14 * s, cw - 8 * s, h * 0.44, NAVY500, rx=16 * s))
    out.append(rect(x + 22 * s, base_y - h * 0.44, w - 44 * s, h * 0.27, NAVY500, rx=12 * s))
    out.append(rect(x + 22 * s, base_y - h * 0.2, w - 44 * s, h * 0.12, NAVY700))
    for ax in (x, x + w - 46 * s):
        out.append(rect(ax, base_y - h * 0.64, 46 * s, h * 0.56, NAVY700, rx=16 * s))
    for lx in (x + 30 * s, x + w - 40 * s):
        out.append(rect(lx, base_y - h * 0.08, 10 * s, h * 0.08, BRASS))
    out.append(rect(x + w * 0.64, base_y - h * 0.66, 54 * s, 46 * s, BRASS_LIGHT, rx=12 * s))
    return "".join(out)


def coffee_table(cx, front_y, w, legs_to):
    depth = 32
    return (rect(cx - w / 2, front_y - depth, w, depth, WOOD_TOP) + rect(cx - w / 2 - 3, front_y, w + 6, 9, WOOD, rx=2)
            + rect(cx - w / 2 + 14, front_y + 9, 9, legs_to - front_y - 9, NAVY800)
            + rect(cx + w / 2 - 23, front_y + 9, 9, legs_to - front_y - 9, NAVY800))


def round_table(cx, top_y, rx, ry, feet_y):
    return (rect(cx - 10, top_y + ry * 0.6, 20, feet_y - top_y - ry * 0.6 - 6, NAVY800)
            + ellipse(cx, feet_y, 70, 11, NAVY800)
            + ellipse(cx, top_y + 9, rx, ry, WOOD)
            + ellipse(cx, top_y, rx, ry, WOOD_TOP))


def desk_lamp(x, y, s=1.0):
    return (ellipse(x, y - 3 * s, 28 * s, 7 * s, NAVY800)
            + f'<path d="M{f(x)},{f(y-6*s)} L{f(x+8*s)},{f(y-96*s)} L{f(x+58*s)},{f(y-128*s)}" stroke="{NAVY800}" stroke-width="{f(6*s)}" fill="none" stroke-linejoin="round"/>'
            + poly([(x + 44 * s, y - 146 * s), (x + 92 * s, y - 128 * s), (x + 66 * s, y - 100 * s)], BRASS))


def mug(x, y, s=1.0):
    return (rect(x, y - 26 * s, 22 * s, 26 * s, "#FFFFFF", extra=f' stroke="{NAVY400}" stroke-width="{f(2.5*s)}"', rx=3 * s)
            + f'<path d="M{f(x+22*s)},{f(y-20*s)} q{f(11*s)},{f(2*s)} 0,{f(13*s)}" stroke="{NAVY400}" stroke-width="{f(3*s)}" fill="none"/>')


def notebook(x, y, s=1.0, col=NAVY500):
    return (poly([(x, y), (x + 74 * s, y), (x + 80 * s, y + 14 * s), (x + 6 * s, y + 14 * s)], col)
            + poly([(x + 8 * s, y + 3 * s), (x + 70 * s, y + 3 * s), (x + 74 * s, y + 11 * s), (x + 12 * s, y + 11 * s)], "#FFFFFF", extra=opa(".25")))


def pen_cup(x, y, s=1.0):
    return (rect(x + 6 * s, y - 44 * s, 4 * s, 22 * s, NAVY500) + rect(x + 13 * s, y - 50 * s, 4 * s, 28 * s, BRASS)
            + rect(x, y - 26 * s, 24 * s, 26 * s, NAVY700, rx=3 * s))


# --------------------------------------------------------------- scenes

STOP_X = (160, 480, 800, 1120, 1440)


def panorama(standalone=True):
    """Homepage strip, 1600x470: five workstations on one bench desk, one per area below it."""
    sc = Scene(1600, 470, 350, prefix="h-", seed=7, cls="panorama", standalone=standalone, preserve="xMidYMax slice")
    sc.add(window(sc, 0, 34, 1600, 236, panes=5, view=0.2, blinds=((0, 0.34), (3, 0.34)), transom=False, sill=False))
    for cx in STOP_X:
        sc.add(pendant(cx, 14, s=0.62))
    sc.add(plant(16, 470, s=0.9), plant(1584, 470, s=0.9))
    front = 336
    sc.add(back_panel(0, 1600, front - 36, h=48, dividers=(320, 640, 960, 1280)))
    sc.add(desk(24, 1552, front, 452, depth=36, panel=False))
    sc.add(f'<path class="line-path" d="M20,{front+6}H1580" stroke="{BRASS}" stroke-width="6" fill="none"/>')
    extras = {0: mug(60, 326, 0.75), 1: notebook(552, 318, 0.75), 2: mug(888, 326, 0.75),
              3: notebook(1188, 318, 0.75, col=BRASS_LIGHT), 4: mug(1512, 326, 0.75)}
    for i, cx in enumerate(STOP_X):
        sc.add(f'<g class="stop s{i+1}">{laptop(sc, cx, 312, s=0.74, screen_cls="screen")}</g>')
        sc.add(extras[i])
    for i, cx in enumerate(STOP_X):
        sc.add(chair_back(cx + (12 if i % 2 else -12), 330, 462, s=0.8, color=NAVY700 if i % 2 else NAVY600))
    return sc.svg()


def scene_port_saeed():
    """A furnished office for two."""
    sc = Scene(1600, 900, 640, seed=21)
    sc.add(window(sc, 270, 110, 800, 370, panes=3, view=0.28, blinds=((0, 0.46),)))
    sc.add(clock(1310, 205, 50))
    sc.add(cabinet(1220, 652, 180, 200))
    sc.add(plant(1310, 444, s=0.62, kind="small", seed=8))
    sc.add(plant(112, 672, s=1.15))
    sc.add(pendant(470, 52), pendant(900, 52))
    sc.add(rug(690, 812, 1060, 120))
    front = 580
    sc.add(desk(200, 960, front, 778, depth=48, pedestal=1012))
    sc.add(desk_lamp(250, front - 22))
    sc.add(laptop(sc, 470, front - 38), laptop(sc, 900, front - 38))
    sc.add(mug(612, front - 16), notebook(985, front - 30), pen_cup(1100, front - 16))
    sc.add(chair_back(455, front - 14, 800), chair_back(915, front - 14, 800, color=NAVY600))
    return sc.svg()


def scene_al_barsha():
    """A team office with four desks."""
    sc = Scene(1600, 900, 640, seed=33)
    sc.add(whiteboard(150, 140, 470, 270))
    sc.add(binder_shelf(720, 300, 330, sc.rng))
    sc.add(window(sc, 1150, 110, 360, 370, panes=2, view=0.26))
    for cx in (290, 800, 1310):
        sc.add(pendant(cx, 46, s=0.9))
    sc.add(plant(1540, 700, s=1.0))
    sc.add(rug(800, 815, 1380, 110))
    front = 590
    sc.add(back_panel(90, 1420, front - 46, h=60, dividers=(445, 800, 1155)))
    sc.add(desk(90, 1420, front, 785, depth=46))
    stations = (268, 622, 978, 1332)
    for i, cx in enumerate(stations):
        sc.add(laptop(sc, cx, front - 34, s=0.96))
    sc.add(mug(380, front - 14), notebook(700, front - 28, col=BRASS_LIGHT), mug(1060, front - 14), pen_cup(1440, front - 14))
    for i, cx in enumerate(stations):
        sc.add(chair_back(cx + (10 if i % 2 else -10), front - 12, 806, s=0.98, color=NAVY700 if i % 2 else NAVY600))
    return sc.svg()


def scene_sheikh_zayed_road():
    """A private office with a desk and a small meeting table."""
    sc = Scene(1600, 900, 650, seed=45)
    sc.add(window(sc, 70, 80, 1460, 440, panes=4, view=0.34, transom=False))
    sc.add(rug(1170, 828, 560, 84))
    front = 606
    sc.add(desk(150, 690, front, 806, depth=50, top=WOOD_TOP, edge=WOOD, pedestal=168))
    sc.add(monitor(sc, 640, front - 30, s=0.95))
    sc.add(laptop(sc, 420, front - 38))
    sc.add(desk_lamp(770, front - 24, s=0.9), mug(300, front - 16), notebook(500, front - 30, col=BRASS_LIGHT))
    sc.add(chair_back(430, front - 30, 826, s=1.08, color=NAVY800, tall=True))
    sc.add(chair_front(1250, 548, s=0.98))
    sc.add(round_table(1170, 640, 176, 40, 812))
    sc.add(laptop_back(1250, 640, s=0.82), mug(1100, 646, s=0.9), notebook(1150, 640, s=0.7, col=NAVY500))
    sc.add(chair_back(1056, 640, 846, s=0.98, color=NAVY600))
    sc.add(plant(1540, 712, s=1.05))
    return sc.svg()


def scene_jlt():
    """A shared workspace: a long table and a lounge corner."""
    sc = Scene(1600, 900, 640, seed=57)
    sc.add(window(sc, 100, 100, 930, 380, panes=3, view=0.24, blinds=((2, 0.3),)))
    sc.add(binder_shelf(1130, 310, 380, sc.rng))
    sc.add(wall_art(1210, 120, 150, 140), wall_art(1380, 140, 110, 120, variant=1))
    for cx in (300, 565, 830):
        sc.add(pendant(cx, 40, s=0.9))
    sc.add(rug(1310, 812, 520, 90))
    sc.add(sofa(1100, 752, 430))
    sc.add(coffee_table(1310, 790, 240, 840))
    sc.add(mug(1250, 776, 0.9), plant(1380, 784, s=0.42, kind="small", seed=11))
    front = 600
    for cx in (432, 698):
        sc.add(chair_front(cx, 470, s=0.96, color=NAVY600))
    sc.add(desk(140, 860, front, 790, depth=56, top=WOOD_TOP, edge=WOOD))
    for cx in (432, 698):
        sc.add(laptop_back(cx, front - 40, s=0.84))
    for cx in (300, 565, 830):
        sc.add(laptop(sc, cx, front - 20, s=0.9))
    sc.add(mug(910, front - 6, 0.9), notebook(180, front - 18, s=0.8, col=BRASS_LIGHT))
    for i, cx in enumerate((300, 565, 830)):
        sc.add(chair_back(cx + (8 if i % 2 else -8), front + 4, 812, s=0.95, color=NAVY700 if i % 2 else NAVY800))
    sc.add(plant(50, 700, s=1.0))
    return sc.svg()


def scene_business_bay():
    """A meeting room."""
    sc = Scene(1600, 900, 640, seed=69)
    sc.add(glass_partition(0, 150, 0, 652))
    sc.add(wall_art(250, 170, 210, 150))
    sc.add(wall_screen(sc, 620, 140, 360, 220))
    sc.add(clock(1360, 200, 44))
    sc.add(rect(560, 60, 480, 12, NAVY800, rx=4), rect(640, 0, 3, 60, NAVY800), rect(957, 0, 3, 60, NAVY800),
           rect(580, 72, 440, 4, "#FFF3D6"))
    sc.add(plant(1500, 700, s=1.1))
    sc.add(rug(800, 830, 1240, 100))
    for cx in (470, 690, 910, 1130):
        sc.add(chair_front(cx, 452, s=0.96))
    front = 640
    sc.add(desk(290, 1020, front, 818, depth=108))
    for cx in (470, 910):
        sc.add(laptop_back(cx, front - 72, s=0.86))
    for cx in (690, 1130):
        sc.add(notebook(cx - 40, front - 82, s=0.85, col=BRASS_LIGHT if cx == 690 else NAVY500))
    sc.add(ellipse(800, front - 52, 30, 9, NAVY800), ellipse(800, front - 56, 18, 5, NAVY500))
    for cx in (560, 1040):
        sc.add(laptop(sc, cx, front - 30, s=0.9))
    sc.add(mug(740, front - 10, 0.9), mug(860, front - 12, 0.9))
    for cx in (560, 800, 1040):
        sc.add(chair_back(cx, front - 14, 846, s=0.98, color=NAVY600 if cx == 800 else NAVY700))
    return sc.svg()


def interior():
    """Furnished private office, 1600x1000: a desk, an office chair and a laptop by a window."""
    sc = Scene(1600, 1000, 720, seed=11)
    sc.add(window(sc, 560, 90, 900, 420, panes=3, view=0.32))
    sx, sy = 90, 150
    sc.add(rect(sx, sy, 330, 560, NAVY700), rect(sx + 330, sy + 10, 26, 550, NAVY900))
    rng = random.Random(11)
    for r in range(4):
        yy = sy + 20 + r * 134
        sc.add(rect(sx + 14, yy, 302, 110, NAVY600))
        bx = sx + 24
        while bx < sx + 290:
            bw, bh = rng.uniform(10, 20), rng.uniform(58, 96)
            if rng.random() < 0.14:
                bx += 26
                continue
            sc.add(rect(bx, yy + 110 - bh, bw, bh, rng.choice([MIST, "#FFFFFF", BRASS_LIGHT, NAVY300, MIST2])))
            bx += bw + 3
    sc.add(plant(1520, 760, s=1.1))
    sc.add(pendant(1010, 40))
    sc.add(rug(1000, 900, 1000, 130))
    front = 660
    sc.add(desk(600, 820, front, 870, depth=52, top=WOOD_TOP, edge=WOOD, pedestal=1260))
    sc.add(laptop(sc, 860, front - 40, s=1.05), monitor(sc, 1110, front - 30))
    sc.add(desk_lamp(660, front - 24), mug(990, front - 18), notebook(700, front - 32, col=BRASS_LIGHT))
    sc.add(chair_back(880, front - 20, 900, s=1.1, color=NAVY800, tall=True))
    return sc.svg()


def logo_mark(size=64):
    """Door-plate mark: a brass-edged plate with a doorway."""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="{size}" height="{size}">'
            f'<rect x="2" y="2" width="60" height="60" rx="12" fill="{NAVY800}"/>'
            f'<rect x="6.5" y="6.5" width="51" height="51" rx="8.5" fill="none" stroke="{BRASS}" stroke-width="3"/>'
            '<path d="M22 50V24a10 10 0 0 1 20 0v26" fill="none" stroke="#fff" stroke-width="5" stroke-linecap="round"/>'
            f'<circle cx="37" cy="38" r="2.6" fill="{BRASS_LIGHT}"/>'
            f'<path d="M14 50h36" stroke="{BRASS}" stroke-width="4" stroke-linecap="round"/>'
            '</svg>')


SCENES = {
    "office-for-rent-port-saeed": scene_port_saeed,
    "sheikh-zayed-road-office": scene_sheikh_zayed_road,
    "business-bay-office-rental": scene_business_bay,
    "office-for-rent-al-barsha": scene_al_barsha,
    "furnished-office-jlt": scene_jlt,
    "furnished-office-dubai": interior,
}


def main():
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "panorama.svg"), "w") as fh:
        fh.write(panorama())
    for name, fn in SCENES.items():
        with open(os.path.join(OUT, name + ".svg"), "w") as fh:
            fh.write(fn())
    print("art written to", OUT)


if __name__ == "__main__":
    main()
