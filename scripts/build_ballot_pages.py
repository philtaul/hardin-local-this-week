#!/usr/bin/env python3
"""
build_ballot_pages.py — Render per-precinct + per-party ballot pages from
merged_ballot.json (composite PDF + interview data joined).

Output: 174 pages at elections/your-ballot/<code>-<party>.html.
"""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / 'data'
TEMPLATES = REPO / 'templates'
OUT_DIR = REPO / 'elections' / 'your-ballot'

PARTY_LONG = {'R': 'Republican', 'D': 'Democrat', 'I': 'Independent / Nonpartisan'}
PARTY_PILL_CLASS = {'R': 'r', 'D': 'd', 'I': 'n'}
PARTY_FILE_SUFFIX = {'R': 'r', 'D': 'd', 'I': 'i'}


def load():
    return {
        'precincts': json.loads((DATA / 'precincts.json').read_text())['precincts'],
        'merged': json.loads((DATA / 'merged_ballot.json').read_text()),
        'vote_centers': json.loads((DATA / 'vote-centers.json').read_text()),
        'voting_info_snippet': (DATA / 'voting-info.html.snippet').read_text(),
        'template': (TEMPLATES / 'your-ballot.html').read_text(),
    }


def race_applies(race: dict, precinct: dict, party: str) -> bool:
    """Does this race appear on this precinct+party ballot?"""
    rp = race['party']
    if party == 'I':
        # Independent voters only see nonpartisan races
        if rp != 'NP':
            return False
    else:
        # R or D voter: get partisan races for their party + all NP races
        if rp != 'NP' and rp != party:
            return False
    return precinct['code'] in race['scope']['precinct_codes']


def render_candidate(c: dict, race_party: str) -> str:
    """Render one candidate sub-card."""
    party_class = {'R': 'r', 'D': 'd', 'NP': 'n'}.get(c.get('party', 'NP'), 'n')
    interview = c.get('interview') or None
    yt_id = (interview or {}).get('youtube_id')
    fb_url = (interview or {}).get('facebook_url')
    yt_live = (interview or {}).get('youtube_live_url')
    interview_time = (interview or {}).get('interview_time')
    registered = (interview or {}).get('registered', True)

    if yt_id:
        embed = f'''<div class="embed-wrap">
        <iframe src="https://www.youtube.com/embed/{yt_id}" title="{c["name"]} — candidate interview" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen loading="lazy"></iframe>
      </div>'''
    elif interview and not registered:
        embed = '''<div class="embed-wrap">
        <div class="embed-placeholder no-register">
          <div class="ph-status">— No Hardin Local interview —</div>
          <div class="ph-msg">Did not register for the free Hardin Local primary interview.</div>
        </div>
      </div>'''
    elif interview:
        # Candidate IS in our interview-tracking data (existing race page) but the
        # video isn't published in our data. Treat as "interview pending / not yet on file".
        embed = '''<div class="embed-wrap">
        <div class="embed-placeholder no-interview">
          <div class="ph-status">— Interview pending —</div>
          <div class="ph-msg">Hardin Local has interview footage scheduled for this candidate but the edited video isn\'t published yet. Check the race page for the latest.</div>
        </div>
      </div>'''
    else:
        # Candidate is on the official ballot but Hardin Local didn't interview them.
        # This is normal for some statewide and down-ballot races — we focus capacity
        # on local Hardin County races where voter information is hardest to find.
        embed = '''<div class="embed-wrap">
        <div class="embed-placeholder no-interview">
          <div class="ph-status">— No Hardin Local interview —</div>
          <div class="ph-msg">Hardin Local does not interview every candidate in races with statewide or multi-county audiences. We focus on the local races where voter information is hardest to find.</div>
        </div>
      </div>'''

    foot_parts = []
    if interview_time:
        foot_parts.append(f'<div class="interview-time"><span class="label">Interview</span> {interview_time}</div>')
    if yt_id:
        foot_parts.append('<div class="note">Edited video published.</div>')
    if fb_url:
        foot_parts.append(f'<a class="fb-link" href="{fb_url}" target="_blank" rel="noopener">📘 Also on Facebook →</a>')
    if yt_live:
        foot_parts.append(f'<a class="yt-live-link" href="{yt_live}" target="_blank" rel="noopener">📹 Raw livestream →</a>')

    party_label = c.get('party', 'NP')
    if party_label == 'NP':
        party_label = 'NP'
    foot_html = ''.join(f'\n        {x}' for x in foot_parts)

    pos_html = ''
    if c.get('ballot_position'):
        pos_html = f'<span class="ballot">Ballot Position {c["ballot_position"]}</span>'

    return f'''      <article class="candidate {party_class}">
        <div class="candidate-head">
          <div class="candidate-name">{c["name"]}</div>
          <div class="candidate-meta">
            <span class="party-pill {party_class}">{party_label}</span>
            {pos_html}
          </div>
        </div>
        {embed}
        <div class="candidate-foot">{foot_html}
        </div>
      </article>'''


def candidate_sort_key(c: dict):
    """Within a race: candidates with a published YouTube interview first,
    then by ballot position (asc, None last), then by name."""
    interview = c.get('interview') or {}
    has_video = 1 if interview.get('youtube_id') else 0
    bp = c.get('ballot_position') or 999
    return (-has_video, bp, c.get('name', ''))


def render_race(race: dict, race_idx: int, party: str) -> str:
    """Render one race section."""
    race_party = race['party']
    pill_class = {'R': 'r', 'D': 'd', 'NP': 'n'}[race_party]
    pill_label = {'R': 'R Primary', 'D': 'D Primary', 'NP': 'Nonpartisan'}[race_party]

    sorted_cands = sorted(race['candidates'], key=candidate_sort_key)
    cand_html = '\n'.join(render_candidate(c, race_party) for c in sorted_cands)

    deeplink = ''
    if race.get('race_file'):
        link = f'../{race["race_file"]}'
        if race.get('race_anchor'):
            link += f'#{race["race_anchor"]}'
        deeplink = f'<div class="ballot-race-foot"><a class="ballot-race-deeplink" href="{link}">Watch Hardin Local interviews on the {race["race_name"]} page →</a></div>'

    vfc = race.get('vote_for', 1)
    vfc_label = f'Vote for not more than {vfc}' if vfc > 1 else 'Vote for one'

    partial_note = ''
    if race['scope'].get('has_partial'):
        partial_note = '<div class="ballot-race-note">⚠️ Some addresses in your precinct are inside the city limits and some aren\'t. If you\'re not sure, check your address against the official precinct map.</div>'

    return f'''        <section class="ballot-race" id="race-{race["race_slug"]}">
          <header class="ballot-race-head">
            <span class="ballot-race-num">#{race_idx}</span>
            <div class="ballot-race-title-block">
              <div class="ballot-race-label">{pill_label} · {vfc_label}</div>
              <h3 class="ballot-race-name">{race["race_name"]}</h3>
            </div>
          </header>
          <div class="ballot-race-blurb">{race.get("what_at_stake", "")}</div>
          {partial_note}
          <div class="ballot-race-candidates">
{cand_html}
          </div>
          {deeplink}
        </section>'''


def render_ballot_toc(applicable: list) -> str:
    if not applicable:
        return '<em>(See empty-ballot message below.)</em>'
    return ' · '.join(
        f'<a href="#race-{r["race_slug"]}">{i}. {r["race_name"]}</a>'
        for i, r in enumerate(applicable, 1)
    )


def render_vote_center_list(vote_centers: dict) -> str:
    out = []
    for vc in vote_centers['election_day_2026_05_19']['locations']:
        addr = f'{vc["street"]}, {vc["city"]} {vc["zip"]}'
        gmap = f'https://www.google.com/maps/search/?api=1&query={vc["lat"]},{vc["lng"]}'
        out.append(f'''<div class="vc-card vc-card-eday">
            <div class="vc-card-title">{vc["title"]}</div>
            <div class="vc-card-addr">{addr}</div>
            <div class="vc-card-hours">{vc["hours"]} · Election Day</div>
            <a class="vc-card-link" href="{gmap}" target="_blank" rel="noopener">Open in Google Maps →</a>
          </div>''')
    out.append('<div class="vc-divider">— Early voting (May 14–16, no excuse needed) —</div>')
    for vc in vote_centers['early_voting_no_excuse_2026_05_14_to_16']['locations']:
        addr = f'{vc["street"]}, {vc["city"]} {vc["zip"]}'
        gmap = f'https://www.google.com/maps/search/?api=1&query={vc["lat"]},{vc["lng"]}'
        out.append(f'''<div class="vc-card vc-card-early">
            <div class="vc-card-title">{vc["title"]}</div>
            <div class="vc-card-addr">{addr}</div>
            <div class="vc-card-hours">{vc["hours"]} · May 14–16</div>
            <a class="vc-card-link" href="{gmap}" target="_blank" rel="noopener">Open in Google Maps →</a>
          </div>''')
    return '\n          '.join(out)


def render_map_init(vote_centers: dict) -> str:
    pins = []
    for vc in vote_centers['election_day_2026_05_19']['locations']:
        title = vc['title'].replace("'", "\\'")
        addr = f'{vc["street"]}, {vc["city"]} {vc["zip"]}'.replace("'", "\\'")
        pins.append(f"      [{vc['lat']}, {vc['lng']}, '{title}', '{addr}', 'eday']")
    for vc in vote_centers['early_voting_no_excuse_2026_05_14_to_16']['locations']:
        title = (vc['title'] + ' (early voting)').replace("'", "\\'")
        addr = f'{vc["street"]}, {vc["city"]} {vc["zip"]}'.replace("'", "\\'")
        pins.append(f"      [{vc['lat']}, {vc['lng']}, '{title}', '{addr}', 'early']")
    pin_arr = ',\n'.join(pins)
    return f'''<script>
  document.addEventListener('DOMContentLoaded', function() {{
    var mapEl = document.getElementById('vote-centers-map');
    if (!mapEl || typeof L === 'undefined') return;
    var pins = [
{pin_arr}
    ];
    var avgLat = pins.reduce(function(s, p) {{ return s + p[0]; }}, 0) / pins.length;
    var avgLng = pins.reduce(function(s, p) {{ return s + p[1]; }}, 0) / pins.length;
    var map = L.map('vote-centers-map').setView([avgLat, avgLng], 11);
    L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
      attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxZoom: 18
    }}).addTo(map);
    var edayIcon = L.divIcon({{className: 'vc-pin vc-pin-eday', html: '🗳️', iconSize: [32, 32], iconAnchor: [16, 16]}});
    var earlyIcon = L.divIcon({{className: 'vc-pin vc-pin-early', html: '⏰', iconSize: [32, 32], iconAnchor: [16, 16]}});
    pins.forEach(function(p) {{
      var icon = p[4] === 'early' ? earlyIcon : edayIcon;
      L.marker([p[0], p[1]], {{icon: icon}}).addTo(map)
        .bindPopup('<strong>' + p[2] + '</strong><br>' + p[3]);
    }});
  }});
</script>'''


def render_page(precinct: dict, party: str, data: dict) -> str:
    races = data['merged']['races']
    applicable = [r for r in races if race_applies(r, precinct, party)]

    if party == 'I':
        hero_blurb = 'Kentucky has a closed primary — independents and "no party" voters do not get a partisan ballot on May 19. You\'ll see only the nonpartisan races below (city offices and any school board races).'
        if not applicable:
            hero_blurb += ' Based on your precinct, you do not have any nonpartisan races on the May 19 ballot.'
    else:
        hero_blurb = f'These are every race + candidate on your {PARTY_LONG[party]} primary ballot in {precinct["name"]} on Tuesday, May 19, 2026. Where Hardin Local interviewed the candidate, the video is embedded inline.'

    if precinct['state_house'] == '10':
        hd_pill = '<span class="pill">KY House District 10</span>'
    elif precinct['state_house'] == '27':
        hd_pill = '<span class="pill">KY House District 27</span>'
    else:
        hd_pill = ''

    sms_body = f'My Hardin Local ballot for May 19 ({precinct["name"]} {PARTY_LONG[party]}): https://philtaul.github.io/hardin-local-this-week/elections/your-ballot/{precinct["code"]}-{PARTY_FILE_SUFFIX[party]}.html'.replace(' ', '%20')

    if applicable:
        race_html = '\n'.join(render_race(r, i + 1, party) for i, r in enumerate(applicable))
    else:
        race_html = '<div class="ballot-empty">No races on the May 19 ballot for this precinct + party combination. (Independents do not get a partisan primary ballot in Kentucky — but they DO get to vote in nonpartisan races. If you live in Radcliff or Vine Grove, you should see a city race here. If not, you may not have any races on May 19, but other races will appear in the November general election.)</div>'

    leaflet_css = '<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=" crossorigin="" />'
    leaflet_js = '<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" crossorigin=""></script>'

    page = data['template']
    replacements = {
        '{{TITLE}}': f'{precinct["name"]} · {PARTY_LONG[party]}',
        '{{PRECINCT_CODE}}': precinct['code'],
        '{{PRECINCT_NAME}}': precinct['name'],
        '{{PARTY_CODE}}': party,
        '{{PARTY_LONG}}': PARTY_LONG[party],
        '{{PARTY_PILL_CLASS}}': PARTY_PILL_CLASS[party],
        '{{MD}}': str(precinct['magistrate_district']),
        '{{HD_PILL}}': hd_pill,
        '{{RACE_COUNT}}': str(len(applicable)),
        '{{RACE_COUNT_S}}': '' if len(applicable) == 1 else 's',
        '{{HERO_BLURB}}': hero_blurb,
        '{{VOTING_INFO_SNIPPET}}': data['voting_info_snippet'],
        '{{VOTE_CENTER_LIST}}': render_vote_center_list(data['vote_centers']),
        '{{BALLOT_TOC}}': render_ballot_toc(applicable),
        '{{BALLOT_RACES}}': race_html,
        '{{SMS_BODY}}': sms_body,
        '{{LEAFLET_CSS}}': leaflet_css,
        '{{LEAFLET_JS}}': leaflet_js,
        '{{MAP_INIT_JS}}': render_map_init(data['vote_centers']),
    }
    for k, v in replacements.items():
        page = page.replace(k, v)
    return page


def main():
    data = load()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Clean stale outputs
    for f in OUT_DIR.glob('*.html'):
        f.unlink()

    count = 0
    for precinct in data['precincts']:
        for party in ['R', 'D', 'I']:
            html = render_page(precinct, party, data)
            out_path = OUT_DIR / f'{precinct["code"]}-{PARTY_FILE_SUFFIX[party]}.html'
            out_path.write_text(html)
            count += 1

    print(f'Wrote {count} pages to {OUT_DIR}', file=sys.stderr)


if __name__ == '__main__':
    main()
