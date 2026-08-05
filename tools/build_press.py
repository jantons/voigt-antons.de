#!/usr/bin/env python3
"""
Render the press and speaking kit into /press/.

Conference organisers and journalists ask the same four things by email: a
biography of about the right length, a photograph, how the name is spelled, and
what has been written before. Answering each by hand costs a day of latency at
the exact moment somebody is deciding whether to include you in a programme.

The three biography lengths are not decoration — they are the three requests. A
programme line, a session page, a press release. The word counts shown are
counted here rather than promised, because a biography advertised as 100 words
and delivered as 140 gets cut by whoever is laying out the page, and they will
cut the half you would have kept.

Sources: data/press.json, and the portrait already on the site.
Target:  press/index.html between <!-- BEGIN press --> / <!-- END press -->

Both languages live side by side in the JSON; tools/build_i18n.py harvests the
pairs, so no sentence here is written twice.

Usage:
    python3 tools/build_press.py
Run before build_i18n.py, which derives /de/press/ from this page.
"""

import html
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "press.json"
PAGE = ROOT / "press" / "index.html"

BEGIN, END = "<!-- BEGIN press -->", "<!-- END press -->"

T = {
    "bios": {"en": "Biographies", "de": "Kurzbiografien"},
    "words": {"en": "%d words", "de": "%d Wörter"},
    "copy": {"en": "Use whichever fits. No need to ask.",
             "de": "Bitte die passende verwenden — Rückfrage nicht nötig."},
    "portrait": {"en": "Portrait", "de": "Porträt"},
    "download": {"en": "Download the portrait", "de": "Porträt herunterladen"},
    "naming": {"en": "How to write the name", "de": "Schreibweise des Namens"},
    "coverage": {"en": "Selected coverage", "de": "Ausgewählte Berichterstattung"},
    "contact": {"en": "For anything else", "de": "Für alles Weitere"},
    "contact_text": {
        "en": "Interview requests, review copies, or a question about the work — "
              "email is fastest, and the answer usually comes within a few days.",
        "de": "Interviewanfragen, Belegexemplare oder eine Frage zur Arbeit — "
              "per E-Mail am schnellsten, Antwort meist innerhalb weniger Tage."},
}

H3 = ('<h3 style="font-family:var(--mono);font-size:11px;letter-spacing:.09em;'
      'text-transform:uppercase;color:var(--accent-2);margin:%s 0 12px">%s</h3>')


H4 = ('<h4 style="font-family:var(--mono);font-size:10.5px;letter-spacing:.09em;'
      'text-transform:uppercase;color:var(--fg-3);margin:20px 0 8px">%s</h4>')


def label(bio, lang):
    """The heading over a biography: what it is for, and how long it is."""
    return "%s · %s" % (bio["label"][lang],
                        T["words"][lang] % len(bio["text"][lang].split()))


def build(data, lang="en"):
    e = html.escape
    out = [BEGIN, H3 % ("4px", T["bios"][lang])]
    out.append('    <p class="metrics-note" style="margin-bottom:18px">%s</p>'
               % T["copy"][lang])

    # Heading and paragraph, not a box: a container carrying one of the classes
    # i18n_lib watches is itself a translation unit, and so is the paragraph
    # inside it. The paragraph then gets translated twice — once as itself, once
    # as part of its parent — and the second pass reports the German sentence as
    # an untranslated English one. Two plain elements have one meaning each.
    for bio in data["bios"]:
        text = bio["text"][lang]
        out.append("    " + H4 % (label(bio, lang)))
        out.append('    <p style="margin-bottom:20px">%s</p>' % e(text))

    portrait = data["portrait"]
    out.append(H3 % ("30px", T["portrait"][lang]))
    out.append("    <p>%s</p>" % e(portrait["note"][lang]))
    if portrait.get("credit"):
        out.append("    <p><b>%s</b></p>" % e(portrait["credit"]))
    out.append('    <div class="cta" style="margin-top:12px">'
               '<a class="btn btn-2" href="%s" download>%s &darr;</a></div>'
               % (portrait["file"], T["download"][lang]))

    naming = data["naming"]
    out.append(H3 % ("30px", T["naming"][lang]))
    out.append('    <ul class="cv-plain">')
    out.append("      <li><strong>%s</strong></li>" % e(naming["full"]))
    out.append("      <li>%s</li>" % e(naming["role"][lang]))
    out.append("      <li>%s</li>" % e(naming["note"][lang]))
    out.append("    </ul>")

    # The coverage list is only rendered once there is something in it. An
    # empty "Selected coverage" heading answers the question badly.
    if data.get("coverage"):
        out.append(H3 % ("30px", T["coverage"][lang]))
        out.append('    <ul class="cv-list stack">')
        for item in data["coverage"]:
            title = e(item["title"])
            if item.get("url"):
                title = '<a class="inline-link" href="%s">%s</a>' % (e(item["url"]), title)
            out.append("      <li><b>%s</b><span>%s — %s</span></li>"
                       % (e(str(item["date"])[:4]), e(item["outlet"]), title))
        out.append("    </ul>")

    out.append(H3 % ("30px", T["contact"][lang]))
    out.append("    <p>%s</p>" % T["contact_text"][lang])
    out.append('    <p style="margin-top:10px"><a class="inline-link" '
               'href="mailto:jan-niklas@voigt-antons.de">'
               'jan-niklas@voigt-antons.de</a></p>')
    out.append(END)
    return "\n".join(out)


def main():
    data = json.loads(SRC.read_text(encoding="utf-8"))
    if not data.get("bios"):
        sys.exit("data/press.json holds no biography — the page has nothing to say")

    text = PAGE.read_text(encoding="utf-8")
    if BEGIN not in text or END not in text:
        sys.exit("markers %s / %s not found in %s" % (BEGIN, END, PAGE))
    new = text[:text.index(BEGIN)] + build(data) + text[text.index(END) + len(END):]
    if new != text:
        PAGE.write_text(new, encoding="utf-8")

    lengths = ", ".join("%s %d" % (b["id"], len(b["text"]["en"].split()))
                        for b in data["bios"])
    print("wrote /press/: biographies of %s words, %d item(s) of coverage"
          % (lengths, len(data.get("coverage", []))))


if __name__ == "__main__":
    main()
