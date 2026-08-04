#!/usr/bin/env python3
"""
Render invited talks, keynotes and public appearances into the CV.

The site said this, once, under "Reviewing & programme committees": "Invited
talks at industry events, universities and international venues." No venue, no
year, no title — and filed under reviewing, which is not what a talk is. It was
the weakest line on the site measured against what actually happens.

What the record shows, once written down, is more specific and more useful than
a count: a medical society, a care consortium, a network of public authorities,
a city lab, and a UK government foresight programme. Five audiences, none of
them computer science, each asking the same question — does this system work
for the people using it. That is the argument; the list is the evidence.

Two blocks, because two different things:

    invited talks and keynotes   somebody else asked him to come
    visits and public visibility a minister came to see the lab, and his own
                                 project's launch — real, but not invitations,
                                 and a CV that files them as such invites the
                                 question

Sources: data/talks.json.
Target:  cv/index.html between <!-- BEGIN talks --> / <!-- END talks -->

line() is imported by tools/build_i18n.py so that the German rendering comes
from the same function as the English one. Two copies of this shape would drift
apart on the first entry that has no city.

Usage:
    python3 tools/build_talks.py
Run before build_i18n.py, which derives the German page from this one.
"""

import html
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "talks.json"
PAGE = ROOT / "cv" / "index.html"

BEGIN, END = "<!-- BEGIN talks -->", "<!-- END talks -->"

# Which block an entry belongs in. Anything not an invitation goes second.
INVITED = ("keynote", "invited", "panel", "tutorial")

KIND = {
    "keynote": {"en": "Keynote", "de": "Keynote"},
    "invited": {"en": "Invited talk", "de": "Eingeladener Vortrag"},
    "panel": {"en": "Panel", "de": "Podium"},
    "tutorial": {"en": "Tutorial", "de": "Tutorial"},
    "visit": {"en": "Presentation to a visiting delegation",
              "de": "Vorstellung vor einer Delegation"},
    "own-event": {"en": "Project launch event", "de": "Projektauftakt"},
}

COUNTRY = {"DE": {"en": "Germany", "de": "Deutschland"},
           "UK": {"en": "United Kingdom", "de": "Vereinigtes Königreich"}}

ONLINE = {"en": "online", "de": "online"}

HEAD = {
    "title": {"en": "Invited talks &amp; keynotes",
              "de": "Eingeladene Vorträge &amp; Keynotes"},
    "invited": {"en": "Keynotes and invited talks",
                "de": "Keynotes und eingeladene Vorträge"},
    "other": {"en": "Visits and public visibility",
              "de": "Besuche und öffentliche Sichtbarkeit"},
}


def place(talk, lang):
    """Where it happened, in the reader's language."""
    if talk.get("city") == "online":
        return ONLINE[lang]
    bits = [talk["city"]] if talk.get("city") else []
    country = COUNTRY.get(talk.get("country"), {}).get(lang)
    if country:
        bits.append(country)
    return ", ".join(bits)


def line(talk, lang):
    """One entry, as the CV renders it.

    The title stays in the language it was given in — a talk is called what it
    was called — and the English page adds a gloss after it, the same rule the
    site follows for German degree grades and programme names.
    """
    e = html.escape
    kind = KIND[talk["kind"]][lang]
    if talk.get("scope") == "workshop" and talk["kind"] == "keynote":
        kind = {"en": "Workshop keynote", "de": "Keynote des Workshops"}[lang]

    title = "<em>%s</em>" % e(talk["title"])
    gloss = talk.get("title_en")
    if lang == "en" and gloss and gloss != talk["title"]:
        title += " (%s)" % e(gloss)

    tail = ", ".join(x for x in (e(talk["event"]), place(talk, lang)) if x)
    year = str(talk["date"])[:4]
    return ('          <li><b>%s</b><span><strong>%s</strong> — %s. %s.</span></li>'
            % (year, e(kind), title, tail))


def lead(talks, lang):
    """A sentence that counts what is below it, in words, from the list."""
    n_key = sum(1 for t in talks if t["kind"] == "keynote")
    n_inv = sum(1 for t in talks if t["kind"] == "invited")
    since = min(str(t["date"])[:4] for t in talks)
    audiences = {
        "en": "medicine, care, public administration, policy and the general public",
        "de": "Medizin, Pflege, Verwaltung, Politik und Öffentlichkeit",
    }[lang]
    return {
        "en": ("%d keynotes and %d invited talks since %s, to audiences in %s — "
               "the applications this work is for, rather than the field it comes from."
               % (n_key, n_inv, since, audiences)),
        "de": ("%d Keynotes und %d eingeladene Vorträge seit %s, vor Publikum aus %s — "
               "den Anwendungsfeldern dieser Arbeit, nicht dem Fach, aus dem sie kommt."
               % (n_key, n_inv, since, audiences)),
    }[lang]


H3 = ('<h3 style="font-family:var(--mono);font-size:11px;letter-spacing:.09em;'
      'text-transform:uppercase;color:var(--accent-2);margin:%s 0 12px">%s</h3>')


def build(data, lang="en"):
    talks = sorted(data["talks"], key=lambda t: str(t["date"]), reverse=True)
    invited = [t for t in talks if t["kind"] in INVITED]
    other = [t for t in talks if t["kind"] not in INVITED]
    if not invited:
        sys.exit("no invited talks in data/talks.json — remove the block from "
                 "cv/index.html rather than shipping an empty heading")

    parts = ['%s\n        <div class="cv-block rv" id="talks">' % BEGIN,
             "          <h2>%s</h2>" % HEAD["title"][lang],
             '          <p class="metrics-note" style="margin-bottom:16px">%s</p>'
             % html.escape(lead(invited, lang)),
             "          " + H3 % ("4px", HEAD["invited"][lang]),
             '          <ul class="cv-list">']
    parts += [line(t, lang) for t in invited]
    parts.append("          </ul>")
    if other:
        parts.append("          " + H3 % ("24px", HEAD["other"][lang]))
        parts.append('          <ul class="cv-list">')
        parts += [line(t, lang) for t in other]
        parts.append("          </ul>")
    parts.append("        </div>\n%s" % END)
    return "\n".join(parts)


def main():
    data = json.loads(SRC.read_text(encoding="utf-8"))
    incomplete = [t["id"] for t in data["talks"] if t.get("missing")]
    if incomplete:
        sys.exit("these entries are still incomplete, so the block would state "
                 "less than it claims: %s" % ", ".join(incomplete))

    text = PAGE.read_text(encoding="utf-8")
    if BEGIN not in text or END not in text:
        sys.exit("markers %s / %s not found in %s" % (BEGIN, END, PAGE))
    new = text[:text.index(BEGIN)] + build(data) + text[text.index(END) + len(END):]
    if new != text:
        PAGE.write_text(new, encoding="utf-8")

    kinds = {}
    for t in data["talks"]:
        kinds[t["kind"]] = kinds.get(t["kind"], 0) + 1
    print("wrote %d talks into /cv/: %s"
          % (len(data["talks"]),
             ", ".join("%d %s" % (n, k) for k, n in sorted(kinds.items()))))


if __name__ == "__main__":
    main()
