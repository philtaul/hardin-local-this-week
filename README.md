# Hardin Local — Events & Community Landing Pages

Static HTML site for Hardin Local community content, published via GitHub Pages.

**Live:** https://philtaul.github.io/hardin-local-this-week/

## Pages

| Page | URL | Purpose |
|---|---|---|
| Events Calendar | `index.html` | Weekly Hardin County events (updated each Monday) |
| Roundabout Guide | `roundabout.html` | Interactive guide to downtown E-town roundabout yield rule changes |
| Election Interviews | `elections.html` | 2026 Primary Election Interview schedule (Fri 4/24, Mon 4/27, Wed 4/29) — links to per-race pages |
| Per-race election pages | `elections/{race}.html` | One page per office: sheriff, pva, magistrate (all 8 districts), mayor-radcliff, radcliff-council, mayor-vine-grove, vine-grove-council, state-federal. Each shows every filed candidate with a 16:9 embed slot. |

## Files

| File | Purpose |
|---|---|
| `index.html` | Events calendar — sponsor block, event listings, footer CTAs |
| `roundabout.html` | Interactive roundabout guide — self-contained HTML/CSS/JS |
| `elections.html` | 2026 Primary Election Interviews — dark theme, JSON-LD ItemList of BroadcastEvents |
| `style.css` | Shared styles for events calendar (HL brand colors, print styles) |
| `elections/` | Per-race election pages (8 HTML files + shared `race-page.css`) — see "Editing per-race election pages" below |
| `newsletter-popup.js` | Exit-intent email collection popup (shared across pages) |
| `dev/api.py` | Local dev API server for testing email collection |
| `dev/worker/` | Cloudflare Worker + D1 schema for production email collection |

## Newsletter Email Collection

An exit-intent popup collects email signups for the upcoming Hardin Local newsletter.

**How it works:**
- Triggers on exit intent (mouse leaves viewport on desktop, scroll-pause on mobile)
- Shows once per visitor (localStorage flag `hl_newsletter_dismissed`)
- Submits to Cloudflare Worker API, stored in D1 (SQLite)

**Production backend:**
- Worker: `https://hl-newsletter.phil-taul.workers.dev`
- Endpoints: `POST /subscribe` (add email), `GET /subscribers` (list all)
- Database: Cloudflare D1 `hl-newsletter-db` (ID: `eab8c438-5eda-47a7-a40a-40be28302f5c`)
- Account: `phil.taul@gmail.com` (ID: `b4d6f31a0e9a8ea040230231fabb0d9b`)

**Check subscribers:**
```bash
curl https://hl-newsletter.phil-taul.workers.dev/subscribers
```

**Local dev:**
```bash
# Start local API (port 8766) + file server (port 8765)
python3 dev/api.py &
python3 -m http.server 8765 --directory . &
# Change HL_API_URL in HTML files to http://localhost:8766 for local testing
```

**Deploying worker changes:**
```bash
cd dev/worker
npx wrangler deploy
```

## Editing per-race election pages

Per-race pages live in `elections/`. They share `elections/race-page.css`. Each candidate has a 16:9 embed slot — currently a `<div class="embed-placeholder">` for candidates without an edited video, and a `<iframe>` for candidates with one.

**Swap a placeholder to a YouTube embed (when an edited video is published):**

In the candidate's `<div class="embed-wrap">` block:
1. Uncomment the `<iframe src="https://www.youtube.com/embed/VIDEO_ID">` line that's already there in the TODO comment, replacing `VIDEO_ID` with the real YouTube ID
2. Delete the entire `<div class="embed-placeholder">…</div>` block

That's it — two-line swap per video.

**Optional: add a "📘 Also on Facebook" pill below the embed.** In the candidate's `<div class="candidate-foot">` add:
```html
<a class="fb-link" href="https://www.facebook.com/share/v/XXXXXXX/" target="_blank" rel="noopener">📘 Also on Facebook →</a>
```

**Add a candidate (e.g., reschedule Vincent Thompson into a new slot):** Copy a sibling card in the same race page, change name + party + ballot position + filed date + interview time. Update the page's candidate count in the hero `.race-meta` pill if it changes.

**Local preview before pushing:**
```bash
cd ~/hardin-local-this-week
python3 -m http.server 8787
# open http://localhost:8787/elections/sheriff.html
```

**Source of truth for candidate data:** the Hardin County Clerk filing list, mirrored in the vault at `hardin-local/Stand Alone Livestreams/Hardin County Elections/Potential Interviews - Full Candidate List - Hardin County Elections 2026.md`. State and federal races aren't in that list — for those, check `elect.ky.gov` and the project's outreach records.

## Brand colors

- **HL Blue:** `#4885ed`
- **HL Green:** `#3cba54`
- **Dark Logo Background:** `#333943`

## Episode sponsor (current)

**Member Medical DPC** — Direct Primary Care in Elizabethtown, KY
- Website: https://membermedicaldpc.com
- Phone: 270.307.1980

## How to publish

Using **Option B — Rolling "this week" site:**
1. Update `index.html` with the new week's events and push to `main`
2. GitHub Pages auto-deploys
3. The Linktree link never changes — just the content behind it

## Customizing for next week

1. Update `index.html`: page title, `hero-eyebrow`, header dates
2. Replace the sponsor block with the new sponsor's info
3. Replace each `<article class="day">` block with the new week's events
4. Update `og:title` and `og:description` meta tags
5. Test mobile view + print preview before publishing

## How to export as PDF

1. Open `index.html` in Chrome/Edge/Safari
2. Print (Cmd/Ctrl+P) → Save as PDF
3. Print styles hide navigation, buttons, and convert backgrounds to white

## Technical notes

- Zero framework — vanilla HTML, CSS, JS
- Zero external dependencies (no CDNs, no build step)
- Mobile-first responsive design
- Accessible semantic HTML
- Open Graph meta tags for social share previews
- Print-friendly with media queries
