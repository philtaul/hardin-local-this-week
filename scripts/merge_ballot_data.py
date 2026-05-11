#!/usr/bin/env python3
"""
merge_ballot_data.py — Merge full-ballot.json (source of truth: 26PComp.pdf) with
candidates.json (interview metadata from existing race pages) into one
machine-friendly merged_ballot.json.

Steps:
1. Parse each race's `scope_text` into a list of precinct codes.
2. For each candidate, fuzzy-match against candidates.json to attach interview data
   (youtube_id, facebook_url, interview_time, registered, race_slug for deep-link).
3. Add hand-curated `race_slug`, `race_file`, and `what_at_stake` per race.
4. Write merged_ballot.json.
"""
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / 'data'

PRECINCT_NAME_TO_CODE = {
    'WEST POINT': 'A001',
    'RADCLIFF EAST': 'A002',
    'RADCLIFF NORTH': 'A003',
    'RADCLIFF NORTHWEST': 'A004',
    'RADCLIFF WEST': 'A005',
    'RED HILL': 'A006',
    'VETERANS': 'A007',
    'RADCLIFF SOUTHWEST': 'A008',
    'FORT KNOX 26': 'A009',
    'FORT KNOX 27': 'A010',
    'RADCLIFF SOUTH': 'B001',
    'RADCLIFF SOUTHEAST': 'B002',
    'SHELTON': 'B003',
    'WOODLAND': 'B004',
    'LONGVIEW': 'B005',
    'PARKWAY': 'B006',
    'HIGHLANDS': 'C001',
    'CITY PARK': 'C002',
    'COLESBURG': 'C003',
    'TUNNEL HILL': 'C004',
    'LINCOLN TRAIL NORTH': 'C005',
    'LINCOLN TRAIL SOUTH': 'C006',
    'ETOWN EAST': 'C007',
    'ELIZABETHTOWN EAST': 'C007',
    'MANTLE': 'D001',
    'FREEMAN': 'D002',
    'OAKLAWN': 'D003',
    'PINE VALLEY': 'D004',
    'HELMWOOD HEIGHTS': 'D005',
    'HELM': 'D006',
    'CENTRAL': 'E001',
    'ETOWN NORTH': 'E002',
    'ELIZABETHTOWN NORTH': 'E002',
    'ETOWN WEST': 'E003',
    'ELIZABETHTOWN WEST': 'E003',
    'VALLEY CREEK': 'E004',
    'MEMORIAL': 'E005',
    'VANMETER CITY': 'E006',
    'VAN METER CITY': 'E006',
    'HAYCRAFT': 'E007',
    'VANMETER': 'F001',
    'VAN METER': 'F001',
    'CHELF': 'F002',
    'COUNTRY CLUB': 'F003',
    'GLENDALE': 'F004',
    'SOUTH DIXIE': 'F005',
    'SONORA': 'F006',
    'UPTON': 'F007',
    'EASTVIEW': 'G001',
    'STEPHENSBURG': 'G002',
    'MEETING CREEK': 'G003',
    'WHITE MILLS': 'G004',
    'PATRIOT': 'G005',
    'CECILIA': 'G006',
    'ST. JOHN': 'G007',
    'ST JOHN': 'G007',
    'HOWEVALLEY': 'G008',
    'RINEYVILLE SOUTH': 'G009',
    'RINEYVILLE NORTH': 'H001',
    'RINEYVILLE WEST': 'H004',
    'VINE GROVE EAST': 'H005',
    'VINE GROVE WEST': 'H006',
    'VINE GROVE SOUTH': 'H007',
    'YATES': 'H008',
}

ALL_PRECINCT_CODES = [
    'A001', 'A002', 'A003', 'A004', 'A005', 'A006', 'A007', 'A008', 'A009', 'A010',
    'B001', 'B002', 'B003', 'B004', 'B005', 'B006',
    'C001', 'C002', 'C003', 'C004', 'C005', 'C006', 'C007',
    'D001', 'D002', 'D003', 'D004', 'D005', 'D006',
    'E001', 'E002', 'E003', 'E004', 'E005', 'E006', 'E007',
    'F001', 'F002', 'F003', 'F004', 'F005', 'F006', 'F007',
    'G001', 'G002', 'G003', 'G004', 'G005', 'G006', 'G007', 'G008', 'G009',
    'H001', 'H004', 'H005', 'H006', 'H007', 'H008',
]

# Hand-curated race-level metadata.
# Keyed by (party, normalized race_name_raw substring match).
RACE_META = {
    ('R', 'UNITED STATES SENATOR'): {
        'race_slug': 'us-senate',
        'short_name': 'U.S. Senator (Kentucky)',
        'race_file': 'state-federal.html',
        'race_anchor': '',
        'what_at_stake': 'Six-year term in the U.S. Senate. Votes on federal laws, judicial confirmations, and treaties.',
    },
    ('D', 'UNITED STATES SENATOR'): {
        'race_slug': 'us-senate',
        'short_name': 'U.S. Senator (Kentucky)',
        'race_file': 'state-federal.html',
        'race_anchor': '',
        'what_at_stake': 'Six-year term in the U.S. Senate. Votes on federal laws, judicial confirmations, and treaties.',
    },
    ('R', 'UNITED STATES REPRESENTATIVE'): {
        'race_slug': 'us-house-ky2',
        'short_name': 'U.S. Representative — Kentucky 2nd District',
        'race_file': 'state-federal.html',
        'race_anchor': '',
        'what_at_stake': 'Two-year term in the U.S. House. Hardin County is in Kentucky\'s 2nd Congressional District.',
    },
    ('D', 'UNITED STATES REPRESENTATIVE'): {
        'race_slug': 'us-house-ky2',
        'short_name': 'U.S. Representative — Kentucky 2nd District',
        'race_file': 'state-federal.html',
        'race_anchor': '',
        'what_at_stake': 'Two-year term in the U.S. House.',
    },
    ('R', 'STATE SENATOR'): {
        'race_slug': 'ky-senate-10',
        'short_name': 'Kentucky State Senator — 10th District',
        'race_file': 'state-federal.html',
        'race_anchor': '',
        'what_at_stake': 'Four-year term in the Kentucky Senate. SD-10 covers all of Hardin County.',
    },
    ('R', 'STATE REPRESENTATIVE / 10th'): {
        'race_slug': 'ky-house-10',
        'short_name': 'Kentucky State Representative — 10th District',
        'race_file': 'state-federal.html',
        'race_anchor': '',
        'what_at_stake': 'Two-year term in the Kentucky House. HD-10 covers western Hardin County, Vine Grove, Cecilia, and surrounding precincts.',
    },
    ('R', 'STATE REPRESENTATIVE / 27th'): {
        'race_slug': 'ky-house-27',
        'short_name': 'Kentucky State Representative — 27th District',
        'race_file': 'state-federal.html',
        'race_anchor': '',
        'what_at_stake': 'Two-year term in the Kentucky House. HD-27 covers most of Radcliff, Fort Knox 27, and a few neighboring precincts.',
    },
    ('R', 'PROPERTY VALUATION ADMINISTRATOR'): {
        'race_slug': 'pva',
        'short_name': 'Property Valuation Administrator',
        'race_file': 'pva.html',
        'race_anchor': '',
        'what_at_stake': 'Four-year term. The PVA decides what your house and car are worth for tax purposes.',
    },
    ('R', 'SHERIFF'): {
        'race_slug': 'sheriff',
        'short_name': 'Hardin County Sheriff',
        'race_file': 'sheriff.html',
        'race_anchor': '',
        'what_at_stake': 'Four-year term. The Sheriff is one of the county\'s elected law-enforcement officers — patrol, civil-process service, and court security. (The county jail is run separately by the Jailer\'s office.)',
    },
    ('R', 'MAGISTRATE / 4th'): {
        'race_slug': 'magistrate-4',
        'short_name': 'Magistrate, District 4',
        'race_file': 'magistrate.html',
        'race_anchor': 'd4',
        'what_at_stake': 'Four-year term on Hardin County Fiscal Court. Magistrates set the county budget and tax rates.',
    },
    ('R', 'MAGISTRATE / 5th'): {
        'race_slug': 'magistrate-5',
        'short_name': 'Magistrate, District 5',
        'race_file': 'magistrate.html',
        'race_anchor': 'd5',
        'what_at_stake': 'Four-year term on Hardin County Fiscal Court.',
    },
    ('R', 'MAGISTRATE / 6th'): {
        'race_slug': 'magistrate-6',
        'short_name': 'Magistrate, District 6',
        'race_file': 'magistrate.html',
        'race_anchor': 'd6',
        'what_at_stake': 'Four-year term on Hardin County Fiscal Court.',
    },
    ('R', 'MAGISTRATE / 7th'): {
        'race_slug': 'magistrate-7',
        'short_name': 'Magistrate, District 7',
        'race_file': 'magistrate.html',
        'race_anchor': 'd7',
        'what_at_stake': 'Four-year term on Hardin County Fiscal Court.',
    },
    ('R', 'MAGISTRATE / 8th'): {
        'race_slug': 'magistrate-8',
        'short_name': 'Magistrate, District 8',
        'race_file': 'magistrate.html',
        'race_anchor': 'd8',
        'what_at_stake': 'Four-year term on Hardin County Fiscal Court.',
    },
    ('R', 'CONSTABLE / 4th'): {
        'race_slug': 'constable-4',
        'short_name': 'Constable, District 4',
        'race_file': '',
        'race_anchor': '',
        'what_at_stake': 'Four-year term. Constables serve civil court papers and have limited law-enforcement authority. Hardin Local did not interview these candidates.',
    },
    ('NP', 'MAYOR / City of Radcliff'): {
        'race_slug': 'mayor-radcliff',
        'short_name': 'Mayor of Radcliff',
        'race_file': 'mayor-radcliff.html',
        'race_anchor': '',
        'what_at_stake': 'Four-year term. The Mayor runs Radcliff city government — police, public works, planning. Winner takes all on May 19 — no November runoff.',
    },
    ('NP', 'CITY COUNCIL / City of Radcliff'): {
        'race_slug': 'radcliff-council',
        'short_name': 'Radcliff City Council (six seats)',
        'race_file': 'radcliff-council.html',
        'race_anchor': '',
        'what_at_stake': 'Two-year terms for six at-large city council seats. The council writes Radcliff\'s ordinances and budget. Top six finishers win outright on May 19 — no November runoff.',
    },
    ('NP', 'MAYOR / City of Vine Grove'): {
        'race_slug': 'mayor-vine-grove',
        'short_name': 'Mayor of Vine Grove',
        'race_file': 'mayor-vine-grove.html',
        'race_anchor': '',
        'what_at_stake': 'Four-year term. The Mayor runs Vine Grove city government. Winner takes all on May 19 — no November runoff.',
    },
}


def parse_scope(scope_text: str) -> dict:
    """Convert scope_text → {precinct_codes, has_partial, raw}."""
    if not scope_text or 'ALL PRECINCTS' in scope_text.upper():
        return {'precinct_codes': list(ALL_PRECINCT_CODES), 'has_partial': False, 'raw': scope_text or 'ALL PRECINCTS'}

    s = scope_text.upper()
    # Extract precincts before "; Part of" — these are full-precinct
    # Extract precincts after "; Part of" — these are partial
    full_part, partial_part = s, ''
    if 'PART OF' in s:
        m = re.search(r';?\s*PART OF\s*(.*)$', s)
        if m:
            partial_part = m.group(1)
            full_part = s[:m.start()]

    def split_names(part):
        if not part:
            return []
        # Split by commas + " and "
        part = re.sub(r'\s+and\s+', ',', part, flags=re.IGNORECASE)
        chunks = [c.strip().rstrip('.;,').strip() for c in part.split(',') if c.strip()]
        return chunks

    full_names = split_names(full_part)
    partial_names = split_names(partial_part)

    codes = []
    unmatched = []
    for n in full_names + partial_names:
        n_clean = n.strip().upper()
        n_clean = re.sub(r'[\.,;]+$', '', n_clean).strip()
        if n_clean in PRECINCT_NAME_TO_CODE:
            codes.append(PRECINCT_NAME_TO_CODE[n_clean])
        elif n_clean:
            unmatched.append(n)

    if unmatched:
        print(f"  [warn] Unmatched precinct names in scope {scope_text!r}: {unmatched}", file=sys.stderr)

    return {
        'precinct_codes': sorted(set(codes)),
        'has_partial': bool(partial_names),
        'partial_codes': sorted({PRECINCT_NAME_TO_CODE.get(n.strip().upper(), n) for n in partial_names if n.strip().upper() in PRECINCT_NAME_TO_CODE}),
        'raw': scope_text,
    }


# Race category + display order. Lower number = renders earlier on the ballot page.
# Phil's preferred order: local → state → federal.
RACE_SORT_KEY = {
    'mayor-radcliff':   (10, 1, 'Local · City'),
    'mayor-vine-grove': (10, 2, 'Local · City'),
    'radcliff-council': (10, 3, 'Local · City'),
    'magistrate-1':     (20, 1, 'Local · County'),
    'magistrate-2':     (20, 2, 'Local · County'),
    'magistrate-3':     (20, 3, 'Local · County'),
    'magistrate-4':     (20, 4, 'Local · County'),
    'magistrate-5':     (20, 5, 'Local · County'),
    'magistrate-6':     (20, 6, 'Local · County'),
    'magistrate-7':     (20, 7, 'Local · County'),
    'magistrate-8':     (20, 8, 'Local · County'),
    'constable-4':      (20, 9, 'Local · County'),
    'sheriff':          (20, 10, 'Local · County'),
    'pva':              (20, 11, 'Local · County'),
    'ky-house-10':      (30, 1, 'State'),
    'ky-house-27':      (30, 2, 'State'),
    'ky-senate-10':     (30, 3, 'State'),
    'us-house-ky2':     (40, 1, 'Federal'),
    'us-senate':        (40, 2, 'Federal'),
}


def race_sort_key(race_slug: str):
    return RACE_SORT_KEY.get(race_slug, (99, 99, 'Other'))


def find_race_meta(race: dict):
    raw = race['race_name_raw'].upper()
    party = race['party']
    for (p, key), meta in RACE_META.items():
        if p == party and key.upper() in raw:
            return meta
    return None


def normalize_for_match(name: str) -> str:
    """Reduce a candidate name to a 'first-last' comparable form."""
    s = name.strip().lower()
    s = re.sub(r'^(rep|sen|hon|mr|mrs|ms|dr)\.\s+', '', s)  # strip title prefix
    s = re.sub(r'\bjr\.?\b', '', s)
    s = re.sub(r'\bsr\.?\b', '', s)
    s = re.sub(r'"[^"]*"', '', s)
    # Treat hyphens as word separators BEFORE stripping non-word chars,
    # so "Lett-Jackson" → "lett jackson" (3 tokens after split, not glued)
    s = s.replace('-', ' ')
    s = re.sub(r'[^\w\s]', '', s)
    s = re.sub(r'\s+', ' ', s).strip()
    # Reduce to "first last" — drop middle names/initials
    parts = s.split()
    parts = [p for p in parts if len(p) > 1]  # drop single-letter middle initials
    if len(parts) >= 2:
        s = f'{parts[0]} {parts[-1]}'
    return s


def attach_interview_data(candidates: list, interviews_by_norm: dict, race_slug: str):
    for c in candidates:
        norm = normalize_for_match(c['name'])
        match = interviews_by_norm.get(norm)
        # Match by name only — interview data is rich enough that a same-name match
        # in a different race is implausible at our scale (74 candidates).
        if match:
            c['interview'] = {
                'youtube_id': match.get('youtube_id'),
                'facebook_url': match.get('facebook_url'),
                'youtube_live_url': match.get('youtube_live_url'),
                'interview_time': match.get('interview_time'),
                'registered': match.get('registered', True),
                'matched_race_slug': match.get('race_slug'),
            }
        else:
            c['interview'] = None


def main():
    full = json.loads((DATA / 'full-ballot.json').read_text())
    cands_json = json.loads((DATA / 'candidates.json').read_text())
    interviews_by_norm = {}
    for c in cands_json['candidates']:
        # Sometimes magistrate.html lists same candidate with district context;
        # we keep the most-detailed entry per normalized-name.
        norm = normalize_for_match(c['name'])
        # Prefer entries with youtube_id
        existing = interviews_by_norm.get(norm)
        if existing is None or (c.get('youtube_id') and not existing.get('youtube_id')):
            interviews_by_norm[norm] = c

    merged_races = []
    for race in full['races']:
        scope = parse_scope(race['scope_text'])
        meta = find_race_meta(race)
        if not meta:
            print(f"  [warn] No meta for race: [{race['party']}] {race['race_name_raw']}", file=sys.stderr)
            meta = {
                'race_slug': re.sub(r'[^a-z0-9]+', '-', race['race_name_raw'].lower())[:40],
                'short_name': race['race_name_raw'],
                'race_file': '',
                'race_anchor': '',
                'what_at_stake': '',
            }
        # Attach interviews
        attach_interview_data(race['candidates'], interviews_by_norm, meta['race_slug'])
        sort_cat, sort_office, category_label = race_sort_key(meta['race_slug'])
        merged_races.append({
            'race_slug': meta['race_slug'],
            'race_name': meta['short_name'],
            'party': race['party'],
            'vote_for': race['vote_for'],
            'vote_for_text': race['vote_for_text'],
            'race_file': meta['race_file'],
            'race_anchor': meta['race_anchor'],
            'what_at_stake': meta['what_at_stake'],
            'scope': scope,
            'candidates': race['candidates'],
            'race_name_raw': race['race_name_raw'],
            'category': category_label,
            'sort_category': sort_cat,
            'sort_office': sort_office,
        })

    # Sort by (category, office, party-preference) so output is in display order.
    # Within same race_slug, R comes before D before NP.
    party_order = {'R': 1, 'D': 2, 'NP': 3}
    merged_races.sort(key=lambda r: (r['sort_category'], r['sort_office'], party_order.get(r['party'], 9)))

    out = {
        '_meta': {
            'merged_from': ['full-ballot.json', 'candidates.json'],
            'merged_on': '2026-05-09',
            'total_races': len(merged_races),
            'total_candidates': sum(len(r['candidates']) for r in merged_races),
            'total_interviewed': sum(1 for r in merged_races for c in r['candidates'] if c.get('interview')),
        },
        'races': merged_races,
    }
    out_path = DATA / 'merged_ballot.json'
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"\nWrote {out_path}")
    print(f"Races: {len(merged_races)}")
    print(f"Total candidates: {out['_meta']['total_candidates']}")
    print(f"With Hardin Local interview: {out['_meta']['total_interviewed']}")
    print()
    for r in merged_races:
        interviewed = sum(1 for c in r['candidates'] if c.get('interview'))
        print(f"  [{r['party']}] {r['race_name']:<55} | {len(r['candidates'])} cands ({interviewed} interviewed) | scope: {len(r['scope']['precinct_codes'])} precincts")


if __name__ == '__main__':
    main()
