# pacificresearchllc.com — production website

A fast, fully static, single-page site for **Pacific Research Group LLC** (SDVOSB federal health-IT
contractor). No build step, no framework, no server code — just HTML, CSS, vanilla JS, and image assets.
Host it anywhere that serves static files.

## Files
```
site/
├── index.html      ← the page (all content + SEO/OG meta + JSON-LD)
├── styles.css      ← all styling (brand tokens inlined, responsive)
├── main.js         ← nav scroll state, mobile drawer, scroll reveal, contact form
├── robots.txt
├── sitemap.xml
└── assets/         ← logo & emblem images (favicon = badge-cross.png)
```

## Deploy

**Option A — your GitHub repo (`pacificresearch/Pacific-Research-LLC-Website`).**
The repo is currently empty. Commit the **contents of this `site/` folder to the repo root** (so
`index.html` sits at the top level), then enable **GitHub Pages** (Settings → Pages → deploy from
`main` / root). Point `pacificresearchllc.com` at Pages with a `CNAME` file containing
`pacificresearchllc.com` and the DNS records GitHub lists.

**Option B — Netlify / Vercel / Cloudflare Pages.** Drag-and-drop the `site/` folder, or connect the
repo with the publish directory set to the folder root. Add `pacificresearchllc.com` as a custom domain.

**Option C — any web host.** Upload everything in `site/` to your web root (`public_html`).

In all cases the site works immediately over HTTPS; fonts load from Google Fonts and icons from the
Lucide CDN.

## Before you go live — edit these
1. **Contact email** — currently `contact@pacificresearchllc.com` (the contact form opens the visitor's
   mail client addressed here, and it appears in the footer/contact section). Change it everywhere if you
   prefer a different inbox: search `contact@pacificresearchllc.com` in `index.html` and `main.js`.
   *Make sure that mailbox actually exists on your domain*, or switch it to your known address.
2. **NAICS codes** — the real registered set is now on the site: primary **541714** (R&D in
   Biotechnology) plus key secondaries (541511, 541512, 541519, 541380, 541611, 541618, 541690, 541990,
   621112, 621999, 611430), shown in the About section. Consider adding **518210** (cloud hosting / data
   processing) for the SaaS-hosted EHR work. Edit the `naics-list` block in `index.html` to adjust.
3. **Phone number** — none was on file, so none is shown. Add a `contact-row` in the Contact section if
   you want one.
4. **Real form delivery (optional but recommended).** The form uses a `mailto:` so it needs no backend.
   For a hosted form (no mail-client popup), wire it to **Formspree**, **Netlify Forms**, or **Basin**:
   set the `<form>` `action`/`method` and remove the `mailto` handler in `main.js`.
5. **Photography (optional).** The hero uses the emblem only. To add real imagery (headshot, clinical/
   federal photography), drop files in `assets/` and reference them — keep the cool, professional cast
   described in the design system.

## Talent pool (CV intake)

The careers page carries a **talent pool** form at `/careers/#talent-pool` that accepts a CV file
upload plus structured fields (discipline, years, clearance, work authorization, availability,
mobility, credentials, veteran status, consent). Entry points: a link in the home-page hero, the
talent-pool band directly under the hero trust bar, the careers hero CTA, the mobile drawer, and
both footers.

**How it delivers.** `main.js` POSTs the form as `multipart/form-data` to **Netlify Forms**
(`name="talent-pool"`, `data-netlify="true"`, honeypot `bot-field`). If that POST fails for any
reason, it falls back to a pre-filled `mailto:` with every field in the body and asks the visitor to
attach the CV there — so no submission is lost if Forms is off or over quota.

**One-time setup in Netlify:** enable **Forms** for the site (Site configuration → Forms), then add a
notification to `contact@pacificresearchllc.com` so submissions land in the inbox. Uploaded files
appear on each submission in the Netlify Forms dashboard. Free-tier limits are 100 submissions/month
and 10 MB per upload; the form caps CVs at 8 MB client-side. To move off Netlify, point the form's
`action` at Formspree/Basin — the JS needs no change.

**Compliance note:** the form states that PRG will not name a candidate or submit a résumé in a
proposal without written permission at bid time, and that submitting a CV is not an offer of
employment. Keep that language if the form is rebuilt.

## SEO / metadata already included
Title + meta description, canonical URL, Open Graph + Twitter cards, `theme-color`, favicon /
apple-touch-icon, `robots.txt`, `sitemap.xml`, and Organization **JSON-LD** structured data.

## Brand
This site is built on the Pacific Research Group design system in the project root (`../README.md`,
`../colors_and_type.css`). Keep the formal, federal-procurement voice and the navy / ocean-blue / sand
palette when extending it.
