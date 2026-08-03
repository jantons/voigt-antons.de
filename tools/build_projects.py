#!/usr/bin/env python3
"""
Generate the funding record on /projects/ from data/projects.json.

Why this exists: the funding figures used to live only as hand-written HTML,
and the same numbers are retyped into every application document. That is where
mistakes creep in — a role total that adds up to 20 while the summary says 19,
a project silently missing, an amount that no longer matches. One JSON file
feeds both the website and, via tools/export_projects_docx.py, the application
table.

Anything placed by hand between the markers is overwritten on the next run —
the download button was, once. Additions belong in this template.

The script replaces everything between these markers in projects/index.html:

    <!-- BEGIN funding-record -->
    <!-- END funding-record -->

Usage:
    python3 tools/build_projects.py
"""

import datetime
import html
import json
import pathlib
import sys
from collections import OrderedDict

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "projects.json"
PAGE = ROOT / "projects" / "index.html"

BEGIN = "<!-- BEGIN funding-record -->"
END = "<!-- END funding-record -->"
BEGIN_ONGOING = "<!-- BEGIN ongoing-projects -->"
END_ONGOING = "<!-- END ongoing-projects -->"
BEGIN_HOME = "<!-- BEGIN home-projects -->"
END_HOME = "<!-- END home-projects -->"

HOME = ROOT / "index.html"

# Project pages worth linking to directly from the start page.
HOMEPAGE_LINK = {
    "didymos-xr": "https://didymos-xr.eu/",
    "mia-prom": "https://mia-prom.de",
    "virtual-institute": "https://digitalise-swf.de",
    "xrwise": "https://xrevent-creator.de",
}

# Projects with a hand-written detail block further down /projects/.
ANCHORS = {"didymos-xr", "mia-prom", "virtual-institute", "digiontrack", "ariadne",
           "fastjets", "silent-bed-monitor", "xrwise", "itt", "xrt-hufusa",
           "infuse", "bernstein"}


def ends(p):
    """End of the funding period as (year, month). to_month is optional."""
    return (p["to"], p.get("to_month", 12))


def is_ongoing(p, today=None):
    """Derived, never stored — see meta.ongoing_note in data/projects.json.

    Year granularity alone is not enough: a project that ran out in spring would
    keep showing as active until January. Hence the optional to_month.
    """
    today = today or datetime.date.today()
    return ends(p) >= (today.year, today.month)


def period(p):
    return str(p["from"]) if p["from"] == p["to"] else "%d–%d" % (p["from"], p["to"])


def money(v):
    return "&euro;%sk" % format(v, ",")


def totals(projects, meta):
    """Role breakdown. Computed, never hand-written."""
    by = OrderedDict((k, [0, 0]) for k in meta["roles"])
    for p in projects:
        by[p["role"]][0] += 1
        by[p["role"]][1] += p["volume"]
    return by


def build(data):
    e = html.escape
    projects = sorted(data["projects"], key=lambda p: (-p["from"], -p["to"], p["name"]))
    meta = data["meta"]
    by = totals(projects, meta)

    n_all = len(projects)
    v_all = sum(p["volume"] for p in projects)
    led = [p for p in projects if p["role"] in meta["self_led_roles"]]
    v_led = sum(p["volume"] for p in led)
    coordinated = [p["short"] for p in projects if p["role"] == "coordinator"]

    role_lis = "".join(
        '<li><b>%d · %s</b><span>%s</span></li>' % (n, money(v), e(meta["roles"][k]))
        for k, (n, v) in by.items() if n
    )
    role_lis += ('<li><b>%d · %s</b><span><strong>Total</strong></span></li>'
                 % (n_all, money(v_all)))

    rows = "".join(
        '\n          <tr><td class="yr">%s</td><td>%s</td><td>%s</td><td>%s</td>'
        '<td class="amt">%s</td></tr>'
        % (period(p),
           ('<a href="#%s">%s</a>' % (e(p["id"]), e(p["name"]))) if p["id"] in ANCHORS else e(p["name"]),
           e(p["funder"]), e(meta["roles"][p["role"]].split(" — ")[0]), money(p["volume"]))
        for p in projects
    )

    others = " · ".join(
        '<a class="inline-link" href="#%s">%s</a> (%s, %s)'
        % (e(o["id"]), e(o["name"]), period(o), e(o["role_label"]))
        for o in data.get("without_own_volume", [])
    )

    return """{begin}
<section>
  <div class="wrap">
    <div class="sec-head"><span class="sec-num">02</span><h2>Full funding record</h2></div>
    <p class="sec-sub">All {n_all} funded projects with period, funder, role and awarded volume.
    This record is kept current; application documents reflect the state at their date of
    submission.</p>

    <div class="tr" style="margin-bottom:26px">
      <div class="tr-item rv">
        <h3>By role</h3>
        <ul>{role_lis}</ul>
      </div>
      <div class="tr-item rv">
        <h3>What that means</h3>
        <ul>
          <li><b>{n_led} of {n_all}</b><span>projects — {v_led} — applied for and led independently, as sole applicant, consortium coordinator or subproject lead</span></li>
          <li><b>{n_coord}</b><span>consortia coordinated end to end, including proposal design, consortium management, reporting and fund calls: {coord}</span></li>
          <li><b>Every</b><span>subproject: proposal written personally, budget managed independently, funded staff led</span></li>
        </ul>
      </div>
    </div>

    <div class="cta" style="margin:0 0 22px">
      <a class="btn btn-2 doc-dl" href="/files/funding.pdf">Download the funding record (PDF) ↓</a>
      <a class="btn btn-2" href="/downloads/">All documents</a>
    </div>

    <div class="table-scroll rv">
      <table>
        <thead>
          <tr><th>Period</th><th>Project</th><th>Funder</th><th>Role</th><th>Volume</th></tr>
        </thead>
        <tbody>{rows}
        </tbody>
      </table>
    </div>

    <p class="metrics-note" style="margin-top:14px">Funding record as of {updated} ·
    amounts are the awarded volumes for the subprojects applied for and managed personally</p>

    <div class="note">
      <b>Further project involvement without own funding volume.</b> {others}.
    </div>
  </div>
</section>
{end}""".format(
        begin=BEGIN, end=END, rows=rows, role_lis=role_lis, others=others,
        n_all=n_all, n_led=len(led), v_led=money(v_led),
        n_coord=len(coordinated), coord=e(", ".join(coordinated)),
        updated=meta["updated"],
    )


def build_ongoing(data):
    e = html.escape
    running = sorted((p for p in data["projects"] if is_ongoing(p)),
                     key=lambda p: (-p["from"], -p["to"], p["name"]))
    extra = [o for o in data.get("without_own_volume", []) if is_ongoing(o)]

    cards = []
    for p in running:
        cards.append(
            '      <a class="pcard rv" href="#%s">\n'
            '        <div class="pyear">%s · %s</div>\n'
            '        <h4>%s</h4>\n'
            '        <p>%s</p>\n'
            '        <span class="role">%s</span>\n'
            '      </a>'
            % (e(p["id"]), period(p),
               e(p.get("funder_short") or p["funder"].split("(")[0].strip()),
               e(p["short"]), e(p.get("blurb", "")),
               e(data["meta"]["roles"][p["role"]].split(" — ")[0])))
    for o in extra:
        cards.append(
            '      <a class="pcard rv" href="#%s">\n'
            '        <div class="pyear">%s · %s</div>\n'
            '        <h4>%s</h4>\n'
            '        <p>%s</p>\n'
            '        <span class="role">%s</span>\n'
            '      </a>'
            % (e(o["id"]), period(o),
               e(o.get("funder_short") or o["funder"].split("(")[0].strip()),
               e(o.get("short", o["name"].split(" — ")[0])), e(o.get("blurb", "")),
               e(o["role_label"])))

    n = len(cards)
    word = {1: "One", 2: "Two", 3: "Three", 4: "Four", 5: "Five", 6: "Six",
            7: "Seven", 8: "Eight", 9: "Nine", 10: "Ten"}.get(n, str(n))
    return """{begin}
<section>
  <div class="wrap">
    <div class="sec-head"><span class="sec-num">01</span><h2>Ongoing projects</h2></div>
    <p class="sec-sub">{word} projects currently running, with awards through {until}.</p>
    <div class="proj">
{cards}
    </div>
  </div>
</section>
{end}""".format(begin=BEGIN_ONGOING, end=END_ONGOING, word=word, cards="\n".join(cards),
                until=max([p["to"] for p in running] + [o["to"] for o in extra]))


def build_home(data):
    """The 'Current projects' cards on the start page.

    These used to be hand-written, and went stale exactly as you would expect:
    the start page still advertised DIDYMOS-XR, MIA-PROM and ARiadne as current
    months after they had ended, while ITT, INFUSE and Silent Bed Monitor —
    running — were missing. Now the same derived rule feeds both pages.
    """
    e = html.escape
    running = sorted((p for p in data["projects"] + data.get("without_own_volume", [])
                      if is_ongoing(p)),
                     key=lambda p: (-p["from"], -p["to"], p["name"]))
    cards = []
    for p in running:
        role = (p["role_label"] if "role_label" in p
                else data["meta"]["roles"][p["role"]].split(" — ")[0])
        cards.append(
            '      <a class="pcard rv" href="%s">\n'
            '        <div class="pyear">%s · %s</div>\n'
            '        <h4>%s</h4>\n'
            '        <p>%s</p>\n'
            '        <span class="role">%s</span>\n'
            '      </a>'
            % (HOMEPAGE_LINK.get(p["id"], "/projects/#" + e(p["id"])),
               period(p), e(p.get("funder_short") or p["funder"].split("(")[0].strip()),
               e(p["short"]), e(p.get("blurb", "")), e(role)))

    return """{begin}
    <div class="proj">
{cards}
    </div>
{end}""".format(begin=BEGIN_HOME, end=END_HOME, cards="\n".join(cards))


def replace_block(text, begin, end, new, path):
    if begin not in text or end not in text:
        sys.exit("markers %s / %s not found in %s" % (begin, end, path))
    return text[:text.index(begin)] + new + text[text.index(end) + len(end):]


def main():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    text = PAGE.read_text(encoding="utf-8")
    text = replace_block(text, BEGIN_ONGOING, END_ONGOING, build_ongoing(data), PAGE)
    text = replace_block(text, BEGIN, END, build(data), PAGE)
    PAGE.write_text(text, encoding="utf-8")

    home = HOME.read_text(encoding="utf-8")
    HOME.write_text(replace_block(home, BEGIN_HOME, END_HOME, build_home(data), HOME),
                    encoding="utf-8")

    n = len(data["projects"])
    v = sum(p["volume"] for p in data["projects"])
    running = [p["short"] for p in data["projects"] + data.get("without_own_volume", [])
               if is_ongoing(p)]
    print("wrote funding record: %d projects, €%sk" % (n, format(v, ",")))
    print("currently running (derived from the end date): %s" % ", ".join(running))

    vague = [p["short"] for p in data["projects"] + data.get("without_own_volume", [])
             if p["to"] == datetime.date.today().year and "to_month" not in p]
    if vague:
        print("note: ends this year without to_month, so still counted as running: %s"
              % ", ".join(vague))

    unconfirmed = [p["short"] for p in data["projects"] if p.get("role_unconfirmed")]
    if unconfirmed:
        print("note: role not yet confirmed for %s" % ", ".join(unconfirmed))


if __name__ == "__main__":
    main()
