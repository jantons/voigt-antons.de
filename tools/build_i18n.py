#!/usr/bin/env python3
"""
Generate the German version of the core pages under /de/.

Scope is deliberate: start page, research, projects, CV and teaching. The
publication list, the 234 detail pages and the blog stay English, because paper
titles, venues and abstracts are English — a German rendering of a citation
would be wrong to copy into a bibliography.

Sources of truth:
    the English page   — structure, markup, generated blocks
    data/i18n.json     — English string → German string

Nothing is duplicated. The German page is derived from the English one on every
run, so a change to an English page cannot leave a stale German page behind:
either the sentence is translated, or the script reports it as missing and
check_site.py fails the build.

The script also maintains, on both language versions:
    * <html lang>, canonical and og:url
    * reciprocal hreflang links including x-default
    * a DE/EN switch in the navigation bar
    * links between core pages, rewritten to stay inside the language

Usage:
    python3 tools/build_i18n.py
Run it after build_projects.py, since /projects/ contains a generated block.
"""

import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from i18n_lib import translate  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "i18n.json"
SITE = "https://voigt-antons.de"

# English page  ->  URL path. The German copy lives under /de/<path>.
PAGES = {
    "index.html": "/",
    "research/index.html": "/research/",
    "projects/index.html": "/projects/",
    "cv/index.html": "/cv/",
    "teaching/index.html": "/teaching/",
}

# Paths that exist in both languages, longest first so /projects/ is matched
# before /. Everything else — /publications/, /blog/, /impressum/ — is left
# pointing at the English page, which is the only one there is.
TRANSLATED_PATHS = sorted(PAGES.values(), key=len, reverse=True)

ALT_BEGIN = "<!-- BEGIN i18n-alt -->"
ALT_END = "<!-- END i18n-alt -->"
SWITCH_RE = re.compile(r'\s*<a class="icon-btn lang-switch"[^>]*>[^<]*</a>')

NAV_LABEL = {
    "/research/": "Forschung",
    "/projects/": "Projekte",
    "/publications/": "Publikationen",
    "/cv/": "Lebenslauf",
    "/blog/": "Blog",
    "/#contact": "Kontakt",
}

# The funding table body stays English (project names, funders), but the role
# column is prose. These four labels are translated in place.
ROLE_CELLS = ("Sole applicant", "Consortium coordinator", "Subproject lead",
              "Co-applicant")


def alternates(path):
    return "\n".join([
        ALT_BEGIN,
        '<link rel="alternate" hreflang="en" href="%s%s">' % (SITE, path),
        '<link rel="alternate" hreflang="de" href="%s/de%s">' % (SITE, path),
        '<link rel="alternate" hreflang="x-default" href="%s%s">' % (SITE, path),
        ALT_END,
    ])


def set_block(text, begin, end, new, after):
    """Replace the marker block, inserting it after `after` on first run."""
    if begin in text and end in text:
        return text[:text.index(begin)] + new + text[text.index(end) + len(end):]
    m = re.search(after, text)
    if not m:
        sys.exit("cannot place the hreflang block: %r not found" % after)
    return text[:m.end()] + "\n" + new + text[m.end():]


def set_switch(text, href, label, aria, lang):
    """Put exactly one language switch into the nav tools."""
    link = ('\n      <a class="icon-btn lang-switch" href="%s" hreflang="%s" '
            'lang="%s" aria-label="%s">%s</a>' % (href, lang, lang, aria, label))
    text = SWITCH_RE.sub("", text)
    return text.replace('<div class="nav-tools">',
                        '<div class="nav-tools">' + link, 1)


def to_german_links(html):
    """Keep navigation inside the German version where a German page exists."""
    def sub(m):
        quote, path, rest = m.group(1), m.group(2), m.group(3)
        for known in TRANSLATED_PATHS:
            if path == known:
                return '%s="/de%s%s' % (quote, path, rest)
        return m.group(0)
    return re.sub(r'(href)="(/[^"#?]*)([^"]*)', sub, html)


def build_german(english, path, table, missing):
    # Drop the English page's own DE switch before translating, otherwise its
    # German aria-label would be collected as an untranslated string.
    html = translate(SWITCH_RE.sub("", english), table, missing)
    html = to_german_links(html)
    html = html.replace('<html lang="en"', '<html lang="de"', 1)

    for label in ROLE_CELLS:
        if label in table:
            html = html.replace("<td>%s</td>" % label, "<td>%s</td>" % table[label])

    html = html.replace('href="%s%s"' % (SITE, path), 'href="%s/de%s"' % (SITE, path))
    html = html.replace('content="%s%s"' % (SITE, path), 'content="%s/de%s"' % (SITE, path))

    html = set_block(html, ALT_BEGIN, ALT_END, alternates(path),
                     r'<link rel="canonical"[^>]*>')
    html = set_switch(html, path, "EN", "This page in English", "en")

    # Navigation labels are short enough to live here rather than in the table.
    for target, german in NAV_LABEL.items():
        english_label = target.strip("/#").replace("contact", "Contact").capitalize()
        html = re.sub(r'(<a href="(?:/de)?%s"[^>]*>)[^<]+(</a>)' % re.escape(target),
                      lambda m, g=german: m.group(1) + g + m.group(2), html)
    html = re.sub(r'(<a href="/de/" class="brand">)', r'\1', html)
    return html


def main():
    table = json.loads(DATA.read_text(encoding="utf-8"))["de"]
    missing = set()
    written = 0

    for page, path in PAGES.items():
        english_path = ROOT / page
        english = english_path.read_text(encoding="utf-8")

        # Keep the English page's own metadata in order, too.
        updated = set_block(english, ALT_BEGIN, ALT_END, alternates(path),
                            r'<link rel="canonical"[^>]*>')
        updated = set_switch(updated, "/de" + path, "DE", "Diese Seite auf Deutsch", "de")
        if updated != english:
            english_path.write_text(updated, encoding="utf-8")
            english = updated

        target = ROOT / "de" / page
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(build_german(english, path, table, missing), encoding="utf-8")
        written += 1

    print("wrote %d German pages under /de/" % written)
    if missing:
        print("\n%d string(s) without a translation — add them to data/i18n.json:"
              % len(missing))
        for text in sorted(missing):
            print("  %s" % (text if len(text) < 110 else text[:107] + "..."))
        return 1
    print("every translatable string is covered")
    return 0


if __name__ == "__main__":
    sys.exit(main())
