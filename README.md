# Hardin Local — Events Landing Page (S2026E16)

Static HTML landing page for **Hardin County events — week of April 15–19, 2026**, tied to Hardin Local Weekly Podcast Episode S2026E16.

## What this is

A zero-dependency, mobile-first, single-page events calendar for audience members. Built to be:

- Pushed to its own GitHub repo
- Published via GitHub Pages
- Linked from the Hardin Local Linktree
- Printable to PDF via browser Print dialog (clean print styles included)

## Files

| File | Purpose |
|---|---|
| `index.html` | The page itself — events, sponsor block, footer CTAs |
| `style.css` | Mobile-first styles, Hardin Local brand colors, print styles |
| `README.md` | This file |

## Brand colors

- **HL Blue:** `#4885ed`
- **HL Green:** `#3cba54`
- **Dark Logo Background:** `#333943`

## Episode sponsor

**Member Medical DPC** — Direct Primary Care in Elizabethtown, KY
- Website: https://membermedicaldpc.com
- Phone: 270.307.1980
- Ribbon Cutting: Wednesday April 15, 2026, 11:30 AM – 2:00 PM at 1230 Woodland Drive, Suite 110

## How to publish

### Option A — Dedicated weekly repo

1. `cd` into this folder
2. `git init && git add . && git commit -m "S2026E16 events landing page"`
3. Create a new GitHub repo (e.g. `hardin-local-events-s2026e16`)
4. `git remote add origin <repo-url>` → `git push -u origin main`
5. In the repo settings, enable **GitHub Pages** from the main branch
6. Copy the Pages URL into the Hardin Local Linktree

### Option B — Rolling "this week" site (recommended going forward)

1. Create a single repo `hardin-local-this-week` once
2. Enable GitHub Pages
3. Each Monday, replace `index.html` with the new week's version and push
4. The Linktree link never changes — just the content behind it
5. SEO compounds: Google indexes a single stable URL rather than a new one each week

## How to export as PDF

1. Open `index.html` in Chrome, Edge, or Safari
2. Print (Cmd/Ctrl+P)
3. Destination: **Save as PDF**
4. Paper size: Letter, Portrait
5. Margins: Default
6. Scale: 100% (or "Fit to page" if needed)
7. Save as `Hardin County Events — Apr 15-19, 2026.pdf`
8. Upload to OneDrive or Linktree

Print styles automatically hide navigation, sponsor buttons, and platform link buttons, and convert all backgrounds to white for clean black-and-white printing.

## Customizing for next week

For the next episode's landing page:
1. Duplicate this folder (or update `index.html` in the rolling repo)
2. Update the page title, `hero-eyebrow`, and header dates
3. Replace the sponsor block with the new sponsor's info
4. Replace each `<article class="day">` block with the new week's events
5. Update `og:title` and `og:description` meta tags
6. Test mobile view + print preview before publishing

## Notes

- Zero JavaScript — static HTML + CSS only
- Zero external dependencies (no CDNs, no fonts, no analytics)
- Mobile-first responsive design
- Accessible semantic HTML
- Print-friendly with media queries
- Open Graph meta tags for Facebook/Twitter share previews
