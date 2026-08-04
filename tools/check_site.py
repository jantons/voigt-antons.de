#!/usr/bin/env python3
"""
Static checks for the site. Runs in CI and locally; no dependencies.

Checks:
  1. Every HTML file has balanced tags.
  2. Every same-page anchor (href="#x") has a matching id.
  3. Every root-relative link resolves to a file or a directory index.
  4. Every inline JSON-LD block parses.
  5. data/*.json parse, and publication ids are unique.
  6. Generated output is in sync with its sources (no uncommitted drift).

Usage:
    python3 tools/check_site.py
Exit code 1 if anything fails.
"""

import hashlib
import html.parser
import json
import os
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SKIP_DIRS = {".git", ".github", ".idea", ".devcontainer", "node_modules", ".claude"}

# Assets the site links to that are not in the repository yet. Empty at the
# moment: the portrait, the preview card and the CV are all in place, so every
# link is checked like any other. Anything parked here is reported at the end
# of each run rather than silently tolerated.
ALLOW_MISSING = set()

problems = []


class Balance(html.parser.HTMLParser):
    VOID = {"meta", "link", "br", "img", "input", "hr", "source", "col", "area",
            "base", "embed", "param", "track", "wbr"}

    def __init__(self):
        super().__init__()
        self.stack = []
        self.errors = []

    def handle_starttag(self, tag, attrs):
        if tag not in self.VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if not self.stack:
            self.errors.append("stray </%s>" % tag)
        elif self.stack[-1] == tag:
            self.stack.pop()
        else:
            self.errors.append("expected </%s>, got </%s>" % (self.stack[-1], tag))


def html_files():
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            if name.endswith(".html"):
                yield pathlib.Path(dirpath) / name


def resolves(url):
    target = ROOT / url.lstrip("/")
    if url == "/":
        return (ROOT / "index.html").exists()
    return target.exists() or (target / "index.html").exists()


def prose_pages():
    """Hand-written and translated pages — everything except the generated ones.

    Was `glob("*/index.html")`, which quietly excluded every German subpage:
    de/cv/, de/research/ and the rest sit one level deeper. The figures on those
    pages went unchecked, which is the opposite of what a drift guard is for.
    """
    for page in sorted(html_files()):
        parts = page.relative_to(ROOT).parts
        if parts[0] in ("publication", "posts"):
            continue
        yield page


def check_conflict_markers():
    """No merge conflict markers anywhere in the repository.

    A merge left "=======" and ">>>>>>> d2db1925" sitting in the middle of the
    downloads page, and every other check passed: the markup stayed balanced,
    the links resolved, the figures matched. Only reading the page found it.

    Cheap to test, and the failure mode is loud — a visitor sees git internals
    on the page — so it is worth its own check rather than trusting review.
    """
    pattern = re.compile(r"^(?:<{7} |={7}$|>{7} )", re.M)
    for path in sorted(html_files()):
        if pattern.search(path.read_text(encoding="utf-8")):
            problems.append("%s: contains merge conflict markers"
                            % path.relative_to(ROOT))
    for folder in ("data", "tools", "assets", "content"):
        for path in sorted((ROOT / folder).rglob("*")):
            if path.is_file() and path.suffix in (".py", ".json", ".css", ".js", ".md"):
                try:
                    text = path.read_text(encoding="utf-8")
                except (UnicodeDecodeError, OSError):
                    continue
                if pattern.search(text):
                    problems.append("%s: contains merge conflict markers"
                                    % path.relative_to(ROOT))


def check_section_numbers(pages):
    """Section numbers must read 01, 02, 03 … in the order the sections appear.

    The teaching page read 01, 03, 02: a section was inserted above another and
    kept the number it would have had below it. Nothing else notices — the
    markup is valid, the anchors resolve — but a reader counts.

    The rule is equality with 1..n, not "ascending". Ascending passes 01, 03, 03
    and 01, 02, 04, which are the two mistakes an editor actually makes when
    moving a section: duplicating a number, or leaving a hole behind.
    """
    for page in pages:
        text = page.read_text(encoding="utf-8")
        numbers = [int(n) for n in
                   re.findall(r'<span class="sec-num">(\d+)</span>', text)]
        if numbers and numbers != list(range(1, len(numbers) + 1)):
            problems.append(
                "%s: section numbers read %s — expected %s"
                % (page.relative_to(ROOT),
                   " ".join("%02d" % n for n in numbers),
                   " ".join("%02d" % n for n in range(1, len(numbers) + 1))))


def check_cross_page_anchors(pages):
    """A fragment on another page has to exist there too.

    Same-page anchors were checked from the start; links like
    /cv/#bibliometrics or /projects/#didymos-xr were not, because the link
    check drops everything after the "#". They fail quietly: the page loads,
    the browser simply stays at the top, and nobody notices that the reader was
    aimed at a section that has since been renamed. The figures on the start
    page each point at the page that documents them, so there are now several.
    """
    id_cache = {}

    def ids_of(url):
        if url not in id_cache:
            target = ROOT / url.lstrip("/")
            if target.is_dir() or url.endswith("/"):
                target = target / "index.html"
            id_cache[url] = (set(re.findall(r'id="([^"]+)"',
                                            target.read_text(encoding="utf-8")))
                             if target.exists() else None)
        return id_cache[url]

    for page in pages:
        text = page.read_text(encoding="utf-8")
        for url, frag in set(re.findall(r'(?:href|src)="(/[^"#?]*)#([^"]+)"', text)):
            if url in ALLOW_MISSING:
                continue
            ids = ids_of(url)
            if ids is not None and frag not in ids:
                problems.append("%s: link to %s#%s — that page has no id %r"
                                % (page.relative_to(ROOT), url, frag, frag))


def check_structured_data(pages):
    """The entity graph has to hold together.

    Every page's JSON-LD refers to one Person, https://voigt-antons.de/#person.
    A reference is only worth something if something defines it, and a
    definition is only worth something if it is the same everywhere: two pages
    describing "#person" differently would merge into one contradictory node,
    which is worse than two honest strangers.

    So: every page carries a block, every @id referenced on a page is either
    defined on that page or is the person node, and the person node is
    byte-identical wherever it appears in a given language.
    """
    person_id = "https://voigt-antons.de/#person"
    # Pages that carry no entity on purpose: a tag index, the error page and
    # the legal notice, which is the one page robots.txt keeps out anyway.
    exempt = {("tags", "index.html"), ("404.html",), ("impressum", "index.html"),
              ("de", "impressum", "index.html")}

    defined, referenced, seen_person = {}, [], {}

    for page in pages:
        rel = page.relative_to(ROOT)
        text = page.read_text(encoding="utf-8")
        blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>',
                            text, re.S)
        if not blocks:
            # A page that asks not to be indexed has nothing to say to a
            # knowledge graph. The redirect stubs left behind by renamed
            # publication ids are all of this kind, and listing them by name
            # would mean editing this check every time one is added.
            noindex = re.search(r'<meta name="robots" content="[^"]*noindex', text)
            if rel.parts not in exempt and not noindex:
                problems.append("%s: no structured data — run tools/build_jsonld.py"
                                % rel)
            continue

        for raw in blocks:
            try:
                data = json.loads(raw)
            except ValueError:
                continue                      # already reported by the JSON-LD check
            nodes = [n for n in data.get("@graph", [data]) if isinstance(n, dict)]

            for node in nodes:
                if node.get("@id"):
                    defined.setdefault(node["@id"], rel)
            referenced += [(rel, r) for r in
                           set(re.findall(r'"@id"\s*:\s*"([^"]+)"', raw))]

            for node in nodes:
                if node.get("@id") == person_id and node.get("@type") == "Person":
                    lang = "de" if rel.parts[0] == "de" else "en"
                    key = json.dumps(node, sort_keys=True, ensure_ascii=False)
                    if lang not in seen_person:
                        seen_person[lang] = (rel, key)
                    elif seen_person[lang][1] != key:
                        problems.append(
                            "%s: describes %s differently from %s — one entity "
                            "cannot have two descriptions"
                            % (rel, person_id, seen_person[lang][0]))

    # References resolve across the site, not within one page: that is the
    # point of the design. The person is defined on the main pages and pointed
    # at from 234 publication pages; requiring a local definition would have
    # meant repeating the whole entity on every one of them.
    for rel, ref in sorted(set(referenced)):
        if ref not in defined:
            problems.append("%s: refers to %s but no page defines it" % (rel, ref))

    for lang in ("en", "de"):
        if lang not in seen_person:
            problems.append("no %s page defines %s" % (lang, person_id))


def check_pdf_fonts():
    """The documents must actually be set in the typeface they were designed in.

    Every PDF generator falls back to the PDF base-14 Helvetica when the
    Liberation fonts are missing. That fallback is deliberate — better a
    readable document than none — but it was silent, and the paths were
    hard-coded to a directory the CI runner did not have. So the site served
    six documents in a typeface nobody had ever reviewed, at a third of the
    file size, and nothing said a word.

    Reading the font names out of the finished file is the only honest test:
    it checks the artefact rather than the intention, and it fails on the
    machine that built it, not on the reader's screen.
    """
    sys.path.insert(0, str(ROOT / "tools"))
    from pdf_fonts import EMBEDDED_MARKER, describe

    documents = sorted((ROOT / "files").glob("*.pdf"))
    if not documents:
        problems.append("files/ holds no PDF — run the document generators")
        return
    for path in documents:
        if EMBEDDED_MARKER not in path.read_bytes():
            problems.append(
                "%s embeds no Liberation font — it was built with the Helvetica "
                "fallback. %s" % (path.relative_to(ROOT), describe()))


def check_label_widths(pages):
    """A label in .cv-list must fit its 104px column.

    That column holds a year or "since 2021" and sets white-space:nowrap, so
    anything longer runs straight across the text beside it. Institution names
    did — "University of Technology Sydney" is three times the width — and the
    partner list was unreadable until someone looked at it. The same shape of
    fault put "2026[C58]" through the publication titles.

    Lists whose label is a name use .cv-list.stack, which puts it on its own
    line; those are exempt. Fourteen characters is what 104px holds at 12.5px
    in the mono face, with a little room.
    """
    limit = 14
    for page in pages:
        text = page.read_text(encoding="utf-8")
        for block in re.finditer(r'<ul class="cv-list(?! stack)[^"]*">(.*?)</ul>',
                                 text, re.S):
            for label in re.findall(r"<li><b>([^<]+)</b>", block.group(1)):
                plain = re.sub(r"&#?\w+;", "x", label)
                if len(plain) > limit:
                    problems.append(
                        "%s: label %r is %d characters and will overrun the "
                        "104px column — use class=\"cv-list stack\""
                        % (page.relative_to(ROOT), label[:40], len(plain)))


def check_placeholders(pages):
    """Nothing marked as "fill this in" may reach the live site.

    The legal notice needs a real, servable address (§ 5 DDG). A page that goes
    online with a bracketed placeholder is worse than none at all, so it fails
    the build rather than quietly publishing.
    """
    for page in pages:
        text = page.read_text(encoding="utf-8")
        for found in set(re.findall(r"\[(?:Anzupassen|Stra&szlig;e|Straße|PLZ|TODO)[^\]]*\]", text)):
            problems.append("%s: unfilled placeholder %s"
                            % (page.relative_to(ROOT), found))


def check_fonts(pages):
    """No third-party requests, and every declared font file has to exist.

    A <link> to fonts.googleapis.com sends every visitor's IP address to Google
    before the page renders — the practice a German court found unlawful in
    LG München I, 3 O 17493/20. The fonts are therefore served from this domain,
    and this check keeps them that way: a generator template that quietly grows
    the old <link> back would otherwise ship on 250 pages unnoticed.
    """
    for page in pages:
        text = page.read_text(encoding="utf-8")
        for host in ("fonts.googleapis.com", "fonts.gstatic.com"):
            if host in text:
                problems.append("%s: links to %s — fonts are self-hosted, see "
                                "tools/fetch_fonts.py" % (page.relative_to(ROOT), host))

    css_path = ROOT / "assets" / "style.css"
    if not css_path.exists():
        return
    css = css_path.read_text(encoding="utf-8")

    block = re.search(r"/\* BEGIN fonts \*/(.*?)/\* END fonts \*/", css, re.S)
    if not block:
        problems.append("assets/style.css: the /* BEGIN fonts */ block is gone")
        return
    if "@font-face" not in block.group(1):
        problems.append("assets/style.css: no @font-face rules — run "
                        "tools/fetch_fonts.py, otherwise the site silently "
                        "falls back to system fonts")
        return

    for url in re.findall(r"url\((/assets/fonts/[^)]+)\)", block.group(1)):
        if not (ROOT / url.lstrip("/")).exists():
            problems.append("assets/style.css: @font-face points at %s, which "
                            "is missing — run tools/fetch_fonts.py" % url)


def check_cv_pdf():
    """Neither CV PDF may be older than what it is derived from.

    The PDF cannot contradict the data by construction — it reads the figures
    out of the JSON. What it can be is stale: built before a publication was
    added or a project ended, and then handed to a committee that also opens the
    website. tools/build_cv_pdf.py leaves a fingerprint of its sources; this
    compares it against the sources as they are now.
    """
    for pdf_name, stamp_name in (("files/cv.pdf", "files/cv.build.json"),
                                 ("files/cv-de.pdf", "files/cv-de.build.json"),
                                 ("files/publications.pdf", "files/records.build.json"),
                                 ("files/funding.pdf", "files/records.build.json"),
                                 ("files/statement.pdf", "files/statement.build.json")):
        pdf, stamp_path = ROOT / pdf_name, ROOT / stamp_name
        if not pdf.exists():
            continue
        if not stamp_path.exists():
            problems.append("%s has no build stamp — run tools/build_cv_pdf.py --all"
                            % pdf_name)
            continue
        try:
            stamp = json.loads(stamp_path.read_text(encoding="utf-8"))
        except ValueError as err:
            problems.append("%s: %s" % (stamp_name, err))
            continue

        digest, gone = hashlib.sha256(), False
        for name in stamp.get("sources", []):
            source = ROOT / name
            if not source.exists():
                problems.append("%s lists %s, which is gone" % (stamp_name, name))
                gone = True
                break
            digest.update(name.encode())
            digest.update(source.read_bytes())
        if gone:
            continue

        if digest.hexdigest()[:16] != stamp.get("fingerprint"):
            problems.append("%s is out of date — %s changed since it was built on %s. "
                            "Run tools/build_cv_pdf.py --all or tools/build_record_pdfs.py --all."
                            % (pdf_name, ", ".join(stamp.get("sources", [])),
                               stamp.get("built", "?")))


def check_i18n():
    """The German version must stay complete and reciprocally linked.

    Two ways this could rot: a new English core page without a German
    counterpart, and hreflang links that point somewhere the other page does not
    point back to. Search engines treat a one-sided hreflang as no hreflang, so
    the German page would compete with the English one instead of complementing
    it.
    """
    data_path = ROOT / "data" / "i18n.json"
    if not data_path.exists():
        return 0

    try:
        table = json.loads(data_path.read_text(encoding="utf-8"))["de"]
    except (ValueError, KeyError) as err:
        problems.append("data/i18n.json: %s" % err)
        return 0

    empty = [k for k, v in table.items() if not str(v).strip()]
    for key in empty[:5]:
        problems.append("data/i18n.json: empty translation for %r" % key[:60])

    # Kept in step with PAGES in tools/build_i18n.py — the statement page was
    # generated but unchecked until it was added here, and a check that lags the
    # generator is worth little.
    pairs = [("index.html", "/"), ("research/index.html", "/research/"),
             ("projects/index.html", "/projects/"), ("cv/index.html", "/cv/"),
             ("teaching/index.html", "/teaching/"),
             ("research/statement/index.html", "/research/statement/")]
    built = 0
    for page, path in pairs:
        german = ROOT / "de" / page
        if not german.exists():
            problems.append("de/%s is missing — run tools/build_i18n.py" % page)
            continue
        built += 1
        gt = german.read_text(encoding="utf-8")
        et = (ROOT / page).read_text(encoding="utf-8")

        if 'lang="de"' not in gt.split("\n")[1]:
            problems.append("de/%s: <html> does not declare lang=\"de\"" % page)
        if 'href="https://voigt-antons.de/de%s"' % path not in gt:
            problems.append("de/%s: canonical does not point at /de%s" % (page, path))

        for text, label in ((et, page), (gt, "de/" + page)):
            for lang, href in (("en", path), ("de", "/de" + path)):
                link = '<link rel="alternate" hreflang="%s" href="https://voigt-antons.de%s">' \
                       % (lang, href)
                if link not in text:
                    problems.append("%s: missing hreflang=%s alternate" % (label, lang))
            if 'class="icon-btn lang-switch"' not in text:
                problems.append("%s: no language switch in the navigation" % label)

            # A German page offering the English PDF is the kind of thing
            # nobody notices until a committee downloads it.
            for m in re.finditer(r'<a[^>]*class="[^"]*\bdoc-dl\b[^"]*"[^>]*'
                                 r'href="(/files/[a-z-]+\.pdf)"', text):
                german_page = label.startswith("de/")
                german_file = m.group(1).endswith("-de.pdf")
                if german_page != german_file:
                    problems.append("%s: download button points at %s"
                                    % (label, m.group(1)))

    # Pages that exist in English only still need a way back to the German
    # section — a visitor who followed "Publikationen" from /de/ would otherwise
    # be stranded in English with no marked route back.
    for page in ("publications/index.html", "blog/index.html", "404.html"):
        text = (ROOT / page).read_text(encoding="utf-8")
        if 'class="icon-btn lang-switch"' not in text:
            problems.append("%s: no way back to the German section — run "
                            "tools/build_i18n.py" % page)
        elif 'href="/de/"' not in text:
            problems.append("%s: the language switch does not point at /de/" % page)
    return built


def check_headline_numbers(items, meta):
    """Publication and citation figures quoted in prose must match the data.

    The hero on the start page claimed 226 publications long after the list had
    grown to 234, because that number is typed by hand in four places and the
    generator never touches it. Nobody notices a headline figure going stale —
    but a search committee comparing it against the publication list would.

    Lines mentioning Scopus are skipped: those cite a different database with
    legitimately different numbers.
    """
    bib = meta.get("bibliometrics", {})
    expected = {
        "publications": len(items),
        "citations": bib.get("citations"),
        "h-index": bib.get("h_index"),
        "i10-index": bib.get("i10_index"),
        # The German pages repeat the same figures in their own words.
        "Publikationen": len(items),
        "Zitationen": bib.get("citations"),
        "h-Index": bib.get("h_index"),
        "i10-Index": bib.get("i10_index"),
    }
    # <b>234</b><span>publications  and  "234 publications" / "h-index 29"
    patterns = (
        (r"<b>([\d,]+)</b>\s*<span>(publications)", 1, 2),
        (r"<b>([\d.]+)</b>\s*<span>(Publikationen|Zitationen)", 1, 2),
        (r"\b([\d,]+)\s+(publications|citations)\b", 1, 2),
        (r"\b([\d.]+)\s+(Publikationen|Zitationen)\b", 1, 2),
        (r"\b(h-index|i10-index|h-Index|i10-Index)\s+([\d,]+)", 2, 1),
    )

    for page in prose_pages():
        # Blank out <script> bodies but keep the line count, so reported line
        # numbers stay usable. Otherwise the filter UI's "0 publications" empty
        # state would be read as a stale claim.
        text = re.sub(r"<script\b[^>]*>.*?</script>",
                      lambda m: "\n" * m.group(0).count("\n"),
                      page.read_text(encoding="utf-8"), flags=re.S)

        for lineno, line in enumerate(text.splitlines(), 1):
            if "Scopus" in line:
                continue

            # A line about the last five years is checked against the recent
            # figures, not the totals — otherwise stating both would be
            # impossible, and the recent ones are the more telling half.
            recent = bib.get("since_2021") or {}
            if recent and ("since 2021" in line or "seit 2021" in line):
                want = {"publications": None,
                        "citations": recent.get("citations"),
                        "Zitationen": recent.get("citations"),
                        "h-index": recent.get("h_index"),
                        "h-Index": recent.get("h_index"),
                        "i10-index": recent.get("i10_index"),
                        "i10-Index": recent.get("i10_index")}
                for pattern, num_group, key_group in patterns:
                    for m in re.finditer(pattern, line):
                        target = want.get(m.group(key_group))
                        if target is None:
                            continue
                        got = int(m.group(num_group).replace(",", "").replace(".", ""))
                        if got != target:
                            problems.append(
                                "%s:%d: says %s %s since 2021, data/publications.json "
                                "says %s" % (page.relative_to(ROOT), lineno,
                                             m.group(num_group), m.group(key_group), target))
                continue
            for pattern, num_group, key_group in patterns:
                for m in re.finditer(pattern, line):
                    key = m.group(key_group)
                    want = expected.get(key)
                    if want is None:
                        continue
                    got = int(m.group(num_group).replace(",", "").replace(".", ""))
                    if got != want:
                        problems.append("%s:%d: says %s %s, data/publications.json "
                                        "says %s" % (page.relative_to(ROOT), lineno,
                                                     m.group(num_group), key, want))


def check_peer_review(items):
    """A figure labelled "peer-reviewed" must not include the ones that are not.

    The site claimed "163 peer-reviewed conference papers" while the data has
    always distinguished them: C1–C105 are the peer-reviewed papers, OC1–OC58
    the further contributions. The application documents draw that line
    correctly, the website did not — and overstating peer review is precisely
    the claim an appointment committee checks.

    The reference prefix carries the distinction, so it can be verified.
    """
    counts = {}
    for item in items:
        ref = item.get("ref", "")
        prefix = "".join(c for c in ref if c.isalpha())
        counts[prefix] = counts.get(prefix, 0) + 1

    expected = {"journal": counts.get("J", 0), "conference": counts.get("C", 0)}
    for page in prose_pages():
        text = " ".join(page.read_text(encoding="utf-8").split())
        for kind, want in expected.items():
            for stated in re.findall(
                    r"([\d,]+)\s+(?:peer-reviewed|begutachtete)\s+"
                    r"(?:%s|%s)" % (kind, "Zeitschriften" if kind == "journal" else "Konferenz"),
                    text):
                got = int(stated.replace(",", ""))
                if got != want:
                    problems.append(
                        "%s: claims %d peer-reviewed %s items, but the data has %d "
                        "(the rest are 'other' entries — O%s)"
                        % (page.relative_to(ROOT), got, kind, want, kind[0].upper()))


def check_projects():
    """Funding record: the rendered page must add up to data/projects.json.

    This is the check that would have caught the inconsistency in the 2026
    application document, where the role breakdown summed to 20 projects while
    the total said 19, and the listed amounts fell €304k short of the headline
    figure.
    """
    data_path = ROOT / "data" / "projects.json"
    page_path = ROOT / "projects" / "index.html"
    if not (data_path.exists() and page_path.exists()):
        return 0

    try:
        data = json.loads(data_path.read_text(encoding="utf-8"))
    except ValueError as err:
        problems.append("data/projects.json: %s" % err)
        return 0

    projects = data["projects"]
    ids = [p["id"] for p in projects]
    for dup in {i for i in ids if ids.count(i) > 1}:
        problems.append("projects.json: duplicate id %s" % dup)

    roles = data["meta"]["roles"]
    for p in projects:
        if p["role"] not in roles:
            problems.append("projects.json: %s has unknown role %r" % (p["id"], p["role"]))
        if p["from"] > p["to"]:
            problems.append("projects.json: %s ends before it starts" % p["id"])

    for p in projects + data.get("without_own_volume", []):
        month = p.get("to_month")
        if month is not None and not (isinstance(month, int) and 1 <= month <= 12):
            problems.append("projects.json: %s has to_month %r, expected 1–12"
                            % (p["id"], month))

    # Hand-written detail blocks must state the same period as the data.
    page_text = page_path.read_text(encoding="utf-8")
    by_id = {p["id"]: p for p in projects}
    by_id.update({o["id"]: o for o in data.get("without_own_volume", [])})
    for m in re.finditer(r'<article class="line rv" id="([^"]+)">\s*'
                         r'<div class="line-label"><span class="lnum">([^<]+)</span>',
                         page_text):
        pid, shown = m.group(1), m.group(2).strip()
        p = by_id.get(pid)
        if not p:
            continue
        expected = (str(p["from"]) if p["from"] == p["to"]
                    else "%d–%d" % (p["from"], p["to"]))
        if shown != expected:
            problems.append("projects/index.html: detail block #%s says %s, "
                            "projects.json says %s" % (pid, shown, expected))

    expected_n = len(projects)
    expected_v = sum(p["volume"] for p in projects)
    expected_led = sum(p["volume"] for p in projects
                       if p["role"] in data["meta"]["self_led_roles"])

    text = page_path.read_text(encoding="utf-8")
    body = re.search(r"<tbody>(.*?)</tbody>", text, re.S)
    if not body:
        problems.append("projects/index.html: no funding table found")
        return expected_n

    amounts = [int(m.replace(",", ""))
               for m in re.findall(r'class="amt">&euro;([\d,]+)k', body.group(1))]
    if len(amounts) != expected_n:
        problems.append("projects/index.html: table has %d rows, projects.json has %d — "
                        "run tools/build_projects.py" % (len(amounts), expected_n))
    if sum(amounts) != expected_v:
        problems.append("projects/index.html: table sums to EUR %dk, projects.json to EUR %dk"
                        % (sum(amounts), expected_v))

    # The headline figures must agree with the data, wherever they appear.
    for label, value in (("total", expected_v), ("self-led", expected_led)):
        millions = "%.3f" % (value / 1000.0)
        if label == "total" and ("€%s million" % millions) not in text and \
                ("€%sM" % millions) not in text:
            problems.append("projects/index.html: headline total does not state €%s million"
                            % millions)

    for page in ("index.html", "cv/index.html"):
        t = (ROOT / page).read_text(encoding="utf-8")
        if "third-party funding" in t or "funded projects" in t:
            if "%.3f" % (expected_v / 1000.0) not in t.replace(",", "."):
                problems.append("%s: funding total is out of sync with data/projects.json"
                                % page)
            if str(expected_n) + "</b><span>funded projects" not in t and \
                    "%d funded projects" % expected_n not in t:
                problems.append("%s: project count is out of sync with data/projects.json"
                                % page)
    return expected_n


def main():
    pages = sorted(html_files())
    if not pages:
        problems.append("no HTML files found — wrong working directory?")

    for page in pages:
        rel = page.relative_to(ROOT)
        text = page.read_text(encoding="utf-8")

        parser = Balance()
        parser.feed(text)
        if parser.stack:
            problems.append("%s: unclosed tags %s" % (rel, parser.stack))
        for err in parser.errors:
            problems.append("%s: %s" % (rel, err))

        ids = set(re.findall(r'id="([^"]+)"', text))
        for frag in set(re.findall(r'href="#([^"]+)"', text)):
            if frag not in ids:
                problems.append("%s: anchor #%s has no target" % (rel, frag))

        for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>',
                                text, re.S):
            try:
                json.loads(block)
            except ValueError as err:
                problems.append("%s: invalid JSON-LD (%s)" % (rel, err))

        for url in set(re.findall(r'(?:href|src)="(/[^"#?\']*)', text)):
            if url in ALLOW_MISSING:
                continue
            if not resolves(url):
                problems.append("%s: dead link %s" % (rel, url))

    pubs_path = ROOT / "data" / "publications.json"
    try:
        items = json.loads(pubs_path.read_text(encoding="utf-8"))["items"]
    except (ValueError, KeyError, OSError) as err:
        problems.append("data/publications.json: %s" % err)
        items = []

    # A DOI identifies exactly one work. Two entries sharing one is almost
    # always a copy-paste slip in the source bibliography.
    by_doi = {}
    for item in items:
        doi = item.get("d", "")
        if doi.startswith("https://doi.org/"):
            by_doi.setdefault(doi, []).append(item["id"])
    for doi, ids in by_doi.items():
        if len(ids) > 1:
            problems.append("publications.json: %s is used by %s" % (doi, ", ".join(ids)))

    # The reference number from the Publikationsverzeichnis identifies one
    # publication. Two entries claiming the same one means the import drifted.
    by_ref = {}
    for item in items:
        if item.get("ref"):
            by_ref.setdefault(item["ref"], []).append(item["id"])
    for ref, ids in by_ref.items():
        if len(ids) > 1:
            problems.append("publications.json: reference [%s] is claimed by %s"
                            % (ref, ", ".join(ids)))

    # Each series (J, C, OC, …) has to run 1..n without gaps; a gap means an
    # entry was dropped or the numbering drifted from the Word document.
    series = {}
    for item in items:
        ref = item.get("ref", "")
        prefix = "".join(c for c in ref if c.isalpha())
        number = ref[len(prefix):]
        if prefix and number.isdigit():
            series.setdefault(prefix, []).append(int(number))
    for prefix, numbers in sorted(series.items()):
        gaps = sorted(set(range(1, max(numbers) + 1)) - set(numbers))
        if gaps:
            problems.append("publications.json: series %s has gaps at %s"
                            % (prefix, ", ".join("%s%d" % (prefix, g) for g in gaps[:10])))

    seen = set()
    for item in items:
        for key in ("id", "y", "t", "ti", "a", "v", "tp"):
            if key not in item:
                problems.append("publications.json: %s missing '%s'"
                                % (item.get("id", "?"), key))
        if item.get("id") in seen:
            problems.append("publications.json: duplicate id %s" % item["id"])
        seen.add(item.get("id"))
        if item.get("id") and not (ROOT / "publication" / item["id"] / "index.html").exists():
            problems.append("publications.json: %s has no generated page — "
                            "run tools/build_publication_pages.py" % item["id"])

    try:
        posts = json.loads((ROOT / "data" / "posts.json").read_text(encoding="utf-8"))["posts"]
    except (ValueError, KeyError, OSError) as err:
        problems.append("data/posts.json: %s" % err)
        posts = []

    for post in posts:
        if not resolves(post["url"]):
            problems.append("posts.json: %s has no generated page — "
                            "run tools/build_posts.py" % post["url"])

    sources = len(list((ROOT / "content" / "posts").glob("*.md")))
    if sources != len(posts):
        problems.append("posts.json lists %d posts but content/posts has %d markdown files — "
                        "run tools/build_posts.py" % (len(posts), sources))

    try:
        meta = json.loads(pubs_path.read_text(encoding="utf-8")).get("meta", {})
    except (ValueError, OSError):
        meta = {}
    check_headline_numbers(items, meta)
    check_peer_review(items)
    check_conflict_markers()
    check_section_numbers(pages)
    check_cross_page_anchors(pages)
    check_structured_data(pages)
    check_pdf_fonts()
    check_label_widths(pages)
    check_placeholders(pages)
    check_cv_pdf()
    german = check_i18n()
    check_fonts(pages)
    projects = check_projects()

    print("checked %d HTML pages, %d publications, %d posts, %d funded projects, "
          "%d German pages" % (len(pages), len(items), len(posts), projects, german))

    pending = sorted(u for u in ALLOW_MISSING if not resolves(u))
    resolved = sorted(u for u in ALLOW_MISSING if resolves(u))
    if pending:
        print("\nstill missing from the repository (does not fail the build):")
        for url in pending:
            print("  - %s — %d page(s) link to it"
                  % (url, sum(1 for p in pages
                              if url in p.read_text(encoding="utf-8"))))
    if resolved:
        print("\nnow present — remove from ALLOW_MISSING in tools/check_site.py "
              "so a future typo is caught: %s" % ", ".join(resolved))

    if problems:
        print("\n%d problem(s):" % len(problems))
        for p in problems:
            print("  - %s" % p)
        return 1
    print("all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
