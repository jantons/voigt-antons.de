#!/usr/bin/env python3
"""
Build the two record documents an appointment committee asks for:

    files/publications.pdf   the complete list of 234, by category
    files/funding.pdf        all 22 funded projects with roles and volumes

Both are generated from data/publications.json and data/projects.json, so they
cannot state anything the website does not. That is the whole point: the
application sent in July 2026 listed a role breakdown summing to 20 projects
against a stated total of 19, and the project table fell €304k short of its own
summary — PflegeTab appeared in the totals but not in the table. Numbers that
are typed twice drift; numbers that are counted do not.

Categories follow the reference prefixes, which is also how the peer-reviewed
line is drawn: J and C are the peer-reviewed works, OJ and OC the further
contributions. The site used to blur that; these documents do not.

Deliberately neutral: no reference number of any advertised post, no private
address, no telephone number. These are documents to link to, not a dossier.

Requires reportlab. Run with --all to build both languages of both documents.

Usage:
    python3 tools/build_record_pdfs.py --all
"""

import argparse
import datetime
import hashlib
import html
import json
import pathlib
import sys

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import (BaseDocTemplate, Frame, PageTemplate,
                                    Paragraph, Spacer, Table, TableStyle)
except ImportError:
    sys.exit("this script needs reportlab:  pip install reportlab")

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGE_W, PAGE_H = A4
MARGIN = 17 * mm

ACCENT = colors.HexColor("#5645f5")
FG = colors.HexColor("#0b0d13")
FG2 = colors.HexColor("#3f4654")
FG3 = colors.HexColor("#7b8391")
LINE = colors.HexColor("#dfe2e9")

FONTS = {
    "sans": "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    "sans-bold": "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
    "sans-italic": "/usr/share/fonts/truetype/liberation2/LiberationSans-Italic.ttf",
    "mono": "/usr/share/fonts/truetype/liberation2/LiberationMono-Regular.ttf",
    "mono-bold": "/usr/share/fonts/truetype/liberation2/LiberationMono-Bold.ttf",
}
FALLBACK = {"sans": "Helvetica", "sans-bold": "Helvetica-Bold",
            "sans-italic": "Helvetica-Oblique", "mono": "Courier",
            "mono-bold": "Courier-Bold"}

# Reference prefix → (english heading, german heading). Order is the order the
# document uses; peer-reviewed work comes before the further contributions.
CATEGORIES = [
    ("B", "Monographs and edited volumes", "Monografien und Sammelbände"),
    ("BC", "Book chapters", "Buchkapitel"),
    ("J", "Peer-reviewed journal articles", "Begutachtete Zeitschriftenaufsätze"),
    ("C", "Peer-reviewed conference papers", "Begutachtete Konferenzbeiträge"),
    ("OJ", "Further journal contributions", "Weitere Zeitschriftenbeiträge"),
    ("OC", "Further conference contributions", "Weitere Konferenzbeiträge"),
    ("S", "Contributions to international standardization",
     "Beiträge zur internationalen Normung"),
    ("P", "Position papers", "Positionspapiere"),
]

T = {
    "en": dict(
        pub_title="List of publications — Jan-Niklas Voigt-Antons",
        pub_head="List of publications",
        pub_lead="All %d publications, grouped by category and ordered by year. Generated from "
                 "the same file that feeds voigt-antons.de/publications/, where the list can be "
                 "filtered by year, type and topic.",
        bib="Google Scholar, %s: %s citations · h-index %d · i10-index %d. Of these %s "
            "citations · h-index %d since 2021.",
        fund_title="Record of third-party funding — Jan-Niklas Voigt-Antons",
        fund_head="Record of third-party funding",
        fund_lead="All %d funded projects with period, funder, role and awarded volume. "
                  "Amounts are the awarded volumes of the subprojects applied for and managed "
                  "personally.",
        by_role="By role", total="Total", of_which="Of which applied for and led independently",
        columns=("Period", "Project", "Funder", "Partners", "Role", "Volume"),
        others="Further project involvement without own funding volume",
        footer="Jan-Niklas Voigt-Antons · %s · generated %s from voigt-antons.de",
        colophon="Generated from data/publications.json and data/projects.json — the files that "
                 "also feed the website, so the two cannot disagree.",
    ),
    "de": dict(
        pub_title="Publikationsverzeichnis — Jan-Niklas Voigt-Antons",
        pub_head="Publikationsverzeichnis",
        pub_lead="Alle %d Publikationen, nach Kategorien gruppiert und nach Jahr sortiert. "
                 "Erzeugt aus derselben Datei, die voigt-antons.de/publications/ speist — dort "
                 "lässt sich die Liste nach Jahr, Typ und Thema filtern.",
        bib="Google Scholar, %s: %s Zitationen · h-Index %d · i10-Index %d. Davon %s "
            "Zitationen · h-Index %d seit 2021.",
        fund_title="Verzeichnis der Drittmittelprojekte — Jan-Niklas Voigt-Antons",
        fund_head="Verzeichnis der Drittmittelprojekte",
        fund_lead="Alle %d geförderten Vorhaben mit Laufzeit, Geldgeber, Rolle und bewilligtem "
                  "Volumen. Die Beträge sind die bewilligten Volumina der selbst beantragten und "
                  "verantworteten Teilvorhaben.",
        by_role="Nach Rolle", total="Gesamt",
        of_which="Davon selbst beantragt und eigenverantwortlich geleitet",
        columns=("Laufzeit", "Vorhaben", "Geldgeber", "Partner", "Rolle", "Volumen"),
        others="Weitere Projektbeteiligungen ohne eigenes Fördervolumen",
        footer="Jan-Niklas Voigt-Antons · %s · erzeugt am %s aus voigt-antons.de",
        colophon="Erzeugt aus data/publications.json und data/projects.json — denselben Dateien, "
                 "die auch die Website speisen; beide können sich daher nicht widersprechen.",
    ),
}

EDITIONS = {
    ("publications", "en"): "files/publications.pdf",
    ("publications", "de"): "files/publications-de.pdf",
    ("funding", "en"): "files/funding.pdf",
    ("funding", "de"): "files/funding-de.pdf",
}


def register_fonts():
    names = {}
    for key, path in FONTS.items():
        if pathlib.Path(path).exists():
            pdfmetrics.registerFont(TTFont(key, path))
            names[key] = key
        else:
            names[key] = FALLBACK[key]
    if names["sans"] == "sans":
        pdfmetrics.registerFontFamily("sans", normal="sans", bold="sans-bold",
                                      italic="sans-italic", boldItalic="sans-bold")
    return names


F = register_fonts()

S = dict(
    h1=ParagraphStyle("h1", fontName=F["sans-bold"], fontSize=20, leading=23, textColor=FG),
    lead=ParagraphStyle("lead", fontName=F["sans"], fontSize=9, leading=12.6, textColor=FG2),
    h2=ParagraphStyle("h2", fontName=F["mono-bold"], fontSize=8, leading=11,
                      textColor=ACCENT, spaceBefore=13, spaceAfter=5),
    entry=ParagraphStyle("entry", fontName=F["sans"], fontSize=8.2, leading=11.2,
                         textColor=FG, spaceAfter=3.4, leftIndent=15, firstLineIndent=-15),
    cell=ParagraphStyle("cell", fontName=F["sans"], fontSize=8.2, leading=11, textColor=FG),
    label=ParagraphStyle("label", fontName=F["mono"], fontSize=7.6, leading=11, textColor=FG3),
    note=ParagraphStyle("note", fontName=F["mono"], fontSize=7, leading=9.6,
                        textColor=FG3, spaceBefore=8),
)


def num(value, lang, decimals=0):
    text = format(round(value, decimals), ",.%df" % decimals) if decimals \
        else format(int(value), ",")
    if lang == "de":
        text = text.replace(",", "\x00").replace(".", ",").replace("\x00", ".")
    return text


def money(value, lang):
    return "%s T€" % num(value, lang) if lang == "de" else "€%sk" % format(value, ",")


def frame_doc(out, title, lang, kind):
    doc = BaseDocTemplate(str(out), pagesize=A4, leftMargin=MARGIN, rightMargin=MARGIN,
                          topMargin=15 * mm, bottomMargin=18 * mm,
                          title=title, author="Jan-Niklas Voigt-Antons", subject=title,
                          lang=lang)

    def chrome(canvas, d):
        canvas.saveState()
        canvas.setFillColor(ACCENT)
        canvas.rect(0, 0, 3.2 * mm, PAGE_H, stroke=0, fill=1)
        canvas.setFont(F["mono"], 7)
        canvas.setFillColor(FG3)
        stamp = (datetime.date.today().strftime("%d.%m.%Y") if lang == "de"
                 else datetime.date.today().isoformat())
        canvas.drawString(MARGIN, 11 * mm, T[lang]["footer"] % (kind, stamp))
        canvas.drawRightString(PAGE_W - MARGIN, 11 * mm, "%d" % d.page)
        canvas.restoreState()

    frame = Frame(MARGIN, 18 * mm, PAGE_W - 2 * MARGIN, PAGE_H - 33 * mm, id="body",
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc.addPageTemplates([PageTemplate(id="p", frames=[frame], onPage=chrome)])
    return doc


def build_publications(lang):
    tr = T[lang]
    data = json.loads((ROOT / "data" / "publications.json").read_text(encoding="utf-8"))
    items, bib = data["items"], data["meta"]["bibliometrics"]
    out = ROOT / EDITIONS[("publications", lang)]
    out.parent.mkdir(parents=True, exist_ok=True)

    story = [Paragraph(tr["pub_head"], S["h1"]), Spacer(1, 5),
             Paragraph(tr["pub_lead"] % len(items), S["lead"]), Spacer(1, 3)]
    recent = bib.get("since_2021", {})
    story.append(Paragraph(tr["bib"] % (bib["as_of"], num(bib["citations"], lang),
                                        bib["h_index"], bib["i10_index"],
                                        num(recent.get("citations", 0), lang),
                                        recent.get("h_index", 0)), S["lead"]))

    written = 0
    for prefix, en, de in CATEGORIES:
        group = [i for i in items
                 if "".join(c for c in i.get("ref", "") if c.isalpha()) == prefix]
        if not group:
            continue
        heading = (de if lang == "de" else en).upper()
        story.append(Paragraph("%s (%d)" % (heading, len(group)), S["h2"]))
        for item in sorted(group, key=lambda i: (-i["y"], i.get("ref", ""))):
            note = (" <i>— %s</i>" % html.escape(item["n"])) if item.get("n") else ""
            doi = (' <font color="#5645f5">%s</font>' % html.escape(item["d"])) \
                if item.get("d") else ""
            story.append(Paragraph(
                "[%s] %s (%d). <b>%s</b>. %s.%s%s"
                % (html.escape(item.get("ref", "")), html.escape(item["a"]), item["y"],
                   html.escape(item["ti"]), html.escape(item.get("v", "")), note, doi),
                S["entry"]))
            written += 1

    story.append(Paragraph(tr["colophon"], S["note"]))
    frame_doc(out, tr["pub_title"], lang, tr["pub_head"]).build(story)
    return out, written


def build_funding(lang):
    tr = T[lang]
    data = json.loads((ROOT / "data" / "projects.json").read_text(encoding="utf-8"))
    projects, meta = data["projects"], data["meta"]
    roles = meta["roles"]
    labels = roles
    if lang == "de":
        table = json.loads((ROOT / "data" / "i18n.json").read_text(encoding="utf-8"))["de"]
        labels = {k: table.get(v.split(" — ")[0], v.split(" — ")[0]) for k, v in roles.items()}
    else:
        labels = {k: v.split(" — ")[0] for k, v in roles.items()}

    out = ROOT / EDITIONS[("funding", lang)]
    out.parent.mkdir(parents=True, exist_ok=True)
    width = PAGE_W - 2 * MARGIN

    total = sum(p["volume"] for p in projects)
    led = [p for p in projects if p["role"] in meta["self_led_roles"]]

    story = [Paragraph(tr["fund_head"], S["h1"]), Spacer(1, 5),
             Paragraph(tr["fund_lead"] % len(projects), S["lead"]), Spacer(1, 8)]

    rows = [[Paragraph("<b>%s</b>" % tr["by_role"], S["label"]),
             Paragraph("", S["label"]), Paragraph("", S["label"])]]
    for key, label in labels.items():
        group = [p for p in projects if p["role"] == key]
        if not group:
            continue
        rows.append([Paragraph(html.escape(label), S["cell"]),
                     Paragraph("%d" % len(group), S["label"]),
                     Paragraph(money(sum(p["volume"] for p in group), lang), S["label"])])
    rows.append([Paragraph("<b>%s</b>" % tr["total"], S["cell"]),
                 Paragraph("<b>%d</b>" % len(projects), S["label"]),
                 Paragraph("<b>%s</b>" % money(total, lang), S["label"])])
    rows.append([Paragraph(tr["of_which"], S["cell"]),
                 Paragraph("%d" % len(led), S["label"]),
                 Paragraph(money(sum(p["volume"] for p in led), lang), S["label"])])
    summary = Table(rows, colWidths=[width - 42 * mm, 14 * mm, 28 * mm])
    summary.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 2.6), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.6),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, LINE),
        ("LINEABOVE", (0, -2), (-1, -2), 0.6, LINE),
    ]))
    story += [summary, Spacer(1, 12)]

    body = [[Paragraph("<b>%s</b>" % c, S["label"]) for c in tr["columns"]]]
    for p in sorted(projects, key=lambda p: (-p["from"], -p["to"], p["name"])):
        period = (str(p["from"]) if p["from"] == p["to"]
                  else "%d–%d" % (p["from"], p["to"]))
        body.append([
            Paragraph(period, S["label"]),
            Paragraph("<b>%s</b><br/>%s" % (html.escape(p["short"]),
                                            html.escape(p["name"])), S["cell"]),
            Paragraph(html.escape(p["funder"]), S["cell"]),
            Paragraph(html.escape(p.get("partners", "") or "—"), S["cell"]),
            Paragraph(html.escape(labels[p["role"]]), S["cell"]),
            Paragraph(money(p["volume"], lang), S["label"]),
        ])
    body.append([Paragraph("", S["label"]),
                 Paragraph("<b>%d</b>" % len(projects), S["cell"]),
                 Paragraph("", S["cell"]), Paragraph("", S["cell"]),
                 Paragraph("", S["cell"]),
                 Paragraph("<b>%s</b>" % money(total, lang), S["label"])])

    # "Verbundkoordinator" is 18 characters; a 25 mm role column broke it across
    # two lines. Partners can wrap, a role label should not.
    table = Table(body, colWidths=[16 * mm, 44 * mm, 32 * mm,
                                   width - 141 * mm, 31 * mm, 18 * mm], repeatRows=1)
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, LINE),
        ("LINEABOVE", (0, -1), (-1, -1), 0.6, LINE),
        ("ALIGN", (5, 0), (5, -1), "RIGHT"),
    ]))
    story.append(table)

    extra = data.get("without_own_volume", [])
    if extra:
        story.append(Paragraph(tr["others"].upper(), S["h2"]))
        for o in extra:
            story.append(Paragraph(
                "<b>%s</b> — %s (%d–%d, %s, %s)"
                % (html.escape(o["short"]), html.escape(o["name"]), o["from"], o["to"],
                   html.escape(o["funder"]), html.escape(o["role_label"])), S["entry"]))

    story.append(Paragraph(tr["colophon"], S["note"]))
    frame_doc(out, tr["fund_title"], lang, tr["fund_head"]).build(story)
    return out, len(projects)


SOURCES = ("data/publications.json", "data/projects.json", "data/i18n.json",
           "tools/build_record_pdfs.py")

# The download page is generated too, so a new document cannot be forgotten
# there — the listing is built from the files that actually exist.
DOWNLOADS = ROOT / "downloads" / "index.html"

CARDS = [
    ("files/cv.pdf", "files/cv-de.pdf", "Curriculum vitae",
     "Appointments, education, awards, bibliometrics, standardization, funding, supervision "
     "and academic service, with a selection of publications."),
    ("files/publications.pdf", "files/publications-de.pdf", "List of publications",
     "All %(publications)d publications by category: peer-reviewed journal articles and "
     "conference papers, further contributions, standardization, position papers."),
    ("files/funding.pdf", "files/funding-de.pdf", "Record of third-party funding",
     "All %(projects)d funded projects with period, funder, partners, role and awarded "
     "volume, and the totals by role."),
]


def write_downloads():
    """List the documents that exist, with their real size and page count."""
    import re

    pubs = json.loads((ROOT / "data" / "publications.json").read_text(encoding="utf-8"))
    proj = json.loads((ROOT / "data" / "projects.json").read_text(encoding="utf-8"))
    counts = {"publications": len(pubs["items"]), "projects": len(proj["projects"])}

    def pages(path):
        """Page count from the page tree, not by counting /Type /Page.

        Counting page objects overshoots — the CV came out as five pages when
        it has four. /Type /Pages carries an authoritative /Count.
        """
        try:
            blob = path.read_bytes()
        except OSError:
            return 0
        counts = [int(n) for n in re.findall(rb"/Type\s*/Pages\b[^>]*?/Count\s+(\d+)", blob)]
        counts += [int(n) for n in re.findall(rb"/Count\s+(\d+)[^>]*?/Type\s*/Pages\b", blob)]
        return max(counts) if counts else 0

    cards = []
    for en_path, de_path, title, blurb in CARDS:
        en, de = ROOT / en_path, ROOT / de_path
        if not en.exists():
            continue
        cards.append(
            '      <article class="card rv">\n'
            '        <h3>%s</h3>\n'
            '        <p>%s</p>\n'
            '        <div class="pub-links" style="margin-top:14px">\n'
            '          <a href="/%s">English (PDF, %d pages, %.0f&nbsp;KB) &darr;</a>\n'
            '          <a href="/%s" hreflang="de">Deutsch (PDF, %d Seiten, %.0f&nbsp;KB) &darr;</a>\n'
            '        </div>\n'
            '      </article>'
            % (title, blurb % counts, en_path, pages(en), en.stat().st_size / 1024.0,
               de_path, pages(de), de.stat().st_size / 1024.0))

    block = ("<!-- BEGIN downloads -->\n    <div class=\"cards\">\n%s\n    </div>\n"
             "<!-- END downloads -->" % "\n".join(cards))
    text = DOWNLOADS.read_text(encoding="utf-8")
    begin, end = "<!-- BEGIN downloads -->", "<!-- END downloads -->"
    text = text[:text.index(begin)] + block + text[text.index(end) + len(end):]
    DOWNLOADS.write_text(text, encoding="utf-8")
    return len(cards)


def fingerprint():
    h = hashlib.sha256()
    for name in SOURCES:
        h.update(name.encode())
        h.update((ROOT / name).read_bytes())
    return h.hexdigest()[:16]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--lang", choices=("en", "de"), default="en")
    args = ap.parse_args()

    langs = ("de", "en") if args.all else (args.lang,)
    for lang in langs:
        out, n = build_publications(lang)
        print("wrote %s (%d entries, %.0f KB)"
              % (out.relative_to(ROOT), n, out.stat().st_size / 1024.0))
        out, n = build_funding(lang)
        print("wrote %s (%d projects, %.0f KB)"
              % (out.relative_to(ROOT), n, out.stat().st_size / 1024.0))

    if args.all:
        print("listed %d documents on /downloads/" % write_downloads())

    stamp = ROOT / "files" / "records.build.json"
    stamp.write_text(json.dumps({
        "note": "Fingerprint of the files the record PDFs were generated from. "
                "tools/check_site.py reports them as stale when the sources move. "
                "Rebuild with tools/build_record_pdfs.py --all.",
        "sources": list(SOURCES),
        "outputs": sorted(EDITIONS.values()),
        "fingerprint": fingerprint(),
        "built": datetime.date.today().isoformat(),
    }, indent=1) + "\n", encoding="utf-8")
    print("stamped files/records.build.json")


if __name__ == "__main__":
    main()
