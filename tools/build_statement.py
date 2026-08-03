#!/usr/bin/env python3
"""
Render the research and teaching statement — as a page and as a PDF.

Source: data/statement.json, which holds both languages side by side.

It began as the statement written for one advertised chair and is stripped of
everything that belonged to that post: no institution, no reference number, no
named neighbouring professorships or local institutes. What is left is the part
that is true wherever it is read — three research lines with what has been done
and what comes next, a teaching approach, a funding strategy and how
infrastructure and supervision are run.

That generalisation is the point of publishing it at all. A dossier written for
one committee tells the next one that you applied elsewhere; a statement of how
you work is an invitation.

Writes:
    research/statement/index.html   English page (German via build_i18n.py)
    files/statement.pdf             English PDF
    files/statement-de.pdf          German PDF

Requires reportlab for the PDFs.

Usage:
    python3 tools/build_statement.py
"""

import datetime
import hashlib
import html
import json
import pathlib
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
                                    Paragraph, Spacer)
except ImportError:
    sys.exit("this script needs reportlab:  pip install reportlab")

# Without this, reportlab stamps every file with the current time and a random
# document id, so two runs over unchanged data produce different bytes — and
# the workflow would commit four changed binaries on every single push.
from reportlab import rl_config  # noqa: E402
rl_config.invariant = 1

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "statement.json"
PAGE = ROOT / "research" / "statement" / "index.html"

PAGE_W, PAGE_H = A4
MARGIN = 20 * mm
ACCENT = colors.HexColor("#5645f5")
FG = colors.HexColor("#0b0d13")
FG2 = colors.HexColor("#3f4654")
FG3 = colors.HexColor("#7b8391")

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

T = {
    "en": dict(
        title="Research and teaching statement — Jan-Niklas Voigt-Antons",
        head="Research and teaching statement",
        lines="Three research lines", done="What is done", next="What comes next",
        footer="Jan-Niklas Voigt-Antons · research and teaching statement · %s · voigt-antons.de",
        note="The current version of this statement is at "
             "voigt-antons.de/research/statement/.",
        out="files/statement.pdf"),
    "de": dict(
        title="Forschungs- und Lehrkonzept — Jan-Niklas Voigt-Antons",
        head="Forschungs- und Lehrkonzept",
        lines="Drei Forschungslinien", done="Vorarbeiten", next="Geplante Vorhaben",
        footer="Jan-Niklas Voigt-Antons · Forschungs- und Lehrkonzept · %s · voigt-antons.de",
        note="Die jeweils aktuelle Fassung dieses Konzepts steht unter "
             "voigt-antons.de/research/statement/.",
        out="files/statement-de.pdf"),
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
    h1=ParagraphStyle("h1", fontName=F["sans-bold"], fontSize=19, leading=22, textColor=FG),
    h2=ParagraphStyle("h2", fontName=F["mono-bold"], fontSize=8.5, leading=11,
                      textColor=ACCENT, spaceBefore=15, spaceAfter=6),
    h3=ParagraphStyle("h3", fontName=F["sans-bold"], fontSize=11, leading=14,
                      textColor=FG, spaceBefore=9, spaceAfter=3),
    label=ParagraphStyle("label", fontName=F["mono"], fontSize=7.4, leading=10,
                         textColor=FG3, spaceBefore=5, spaceAfter=1),
    body=ParagraphStyle("body", fontName=F["sans"], fontSize=9.1, leading=13,
                        textColor=FG, alignment=TA_JUSTIFY, spaceAfter=4),
    lead=ParagraphStyle("lead", fontName=F["sans"], fontSize=10, leading=14.4,
                        textColor=FG2, alignment=TA_JUSTIFY, spaceAfter=6),
    note=ParagraphStyle("note", fontName=F["mono"], fontSize=7.2, leading=10,
                        textColor=FG3, spaceBefore=12),
)


def pdf(lang, data):
    tr = T[lang]
    out = ROOT / tr["out"]
    out.parent.mkdir(parents=True, exist_ok=True)

    doc = BaseDocTemplate(str(out), pagesize=A4, leftMargin=MARGIN, rightMargin=MARGIN,
                          topMargin=16 * mm, bottomMargin=18 * mm,
                          title=tr["title"], author="Jan-Niklas Voigt-Antons",
                          subject=tr["title"], lang=lang)

    def chrome(canvas, d):
        canvas.saveState()
        canvas.setFillColor(ACCENT)
        canvas.rect(0, 0, 3.2 * mm, PAGE_H, stroke=0, fill=1)
        canvas.setFont(F["mono"], 7)
        canvas.setFillColor(FG3)
        stamp = (datetime.date.today().strftime("%d.%m.%Y") if lang == "de"
                 else datetime.date.today().isoformat())
        canvas.drawString(MARGIN, 11 * mm, tr["footer"] % stamp)
        canvas.drawRightString(PAGE_W - MARGIN, 11 * mm, "%d" % d.page)
        canvas.restoreState()

    frame = Frame(MARGIN, 18 * mm, PAGE_W - 2 * MARGIN, PAGE_H - 34 * mm, id="b",
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc.addPageTemplates([PageTemplate(id="p", frames=[frame], onPage=chrome)])

    story = [Paragraph(tr["head"], S["h1"]), Spacer(1, 7),
             Paragraph(data["lead"][lang], S["lead"]),
             Paragraph(data["thread"][lang], S["body"])]

    story.append(Paragraph(tr["lines"].upper(), S["h2"]))
    for line in data["lines"]:
        story.append(Paragraph("%s — %s" % (line["letter"], line["title"][lang]), S["h3"]))
        story.append(Paragraph(line["question"][lang], S["body"]))
        story.append(Paragraph(tr["done"].upper(), S["label"]))
        story.append(Paragraph(line["done"][lang], S["body"]))
        story.append(Paragraph(tr["next"].upper(), S["label"]))
        story.append(Paragraph(line["next"][lang], S["body"]))

    fund = data["funding_strategy"]
    story.append(Paragraph(fund["title"][lang].upper(), S["h2"]))
    story.append(Paragraph(fund["intro"][lang], S["body"]))
    for phase in fund["phases"]:
        story.append(Paragraph(phase["span"][lang], S["label"]))
        story.append(Paragraph(phase["text"][lang], S["body"]))
    story.append(Paragraph(fund["candid"][lang], S["body"]))

    teach = data["teaching"]
    story.append(Paragraph(teach["title"][lang].upper(), S["h2"]))
    story.append(Paragraph(teach["core"][lang], S["body"]))
    for principle in teach["principles"]:
        story.append(Paragraph("— " + principle[lang], S["body"]))
    for method in teach["methods"]:
        story.append(Paragraph(method["title"][lang], S["h3"]))
        story.append(Paragraph(method["text"][lang], S["body"]))
    story.append(Paragraph(teach["supervision"][lang], S["body"]))

    infra = data["infrastructure"]
    story.append(Paragraph(infra["title"][lang].upper(), S["h2"]))
    story.append(Paragraph(infra["text"][lang], S["body"]))

    story.append(Paragraph(tr["note"], S["note"]))
    doc.build(story)
    return out


def page(data):
    """The English page. build_i18n.py derives the German one from it."""
    e = html.escape
    lines = []
    for line in data["lines"]:
        lines.append("""
    <article class="line rv" id="{id}">
      <div class="line-label">
        <span class="lnum">LINE {letter}</span>
        <h3>{title}</h3>
      </div>
      <div class="line-body">
        <p>{question}</p>
        <h4>What is done</h4>
        <p>{done}</p>
        <h4>What comes next</h4>
        <p>{next}</p>
      </div>
    </article>""".format(id=e(line["id"]), letter=line["letter"],
                         title=line["title"]["en"], question=line["question"]["en"],
                         done=line["done"]["en"], next=line["next"]["en"]))

    fund = data["funding_strategy"]
    phases = "".join(
        '<li><b>%s</b><span>%s</span></li>' % (p["span"]["en"], p["text"]["en"])
        for p in fund["phases"])

    teach = data["teaching"]
    principles = "".join("<li>%s</li>" % p["en"] for p in teach["principles"])
    methods = "".join(
        '<article class="card flat rv"><h3>%s</h3><p style="margin-bottom:0">%s</p></article>'
        % (m["title"]["en"], m["text"]["en"]) for m in teach["methods"])

    return """<!-- BEGIN statement -->
<header class="page-head">
  <div class="wrap">
    <div class="crumbs"><a href="/">Home</a> / <a href="/research/">Research</a> / Statement</div>
    <div class="eyebrow"><i class="dot"></i>Research and teaching</div>
    <h1>How I work, and what I would build next</h1>
    <p class="lede">{lead}</p>
  </div>
</header>

<section>
  <div class="wrap">
    <p class="sec-sub" style="max-width:78ch">{thread}</p>
    <div class="pub-links" style="margin-top:18px">
      <a href="/files/statement.pdf">English (PDF) &darr;</a>
      <a href="/files/statement-de.pdf" hreflang="de">Deutsch (PDF) &darr;</a>
    </div>
  </div>
</section>

<section>
  <div class="wrap">
    <div class="sec-head"><span class="sec-num">01</span><h2>Three research lines</h2></div>
{lines}
  </div>
</section>

<section>
  <div class="wrap">
    <div class="sec-head"><span class="sec-num">02</span><h2>{fund_title}</h2></div>
    <p class="sec-sub">{fund_intro}</p>
    <div class="tr">
      <div class="tr-item rv"><h3>First five years</h3><ul>{phases}</ul></div>
      <div class="tr-item rv"><h3>Where I am weaker</h3><p style="margin-bottom:0">{candid}</p></div>
    </div>
  </div>
</section>

<section>
  <div class="wrap">
    <div class="sec-head"><span class="sec-num">03</span><h2>{teach_title}</h2></div>
    <p class="sec-sub" style="max-width:78ch">{core}</p>
    <ul class="cv-plain" style="margin:16px 0 26px">{principles}</ul>
    <div class="cards">{methods}</div>
    <div class="note" style="margin-top:24px">{supervision}</div>
  </div>
</section>

<section>
  <div class="wrap">
    <div class="sec-head"><span class="sec-num">04</span><h2>{infra_title}</h2></div>
    <p class="sec-sub" style="max-width:78ch">{infra}</p>
  </div>
</section>
<!-- END statement -->""".format(
        lead=data["lead"]["en"], thread=data["thread"]["en"], lines="".join(lines),
        fund_title=fund["title"]["en"], fund_intro=fund["intro"]["en"],
        phases=phases, candid=fund["candid"]["en"],
        teach_title=teach["title"]["en"], core=teach["core"]["en"],
        principles=principles, methods=methods, supervision=teach["supervision"]["en"],
        infra_title=data["infrastructure"]["title"]["en"],
        infra=data["infrastructure"]["text"]["en"])


SOURCES = ("data/statement.json", "tools/build_statement.py")


def main():
    data = json.loads(DATA.read_text(encoding="utf-8"))

    text = PAGE.read_text(encoding="utf-8")
    begin, end = "<!-- BEGIN statement -->", "<!-- END statement -->"
    if begin not in text:
        sys.exit("markers not found in %s" % PAGE)
    PAGE.write_text(text[:text.index(begin)] + page(data)
                    + text[text.index(end) + len(end):], encoding="utf-8")

    for lang in ("en", "de"):
        out = pdf(lang, data)
        print("wrote %s (%.0f KB)" % (out.relative_to(ROOT), out.stat().st_size / 1024.0))

    digest = hashlib.sha256()
    for name in SOURCES:
        digest.update(name.encode())
        digest.update((ROOT / name).read_bytes())
    (ROOT / "files" / "statement.build.json").write_text(json.dumps({
        "note": "Fingerprint of the sources of files/statement.pdf. check_site.py reports a "
                "stale statement. Rebuild with tools/build_statement.py.",
        "sources": list(SOURCES),
        "fingerprint": digest.hexdigest()[:16],
        "built": datetime.date.today().isoformat(),
    }, indent=1) + "\n", encoding="utf-8")
    print("wrote %s and stamped files/statement.build.json" % PAGE.relative_to(ROOT))


if __name__ == "__main__":
    main()
