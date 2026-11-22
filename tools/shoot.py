"""Screenshot pages of the built site for visual review.

Usage: python3 tools/shoot.py http://localhost:8080 out_dir /path/ [/path2/ ...]
"""
import os
import sys

from playwright.sync_api import sync_playwright

CHROME = os.environ.get("CHROME_PATH", "/usr/bin/google-chrome")


def main():
    base, out = sys.argv[1], sys.argv[2]
    paths = sys.argv[3:]
    os.makedirs(out, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        for label, vp in (("desktop", {"width": 1440, "height": 900}), ("mobile", {"width": 390, "height": 844})):
            ctx = browser.new_context(viewport=vp, device_scale_factor=1, reduced_motion="reduce",
                                      is_mobile=(label == "mobile"), has_touch=(label == "mobile"))
            page = ctx.new_page()
            errors = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
            for path in paths:
                page.goto(base + path, wait_until="networkidle")
                name = (path.strip("/").replace("/", "_") or "home") + f"-{label}.png"
                page.screenshot(path=os.path.join(out, name), full_page=True)
                print("shot", name)
            if errors:
                print("ERRORS", label, errors)
            ctx.close()
        browser.close()


if __name__ == "__main__":
    main()
