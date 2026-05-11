#!/usr/bin/env python3
"""
build_area_pages.py — Render per-area landing pages:
  - 4 city pages: elections/area/{radcliff,elizabethtown,vine-grove,west-point}.html
  - 8 magistrate pages: elections/area/magistrate-{1..8}.html

Each lists the precincts in that geography, links to the per-precinct ballot pages,
links to relevant race pages, and shows the magistrate-district PDF map.
Useful as SEO landing pages for searches like "radcliff city council 2026".
"""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / 'data'
OUT_DIR = REPO / 'elections' / 'area'

PARTY_LONG = {'r': 'Republican', 'd': 'Democrat', 'i': 'Independent / Nonpartisan'}


def load():
    return {
        'precincts': json.loads((DATA / 'precincts.json').read_text())['precincts'],
        'merged': json.loads((DATA / 'merged_ballot.json').read_text()),
        'vote_centers': json.loads((DATA / 'vote-centers.json').read_text()),
    }


HEADER = '''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title} | Hardin Local</title>
  <meta name="description" content="{desc}" />
  <meta name="theme-color" content="#0e1219" />
  <meta name="robots" content="index, follow" />
  <link rel="canonical" href="https://philtaul.github.io/hardin-local-this-week/elections/area/{slug}.html" />
  <meta property="og:title" content="{title}" />
  <meta property="og:description" content="{desc}" />
  <meta property="og:type" content="website" />
  <meta property="og:site_name" content="Hardin Local" />
  <link rel="stylesheet" href="../race-page.css" />
  <link rel="stylesheet" href="../your-ballot.css" />
</head>
<body>
  <div class="rainbow-rule"></div>
  <div class="grid-bg" aria-hidden="true"></div>
  <div class="glow" aria-hidden="true"></div>
  <header class="site-header">
    <div class="header-inner">
      <div class="brand">
        <span class="brand-name">Hardin Local</span>
        <span class="brand-tag">Civic Coverage</span>
      </div>
      <button class="nav-toggle" type="button" aria-label="Open menu" aria-expanded="false" aria-controls="site-nav">&#9776;</button>
      <nav class="header-nav collapsible" id="site-nav" aria-label="Primary">
        <a href="../../index.html" class="nav-link">📅 This Week</a>
        <a href="../../elections.html" class="nav-link">🗳️ Election Interviews</a>
        <a href="../find-your-ballot.html" class="nav-link">🔍 Find Your Ballot</a>
        <a href="https://hardinlocal.com" class="nav-link">HardinLocal.com</a>
      </nav>
    </div>
  </header>
  <main>
    <nav class="breadcrumbs" aria-label="Breadcrumb">
      <a href="../../elections.html">Election Interviews</a>
      <span class="sep">›</span>
      <a href="../find-your-ballot.html">Find Your Ballot</a>
      <span class="sep">›</span>
      <span>{breadcrumb}</span>
    </nav>
'''

FOOTER = '''
    <section class="other-races">
      <h3>Other areas</h3>
      <div class="other-races-grid">
        <a href="radcliff.html">Radcliff</a>
        <a href="elizabethtown.html">Elizabethtown</a>
        <a href="vine-grove.html">Vine Grove</a>
        <a href="west-point.html">West Point</a>
        <a href="magistrate-1.html">Magistrate D-1</a>
        <a href="magistrate-2.html">Magistrate D-2</a>
        <a href="magistrate-3.html">Magistrate D-3</a>
        <a href="magistrate-4.html">Magistrate D-4</a>
        <a href="magistrate-5.html">Magistrate D-5</a>
        <a href="magistrate-6.html">Magistrate D-6</a>
        <a href="magistrate-7.html">Magistrate D-7</a>
        <a href="magistrate-8.html">Magistrate D-8</a>
        <a href="../find-your-ballot.html">← Find Your Ballot</a>
      </div>
    </section>
  </main>
  <footer class="site-footer">
    <div class="footer-row">
      <div>Free, non-partisan civic coverage from <span class="pill fb">Facebook</span> <span class="pill yt">YouTube</span></div>
      <div class="handle">HardinLocal.com</div>
    </div>
    <p class="footer-fine">Hardin Local is a community-focused podcast and social media platform covering Hardin County, Kentucky. Election interviews are produced as a free, non-partisan public service. Sample ballot data is sourced from the Hardin County Clerk's official 2026 Primary Composite Sample Ballot.</p>
  </footer>
  <script src="../../site-nav.js" defer></script>
</body>
</html>
'''


def precinct_card(p: dict) -> str:
    """A card linking to all 3 party ballot pages for one precinct."""
    return f'''<div class="vc-card">
            <div class="vc-card-title">{p["name"]} <span style="color:var(--dim,#a4adbf);font-weight:400;">({p["code"]})</span></div>
            <div class="vc-card-addr">Magistrate District {p["magistrate_district"]}{" · KY House " + p["state_house"] if p["state_house"] != "other" else ""}</div>
            <div style="margin-top:0.5rem;display:flex;gap:0.5rem;flex-wrap:wrap;">
              <a class="vc-card-link" href="../your-ballot/{p["code"]}-r.html">Republican ballot →</a>
              <a class="vc-card-link" href="../your-ballot/{p["code"]}-d.html">Democrat ballot →</a>
              <a class="vc-card-link" href="../your-ballot/{p["code"]}-i.html">Independent ballot →</a>
            </div>
            <div style="margin-top:0.4rem;font-size:0.8rem;"><a href="{p["pdf_map_url"]}" target="_blank" rel="noopener" style="color:var(--dim,#a4adbf);">📍 Precinct boundary map (PDF) →</a></div>
          </div>'''


def race_summary_card(race: dict) -> str:
    """A small card summarizing a race + linking to its interview page."""
    interviewed = sum(1 for c in race['candidates'] if (c.get('interview') or {}).get('youtube_id'))
    link = ''
    if race.get('race_file'):
        href = f'../{race["race_file"]}'
        if race.get('race_anchor'):
            href += f'#{race["race_anchor"]}'
        link = f'<a class="vc-card-link" href="{href}">Watch interviews →</a>'
    pill = {'R': 'R primary', 'D': 'D primary', 'NP': 'Nonpartisan'}.get(race['party'], '')
    return f'''<div class="vc-card vc-card-eday">
            <div class="vc-card-title">{race["race_name"]}</div>
            <div class="vc-card-addr">{pill} · {len(race["candidates"])} candidates · {interviewed} with a Hardin Local interview</div>
            <div style="margin-top:0.4rem;">{link}</div>
          </div>'''


def render_city_page(city_name: str, slug: str, precincts: list, data: dict) -> str:
    """City landing page."""
    codes = {p['code'] for p in precincts}
    # Races touching any of these precincts
    races = [r for r in data['merged']['races'] if codes & set(r['scope']['precinct_codes'])]
    # De-dupe by race_slug, keep first
    seen = set()
    uniq_races = []
    for r in races:
        if r['race_slug'] not in seen:
            seen.add(r['race_slug'])
            uniq_races.append(r)

    title = f'{city_name} — 2026 Primary Ballot Lookup'
    desc = f'Every precinct, race, and candidate on the May 19, 2026 primary ballot for {city_name}, Kentucky. Pick your precinct + party for a personalized ballot.'
    breadcrumb = city_name

    precinct_html = '\n          '.join(precinct_card(p) for p in sorted(precincts, key=lambda x: x['code']))
    race_html = '\n          '.join(race_summary_card(r) for r in uniq_races)

    body = f'''
    <section class="find-ballot-hero">
      <p class="race-eyebrow">— 2026 Primary · Hardin County —</p>
      <h1>{city_name} <span class="accent">Ballot</span></h1>
      <p class="race-blurb">
        {city_name} spans {len(precincts)} voting precinct{"s" if len(precincts) != 1 else ""} in Hardin County. Your exact ballot depends on which precinct you live in and your party registration. Find your precinct below — or use the <a href="../find-your-ballot.html">Find Your Ballot</a> tool to get there in two clicks.
      </p>
    </section>

    <section class="vote-centers-section">
      <h2>Precincts in {city_name}</h2>
      <p class="vc-tagline">Click your precinct's ballot below. Not sure which precinct you're in? Open the boundary-map PDF or check the <a href="https://vrsws.sos.ky.gov/VIC/" target="_blank" rel="noopener">KY Voter Information Center</a>.</p>
      <div class="vc-list-grid">
          {precinct_html}
      </div>
    </section>

    <section class="vote-centers-section">
      <h2>Races on {city_name} ballots</h2>
      <p class="vc-tagline">Every race that appears for at least some {city_name} voters. (Which races YOU see depends on precinct + party — get your personalized list from <a href="../find-your-ballot.html">Find Your Ballot</a>.)</p>
      <div class="vc-list-grid">
          {race_html}
      </div>
    </section>
'''
    return (HEADER.format(title=title, desc=desc, slug=slug, breadcrumb=breadcrumb)
            + body + FOOTER)


def render_magistrate_page(md_num: int, precincts: list, data: dict) -> str:
    """Magistrate-district landing page."""
    codes = {p['code'] for p in precincts}
    races = [r for r in data['merged']['races'] if codes & set(r['scope']['precinct_codes'])]
    seen = set()
    uniq_races = []
    for r in races:
        if r['race_slug'] not in seen:
            seen.add(r['race_slug'])
            uniq_races.append(r)

    # The magistrate race itself (if on the ballot)
    mag_race = next((r for r in data['merged']['races'] if r['race_slug'] == f'magistrate-{md_num}'), None)

    title = f'Hardin County Magistrate District {md_num} — 2026 Primary'
    desc = f'Precincts, candidates, and the May 19, 2026 primary ballot for Magistrate District {md_num} in Hardin County, Kentucky.'
    breadcrumb = f'Magistrate District {md_num}'
    slug = f'magistrate-{md_num}'

    precinct_names = ', '.join(p['name'] for p in sorted(precincts, key=lambda x: x['code']))

    precinct_html = '\n          '.join(precinct_card(p) for p in sorted(precincts, key=lambda x: x['code']))
    race_html = '\n          '.join(race_summary_card(r) for r in uniq_races)

    mag_section = ''
    if mag_race:
        cands = []
        for c in mag_race['candidates']:
            iv = c.get('interview') or {}
            yt = iv.get('youtube_id')
            vid = f' · <a class="vc-card-link" href="https://youtu.be/{yt}" target="_blank" rel="noopener">▶ Interview</a>' if yt else ''
            cands.append(f'<li><strong>{c["name"]}</strong> ({c.get("party","")}){vid}</li>')
        cand_li = '\n            '.join(cands)
        mag_link = f'../{mag_race["race_file"]}#{mag_race["race_anchor"]}' if mag_race.get('race_file') else '../magistrate.html'
        mag_section = f'''
    <section class="closed-primary-callout">
      <h2>Magistrate District {md_num} race</h2>
      <div class="cp-card" style="border-left-color:var(--gold,#f2b84c);">
        <strong>{mag_race["race_name"]} — {len(mag_race["candidates"])} candidate{"s" if len(mag_race["candidates"]) != 1 else ""}</strong>
        <ul style="margin:0.5rem 0 0;padding-left:1.25rem;">
            {cand_li}
        </ul>
        <p style="margin-top:0.5rem;"><a href="{mag_link}" style="color:var(--blue,#4885ed);">Full Hardin Local interviews →</a></p>
      </div>
    </section>'''
    else:
        mag_section = f'''
    <section class="closed-primary-callout">
      <h2>Magistrate District {md_num} race</h2>
      <div class="cp-card">
        <strong>No contested primary in District {md_num}</strong>
        <p style="margin-top:0.4rem;">The District {md_num} magistrate seat is not contested in the May 19 primary, so it won't appear on this district's primary ballot. It may appear on the November general election ballot.</p>
      </div>
    </section>'''

    body = f'''
    <section class="find-ballot-hero">
      <p class="race-eyebrow">— 2026 Primary · Hardin County —</p>
      <h1>Magistrate District <span class="accent">{md_num}</span></h1>
      <p class="race-blurb">
        Magistrate District {md_num} covers {len(precincts)} voting precinct{"s" if len(precincts) != 1 else ""}: {precinct_names}. Your magistrate represents this district on the Hardin County Fiscal Court, which sets the county budget and tax rates. Find your precinct below to see your full ballot.
      </p>
    </section>
{mag_section}
    <section class="vote-centers-section">
      <h2>Precincts in District {md_num}</h2>
      <p class="vc-tagline">Click your precinct's ballot below. Not sure which precinct? Open the boundary-map PDF or check the <a href="https://vrsws.sos.ky.gov/VIC/" target="_blank" rel="noopener">KY Voter Information Center</a>.</p>
      <div class="vc-list-grid">
          {precinct_html}
      </div>
    </section>

    <section class="vote-centers-section">
      <h2>Races on District {md_num} ballots</h2>
      <p class="vc-tagline">Every race appearing for at least some District {md_num} voters. Get your personalized list from <a href="../find-your-ballot.html">Find Your Ballot</a>.</p>
      <div class="vc-list-grid">
          {race_html}
      </div>
    </section>
'''
    return (HEADER.format(title=title, desc=desc, slug=slug, breadcrumb=breadcrumb)
            + body + FOOTER)


def main():
    data = load()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    precincts = data['precincts']
    count = 0

    # City pages — defined by area_group label
    city_map = {
        'Radcliff': 'radcliff',
        'Elizabethtown': 'elizabethtown',
        'Vine Grove': 'vine-grove',
        'West Point': 'west-point',
    }
    for city_name, slug in city_map.items():
        city_precincts = [p for p in precincts if p['area_group'] == city_name]
        if not city_precincts:
            print(f"  [warn] no precincts for {city_name}", file=sys.stderr)
            continue
        html = render_city_page(city_name, slug, city_precincts, data)
        (OUT_DIR / f'{slug}.html').write_text(html)
        count += 1

    # Magistrate pages
    for md in range(1, 9):
        md_precincts = [p for p in precincts if p['magistrate_district'] == md]
        html = render_magistrate_page(md, md_precincts, data)
        (OUT_DIR / f'magistrate-{md}.html').write_text(html)
        count += 1

    print(f"Wrote {count} area pages to {OUT_DIR}", file=sys.stderr)


if __name__ == '__main__':
    main()
