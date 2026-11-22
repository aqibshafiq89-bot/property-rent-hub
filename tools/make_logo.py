"""Prepare the Property Rent Hub logo for the website.

Input:  brand/logo-original.png  (the square logo on a black background)
Output: assets/img/logo-lockup.png/.webp   horizontal logo for the header (transparent)
        assets/img/logo-full.png/.webp     full square logo for the footer (transparent)
        assets/icons/*                     favicons and app icons (emblem on black)
        brand/logo-*.png                   transparent master files for print and social

The black background is removed with a colour-to-alpha step, so the gold and
white parts keep their exact colours on any dark background.
If the artwork changes, replace brand/logo-original.png and run this again.
"""
import os

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "brand", "logo-original.png")
IMG = os.path.join(ROOT, "assets", "img")
ICONS = os.path.join(ROOT, "assets", "icons")
BRAND = os.path.join(ROOT, "brand")

# Regions of the original artwork (pixels), measured from the 1254 x 1254 file.
EMBLEM = (136, 192, 1079, 783)
WORDMARK = (98, 783, 1171, 987)
FULL = (98, 192, 1171, 987)


def black_to_alpha(img):
    """Treat black as transparent: alpha = brightest channel, colour = unpremultiplied."""
    a = np.asarray(img.convert("RGB")).astype(np.float32) / 255.0
    alpha = a.max(axis=2)
    alpha = np.where(alpha < 6 / 255.0, 0.0, alpha)
    safe = np.maximum(alpha, 1e-6)[..., None]
    rgb = np.clip(a / safe, 0, 1)
    out = np.dstack([rgb, alpha[..., None]])
    return Image.fromarray((out * 255 + 0.5).astype(np.uint8), "RGBA")


def fit_height(im, h):
    w = round(im.width * h / im.height)
    return im.resize((w, h), Image.LANCZOS)


def save_pair(im, name):
    im.save(os.path.join(IMG, name + ".png"), optimize=True)
    im.save(os.path.join(IMG, name + ".webp"), "WEBP", quality=90, method=6)


def main():
    os.makedirs(IMG, exist_ok=True)
    os.makedirs(ICONS, exist_ok=True)
    original = Image.open(SRC).convert("RGB")
    clear = black_to_alpha(original)

    emblem = clear.crop(EMBLEM)
    wordmark = clear.crop(WORDMARK)
    full = clear.crop(FULL)
    emblem.save(os.path.join(BRAND, "logo-emblem-transparent.png"), optimize=True)
    full.save(os.path.join(BRAND, "logo-full-transparent.png"), optimize=True)

    # Horizontal lockup for the header, drawn at 2x (shown at 48 px high).
    H = 96
    e = fit_height(emblem, H)
    w = fit_height(wordmark, round(H * 0.74))
    gap = 22
    lock = Image.new("RGBA", (e.width + gap + w.width, H), (0, 0, 0, 0))
    lock.alpha_composite(e, (0, 0))
    lock.alpha_composite(w, (e.width + gap, (H - w.height) // 2 + 2))
    save_pair(lock, "logo-lockup")
    lock.save(os.path.join(BRAND, "logo-horizontal-transparent.png"), optimize=True)

    # Full logo for the footer (shown about 200 px wide).
    save_pair(fit_height(full, 300), "logo-full")

    # Icons: the emblem centred on black, as in the original artwork.
    def icon(size, pad=0.12):
        canvas = Image.new("RGBA", (size, size), (0, 0, 0, 255))
        inner = int(size * (1 - 2 * pad))
        em = emblem.copy()
        em.thumbnail((inner, inner), Image.LANCZOS)
        canvas.alpha_composite(em, ((size - em.width) // 2, (size - em.height) // 2))
        return canvas.convert("RGB")

    icon(32, pad=0.0).save(os.path.join(ICONS, "favicon-32.png"), optimize=True)
    icon(180, pad=0.07).save(os.path.join(ICONS, "apple-touch-icon.png"), optimize=True)
    icon(192, pad=0.07).save(os.path.join(ICONS, "icon-192.png"), optimize=True)
    icon(512, pad=0.07).save(os.path.join(ICONS, "icon-512.png"), optimize=True)
    icon(48, pad=0.0).save(os.path.join(ROOT, "assets", "favicon.ico"), sizes=[(16, 16), (32, 32), (48, 48)])
    old_svg = os.path.join(ICONS, "favicon.svg")
    if os.path.exists(old_svg):
        os.remove(old_svg)
    # Square logo with its original black background, for Google (Organization logo) and social profiles.
    original.resize((512, 512), Image.LANCZOS).save(os.path.join(IMG, "logo-square-512.png"), optimize=True)
    print("lockup", lock.size, "| full", full.size, "| emblem", emblem.size)


if __name__ == "__main__":
    main()
