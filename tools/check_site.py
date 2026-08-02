#!/usr/bin/env python3
"""
Static checks for the site. Runs in CI and locally; no dependencies.

Checks:
  1. Every HTML file has balanced tags.
  2. Every same-page anchor (href="#x") has a matching id.
  3. Every root-relative link resolves to a file or a directory index.
  4. Every inline JSON-LD block parses.
  5. data/*.json parse, and publication ids are unique.
  6. Generated output is in sync with its sources (no uncommitted drift).

Usage:
    python3 tools/check_site.py
Exit code 1 if anything fails.
"""

import html.parser
import json
import os
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SKIP_DIRS = {".git", ".github", ".idea", ".devcontainer", "node_modules", ".claude"}

# Assets the site links to but that are binary//external to this checker.
ALLOW_MISSING = {"/files/cv.pdf", "/images/profile.png", "/images/og-card.png"}

problems = []


class Balance(html.parser.HTMLParser):
    VOID = {"meta", "link", "br", "img", "input", "hr", "source", "col", "area",
            "base", "embed", "param", "track", "wbr"}

    def __init__(self):
        super().__init__()
        self.stack = []
        self.errors = []

    def handle_starttag(self, tag, attrs):
        if tag not in self.VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if not self.stack:
            self.errors.append("stray </%s>" % tag)
        elif self.stack[-1] == tag:
            self.stack.pop()
        else:
            self.errors.append("expected </%s>, got </%s>" % (self.stack[-1], tag))


def html_files():
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            if name.endswith(".html"):
                yield pathlib.Path(dirpath) / name


def resolves(url):
    target = ROOT / url.lstrip("/")
    if url == "/":
        return (ROOT / "index.html").exists()
    return target.exists() or (target / "index.html").exists()


def main():
    pages = sorted(html_files())
    if not pages:
        problems.append("no HTML files found — wrong working directory?")

    for page in pages:
        rel = page.relative_to(ROOT)
        text = page.read_text(encoding="utf-8")

        parser = Balance()
        parser.feed(text)
        if parser.stack:
            problems.append("%s: unclosed tags %s" % (rel, parser.stack))
        for err in parser.errors:
            problems.append("%s: %s" % (rel, err))

        ids = set(re.findall(r'id="([^"]+)"', text))
        for frag in set(re.findall(r'href="#([^"]+)"', text)):
            if frag not in ids:
                problems.append("%s: anchor #%s has no target" % (rel, frag))

        for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>',
                                text, re.S):
            try:
                json.loads(block)
            except ValueError as err:
                problems.append("%s: invalid JSON-LD (%s)" % (rel, err))

        for url in set(re.findall(r'(?:href|src)="(/[^"#?\']*)', text)):
            if url in ALLOW_MISSING:
                continue
            if not resolves(url):
                problems.append("%s: dead link %s" % (rel, url))

    pubs_path = ROOT / "data" / "publications.json"
    try:
        items = json.loads(pubs_path.read_text(encoding="utf-8"))["items"]
    except (ValueError, KeyError, OSError) as err:
        problems.append("data/publications.json: %s" % err)
        items = []

    # A DOI identifies exactly one work. Two entries sharing one is almost
    # always a copy-paste slip in the source bibliography.
    by_doi = {}
    for item in items:
        doi = item.get("d", "")
        if doi.startswith("https://doi.org/"):
            by_doi.setdefault(doi, []).append(item["id"])
    for doi, ids in by_doi.items():
        if len(ids) > 1:
            problems.append("publications.json: %s is used by %s" % (doi, ", ".join(ids)))

    # The reference number from the Publikationsverzeichnis identifies one
    # publication. Two entries claiming the same one means the import drifted.
    by_ref = {}
    for item in items:
        if item.get("ref"):
            by_ref.setdefault(item["ref"], []).append(item["id"])
    for ref, ids in by_ref.items():
        if len(ids) > 1:
            problems.append("publications.json: reference [%s] is claimed by %s"
                            % (ref, ", ".join(ids)))

    # Each series (J, C, OC, …) has to run 1..n without gaps; a gap means an
    # entry was dropped or the numbering drifted from the Word document.
    series = {}
    for item in items:
        ref = item.get("ref", "")
        prefix = "".join(c for c in ref if c.isalpha())
        number = ref[len(prefix):]
        if prefix and number.isdigit():
            series.setdefault(prefix, []).append(int(number))
    for prefix, numbers in sorted(series.items()):
        gaps = sorted(set(range(1, max(numbers) + 1)) - set(numbers))
        if gaps:
            problems.append("publications.json: series %s has gaps at %s"
                            % (prefix, ", ".join("%s%d" % (prefix, g) for g in gaps[:10])))

    seen = set()
    for item in items:
        for key in ("id", "y", "t", "ti", "a", "v", "tp"):
            if key not in item:
                problems.append("publications.json: %s missing '%s'"
                                % (item.get("id", "?"), key))
        if item.get("id") in seen:
            problems.append("publications.json: duplicate id %s" % item["id"])
        seen.add(item.get("id"))
        if item.get("id") and not (ROOT / "publication" / item["id"] / "index.html").exists():
            problems.append("publications.json: %s has no generated page — "
                            "run tools/build_publication_pages.py" % item["id"])

    try:
        posts = json.loads((ROOT / "data" / "posts.json").read_text(encoding="utf-8"))["posts"]
    except (ValueError, KeyError, OSError) as err:
        problems.append("data/posts.json: %s" % err)
        posts = []

    for post in posts:
        if not resolves(post["url"]):
            problems.append("posts.json: %s has no generated page — "
                            "run tools/build_posts.py" % post["url"])

    sources = len(list((ROOT / "content" / "posts").glob("*.md")))
    if sources != len(posts):
        problems.append("posts.json lists %d posts but content/posts has %d markdown files — "
                        "run tools/build_posts.py" % (len(posts), sources))

    print("checked %d HTML pages, %d publications, %d posts"
          % (len(pages), len(items), len(posts)))

    if problems:
        print("\n%d problem(s):" % len(problems))
        for p in problems:
            print("  - %s" % p)
        return 1
    print("all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
