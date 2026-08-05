#!/usr/bin/env python3
"""
One entity for one person, referenced from every page.

Before this script the site carried 1,315 separate Person blocks — one per
author on each of the 234 publication pages, plus one on the start page — and
nothing said they were the same human being. A search engine or a language
model reading the site had no way to know that the "Voigt-Antons, J.-N." on a
2010 EEG paper is the person whose CV sits at /cv/. Seven of the main pages
carried no structured data at all.

The fix is a single node, https://voigt-antons.de/#person, defined in full on
the main pages and referred to by @id everywhere else. Publication pages point
their own author entry at it, which turns 234 unconnected islands into one
node with 234 edges. That is the shape both Google's knowledge graph and
retrieval-augmented models are built to read.

Nothing here is typed twice. Every fact is parsed out of the pages that
already state it:

    description   the meta description of the start page
    knowsAbout    the research line headings on /research/
    alumniOf      the education entries on /cv/
    award         the awards list on /cv/
    memberOf      the memberships line on /cv/
    sameAs        the external profile links on / and /cv/

If a parse comes back empty the script stops rather than emitting a thin
entity, because a silently impoverished graph is worse than none: it looks
answered and is not.

Usage:
    python3 tools/build_jsonld.py

Run after build_i18n.py — the German pages are derived from the English ones,
so they have to exist before their own blocks can be written into them.
"""

import html
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = "https://voigt-antons.de"

PERSON = SITE + "/#person"
WEBSITE = SITE + "/#website"
HSHL = SITE + "/#hshl"
LAB = SITE + "/#lab"

BEGIN, END = "<!-- BEGIN jsonld -->", "<!-- END jsonld -->"

# Hosts that identify the same person elsewhere. Anything else linked from the
# pages — the lab, a project site — describes an organisation, not him, and
# would be a false sameAs.
PROFILE_HOSTS = ("orcid.org", "scholar.google", "dblp.org", "scopus.com",
                 "semanticscholar.org", "dl.acm.org", "linkedin.com",
                 "github.com", "hshl.de/personen")

# Pages that get the full entity, with the breadcrumb trail each one sits in.
# The start page and the CV are profile pages in schema.org's sense: their
# subject is the person. The rest are ordinary pages about him.
PAGES = {
    "index.html": ("/", "ProfilePage", []),
    "cv/index.html": ("/cv/", "ProfilePage", [("CV", "/cv/")]),
    "research/index.html": ("/research/", "WebPage", [("Research", "/research/")]),
    "research/statement/index.html": ("/research/statement/", "WebPage",
                                      [("Research", "/research/"),
                                       ("Statement", "/research/statement/")]),
    "projects/index.html": ("/projects/", "WebPage", [("Projects", "/projects/")]),
    "teaching/index.html": ("/teaching/", "WebPage", [("Teaching", "/teaching/")]),
    "publications/index.html": ("/publications/", "CollectionPage",
                                [("Publications", "/publications/")]),
    "downloads/index.html": ("/downloads/", "CollectionPage",
                             [("Documents", "/downloads/")]),
    "blog/index.html": ("/blog/", "CollectionPage", [("Notes", "/blog/")]),
    "press/index.html": ("/press/", "WebPage", [("Press", "/press/")]),
}

# German equivalents of the breadcrumb labels. The German pages are the same
# entity at a different URL, so the @id of the person never changes — only the
# page node around it does.
DE_LABELS = {"CV": "Lebenslauf", "Research": "Forschung", "Statement": "Konzept",
             "Projects": "Projekte", "Teaching": "Lehre",
             "Publications": "Publikationen", "Documents": "Dokumente",
             "Notes": "Notizen", "Home": "Start",
             "Press": "Presse"}

problems = []


def text_of(fragment):
    """Visible text of an HTML fragment, entities resolved."""
    return html.unescape(re.sub(r"<[^>]+>", "", fragment)).strip()


def read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


def need(values, what):
    if not values:
        sys.exit("could not parse %s — the page changed shape; fix the parser "
                 "rather than shipping an entity without it" % what)
    return values


def block(page, start, stop=r'</div>'):
    """The markup between a heading and the end of its block."""
    m = re.search(start + r"(.*?)" + stop, page, re.S)
    return m.group(1) if m else ""


def description(page):
    m = re.search(r'<meta name="description" content="([^"]+)"', page)
    return html.unescape(m.group(1)) if m else ""


def research_lines(page):
    """The names of the research lines, from the <article class="line"> blocks.

    The first version split the page at the heading "Research lines". On the
    German page that string does not occur, so the split returned the whole
    document and knowsAbout came out as "Was diese Arbeit auszeichnet" and
    "Methodenkoffer" — section headings, not research topics. Anchoring on the
    markup instead of on an English sentence is language-proof, and these
    articles carry stable ids because the rest of the site links to them.
    """
    return [text_of(h) for h in
            re.findall(r'<article class="line[^"]*"[^>]*>.*?<h3[^>]*>(.*?)</h3>',
                       page, re.S)]


def education(cv):
    """Institutions awarding a degree, most recent first."""
    out = []
    for li in re.findall(r"<li>(.*?)</li>", block(cv, r'id="education"'), re.S):
        m = re.search(r"(Technische Universität \w+)", text_of(li))
        if m and m.group(1) not in out:
            out.append(m.group(1))
    return out


def awards(cv):
    """Award names, with the awarding body but without the explanation.

    Cutting at the first comma looked tidy and produced "Special Prize" and
    "Key Innovator" — labels that identify nothing on their own. The comma
    separates the award from who gave it, which is the half that makes it
    findable; the em dash separates it from the story, which is the half that
    does not belong in a graph.
    """
    out = []
    for li in re.findall(r"<li>(.*?)</li>", block(cv, r'id="awards"'), re.S):
        body = re.sub(r"^\s*\d{4}\s*", "", text_of(re.sub(r"<b>.*?</b>", "", li)))
        name = re.split(r"\s+[—–]\s+", body)[0]
        name = re.sub(r"\s*\([^)]*\)\s*$", "", name).strip(" ,·")
        if name and name not in out:
            out.append(name)
    return out


def memberships(cv):
    """Learned societies, from the memberships line."""
    m = re.search(r"(?:Memberships|Mitgliedschaften)</h3>\s*<ul[^>]*>\s*<li>(.*?)</li>", cv, re.S)
    if not m:
        return []
    out = []
    for part in text_of(m.group(1)).split("·"):
        name = part.split(",")[0].strip()
        if name:
            out.append(name)
        inner = re.search(r"\(([A-Z]{2,})\)", part)      # "… Society (ITG)"
        if inner:
            out.append(inner.group(1))
    return out


def profiles():
    """External profiles, taken from the pages that link them.

    The CV linked Google Scholar twice with two different hosts — .com in the
    profile block, .de in the footer — which is two identities for one person
    as far as a crawler is concerned. An earlier version of this function
    normalised the host before comparing and so could never have found that.
    It now compares what the pages actually say and reports any difference,
    because the point of reading the pages is to catch them disagreeing.
    """
    found = {}
    for page in ("index.html", "cv/index.html"):
        urls = {u for u in re.findall(r'href="(https://[^"]+)"', read(page))
                if any(h in u for h in PROFILE_HOSTS)}
        found[page] = urls
    only_home = found["index.html"] - found["cv/index.html"]
    only_cv = found["cv/index.html"] - found["index.html"]
    for url in sorted(only_home):
        problems.append("%s is linked on the start page but not on /cv/" % url)
    for url in sorted(only_cv):
        problems.append("%s is linked on /cv/ but not on the start page" % url)
    return sorted(found["index.html"] | found["cv/index.html"])


def person_node(desc, knows, alumni, award_names, member_names, same_as, lang):
    return {
        "@type": "Person",
        "@id": PERSON,
        "name": "Jan-Niklas Voigt-Antons",
        "honorificPrefix": "Prof. Dr.-Ing.",
        "givenName": "Jan-Niklas",
        "familyName": "Voigt-Antons",
        "jobTitle": ("Professor für Informatik (Immersive Medien)" if lang == "de"
                     else "Professor of Computer Science (Immersive Media)"),
        "description": desc,
        "url": SITE + ("/de/" if lang == "de" else "/"),
        "image": SITE + "/images/profile@2x.jpg",
        "email": "mailto:jan-niklas@voigt-antons.de",
        "knowsLanguage": ["de", "en"],
        "identifier": {
            "@type": "PropertyValue",
            "propertyID": "ORCID",
            "value": "0000-0002-2786-9262",
            "url": "https://orcid.org/0000-0002-2786-9262",
        },
        "affiliation": {"@id": HSHL},
        "worksFor": {"@id": HSHL},
        "alumniOf": [{"@type": "CollegeOrUniversity", "name": n} for n in alumni],
        "memberOf": [{"@type": "Organization", "name": n} for n in member_names],
        "award": award_names,
        "knowsAbout": knows,
        "sameAs": same_as,
    }


def org_nodes():
    return [
        {"@type": "CollegeOrUniversity", "@id": HSHL,
         "name": "Hamm-Lippstadt University of Applied Sciences",
         "alternateName": "Hochschule Hamm-Lippstadt",
         "url": "https://www.hshl.de/"},
        {"@type": "ResearchOrganization", "@id": LAB,
         "name": "Immersive Reality Lab",
         "url": "https://immersive-reality-lab.de",
         "parentOrganization": {"@id": HSHL},
         "founder": {"@id": PERSON}},
    ]


def breadcrumb(base, trail, lang):
    home = "Start" if lang == "de" else "Home"
    items = [(home, "/")] + list(trail)
    return {
        "@type": "BreadcrumbList",
        "@id": base + "breadcrumb",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1,
             "name": DE_LABELS.get(name, name) if lang == "de" else name,
             "item": SITE + ("/de" + url if lang == "de" and url != "/" else url)}
            for i, (name, url) in enumerate(items)],
    }


def artifact_nodes(lang):
    """Datasets and software, as their own entities.

    Google indexes datasets separately from pages, and a Dataset node is the
    only way a repository entry, the paper that documents it and the person who
    made it end up connected. Read from the same file that renders the visible
    list, so the two cannot describe different things.
    """
    path = ROOT / "data" / "artifacts.json"
    if not path.exists():
        return []
    pubs = {p["id"]: p for p in json.loads(
        (ROOT / "data" / "publications.json").read_text(encoding="utf-8"))["items"]}
    nodes = []
    for art in json.loads(path.read_text(encoding="utf-8"))["artifacts"]:
        node = {
            "@type": art["kind"],
            "@id": "%s/research/#artifact-%s" % (SITE, art["id"]),
            "name": art["name"],
            "description": art["summary"],
            "url": art["url"],
            "datePublished": str(art["year"]),
            "creator": {"@id": PERSON},
            "includedInDataCatalog": {"@type": "DataCatalog",
                                      "name": art["repository"]},
        }
        if art.get("keywords"):
            node["keywords"] = art["keywords"]
        # The paper that documents the data is the citation its authors ask
        # for. Without this edge the dataset and the paper describing it sit in
        # the graph as unrelated things.
        pub = pubs.get(art.get("paper"))
        if pub:
            node["citation"] = {
                "@type": "ScholarlyArticle",
                "name": pub["ti"],
                "datePublished": str(pub["y"]),
                "url": "%s/publication/%s" % (SITE, pub["id"]),
            }
            if pub.get("d"):
                node["citation"]["sameAs"] = pub["d"]
        nodes.append(node)
    return nodes


def graph_for(path, kind, trail, person, lang):
    url = SITE + ("/de" + path if lang == "de" and path != "/" else path)
    if lang == "de" and path == "/":
        url = SITE + "/de/"
    base = url + "#"
    page_node = {
        "@type": kind,
        "@id": base + "webpage",
        "url": url,
        "isPartOf": {"@id": WEBSITE},
        "about": {"@id": PERSON},
        "inLanguage": lang,
    }
    if kind == "ProfilePage":
        page_node["mainEntity"] = {"@id": PERSON}
    nodes = [page_node]
    # A trail of one is just the page itself. Emitting it would claim a
    # hierarchy that is not there and shows up as a stray crumb in results.
    if trail:
        page_node["breadcrumb"] = {"@id": base + "breadcrumb"}
        nodes.append(breadcrumb(base, trail, lang))
    if path == "/":
        nodes.append({
            "@type": "WebSite", "@id": WEBSITE,
            "url": SITE + "/", "name": "Jan-Niklas Voigt-Antons",
            "inLanguage": ["en", "de"], "publisher": {"@id": PERSON}})
        nodes += org_nodes()
    if path == "/research/":
        nodes += artifact_nodes(lang)
    nodes.append(person)
    return {"@context": "https://schema.org", "@graph": nodes}


def write_block(rel, payload):
    path = ROOT / rel
    text = path.read_text(encoding="utf-8")
    script = ('%s\n<script type="application/ld+json">%s</script>\n%s'
              % (BEGIN, json.dumps(payload, ensure_ascii=False,
                                   separators=(",", ":")), END))
    if BEGIN in text and END in text:
        new = text[:text.index(BEGIN)] + script + text[text.index(END) + len(END):]
    else:
        # First run: replace the hand-written block, or insert before </head>.
        old = re.search(r'<script type="application/ld\+json">.*?</script>\n?',
                        text, re.S)
        if old:
            new = text[:old.start()] + script + "\n" + text[old.end():]
        else:
            new = text.replace("</head>", script + "\n</head>", 1)
    if new != text:
        path.write_text(new, encoding="utf-8")
        return True
    return False


def main():
    same_as = profiles()

    # Both languages are parsed the same way and both are guarded. The German
    # side was unguarded once and shipped section headings as research topics
    # while the English side looked perfect — a check that only watches the
    # source language is not a check.
    facts = {}
    for lang, home_p, cv_p, res_p in (("en", "index.html", "cv/index.html",
                                       "research/index.html"),
                                      ("de", "de/index.html", "de/cv/index.html",
                                       "de/research/index.html")):
        where = " on the %s pages" % lang
        facts[lang] = dict(
            desc=need(description(read(home_p)), "the description" + where),
            knows=need(research_lines(read(res_p)), "the research lines" + where),
            alumni=need(education(read(cv_p)), "the education entries" + where),
            award_names=need(awards(read(cv_p)), "the awards" + where),
            member_names=need(memberships(read(cv_p)), "the memberships" + where))

    written = 0
    for lang in ("en", "de"):
        person = person_node(same_as=same_as, lang=lang, **facts[lang])
        for page, (path, kind, trail) in PAGES.items():
            rel = page if lang == "en" else "de/" + page
            if not (ROOT / rel).exists():
                continue
            written += write_block(rel, graph_for(path, kind, trail, person, lang))

    print("wrote structured data into %d page(s)" % written)
    print("person entity %s — %d profiles, %d research topics, %d awards"
          % (PERSON, len(same_as), len(facts["en"]["knows"]),
             len(facts["en"]["award_names"])))
    for note in problems:
        print("  - %s" % note)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
