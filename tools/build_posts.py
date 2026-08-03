#!/usr/bin/env python3
"""
Build blog posts from content/posts/*.md.

Emits /posts/<YYYY>/<MM>/<slug>/index.html — the same URL scheme the previous
Jekyll site used, so existing links keep working — and regenerates
data/posts.json, which the blog index reads at runtime.

Usage:
    python3 tools/build_posts.py

Front matter (between --- fences):
    title:   post title (quote it if it contains a colon)
    date:    YYYY-MM-DD
    slug:    URL segment
    tags:    [comma, separated]
    summary: one-sentence teaser for the index and meta description

Markdown support is deliberately minimal — headings, paragraphs, bullet and
numbered lists, links, bold and italic. That covers the existing posts and
keeps this file dependency-free.
"""

import html
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "content" / "posts"
OUT = ROOT / "posts"
INDEX = ROOT / "data" / "posts.json"

NAV_LINKS = [
    ("/research/", "Research"),
    ("/projects/", "Projects"),
    ("/publications/", "Publications"),
    ("/cv/", "CV"),
    ("/blog/", "Blog"),
]


def nav():
    links = "".join(
        '<a href="%s"%s>%s</a>' % (h, ' aria-current="page"' if h == "/blog/" else "", t)
        for h, t in NAV_LINKS)
    mobile = "".join('<a href="%s">%s</a>' % (h, t) for h, t in NAV_LINKS)
    return """<nav>
  <div class="nav-in">
    <a href="/" class="brand">voigt-antons<span>.de</span></a>
    <div class="nav-links">%s</div>
    <div class="nav-tools">
      <button class="icon-btn" id="navToggle" aria-label="Menu" aria-expanded="false">&#9776;</button>
      <button class="icon-btn" id="themeToggle" aria-label="Switch to dark theme">&#9686;</button>
    </div>
  </div>
  <div class="mobile-menu" id="mobileMenu">%s<a href="/#contact">Contact</a></div>
</nav>""" % (links, mobile)


FOOTER = """<footer>
  <div class="wrap">
    <div class="foot-grid">
      <div>
        <div class="brand" style="font-size:14px;margin-bottom:6px">Prof. Dr.-Ing. Jan-Niklas Voigt-Antons</div>
        <div class="foot-col">Professor of Computer Science (Immersive Media)<br>Hamm-Lippstadt University of Applied Sciences</div>
        <div class="ids">
          <a class="id-chip" href="https://scholar.google.de/citations?user=IFIaOZsAAAAJ">Google Scholar</a>
          <a class="id-chip" href="https://orcid.org/0000-0002-2786-9262">ORCID</a>
          <a class="id-chip" href="https://dblp.org/pid/39/10762">DBLP</a>
          <a class="id-chip" href="https://www.linkedin.com/in/jnvoigtantons">LinkedIn</a>
        </div>
      </div>
      <div class="foot-col">
        <div class="fh">Elsewhere</div>
        <a href="https://immersive-reality-lab.de">Immersive Reality Lab &#8599;</a><br>
        <a href="/teaching/">Teaching</a> &middot; <a href="/cv/">CV</a> &middot; <a href="/blog/">Blog</a><br>
        <a class="inline-link" href="mailto:jan-niklas@voigt-antons.de">jan-niklas@voigt-antons.de</a>
      </div>
    </div>
    <div class="copy">&copy; 2026 &middot; <a href="/impressum/">Legal Notice</a> &middot; <a href="/impressum/#privacy">Privacy</a></div>
  </div>
</footer>"""

MONTHS = ["January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December"]


def parse_front_matter(text):
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        raise ValueError("missing front matter")
    meta, body = {}, m.group(2).strip()
    for line in m.group(1).splitlines():
        if not line.strip() or ":" not in line:
            continue
        k, v = line.split(":", 1)
        v = v.strip()
        if v.startswith("[") and v.endswith("]"):
            v = [x.strip() for x in v[1:-1].split(",") if x.strip()]
        elif len(v) > 1 and v[0] == v[-1] and v[0] in "\"'":
            v = v[1:-1]
        meta[k.strip()] = v
    return meta, body


def inline(s):
    """Escape, then re-apply the inline markdown we support."""
    s = html.escape(s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", s)
    return s


def markdown(body):
    out, block, mode = [], [], None

    def flush():
        if not block:
            return
        if mode == "ul":
            out.append("<ul>%s</ul>" % "".join("<li>%s</li>" % inline(x) for x in block))
        elif mode == "ol":
            out.append("<ol>%s</ol>" % "".join("<li>%s</li>" % inline(x) for x in block))
        else:
            out.append("<p>%s</p>" % inline(" ".join(block)))
        block.clear()

    for raw in body.splitlines():
        line = raw.rstrip()
        if not line.strip():
            flush(); mode = None; continue
        if line.startswith("### "):
            flush(); mode = None; out.append("<h3>%s</h3>" % inline(line[4:])); continue
        if line.startswith("## "):
            flush(); mode = None; out.append("<h2>%s</h2>" % inline(line[3:])); continue
        m = re.match(r"^[-*]\s+(.*)$", line)
        if m:
            if mode != "ul":
                flush(); mode = "ul"
            block.append(m.group(1)); continue
        m = re.match(r"^\d+\.\s+(.*)$", line)
        if m:
            if mode != "ol":
                flush(); mode = "ol"
            block.append(m.group(1)); continue
        if mode in ("ul", "ol"):
            flush(); mode = None
        mode = mode or "p"
        block.append(line.strip())
    flush()
    return "\n".join(out)


def page(post, prev_post, next_post):
    e = html.escape
    y, mth, d = post["date"].split("-")
    date_label = "%s %d, %s" % (MONTHS[int(mth) - 1], int(d), y)
    url = post["url"]

    tags = "".join('<span class="tag">%s</span>' % e(t) for t in post.get("tags", []))
    prev_html = ('<a class="more" href="%s">&#8592; %s</a>'
                 % (e(prev_post["url"]), e(prev_post["title"]))) if prev_post else "<span></span>"
    next_html = ('<a class="more" href="%s">%s &#8594;</a>'
                 % (e(next_post["url"]), e(next_post["title"]))) if next_post else "<span></span>"

    schema = json.dumps({
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": post["title"],
        "datePublished": post["date"],
        "description": post["summary"],
        "author": {"@type": "Person", "name": "Jan-Niklas Voigt-Antons"},
        "mainEntityOfPage": "https://voigt-antons.de" + url,
    }, ensure_ascii=False)

    return """<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} &mdash; Jan-Niklas Voigt-Antons</title>
<meta name="description" content="{summary}">
<link rel="canonical" href="https://voigt-antons.de{url}">
<meta property="og:type" content="article">
<meta property="article:published_time" content="{date}T00:00:00+00:00">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{summary}">
<meta property="og:image" content="https://voigt-antons.de/images/og-card.png">
<meta property="og:url" content="https://voigt-antons.de{url}">
<meta name="twitter:card" content="summary_large_image">
<link rel="stylesheet" href="/assets/style.css">
<script type="application/ld+json">{schema}</script>
</head>
<body>
<div class="bgfx"></div>
<a class="skip" href="#main">Skip to content</a>
{nav}
<main id="main">
<header class="page-head">
  <div class="wrap">
    <div class="crumbs"><a href="/">Home</a> / <a href="/blog/">Blog</a> / {year}</div>
    <div class="eyebrow"><i class="dot"></i>{date_label}</div>
    <h1>{title}</h1>
    <p class="lede">{summary}</p>
  </div>
</header>

<section>
  <div class="wrap">
    <article class="prose">
{body}
    </article>

    <div class="tags" style="margin-top:36px">{tags}</div>

    <div style="display:flex;justify-content:space-between;gap:20px;margin-top:40px;padding-top:24px;border-top:1px solid var(--line);flex-wrap:wrap">
      {prev}
      {next}
    </div>
  </div>
</section>
</main>
{footer}
<script src="/assets/main.js" defer></script>
</body>
</html>
""".format(
        title=e(post["title"]),
        summary=e(post["summary"]),
        url=e(url),
        date=e(post["date"]),
        date_label=date_label,
        year=y,
        body=markdown(post["body"]),
        tags=tags,
        prev=prev_html,
        next=next_html,
        schema=schema,
        nav=nav(),
        footer=FOOTER,
    )


def main():
    if not SRC.exists():
        sys.exit("missing %s" % SRC)

    posts = []
    for f in sorted(SRC.glob("*.md")):
        meta, body = parse_front_matter(f.read_text(encoding="utf-8"))
        for key in ("title", "date", "slug", "summary"):
            if key not in meta:
                sys.exit("%s: missing '%s' in front matter" % (f.name, key))
        y, mth, _ = meta["date"].split("-")
        posts.append({
            "title": meta["title"],
            "date": meta["date"],
            "slug": meta["slug"],
            "summary": meta["summary"],
            "tags": meta.get("tags", []),
            "url": "/posts/%s/%s/%s/" % (y, mth, meta["slug"]),
            "body": body,
        })

    posts.sort(key=lambda p: p["date"], reverse=True)

    OUT.mkdir(parents=True, exist_ok=True)
    for i, p in enumerate(posts):
        d = ROOT / p["url"].strip("/")
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(
            page(p, posts[i - 1] if i > 0 else None,
                 posts[i + 1] if i + 1 < len(posts) else None),
            encoding="utf-8")

    INDEX.write_text(json.dumps(
        {"posts": [{k: v for k, v in p.items() if k != "body"} for p in posts]},
        indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print("generated %d posts, wrote %s" % (len(posts), INDEX.relative_to(ROOT)))


if __name__ == "__main__":
    main()
