#!/usr/bin/env python3
"""
Generate /publication/<id>/index.html for every entry in data/publications.json.

Why: the previous Jekyll site exposed per-paper URLs like
/publication/2024-10-01-C78. Those URLs are cited in papers, indexed by search
engines and linked from Scholar, so they must keep working after the relaunch.

Usage:
    python3 tools/build_publication_pages.py

Re-run after every edit to data/publications.json. Idempotent: it deletes and
rebuilds the whole /publication/ directory.
"""

import json
import pathlib
import re
import shutil
import html
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "publications.json"
OUT = ROOT / "publication"

TYPE_LABEL = {
    "journal": "Journal article",
    "conference": "Conference paper",
    "chapter": "Book chapter",
    "book": "Book / edited volume",
    "standard": "Standardization contribution",
    "position": "Position paper",
}
TYPE_BADGE = {
    "journal": ("JOURNAL", "venue"),
    "conference": ("CONFERENCE", "venue"),
    "chapter": ("CHAPTER", "venue t-book"),
    "book": ("BOOK", "venue t-book"),
    "standard": ("STANDARD", "venue t-standard"),
    "position": ("POSITION PAPER", "venue t-position"),
}
TOPIC_LABEL = {
    "xr": ("XR & Spatial Interaction", "xr-spatial-interaction"),
    "qoe": ("Quality of Experience", "qoe"),
    "psychophysiology": ("Psychophysiology & Behavioural Measurement", "psychophysiology"),
    "digital-health": ("Digital Health & Learning", "digital-health-learning"),
}
BIBTEX_TYPE = {
    "journal": "article",
    "conference": "inproceedings",
    "chapter": "incollection",
    "book": "book",
    "standard": "techreport",
    "position": "techreport",
}

NAV = """<nav>
  <div class="nav-in">
    <a href="/" class="brand">voigt-antons<span>.de</span></a>
    <div class="nav-links">
      <a href="/research/">Research</a>
      <a href="/projects/">Projects</a>
      <a href="/publications/" aria-current="page">Publications</a>
      <a href="/cv/">CV</a>
      <a href="/blog/">Blog</a>
    </div>
    <div class="nav-tools">
      <button class="icon-btn" id="navToggle" aria-label="Menu" aria-expanded="false">&#9776;</button>
      <button class="icon-btn" id="themeToggle" aria-label="Switch to dark theme">&#9686;</button>
    </div>
  </div>
  <div class="mobile-menu" id="mobileMenu">
    <a href="/research/">Research</a>
    <a href="/projects/">Projects</a>
    <a href="/publications/">Publications</a>
    <a href="/cv/">CV</a>
    <a href="/blog/">Blog</a>
    <a href="/#contact">Contact</a>
  </div>
</nav>"""

FOOTER = """<footer>
  <div class="wrap">
    <div class="foot-grid">
      <div>
        <div class="brand" style="font-size:14px;margin-bottom:6px">Prof. Dr.-Ing. Jan-Niklas Voigt-Antons</div>
        <div class="foot-col">Professor of Computer Science (Immersive Media)<br>Hamm-Lippstadt University of Applied Sciences</div>
        <div class="ids">
          <a class="id-chip" href="https://scholar.google.de/citations?user=IFIaOZsAAAAJ">Google Scholar</a>
          <a class="id-chip" href="https://orcid.org/0000-0002-2786-9262">ORCID</a>
          <a class="id-chip" href="https://dblp.org/pid/39/10762">DBLP</a>
          <a class="id-chip" href="https://dl.acm.org/profile/99659317387">ACM DL</a>
        </div>
      </div>
      <div class="foot-col">
        <div class="fh">Elsewhere</div>
        <a href="https://immersive-reality-lab.de">Immersive Reality Lab &#8599;</a><br>
        <a href="/teaching/">Teaching</a> &middot; <a href="/cv/">CV</a> &middot; <a href="/blog/">Blog</a><br>
        <a class="inline-link" href="mailto:jan-niklas@voigt-antons.de">jan-niklas@voigt-antons.de</a>
      </div>
    </div>
    <div class="copy">&copy; 2026 &middot; <a href="/impressum/">Legal Notice</a> &middot; <a href="/impressum/#privacy">Privacy</a></div>
  </div>
</footer>"""


_AUTHOR_SPLIT = re.compile(r",\s+(?=[A-ZÀ-ÖØ-Þ][a-zà-öø-ÿ'’])")


def split_authors(s):
    """Split 'Kaeder, J., Vergari, M. & Möller, S.' into surname-first names.

    Authors are written as 'Surname, Initials', so a plain split on ', ' would
    also cut between surname and initials. We therefore only split at a comma
    that is followed by a capital letter plus a lowercase letter — i.e. the
    start of the next surname, never an initial such as 'J.'.
    """
    s = s.replace(" & ", ", ").replace("…", "").strip().strip(",")
    parts = [a.strip() for a in _AUTHOR_SPLIT.split(s) if a.strip()]
    out = []
    for a in parts:
        a = re.sub(r"\s*\((?:Eds?\.|Hrsg\.)\)\s*$", "", a)
        a = re.sub(r"\s+et\s+al\.?\s*$", "", a).strip().strip(",")
        if a and a.lower() not in ("et al.", "et al"):
            out.append(a)
    return out


def bibtex(p):
    key = "voigtantons" + str(p["y"]) + p["id"].split("-")[-1].lower()
    authors = " and ".join(split_authors(p["a"])) + (
        " and others" if "et al" in p["a"] else "")
    lines = [
        "@%s{%s," % (BIBTEX_TYPE.get(p["t"], "misc"), key),
        "  author    = {%s}," % authors,
        "  title     = {%s}," % p["ti"],
        "  year      = {%s}," % p["y"],
    ]
    field = "journal" if p["t"] == "journal" else "booktitle"
    lines.append("  %-9s = {%s}," % (field, p["v"]))
    d = p.get("d", "")
    if d.startswith("https://doi.org/"):
        lines.append("  doi       = {%s}," % d[len("https://doi.org/"):])
    elif d:
        lines.append("  url       = {%s}," % d)
    lines.append("}")
    return "\n".join(lines)


def trunc(s, n=60):
    return s[:n] + ("…" if len(s) > n else "")


def page(p, prev_item, next_item):
    e = html.escape
    label, badge_cls = TYPE_BADGE.get(p["t"], ("OTHER", "venue"))
    topic_name, topic_anchor = TOPIC_LABEL.get(p.get("tp", ""), ("", ""))

    links = []
    if p.get("d"):
        links.append('<a class="btn btn-1" href="%s" rel="noopener">DOI / paper &#8599;</a>' % e(p["d"]))
    links.append('<a class="btn btn-2" href="#bibtex">BibTeX &#8595;</a>')
    links.append('<a class="btn btn-2" href="/publications/">All publications</a>')

    meta_rows = []
    if p.get("ref"):
        meta_rows.append(("Reference", "<code>[%s]</code> in the Publikationsverzeichnis"
                          % e(p["ref"])))
    meta_rows += [("Type", e(TYPE_LABEL.get(p["t"], "Other"))), ("Year", e(str(p["y"])))]
    if topic_name:
        meta_rows.append(("Research line", '<a class="inline-link" href="/research/#%s">%s</a>'
                          % (topic_anchor, e(topic_name))))
    if p.get("n"):
        meta_rows.append(("Note", "<strong>%s</strong>" % e(p["n"])))
    meta_rows.append(("Identifier", "<code>%s</code>" % e(p["id"])))

    nav_prev = ('<a class="more" href="/publication/%s">&#8592; %s</a>'
                % (e(prev_item["id"]), e(trunc(prev_item["ti"])))) if prev_item else "<span></span>"
    nav_next = ('<a class="more" href="/publication/%s">%s &#8594;</a>'
                % (e(next_item["id"]), e(trunc(next_item["ti"])))) if next_item else "<span></span>"

    schema = {
        "@context": "https://schema.org",
        "@type": "ScholarlyArticle",
        "headline": p["ti"],
        "datePublished": str(p["y"]),
        "author": [{"@type": "Person", "name": n} for n in split_authors(p["a"])],
        "isPartOf": p["v"],
    }
    if p.get("d"):
        schema["url"] = p["d"]

    return """<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} &mdash; Jan-Niklas Voigt-Antons</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="https://voigt-antons.de/publication/{pid}">
<meta property="og:type" content="article">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:image" content="https://voigt-antons.de/images/og-card.png">
<link rel="stylesheet" href="/assets/style.css">
<script type="application/ld+json">{schema}</script>
</head>
<body>
<div class="bgfx"></div>
<a class="skip" href="#main">Skip to content</a>
{nav}
<main id="main">
<header class="page-head">
  <div class="wrap">
    <div class="crumbs"><a href="/">Home</a> / <a href="/publications/">Publications</a> / {year}</div>
    <span class="{badge_cls}" style="display:inline-block;margin-bottom:16px">{badge}</span>{refbadge}
    <h1 style="font-size:clamp(1.5rem,3.4vw,2.3rem);max-width:34ch">{title}</h1>
    <p class="lede" style="font-size:1rem">{authors}</p>
    <p class="lede" style="font-size:.95rem;font-style:italic;margin-top:6px">{venue}</p>
    <div class="cta">{links}</div>
  </div>
</header>

<section>
  <div class="wrap" style="max-width:820px;margin-left:0">
    <div class="tr-item rv">
      <h3>Record</h3>
      <ul>{meta}</ul>
    </div>

    <div class="cv-block rv" id="bibtex" style="margin-top:36px">
      <h2>BibTeX</h2>
      <div class="table-scroll" style="padding:18px 20px">
<pre style="font-family:var(--mono);font-size:12.5px;line-height:1.7;color:var(--fg-2);white-space:pre-wrap;margin:0">{bib}</pre>
      </div>
    </div>

    <div style="display:flex;justify-content:space-between;gap:20px;margin-top:40px;padding-top:24px;border-top:1px solid var(--line);flex-wrap:wrap">
      {prev}
      {next}
    </div>
  </div>
</section>
</main>
{footer}
<script src="/assets/main.js" defer></script>
</body>
</html>
""".format(
        title=e(p["ti"]),
        desc=e((p["a"][:80] + " — " + p["v"])[:180]),
        pid=e(p["id"]),
        year=e(str(p["y"])),
        badge=label,
        badge_cls=badge_cls,
        refbadge=('<span class="refnum" style="margin-left:8px">[%s]</span>' % e(p["ref"])
                  if p.get("ref") else ""),
        authors=e(p["a"]),
        venue=e(p["v"]),
        links="".join(links),
        meta="".join("<li><b>%s</b><span>%s</span></li>" % r for r in meta_rows),
        bib=e(bibtex(p)),
        schema=json.dumps(schema, ensure_ascii=False),
        nav=NAV,
        footer=FOOTER,
        prev=nav_prev,
        next=nav_next,
    )


def main():
    if not DATA.exists():
        sys.exit("missing %s" % DATA)
    items = json.loads(DATA.read_text(encoding="utf-8"))["items"]
    items.sort(key=lambda x: x["id"], reverse=True)

    OUT.mkdir(parents=True, exist_ok=True)

    # Drop pages whose entry no longer exists in the JSON (best effort: some
    # filesystems disallow unlink from this process).
    keep = {p["id"] for p in items}

    # Redirect stubs for renamed ids also live under /publication/ and must
    # survive this cleanup — otherwise every run would delete them again.
    redirects = ROOT / "data" / "redirects.json"
    if redirects.exists():
        for entry in json.loads(redirects.read_text(encoding="utf-8")):
            src = entry["from"].strip("/")
            if src.startswith("publication/"):
                keep.add(src.split("/", 1)[1])
    for d in OUT.iterdir():
        if d.is_dir() and d.name not in keep:
            try:
                shutil.rmtree(d)
            except OSError as err:
                print("warning: could not remove stale %s (%s)" % (d.name, err))

    for i, p in enumerate(items):
        d = OUT / p["id"]
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(
            page(p, items[i - 1] if i > 0 else None,
                 items[i + 1] if i + 1 < len(items) else None),
            encoding="utf-8")

    print("generated %d publication pages in %s" % (len(items), OUT))


if __name__ == "__main__":
    main()
