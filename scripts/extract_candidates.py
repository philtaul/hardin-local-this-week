#!/usr/bin/env python3
"""
extract_candidates.py — One-time scraper that walks elections/*.html and pulls every
<article class="candidate ..."> block into a structured candidates.json.

Output: data/candidates.json
"""
import json, re, sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ELECTIONS_DIR = REPO / 'elections'
OUT = REPO / 'data' / 'candidates.json'

RACE_FILES = {
    'state-federal.html': {'race_slug': 'state-federal', 'multi_race': True},
    'sheriff.html': {'race_slug': 'sheriff', 'race_name': 'Hardin County Sheriff'},
    'pva.html': {'race_slug': 'pva', 'race_name': 'PVA'},
    'magistrate.html': {'race_slug': 'magistrate', 'multi_race': True},
    'mayor-radcliff.html': {'race_slug': 'mayor-radcliff', 'race_name': 'Mayor of Radcliff'},
    'radcliff-council.html': {'race_slug': 'radcliff-council', 'race_name': 'Radcliff City Council'},
    'mayor-vine-grove.html': {'race_slug': 'mayor-vine-grove', 'race_name': 'Mayor of Vine Grove'},
}

CAND_RE = re.compile(r'<article class="candidate (\w)"[^>]*>(.*?)</article>', re.DOTALL)
NAME_RE = re.compile(r'<div class="candidate-name">([^<]+)</div>')
PARTY_PILL_RE = re.compile(r'<span class="party-pill (\w)">(\w+)</span>')
BALLOT_POS_RE = re.compile(r'Ballot Position (\d+)')
FILED_RE = re.compile(r'Filed ([A-Z][a-z]+ \d+, \d{4})')
YT_EMBED_RE = re.compile(r'youtube\.com/embed/([\w-]+)')
INTERVIEW_TIME_RE = re.compile(r'<div class="interview-time"><span class="label">Interview</span>\s*([^<]+?)</div>', re.DOTALL)
FB_LINK_RE = re.compile(r'<a class="fb-link" href="([^"]+)"')
YT_LIVE_RE = re.compile(r'<a class="yt-live-link" href="([^"]+)"')
NO_REGISTER_RE = re.compile(r'embed-placeholder no-register')
H2_RE = re.compile(r'<h2[^>]*>(.*?)</h2>', re.DOTALL)
DISTRICT_TITLE_RE = re.compile(r'class="district-title"[^>]*>(.*?)</h\d>', re.DOTALL)


def strip_html(s):
    return re.sub(r'<[^>]+>', '', s).strip()


def parse_file(path: Path, meta: dict) -> list:
    html = path.read_text()
    candidates = []
    pos = 0
    current_race = meta.get('race_name')
    current_district = None

    while pos < len(html):
        h2 = H2_RE.search(html, pos)
        cand = CAND_RE.search(html, pos)
        dist = DISTRICT_TITLE_RE.search(html, pos)

        # Priority order: district > candidate > h2 (so district-title h2 doesn't get consumed as race header)
        ordered = [(dist, 'dist'), (cand, 'cand'), (h2, 'h2')]
        candidates_pos = [(m, kind) for m, kind in ordered if m]
        if not candidates_pos:
            break
        # pick by earliest start; ties broken by ordered priority above
        next_match, kind = min(candidates_pos, key=lambda x: (x[0].start(), [k for _, k in ordered].index(x[1])))

        if kind == 'dist':
            current_district = strip_html(dist.group(1))
            pos = dist.end()
            continue
        if kind == 'h2':
            h2_text = h2.group(0)
            if 'district-title' in h2_text:
                # Capture as district, not race
                current_district = strip_html(h2.group(1))
            else:
                current_race = strip_html(h2.group(1))
            pos = h2.end()
            continue
        if kind == 'cand':
            party_class = cand.group(1)  # noqa: keep for clarity
            body = cand.group(2)
            name_m = NAME_RE.search(body)
            if not name_m:
                pos = cand.end()
                continue
            name = name_m.group(1).strip()
            party_pill_m = PARTY_PILL_RE.search(body)
            party = party_pill_m.group(2) if party_pill_m else party_class.upper()
            ballot_pos_m = BALLOT_POS_RE.search(body)
            filed_m = FILED_RE.search(body)
            yt_m = YT_EMBED_RE.search(body)
            interview_m = INTERVIEW_TIME_RE.search(body)
            fb_m = FB_LINK_RE.search(body)
            yt_live_m = YT_LIVE_RE.search(body)
            registered = not bool(NO_REGISTER_RE.search(body))

            entry = {
                "name": name,
                "party": party,
                "race": current_race,
                "race_file": path.name,
                "race_slug": meta['race_slug'],
                "ballot_position": int(ballot_pos_m.group(1)) if ballot_pos_m else None,
                "filed": filed_m.group(1) if filed_m else None,
                "youtube_id": yt_m.group(1) if yt_m else None,
                "facebook_url": fb_m.group(1) if fb_m else None,
                "youtube_live_url": yt_live_m.group(1) if yt_live_m else None,
                "registered": registered,
                "interview_time": strip_html(interview_m.group(1)) if interview_m else None,
            }
            if current_district:
                entry['magistrate_district'] = current_district
            candidates.append(entry)
            pos = cand.end()

    return candidates


def main():
    all_cands = []
    for fname, meta in RACE_FILES.items():
        path = ELECTIONS_DIR / fname
        if not path.exists():
            print(f"  [skip] {fname} not found", file=sys.stderr)
            continue
        cands = parse_file(path, meta)
        print(f"  {fname}: {len(cands)} candidates", file=sys.stderr)
        all_cands.extend(cands)

    out = {
        "_meta": {
            "extracted_from": "elections/*.html",
            "extracted_on": "2026-05-09",
            "total_candidates": len(all_cands),
        },
        "candidates": all_cands,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2))
    print(f"\nWrote {OUT} ({len(all_cands)} candidates)", file=sys.stderr)


if __name__ == '__main__':
    main()
