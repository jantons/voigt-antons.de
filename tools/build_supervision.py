#!/usr/bin/env python3
"""
Render doctoral supervision and international collaboration into the pages.

Both were missing from the site while sitting in the application documents —
and they are among the strongest material there is: five named doctoral
researchers with their topics and the projects funding them, four completed
procedures with titles, faculties and international examiners, nineteen
countries and eight named partner institutions.

Sources: data/supervision.json, data/network.json.
Targets:
    teaching/index.html   between <!-- BEGIN doctoral --> / <!-- END doctoral -->
    cv/index.html         between <!-- BEGIN network -->  / <!-- END network -->

The counts — five ongoing, four completed, nineteen countries — are derived
from the lists, never typed. That is the rule the rest of this repository
follows, for the reason the start page demonstrated when it advertised 226
publications against a list of 234.

Names are on the site because they are already public in every one of these
people's own publications; the topics and project links are what make the
supervision legible to a committee.

Usage:
    python3 tools/build_supervision.py
Run before build_i18n.py, which derives the German pages from these.
"""

import html
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SUP = ROOT / "data" / "supervision.json"
NET = ROOT / "data" / "network.json"

WORDS = {1: "One", 2: "Two", 3: "Three", 4: "Four", 5: "Five", 6: "Six", 7: "Seven",
         8: "Eight", 9: "Nine", 10: "Ten"}

# Project ids that have an anchor on /projects/.
PROJECT_NAMES = {}


def project_link(pid):
    name = PROJECT_NAMES.get(pid, pid)
    return '<a class="inline-link" href="/projects/#%s">%s</a>' % (html.escape(pid),
                                                                  html.escape(name))


def build_doctoral(sup):
    e = html.escape
    ongoing, completed = sup["ongoing"], sup["completed"]
    theses = sup["meta"]["theses"]

    rows = []
    for person in ongoing:
        bits = [e(person["topic"])]
        if person.get("role"):
            bits.append(e(person["role"]))
        if person.get("project"):
            bits.append("in " + project_link(person["project"]))
        since = " (since %d)" % person["since"] if person.get("since") else ""
        rows.append(
            '          <li><b>%s</b><span>%s%s — %s</span></li>'
            % (e(person["name"]), e(person["degree"]), since, " · ".join(bits)))

    done = []
    for person in completed:
        detail = ["%s, %s" % (e(person["institution"]), e(person["role"]))]
        if person.get("examiners"):
            detail.append("further examiners: " + e(person["examiners"]))
        if person.get("note"):
            detail.append(e(person["note"]))
        # Where someone went after the defence says more about supervision
        # than the title of the thesis does: a committee reading a CV wants to
        # know whether the people who finish here can carry on.
        after = (" <strong>Now:</strong> %s." % e(person["now"])
                 if person.get("now") else "")
        # "Dr.-Ing." already ends in a full stop; a template that adds one
        # unconditionally produces "Dr.-Ing..".
        awarded = e(person["awarded"])
        done.append(
            '          <li><b>%d</b><span><strong>%s</strong>, %s — <em>%s</em>. %s. %s%s%s</span></li>'
            % (person["year"], e(person["name"]), e(person["degree"]),
               e(person["title"]), " · ".join(detail), awarded,
               "" if awarded.endswith(".") else ".", after))

    further = "".join("<li>%s</li>" % e(x) for x in sup["further"])

    return """<!-- BEGIN doctoral -->
    <div class="tr">
      <div class="tr-item rv">
        <h3>Ongoing doctoral projects</h3>
        <p class="sec-sub" style="margin-bottom:14px">{n_ongoing} researchers in the Immersive
        Reality Lab, each embedded in a funded project.</p>
        <ul>
{rows}
        </ul>
        <p class="metrics-note" style="margin-top:14px">{presenting}</p>
      </div>
      <div class="tr-item rv">
        <h3>Theses</h3>
        <ul>
          <li><b>{master}</b><span>Master's theses supervised since {since}</span></li>
          <li><b>{bachelor}</b><span>Bachelor's theses supervised since {since}</span></li>
          <li><b>2024</b><span>Special Prize, Sustainability Award of Volksbank Beckum-Lippstadt, for a supervised Bachelor's thesis</span></li>
        </ul>
        <p class="metrics-note" style="margin-top:12px">{theses_note}</p>
        <h4 style="font-family:var(--mono);font-size:10.5px;letter-spacing:.09em;text-transform:uppercase;color:var(--fg-3);margin:20px 0 10px">Selected further supervision</h4>
        <ul class="cv-plain">{further}</ul>
        <div class="note" style="margin-top:22px">
          <b>Thesis topics and student positions</b> are advertised on the
          <a class="inline-link" href="https://immersive-reality-lab.de">Immersive Reality Lab site</a>,
          not here.
        </div>
      </div>
    </div>

    <h3 style="font-family:var(--mono);font-size:11px;letter-spacing:.09em;text-transform:uppercase;color:var(--accent-2);margin:30px 0 12px">Completed doctorates</h3>
    <ul class="cv-list">
{done}
    </ul>
    <p class="metrics-note" style="margin-top:12px">{note_completed} {note_alumni}</p>
<!-- END doctoral -->""".format(
        n_ongoing=WORDS.get(len(ongoing), len(ongoing)),
        rows="\n".join(rows), done="\n".join(done), further=further,
        master=theses["master"], bachelor=theses["bachelor"], since=theses["since"],
        theses_note=html.escape(theses["note"]),
        note_completed=html.escape(sup["note_completed"]),
        note_alumni=html.escape(sup.get("note_alumni", "")),
        presenting=html.escape(sup.get("note_presenting", "")))


def build_network(net):
    e = html.escape
    countries = net["countries"]
    partners = "".join(
        '          <li><b>%s</b><span>%s — %s</span></li>'
        % (e(p["institution"]), e(p["country"]), e(p["subject"]))
        for p in net["partners"])
    stay = net["research_stay"]

    return """<!-- BEGIN network -->
          <h2 id="network">International collaboration</h2>
          <ul class="cv-plain">
            <li>Joint publications, research proposals and project partnerships with partners in
            <strong>{n} countries</strong>: {countries}</li>
            <li>Research stay: {stay_inst}, {stay_country} ({stay_year}) — {stay_subject}</li>
          </ul>
          <h3 style="font-family:var(--mono);font-size:11px;letter-spacing:.09em;text-transform:uppercase;color:var(--accent-2);margin:20px 0 12px">Named partner institutions</h3>
          <ul class="cv-list stack">
{partners}
          </ul>
<!-- END network -->""".format(
        n=len(countries), countries=e(", ".join(countries)),
        stay_inst=e(stay["institution"]), stay_country=e(stay["country"]),
        stay_year=stay["year"], stay_subject=e(stay["subject"]), partners=partners)


def replace(path, begin, end, new):
    text = path.read_text(encoding="utf-8")
    if begin not in text or end not in text:
        sys.exit("markers %s / %s not found in %s" % (begin, end, path))
    text = text[:text.index(begin)] + new + text[text.index(end) + len(end):]
    path.write_text(text, encoding="utf-8")


def main():
    sup = json.loads(SUP.read_text(encoding="utf-8"))
    net = json.loads(NET.read_text(encoding="utf-8"))

    projects = json.loads((ROOT / "data" / "projects.json").read_text(encoding="utf-8"))
    for p in projects["projects"] + projects.get("without_own_volume", []):
        PROJECT_NAMES[p["id"]] = p["short"]

    replace(ROOT / "teaching" / "index.html",
            "<!-- BEGIN doctoral -->", "<!-- END doctoral -->", build_doctoral(sup))
    replace(ROOT / "cv" / "index.html",
            "<!-- BEGIN network -->", "<!-- END network -->", build_network(net))

    print("wrote %d ongoing and %d completed doctorates into /teaching/"
          % (len(sup["ongoing"]), len(sup["completed"])))
    print("wrote %d countries and %d named partners into /cv/"
          % (len(net["countries"]), len(net["partners"])))


if __name__ == "__main__":
    main()
