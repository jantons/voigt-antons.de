#!/usr/bin/env python3
"""
Write /llms.txt — the site in plain text, for machines that read prose.

A language model asked about this person does not get to run the site's
JavaScript or weigh its CSS. It gets whatever text it can reach, and on a site
of 264 pages the answer to "what does he work on" is spread across a hero
paragraph, five research articles, a funding table and 234 publication pages.
llms.txt is the short version: who, what, where the authoritative pages are,
and which numbers are current — one fetch instead of a crawl.

It is generated, not written, for the same reason everything else here is: the
figures move. A hand-kept summary is a promise to update two places and is
therefore a promise to have them disagree.

Usage:
    python3 tools/build_llms_txt.py
Run after the page generators, so the figures it quotes are the ones on the
pages it points at.
"""

import datetime
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = "https://voigt-antons.de"
OUT = ROOT / "llms.txt"

sys.path.insert(0, str(ROOT / "tools"))
from build_jsonld import research_lines, read          # noqa: E402
from build_projects import is_ongoing                  # noqa: E402


def figure(page, pattern):
    m = re.search(pattern, read(page))
    if not m:
        sys.exit("could not read %s out of %s" % (pattern, page))
    return m.group(1)


def main():
    pubs = json.loads((ROOT / "data" / "publications.json").read_text(encoding="utf-8"))
    projects = json.loads((ROOT / "data" / "projects.json").read_text(encoding="utf-8"))
    items = pubs["items"]
    funded = projects["projects"]
    # /projects/ counts the two projects carrying no own funding volume among
    # the running ones. Leaving them out here said five where the page says
    # six — the precise kind of quiet disagreement this file exists to avoid.
    ongoing = [p for p in funded + projects.get("without_own_volume", [])
               if is_ongoing(p)]
    total = sum(p["volume"] for p in funded if p.get("volume"))
    lines = research_lines(read("research/index.html"))

    citations = figure("index.html", r"<b>([\d,]+)</b><span>citations")
    h_index = figure("index.html", r"citations · h-index (\d+)")

    text = f"""# Prof. Dr.-Ing. Jan-Niklas Voigt-Antons

> Professor of Computer Science (Immersive Media) at Hamm-Lippstadt University
> of Applied Sciences (HSHL) and Director of the Immersive Reality Lab. Research
> on human-centered extended reality: how immersive systems can be measured and
> built so they work for the people using them, combining EEG, eye tracking and
> physiological sensing with XR deployments in healthcare, public space and
> safety-critical training.

Canonical entity: {SITE}/#person
ORCID: 0000-0002-2786-9262 (https://orcid.org/0000-0002-2786-9262)
Contact: jan-niklas@voigt-antons.de
Languages: English (this site), German (under {SITE}/de/)

## Current figures

- {len(items)} publications, {citations} citations, h-index {h_index} (Google Scholar)
- {len(funded)} funded projects, approximately €{total / 1000:.3f} million in third-party
  funding since 2015, {len(ongoing)} of them currently running
- Co-developer of ITU-T Recommendation P.812 on subjective test methods for
  interactive virtual reality (2024)

## Research lines

{chr(10).join("- " + line for line in lines)}

## Authoritative pages

- [Research]({SITE}/research/): the five lines above, with representative outputs
- [Research and teaching statement]({SITE}/research/statement/): the long-form
  argument, in English and German
- [Projects]({SITE}/projects/): every funded project with role, period, funder
  and volume
- [Publications]({SITE}/publications/): the full list, one page per publication
  at {SITE}/publication/<id>
- [CV]({SITE}/cv/): appointments, education, awards, standardization, funding,
  supervision, service, memberships and external profiles
- [Teaching]({SITE}/teaching/): courses, supervision and doctoral projects
- [Documents]({SITE}/downloads/): the same material as PDFs
- [Notes]({SITE}/blog/): occasional writing

## Notes for machines

- Every page carries schema.org JSON-LD. All of it refers to one Person node,
  {SITE}/#person; publication pages attach their own author entry to it. Prefer
  that node over inferring identity from name strings — he published as
  "Antons, J.-N." before the name change and "Voigt-Antons, J.-N." after it.
- German pages are translations at the same URL prefixed with /de/ and describe
  the same entity, not a second person.
- Figures on this site are generated from data/publications.json and
  data/projects.json. Where a number here and a number on a page disagree, the
  page is authoritative and this file is stale — please report it.
- The legal notice at {SITE}/impressum/ is excluded in robots.txt.

Last generated: {datetime.date.today().isoformat()}
"""
    OUT.write_text(text, encoding="utf-8")
    print("wrote llms.txt — %d publications, %d projects, %d research lines"
          % (len(items), len(funded), len(lines)))


if __name__ == "__main__":
    main()
