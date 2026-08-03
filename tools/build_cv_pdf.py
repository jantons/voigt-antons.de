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

Usage:
    python3 tools/build_cv_pdf.py
"""

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

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "files" / "cv.pdf"
STAMP = ROOT / "files" / "cv.build.json"

# Everything the PDF is derived from. check_site.py hashes these and compares
# against the stamp, so a CV built before the data moved is caught — the one
# failure this design cannot rule out by construction.
SOURCES = ("cv/index.html", "data/publications.json", "data/projects.json",
           "tools/build_cv_pdf.py")

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


def cv_sections():
    """Parse cv/index.html into [(heading, [(label, text), ...]), ...]."""
    page = (ROOT / "cv" / "index.html").read_text(encoding="utf-8")
    page = re.sub(r"<nav>.*?</nav>|<footer>.*?</footer>|<script.*?</script>",
                  "", page, flags=re.S)

    sections = []
    for m in re.finditer(r"<h2>(.*?)</h2>(.*?)(?=<h2>|\Z)", page, re.S):
        heading = html.unescape(strip(m.group(1)))
        if heading in ("External profiles", "CV sections"):
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


def data_figures():
    pubs = json.loads((ROOT / "data" / "publications.json").read_text(encoding="utf-8"))
    proj = json.loads((ROOT / "data" / "projects.json").read_text(encoding="utf-8"))
    bib = pubs["meta"]["bibliometrics"]
    total = sum(p["volume"] for p in proj["projects"])
    led = sum(p["volume"] for p in proj["projects"]
              if p["role"] in proj["meta"]["self_led_roles"])
    return pubs, proj, dict(
        funding="%.3f" % (total / 1000.0), led="%.3f" % (led / 1000.0),
        projects=len(proj["projects"]), publications=len(pubs["items"]),
        citations=format(bib["citations"], ","), h=bib["h_index"],
        i10=bib["i10_index"], as_of=bib["as_of"],
    )


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


def funding_table(proj, width):
    rows = [[Paragraph("<b>Period</b>", S["label"]), Paragraph("<b>Project</b>", S["label"]),
             Paragraph("<b>Funder</b>", S["label"]), Paragraph("<b>Role</b>", S["label"]),
             Paragraph("<b>Volume</b>", S["label"])]]
    roles = proj["meta"]["roles"]
    for p in sorted(proj["projects"], key=lambda p: (-p["from"], -p["to"], p["name"])):
        period = (str(p["from"]) if p["from"] == p["to"]
                  else "%d–%d" % (p["from"], p["to"]))
        rows.append([
            Paragraph(period, S["label"]),
            Paragraph(html.escape(p["short"]), S["cell"]),
            Paragraph(html.escape(p["funder"].split("(")[0].strip()), S["cell"]),
            Paragraph(html.escape(roles[p["role"]].split(" — ")[0]), S["cell"]),
            Paragraph("€%sk" % format(p["volume"], ","), S["label"]),
        ])
    total = sum(p["volume"] for p in proj["projects"])
    rows.append([Paragraph("", S["label"]),
                 Paragraph("<b>%d projects</b>" % len(proj["projects"]), S["cell"]),
                 Paragraph("", S["cell"]), Paragraph("", S["cell"]),
                 Paragraph("<b>€%sk</b>" % format(total, ","), S["label"])])

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


def header_footer(canvas, doc, fig):
    canvas.saveState()
    canvas.setFillColor(ACCENT)
    canvas.rect(0, 0, 3.2 * mm, PAGE_H, stroke=0, fill=1)
    canvas.setFont(F["mono"], 7)
    canvas.setFillColor(FG3)
    canvas.drawString(MARGIN, 11 * mm,
                      "Jan-Niklas Voigt-Antons · curriculum vitae · "
                      "generated %s from voigt-antons.de" % datetime.date.today())
    canvas.drawRightString(PAGE_W - MARGIN, 11 * mm, "%d" % doc.page)
    canvas.restoreState()


def build():
    pubs, proj, fig = data_figures()
    width = PAGE_W - 2 * MARGIN

    doc = BaseDocTemplate(str(OUT), pagesize=A4,
                          leftMargin=MARGIN, rightMargin=MARGIN,
                          topMargin=15 * mm, bottomMargin=18 * mm,
                          title="Curriculum Vitae — Jan-Niklas Voigt-Antons",
                          author="Jan-Niklas Voigt-Antons",
                          subject="Academic CV")
    frame = Frame(MARGIN, 18 * mm, width, PAGE_H - 33 * mm, id="body",
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc.addPageTemplates([PageTemplate(id="page", frames=[frame],
                                       onPage=lambda c, d: header_footer(c, d, fig))])

    story = [
        Paragraph("Prof. Dr.-Ing. Jan-Niklas Voigt-Antons", S["h1"]),
        Paragraph("Professor of Computer Science (Immersive Media) &nbsp;·&nbsp; "
                  "Hamm-Lippstadt University of Applied Sciences<br/>"
                  "Director, Immersive Reality Lab &nbsp;·&nbsp; "
                  "Guest Researcher, Technische Universität Berlin", S["role"]),
        Spacer(1, 5),
        Paragraph("jan-niklas@voigt-antons.de &nbsp;·&nbsp; voigt-antons.de "
                  "&nbsp;·&nbsp; ORCID 0000-0002-2786-9262 &nbsp;·&nbsp; "
                  "Hamm · Lippstadt · Berlin, Germany", S["contact"]),
        Spacer(1, 9),
    ]

    figures = [
        ("€%s M" % fig["funding"], "third-party funding"),
        ("%d" % fig["publications"], "publications"),
        ("%s" % fig["citations"], "citations, h-index %d" % fig["h"]),
        ("ITU-T P.812", "co-developer"),
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

    story.append(Paragraph(
        "I study how virtual and augmented reality systems can be built so they actually "
        "work for people. My work pairs EEG, eye tracking and physiological sensing with XR "
        "deployments in hospitals, public space and safety-critical training — measuring what "
        "questionnaires cannot capture.", S["lead"]))

    for heading, entries in cv_sections():
        story.append(Paragraph(heading.upper(), S["h2"]))
        story.append(entry_table(entries, width))
        if heading == "Third-party funding":
            story += [Spacer(1, 5), funding_table(proj, width)]

    story.append(Paragraph("SELECTED PUBLICATIONS", S["h2"]))
    story.append(Paragraph(
        "Chosen by a fixed rule rather than by preference: every publication carrying an "
        "award, then the most recent journal articles. The complete list of %d — with "
        "filters by year, type and topic — is at voigt-antons.de/publications/."
        % fig["publications"], S["body"]))
    story.append(Spacer(1, 5))
    for item in selected(pubs):
        note = (" <i>— %s</i>" % html.escape(item["n"])) if item.get("n") else ""
        story.append(Paragraph(
            "[%s] %s (%d). <b>%s</b>. %s.%s"
            % (html.escape(item.get("ref", "")), html.escape(item["a"]), item["y"],
               html.escape(item["ti"]), html.escape(item.get("v", "")), note),
            S["pub"]))

    story.append(Paragraph(
        "Figures in this document are read from the same files that feed the website "
        "(data/publications.json, data/projects.json); the prose is parsed from "
        "voigt-antons.de/cv/. Bibliometrics: Google Scholar, %s." % fig["as_of"],
        S["note"]))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.build(story)
    return fig


def fingerprint():
    h = hashlib.sha256()
    for name in SOURCES:
        h.update(name.encode())
        h.update((ROOT / name).read_bytes())
    return h.hexdigest()[:16]


def main():
    fig = build()
    STAMP.write_text(json.dumps({
        "note": "Fingerprint of the files files/cv.pdf was generated from. "
                "tools/check_site.py compares it against the current sources and "
                "reports a stale CV. Regenerate with tools/build_cv_pdf.py.",
        "sources": list(SOURCES),
        "fingerprint": fingerprint(),
        "built": datetime.date.today().isoformat(),
        "pages_note": "figures are read from the data files, never typed",
    }, indent=1) + "\n", encoding="utf-8")
    print("wrote %s (%.0f KB)" % (OUT.relative_to(ROOT), OUT.stat().st_size / 1024.0))
    print("figures: €%s M across %d projects · %s publications · %s citations · h-index %d"
          % (fig["funding"], fig["projects"], fig["publications"], fig["citations"],
             fig["h"]))
    print("prose parsed from cv/index.html — edit the page, not this script")
    print("stamped %s" % STAMP.relative_to(ROOT))


if __name__ == "__main__":
    main()
