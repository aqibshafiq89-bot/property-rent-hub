# Property Rent Hub website

A fast, static, SEO-ready website for Property Rent Hub: 25 pages, built from simple content files by a small Python script. No WordPress, no database, nothing to patch.

- **`dist/`** is the finished website. It is published with GitHub Pages at **https://aqibshafiq89-bot.github.io/property-rent-hub/** from the `main` branch of `github.com/aqibshafiq89-bot/property-rent-hub`.
- Everything else is the source you edit before rebuilding `dist/`.
- The site shows **no office prices** anywhere. Rental details are shared on WhatsApp. `tools/check_site.py` flags any office price that slips back into a page.

## What's in the site

| Page | URL |
|---|---|
| Homepage | `/` |
| Location pages (5) | `/office-for-rent-al-barsha/`, `/office-for-rent-port-saeed/`, `/office-for-rent-sheikh-zayed-road/`, `/office-for-rent-jlt/`, `/office-for-rent-business-bay/` |
| Available offices + one page per office | `/offices/`, `/offices/furnished-office-port-saeed/`, `/offices/furnished-office-al-barsha/` |
| Guides (blog index + 10 articles) | `/blog/` and `/blog/<article>/` |
| About, FAQ, Contact, Privacy | `/about/`, `/faq/`, `/contact/`, `/privacy-policy/` |
| Custom 404 | `/404.html` |
| Technical files | `sitemap.xml`, `robots.txt`, `site.webmanifest`, `.nojekyll` (GitHub Pages); `_headers` (Netlify/Cloudflare) and `.htaccess` (Apache/cPanel) when `hosting` in `site.json` is not `github-pages` |

Every page has a unique title and meta description, one H1, a canonical tag, Open Graph and Twitter tags, breadcrumbs, and Schema.org data (Organization, WebSite, BreadcrumbList, plus BlogPosting, FAQPage, ItemList, AboutPage or ContactPage where they apply). Content is plain HTML, so nothing depends on JavaScript to be crawled.

## Before you go live

1. **Site address.** `site_url` in `site.json` is `https://aqibshafiq89-bot.github.io/property-rent-hub`. Canonicals, the sitemap and share links all use it, and every link on the site starts with the `/property-rent-hub/` folder. If you connect your own domain later (recommended), change `site_url` to it (for example `https://www.propertyrenthub.ae`), rebuild and publish: the links lose the folder and the build adds the `CNAME` file GitHub Pages needs for a custom domain. Then add the domain under the repository's Settings → Pages and tick Enforce HTTPS.
2. **Add real office details and photos** in `content/properties.json` (see below). Each office page stays `noindex` and out of the sitemap until it has a size and at least 3 genuine photos, so Google never sees a thin listing.
3. **Check advertising permits.** The Dubai Land Department requires brokerages to get an advertising permit (Trakheesi) for property adverts and to show the permit number; many adverts also carry a Madmoun QR code. Confirm with DLD/RERA whether this applies to your offices. If it does, put the number in each office's `trakheesi_permit` field and it appears on the page.
4. **Analytics.** Put your GA4 measurement ID (`G-…`) or Google Tag Manager ID (`GTM-…`) in `site.json` → `analytics`.
5. **Search Console.** See "Search Console after launch" below. On the github.io address, verify with the HTML-tag code in `site.json` → `verification.google_site_verification`. With your own domain you can verify by DNS instead.
6. **Google Business Profile.** Only after Google verifies your address, fill in `site.json` → `business` (street address, map link, embed link, coordinates, opening hours) and set `address_verified` to `true`. The site then shows your address and map on the Contact page and footer, and adds LocalBusiness (`RealEstateAgent`) structured data. Until then it publishes no address and no LocalBusiness data. Keep the name and phone exactly as on the profile.
7. **Read the privacy policy** (`content/pages/privacy.html`) and adjust it to how you actually handle enquiries.
8. Rebuild and upload (below).

## Build commands

You need Python 3.10 or newer. Nothing else is required to rebuild the site.

```bash
python3 build.py            # builds dist/ (upload this)
python3 build.py --all      # also builds preview/, which opens straight from your computer without a server
python3 tools/check_site.py # checks titles, descriptions, H1s, links, images, schema and the sitemap
```

The build prints a short "Before going live" list until the placeholder settings are replaced.

Optional tools (only needed if you change images): Pillow (`pip install pillow`), `rsvg-convert` (librsvg) for the illustrations, and Playwright with Chrome for the share images.

```bash
python3 tools/make_logo.py     # prepares the logo, favicons and app icons from brand/logo-original.png
python3 tools/make_images.py   # makes the WebP/AVIF image sizes of the illustrations
python3 tools/make_og.py       # makes the 1200×630 share images (run build.py first and again after)
```

## Publishing

**GitHub Pages (current).** The repository's `main` branch holds the contents of `dist/`, and Settings → Pages is set to *Deploy from a branch* → `main` → `/ (root)`. To publish a change:

```bash
python3 build.py && python3 tools/check_site.py
# copy everything in dist/ into your clone of the repository (keep its .git folder), then:
git add -A && git commit -m "Update site" && git push
```

GitHub rebuilds the live site within a few minutes. It serves `404.html` for missing pages automatically. GitHub Pages ignores `_headers` and `.htaccess`, so the build leaves them out while `hosting` is `github-pages`.

**Other hosts.** Set `hosting` in `site.json` to `""` and `site_url` to your domain, then rebuild:

- **Netlify or Cloudflare Pages:** drag the `dist` folder into a new site (Netlify "Deploy manually"), or connect a Git repository with build command `python3 build.py` and output folder `dist`. Both serve `404.html` and read `_headers` automatically.
- **cPanel / Apache hosting:** upload the contents of `dist/` (including the hidden `.htaccess`) into `public_html`. In `.htaccess`, uncomment the www or non-www redirect that matches your `site_url`.
- **Nginx:** add `error_page 404 /404.html;` and serve `index.html` for folder URLs.

Make sure the site is on HTTPS.

## Updating office listings

Edit `content/properties.json`, then rebuild. Each office has:

| Field | What to put |
|---|---|
| `ref` | Your reference, e.g. `PRH-PS-02`. It appears in the WhatsApp message so you know which office the person means. |
| `slug` | The URL: `/offices/<slug>/`. Use lowercase words and hyphens. Don't change it once the page is live. |
| `location` | One of `port-saeed`, `al-barsha`, `sheikh-zayed-road`, `jlt`, `business-bay`. |
| `status` | `available`, `let` (shows "Recently let") or `hidden` (removes the page). |
| `ejari` | `included`, `available`, `ask` or `not-available`. |
| `size_sqft`, `capacity`, `building`, `floor`, `available_from`, `amenities` | Genuine details. Leave empty if unknown; empty fields are hidden. |
| `availability_checked` | Date you last confirmed the details, e.g. `2026-12-01`. Shown on the page. |
| `photos` | Genuine photos of this office: `[{"file": "ps-01-desk.webp", "alt": "Furnished private office with two desks and a window", "width": 1600, "height": 1067}]`. Put the files in `assets/img/properties/`. |
| `trakheesi_permit` | Advertising permit number, if one applies. |

When an office is let, set `status` to `let` for a few weeks, then `hidden`. To add an office in a new area, copy an existing entry.

## Pictures

The general pictures are **example photos of typical offices** from Unsplash, which are free to use on a business website (credits in `photos/CREDITS.md`). They show the kind of office on offer, not a specific listing. Every caption says "(example photo)", and the footer says that pictures show typical offices. The photos keep the file names you asked for (`furnished-office-dubai`, `office-for-rent-al-barsha`, `office-for-rent-port-saeed`, `sheikh-zayed-road-office`, `furnished-office-jlt`, `business-bay-office-rental`), plus `office-hero` for the wide homepage picture.

To change a picture:

1. Save the new photo as `photos/<same-name>.jpg` (landscape, at least 1600 px wide). Use your own photos or ones you have a licence for.
2. Run `python3 tools/make_images.py`. It crops, resizes and converts it to WebP and AVIF. For the homepage picture, `IMAGES` in that script sets how far down the wide crop sits.
3. Update its alt text and caption in `content/images.json` (and `image_alt` in `content/locations/*.html` for a location picture).
4. Run `python3 tools/make_og.py` and `python3 build.py`, then publish.

If a photo is removed, the original drawings in `tools/art.py` are used instead and the captions switch to "(illustration)".

Photos of a real office that you are advertising belong on that office's page (the `photos` field in `content/properties.json`), never as a general picture.

## Logo

Your logo artwork is in `brand/logo-original.png`. `python3 tools/make_logo.py` removes its black background and creates:

- `assets/img/logo-lockup.webp` – the horizontal logo in the header (sits on the dark navy header)
- `assets/img/logo-full.webp` – the full logo in the footer
- `assets/img/logo-square-512.png` – the square logo on black, used for Google (Organization data)
- `assets/icons/*` and `favicon.ico` – browser and phone icons (the building emblem on black)
- `brand/logo-*-transparent.png` – transparent master files you can reuse for print or social media

If your designer sends updated artwork, replace `brand/logo-original.png` and run `python3 tools/make_logo.py`, then `python3 tools/make_og.py` and `python3 build.py`. (If the new artwork has a different layout, adjust the crop boxes at the top of `make_logo.py`.)

## Office enquiry form and WhatsApp

The office enquiry form appears on the homepage, the Contact page, every location page, every office page, the Available Offices page and the FAQ page. It asks for:

- **Your details:** full name and mobile/WhatsApp number (required), email, company name
- **Office requirements:** preferred location and number of people (required), office type, move-in, yearly budget (free text, so no amounts appear on the site), Ejari
- **More details (optional):** trade licence status, contract length, business activity, preferred viewing time, message

When the visitor presses **Get Rental Details on WhatsApp**, the form checks the required fields, then opens WhatsApp (app on phones, WhatsApp Web on computers) with a message to +971 56 786 3596 that lists every answer, the page it came from and a reference (`Ref: WEB-FORM`, or the office reference on office pages). The visitor taps **Send** and the enquiry arrives in your WhatsApp chat. The website itself stores nothing.

A website cannot send a WhatsApp message on the visitor's behalf; the visitor always taps Send. If you later want enquiries to arrive without that tap (for example as an automatic WhatsApp or email alert), that needs the WhatsApp Business Platform (API) through a provider, or a form service that emails you, plus a small server-side component.

The visitor's choices change in `build.py` (`ENQUIRY_CHOICES`). In GA4 each sent form records a `generate_lead` event with the location, team size and office type (never the name, phone or email); mark it as a key event.

**Floating WhatsApp button:** a round WhatsApp icon sits in the bottom-right corner of every page and opens a chat with you directly. On location and office pages its message names the area or office. On phones the header also has a call button.

## Adding a guide

Copy any file in `content/blog/`, change the JSON at the top (`slug`, `title`, `seo_title` up to about 60 characters, `meta_description` 120–160 characters, dates, `related_locations`, `sources`) and write the article in HTML below it. `{{cta}}` inserts a WhatsApp box; `{{cta:al-barsha}}` inserts one for a location. Link to location pages and offices with root-relative links such as `/office-for-rent-jlt/`. Only include figures you can source, and list the sources.

## WhatsApp tracking (GA4)

Every WhatsApp button carries `data-wa` (where it is on the page), `data-area` and, on office pages, `data-ref`. `assets/js/site.js` sends:

- `whatsapp_click` with `link_placement`, `office_area`, `property_ref`, `page_type` (the floating button uses placement `floating`)
- `generate_lead` when the enquiry form is sent, with `link_placement`, `office_area`, `team_size`, `office_type`, `property_ref`
- `phone_click` with `link_placement`, `page_type`

Both go to `gtag` (GA4) and to `dataLayer` (Google Tag Manager). In GA4: Admin → Events → mark `generate_lead` and `whatsapp_click` as **key events**, and add the four parameters as event-scoped **custom dimensions** so you can report on them. Each pre-filled WhatsApp message also ends with a source code (e.g. `Ref: WEB-BARSHA`, `WEB-BLOG`, or the office ref), matching the codes in your lead tracker.

## Search Console after launch

1. In Google Search Console, add a property and choose **URL prefix** with `https://aqibshafiq89-bot.github.io/property-rent-hub/` (a Domain property is not possible on a github.io address).
2. Choose the **HTML tag** method. Copy only the code inside `content="…"` into `site.json` → `verification.google_site_verification`, rebuild, publish, then press **Verify**.
3. Sitemaps → enter `sitemap.xml` → Submit. (Google reads `robots.txt` only at the root of a host, so on the github.io address the sitemap must be submitted here.)
4. URL Inspection → Request indexing for the homepage and the five location pages.
5. Check the Pages report after a week or two.

If you move to your own domain, add a new Search Console property for it, verify it and submit its sitemap there too.

Note: Google no longer shows FAQ rich results in search. The FAQ markup is kept because it is valid and harmless, but don't expect FAQ dropdowns in Google results.

## Keeping content accurate

- No office prices are published. Keep it that way when you edit text: say "rental details on request" instead. The only AED figures on the site are the Dubai Land Department's Ejari fees in the guides.
- Metro station names in Dubai change under the RTA naming-rights programme. If a station is renamed, update the location files and the two articles that mention station names.
- Ejari fees in the guides are from the Dubai Land Department's service page (November 2026). Check them every few months.
- The site never publishes reviews, ratings or branch addresses it can't back up.

## Licences

The Archivo font is under the SIL Open Font License (`assets/fonts/OFL-Archivo.txt`). The illustrations were drawn for this site (`tools/art.py`). The logo is your own artwork. The WhatsApp glyph is used only to label links that open WhatsApp.
