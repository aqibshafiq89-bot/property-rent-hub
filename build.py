#!/usr/bin/env python3
"""Property Rent Hub static site generator.

Python 3.10+ with no third-party packages. Reads site.json and content/,
writes a complete static website to dist/ (ready to upload to any host).

    python3 build.py             build dist/ (production, clean URLs)
    python3 build.py --preview   build preview/ (relative links, for opening files locally)
    python3 build.py --all       build both
"""
import datetime as _dt
import hashlib
import html
import json
import math
import os
import re
import shutil
import sys
from urllib.parse import quote, urlsplit

ROOT = os.path.dirname(os.path.abspath(__file__))
CONTENT = os.path.join(ROOT, "content")
ASSETS = os.path.join(ROOT, "assets")
TODAY = _dt.date.today().isoformat()
PLACEHOLDER_DOMAIN = "https://www.example.com"

WARNINGS = []


def warn(msg):
    WARNINGS.append(msg)


# ============================================================== loading

def load_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def parse_content(path):
    """A content file starts with a JSON block inside <!-- -->, then HTML."""
    with open(path, encoding="utf-8") as fh:
        raw = fh.read()
    m = re.match(r"\s*<!--(.*?)-->(.*)$", raw, re.S)
    if not m:
        raise ValueError(f"{path}: missing JSON front matter")
    meta = json.loads(m.group(1))
    return meta, m.group(2).strip()


def esc(s):
    return html.escape(str(s), quote=True)


def slugify(text):
    text = re.sub(r"<[^>]+>", "", text).lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text[:60] or "section"


def strip_tags(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s)).strip()


def fmt_date(iso):
    d = _dt.date.fromisoformat(iso)
    return f"{d.day} {d.strftime('%B %Y')}"


class Site:
    def __init__(self):
        self.cfg = load_json(os.path.join(ROOT, "site.json"))
        self.url = self.cfg["site_url"].rstrip("/")
        parts = urlsplit(self.url)
        self.host = parts.hostname or ""
        # "" when the site sits at the root of its domain; "/property-rent-hub" for a GitHub project site.
        self.base = parts.path.rstrip("/")
        self.hosting = self.cfg.get("hosting", "")
        if self.url == PLACEHOLDER_DOMAIN:
            warn("site_url in site.json is still the placeholder (www.example.com). Set your real domain before going live.")
        self.home = load_json(os.path.join(CONTENT, "pages", "home.json"))
        self.faq = load_json(os.path.join(CONTENT, "pages", "faq.json"))
        self.about = parse_content(os.path.join(CONTENT, "pages", "about.html"))
        self.privacy = parse_content(os.path.join(CONTENT, "pages", "privacy.html"))
        self.locations = []
        for name in os.listdir(os.path.join(CONTENT, "locations")):
            if name.endswith(".html"):
                meta, body = parse_content(os.path.join(CONTENT, "locations", name))
                meta["body"] = body
                self.locations.append(meta)
        self.locations.sort(key=lambda m: m["order"])
        self.loc_by_key = {m["key"]: m for m in self.locations}
        props = load_json(os.path.join(CONTENT, "properties.json"))["properties"]
        self.properties = [p for p in props if p.get("status") != "hidden"]
        for p in self.properties:
            if p["location"] not in self.loc_by_key:
                raise ValueError(f"Property {p['ref']} has unknown location {p['location']}")
            p["path"] = f"/offices/{p['slug']}/"
            p["indexable"] = bool(p.get("size_sqft")) and len(p.get("photos") or []) >= 3
            if not p["indexable"]:
                warn(f"Property {p['ref']} is published with noindex until it has a size and at least 3 photos.")
            if not p.get("trakheesi_permit"):
                warn(f"Property {p['ref']} has no advertising permit number. Check with the Dubai Land Department whether one is needed.")
        self.posts = []
        for name in os.listdir(os.path.join(CONTENT, "blog")):
            if name.endswith(".html"):
                meta, body = parse_content(os.path.join(CONTENT, "blog", name))
                meta["body"] = body
                meta["path"] = f"/blog/{meta['slug']}/"
                words = len(strip_tags(body).split())
                meta["words"] = words
                meta["minutes"] = max(1, math.ceil(words / 220))
                self.posts.append(meta)
        self.posts.sort(key=lambda m: (m["date_published"], m["title"]), reverse=True)
        self.post_by_slug = {p["slug"]: p for p in self.posts}
        self.version = {}
        for rel in ("css/site.css", "js/site.js"):
            with open(os.path.join(ASSETS, rel), "rb") as fh:
                self.version[rel] = hashlib.md5(fh.read()).hexdigest()[:10]

    def abs(self, path):
        return self.url + path

    # ---------------------------------------------------------- WhatsApp
    def wa(self, message):
        return f"https://wa.me/{self.cfg['whatsapp_number']}?text={quote(message, safe='')}"


# ============================================================== icons

ICON_WA = ('<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path fill="currentColor" d="M17.47 14.38c-.3-.15-1.76-.87-2.03-.97-.27-.1-.47-.15-.67.15-.2.3-.77.97-.94 1.16-.17.2-.35.22-.64.08-.3-.15-1.26-.46-2.39-1.48-.88-.79-1.48-1.76-1.65-2.06-.17-.3-.02-.46.13-.6.13-.14.3-.35.45-.52.15-.18.2-.3.3-.5.1-.2.05-.37-.03-.52-.07-.15-.67-1.61-.92-2.2-.24-.58-.49-.5-.67-.51h-.57c-.2 0-.52.07-.8.37-.27.3-1.04 1.02-1.04 2.48 0 1.46 1.07 2.88 1.21 3.07.15.2 2.1 3.2 5.08 4.49.71.31 1.26.49 1.7.63.71.22 1.36.19 1.87.12.57-.09 1.76-.72 2-1.41.25-.7.25-1.29.18-1.41-.08-.13-.28-.2-.57-.35m-5.42 7.4h-.01a9.87 9.87 0 0 1-5.03-1.38l-.36-.21-3.74.98 1-3.65-.24-.37a9.86 9.86 0 0 1-1.51-5.26c0-5.45 4.44-9.88 9.89-9.88 2.64 0 5.12 1.03 6.99 2.9a9.82 9.82 0 0 1 2.89 6.99c0 5.45-4.44 9.88-9.89 9.88m8.41-18.3A11.82 11.82 0 0 0 12.05 0C5.5 0 .16 5.34.16 11.89c0 2.1.55 4.14 1.59 5.95L.06 24l6.3-1.65a11.88 11.88 0 0 0 5.68 1.45h.01c6.55 0 11.89-5.34 11.89-11.89 0-3.18-1.24-6.16-3.48-8.41"/></svg>')
ICON_PHONE = ('<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path fill="currentColor" d="M6.6 10.8a15.2 15.2 0 0 0 6.6 6.6l2.2-2.2c.3-.3.7-.4 1-.2 1.1.4 2.3.6 3.6.6.6 0 1 .4 1 1V20c0 .6-.4 1-1 1A17 17 0 0 1 3 4c0-.6.4-1 1-1h3.5c.6 0 1 .4 1 1 0 1.3.2 2.5.6 3.6.1.3 0 .7-.2 1z"/></svg>')
# The logo artwork lives in brand/logo-original.png; tools/make_logo.py prepares these files.
LOGO_HEADER = ('<img class="brand-logo" src="/assets/img/logo-lockup.webp" width="274" height="48" '
               'alt="Property Rent Hub">')
LOGO_FOOTER = ('<img class="footer-logo" src="/assets/img/logo-full.webp" width="210" height="156" '
               'alt="Property Rent Hub" loading="lazy" decoding="async">')


# ============================================================== components

def wa_button(site, label, message, placement, area="", ref="", cls="btn btn-wa", icon=True):
    attrs = f' data-wa="{esc(placement)}"'
    if area:
        attrs += f' data-area="{esc(area)}"'
    if ref:
        attrs += f' data-ref="{esc(ref)}"'
    ic = ICON_WA if icon else ""
    return (f'<a class="{cls}" href="{esc(site.wa(message))}" target="_blank" rel="noopener"{attrs}>'
            f'{ic}<span>{esc(label)}</span></a>')


def phone_link(site, placement, cls="btn btn-ghost", label=None):
    lab = label or site.cfg["phone_display"]
    return (f'<a class="{cls}" href="tel:{esc(site.cfg["phone_e164"])}" data-place="{esc(placement)}">'
            f'{ICON_PHONE}<span class="nowrap">{esc(lab)}</span></a>')


def msg_with_ref(text, ref):
    return f"{text}\nRef: {ref}"


def loc_messages(loc):
    name = loc.get("long_name", loc["name"])
    code = loc["wa_code"]
    return {
        "availability": msg_with_ref(f"Hello Property Rent Hub, I'm looking for an office in {name}. Please share current availability and rental details.\nTeam size: \nMove-in date: ", code),
        "viewing": msg_with_ref(f"Hello Property Rent Hub, I'd like to book an office viewing in {name}. Which times are available?", code),
    }


def prop_messages(p, loc):
    what = f"the {p['type'].lower()} in {loc['name']} (ref {p['ref']})"
    return {
        "details": f"Hello Property Rent Hub, I'm interested in {what}. Please share availability, rental details and Ejari information.\nTeam size: \nMove-in date: ",
        "viewing": f"Hello Property Rent Hub, I'd like to book a viewing of {what}. Which times are available?",
    }


def generic_message(code):
    return msg_with_ref("Hello Property Rent Hub, I'd like details about offices for rent in Dubai.", code)


def picture(name, alt, sizes, eager=False, cls="", ratio=(16, 9), widths=(480, 800, 1200, 1600)):
    w, h = 1600, round(1600 * ratio[1] / ratio[0])
    avif = ", ".join(f"/assets/img/{name}-{x}.avif {x}w" for x in widths)
    webp = ", ".join(f"/assets/img/{name}-{x}.webp {x}w" for x in widths)
    loading = 'fetchpriority="high" loading="eager"' if eager else 'loading="lazy"'
    c = f' class="{cls}"' if cls else ""
    return (f'<picture{c}><source type="image/avif" srcset="{avif}" sizes="{sizes}">'
            f'<source type="image/webp" srcset="{webp}" sizes="{sizes}">'
            f'<img src="/assets/img/{name}-1200.webp" alt="{esc(alt)}" width="{w}" height="{h}" {loading} decoding="async"></picture>')


def ejari_label(v):
    return {"included": "Ejari included", "available": "Ejari available",
            "not-available": "Ejari not available"}.get(v, "Ejari: ask us to confirm")


def ejari_value(v):
    return {"included": "Included", "available": "Available", "not-available": "Not available"}.get(
        v, "Ask us to confirm it for your business activity")


def directory(site, rows, light=False):
    out = ['<ul class="directory">']
    for r in rows:
        out.append('<li class="dir-row">'
                   f'<div class="dir-area"><a href="{r["href"]}">{esc(r["area"])}</a><small>{esc(r["sub"])}</small></div>'
                   f'<div class="dir-type">{esc(r["type"])}<small>{esc(r["type_sub"])}</small></div>'
                   f'<div class="dir-action">{r["action"]}</div></li>')
    out.append('</ul>')
    return "".join(out)


def property_row(site, p):
    loc = site.loc_by_key[p["location"]]
    m = prop_messages(p, loc)
    area = loc.get("long_name", loc["name"])
    if p["location"] == "port-saeed":
        area = "Port Saeed, Deira"
    return {
        "href": p["path"], "area": area, "sub": f"Ref {p['ref']}",
        "type": p["type"], "type_sub": ejari_label(p.get("ejari")),
        "action": wa_button(site, "Get Rental Details", m["details"], "directory", area=loc["key"], ref=p["ref"]),
    }


def request_row(site, loc):
    m = loc_messages(loc)
    return {
        "href": loc["path"], "area": loc.get("long_name", loc["name"]), "sub": loc["descriptor"],
        "type": "Private offices and workspaces", "type_sub": "Options shared on request",
        "action": wa_button(site, "Check Office Availability", m["availability"], "directory", area=loc["key"]),
    }


def directory_rows(site, only_location=None):
    rows = []
    for loc in site.locations:
        if only_location and loc["key"] != only_location:
            continue
        props = [p for p in site.properties if p["location"] == loc["key"] and p.get("status") == "available"]
        if props:
            rows.extend(property_row(site, p) for p in props)
        else:
            rows.append(request_row(site, loc))
    return rows


def faq_html(items):
    out = ['<div class="faq">']
    for it in items:
        out.append(f'<details><summary>{esc(it["q"])}</summary><div class="answer">{it["a"]}</div></details>')
    out.append('</div>')
    return "".join(out)


def _options(pairs, selected=""):
    out = []
    for val, text in pairs:
        sel = " selected" if selected and val == selected else ""
        out.append(f'<option value="{esc(val)}"{sel}>{esc(text)}</option>')
    return "".join(out)


ENQUIRY_CHOICES = {
    "people": [("", "Choose"), ("1", "1 person"), ("2", "2 people"), ("3-5", "3 to 5 people"), ("6-10", "6 to 10 people"),
               ("11-20", "11 to 20 people"), ("20+", "More than 20 people")],
    "type": [("", "Choose"), ("furnished-private", "Furnished private office"), ("serviced", "Serviced office"),
             ("shared", "Shared workspace or desk"), ("virtual", "Virtual office"), ("unfurnished", "Unfurnished office"),
             ("not-sure", "Not sure yet")],
    "movein": [("", "Choose"), ("asap", "As soon as possible"), ("1-month", "Within a month"), ("1-3-months", "In 1 to 3 months"),
               ("3-months+", "In more than 3 months"), ("researching", "Just researching")],
    "ejari": [("", "Choose"), ("yes", "Yes"), ("no", "No"), ("not-sure", "Not sure")],
    "licence": [("", "Choose"), ("mainland", "I have a mainland (DET) trade licence"), ("free-zone", "I have a free zone licence"),
                ("new-company", "I'm setting up a new company"), ("not-sure", "Not sure yet")],
    "contract": [("", "Choose"), ("12-months", "12 months"), ("under-12", "Less than 12 months"),
                 ("over-12", "More than 12 months"), ("not-sure", "Not sure yet")],
    "viewing": [("", "Choose"), ("morning", "Morning"), ("afternoon", "Afternoon"), ("evening", "Evening"), ("any", "Any time")],
}


def enquiry_form(site, placement, source, preset_area="", prop=None, level=3, title="Office enquiry form",
                 expanded=False, compact=False, ref="WEB-FORM"):
    """Office enquiry form. On submit, site.js opens WhatsApp with every answer filled in."""
    uid = re.sub(r"[^a-z0-9]", "", placement.lower())[:16] or "form"
    locs = [("", "Choose a location")] + [(l["key"], l.get("long_name", l["name"])) for l in site.locations] + [("any", "Any location or not sure")]
    c = ENQUIRY_CHOICES

    def text_field(name, label, kind="text", required=False, auto="", extra="", hint="", span=False, short=None):
        fid = f"{uid}-{name}"
        req = ' required aria-required="true"' if required else ""
        mark = '<span class="req" aria-hidden="true">*</span>' if required else ""
        hint_html = f'<span class="hint" id="{fid}-hint">{esc(hint)}</span>' if hint else ""
        described = f' aria-describedby="{fid}-hint"' if hint else ""
        auto_attr = f' autocomplete="{auto}"' if auto else ""
        cls = "field span-2" if span else "field"
        if kind == "textarea":
            control = f'<textarea id="{fid}" name="{name}" rows="3" data-label="{esc(short or label)}"{req}{described}{extra}></textarea>'
        else:
            control = f'<input id="{fid}" name="{name}" type="{kind}" data-label="{esc(short or label)}"{auto_attr}{req}{described}{extra}>'
        return f'<div class="{cls}"><label for="{fid}">{esc(label)}{mark}</label>{control}{hint_html}</div>'

    def select_field(name, label, options, required=False, selected="", short=None):
        fid = f"{uid}-{name}"
        req = ' required aria-required="true"' if required else ""
        mark = '<span class="req" aria-hidden="true">*</span>' if required else ""
        return (f'<div class="field"><label for="{fid}">{esc(label)}{mark}</label>'
                f'<select id="{fid}" name="{name}" data-label="{esc(short or label)}"{req}>{_options(options, selected)}</select></div>')

    office_attr = ""
    if prop:
        loc = site.loc_by_key[prop["location"]]
        office_attr = (f' data-office="{esc(prop["title"])} (ref {esc(prop["ref"])})"'
                       f' data-ref-code="{esc(prop["ref"])}"')
        preset_area = preset_area or loc["key"]
        ref = prop["ref"]
    phone = site.cfg["phone_display"]
    return f'''<form class="enquiry{' compact' if compact else ''}" data-enquiry data-number="{esc(site.cfg['whatsapp_number'])}" data-source="{esc(source)}" data-ref="{esc(ref)}" data-placement="{esc(placement)}"{office_attr} action="https://wa.me/{esc(site.cfg['whatsapp_number'])}" method="get" target="_blank" aria-labelledby="{uid}-title">
<h{level} class="enquiry-title" id="{uid}-title">{esc(title)}</h{level}>
<p class="enquiry-intro">Tell us what you need. When you press the button, WhatsApp opens with your answers filled in. Tap Send and your enquiry comes straight to us.</p>
<p class="enquiry-req">Fields marked <span class="req" aria-hidden="true">*</span><span class="visually-hidden">with an asterisk</span> are required.</p>
<fieldset><legend>Your details</legend><div class="grid">
{text_field("name", "Full name", required=True, auto="name", short="Name")}
{text_field("phone", "Mobile or WhatsApp number", kind="tel", required=True, auto="tel", short="Phone", extra=' inputmode="tel" placeholder="+971 5X XXX XXXX"', hint="Include the country code, e.g. +971 50 123 4567")}
{text_field("email", "Email", kind="email", auto="email", extra=' placeholder="name@company.com"')}
{text_field("company", "Company name", auto="organization", short="Company")}
</div></fieldset>
<fieldset><legend>Office requirements</legend><div class="grid">
{select_field("location", "Preferred location", locs, required=True, selected=preset_area, short="Location")}
{select_field("people", "Number of people", c["people"], required=True)}
{select_field("type", "Office type", c["type"])}
{select_field("movein", "Move-in", c["movein"])}
{text_field("budget", "Yearly budget", short="Budget")}
{select_field("ejari", "Do you need Ejari?", c["ejari"], short="Ejari needed")}
</div></fieldset>
<details class="more"{' open' if expanded else ''}><summary>More details (optional)</summary><div class="grid">
{select_field("licence", "Trade licence", c["licence"])}
{select_field("contract", "Contract length", c["contract"])}
{text_field("activity", "Business activity", extra=' placeholder="e.g. General trading, IT consultancy"')}
{select_field("viewing", "Preferred viewing time", c["viewing"], short="Viewing time")}
{text_field("message", "Anything else we should know?", kind="textarea", span=True, short="Message")}
</div></details>
<button class="btn btn-wa btn-send" type="submit">{ICON_WA}<span>Get Rental Details on WhatsApp</span></button>
<p class="enquiry-privacy">Your answers go into a WhatsApp message to {esc(phone)}; this website does not store them. <a href="/privacy-policy/">Privacy policy</a></p>
<div class="enquiry-status" data-status role="status" aria-live="polite"></div>
</form>'''


def post_cards(site, posts, cls="posts", heading_tag="h3"):
    out = [f'<ul class="{cls}">']
    for p in posts:
        out.append(f'<li><{heading_tag}><a href="{p["path"]}">{esc(p["title"])}</a></{heading_tag}><p>{esc(p["excerpt"])}</p></li>')
    out.append('</ul>')
    return "".join(out)


def crumbs_html(items):
    out = ['<nav class="crumbs wrap" aria-label="Breadcrumb"><ol>']
    for i, (name, path) in enumerate(items):
        if i == len(items) - 1:
            out.append(f'<li><span aria-current="page">{esc(name)}</span></li>')
        else:
            out.append(f'<li><a href="{path}">{esc(name)}</a></li>')
    out.append('</ol></nav>')
    return "".join(out)


def cta_band(site, heading, text, message, placement, area=""):
    return (f'<section class="band navy on-navy" aria-labelledby="cta-{placement}"><div class="wrap split">'
            f'<div><h2 id="cta-{placement}">{esc(heading)}</h2><p class="lede" style="color:inherit">{esc(text)}</p></div>'
            f'<div><div class="btn-row" style="margin-top:0">{wa_button(site, "Book Your Office Viewing", message, placement, area=area)}'
            f'{phone_link(site, placement)}</div>'
            f'<p class="small muted" style="margin-top:14px">WhatsApp or call {esc(site.cfg["phone_display"])}</p></div>'
            '</div></section>')


def enquiry_band(site, heading, text, placement, source, viewing_message, area="", prop=None):
    steps = ("<ol class=\"steps\">"
             "<li><h3>Send your enquiry</h3><p>Fill in the form; WhatsApp opens with your answers ready to send.</p></li>"
             "<li><h3>Get matching offices</h3><p>We reply with available offices, rental details, what is included and Ejari information.</p></li>"
             "<li><h3>Book your viewing</h3><p>Choose a time and see the office in person.</p></li></ol>")
    return (f'<section class="band navy on-navy" id="enquiry" aria-labelledby="{placement}-h"><div class="wrap split">'
            f'<div><h2 id="{placement}-h">{esc(heading)}</h2><p class="lede" style="color:inherit">{esc(text)}</p>{steps}'
            f'<div class="btn-row">{wa_button(site, "Book Your Office Viewing", viewing_message, placement + "-viewing", area=area, ref=(prop or {}).get("ref", ""))}'
            f'{phone_link(site, placement)}</div></div>'
            f'<div>{enquiry_form(site, placement, source, preset_area=area, prop=prop, level=3)}</div>'
            '</div></section>')


def inline_cta(site, loc_key=None, post=None):
    if loc_key and loc_key in site.loc_by_key:
        loc = site.loc_by_key[loc_key]
        m = loc_messages(loc)
        return (f'<aside class="cta-box" aria-label="Offices in {esc(loc["name"])}"><p class="cta-title">Looking for an office in {esc(loc["name"])}?</p>'
                f'<p>{esc(loc["rental_note"])}</p><div class="btn-row">'
                f'{wa_button(site, "Check Office Availability", m["availability"], "article-cta", area=loc_key)}'
                f'<a class="btn btn-ghost" href="{loc["path"]}" style="color:#fff;border-color:#D9B76E">See {esc(loc["name"])} offices</a></div></aside>')
    title = post["title"] if post else "an office guide"
    msg = msg_with_ref(f"Hello Property Rent Hub, I read your guide \"{title}\" and I'm looking for an office in Dubai.\nArea: \nTeam size: ", "WEB-BLOG")
    return ('<aside class="cta-box" aria-label="Get office options"><p class="cta-title">Want options that fit your budget?</p>'
            '<p>Tell us your preferred area, team size and move-in date. We will reply on WhatsApp with offices that match, including rental details and Ejari information.</p>'
            f'<div class="btn-row">{wa_button(site, "Contact Us on WhatsApp", msg, "article-cta")}'
            '<a class="btn btn-ghost" href="/offices/" style="color:#fff;border-color:#D9B76E">Explore Available Offices</a></div></aside>')


def expand_tokens(site, body, post=None):
    def rep(m):
        key = m.group(1)
        if key == "cta":
            return inline_cta(site, m.group(2), post)
        return m.group(0)
    return re.sub(r"\{\{(cta)(?::([\w-]+))?\}\}", rep, body)


def add_heading_ids(body):
    seen = set()
    toc = []

    def rep(m):
        attrs, text = m.group(1), m.group(2)
        if "id=" in attrs:
            return m.group(0)
        hid = slugify(text)
        base, n = hid, 2
        while hid in seen:
            hid = f"{base}-{n}"
            n += 1
        seen.add(hid)
        toc.append((hid, strip_tags(text)))
        return f'<h2{attrs} id="{hid}">{text}</h2>'
    body = re.sub(r"<h2([^>]*)>(.*?)</h2>", rep, body, flags=re.S)
    return body, toc


def wrap_tables(body):
    return body


# ============================================================== schema

def org_node(site):
    cfg = site.cfg
    node = {
        "@type": "Organization",
        "@id": site.abs("/#organization"),
        "name": cfg["site_name"],
        "url": site.abs("/"),
        "logo": {"@type": "ImageObject", "url": site.abs(cfg["logo_path"]), "width": 512, "height": 512},
        "telephone": cfg["phone_e164"],
        "contactPoint": [{
            "@type": "ContactPoint",
            "telephone": cfg["phone_e164"],
            "contactType": "sales",
            "areaServed": "AE",
        }],
    }
    if cfg.get("email"):
        node["email"] = cfg["email"]
    if cfg.get("social_profiles"):
        node["sameAs"] = cfg["social_profiles"]
    b = cfg["business"]
    if b.get("address_verified") and b.get("street_address"):
        node["address"] = postal_address(b)
    return node


def postal_address(b):
    a = {"@type": "PostalAddress", "streetAddress": b["street_address"], "addressLocality": b["address_locality"],
         "addressRegion": b["address_region"], "addressCountry": b["address_country"]}
    if b.get("postal_code"):
        a["postalCode"] = b["postal_code"]
    return a


def local_business_node(site):
    """Only for a genuine, verified business location (see site.json)."""
    b = site.cfg["business"]
    if not (b.get("address_verified") and b.get("street_address")):
        return None
    node = {
        "@type": "RealEstateAgent",
        "@id": site.abs("/#business"),
        "name": b.get("legal_name") or site.cfg["site_name"],
        "url": site.abs("/"),
        "image": site.abs("/assets/og/default.jpg"),
        "telephone": site.cfg["phone_e164"],
        "address": postal_address(b),
        "parentOrganization": {"@id": site.abs("/#organization")},
        "areaServed": [{"@type": "Place", "name": f"{l.get('long_name', l['name'])}, Dubai"} for l in site.locations],
    }
    if b.get("latitude") is not None and b.get("longitude") is not None:
        node["geo"] = {"@type": "GeoCoordinates", "latitude": b["latitude"], "longitude": b["longitude"]}
    if b.get("google_maps_url"):
        node["hasMap"] = b["google_maps_url"]
    if b.get("opening_hours"):
        node["openingHoursSpecification"] = [
            {"@type": "OpeningHoursSpecification", "dayOfWeek": h["days"], "opens": h["opens"], "closes": h["closes"]}
            for h in b["opening_hours"]]
    return node


def website_node(site):
    return {"@type": "WebSite", "@id": site.abs("/#website"), "url": site.abs("/"), "name": site.cfg["site_name"],
            "publisher": {"@id": site.abs("/#organization")}, "inLanguage": site.cfg["language"]}


def webpage_node(site, page, typ="WebPage", extra=None):
    node = {"@type": typ, "@id": site.abs(page["path"]) + "#webpage", "url": site.abs(page["path"]),
            "name": page["title"], "description": page["description"], "isPartOf": {"@id": site.abs("/#website")},
            "inLanguage": site.cfg["language"]}
    if page.get("crumbs") and len(page["crumbs"]) > 1:
        node["breadcrumb"] = {"@id": site.abs(page["path"]) + "#breadcrumb"}
    if page.get("og_image_abs"):
        node["primaryImageOfPage"] = {"@type": "ImageObject", "url": page["og_image_abs"]}
    if page.get("modified"):
        node["dateModified"] = page["modified"]
    if extra:
        node.update(extra)
    return node


def breadcrumb_node(site, page):
    items = []
    for i, (name, path) in enumerate(page["crumbs"]):
        items.append({"@type": "ListItem", "position": i + 1, "name": name, "item": site.abs(path)})
    return {"@type": "BreadcrumbList", "@id": site.abs(page["path"]) + "#breadcrumb", "itemListElement": items}


def graph(nodes):
    data = {"@context": "https://schema.org", "@graph": [n for n in nodes if n]}
    txt = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    return txt.replace("</", "<\\/")


# ============================================================== layout

def head_analytics(site):
    a = site.cfg["analytics"]
    if a.get("gtm_container_id"):
        gid = esc(a["gtm_container_id"])
        return ("<script>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':new Date().getTime(),event:'gtm.js'});"
                "var f=d.getElementsByTagName(s)[0],j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;"
                "j.src='https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);"
                f"}})(window,document,'script','dataLayer','{gid}');</script>")
    if a.get("ga4_measurement_id"):
        gid = esc(a["ga4_measurement_id"])
        return (f'<script async src="https://www.googletagmanager.com/gtag/js?id={gid}"></script>'
                "<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}"
                f"gtag('js',new Date());gtag('config','{gid}');</script>")
    return ""


def body_analytics(site):
    a = site.cfg["analytics"]
    if a.get("gtm_container_id"):
        gid = esc(a["gtm_container_id"])
        return (f'<noscript><iframe src="https://www.googletagmanager.com/ns.html?id={gid}" height="0" width="0" '
                'style="display:none;visibility:hidden" title="Google Tag Manager"></iframe></noscript>')
    return ""


def nav_html(site, current):
    def a(path, label):
        cur = ' aria-current="page"' if current == path else ""
        return f'<a href="{path}"{cur}>{esc(label)}</a>'
    cur_attr = ' aria-current="page"'
    loc_items = "".join(
        f'<li><a href="{l["path"]}"{cur_attr if current == l["path"] else ""}>'
        f'{esc(l.get("long_name", l["name"]))}<span class="menu-note">{esc(l["descriptor"])}</span></a></li>'
        for l in site.locations)
    return (f'<nav class="primary-nav" id="primary-nav" aria-label="Main"><ul>'
            f'<li>{a("/offices/", "Offices")}</li>'
            f'<li><details><summary>Locations</summary><ul class="menu">{loc_items}</ul></details></li>'
            f'<li>{a("/blog/", "Guides")}</li><li>{a("/about/", "About")}</li>'
            f'<li>{a("/faq/", "FAQ")}</li><li>{a("/contact/", "Contact")}</li></ul></nav>')


def header_html(site, current):
    promo = ""
    p = site.cfg.get("promo") or {}
    if p.get("enabled"):
        promo = (f'<div class="promo">{esc(p["text"])} '
                 f'<a href="{esc(site.wa(msg_with_ref(p["whatsapp_message"], "WEB-PROMO")))}" target="_blank" rel="noopener" data-wa="promo-bar">{esc(p["link_text"])}</a></div>')
    phone = site.cfg["phone_display"]
    return (promo + '<header class="site-header"><div class="wrap header-inner">'
            f'<a class="brand" href="/">{LOGO_HEADER}</a>'
            f'<a class="header-call" href="tel:{esc(site.cfg["phone_e164"])}" data-place="header" aria-label="Call {esc(phone)}">{ICON_PHONE}</a>'
            '<button class="menu-toggle" type="button" aria-expanded="false" aria-controls="primary-nav">'
            '<span class="bars" aria-hidden="true"></span><span class="visually-hidden">Menu</span></button>'
            + nav_html(site, current)
            + wa_button(site, "WhatsApp", generic_message("WEB-HEADER"), "header", cls="btn btn-wa header-wa")
            + '</div></header>')


def footer_html(site):
    cfg = site.cfg
    b = cfg["business"]
    addr = ""
    if b.get("address_verified") and b.get("street_address"):
        parts = [b["street_address"], b["address_locality"]]
        addr = "<br>".join(esc(x) for x in parts if x)
        if b.get("google_maps_url"):
            addr += f'<br><a href="{esc(b["google_maps_url"])}" rel="noopener" target="_blank">View on Google Maps</a>'
        addr += "<br>"
    hours = ""
    if b.get("opening_hours"):
        hours = "<br>".join(f'{esc(", ".join(h["days"]))}: {esc(h["opens"])} to {esc(h["closes"])}' for h in b["opening_hours"]) + "<br>"
    locs = "".join(f'<li><a href="{l["path"]}">Office for rent in {esc(l.get("long_name", l["name"]))}</a></li>' for l in site.locations)
    offices = "".join(f'<li><a href="{p["path"]}">{esc(p["card_title"])}, {esc(site.loc_by_key[p["location"]]["name"])}</a></li>'
                      for p in site.properties if p.get("status") == "available")
    guides = "".join(f'<li><a href="{p["path"]}">{esc(p["title"])}</a></li>' for p in site.posts[:5])
    year = _dt.date.today().year
    return f'''<footer class="site-footer"><div class="wrap">
<div class="footer-grid">
<div class="footer-brand">
<a href="/">{LOGO_FOOTER}</a>
<p>Office rental assistance in Dubai: furnished private offices, serviced offices, shared workspaces and Ejari options in five areas.</p>
<address class="nap"><strong>{esc(cfg["site_name"])}</strong><br>{addr}{hours}
WhatsApp and phone: <a href="tel:{esc(cfg["phone_e164"])}" data-place="footer" class="nowrap">{esc(cfg["phone_display"])}</a><br>
<a href="{esc(site.wa(generic_message("WEB-FOOTER")))}" target="_blank" rel="noopener" data-wa="footer">Contact Us on WhatsApp</a></address>
</div>
<div><h2>Office locations</h2><ul>{locs}</ul></div>
<div><h2>Offices</h2><ul><li><a href="/offices/">Explore Available Offices</a></li>{offices}<li><a href="/contact/">Book Your Office Viewing</a></li></ul></div>
<div><h2>Guides</h2><ul>{guides}<li><a href="/blog/">All guides</a></li></ul></div>
</div>
<div class="footer-bottom">
<p>Pictures on this website show typical offices, not specific listings. Ask us for photos of any office.</p>
<p>&copy; {year} {esc(cfg["site_name"])}. <a href="/about/">About</a> &middot; <a href="/faq/">FAQ</a> &middot; <a href="/privacy-policy/">Privacy</a></p>
</div></div></footer>'''


def wa_float(site, message, area=""):
    """Floating WhatsApp button shown on every page."""
    a = f' data-area="{esc(area)}"' if area else ""
    return (f'<a class="wa-float" href="{esc(site.wa(message))}" target="_blank" rel="noopener" data-wa="floating"{a} '
            f'aria-label="Chat with Property Rent Hub on WhatsApp" title="Chat with us on WhatsApp">{ICON_WA}</a>')


def layout(site, page):
    cfg = site.cfg
    title = page["title"]
    desc = page["description"]
    canonical = site.abs(page["path"])
    robots = page.get("robots", "index, follow, max-image-preview:large, max-snippet:-1")
    og_img = page.get("og_image_abs") or site.abs("/assets/og/default.jpg")
    og_alt = page.get("og_image_alt", f"{cfg['site_name']}: offices for rent in Dubai")
    ver = site.version
    verif = ""
    v = cfg.get("verification", {})
    if v.get("google_site_verification"):
        verif += f'<meta name="google-site-verification" content="{esc(v["google_site_verification"])}">'
    if v.get("bing_site_verification"):
        verif += f'<meta name="msvalidate.01" content="{esc(v["bing_site_verification"])}">'
    og_extra = ""
    if page.get("og_type") == "article":
        og_extra = (f'<meta property="article:published_time" content="{esc(page["published"])}">'
                    f'<meta property="article:modified_time" content="{esc(page["modified"])}">')
    canonical_tag = f'<link rel="canonical" href="{esc(canonical)}">' if page.get("canonical", True) else ""
    schema = f'<script type="application/ld+json">{graph(page.get("schema", []))}</script>' if page.get("schema") else ""
    return f'''<!DOCTYPE html>
<html lang="{esc(cfg["language"])}" class="no-js">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
{canonical_tag}
<meta name="robots" content="{esc(robots)}">
<meta name="theme-color" content="#0A1A31">
<link rel="preload" href="/assets/fonts/archivo-var.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/assets/css/site.css?v={ver["css/site.css"]}">
<link rel="icon" href="/favicon.ico" sizes="48x48">
<link rel="icon" href="/assets/icons/favicon-32.png" sizes="32x32" type="image/png">
<link rel="apple-touch-icon" href="/assets/icons/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
<meta property="og:site_name" content="{esc(cfg["site_name"])}">
<meta property="og:locale" content="{esc(cfg["og_locale"])}">
<meta property="og:type" content="{esc(page.get("og_type", "website"))}">
<meta property="og:title" content="{esc(page.get("og_title", title))}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{esc(canonical)}">
<meta property="og:image" content="{esc(og_img)}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{esc(og_alt)}">
{og_extra}<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(page.get("og_title", title))}">
<meta name="twitter:description" content="{esc(desc)}">
<meta name="twitter:image" content="{esc(og_img)}">
{verif}<script>document.documentElement.className=document.documentElement.className.replace('no-js','js')</script>
{head_analytics(site)}{schema}
</head>
<body data-page-type="{esc(page.get("page_type", "page"))}">
{body_analytics(site)}<a class="skip" href="#main">Skip to content</a>
{header_html(site, page["path"])}
<main id="main">
{page["body"]}
</main>
{footer_html(site)}
{wa_float(site, page.get("mobile_message") or generic_message("WEB-FLOAT"), page.get("area", ""))}
<script src="/assets/js/site.js?v={ver["js/site.js"]}" defer></script>
</body>
</html>
'''


# ============================================================== OG images

def og_for(page_key):
    """Path of a generated share image, or the default."""
    p = os.path.join(ASSETS, "og", f"{page_key}.jpg")
    if os.path.exists(p):
        return f"/assets/og/{page_key}.jpg"
    return "/assets/og/default.jpg"


OG_MANIFEST = []


def register_og(key, title, subtitle, image):
    OG_MANIFEST.append({"key": key, "title": title, "subtitle": subtitle, "image": image})


# ============================================================== pages

IMAGES = load_json(os.path.join(CONTENT, "images.json"))


def is_photo(name):
    """True once a licensed photo has replaced the illustration (photos/<name>.jpg)."""
    return any(os.path.exists(os.path.join(ROOT, "photos", name + ext)) for ext in (".jpg", ".jpeg", ".png", ".webp"))


def image_caption(name):
    return IMAGES.get(name, {}).get("caption", "A typical office")


def caption(text, name):
    """Pictures show typical offices, never a specific listing, and say so."""
    return f"{text} (example photo)" if is_photo(name) else f"{text} (illustration)"


def image_alt(site, name):
    for l in site.locations:
        if l["image"] == name:
            return l["image_alt"]
    return IMAGES.get(name, {}).get("alt", "Offices in Dubai")


def strip_map(site):
    from art import panorama  # tools/art.py draws the hero illustration
    items = []
    for l in site.locations:
        label = "JLT" if l["key"] == "jlt" else l.get("long_name", l["name"])
        items.append(f'<li><a href="{l["path"]}"><span class="stop-name">{esc(label)}</span>'
                     f'<span class="stop-note">{esc(l["descriptor"])}</span></a></li>')
    if is_photo("office-hero"):
        art = picture("office-hero", IMAGES.get("office-hero", {}).get("alt", ""), "100vw", eager=True, ratio=(1600, 470))
    else:
        art = panorama(standalone=False)
    return ('<figure class="hero-figure" aria-labelledby="line-caption">'
            f'<div class="panorama-box">{art}</div>'
            f'<ol class="stops" aria-label="Office areas along the line, from Deira to JLT">{"".join(items)}</ol>'
            f'<figcaption class="stops-foot"><div class="wrap"><p id="line-caption">{esc(site.home["line_note"])}</p></div></figcaption></figure>')


def build_home(site):
    h = site.home
    path = "/"
    faqs = [it for g in site.faq["groups"] for it in g["items"] if it.get("home")]
    types = "".join(
        f'<li><h3>{esc(t["name"])}</h3><p>{esc(t["text"])}</p>'
        f'{wa_button(site, "Ask about " + t["name"].lower() + "s", msg_with_ref(t["message"], "WEB-HOME"), "workspace-types", cls="text-link", icon=False)}</li>'
        for t in h["types"])
    steps = "".join(f'<li><h3>{esc(s["title"])}</h3><p>{esc(s["text"])}</p></li>' for s in h["steps"])
    intro = "".join(f"<p>{esc(p)}</p>" for p in h["intro"])
    body = f'''<section class="hero" aria-labelledby="hero-title">
<div class="wrap hero-head">
<h1 id="hero-title">{esc(h["h1"])}</h1>
<div class="hero-side">
<p class="lede">{esc(h["supporting"])}</p>
<div class="btn-row">
<a class="btn btn-primary" href="/offices/">Explore Available Offices</a>
{wa_button(site, "Contact Us on WhatsApp", generic_message("WEB-HOME"), "hero")}
</div>
</div>
</div>
{strip_map(site)}
</section>

<section class="band" aria-labelledby="intro-title"><div class="wrap split">
<div><h2 id="intro-title">{esc(h["intro_heading"])}</h2>
<figure class="figure" style="margin-top:28px">{picture("furnished-office-dubai", image_alt(site, "furnished-office-dubai"), "(min-width: 860px) 48vw, 100vw", ratio=(16, 10))}
<figcaption>{esc(caption(image_caption("furnished-office-dubai"), "furnished-office-dubai"))}</figcaption></figure></div>
<div class="measure">{intro}<p><strong>{esc(h["intro_close"])}</strong></p>
<div class="btn-row"><a class="btn btn-ghost" href="/contact/">Book Your Office Viewing</a></div></div>
</div></section>

<section class="band navy on-navy" aria-labelledby="dir-title"><div class="wrap">
<div class="band-head"><h2 id="dir-title">{esc(h["directory_heading"])}</h2><p>{esc(h["directory_intro"])}</p></div>
{directory(site, directory_rows(site))}
<div class="btn-row"><a class="btn btn-ghost" href="/offices/">Explore Available Offices</a></div>
</div></section>

<section class="band" aria-labelledby="types-title"><div class="wrap">
<div class="band-head"><h2 id="types-title">{esc(h["types_heading"])}</h2>
<p>Not sure which you need? Our guide to <a href="/blog/private-office-vs-shared-workspace-dubai/">private offices and shared workspaces</a> explains the difference.</p></div>
<ul class="types">{types}</ul>
</div></section>

<section class="band rule-top-band" aria-labelledby="steps-title"><div class="wrap split">
<div><h2 id="steps-title">{esc(h["steps_heading"])}</h2><ol class="steps">{steps}</ol>
<div class="callout"><p><strong>Prefer to talk?</strong> Call or WhatsApp us on <a href="tel:{esc(site.cfg["phone_e164"])}" data-place="home-steps" class="nowrap">{esc(site.cfg["phone_display"])}</a>. Tell us the area and your team size, and we will suggest offices and viewing times.</p></div></div>
<div>{enquiry_form(site, "home-form", "Homepage", level=3)}</div>
</div></section>

<section class="band" aria-labelledby="faq-title"><div class="wrap split">
<div><h2 id="faq-title">{esc(h["faq_heading"])}</h2><p><a class="text-link" href="/faq/">See all questions and answers</a></p></div>
<div>{faq_html(faqs)}</div>
</div></section>

<section class="band" aria-labelledby="guides-title"><div class="wrap">
<div class="band-head"><h2 id="guides-title">{esc(h["guides_heading"])}</h2><p><a class="text-link" href="/blog/">All guides</a></p></div>
{post_cards(site, site.posts[:3])}
</div></section>

{cta_band(site, h["final_heading"], h["final_text"], generic_message("WEB-HOME-CTA"), "home-final")}'''
    page = {"path": path, "title": h["seo_title"], "description": h["meta_description"], "page_type": "home",
            "body": body, "crumbs": [("Home", "/")], "og_title": "Office for Rent in Dubai: Property Rent Hub"}
    page["og_image_abs"] = site.abs(og_for("home"))
    register_og("home", h["h1"], "Al Barsha, Port Saeed, Sheikh Zayed Road, JLT and Business Bay", "office-hero")
    page["og_image_alt"] = "Property Rent Hub: offices for rent across Dubai, from Port Saeed to JLT"
    page["schema"] = [org_node(site), website_node(site), local_business_node(site),
                      webpage_node(site, page, "WebPage", {"about": {"@id": site.abs("/#organization")}})]
    page["modified"] = TODAY
    return page


def build_location(site, loc):
    path = loc["path"]
    name = loc.get("long_name", loc["name"])
    m = loc_messages(loc)
    facts = "".join(f'<div><dt>{esc(k)}</dt><dd>{esc(v)}</dd></div>' for k, v in loc["facts"])
    note = f'<p class="contact-line">{esc(loc["rental_note"])}</p>' if loc.get("rental_note") else ""
    related = [site.post_by_slug[s] for s in loc.get("related_posts", []) if s in site.post_by_slug]
    cur_attr = ' aria-current="page"'
    others = "".join(f'<li><a href="{l["path"]}"{cur_attr if l["key"] == loc["key"] else ""}>{esc(l.get("long_name", l["name"]))}</a></li>'
                     for l in site.locations)
    rows = directory_rows(site, only_location=loc["key"])
    has_listing = any(p["location"] == loc["key"] and p.get("status") == "available" for p in site.properties)
    dir_intro = ("Offices we currently advertise here. Message us for today's availability, photos and full rental details."
                 if has_listing else "We share current options in this area on request. Tell us your team size, budget and move-in date.")
    body = f'''{crumbs_html([("Home", "/"), (f"Offices in {loc['name']}", path)])}
<section class="page-head"><div class="wrap">
<h1>{esc(loc["h1"])}</h1>
<p class="lede">{esc(loc["lede"])}</p>
{note}
<div class="btn-row">
{wa_button(site, "Check Office Availability", m["availability"], "location-hero", area=loc["key"])}
{wa_button(site, "Book Your Office Viewing", m["viewing"], "location-hero-viewing", area=loc["key"], cls="btn btn-ghost", icon=False)}
</div>
</div></section>

<div class="wrap loc-grid">
<div>
<figure class="figure">{picture(loc["image"], loc["image_alt"], "(min-width: 1240px) 780px, (min-width: 900px) 62vw, 100vw", eager=True)}
<figcaption>{esc(caption(image_caption(loc["image"]), loc["image"]))}</figcaption></figure>
<div class="prose" style="margin-top:28px">{loc["body"]}</div>
</div>
<aside class="aside-sticky" aria-labelledby="facts-title">
<h2 class="facts-title" id="facts-title">{esc(loc["name"])} at a glance</h2>
<dl class="facts">{facts}</dl>
<div class="btn-row">{wa_button(site, "Get Rental Details", m["availability"], "location-aside", area=loc["key"])}</div>
</aside>
</div>

<section class="band navy on-navy" aria-labelledby="loc-dir-title" style="margin-top:clamp(48px,7vw,96px)"><div class="wrap">
<div class="band-head"><h2 id="loc-dir-title">Offices for rent in {esc(loc["name"])}</h2><p>{esc(dir_intro)}</p></div>
{directory(site, rows)}
</div></section>

<section class="band" aria-labelledby="loc-faq-title"><div class="wrap split">
<div><h2 id="loc-faq-title">Questions about offices in {esc(loc["name"])}</h2>
<p class="muted">More answers on our <a href="/faq/">FAQ page</a>.</p></div>
<div>{faq_html(loc["faqs"])}</div>
</div></section>

<section class="band" aria-labelledby="loc-more-title"><div class="wrap">
<div class="band-head"><h2 id="loc-more-title">Guides for renting in {esc(loc["name"])}</h2></div>
{post_cards(site, related)}
<h3 style="margin-top:40px">Other office areas on the line</h3>
<ul class="area-links">{others}</ul>
</div></section>

{enquiry_band(site, f"Request office details in {loc['name']}", "Tell us your team size, budget and move-in date. We will reply on WhatsApp with offices that fit and arrange a viewing.", "location-form", f"{loc['name']} page", m["viewing"], area=loc["key"])}'''
    page = {"path": path, "title": loc["seo_title"], "description": loc["meta_description"], "page_type": "location",
            "body": body, "crumbs": [("Home", "/"), (f"Offices in {loc['name']}", path)], "area": loc["key"],
            "mobile_message": m["availability"], "modified": loc.get("date_modified", TODAY)}
    page["og_image_abs"] = site.abs(og_for(f"location-{loc['key']}"))
    page["og_image_alt"] = loc["image_alt"]
    register_og(f"location-{loc['key']}", loc["h1"], loc["descriptor"], loc["image"])
    place = {"@type": "Place", "name": f"{name}, Dubai", "address": {"@type": "PostalAddress", "addressLocality": "Dubai", "addressCountry": "AE"}}
    props = [p for p in site.properties if p["location"] == loc["key"] and p.get("status") == "available"]
    nodes = [org_node(site), website_node(site),
             webpage_node(site, page, "WebPage", {"about": place, "primaryImageOfPage": {"@type": "ImageObject", "url": site.abs(f"/assets/img/{loc['image']}.webp")}}),
             breadcrumb_node(site, page)]
    if props:
        nodes.append({"@type": "ItemList", "@id": site.abs(path) + "#offices", "name": f"Offices for rent in {name}",
                      "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": site.abs(p["path"]), "name": p["title"]} for i, p in enumerate(props)]})
    page["schema"] = nodes
    return page


def build_property(site, p):
    loc = site.loc_by_key[p["location"]]
    m = prop_messages(p, loc)
    path = p["path"]
    rows = [("Reference", esc(p["ref"])),
            ("Area", f'<a href="{loc["path"]}">{esc(loc.get("long_name", loc["name"]))}</a>'),
            ("Office type", esc(p["type"])),
            ("Rental details", "On request via WhatsApp"),
            ("Ejari", esc(ejari_value(p.get("ejari"))))]
    if p.get("size_sqft"):
        rows.append(("Size", f'{p["size_sqft"]:,} sq ft'))
    else:
        rows.append(("Size", "Ask us for the current size and layout"))
    if p.get("capacity"):
        rows.append(("Suits", esc(p["capacity"])))
    if p.get("building"):
        rows.append(("Building", esc(p["building"]) + (f', {esc(p["floor"])}' if p.get("floor") else "")))
    if p.get("available_from"):
        rows.append(("Available from", esc(p["available_from"])))
    if p.get("amenities"):
        rows.append(("Includes", esc(", ".join(p["amenities"]))))
    if p.get("trakheesi_permit"):
        rows.append(("Advertising permit", esc(p["trakheesi_permit"])))
    if p.get("availability_checked"):
        rows.append(("Details last checked", esc(fmt_date(p["availability_checked"]))))
    facts = "".join(f"<div><dt>{k}</dt><dd>{v}</dd></div>" for k, v in rows)
    if p.get("photos"):
        figs = "".join(
            f'<figure><img src="/assets/img/properties/{esc(ph["file"])}" alt="{esc(ph["alt"])}" width="{ph.get("width", 1200)}" height="{ph.get("height", 800)}" loading="{"eager" if i == 0 else "lazy"}" decoding="async"></figure>'
            for i, ph in enumerate(p["photos"]))
        gallery = f'<div class="gallery">{figs}</div>'
    else:
        gallery = (f'<div class="gallery-empty"><h2 style="font-size:1.2rem;margin:0">Photos of this office</h2>'
                   f'<p>We send current photos and a short video of this office on WhatsApp, so you see exactly what is available today.</p>'
                   f'{wa_button(site, "Get Rental Details", m["details"], "property-photos", area=loc["key"], ref=p["ref"])}</div>')
    status = '<span class="status">Available</span>' if p.get("status") == "available" else '<span class="status let">Recently let</span>'
    body = f'''{crumbs_html([("Home", "/"), ("Offices", "/offices/"), (p["title"], path)])}
<section class="page-head"><div class="wrap">
<p style="margin:0 0 10px">{status} <span class="ref">Ref {esc(p["ref"])}</span></p>
<h1>{esc(p["title"])}</h1>
<p class="lede">{esc(p["summary"])}</p>
<div class="btn-row">
{wa_button(site, "Get Rental Details", m["details"], "property-hero", area=loc["key"], ref=p["ref"])}
{wa_button(site, "Book Your Office Viewing", m["viewing"], "property-hero-viewing", area=loc["key"], ref=p["ref"], cls="btn btn-ghost", icon=False)}
</div>
</div></section>
<div class="wrap loc-grid">
<div>
{gallery}
<div class="prose" style="margin-top:32px">
<h2>About the location</h2>
<p>{esc(loc["lede"])} Read more about <a href="{loc["path"]}">offices for rent in {esc(loc["name"])}</a>, including transport, licensing and what to check before you sign.</p>
<figure class="figure" style="margin:22px 0">{picture(loc["image"], loc["image_alt"], "(min-width: 1240px) 780px, (min-width: 900px) 62vw, 100vw")}
<figcaption>{"Example photo" if is_photo(loc["image"]) else "Illustration"} of a typical office, not of this office</figcaption></figure>
<h2>Questions to ask before your viewing</h2>
<ul class="checklist">
<li>What does the rent cover: furniture, internet, electricity and water, cleaning, meeting rooms?</li>
<li>Can the lease be registered through Ejari for my company and activity?</li>
<li>How many payments can the rent be split into?</li>
<li>Is parking included, and where do visitors park?</li>
<li>When can I move in, and how long is the contract?</li>
</ul>
<p>Our <a href="/blog/office-rental-checklist-new-business-dubai/">office rental checklist</a> covers the full process from viewing to Ejari.</p>
</div>
</div>
<aside class="aside-sticky" aria-labelledby="prop-facts">
<h2 class="facts-title" id="prop-facts">Office details</h2>
<dl class="facts">{facts}</dl>
<div class="btn-row">{wa_button(site, "Check Office Availability", m["details"], "property-aside", area=loc["key"], ref=p["ref"])}</div>
</aside>
</div>
{enquiry_band(site, "Ask about this office", "Send your details and we will confirm availability, rental details and Ejari information, then arrange a viewing.", "property-form", f"Office page {p['ref']}", m["viewing"], area=loc["key"], prop=p)}'''
    page = {"path": path, "title": f'{p["title"]} | Property Rent Hub', "description": p["meta_description"],
            "page_type": "property", "body": body, "area": loc["key"], "mobile_message": m["details"],
            "crumbs": [("Home", "/"), ("Offices", "/offices/"), (p["title"], path)], "modified": p.get("availability_checked") or TODAY}
    if len(page["title"]) > 65:
        page["title"] = p["title"]
    if not p["indexable"]:
        page["robots"] = "noindex, follow"
    page["og_image_abs"] = site.abs(og_for(f"property-{p['slug']}"))
    page["og_image_alt"] = p["title"]
    og_sub = "Availability and rental details on WhatsApp"
    register_og(f"property-{p['slug']}", p["title"], og_sub, loc["image"])
    page["schema"] = [org_node(site), website_node(site), webpage_node(site, page, "WebPage"), breadcrumb_node(site, page)]
    return page


def build_offices(site):
    path = "/offices/"
    available = [p for p in site.properties if p.get("status") == "available"]
    body = f'''{crumbs_html([("Home", "/"), ("Offices", path)])}
<section class="page-head"><div class="wrap">
<h1>Available Offices for Rent in Dubai</h1>
<p class="lede">Furnished private offices, serviced offices and workspaces across five Dubai areas. Availability changes quickly, so the list below shows our current advertised offices and the areas where we share options on request.</p>
<div class="btn-row">{wa_button(site, "Check Office Availability", generic_message("WEB-OFFICES"), "offices-hero")}</div>
</div></section>
<section class="band navy on-navy" aria-labelledby="all-dir"><div class="wrap">
<div class="band-head"><h2 id="all-dir">Offices by area</h2><p>Select an office for its details, or message us for photos and current rental details.</p></div>
{directory(site, directory_rows(site))}
</div></section>
<section class="band" aria-labelledby="off-help"><div class="wrap split">
<div>
<h2 id="off-help">Don't see the right office?</h2>
<p class="measure">Tell us what you need and we will check current availability across Port Saeed, Sheikh Zayed Road, Business Bay, Al Barsha and JLT. Include your team size, budget and move-in date, and whether you need Ejari for your trade licence.</p>
<figure class="figure" style="margin-top:24px">{picture("furnished-office-dubai", image_alt(site, "furnished-office-dubai"), "(min-width: 900px) 50vw, 100vw", ratio=(16, 10))}
<figcaption>{esc(caption(image_caption("furnished-office-dubai"), "furnished-office-dubai"))}</figcaption></figure>
</div>
<div>{enquiry_form(site, "offices-form", "Available offices page", level=3)}</div>
</div></section>
<section class="band" aria-labelledby="off-guides"><div class="wrap">
<div class="band-head"><h2 id="off-guides">Before you choose</h2></div>
{post_cards(site, [site.post_by_slug[s] for s in ("office-rent-cost-dubai", "furnished-vs-unfurnished-offices-dubai", "office-rental-checklist-new-business-dubai")])}
</div></section>'''
    page = {"path": path, "title": "Available Offices for Rent in Dubai | Property Rent Hub",
            "description": "Browse furnished offices for rent in Dubai with availability and Ejari details: Port Saeed, Al Barsha, Sheikh Zayed Road, Business Bay and JLT.",
            "page_type": "offices", "body": body, "crumbs": [("Home", "/"), ("Offices", path)], "modified": TODAY,
            "mobile_message": generic_message("WEB-OFFICES")}
    page["og_image_abs"] = site.abs(og_for("offices"))
    register_og("offices", "Available Offices for Rent in Dubai", "Furnished private offices and workspaces in five areas", "furnished-office-dubai")
    page["schema"] = [org_node(site), website_node(site), webpage_node(site, page, "CollectionPage"), breadcrumb_node(site, page),
                      {"@type": "ItemList", "@id": site.abs(path) + "#list", "name": "Offices for rent",
                       "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": site.abs(p["path"]), "name": p["title"]} for i, p in enumerate(available)]}]
    return page


def build_blog_index(site):
    path = "/blog/"
    groups = {}
    for p in site.posts:
        groups.setdefault(p.get("topic", "Guides"), []).append(p)
    order = ["Costs and contracts", "Areas", "Workspace types"]
    sections = ""
    for g in order + [k for k in groups if k not in order]:
        if g not in groups:
            continue
        items = "".join(
            f'<li><div><h3><a href="{p["path"]}">{esc(p["title"])}</a></h3><p>{esc(p["excerpt"])}</p></div>'
            f'<time datetime="{p["date_modified"]}">Updated {fmt_date(p["date_modified"])}</time></li>' for p in groups[g])
        sections += f'<section class="band" aria-labelledby="g-{slugify(g)}"><div class="wrap"><h2 id="g-{slugify(g)}">{esc(g)}</h2><ul class="post-index">{items}</ul></div></section>'
    body = f'''{crumbs_html([("Home", "/"), ("Guides", path)])}
<section class="page-head"><div class="wrap">
<h1>Office Rental Guides for Dubai</h1>
<p class="lede">Plain-language guides to renting an office in Dubai: Ejari, contracts, workspace types and how the main business areas compare. Guides that refer to rules link to the official sources we used.</p>
</div></section>
{sections}
{cta_band(site, "Looking for an office now?", "Tell us your area, team size and move-in date and we will send matching offices on WhatsApp.", generic_message("WEB-BLOG"), "blog-index")}'''
    page = {"path": path, "title": "Office Rental Guides for Dubai | Property Rent Hub",
            "description": "Practical guides to renting an office in Dubai: costs, Ejari, contracts, furnished and shared workspaces, and how Business Bay, JLT and Al Barsha compare.",
            "page_type": "blog-index", "body": body, "crumbs": [("Home", "/"), ("Guides", path)], "modified": TODAY}
    page["og_image_abs"] = site.abs(og_for("blog"))
    register_og("blog", "Office Rental Guides for Dubai", "Costs, Ejari, contracts and areas, explained", "business-bay-office-rental")
    page["schema"] = [org_node(site), website_node(site), webpage_node(site, page, "CollectionPage"), breadcrumb_node(site, page),
                      {"@type": "ItemList", "@id": site.abs(path) + "#list", "itemListElement": [
                          {"@type": "ListItem", "position": i + 1, "url": site.abs(p["path"]), "name": p["title"]} for i, p in enumerate(site.posts)]}]
    return page


def build_post(site, post):
    path = post["path"]
    body_html = expand_tokens(site, post["body"], post)
    body_html, toc = add_heading_ids(body_html)
    lead_html = ""
    m_lead = re.match(r"\s*(<p>.*?</p>)(.*)$", body_html, re.S)
    if m_lead:
        lead_html, body_html = m_lead.group(1), m_lead.group(2)
    toc_html = ""
    toc_clean = [(hid, re.sub(r"^[0-9]+[.)]\s*", "", t)) for hid, t in toc]
    if len(toc) >= 4:
        toc_html = '<nav class="toc" aria-label="On this page"><p>On this page</p><ol>' + "".join(
            f'<li><a href="#{hid}">{esc(t)}</a></li>' for hid, t in toc_clean) + '</ol></nav>'
    sources = ""
    if post.get("sources"):
        sources = '<section class="sources" aria-labelledby="sources-title"><h2 id="sources-title">Sources</h2><ol>' + "".join(
            f'<li><a href="{esc(s["url"])}" rel="noopener" target="_blank">{esc(s["title"])}</a></li>' for s in post["sources"]) + \
            f'</ol><p>Reviewed by the Property Rent Hub team on {fmt_date(post["date_modified"])}. Rules change; check the official source before you act.</p></section>'
    rel_locs = "".join(f'<li><a href="{site.loc_by_key[k]["path"]}">Offices in {esc(site.loc_by_key[k].get("long_name", site.loc_by_key[k]["name"]))}</a></li>'
                       for k in post.get("related_locations", []) if k in site.loc_by_key)
    rel_posts = "".join(f'<li><a href="{site.post_by_slug[s]["path"]}">{esc(site.post_by_slug[s]["title"])}</a></li>'
                        for s in post.get("related_posts", []) if s in site.post_by_slug)
    first_loc = (post.get("related_locations") or [None])[0]
    aside_btn = wa_button(site, "Contact Us on WhatsApp",
                          msg_with_ref(f"Hello Property Rent Hub, I read your guide \"{post['title']}\" and I'm looking for an office in Dubai.\nArea: \nTeam size: ", "WEB-BLOG"),
                          "article-aside", area=first_loc or "")
    hero_img = ""
    if post.get("image"):
        ratio = (16, 10) if post["image"] == "furnished-office-dubai" else (16, 9)
        hero_img = (f'<figure class="figure" style="margin:0 0 28px">{picture(post["image"], image_alt(site, post["image"]), "(min-width: 1240px) 700px, (min-width: 980px) 58vw, 100vw", eager=True, ratio=ratio)}'
                    f'<figcaption>{esc(caption(image_caption(post["image"]), post["image"]))}</figcaption></figure>')
    body = f'''{crumbs_html([("Home", "/"), ("Guides", "/blog/"), (post["title"], path)])}
<article class="article">
<header class="wrap article-head">
<h1>{esc(post["title"])}</h1>
<p class="article-meta"><span>By the Property Rent Hub team</span><span>Updated <time datetime="{post["date_modified"]}">{fmt_date(post["date_modified"])}</time></span><span>{post["minutes"]} min read</span></p>
</header>
<div class="wrap article-grid">
<div>
<div class="prose lead-wrap">{lead_html}</div>
{hero_img}
{toc_html}
<div class="prose">{body_html}</div>
{sources}
</div>
<aside>
<div class="aside-sticky">
<div class="aside-block"><h2>Office areas</h2><ul>{rel_locs}</ul></div>
<div class="aside-block"><h2>Related guides</h2><ul>{rel_posts}</ul></div>
<div class="aside-block"><h2>Need an office?</h2><p class="small muted">Send your area, team size and move-in date.</p>{aside_btn}</div>
</div>
</aside>
</div>
</article>'''
    title = post.get("seo_title") or post["title"]
    if len(title) + len(" | Property Rent Hub") <= 62:
        title = title + " | Property Rent Hub"
    page = {"path": path, "title": title, "description": post["meta_description"], "page_type": "article",
            "body": body, "og_type": "article", "published": post["date_published"], "modified": post["date_modified"],
            "crumbs": [("Home", "/"), ("Guides", "/blog/"), (post["title"], path)], "og_title": post["title"],
            "area": first_loc or "",
            "mobile_message": msg_with_ref(f"Hello Property Rent Hub, I read your guide \"{post['title']}\" and I'm looking for an office in Dubai.", "WEB-BLOG")}
    page["og_image_abs"] = site.abs(og_for(f"post-{post['slug']}"))
    page["og_image_alt"] = post["title"]
    register_og(f"post-{post['slug']}", post["title"], "Property Rent Hub guide", post.get("image") or "furnished-office-dubai")
    img = site.abs(f"/assets/img/{post['image']}.webp") if post.get("image") else page["og_image_abs"]
    article = {"@type": "BlogPosting", "@id": site.abs(path) + "#article", "headline": post["title"],
               "description": post["meta_description"], "datePublished": post["date_published"], "dateModified": post["date_modified"],
               "author": {"@type": "Organization", "name": "Property Rent Hub", "url": site.abs("/about/")},
               "publisher": {"@id": site.abs("/#organization")}, "mainEntityOfPage": {"@id": site.abs(path) + "#webpage"},
               "image": [page["og_image_abs"], img], "wordCount": post["words"], "inLanguage": site.cfg["language"],
               "articleSection": post.get("topic", "Guides")}
    if post.get("sources"):
        article["citation"] = [s["url"] for s in post["sources"]]
    page["schema"] = [org_node(site), website_node(site), webpage_node(site, page, "WebPage"), breadcrumb_node(site, page), article]
    return page


def build_about(site):
    meta, body_html = site.about
    path = "/about/"
    locs = "".join(f'<li><a href="{l["path"]}">{esc(l.get("long_name", l["name"]))}</a></li>' for l in site.locations)
    body = f'''{crumbs_html([("Home", "/"), ("About", path)])}
<section class="page-head"><div class="wrap">
<h1>{esc(meta["h1"])}</h1>
<p class="lede">{esc(meta["lede"])}</p>
</div></section>
<div class="wrap loc-grid">
<div class="prose">{body_html}</div>
<aside class="aside-sticky" aria-labelledby="about-contact">
<h2 class="facts-title" id="about-contact">Contact</h2>
<dl class="facts">
<div><dt>WhatsApp and phone</dt><dd><a href="tel:{esc(site.cfg["phone_e164"])}" data-place="about" class="nowrap">{esc(site.cfg["phone_display"])}</a></dd></div>
<div><dt>Areas</dt><dd><ul class="area-links" style="margin-top:8px">{locs}</ul></dd></div>
</dl>
<div class="btn-row">{wa_button(site, "Contact Us on WhatsApp", generic_message("WEB-ABOUT"), "about")}</div>
</aside>
</div>
<div style="height:clamp(48px,7vw,96px)"></div>
{cta_band(site, "Tell us what you need", "Area, team size, budget and move-in date are enough to start. We will reply with matching offices.", generic_message("WEB-ABOUT"), "about-final")}'''
    page = {"path": path, "title": meta["seo_title"], "description": meta["meta_description"], "page_type": "about",
            "body": body, "crumbs": [("Home", "/"), ("About", path)], "modified": meta.get("date_modified", TODAY)}
    page["og_image_abs"] = site.abs(og_for("about"))
    register_og("about", meta["h1"], "Office rental assistance in Dubai", "furnished-office-dubai")
    page["schema"] = [org_node(site), website_node(site), local_business_node(site),
                      webpage_node(site, page, "AboutPage", {"about": {"@id": site.abs("/#organization")}}), breadcrumb_node(site, page)]
    return page


def build_faq(site):
    f = site.faq
    path = "/faq/"
    blocks = "".join(f'<section class="faq-group" aria-labelledby="fg-{slugify(g["heading"])}"><h2 id="fg-{slugify(g["heading"])}" style="font-size:1.4rem;margin-top:1.6em">{esc(g["heading"])}</h2>{faq_html(g["items"])}</section>'
                     for g in f["groups"])
    body = f'''{crumbs_html([("Home", "/"), ("FAQ", path)])}
<section class="page-head"><div class="wrap">
<h1>{esc(f["h1"])}</h1>
<p class="lede">{esc(f["lede"])}</p>
</div></section>
<div class="wrap loc-grid">
<div>{blocks}</div>
<aside aria-label="Office enquiry">{enquiry_form(site, "faq-form", "FAQ page", level=2, compact=True)}</aside>
</div>
<div style="height:clamp(48px,7vw,96px)"></div>
{cta_band(site, "Still have a question?", "Message us on WhatsApp and we will answer it for the specific office you have in mind.", generic_message("WEB-FAQ"), "faq-final")}'''
    page = {"path": path, "title": f["seo_title"], "description": f["meta_description"], "page_type": "faq",
            "body": body, "crumbs": [("Home", "/"), ("FAQ", path)], "modified": TODAY}
    page["og_image_abs"] = site.abs(og_for("faq"))
    register_og("faq", f["h1"], "Office rent, Ejari, locations and viewings", "furnished-office-dubai")
    qa = [{"@type": "Question", "name": it["q"], "acceptedAnswer": {"@type": "Answer", "text": strip_tags(it["a"])}}
          for g in f["groups"] for it in g["items"]]
    page["schema"] = [org_node(site), website_node(site), webpage_node(site, page, "FAQPage", {"mainEntity": qa}), breadcrumb_node(site, page)]
    return page


def build_contact(site):
    path = "/contact/"
    cfg = site.cfg
    b = cfg["business"]
    if b.get("address_verified") and b.get("street_address"):
        addr = f'<p><strong>{esc(b.get("legal_name") or cfg["site_name"])}</strong><br>{esc(b["street_address"])}<br>{esc(b["address_locality"])}</p>'
        if b.get("google_maps_url"):
            addr += f'<p><a class="text-link" href="{esc(b["google_maps_url"])}" target="_blank" rel="noopener">Open in Google Maps</a></p>'
        if b.get("google_maps_embed_src"):
            addr += f'<iframe class="map-frame" src="{esc(b["google_maps_embed_src"])}" loading="lazy" referrerpolicy="no-referrer-when-downgrade" title="Map showing the Property Rent Hub office"></iframe>'
        office = f'<h2>Our office</h2>{addr}'
    else:
        office = ('<h2>Viewings</h2><p>Viewings take place at the office you are interested in. When you book, we send the building, '
                  'floor and the best way to get there on WhatsApp.</p>')
    hours = ""
    if b.get("opening_hours"):
        hours = "<h2>Opening hours</h2><ul>" + "".join(f'<li>{esc(", ".join(h["days"]))}: {esc(h["opens"])} to {esc(h["closes"])}</li>' for h in b["opening_hours"]) + "</ul>"
    area_links = "".join(
        "<li>" + wa_button(site, "Book Your Office Viewing in " + l["name"], loc_messages(l)["viewing"], "contact-area",
                           area=l["key"], cls="text-link", icon=False) + "</li>"
        for l in site.locations)
    body = f'''{crumbs_html([("Home", "/"), ("Contact", path)])}
<section class="page-head"><div class="wrap">
<h1>Contact Us and Book an Office Viewing</h1>
<p class="lede">The quickest way to reach us is WhatsApp. Tell us your preferred area, team size and move-in date, and we will reply with available offices and viewing times.</p>
<div class="btn-row">
{wa_button(site, "Contact Us on WhatsApp", generic_message("WEB-CONTACT"), "contact-hero")}
{phone_link(site, "contact-hero")}
</div>
</div></section>
<div class="wrap split" style="padding-bottom:clamp(48px,7vw,96px)">
<div>{enquiry_form(site, "contact-form", "Contact page", level=2, expanded=True)}</div>
<div class="prose">
<h2>WhatsApp and phone</h2>
<p><a href="tel:{esc(cfg["phone_e164"])}" data-place="contact-body" class="nowrap">{esc(cfg["phone_display"])}</a><br>We reply to WhatsApp messages and arrange viewings at each property.</p>
{office}
{hours}
<h2>Book a viewing by area</h2>
<ul>{area_links}</ul>
</div>
</div>'''
    page = {"path": path, "title": "Book an Office Viewing in Dubai | Property Rent Hub",
            "description": "Contact Property Rent Hub on WhatsApp to check office availability, get rental details and book a viewing in Al Barsha, Port Saeed, JLT and more.",
            "page_type": "contact", "body": body, "crumbs": [("Home", "/"), ("Contact", path)], "modified": TODAY,
            "mobile_message": generic_message("WEB-CONTACT")}
    page["og_image_abs"] = site.abs(og_for("contact"))
    register_og("contact", "Book an Office Viewing in Dubai", "WhatsApp " + cfg["phone_display"], "office-hero")
    page["schema"] = [org_node(site), website_node(site), local_business_node(site), webpage_node(site, page, "ContactPage"), breadcrumb_node(site, page)]
    return page


def build_privacy(site):
    meta, body_html = site.privacy
    path = "/privacy-policy/"
    body = f'''{crumbs_html([("Home", "/"), ("Privacy policy", path)])}
<section class="page-head"><div class="wrap"><h1>{esc(meta["h1"])}</h1><p class="lede">{esc(meta["lede"])}</p></div></section>
<div class="wrap" style="padding-bottom:clamp(48px,7vw,96px)"><div class="prose">{body_html}
<h2>Contact</h2><p>{esc(site.cfg["site_name"])}, WhatsApp and phone <a href="tel:{esc(site.cfg["phone_e164"])}" data-place="privacy">{esc(site.cfg["phone_display"])}</a>.</p>
<p class="small muted">Last updated {fmt_date(meta["date_modified"])}.</p></div></div>'''
    page = {"path": path, "title": meta["seo_title"], "description": meta["meta_description"], "page_type": "privacy",
            "body": body, "crumbs": [("Home", "/"), ("Privacy policy", path)], "modified": meta["date_modified"]}
    page["og_image_abs"] = site.abs(og_for("default"))
    page["schema"] = [org_node(site), website_node(site), webpage_node(site, page), breadcrumb_node(site, page)]
    return page


def build_404(site):
    locs = "".join(f'<li><a href="{l["path"]}">{esc(l.get("long_name", l["name"]))}</a></li>' for l in site.locations)
    body = f'''<section class="notfound"><div class="wrap">
<h1>We couldn't find that page</h1>
<p class="lede">The link may be old or the office may have been let. Try one of these instead, or message us and we will help.</p>
<div class="btn-row"><a class="btn btn-primary" href="/offices/">Explore Available Offices</a>
{wa_button(site, "Contact Us on WhatsApp", generic_message("WEB-404"), "404")}</div>
<h2 style="margin-top:48px;font-size:1.3rem">Offices by area</h2>
<ul class="area-links">{locs}</ul>
<h2 style="margin-top:36px;font-size:1.3rem">Popular guides</h2>
{post_cards(site, site.posts[:3])}
</div></section>'''
    page = {"path": "/404.html", "title": "Page not found | Property Rent Hub",
            "description": "This page could not be found. Explore available offices for rent in Dubai or contact Property Rent Hub on WhatsApp.",
            "page_type": "404", "body": body, "robots": "noindex, follow", "canonical": False, "crumbs": []}
    page["og_image_abs"] = site.abs(og_for("default"))
    return page


# ============================================================== extra files

def sitemap_xml(site, pages):
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">']
    for p in pages:
        if p.get("robots", "").startswith("noindex") or p["path"] == "/404.html":
            continue
        out.append("<url>")
        out.append(f"<loc>{esc(site.abs(p['path']))}</loc>")
        if p.get("modified"):
            out.append(f"<lastmod>{p['modified']}</lastmod>")
        for img in p.get("sitemap_images", []):
            out.append(f"<image:image><image:loc>{esc(site.abs(img))}</image:loc></image:image>")
        out.append("</url>")
    out.append("</urlset>")
    return "\n".join(out) + "\n"


def robots_txt(site):
    return f"User-agent: *\nAllow: /\n\nSitemap: {site.abs('/sitemap.xml')}\n"


def manifest(site, base=""):
    return json.dumps({
        "name": site.cfg["site_name"], "short_name": "Rent Hub", "start_url": base + "/", "scope": base + "/", "display": "browser",
        "background_color": "#FFFFFF", "theme_color": "#0E2240",
        "icons": [{"src": base + "/assets/icons/icon-192.png", "sizes": "192x192", "type": "image/png"},
                  {"src": base + "/assets/icons/icon-512.png", "sizes": "512x512", "type": "image/png"}]}, indent=2)


HEADERS = """# Netlify and Cloudflare Pages read this file. Other hosts ignore it.
/*
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: camera=(), microphone=(), geolocation=()
  X-Frame-Options: SAMEORIGIN
/assets/fonts/*
  Cache-Control: public, max-age=31536000, immutable
/assets/css/*
  Cache-Control: public, max-age=31536000, immutable
/assets/js/*
  Cache-Control: public, max-age=31536000, immutable
/assets/img/*
  Cache-Control: public, max-age=2592000
/assets/og/*
  Cache-Control: public, max-age=2592000
/assets/icons/*
  Cache-Control: public, max-age=2592000
"""

HTACCESS = r"""# Apache / cPanel hosting. Netlify, Cloudflare Pages and Vercel ignore this file.
ErrorDocument 404 /404.html
DirectoryIndex index.html
Options -Indexes

AddType image/avif .avif
AddType image/webp .webp
AddType application/manifest+json .webmanifest
AddType font/woff2 .woff2

<IfModule mod_rewrite.c>
  RewriteEngine On
  # Send all visitors to HTTPS
  RewriteCond %{HTTPS} off
  RewriteCond %{HTTP:X-Forwarded-Proto} !https
  RewriteRule ^ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]
  # Pick ONE host to match site_url in site.json. Uncomment the pair you need.
  # www -> non-www:
  # RewriteCond %{HTTP_HOST} ^www\.(.+)$ [NC]
  # RewriteRule ^ https://%1%{REQUEST_URI} [L,R=301]
  # non-www -> www:
  # RewriteCond %{HTTP_HOST} !^www\. [NC]
  # RewriteRule ^ https://www.%{HTTP_HOST}%{REQUEST_URI} [L,R=301]
  # Add a trailing slash to folder URLs
  RewriteCond %{REQUEST_FILENAME} -d
  RewriteRule ^(.*[^/])$ /$1/ [L,R=301]
</IfModule>

<IfModule mod_headers.c>
  Header always set X-Content-Type-Options "nosniff"
  Header always set Referrer-Policy "strict-origin-when-cross-origin"
  Header always set X-Frame-Options "SAMEORIGIN"
  <FilesMatch "\.(woff2|css|js)$">
    Header set Cache-Control "public, max-age=31536000, immutable"
  </FilesMatch>
  <FilesMatch "\.(avif|webp|jpg|png|svg|ico)$">
    Header set Cache-Control "public, max-age=2592000"
  </FilesMatch>
</IfModule>

<IfModule mod_deflate.c>
  AddOutputFilterByType DEFLATE text/html text/css application/javascript application/json application/xml text/xml image/svg+xml application/manifest+json
</IfModule>
"""


# ============================================================== output

def rewrite_relative(html_text, page_path):
    """For the preview build: turn root-relative URLs into relative file paths."""
    if page_path.endswith(".html"):
        cur_dir = os.path.dirname(page_path)
    else:
        cur_dir = page_path.rstrip("/") or "/"
    if cur_dir == "":
        cur_dir = "/"

    def rel(url):
        if not url.startswith("/") or url.startswith("//"):
            return url
        path, sep, frag = url.partition("#")
        path, qsep, query = path.partition("?")
        if path.endswith("/"):
            path += "index.html"
        r = os.path.relpath(path, cur_dir)
        return r + (qsep + query if qsep else "") + (sep + frag if sep else "")

    def attr(m):
        return f'{m.group(1)}="{rel(m.group(2))}"'
    html_text = re.sub(r'\b(href|src)="(/[^"]*)"', attr, html_text)

    def srcset(m):
        parts = []
        for item in m.group(2).split(","):
            item = item.strip()
            u, _, d = item.partition(" ")
            parts.append((rel(u) + (" " + d if d else "")))
        return f'{m.group(1)}="{", ".join(parts)}"'
    html_text = re.sub(r'\b(srcset)="([^"]*)"', srcset, html_text)
    # CSS url() inside the stylesheet link is handled separately; inline styles have none.
    return html_text


def prefix_base(html_text, base):
    """For a site that lives in a sub-folder (a GitHub project site such as
    username.github.io/property-rent-hub/): put the folder in front of every
    root-relative link, image and script, so "/offices/" becomes
    "/property-rent-hub/offices/". Absolute URLs are already complete."""
    if not base:
        return html_text

    def fix(url):
        return base + url if url.startswith("/") and not url.startswith("//") else url

    html_text = re.sub(r'\b(href|src|action|poster)="(/[^"]*)"', lambda m: f'{m.group(1)}="{fix(m.group(2))}"', html_text)

    def srcset(m):
        items = []
        for item in m.group(2).split(","):
            u, _, d = item.strip().partition(" ")
            items.append(fix(u) + (" " + d if d else ""))
        return f'{m.group(1)}="{", ".join(items)}"'
    return re.sub(r'\b(srcset|imagesrcset)="([^"]*)"', srcset, html_text)


def write_file(out_dir, rel_path, text):
    full = os.path.join(out_dir, rel_path.lstrip("/"))
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as fh:
        fh.write(text)


def minify_css(css):
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    css = re.sub(r"\s+", " ", css)
    css = re.sub(r"\s*([{}:;,>])\s*", r"\1", css)
    css = css.replace(";}", "}")
    return css.strip()


def copy_assets(out_dir, preview, base=""):
    dst = os.path.join(out_dir, "assets")
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(ASSETS, dst, ignore=shutil.ignore_patterns("favicon.ico", "*.txt.bak"))
    css_path = os.path.join(dst, "css", "site.css")
    with open(css_path, encoding="utf-8") as fh:
        css = fh.read()
    css = minify_css(css)
    if preview:
        css = css.replace('url("/assets/fonts/', 'url("../fonts/')
    elif base:
        css = css.replace('url("/assets/', f'url("{base}/assets/')
    with open(css_path, "w", encoding="utf-8") as fh:
        fh.write(css)
    shutil.copy(os.path.join(ASSETS, "favicon.ico"), os.path.join(out_dir, "favicon.ico"))


def build(preview=False):
    site = Site()
    out_dir = os.path.join(ROOT, "preview" if preview else "dist")
    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)
    os.makedirs(out_dir)
    OG_MANIFEST.clear()

    pages = [build_home(site)]
    for loc in site.locations:
        pg = build_location(site, loc)
        pg["sitemap_images"] = [f"/assets/img/{loc['image']}.webp"]
        pages.append(pg)
    pages.append(build_offices(site))
    for p in site.properties:
        pages.append(build_property(site, p))
    pages.append(build_blog_index(site))
    for post in site.posts:
        pg = build_post(site, post)
        if post.get("image"):
            pg["sitemap_images"] = [f"/assets/img/{post['image']}.webp"]
        pages.append(pg)
    pages.append(build_about(site))
    pages.append(build_faq(site))
    pages.append(build_contact(site))
    pages.append(build_privacy(site))
    nf = build_404(site)

    for p in pages + [nf]:
        text = layout(site, p)
        if preview:
            # A preview copy must never be indexed alongside the real site.
            text = re.sub(r'<meta name="robots" content="[^"]*">', '<meta name="robots" content="noindex, nofollow">', text)
            text = rewrite_relative(text, p["path"])
        else:
            text = prefix_base(text, site.base)
        rel = p["path"] if p["path"].endswith(".html") else p["path"] + "index.html"
        write_file(out_dir, rel, text)

    base = "" if preview else site.base
    copy_assets(out_dir, preview, base)
    write_file(out_dir, "/sitemap.xml", sitemap_xml(site, pages))
    write_file(out_dir, "/robots.txt", robots_txt(site))
    write_file(out_dir, "/site.webmanifest", manifest(site, base))
    if site.hosting == "github-pages":
        # Serve every file as it is (no Jekyll processing).
        write_file(out_dir, "/.nojekyll", "")
        # With your own domain, GitHub Pages needs a CNAME file holding it.
        if site.host and not site.host.endswith(".github.io") and site.url != PLACEHOLDER_DOMAIN:
            write_file(out_dir, "/CNAME", site.host + "\n")
    else:
        write_file(out_dir, "/_headers", HEADERS)
        write_file(out_dir, "/.htaccess", HTACCESS)
    with open(os.path.join(ROOT, "tools", "og-manifest.json"), "w", encoding="utf-8") as fh:
        json.dump(OG_MANIFEST, fh, indent=1)
    if not site.cfg["analytics"].get("ga4_measurement_id") and not site.cfg["analytics"].get("gtm_container_id"):
        warn("No GA4 or GTM ID in site.json yet; WhatsApp click events will be ready but not sent anywhere.")
    if not site.cfg["verification"].get("google_site_verification"):
        warn("No Google Search Console verification code in site.json (or verify by DNS instead).")
    return out_dir, pages


def main(argv):
    targets = []
    if "--all" in argv:
        targets = [False, True]
    elif "--preview" in argv:
        targets = [True]
    else:
        targets = [False]
    for preview in targets:
        WARNINGS.clear()
        out_dir, pages = build(preview=preview)
        print(f"Built {len(pages) + 1} pages into {os.path.relpath(out_dir, ROOT)}/")
    if WARNINGS:
        print("\nBefore going live:")
        for w in dict.fromkeys(WARNINGS):
            print("  -", w)


if __name__ == "__main__":
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    main(sys.argv[1:])
