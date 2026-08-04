#!/usr/bin/env python3
"""
Render reusable research artefacts into /research/.

The site listed 234 publications and not one thing anyone could download. The
Storytime dataset was named in one subordinate clause of the research
statement, with no link — which is the same as not having it: a dataset nobody
can reach is a claim, not a contribution.

This is the section that serves the collaboration half of the site's purpose.
A paper earns a citation; an artefact earns an email. It is generated from
data/artifacts.json so that adding the next one is a four-line edit, and so
that tools/build_jsonld.py can emit schema.org Dataset markup from the same
source — Google indexes datasets separately, and a hand-written duplicate of
these facts would drift from the visible list within a release or two.

Sources: data/artifacts.json, data/publications.json (for the citation).
Target:  research/index.html between <!-- BEGIN artifacts --> / <!-- END artifacts -->

Usage:
    python3 tools/build_artifacts.py
Run before build_i18n.py, which derives the German page from this one.
"""

import html
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
ART = ROOT / "data" / "artifacts.json"
PUBS = ROOT / "data" / "publications.json"
PAGE = ROOT / "research" / "index.html"

BEGIN, END = "<!-- BEGIN artifacts -->", "<!-- END artifacts -->"

KIND_LABEL = {"Dataset": "Dataset", "SoftwareSourceCode": "Software",
              "CreativeWork": "Instrument"}


def citation(pub):
    """The paper to cite, exactly as the publication list states it."""
    return "%s (%s). <em>%s</em>. %s" % (
        html.escape(pub["a"]), pub["y"], html.escape(pub["ti"]),
        html.escape(pub["v"]))


def build(artifacts, by_id):
    e = html.escape
    cards = []
    for art in artifacts:
        pub = by_id.get(art.get("paper"))
        if art.get("paper") and pub is None:
            sys.exit("artifact %s cites publication %s, which is not in "
                     "data/publications.json" % (art["id"], art["paper"]))

        cite = ""
        if pub:
            doi = ('<a class="inline-link" href="%s">%s</a>'
                   % (e(pub["d"]), e(pub["d"].replace("https://doi.org/", "doi:")))
                   ) if pub.get("d") else ""
            # The label and the citation are separate elements on purpose.
            # i18n_lib keeps any fragment containing a link to /publication/
            # verbatim, so that titles and venues stay in the citable form —
            # correct for the citation, wrong for the words around it. With
            # both in one paragraph the German page read "Cite as", and the
            # generator reported full coverage because it had never offered
            # the string for translation at all.
            cite = (
                '        <h4 style="font-family:var(--mono);font-size:10.5px;'
                'letter-spacing:.09em;text-transform:uppercase;color:var(--fg-3);'
                'margin:16px 0 6px">Cite as</h4>\n'
                '        <p class="metrics-note">%s. %s '
                '<a class="inline-link" href="/publication/%s">Details</a></p>'
                % (citation(pub), doi, e(pub["id"])))

        cards.append("""      <div class="tr-item rv" id="artifact-{aid}">
        <h3>{name}</h3>
        <p class="sec-sub" style="margin-bottom:12px">{kind} · {year} · {repo}</p>
        <p>{summary}</p>
        <div class="cta" style="margin-top:14px">
          <a class="btn btn-2" href="{url}">Open on {repo} →</a>
        </div>
{cite}
      </div>""".format(
            aid=e(art["id"]), name=e(art["name"]),
            kind=KIND_LABEL.get(art["kind"], art["kind"]),
            year=art["year"], repo=e(art["repository"]),
            summary=e(art["summary"]), url=e(art["url"]), cite=cite))

    return """{begin}
<section id="artifacts">
  <div class="wrap">
    <div class="sec-head"><span class="sec-num">03</span><h2>Data and instruments</h2></div>
    <p class="sec-sub">Material from this work that other groups can download, reuse and cite.</p>
    <div class="tr">
{cards}
    </div>
  </div>
</section>
{end}""".format(begin=BEGIN, end=END, cards="\n".join(cards))


def main():
    data = json.loads(ART.read_text(encoding="utf-8"))
    by_id = {p["id"]: p for p in
             json.loads(PUBS.read_text(encoding="utf-8"))["items"]}
    artifacts = data["artifacts"]
    if not artifacts:
        sys.exit("data/artifacts.json is empty — remove the section from "
                 "research/index.html rather than shipping an empty heading")

    text = PAGE.read_text(encoding="utf-8")
    if BEGIN not in text or END not in text:
        sys.exit("markers %s / %s not found in %s" % (BEGIN, END, PAGE))
    new = text[:text.index(BEGIN)] + build(artifacts, by_id) + \
        text[text.index(END) + len(END):]
    if new != text:
        PAGE.write_text(new, encoding="utf-8")

    print("wrote %d artefact(s) into /research/: %s"
          % (len(artifacts), ", ".join(a["name"] for a in artifacts)))


if __name__ == "__main__":
    main()
