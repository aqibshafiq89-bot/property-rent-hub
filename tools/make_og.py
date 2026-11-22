"""Render 1200x630 Open Graph share images (JPG) for every page.

Run after build.py (which writes tools/og-manifest.json), then run build.py again.
Requires Playwright for Python and a Chrome/Chromium browser.

JPG is used on purpose: WhatsApp, LinkedIn and Facebook link previews handle it
reliably, while WebP previews are inconsistent.
"""
import base64
import json
import os
import sys

from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "og")
FONT = os.path.join(ROOT, "assets", "fonts", "archivo-var.woff2")
CHROME = os.environ.get("CHROME_PATH", "/usr/bin/google-chrome")


def data_uri(path, mime):
    with open(path, "rb") as fh:
        return f"data:{mime};base64," + base64.b64encode(fh.read()).decode()


def image_uri(name):
    if name == "panorama":
        return data_uri(os.path.join(ROOT, "art", "panorama.svg"), "image/svg+xml")
    return data_uri(os.path.join(ROOT, "assets", "img", f"{name}-1200.webp"), "image/webp")


def page_html(title, subtitle, img, font_uri, logo_uri, wide=False):
    img_css = ("position:absolute;left:0;right:0;bottom:0;height:300px;background:url('%s') center bottom/cover no-repeat;" % img) if wide else \
              ("position:absolute;top:0;right:0;bottom:0;width:470px;background:url('%s') center/cover no-repeat;" % img)
    text_w = "1080px" if wide else "640px"
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
@font-face{{font-family:A;src:url('{font_uri}') format('woff2');font-weight:400 700;font-stretch:100% 125%}}
*{{box-sizing:border-box;margin:0}}
body{{width:1200px;height:630px;overflow:hidden;font-family:A,Arial,sans-serif;background:#fff}}
.card{{position:relative;width:1200px;height:630px;background:{'#fff' if wide else '#0A1A31'}}}
.img{{{img_css}}}
.text{{position:absolute;left:64px;top:{'52px' if wide else '70px'};width:{text_w}}}
h1{{font-weight:650;font-stretch:118%;font-size:{'52px' if wide else '50px'};line-height:1.06;letter-spacing:-.01em;color:{'#0E2240' if wide else '#fff'}}}
p{{margin-top:18px;font-size:26px;line-height:1.3;color:{'#3A4B66' if wide else '#C9D4E3'}}}
.rule{{width:90px;height:6px;background:#B58A3C;margin-bottom:26px;border-radius:3px}}
.brand{{position:absolute;left:64px;bottom:50px}}
.brand img{{height:62px;width:auto;display:block}}
</style></head><body><div class="card"><div class="img"></div>
<div class="text"><div class="rule"></div><h1>{title}</h1>{f'<p>{subtitle}</p>' if subtitle and not wide else ''}</div>
<div class="brand"><img src="{logo_uri}" alt=""></div></div></body></html>"""


def main():
    manifest_path = os.path.join(ROOT, "tools", "og-manifest.json")
    with open(manifest_path) as fh:
        items = json.load(fh)
    items.append({"key": "default", "title": "Office for Rent in Dubai", "subtitle": "Furnished offices, flexible workspaces and Ejari options", "image": "panorama"})
    os.makedirs(OUT, exist_ok=True)
    font_uri = data_uri(FONT, "font/woff2")
    logo_uri = data_uri(os.path.join(ROOT, "assets", "img", "logo-lockup.png"), "image/png")
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        page = browser.new_page(viewport={"width": 1200, "height": 630}, device_scale_factor=1)
        for it in items:
            html = page_html(it["title"], it.get("subtitle", ""), image_uri(it["image"]), font_uri, logo_uri)
            page.set_content(html, wait_until="load")
            page.evaluate("document.fonts.ready")
            page.screenshot(path=os.path.join(OUT, f"{it['key']}.jpg"), type="jpeg", quality=86)
            print("og", it["key"])
        browser.close()


if __name__ == "__main__":
    sys.exit(main())
