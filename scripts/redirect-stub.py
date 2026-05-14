#!/usr/bin/env python3
"""
Replace every legacy GH Pages .html with a 301-style redirect stub.

Strategy:
- Map source path → Ghost URL (strip `.html`, add trailing slash, swap to hardinlocal.com)
- Write a meta-refresh + canonical link + noindex + visible link fallback
- Search engines treat meta-refresh + canonical to a new domain as a 301-equivalent

After running, commit + push the repo and GitHub Pages serves the new stubs within ~1 min.

Idempotent — re-run safely; just overwrites.
"""
import os
import re
import sys
from pathlib import Path

ROOT = Path(os.environ.get("LEGACY_ROOT", os.path.expanduser("~/hardin-local-this-week")))
NEW_BASE = "https://hardinlocal.com"

# Overrides where the Ghost-side URL doesn't match the literal path translation
OVERRIDES = {
    "index.html":                          "/",
    "elections.html":                      "/elections/",
    "roundabout.html":                     "/roundabout/",
    "housing-market-update/index.html":    "/housing-market/",
    # leave elections/* and your-ballot/* to default mapping
}

def default_target(rel_path: str) -> str:
    # /elections/area/elizabethtown.html  → /elections/area/elizabethtown/
    # /elections/your-ballot/A001-d.html  → /elections/your-ballot/A001-d/
    no_html = re.sub(r"\.html$", "", rel_path)
    if not no_html.endswith("/"):
        no_html += "/"
    return "/" + no_html.lstrip("/")

def target_for(rel_path: str) -> str:
    if rel_path in OVERRIDES:
        return OVERRIDES[rel_path]
    return default_target(rel_path)

STUB = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>Hardin Local has moved → hardinlocal.com</title>
  <link rel="canonical" href="{full_url}" />
  <meta http-equiv="refresh" content="0; url={full_url}" />
  <meta name="robots" content="noindex" />
  <style>
    body {{ font-family: -apple-system, system-ui, sans-serif; padding: 2rem; max-width: 40rem; margin: auto; }}
    a {{ color: #4885ed; }}
  </style>
</head>
<body>
  <h1>Hardin Local has moved.</h1>
  <p>This page is now at <a href="{full_url}">{full_url}</a>. Redirecting you now…</p>
  <p>If your browser doesn't redirect, click the link above.</p>
</body>
</html>
"""

def main():
    rewritten = 0
    skipped   = 0
    htmls = sorted(ROOT.rglob("*.html"))
    htmls = [p for p in htmls if "/.git/" not in str(p) and "/dev/" not in str(p) and "/templates/" not in str(p)]

    for src in htmls:
        rel = str(src.relative_to(ROOT))
        target_path = target_for(rel)
        full_url = NEW_BASE + target_path
        new_content = STUB.format(full_url=full_url)
        existing = src.read_text(encoding="utf-8", errors="ignore") if src.exists() else ""
        if existing == new_content:
            skipped += 1
            continue
        src.write_text(new_content, encoding="utf-8")
        rewritten += 1

    print(f"Rewrote {rewritten} stub(s), {skipped} no-op (already current).")
    print(f"Total .html under {ROOT}: {len(htmls)}")
    print()
    print("Next: cd ~/hardin-local-this-week && git add -A && git commit -m 'Phase 5: redirect to hardinlocal.com' && git push")

if __name__ == "__main__":
    main()
