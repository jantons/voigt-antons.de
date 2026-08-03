#!/usr/bin/env python3
"""
Build files/cv.pdf — the download behind the most prominent button on the site.

Nothing in this script is typed twice. The prose sections are parsed out of
cv/index.html, and the figures come from data/publications.json and
data/projects.json. Change the CV page and the PDF follows on the next run;
there is no second copy of the text to forget about.

That matters more than it sounds. The application sent in July 2026 stated a
role breakdown adding up to 20 projects while the total said 19, and was
€304k short — because those numbers were retyped by hand. A CV handed to a
committee that contradicts the website it links to is the same failure with a
worse audience.

Selected publications are chosen by a stated rule, not by taste: every
publication carrying an award or a note, then the most recent journal
articles, up to a cap. The rule is printed in the document, and the complete
list of 234 stays on the website.

Requires reportlab (pip install reportlab). Not part of the CI build — the CV
is a deliverable, regenerated when its sources move.

The German edition is not a second document: it is parsed out of de/cv/index.html,
which tools/build_i18n.py already generates. One CV page to maintain, two PDFs.

Usage:
    python3 tools/build_cv_pdf.py              # files/cv.pdf
    python3 tools/build_cv_pdf.py --lang de    # files/cv-de.pdf
"""

import argparse
import datetime
import hashlib
import html
import json
import pathlib
import re
import sys

try:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_JUSTIFY
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import (BaseDocTemplate, Frame, PageTemplate,
                                    Paragraph, Spacer, Table, TableStyle,
                                    KeepTogether)
except ImportError:
    sys.exit("this script needs reportlab:  pip install reportlab")

# Without this, reportlab stamps every file with the current time and a random
# document id, so two runs over unchanged data produce different bytes — and
# the workflow would commit four changed binaries on every single push.
from reportlab import rl_config  # noqa: E402
rl_config.invariant = 1

ROOT = pathlib.Path(__file__).resolve().parent.parent

# Per language: the page it is parsed from, the file it writes, its stamp.
EDITIONS = {
    "en": dict(page="cv/index.html", out="files/cv.pdf",
               stamp="files/cv.build.json"),
    "de": dict(page="de/cv/index.html", out="files/cv-de.pdf",
               stamp="files/cv-de.build.json"),
}

# Chrome that belongs to the document rather than to the page. Everything else
# — headings, entries, section order — comes from the parsed page, so the German
# edition inherits every translation without a second copy of the content.
T = {
    "en": dict(
        title="Curriculum Vitae — Jan-Niklas Voigt-Antons",
        role="Professor of Computer Science (Immersive Media) &nbsp;·&nbsp; "
             "Hamm-Lippstadt University of Applied Sciences<br/>"
             "Director, Immersive Reality Lab &nbsp;·&nbsp; "
             "Guest Researcher, Technische Universität Berlin",
        place="Hamm · Lippstadt · Berlin, Germany",
        lead="I study how virtual and augmented reality systems can be built so they "
             "actually work for people. My work pairs EEG, eye tracking and physiological "
             "sensing with XR deployments in hospitals, public space and safety-critical "
             "training — measuring what questionnaires cannot capture.",
        figures=("third-party funding", "publications", "citations, h-index %d",
                 "co-developer"),
        selected="SELECTED PUBLICATIONS",
        rule="Chosen by a fixed rule rather than by preference: every publication carrying "
             "an award, then the most recent journal articles. The complete list of %d — "
             "with filters by year, type and topic — is at voigt-antons.de/publications/.",
        columns=("Period", "Project", "Funder", "Role", "Volume"),
        projects="%d projects",
        footer="Jan-Niklas Voigt-Antons · curriculum vitae · generated %s from voigt-antons.de",
    ),
    "de": dict(
        title="Lebenslauf — Jan-Niklas Voigt-Antons",
        role="Professor für Informatik (Immersive Medien) &nbsp;·&nbsp; "
             "Hochschule Hamm-Lippstadt<br/>"
             "Leiter des Immersive Reality Lab &nbsp;·&nbsp; "
             "Gastwissenschaftler, Technische Universität Berlin",
        place="Hamm · Lippstadt · Berlin",
        lead="Ich erforsche, wie sich Virtual- und Augmented-Reality-Systeme so bauen "
             "lassen, dass sie für Menschen wirklich funktionieren. Dafür verbinde ich EEG, "
             "Eye-Tracking und physiologische Messung mit XR-Einsätzen in Kliniken, im "
             "öffentlichen Raum und in sicherheitskritischer Ausbildung — und erfasse, was "
             "Fragebögen nicht abbilden.",
        figures=("Drittmittel", "Publikationen", "Zitationen, h-Index %d", "Mitautor"),
        selected="AUSGEWÄHLTE PUBLIKATIONEN",
        rule="Nach einer festen Regel ausgewählt, nicht nach Geschmack: zuerst alle "
             "ausgezeichneten Arbeiten, dann die neuesten Zeitschriftenaufsätze. Die "
             "vollständige Liste aller %d — mit Filtern nach Jahr, Typ und Thema — steht "
             "auf voigt-antons.de/publications/.",
        columns=("Laufzeit", "Vorhaben", "Geldgeber", "Rolle", "Volumen"),
        projects="%d Vorhaben",
        footer="Jan-Niklas Voigt-Antons · Lebenslauf · erzeugt am %s aus voigt-antons.de",
    ),
}

ROLE_KEYS = ("Sole applicant", "Consortium coordinator", "Subproject lead", "Co-applicant")

ACCENT = colors.HexColor("#5645f5")
FG = colors.HexColor("#0b0d13")
FG2 = colors.HexColor("#3f4654")
FG3 = colors.HexColor("#7b8391")
LINE = colors.HexColor("#dfe2e9")

MAX_SELECTED = 14

FONTS = {
    "sans": "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    "sans-bold": "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
    "sans-italic": "/usr/share/fonts/truetype/liberation2/LiberationSans-Italic.ttf",
    "mono": "/usr/share/fonts/truetype/liberation2/LiberationMono-Regular.ttf",
    "mono-bold": "/usr/share/fonts/truetype/liberation2/LiberationMono-Bold.ttf",
}
FALLBACK = {
    "sans": "Helvetica", "sans-bold": "Helvetica-Bold",
    "sans-italic": "Helvetica-Oblique", "mono": "Courier", "mono-bold": "Courier-Bold",
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
        # Without this, <b> and <i> in a Paragraph silently render as regular
        # text: reportlab maps the tags through the family, not the font name.
        pdfmetrics.registerFontFamily("sans", normal="sans", bold="sans-bold",
                                      italic="sans-italic", boldItalic="sans-bold")
    return names


F = register_fonts()


# --------------------------------------------------------------------------
# Reading the sources
# --------------------------------------------------------------------------

def strip(fragment):
    """HTML fragment → reportlab markup. Keeps bold, italic and links."""
    t = fragment
    t = re.sub(r"<a[^>]*href=\"(https?://[^\"]+)\"[^>]*>(.*?)</a>",
               lambda m: '<link href="%s" color="#5645f5">%s</link>'
               % (m.group(1), m.group(2)), t, flags=re.S)
    t = re.sub(r"</?(strong|b)>", lambda m: "<b>" if "/" not in m.group(0) else "</b>", t)
    t = re.sub(r"</?(em|i)>", lambda m: "<i>" if "/" not in m.group(0) else "</i>", t)
    t = re.sub(r"<br\s*/?>", "<br/>", t)
    t = re.sub(r"<(?!/?(b|i|br|link|super|sub)\b)[^>]*>", "", t)
    return " ".join(t.split())


def cv_sections(page_path):
    """Parse the CV page into [(heading, [(label, text), ...]), ...]."""
    page = (ROOT / page_path).read_text(encoding="utf-8")
    page = re.sub(r"<nav>.*?</nav>|<footer>.*?</footer>|<script.*?</script>",
                  "", page, flags=re.S)

    sections = []
    for m in re.finditer(r"<h2>(.*?)</h2>(.*?)(?=<h2>|\Z)", page, re.S):
        heading = html.unescape(strip(m.group(1)))
        if heading in ("External profiles", "Externe Profile",
                       "CV sections", "Abschnitte"):
            continue
        entries = []
        for chunk in re.finditer(r"<h3[^>]*>(.*?)</h3>|<li[^>]*>(.*?)</li>",
                                 m.group(2), re.S):
            if chunk.group(1) is not None:
                entries.append(("__sub__", strip(chunk.group(1))))
                continue
            item = chunk.group(2)
            label = re.match(r"\s*<b>(.*?)</b>\s*<span>(.*)</span>\s*$", item, re.S)
            if label:
                entries.append((strip(label.group(1)), strip(label.group(2))))
            else:
                entries.append(("", strip(item)))
        if entries:
            sections.append((heading, entries))
    return sections


def num(value, lang, decimals=0):
    """German writes 4,609 for the decimal and 2.987 for the thousand."""
    text = ("%%.%df" % decimals) % value if decimals else format(int(value), ",")
    if decimals:
        text = format(round(value, decimals), ",.%df" % decimals)
    if lang == "de":
        text = text.replace(",", "\x00").replace(".", ",").replace("\x00", ".")
    return text


def data_figures():
    pubs = json.loads((ROOT / "data" / "publications.json").read_text(encoding="utf-8"))
    proj = json.loads((ROOT / "data" / "projects.json").read_text(encoding="utf-8"))
    bib = pubs["meta"]["bibliometrics"]
    total = sum(p["volume"] for p in proj["projects"])
    led = sum(p["volume"] for p in proj["projects"]
              if p["role"] in proj["meta"]["self_led_roles"])
    return pubs, proj, dict(
        funding=total / 1000.0, led=led / 1000.0,
        projects=len(proj["projects"]), publications=len(pubs["items"]),
        citations=bib["citations"], h=bib["h_index"],
        i10=bib["i10_index"], as_of=bib["as_of"],
    )


def role_labels(lang):
    """Reuse data/i18n.json rather than translating the same four words twice."""
    if lang == "en":
        return {k: k for k in ROLE_KEYS}
    table = json.loads((ROOT / "data" / "i18n.json").read_text(encoding="utf-8"))["de"]
    return {k: table.get(k, k) for k in ROLE_KEYS}


def selected(pubs):
    """Award-carrying work first, then the newest journal articles."""
    items = pubs["items"]
    picked, seen = [], set()
    for item in sorted((i for i in items if i.get("n")),
                       key=lambda i: -i["y"]):
        if item["n"] in ("In press", "Edited volume", "Shared first authorship"):
            continue
        picked.append(item)
        seen.add(item["id"])
    for item in sorted((i for i in items if i["t"] == "journal"),
                       key=lambda i: -i["y"]):
        if len(picked) >= MAX_SELECTED:
            break
        if item["id"] not in seen:
            picked.append(item)
            seen.add(item["id"])
    return sorted(picked[:MAX_SELECTED], key=lambda i: (-i["y"], i.get("ref", "")))


# --------------------------------------------------------------------------
# Layout
# --------------------------------------------------------------------------

S = dict(
    h1=ParagraphStyle("h1", fontName=F["sans-bold"], fontSize=22, leading=25,
                      textColor=FG, spaceAfter=2),
    role=ParagraphStyle("role", fontName=F["sans"], fontSize=10.5, leading=14,
                        textColor=FG2),
    contact=ParagraphStyle("contact", fontName=F["mono"], fontSize=8, leading=12,
                           textColor=FG3),
    h2=ParagraphStyle("h2", fontName=F["mono-bold"], fontSize=8, leading=11,
                      textColor=ACCENT, spaceBefore=11, spaceAfter=5,
                      tracking=1),
    h3=ParagraphStyle("h3", fontName=F["sans-bold"], fontSize=8.6, leading=11,
                      textColor=FG2, spaceBefore=6, spaceAfter=3),
    body=ParagraphStyle("body", fontName=F["sans"], fontSize=8.9, leading=12.4,
                        textColor=FG, alignment=TA_JUSTIFY),
    cell=ParagraphStyle("cell", fontName=F["sans"], fontSize=8.9, leading=12.4,
                        textColor=FG),
    label=ParagraphStyle("label", fontName=F["mono"], fontSize=8, leading=12.4,
                         textColor=FG3),
    lead=ParagraphStyle("lead", fontName=F["sans"], fontSize=9.4, leading=13.6,
                        textColor=FG2, alignment=TA_JUSTIFY),
    pub=ParagraphStyle("pub", fontName=F["sans"], fontSize=8.4, leading=11.6,
                       textColor=FG, spaceAfter=4, leftIndent=13,
                       firstLineIndent=-13),
    note=ParagraphStyle("note", fontName=F["mono"], fontSize=7.2, leading=10,
                        textColor=FG3, spaceBefore=3),
)

PAGE_W, PAGE_H = A4
MARGIN = 17 * mm


def entry_table(entries, width):
    """Two columns: mono label on the left, prose on the right."""
    rows, styles = [], [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 1.6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.6),
    ]
    for label, text in entries:
        if label == "__sub__":
            styles.append(("SPAN", (0, len(rows)), (-1, len(rows))))
            rows.append([Paragraph(text, S["h3"]), ""])
        elif label:
            rows.append([Paragraph(label, S["label"]), Paragraph(text, S["cell"])])
        else:
            styles.append(("SPAN", (0, len(rows)), (-1, len(rows))))
            rows.append([Paragraph(text, S["body"]), ""])
    t = Table(rows, colWidths=[26 * mm, width - 26 * mm])
    t.setStyle(TableStyle(styles))
    return t


def funding_table(proj, width, lang):
    tr = T[lang]
    rows = [[Paragraph("<b>%s</b>" % c, S["label"]) for c in tr["columns"]]]
    roles = proj["meta"]["roles"]
    labels = role_labels(lang)
    for p in sorted(proj["projects"], key=lambda p: (-p["from"], -p["to"], p["name"])):
        period = (str(p["from"]) if p["from"] == p["to"]
                  else "%d–%d" % (p["from"], p["to"]))
        rows.append([
            Paragraph(period, S["label"]),
            Paragraph(html.escape(p["short"]), S["cell"]),
            Paragraph(html.escape(p["funder"].split("(")[0].strip()), S["cell"]),
            Paragraph(html.escape(labels[roles[p["role"]].split(" — ")[0]]), S["cell"]),
            Paragraph("%s T€" % num(p["volume"], lang) if lang == "de"
                      else "€%sk" % format(p["volume"], ","), S["label"]),
        ])
    total = sum(p["volume"] for p in proj["projects"])
    rows.append([Paragraph("", S["label"]),
                 Paragraph("<b>%s</b>" % (tr["projects"] % len(proj["projects"])), S["cell"]),
                 Paragraph("", S["cell"]), Paragraph("", S["cell"]),
                 Paragraph("<b>%s</b>" % ("%s T€" % num(total, lang) if lang == "de"
                                          else "€%sk" % format(total, ",")), S["label"])])

    t = Table(rows, colWidths=[17 * mm, 47 * mm, 43 * mm, 33 * mm,
                               width - 140 * mm], repeatRows=1)
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 2.4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.4),
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, LINE),
        ("LINEABOVE", (0, -1), (-1, -1), 0.6, LINE),
        ("ALIGN", (4, 0), (4, -1), "RIGHT"),
    ]))
    return t


def header_footer(canvas, doc, lang):
    canvas.saveState()
    canvas.setFillColor(ACCENT)
    canvas.rect(0, 0, 3.2 * mm, PAGE_H, stroke=0, fill=1)
    canvas.setFont(F["mono"], 7)
    canvas.setFillColor(FG3)
    stamp = (datetime.date.today().strftime("%d.%m.%Y") if lang == "de"
             else datetime.date.today().isoformat())
    canvas.drawString(MARGIN, 11 * mm, T[lang]["footer"] % stamp)
    canvas.drawRightString(PAGE_W - MARGIN, 11 * mm, "%d" % doc.page)
    canvas.restoreState()


def build(lang):
    tr = T[lang]
    edition = EDITIONS[lang]
    out = ROOT / edition["out"]
    pubs, proj, fig = data_figures()
    width = PAGE_W - 2 * MARGIN

    out.parent.mkdir(parents=True, exist_ok=True)
    doc = BaseDocTemplate(str(out), pagesize=A4,
                          leftMargin=MARGIN, rightMargin=MARGIN,
                          topMargin=15 * mm, bottomMargin=18 * mm,
                          title=tr["title"], author="Jan-Niklas Voigt-Antons",
                          subject=tr["title"], lang=lang)
    frame = Frame(MARGIN, 18 * mm, width, PAGE_H - 33 * mm, id="body",
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc.addPageTemplates([PageTemplate(id="page", frames=[frame],
                                       onPage=lambda c, d: header_footer(c, d, lang))])

    story = [
        Paragraph("Prof. Dr.-Ing. Jan-Niklas Voigt-Antons", S["h1"]),
        Paragraph(tr["role"], S["role"]),
        Spacer(1, 5),
        Paragraph("jan-niklas@voigt-antons.de &nbsp;·&nbsp; voigt-antons.de "
                  "&nbsp;·&nbsp; ORCID 0000-0002-2786-9262 &nbsp;·&nbsp; %s"
                  % tr["place"], S["contact"]),
        Spacer(1, 9),
    ]

    money = ("%s Mio. €" % num(fig["funding"], lang, 3) if lang == "de"
             else "€%s M" % num(fig["funding"], lang, 3))
    figures = [
        (money, tr["figures"][0]),
        (num(fig["publications"], lang), tr["figures"][1]),
        (num(fig["citations"], lang), tr["figures"][2] % fig["h"]),
        ("ITU-T P.812", tr["figures"][3]),
    ]
    cells = [[Paragraph("<b>%s</b>" % v, ParagraphStyle(
        "k", fontName=F["mono-bold"], fontSize=11, leading=14, textColor=FG))
        for v, _ in figures],
        [Paragraph(k, S["label"]) for _, k in figures]]
    strip_t = Table(cells, colWidths=[width / 4.0] * 4)
    strip_t.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ("LINEABOVE", (0, 0), (-1, 0), 0.6, LINE),
        ("LINEBELOW", (0, -1), (-1, -1), 0.6, LINE),
        ("TOPPADDING", (0, 0), (-1, 0), 6), ("BOTTOMPADDING", (0, -1), (-1, -1), 6),
    ]))
    story += [strip_t, Spacer(1, 10)]

    story.append(Paragraph(tr["lead"], S["lead"]))

    for heading, entries in cv_sections(edition["page"]):
        story.append(Paragraph(heading.upper(), S["h2"]))
        story.append(entry_table(entries, width))
        if heading in ("Third-party funding", "Drittmittel"):
            story += [Spacer(1, 5), funding_table(proj, width, lang)]

    story.append(Paragraph(tr["selected"], S["h2"]))
    story.append(Paragraph(tr["rule"] % fig["publications"], S["body"]))
    story.append(Spacer(1, 5))
    for item in selected(pubs):
        note = (" <i>— %s</i>" % html.escape(item["n"])) if item.get("n") else ""
        story.append(Paragraph(
            "[%s] %s (%d). <b>%s</b>. %s.%s"
            % (html.escape(item.get("ref", "")), html.escape(item["a"]), item["y"],
               html.escape(item["ti"]), html.escape(item.get("v", "")), note),
            S["pub"]))


    doc.build(story)
    return fig, out


def sources(lang):
    return (EDITIONS[lang]["page"], "data/publications.json", "data/projects.json",
            "data/i18n.json", "tools/build_cv_pdf.py")


def fingerprint(lang):
    h = hashlib.sha256()
    for name in sources(lang):
        h.update(name.encode())
        h.update((ROOT / name).read_bytes())
    return h.hexdigest()[:16]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--lang", choices=sorted(EDITIONS), default="en")
    ap.add_argument("--all", action="store_true", help="build every edition")
    args = ap.parse_args()

    for lang in (sorted(EDITIONS) if args.all else [args.lang]):
        fig, out = build(lang)
        stamp = ROOT / EDITIONS[lang]["stamp"]
        stamp.write_text(json.dumps({
            "note": "Fingerprint of the files %s was generated from. "
                    "tools/check_site.py compares it against the current sources and "
                    "reports a stale CV. Regenerate with tools/build_cv_pdf.py --all."
                    % EDITIONS[lang]["out"],
            "lang": lang,
            "sources": list(sources(lang)),
            "fingerprint": fingerprint(lang),
            "built": datetime.date.today().isoformat(),
        }, indent=1) + "\n", encoding="utf-8")

        print("wrote %s (%.0f KB, %s)"
              % (out.relative_to(ROOT), out.stat().st_size / 1024.0, lang))
        print("   %s Mio. € · %d %s · %s %s · h-index %d"
              % (num(fig["funding"], lang, 3), fig["publications"],
                 T[lang]["figures"][1], num(fig["citations"], lang),
                 T[lang]["figures"][2].split(",")[0], fig["h"]))
        print("   prose parsed from %s — edit the page, not this script"
              % EDITIONS[lang]["page"])


if __name__ == "__main__":
    main()
