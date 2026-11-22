"""Render art/*.svg to responsive WebP + AVIF files in assets/img/.
(Logo files and favicons come from tools/make_logo.py.)

Requires: rsvg-convert (librsvg) and Pillow with WebP/AVIF support.
Usage: python3 tools/make_images.py

To use licensed photos instead of the illustrations, put a large JPG/PNG at
photos/<name>.jpg (same <name> as below) and run this script again: photos
take priority over the illustrations and get the same file names and sizes.
"""
import io
import os
import subprocess

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART = os.path.join(ROOT, "art")
PHOTOS = os.path.join(ROOT, "photos")
IMG = os.path.join(ROOT, "assets", "img")

# name -> aspect ratio (w, h)
IMAGES = {
    "furnished-office-dubai": (16, 10),
    "office-for-rent-al-barsha": (16, 9),
    "office-for-rent-port-saeed": (16, 9),
    "sheikh-zayed-road-office": (16, 9),
    "furnished-office-jlt": (16, 9),
    "business-bay-office-rental": (16, 9),
}
WIDTHS = (480, 800, 1200, 1600)


def render_svg(path, width):
    png = subprocess.run(["rsvg-convert", "-w", str(width), path], check=True, capture_output=True).stdout
    return Image.open(io.BytesIO(png)).convert("RGB")


def source_image(name, width):
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        p = os.path.join(PHOTOS, name + ext)
        if os.path.exists(p):
            im = Image.open(p).convert("RGB")
            aw, ah = IMAGES[name]
            # centre-crop to the target aspect ratio
            tw = im.width
            th = round(tw * ah / aw)
            if th > im.height:
                th = im.height
                tw = round(th * aw / ah)
            left = (im.width - tw) // 2
            top = (im.height - th) // 2
            im = im.crop((left, top, left + tw, top + th))
            return im.resize((width, round(width * ah / aw)), Image.LANCZOS)
    return render_svg(os.path.join(ART, name + ".svg"), width)


def save_variants(name):
    for w in WIDTHS:
        im = source_image(name, w)
        im.save(os.path.join(IMG, f"{name}-{w}.webp"), "WEBP", quality=82, method=6)
        im.save(os.path.join(IMG, f"{name}-{w}.avif"), "AVIF", quality=60, speed=4)
    # the plain file name (largest size) for sitemaps, Open Graph and sharing
    big = source_image(name, WIDTHS[-1])
    big.save(os.path.join(IMG, f"{name}.webp"), "WEBP", quality=82, method=6)


def main():
    os.makedirs(IMG, exist_ok=True)
    for name in IMAGES:
        save_variants(name)
        print("ok", name)
    total = sum(os.path.getsize(os.path.join(IMG, f)) for f in os.listdir(IMG))
    print(f"assets/img total: {total/1024:.0f} KB")


if __name__ == "__main__":
    main()
