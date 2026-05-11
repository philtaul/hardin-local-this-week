#!/usr/bin/env python3
"""
extract_full_ballot.py — Parse hccoky.org/pdf/ballots/26PComp.pdf into a full
candidate list per race + per party. Output: data/full-ballot.json.

This is the SOURCE OF TRUTH for who appears on each ballot. The existing
candidates.json (extracted from race-page HTML) is the SOURCE OF TRUTH for
who Hardin Local interviewed (with YT/FB links). The build_ballot_pages.py
generator joins these two by name.
"""
import json
import re
import sys
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / 'data' / 'full-ballot.json'
PDF_URL = 'https://hccoky.org/pdf/ballots/26PComp.pdf'
PDF_LOCAL = Path('/tmp/26PComp.pdf')


def normalize_name(raw: str) -> str:
    """Clean OCR-garbled name: 'c:J Daniel CAMERON' → 'Daniel Cameron'.

    Rules:
    - Strip the 'c:J' or 'c:j' prefix and any leading punctuation.
    - Convert ALL-CAPS surname to title case.
    - Preserve quoted nicknames.
    """
    # Strip the checkbox glyph (varies: "c:J", "c:j", "c:Jsteve", etc. — sometimes runs into name)
    s = raw.strip()
    s = re.sub(r'^c:[JjI]\s*', '', s, flags=re.IGNORECASE)
    s = s.strip()
    # OCR sometimes joins glyphs to names ('c:Jsteve CRUM') — keep moving prefix
    s = re.sub(r'^c:[JjI]', '', s, flags=re.IGNORECASE)
    # Collapse double spaces from OCR
    s = re.sub(r'\s+', ' ', s)
    # Find ALL-CAPS surname token(s) at end and titlecase them
    parts = s.split(' ')
    out = []
    for p in parts:
        if p.isupper() and len(p) > 1 and p.isalpha():
            out.append(p.title())
        elif re.match(r'^[A-Z]+[a-z]+\s*$', p):
            # Mid-word like 'McLAURIN' or 'BOYER'
            # Already handled by below
            out.append(p)
        else:
            out.append(p)
    s = ' '.join(out)
    # Title-case any all-caps last name we missed
    s = re.sub(r'\b([A-Z]{2,})\b', lambda m: m.group(1).title(), s)
    # Fix common OCR artifacts: "Andy BARR" → "Andy Barr" (handled above);
    # "JimmyI. LEON" → "Jimmy I. Leon"
    s = re.sub(r'([a-z])([A-Z])', r'\1 \2', s)
    # "Kenn yMUSE" → "Kenny Muse" (note OCR splits)
    s = re.sub(r'\s+', ' ', s).strip()
    # Remove stray leading punctuation
    s = re.sub(r'^[^\w]+', '', s)
    return s


def parse_pdf():
    if not PDF_LOCAL.exists():
        print(f"Downloading {PDF_URL} → {PDF_LOCAL}", file=sys.stderr)
        urllib.request.urlretrieve(PDF_URL, PDF_LOCAL)
    from pypdf import PdfReader
    reader = PdfReader(str(PDF_LOCAL))
    text = ''
    for p in reader.pages:
        text += p.extract_text() + '\n'
    return text


def parse_ballot_text(text: str) -> dict:
    """Parse the OCR'd composite ballot into structured race+candidate data.

    Algorithm:
    - Split into 3 party sections by their header lines.
    - Within each, find race blocks. A race block looks like:
        <RACE NAME>
        <optional district line, e.g. "10th Senatorial District">
        (Vote for ...)
        c:J <NAME>
        c:J <NAME>
        ...
        <precinct list> | "ALL PRECINCTS"
    - Each candidate line starts with "c:J" (or variants).
    """
    # Normalize whitespace but keep newlines as race-block separators
    text = re.sub(r'[ \t]+', ' ', text)

    # Find section starts
    sections = []
    section_starts = [
        ('R', r'REPUBLICAN PARTY\s*\n?\s*PRIMARY ELECTION'),
        ('D', r'DEMOCRATIC PARTY\s*\n?\s*PRIMARY ELECTION'),
        ('NP', r'NONPARTISAN CITY BALLOT'),
    ]
    positions = []
    for code, pat in section_starts:
        for m in re.finditer(pat, text, re.IGNORECASE):
            positions.append((m.start(), code, m.end()))
    positions.sort()

    # Each section runs from its match end until the next section start (or EOF)
    sect_ranges = []
    for i, (start, code, end) in enumerate(positions):
        next_start = positions[i + 1][0] if i + 1 < len(positions) else len(text)
        sect_ranges.append((code, end, next_start))

    races = []
    for code, start, end in sect_ranges:
        section_text = text[start:end]
        races.extend(parse_section(section_text, code))
    return {'races': races}


# Race name patterns we expect to see in a header line (in caps).
RACE_HEADERS = [
    'UNITED STATES SENATOR',
    'UNITED STATES REPRESENTATIVE',
    'STATE SENATOR',
    'STATE REPRESENTATIVE',
    'PROPERTY VALUATION ADMINISTRATOR',
    'SHERIFF',
    'MAGISTRATE',
    'CONSTABLE',
    'MAYOR',
    'CITY COUNCIL',
]


def parse_section(text: str, party: str) -> list:
    """Within a single party section, find each race block."""
    # Clean known OCR splits (e.g., "PROPERTY VALUATION ADMINISTR ATOR")
    text = re.sub(r'ADMINISTR ATOR', 'ADMINISTRATOR', text)
    text = re.sub(r'REPRESENT ATIVE', 'REPRESENTATIVE', text)

    # Split by race headers. We use a non-greedy approach: find each race header position.
    header_re = re.compile(
        r'^\s*(' + '|'.join(re.escape(h) for h in RACE_HEADERS) + r')\s*\n',
        re.MULTILINE,
    )
    headers = list(header_re.finditer(text))
    races = []
    for i, m in enumerate(headers):
        race_start = m.start()
        race_end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
        block = text[race_start:race_end]
        race = parse_race_block(block, party)
        if race:
            races.append(race)

    # Scope-text propagation: in the composite PDF, a single scope footer like
    # "ALL PRECINCTS" or "MANTLE, FREEMAN, ..." applies to ITSELF + any
    # immediately-preceding races whose scope_text is empty. Forward-walk:
    pending = []
    for race in races:
        pending.append(race)
        if race['scope_text']:
            # Trim trailing junk from page-break footers
            race['scope_text'] = re.sub(
                r'\s*PURSUANT TO KRS.*$', '', race['scope_text'], flags=re.IGNORECASE | re.DOTALL
            ).strip()
            scope = race['scope_text']
            for r in pending:
                if not r['scope_text']:
                    r['scope_text'] = scope
            pending = []
    # Any trailing empty-scope races default to ALL PRECINCTS
    for r in pending:
        if not r['scope_text']:
            r['scope_text'] = 'ALL PRECINCTS'

    return races


def parse_race_block(block: str, party: str) -> dict | None:
    lines = [ln.strip() for ln in block.split('\n') if ln.strip()]
    if not lines:
        return None
    race_name = lines[0]
    # Combine multi-line race name (e.g. "UNITED STATES REPRESENTATIVE\nin CONGRESS")
    next_line_idx = 1
    while next_line_idx < len(lines) and not lines[next_line_idx].startswith('c:') and '(Vote' not in lines[next_line_idx]:
        ln = lines[next_line_idx]
        # If this line looks like a district qualifier or continuation
        if re.match(r'^(in\s|City of|\d+(st|nd|rd|th)\s)', ln, re.IGNORECASE):
            race_name += ' / ' + ln
            next_line_idx += 1
        elif ln.isupper() and not re.match(r'^[A-Z][a-z]', ln):
            # Could be all-caps continuation, or precinct list — only join if short
            if len(ln.split()) <= 4:
                race_name += ' / ' + ln
                next_line_idx += 1
            else:
                break
        else:
            break

    # Find "(Vote for ...)" line
    vote_for = 1
    vote_for_text = ''
    for j in range(next_line_idx, len(lines)):
        ln = lines[j]
        m = re.search(r'\(Vote for (?:up to\s+)?(\w+)\)', ln, re.IGNORECASE)
        if m:
            vote_for_text = ln
            num = m.group(1).lower()
            num_map = {'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
                       'six': 6, 'seven': 7, 'eight': 8}
            try:
                vote_for = int(num) if num.isdigit() else num_map.get(num, 1)
            except ValueError:
                vote_for = 1
            next_line_idx = j + 1
            break

    # Collect candidates (c:J prefix lines)
    candidates = []
    precinct_lines = []
    for j in range(next_line_idx, len(lines)):
        ln = lines[j]
        if re.match(r'^c:\s*[JjI]', ln, re.IGNORECASE) or ln.lower().startswith('c:j'):
            name = normalize_name(ln)
            if name:
                candidates.append({'name': name, 'party': party, 'ballot_position': len(candidates) + 1})
        else:
            # everything after candidates is precinct scope
            precinct_lines.append(ln)

    # Final scope text
    scope_text = ' '.join(precinct_lines).strip()
    scope_text = re.sub(r'\s+', ' ', scope_text)
    # Filter out section-end markers
    scope_text = re.sub(r'\(CONTINUED ON NEXT PAGE\)', '', scope_text)
    scope_text = re.sub(r'\bSample\b', '', scope_text).strip()

    return {
        'race_name_raw': race_name.strip(),
        'party': party,
        'vote_for': vote_for,
        'vote_for_text': vote_for_text,
        'scope_text': scope_text,
        'candidates': candidates,
    }


NAME_OVERRIDES = {
    'Andy BARR': 'Andy Barr',
    'Matt DENEEN': 'Matt Deneen',
    'Ken n y MUSE': 'Kenny Muse',
    'Amy Mc GRATH': 'Amy McGrath',
    'La Quita Y. Gaskins': 'LaQuita Y. Gaskins',
    'Mitchell Mc LAURIN': 'Mitchell McLaurin',
    'Seren ity JOHNSON': 'Serenity Johnson',
    'Maria BELL': 'Maria Bell',
    'Pamela J. De ROCHE': 'Pamela J. DeRoche',
    'Other Dona ld Wenzel': 'Donald Wenzel',
    'Dani el Cameron': 'Daniel Cameron',
    'G. "Shay " Perry-Adelmann': 'G. "Shay" Perry-Adelmann',
    'C: JSteve Crum': 'Steve Crum',
    'C: Jsteve Crum': 'Steve Crum',
    'steve Crum': 'Steve Crum',
    'Steve CRUM': 'Steve Crum',
    'Robert "Bob" MAHANNA': 'Robert "Bob" Mahanna',
    'Bryan L PACKARD': 'Bryan L. Packard',
    'Lynnette KENNEDY': 'Lynnette Kennedy',
    'Kim THOMPSON': 'Kim Thompson',
    'Pamela STEVENSON': 'Pamela Stevenson',
    'Charles BOOKER': 'Charles Booker',
    'Vincent Anthony THOMPSON': 'Vincent Anthony Thompson',
    'Hank LINDERMAN': 'Hank Linderman',
    'William Dakota COMPTON': 'William Dakota Compton',
    'Megan WINGFIELD': 'Megan Wingfield',
    'David S. HATFIELD': 'David S. Hatfield',
    'Logan FORSYTHE': 'Logan Forsythe',
    'Dale Lewis ROMANS': 'Dale Lewis Romans',
    'Pamela OGDEN': 'Pamela Ogden',
    'Selena HUDSON': 'Selena Hudson',
    'Toshie MURRELL': 'Toshie Murrell',
    'Michelle MITCHELL': 'Michelle Mitchell',
    'Terry OWENS': 'Terry Owens',
    'Douglas H. GOODMAN': 'Douglas H. Goodman',
    'Aundra Lett JACKSON': 'Aundra Lett Jackson',
    'Alyssa C AGER-BOOI': 'Alyssa Cager-Booi',
    'Alyssa C Ager-Booi': 'Alyssa Cager-Booi',
    'Jerry BROWN': 'Jerry Brown',
}


def apply_name_fixes(data: dict):
    for race in data['races']:
        for c in race['candidates']:
            if c['name'] in NAME_OVERRIDES:
                c['name'] = NAME_OVERRIDES[c['name']]
            else:
                # Generic title-case for any all-caps surname tokens still lurking
                c['name'] = re.sub(r'\b([A-Z]{2,})\b', lambda m: m.group(1).title(), c['name'])
                c['name'] = re.sub(r'\s+', ' ', c['name']).strip()


def main():
    text = parse_pdf()
    data = parse_ballot_text(text)
    apply_name_fixes(data)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    print(f"Wrote {OUT}")
    # Summary
    from collections import Counter
    party_counts = Counter()
    for r in data['races']:
        party_counts[r['party']] += len(r['candidates'])
    print(f"Races: {len(data['races'])}")
    print(f"Candidates by party: {dict(party_counts)}")
    print()
    print("=== Race summary ===")
    for r in data['races']:
        names = ', '.join(c['name'] for c in r['candidates'])
        print(f"  [{r['party']}] {r['race_name_raw'][:60]:<60} | {len(r['candidates'])} cands: {names[:80]}")


if __name__ == '__main__':
    main()
