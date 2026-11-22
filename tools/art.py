"""Original vector illustrations for Property Rent Hub.

Generates SVG scenes (hero panorama, one scene per location, an office interior
and the logo mark) into art/. tools/make_images.py turns them into WebP/AVIF.

The drawings are deliberately generic: no real landmark is reproduced, and
they are labelled as illustrations wherever they appear.
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
LEAF = "#2F6B4F"
LEAF2 = "#3F8462"


def f(v):
    s = f"{v:.1f}"
    return s[:-2] if s.endswith(".0") else s


def patterns(k=1.0):
    """Facade textures as patterns: k scales their size for larger scenes."""
    gw, gh = 7 * k, 9 * k
    pw, ph = 11 * k, 13 * k
    return (
        f'<pattern id="glass" width="{f(gw)}" height="{f(gh)}" patternUnits="userSpaceOnUse">'
        f'<path d="M0 {f(gh-0.5)}H{f(gw)}" stroke="#fff" stroke-opacity=".22" stroke-width="{f(max(1, k*0.8))}"/>'
        f'<path d="M{f(gw-0.5)} 0V{f(gh)}" stroke="#fff" stroke-opacity=".09" stroke-width="{f(max(1, k*0.7))}"/></pattern>'
        f'<pattern id="punch" width="{f(pw)}" height="{f(ph)}" patternUnits="userSpaceOnUse">'
        f'<rect x="{f(2.5*k)}" y="{f(3.6*k)}" width="{f(6*k)}" height="{f(5.4*k)}" fill="#fff" fill-opacity=".42"/></pattern>'
    )


# ---------------------------------------------------------------- primitives

def lit_window(x, y, w, h):
    return f'<rect x="{f(x)}" y="{f(y)}" width="{f(w)}" height="{f(h)}" fill="{BRASS_LIGHT}" stroke="{BRASS}" stroke-width="1"/>'


def tower(x, base, w, h, face=NAVY700, side=NAVY900, top="flat", lit=False):
    depth = max(6, w * 0.22)
    y = base - h
    out = []
    cap = 0  # height of the shaped top above the textured shaft
    if top == "slant":
        cap = w * 0.45
        shape = f"M{f(x)},{f(y+cap)} L{f(x+w)},{f(y)} L{f(x+w)},{f(base)} L{f(x)},{f(base)} Z"
        side_top = y
    elif top == "step":
        cap = h * 0.10
        s = w * 0.18
        shape = (f"M{f(x)},{f(y+cap)} H{f(x+s)} V{f(y+h*0.04)} H{f(x+2*s)} V{f(y)} H{f(x+w-2*s)} V{f(y+h*0.04)} "
                 f"H{f(x+w-s)} V{f(y+cap)} H{f(x+w)} V{f(base)} H{f(x)} Z")
        side_top = y + cap
    elif top == "crown":
        cap = 12 + w * 0.1
        shape = f"M{f(x)},{f(y+cap)} L{f(x+w*0.5)},{f(y)} L{f(x+w)},{f(y+cap)} L{f(x+w)},{f(base)} L{f(x)},{f(base)} Z"
        side_top = y + cap
    elif top == "round":
        cap = w / 2
        shape = f"M{f(x)},{f(base)} L{f(x)},{f(y+cap)} A{f(cap)},{f(cap)} 0 0 1 {f(x+w)},{f(y+cap)} L{f(x+w)},{f(base)} Z"
        side_top = y + cap
    else:
        shape = f"M{f(x)},{f(y)} H{f(x+w)} V{f(base)} H{f(x)} Z"
        side_top = y
    out.append(f'<path d="M{f(x+w)},{f(side_top)} L{f(x+w+depth)},{f(side_top+depth*0.3)} L{f(x+w+depth)},{f(base)} L{f(x+w)},{f(base)} Z" fill="{side}"/>')
    out.append(f'<path d="{shape}" fill="{face}"/>')
    out.append(f'<rect x="{f(x)}" y="{f(y+cap)}" width="{f(w)}" height="{f(h-cap)}" fill="url(#glass)"/>')
    out.append(f'<path d="M{f(x+0.7)},{f(y+cap)}V{f(base)}" stroke="#fff" stroke-opacity=".38" stroke-width="1.4"/>')
    if lit:
        out.append(lit_window(x + w * 0.22, y + cap + (h - cap) * 0.30, w * 0.40, max(5, w * 0.14)))
    return "".join(out)


def block(x, base, w, h, face=NAVY600, side=NAVY800, lit=False):
    depth = max(5, w * 0.16)
    y = base - h
    out = [f'<path d="M{f(x+w)},{f(y+3)} L{f(x+w+depth)},{f(y+3+depth*0.35)} L{f(x+w+depth)},{f(base)} L{f(x+w)},{f(base)} Z" fill="{side}"/>',
           f'<rect x="{f(x)}" y="{f(y)}" width="{f(w)}" height="{f(h)}" fill="{face}"/>',
           f'<rect x="{f(x-1)}" y="{f(y-3)}" width="{f(w+2)}" height="3" fill="{side}"/>',
           f'<rect x="{f(x+2)}" y="{f(y+3)}" width="{f(w-4)}" height="{f(h-6)}" fill="url(#punch)"/>',
           f'<path d="M{f(x+0.7)},{f(y)}V{f(base)}" stroke="#fff" stroke-opacity=".3" stroke-width="1.2"/>']
    if lit:
        out.append(lit_window(x + w * 0.3, y + h * 0.35, w * 0.3, max(5, w * 0.1)))
    return "".join(out)


def palm(x, base, s=1.0):
    """Date palm: slightly curved trunk and drooping fronds."""
    h = 52 * s
    tx = x + 4 * s
    top = base - h
    out = [f'<path d="M{f(x)},{f(base)} Q{f(x+7*s)},{f(base-h*0.55)} {f(tx)},{f(top)}" stroke="{NAVY700}" stroke-width="{f(3.6*s)}" fill="none" stroke-linecap="round"/>']
    fronds = [(-26, 9), (-20, -1), (-11, -7), (0, -9), (11, -7), (20, -1), (26, 9), (-14, 13), (15, 13)]
    for i, (dx, dy) in enumerate(fronds):
        ex, ey = tx + dx * s, top + dy * s + 6 * s
        cx, cy = tx + dx * 0.45 * s, top + min(dy, 0) * s - 9 * s
        out.append(f'<path d="M{f(tx)},{f(top)} Q{f(cx)},{f(cy)} {f(ex)},{f(ey)}" stroke="{LEAF if i % 2 else LEAF2}" '
                   f'stroke-width="{f(3.4*s)}" fill="none" stroke-linecap="round"/>')
    out.append(f'<circle cx="{f(tx)}" cy="{f(top+2*s)}" r="{f(2.6*s)}" fill="{BRASS}"/>')
    return "".join(out)


def dhow(x, water_y, s=1.0):
    """Generic wooden boat, side view."""
    L = 120 * s
    hull = (f'M{f(x)},{f(water_y-14*s)} L{f(x+L)},{f(water_y-22*s)} '
            f'Q{f(x+L*0.92)},{f(water_y+2*s)} {f(x+L*0.70)},{f(water_y+4*s)} '
            f'L{f(x+L*0.22)},{f(water_y+4*s)} Q{f(x+L*0.05)},{f(water_y)} {f(x)},{f(water_y-14*s)} Z')
    out = [f'<path d="{hull}" fill="{WOOD}" opacity=".2" transform="translate(0,{f(2*water_y+8*s)}) scale(1,-1)"/>',
           f'<path d="{hull}" fill="{WOOD}"/>',
           f'<path d="M{f(x+L*0.06)},{f(water_y-11*s)} L{f(x+L*0.96)},{f(water_y-18*s)}" stroke="{BRASS_LIGHT}" stroke-width="{f(2*s)}"/>',
           f'<rect x="{f(x+L*0.30)}" y="{f(water_y-30*s)}" width="{f(L*0.34)}" height="{f(14*s)}" fill="{NAVY600}"/>']
    for k in (0.33, 0.43, 0.53):
        out.append(f'<rect x="{f(x+L*k)}" y="{f(water_y-27*s)}" width="{f(L*0.06)}" height="{f(6*s)}" fill="#fff" fill-opacity=".6"/>')
    out += [f'<path d="M{f(x+L*0.48)},{f(water_y-30*s)}V{f(water_y-92*s)}" stroke="{NAVY800}" stroke-width="{f(2.4*s)}"/>',
            f'<path d="M{f(x+L*0.18)},{f(water_y-46*s)} L{f(x+L*0.82)},{f(water_y-86*s)}" stroke="{NAVY800}" stroke-width="{f(2*s)}"/>',
            f'<path d="M{f(x+L*0.22)},{f(water_y-48*s)} L{f(x+L*0.78)},{f(water_y-83*s)} L{f(x+L*0.62)},{f(water_y-60*s)} Z" fill="#FBFCFE" stroke="{NAVY500}" stroke-width="1"/>']
    return "".join(out)


def ripples(x0, x1, y0, y1, rng, n=18, op=0.35, sw=1.2):
    d = []
    for _ in range(n):
        y = rng.uniform(y0 + 4, y1 - 3)
        x = rng.uniform(x0, x1 - 40)
        w = rng.uniform(18, 70)
        d.append(f"M{f(x)},{f(y)}h{f(w)}")
    return f'<path d="{"".join(d)}" stroke="{NAVY400}" stroke-opacity="{op}" stroke-width="{sw}" stroke-linecap="round"/>'


def viaduct(x0, x1, y, ground, pier_gap=90, stops=(), stop_r=9.0, line_w=5.0, deck=6.0):
    out = []
    px = x0 + pier_gap / 2
    piers = []
    caps = []
    while px < x1:
        piers.append(f"M{f(px)},{f(y+deck)}V{f(ground)}")
        caps.append(f"M{f(px-deck*1.5)},{f(y+deck)}h{f(deck*3)}")
        px += pier_gap
    out.append(f'<path d="{"".join(piers)}" stroke="{NAVY600}" stroke-width="{f(deck)}"/>')
    out.append(f'<path d="{"".join(caps)}" stroke="{NAVY700}" stroke-width="{f(deck*0.7)}"/>')
    out.append(f'<rect x="{f(x0)}" y="{f(y+line_w*0.2)}" width="{f(x1-x0)}" height="{f(deck)}" fill="{NAVY800}"/>')
    out.append(f'<path class="line-path" d="M{f(x0)},{f(y)}H{f(x1)}" stroke="{BRASS}" stroke-width="{f(line_w)}" stroke-linecap="round" fill="none"/>')
    for i, sx in enumerate(stops):
        out.append(f'<g class="stop s{i+1}"><circle cx="{f(sx)}" cy="{f(y)}" r="{f(stop_r)}" fill="#fff" stroke="{BRASS}" stroke-width="{f(stop_r*0.44)}"/>'
                   f'<circle cx="{f(sx)}" cy="{f(y)}" r="{f(stop_r*0.36)}" fill="{NAVY800}"/></g>')
    return "".join(out)


def far_skyline(x0, x1, base, rng, op=0.3, hmin=30, hmax=110, wmin=14, wmax=34):
    d = []
    x = x0
    while x < x1:
        w = rng.uniform(wmin, wmax)
        h = rng.uniform(hmin, hmax)
        d.append(f"M{f(x)},{f(base)}V{f(base-h)}h{f(w)}V{f(base)}Z")
        x += w + rng.uniform(2, 14)
    return f'<path d="{"".join(d)}" fill="{NAVY300}" fill-opacity="{op}"/>'


def gradients():
    return ('<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0" stop-color="#FFFFFF"/><stop offset="1" stop-color="{MIST}"/></linearGradient>'
            '<linearGradient id="water" x1="0" y1="0" x2="0" y2="1">'
            '<stop offset="0" stop-color="#DCE5F0"/><stop offset="1" stop-color="#C6D4E5"/></linearGradient>')


# ---------------------------------------------------------------- districts
# spec tuples: (x as share of W, width as share of W, height, top or None for a block, face)

PORT_SAEED = [(0.02, 0.15, 70, None, NAVY600), (0.19, 0.13, 96, None, NAVY500), (0.34, 0.17, 62, None, NAVY700),
              (0.53, 0.12, 120, None, NAVY600), (0.67, 0.16, 84, None, NAVY500), (0.84, 0.13, 104, None, NAVY700)]
SZR = [(0.00, 0.09, 190, "flat", NAVY700), (0.11, 0.08, 250, "slant", NAVY600), (0.22, 0.10, 214, "step", NAVY800),
       (0.35, 0.07, 286, "crown", NAVY700), (0.45, 0.09, 230, "flat", NAVY600), (0.57, 0.08, 266, "slant", NAVY800),
       (0.68, 0.10, 205, "round", NAVY700), (0.81, 0.08, 244, "step", NAVY600), (0.91, 0.08, 196, "flat", NAVY700)]
BUSINESS_BAY = [(0.02, 0.12, 170, "step", NAVY600), (0.17, 0.10, 232, "slant", NAVY700), (0.30, 0.13, 270, "flat", NAVY800),
                (0.47, 0.10, 210, "round", NAVY600), (0.60, 0.12, 246, "crown", NAVY700), (0.76, 0.10, 186, "slant", NAVY800),
                (0.88, 0.10, 150, "flat", NAVY600)]
AL_BARSHA = [(0.00, 0.14, 110, None, NAVY600), (0.16, 0.12, 150, None, NAVY700), (0.30, 0.13, 92, None, NAVY500),
             (0.63, 0.13, 138, None, NAVY700), (0.78, 0.12, 118, None, NAVY600), (0.91, 0.09, 160, None, NAVY800)]
JLT = [(0.03, 0.09, 236, "flat", NAVY700), (0.14, 0.09, 270, "step", NAVY800), (0.26, 0.08, 206, "slant", NAVY600),
       (0.40, 0.11, 300, "crown", NAVY700), (0.55, 0.09, 226, "round", NAVY600), (0.67, 0.09, 262, "flat", NAVY800),
       (0.80, 0.09, 214, "slant", NAVY700), (0.90, 0.08, 246, "step", NAVY600)]

SPECS = {"port-saeed": PORT_SAEED, "sheikh-zayed-road": SZR, "business-bay": BUSINESS_BAY,
         "al-barsha": AL_BARSHA, "jlt": JLT}


def draw_district(key, x, g, W=320, hs=1.0, lit_index=None):
    out = []
    for i, (px, pw, ph, top, face) in enumerate(SPECS[key]):
        lit = (i == lit_index)
        if top is None:
            out.append(block(x + px * W, g, pw * W, ph * hs, face=face, lit=lit))
        else:
            out.append(tower(x + px * W, g, pw * W, ph * hs, face=face, top=top, lit=lit))
    if key == "al-barsha":
        # long low building with a barrel roof (generic retail form)
        mx, mw, mh = x + 0.45 * W, 0.17 * W, 52 * hs
        out.append(f'<rect x="{f(mx)}" y="{f(g-mh)}" width="{f(mw)}" height="{f(mh)}" fill="{NAVY500}"/>')
        out.append(f'<path d="M{f(mx-3)},{f(g-mh)} Q{f(mx+mw/2)},{f(g-mh-26*hs)} {f(mx+mw+3)},{f(g-mh)} Z" fill="{NAVY700}"/>')
        out.append(f'<rect x="{f(mx+6)}" y="{f(g-mh+10*hs)}" width="{f(mw-12)}" height="{f(8*hs)}" fill="#fff" fill-opacity=".45"/>')
        out.append(f'<rect x="{f(mx)}" y="{f(g-14*hs)}" width="{f(mw)}" height="{f(14*hs)}" fill="{NAVY800}"/>')
    return "".join(out)


# ---------------------------------------------------------------- scenes

STOP_X = (160, 480, 800, 1120, 1440)


def panorama(standalone=True):
    """Hero drawing: five districts along one elevated line. viewBox 1600x470."""
    rng = random.Random(7)
    W, H = 1600, 470
    g = 404
    line_y = 352
    attrs = 'xmlns="http://www.w3.org/2000/svg" ' if standalone else ''
    out = [f'<svg {attrs}class="panorama" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMax slice" aria-hidden="true" focusable="false">',
           f'<defs>{gradients()}{patterns(1)}</defs>',
           f'<rect width="{W}" height="{g}" fill="url(#sky)"/>',
           far_skyline(0, W, g, rng, op=0.28, hmin=40, hmax=150)]
    order = ["port-saeed", "sheikh-zayed-road", "business-bay", "al-barsha", "jlt"]
    for i, key in enumerate(order):
        out.append(draw_district(key, i * 320, g, lit_index=(2 if key == "business-bay" else None)))
    out.append(f'<rect x="0" y="{g}" width="{W}" height="{H-g}" fill="{MIST}"/>')
    out.append(f'<rect x="0" y="{g}" width="330" height="{H-g}" fill="url(#water)"/>')
    out.append(ripples(0, 330, g, H, rng, n=12))
    out.append(f'<rect x="640" y="{g+18}" width="320" height="24" fill="url(#water)"/>')
    out.append(f'<path d="M690,{g+18} Q800,{g-16} 910,{g+18}" stroke="{NAVY600}" stroke-width="4" fill="none"/>')
    out.append(f'<rect x="1290" y="{g}" width="310" height="{H-g}" fill="url(#water)"/>')
    out.append(ripples(1290, W, g, H, rng, n=12))
    out.append(f'<path d="M0,{g}H{W}" stroke="{NAVY800}" stroke-width="2"/>')
    out.append(viaduct(-10, W + 10, line_y, g, pier_gap=100, stops=STOP_X))
    out.append(dhow(150, g + 34, s=0.62))
    for px in (995, 1190, 1250):
        out.append(palm(px, g + 2, s=0.62))
    out.append('</svg>')
    return "".join(out)


def location_scene(key):
    """16:9 scene, 1600x900: one district drawn large, with its stop on the line."""
    rng = random.Random(sum(map(ord, key)))
    W, H = 1600, 900
    g = 712
    line_y = 618
    tallest = max(s[2] for s in SPECS[key])
    hs = 560 / tallest
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}">',
           f'<defs>{gradients()}{patterns(1.9)}</defs>',
           f'<rect width="{W}" height="{g}" fill="url(#sky)"/>',
           far_skyline(0, W, g, rng, op=0.26, hmin=120, hmax=420, wmin=30, wmax=70)]
    lit = {"port-saeed": 3, "sheikh-zayed-road": 4, "business-bay": 2, "al-barsha": 3, "jlt": 3}[key]
    out.append(draw_district(key, -30, g, W=W * 1.0, hs=hs, lit_index=lit))
    out.append(f'<rect x="0" y="{g}" width="{W}" height="{H-g}" fill="{MIST}"/>')
    extra = []
    if key in ("port-saeed", "jlt"):
        out.append(f'<rect x="0" y="{g}" width="{W}" height="{H-g}" fill="url(#water)"/>')
        if key == "jlt":
            out.append(f'<g opacity=".13" transform="translate(0,{2*g}) scale(1,-1)">{draw_district(key, -30, g, W=W, hs=hs*0.4)}</g>')
        out.append(ripples(0, W, g, H, rng, n=46, op=0.42, sw=2))
        if key == "port-saeed":
            extra.append(dhow(930, g + 118, s=2.2))
    elif key == "business-bay":
        out.append(f'<rect x="0" y="{g+78}" width="{W}" height="96" fill="url(#water)"/>')
        out.append(ripples(0, W, g + 80, g + 172, rng, n=22, op=0.4, sw=2))
        extra.append(f'<path d="M380,{g+80} Q800,{g-40} 1220,{g+80}" stroke="{NAVY600}" stroke-width="12" fill="none"/>')
        extra.append(f'<path d="M380,{g+80} Q800,{g-18} 1220,{g+80}" stroke="{NAVY400}" stroke-width="4" fill="none"/>')
        extra.append(f'<path d="M300,{g+80}H1300" stroke="{NAVY700}" stroke-width="6"/>')
    elif key == "sheikh-zayed-road":
        for lane in range(4):
            out.append(f'<path d="M0,{g+44+lane*36}H{W}" stroke="#fff" stroke-width="5" stroke-dasharray="52 38"/>')
    elif key == "al-barsha":
        for px in (110, 330, 1270, 1500):
            extra.append(palm(px, g + 150, s=2.5))
    out.append(f'<path d="M0,{g}H{W}" stroke="{NAVY800}" stroke-width="3"/>')
    out.append(viaduct(-20, W + 20, line_y, g, pier_gap=240, stops=(800,), stop_r=18, line_w=10, deck=12))
    out.extend(extra)
    out.append('</svg>')
    return "".join(out)


def interior():
    """Furnished private office interior, 1600x1000."""
    rng = random.Random(11)
    W, H = 1600, 1000
    floor_y = 760
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}">',
           '<defs>'
           f'<linearGradient id="wall" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#FFFFFF"/><stop offset="1" stop-color="{MIST2}"/></linearGradient>'
           f'<linearGradient id="win" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#F7F9FC"/><stop offset="1" stop-color="{MIST}"/></linearGradient>'
           '<linearGradient id="flr" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#D9E1EC"/><stop offset="1" stop-color="#C8D3E2"/></linearGradient>'
           '</defs>',
           f'<rect width="{W}" height="{floor_y}" fill="url(#wall)"/>',
           f'<rect y="{floor_y}" width="{W}" height="{H-floor_y}" fill="url(#flr)"/>']
    wx, wy, ww, wh = 520, 90, 1000, 600
    out.append(f'<rect x="{wx}" y="{wy}" width="{ww}" height="{wh}" fill="url(#win)"/>')
    out.append(far_skyline(wx, wx + ww, wy + wh, rng, op=0.55, hmin=80, hmax=330, wmin=26, wmax=60))
    out.append(f'<path d="M{wx},{wy+wh-90}H{wx+ww}" stroke="{BRASS}" stroke-width="5"/>')
    for k in range(1, 4):
        out.append(f'<rect x="{wx + k*ww/4 - 5}" y="{wy}" width="10" height="{wh}" fill="{NAVY700}"/>')
    out.append(f'<rect x="{wx-14}" y="{wy-14}" width="{ww+28}" height="{wh+28}" fill="none" stroke="{NAVY800}" stroke-width="14"/>')
    sx, sy = 90, 150
    out.append(f'<rect x="{sx}" y="{sy}" width="330" height="610" fill="{NAVY700}"/>')
    out.append(f'<rect x="{sx+330}" y="{sy+10}" width="26" height="600" fill="{NAVY900}"/>')
    for r in range(4):
        yy = sy + 20 + r * 148
        out.append(f'<rect x="{sx+14}" y="{yy}" width="302" height="122" fill="{NAVY600}"/>')
        bx = sx + 24
        while bx < sx + 290:
            bw = rng.uniform(10, 20)
            bh = rng.uniform(62, 104)
            col = rng.choice([MIST, "#fff", BRASS_LIGHT, NAVY300, MIST2])
            if rng.random() < 0.14:
                bx += 26
                continue
            out.append(f'<rect x="{f(bx)}" y="{f(yy+122-bh)}" width="{f(bw)}" height="{f(bh)}" fill="{col}"/>')
            bx += bw + 3
    out.append(f'<rect x="1450" y="{floor_y-118}" width="90" height="118" fill="{NAVY800}"/>')
    for k in range(9):
        r = math.radians(-160 + k * 18)
        ex = 1495 + math.cos(r) * 120
        ey = floor_y - 118 + math.sin(r) * 190
        out.append(f'<path d="M1495,{floor_y-118} Q{f(1495+math.cos(r)*40)},{f(floor_y-118+math.sin(r)*130)} {f(ex)},{f(ey)}" stroke="{LEAF if k%2 else LEAF2}" stroke-width="16" fill="none" stroke-linecap="round"/>')
    out.append(f'<ellipse cx="930" cy="{floor_y+120}" rx="560" ry="90" fill="{NAVY300}" fill-opacity=".45"/>')
    dx, dy, dw = 640, 560, 640
    out.append(f'<rect x="{dx}" y="{dy}" width="{dw}" height="26" fill="{NAVY800}"/>')
    out.append(f'<rect x="{dx}" y="{dy+26}" width="{dw}" height="10" fill="{BRASS}"/>')
    out.append(f'<rect x="{dx+20}" y="{dy+36}" width="200" height="190" fill="{NAVY700}"/>')
    out.append(f'<rect x="{dx+dw-34}" y="{dy+36}" width="14" height="190" fill="{BRASS}"/>')
    for k in range(3):
        out.append(f'<rect x="{dx+36}" y="{dy+52+k*58}" width="168" height="44" fill="{NAVY600}"/><rect x="{dx+104}" y="{dy+70+k*58}" width="32" height="6" fill="{BRASS_LIGHT}"/>')
    out.append(f'<rect x="{dx+250}" y="{dy-170}" width="230" height="140" fill="{NAVY900}"/><rect x="{dx+262}" y="{dy-158}" width="206" height="116" fill="{NAVY600}"/>')
    out.append(f'<rect x="{dx+352}" y="{dy-30}" width="26" height="30" fill="{NAVY800}"/><rect x="{dx+320}" y="{dy-6}" width="90" height="6" fill="{NAVY800}"/>')
    out.append(f'<path d="M{dx+560},{dy} L{dx+560},{dy-150} L{dx+600},{dy-190}" stroke="{NAVY800}" stroke-width="6" fill="none"/>')
    out.append(f'<path d="M{dx+578},{dy-208} L{dx+640},{dy-182} L{dx+610},{dy-150} Z" fill="{BRASS}"/>')
    out.append(f'<rect x="{dx+120}" y="{dy-10}" width="90" height="10" fill="#fff"/><rect x="{dx+128}" y="{dy-18}" width="80" height="8" fill="{MIST}"/>')
    cx = dx + 330
    out.append(f'<rect x="{cx-70}" y="{dy-250}" width="140" height="210" rx="26" fill="{NAVY700}"/>')
    out.append(f'<rect x="{cx-58}" y="{dy-236}" width="10" height="180" fill="#fff" fill-opacity=".18"/>')
    for gx in (dx + 70, dx + 430):
        out.append(f'<rect x="{gx}" y="{dy+120}" width="150" height="34" fill="{NAVY600}"/>')
        out.append(f'<rect x="{gx}" y="{dy+20}" width="150" height="108" rx="14" fill="{NAVY700}"/>')
        out.append(f'<rect x="{gx+12}" y="{dy+154}" width="8" height="{floor_y+70-(dy+154)}" fill="{BRASS}"/>')
        out.append(f'<rect x="{gx+130}" y="{dy+154}" width="8" height="{floor_y+70-(dy+154)}" fill="{BRASS}"/>')
    out.append(f'<path d="M1000,0V60" stroke="{NAVY800}" stroke-width="3"/><rect x="900" y="60" width="200" height="12" fill="{BRASS}"/>')
    out.append('</svg>')
    return "".join(out)


def logo_mark(size=64):
    """Door-plate mark: a brass-edged plate with a doorway."""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="{size}" height="{size}">'
            f'<rect x="2" y="2" width="60" height="60" rx="12" fill="{NAVY800}"/>'
            f'<rect x="6.5" y="6.5" width="51" height="51" rx="8.5" fill="none" stroke="{BRASS}" stroke-width="3"/>'
            '<path d="M22 50V24a10 10 0 0 1 20 0v26" fill="none" stroke="#fff" stroke-width="5" stroke-linecap="round"/>'
            f'<circle cx="37" cy="38" r="2.6" fill="{BRASS_LIGHT}"/>'
            f'<path d="M14 50h36" stroke="{BRASS}" stroke-width="4" stroke-linecap="round"/>'
            '</svg>')


SCENE_FILES = {
    "port-saeed": "office-for-rent-port-saeed",
    "sheikh-zayed-road": "sheikh-zayed-road-office",
    "business-bay": "business-bay-office-rental",
    "al-barsha": "office-for-rent-al-barsha",
    "jlt": "furnished-office-jlt",
}


def main():
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "panorama.svg"), "w") as fh:
        fh.write(panorama())
    for key, name in SCENE_FILES.items():
        with open(os.path.join(OUT, name + ".svg"), "w") as fh:
            fh.write(location_scene(key))
    with open(os.path.join(OUT, "furnished-office-dubai.svg"), "w") as fh:
        fh.write(interior())
    print("art written to", OUT)


if __name__ == "__main__":
    main()
