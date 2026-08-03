#!/usr/bin/env python3
"""
Regenerate sitemap.xml from the pages that actually exist on disk.

Run after the two page generators; the CI workflow does this automatically.

Usage:
    python3 tools/build_sitemap.py
"""

import datetime
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
BASE = "https://voigt-antons.de"

# Pages that should not appear in search results.
EXCLUDE = {"/impressum/", "/tags/", "/404.html"}

STATIC = ["/", "/research/", "/projects/", "/publications/", "/cv/", "/teaching/",
          "/blog/", "/downloads/"]

# The German versions are separate URLs and belong in the sitemap. Each entry
# carries xhtml:link alternates, because a sitemap that lists /de/ without
# declaring the pairing invites search engines to read the two as duplicates.
TRANSLATED = ["/", "/research/", "/projects/", "/cv/", "/teaching/"]


def priority(url):
    if url == "/":
        return "1.0"
    if url in STATIC:
        return "0.8"
    if url.startswith("/de/") or url == "/de/":
        return "0.8"
    if url.startswith("/posts/"):
        return "0.7"
    return "0.5"


def main():
    today = datetime.date.today().isoformat()

    urls = [u for u in STATIC if u not in EXCLUDE]
    urls += ["/de%s" % u for u in TRANSLATED
             if (ROOT / ("de" + u).lstrip("/") / "index.html").exists()]

    posts = json.loads((ROOT / "data" / "posts.json").read_text(encoding="utf-8"))["posts"]
    urls += [p["url"] for p in posts]

    pub_dir = ROOT / "publication"
    if pub_dir.exists():
        urls += sorted(
            "/publication/%s" % d.name
            for d in pub_dir.iterdir()
            if d.is_dir() and (d / "index.html").exists()
        )

    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"'
             ' xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for url in urls:
        english = url[3:] if url.startswith("/de/") else url
        english = "/" if english == "" else english
        if english in TRANSLATED:
            lines.append(
                "  <url><loc>%s%s</loc><lastmod>%s</lastmod><priority>%s</priority>"
                '<xhtml:link rel="alternate" hreflang="en" href="%s%s"/>'
                '<xhtml:link rel="alternate" hreflang="de" href="%s/de%s"/>'
                '<xhtml:link rel="alternate" hreflang="x-default" href="%s%s"/></url>'
                % (BASE, url, today, priority(url), BASE, english, BASE, english,
                   BASE, english))
            continue
        lines.append(
            "  <url><loc>%s%s</loc><lastmod>%s</lastmod><priority>%s</priority></url>"
            % (BASE, url, today, priority(url)))
    lines.append("</urlset>")

    (ROOT / "sitemap.xml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote sitemap.xml with %d URLs" % len(urls))


if __name__ == "__main__":
    main()
