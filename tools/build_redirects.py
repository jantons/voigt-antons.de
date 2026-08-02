#!/usr/bin/env python3
"""
Generate redirect pages from data/redirects.json.

Whenever a publication id changes — because the numbering in the
Publikationsverzeichnis changed, or a year was corrected — the old URL must
keep working: those URLs are indexed and cited. Add an entry here instead of
letting the old address 404.

data/redirects.json:
    [{"from": "/publication/2016-09-15-J6", "to": "/publication/2017-01-01-J6"}]

Usage:
    python3 tools/build_redirects.py
"""

import html
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "redirects.json"

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Moved &mdash; Jan-Niklas Voigt-Antons</title>
<link rel="canonical" href="https://voigt-antons.de{to}">
<meta name="robots" content="noindex, follow">
<meta http-equiv="refresh" content="0; url={to}">
<script>location.replace("{to}");</script>
<style>
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
     max-width:34rem;margin:20vh auto;padding:0 1.5rem;line-height:1.6;color:#0b0d13}}
a{{color:#5645f5}}
</style>
</head>
<body>
<p>This publication moved to <a href="{to}">{to}</a>.</p>
</body>
</html>
"""


def main():
    if not DATA.exists():
        print("no data/redirects.json — nothing to do")
        return 0

    entries = json.loads(DATA.read_text(encoding="utf-8"))
    written, skipped = 0, []

    for e in entries:
        src, dst = e["from"].strip("/"), e["to"]
        target = ROOT / src

        # Never shadow a real page: if something already lives at the old
        # address, the redirect would hide it.
        if (target / "index.html").exists() and not _is_redirect(target / "index.html"):
            skipped.append(e["from"])
            continue

        if not (ROOT / dst.strip("/") / "index.html").exists():
            print("warning: redirect target does not exist: %s" % dst)

        target.mkdir(parents=True, exist_ok=True)
        (target / "index.html").write_text(
            TEMPLATE.format(to=html.escape(dst)), encoding="utf-8")
        written += 1

    print("wrote %d redirect pages" % written)
    if skipped:
        print("skipped (a real page already lives there): %s" % ", ".join(skipped))
        return 1
    return 0


def _is_redirect(path):
    return "location.replace(" in path.read_text(encoding="utf-8")[:1200]


if __name__ == "__main__":
    sys.exit(main())
