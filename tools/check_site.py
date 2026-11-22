"""Quality checks for the built site in dist/.

    python3 tools/check_site.py              static checks
    python3 tools/check_site.py --browser    also checks mobile overflow and JS errors (needs a server on :8080
                                             that serves dist/ at the site's folder, e.g. /property-rent-hub/)
"""
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from urllib.parse import urlsplit

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, "dist")
CFG = json.load(open(os.path.join(ROOT, "site.json")))
SITE = CFG["site_url"].rstrip("/")
BASE = urlsplit(SITE).path.rstrip("/")  # "/property-rent-hub" on a GitHub project site
WA = CFG["whatsapp_number"]
# Owner's instruction: no prices, fees, VAT or other cost figures anywhere on the site.
PRICE_PATTERNS = [r"(?i)AED\s?\d", r"(?i)\bdhs?\.?\s?\d", r"\bVAT\b", r"\d\s?%", r"(?i)\bper cent\b",
                  r"(?i)previously advertised", r"(?i)price guide", r"(?i)\bprices?\b"]

problems = []


def problem(page, msg):
    problems.append(f"{page}: {msg}")


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.h1 = 0
        self.headings = []
        self.links = []
        self.imgs = []
        self.title = ""
        self._in_title = False
        self.meta = {}
        self.canonical = None
        self.jsonld = []
        self._in_ld = False
        self._buf = ""
        self.ids = set()
        self.wa = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            if a["id"] in self.ids:
                self.dup_id = a["id"]
            self.ids.add(a["id"])
        if tag == "h1":
            self.h1 += 1
        if re.fullmatch(r"h[1-6]", tag):
            self.headings.append(int(tag[1]))
        if tag == "a" and "href" in a:
            self.links.append(a["href"])
            if "wa.me" in a["href"]:
                self.wa.append(a)
        if tag == "img":
            self.imgs.append(a)
        if tag == "title":
            self._in_title = True
        if tag == "meta":
            k = a.get("name") or a.get("property")
            if k:
                self.meta[k] = a.get("content", "")
        if tag == "link" and a.get("rel") == "canonical":
            self.canonical = a.get("href")
        if tag == "script" and a.get("type") == "application/ld+json":
            self._in_ld = True
            self._buf = ""

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        if tag == "script" and self._in_ld:
            self._in_ld = False
            self.jsonld.append(self._buf)

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        if self._in_ld:
            self._buf += data


def html_files():
    for dirpath, _, files in os.walk(DIST):
        for f in files:
            if f.endswith(".html"):
                yield os.path.join(dirpath, f)


def url_for(path):
    rel = "/" + os.path.relpath(path, DIST).replace(os.sep, "/")
    return rel[: -len("index.html")] if rel.endswith("/index.html") else rel


def site_path(href):
    """Root-relative link -> path inside dist/, or None if it misses the base folder."""
    if BASE:
        if href != BASE and not href.startswith(BASE + "/"):
            return None
        href = href[len(BASE):] or "/"
    return href


def resolve(href):
    path = href.split("#")[0].split("?")[0]
    if path.endswith("/"):
        path += "index.html"
    return os.path.join(DIST, path.lstrip("/"))


def main():
    titles, descs = {}, {}
    pages = {}
    for f in sorted(html_files()):
        u = url_for(f)
        p = Page()
        text = open(f, encoding="utf-8").read()
        p.feed(text)
        pages[u] = p
        visible = re.sub(r"<script.*?</script>|<[^>]+>", " ", text, flags=re.S)
        for pat in PRICE_PATTERNS:
            for m in re.finditer(pat, visible):
                problem(u, f"price, fee or VAT on the page: '{visible[max(0, m.start() - 30):m.end() + 20].strip()}'")
        noindex = "noindex" in p.meta.get("robots", "")
        if p.h1 != 1:
            problem(u, f"{p.h1} h1 elements")
        prev = 1
        for lvl in p.headings[1:]:
            if lvl > prev + 1:
                problem(u, f"heading jumps from h{prev} to h{lvl}")
            prev = lvl
        if not p.title.strip():
            problem(u, "missing title")
        if not noindex:
            titles.setdefault(p.title, []).append(u)
            descs.setdefault(p.meta.get("description", ""), []).append(u)
            if len(p.title) > 65:
                problem(u, f"title {len(p.title)} chars")
            d = p.meta.get("description", "")
            if not 70 <= len(d) <= 165:
                problem(u, f"meta description {len(d)} chars")
            if not p.canonical or not p.canonical.startswith(SITE):
                problem(u, "canonical missing or not absolute")
            elif p.canonical != SITE + u:
                problem(u, f"canonical {p.canonical} != page URL")
        for k in ("og:title", "og:description", "og:image", "og:url", "twitter:card"):
            if k not in p.meta and u != "/404.html":
                problem(u, f"missing {k}")
        og = p.meta.get("og:image", "")
        if og.startswith(SITE) and not os.path.exists(os.path.join(DIST, og[len(SITE):].lstrip("/"))):
            problem(u, f"og:image file missing {og}")
        for href in p.links:
            if href.startswith("/") and not href.startswith("//"):
                local = site_path(href)
                if local is None:
                    problem(u, f"link without the {BASE} folder: {href}")
                    continue
                if not os.path.exists(resolve(local)):
                    problem(u, f"broken link {href}")
                frag = local.partition("#")[2]
                if frag and local.split("#")[0] in ("", u):
                    if frag not in p.ids:
                        problem(u, f"missing anchor #{frag}")
            elif href.startswith("#") and len(href) > 1 and href[1:] not in p.ids:
                problem(u, f"missing anchor {href}")
        for a in p.wa:
            if f"wa.me/{WA}" not in a["href"]:
                problem(u, f"WhatsApp link with wrong number: {a['href'][:60]}")
            if "data-wa" not in a:
                problem(u, "WhatsApp link without tracking attribute")
        eager = 0
        for img in p.imgs:
            if "alt" not in img:
                problem(u, f"img without alt {img.get('src')}")
            if not img.get("width") or not img.get("height"):
                problem(u, f"img without width/height {img.get('src')}")
            if img.get("loading") != "lazy" and "brand-logo" not in (img.get("class") or ""):
                eager += 1
            src = img.get("src", "")
            if src.startswith("/"):
                local = site_path(src)
                if local is None or not os.path.exists(resolve(local)):
                    problem(u, f"missing image {src}")
        if eager > 1:
            problem(u, f"{eager} images not lazy-loaded")
        for blob in p.jsonld:
            try:
                data = json.loads(blob)
            except Exception as e:  # noqa
                problem(u, f"invalid JSON-LD: {e}")
                continue
            types = [n.get("@type") for n in data.get("@graph", [])]
            if "Organization" not in types:
                problem(u, "JSON-LD without Organization")
            if u not in ("/",) and "BreadcrumbList" not in types:
                problem(u, "JSON-LD without BreadcrumbList")
            if "LocalBusiness" in types or "RealEstateAgent" in types:
                if not CFG["business"].get("address_verified"):
                    problem(u, "LocalBusiness data published without a verified address")
        if not p.jsonld and u != "/404.html":
            problem(u, "no JSON-LD")
    for t, us in titles.items():
        if len(us) > 1:
            problem(",".join(us), f"duplicate title '{t}'")
    for d, us in descs.items():
        if len(us) > 1:
            problem(",".join(us), "duplicate meta description")

    # sitemap
    tree = ET.parse(os.path.join(DIST, "sitemap.xml"))
    ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    locs = [e.text for e in tree.getroot().findall("s:url/s:loc", ns)]
    for loc in locs:
        path = loc[len(SITE):]
        if not os.path.exists(resolve(path)):
            problem("sitemap", f"URL without file {loc}")
        p = pages.get(path)
        if p and "noindex" in p.meta.get("robots", ""):
            problem("sitemap", f"noindex page in sitemap {loc}")
    indexable = [u for u, p in pages.items() if "noindex" not in p.meta.get("robots", "")]
    missing = set(indexable) - {l[len(SITE):] for l in locs}
    for m in sorted(missing):
        problem("sitemap", f"indexable page missing from sitemap {m}")
    robots = open(os.path.join(DIST, "robots.txt")).read()
    if f"Sitemap: {SITE}/sitemap.xml" not in robots:
        problem("robots.txt", "sitemap line missing")
    css = open(os.path.join(DIST, "assets", "css", "site.css"), encoding="utf-8").read()
    if f'url("{BASE}/assets/fonts/archivo-var.woff2")' not in css:
        problem("site.css", "font URL does not match the site folder")
    man = json.load(open(os.path.join(DIST, "site.webmanifest")))
    if man["start_url"] != BASE + "/" or not all(i["src"].startswith(BASE + "/assets/") for i in man["icons"]):
        problem("site.webmanifest", "paths do not match the site folder")
    if CFG.get("hosting") == "github-pages" and not os.path.exists(os.path.join(DIST, ".nojekyll")):
        problem("dist", ".nojekyll missing for GitHub Pages")

    print(f"Checked {len(pages)} HTML pages, {len(locs)} sitemap URLs.")
    if "--browser" in sys.argv:
        browser_checks(list(pages.keys()))
    if problems:
        print(f"{len(problems)} problem(s):")
        for p in problems:
            print("  -", p)
        sys.exit(1)
    print("No problems found.")


def browser_checks(urls):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path=os.environ.get("CHROME_PATH", "/usr/bin/google-chrome"), args=["--no-sandbox"])
        for label, vp in (("mobile-360", {"width": 360, "height": 780}), ("desktop", {"width": 1366, "height": 860})):
            ctx = b.new_context(viewport=vp)
            page = ctx.new_page()
            errs = []
            page.on("pageerror", lambda e: errs.append(str(e)))
            for u in urls:
                page.goto("http://localhost:8080" + BASE + u, wait_until="load")
                sw = page.evaluate("document.documentElement.scrollWidth")
                cw = page.evaluate("document.documentElement.clientWidth")
                if sw > cw + 1:
                    wide = page.evaluate("""() => { const W=document.documentElement.clientWidth; const out=[];
                        for (const el of document.querySelectorAll('body *')) { const r=el.getBoundingClientRect();
                          if (r.right > W + 1 && r.width > 0) out.push(el.tagName.toLowerCase()+'.'+[...el.classList].join('.')); }
                        return out.slice(0,5); }""")
                    problem(u, f"{label}: horizontal overflow {sw}>{cw} {wide}")
                if errs:
                    problem(u, f"{label}: JS errors {errs}")
                    errs.clear()
            ctx.close()
        b.close()


if __name__ == "__main__":
    main()
