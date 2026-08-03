#!/usr/bin/env python3
"""
Shared extraction logic for the German version of the site.

The design decision worth knowing: **the English source text is the key.**
data/i18n.json maps an English string to its German counterpart. Nothing in the
English pages is marked up, and no key has to be invented or kept in sync.

The payoff is that drift cannot hide. Edit an English sentence and its key
changes, so tools/build_i18n.py reports the string as untranslated instead of
silently shipping a German page that still claims the old thing. That is the
same failure this repository has already seen twice: a paragraph that existed
on two pages and quietly diverged, and a headline figure that went stale
because it was typed by hand in four places.

Translation units are *leaf block elements* — a <p>, <li> or heading that
contains no further block element. Inline markup (<em>, <strong>, <a>) stays
inside the unit, so a translator sees a whole sentence rather than fragments
torn apart at every tag.
"""

import re

# Elements whose text is translated, provided they contain no nested block.
BLOCK = ("p", "h1", "h2", "h3", "h4", "li", "figcaption", "caption", "summary",
         "title", "th", "button")

# Elements that may appear inside a unit without ending it.
INLINE = {"a", "em", "strong", "b", "i", "span", "code", "br", "sup", "sub",
          "small", "abbr", "time", "u", "s", "q", "cite", "wbr", "svg", "path"}

# Prose also lives in <a>, <div> and <span> carrying one of these classes —
# breadcrumbs, buttons, eyebrows, topic tags, footer columns. Without this the
# German page would keep its "Skip to content", "Home" and "Get in touch".
CLASSES = ("skip", "btn", "more", "crumbs", "eyebrow", "tag", "role", "fh",
           "foot-col", "copy", "empty", "lede", "sec-sub", "metric", "note",
           "metrics-note", "cv-nav")

BLOCK_RE = re.compile(
    r"<(%s)(\s[^>]*)?>(.*?)</\1>" % "|".join(BLOCK), re.S)

CLASS_OPEN = re.compile(
    r'<(a|div|span|aside)(\s[^>]*class="[^"]*\b(?:%s)\b[^"]*"[^>]*)>' % "|".join(CLASSES))
TAG = re.compile(r"<(/?)(a|div|span|aside)\b[^>]*>")


def class_elements(html):
    """Outermost class-matched elements, with the *correct* closing tag.

    A non-greedy regex cannot do this. For
    <div class="foot-col"><div class="fh">Elsewhere</div>…</div>
    it stops at the first </div>, so the outer match ends mid-element and the
    inner one is never seen at all. "Elsewhere" shipped untranslated while the
    generator reported full coverage — a silent gap, which is the one thing this
    design is supposed to prevent. Hence an explicit depth count.
    """
    pos = 0
    while True:
        m = CLASS_OPEN.search(html, pos)
        if not m:
            return
        tag, depth, scan = m.group(1), 1, m.end()
        while depth:
            t = TAG.search(html, scan)
            if not t:
                return
            scan = t.end()
            if t.group(2) == tag:
                depth += -1 if t.group(1) else 1
        yield m.start(), m.end(), t.start(), scan, tag, m.group(2)
        pos = scan

# Attributes carrying prose.
ATTR_RE = re.compile(
    r'(<meta\s+(?:name|property)="'
    r'(?:description|keywords|og:title|og:description|og:site_name)"\s+content=")([^"]+)(")'
    r'|(\s(?:aria-label|alt|title|placeholder)=")([^"]+)(")')

# Anything without a letter is an icon, a number or punctuation — nothing to
# translate. This also covers the ☰ and ◐ button glyphs.
HAS_LETTER = re.compile(r"[A-Za-zÀ-ÿ]")

# Publication titles and their venues stay English: they are the citable form
# of the work. A German rendering would be wrong to copy into a bibliography,
# and the entries come straight from data/publications.json anyway.
VERBATIM = re.compile(r'href="/publication/|class="pub-title"|class="venue"')


def _has_block(fragment):
    for tag in re.findall(r"</?([a-zA-Z][a-zA-Z0-9]*)", fragment):
        if tag.lower() not in INLINE:
            return True
    return False


def normalise(text):
    """Collapse whitespace so re-indenting a page does not invalidate a key."""
    return " ".join(text.split())


def _leaves(html):
    """Yield the innermost translatable fragments, descending into containers."""
    for m in BLOCK_RE.finditer(html):
        inner = m.group(3)
        if _has_block(inner):
            for nested in _leaves(inner):
                yield nested
        else:
            yield inner
    for _, open_end, close_start, _, _, _ in class_elements(html):
        inner = html[open_end:close_start]
        if _has_block(inner):
            for nested in _leaves(inner):
                yield nested
        else:
            yield inner


def units(html):
    """Yield every translatable string in the page, in document order."""
    seen = set()
    for inner in _leaves(html):
        if VERBATIM.search(inner):
            continue
        text = normalise(inner)
        if HAS_LETTER.search(text) and text not in seen:
            seen.add(text)
            yield text
    for m in ATTR_RE.finditer(html):
        value = m.group(2) or m.group(5)
        text = normalise(value)
        if HAS_LETTER.search(text) and text not in seen:
            seen.add(text)
            yield text


def translate(html, table, missing=None):
    """Return the page with every known unit replaced by its translation."""

    def render(inner):
        """Translate a fragment, descending into anything still nested."""
        if _has_block(inner):
            return translate_classes(BLOCK_RE.sub(block_sub, inner))
        if VERBATIM.search(inner):
            return inner
        key = normalise(inner)
        if not HAS_LETTER.search(key):
            return inner
        if key in table:
            return table[key]
        if missing is not None:
            missing.add(key)
        return inner

    def translate_classes(text):
        out, cursor = [], 0
        for open_start, open_end, close_start, close_end, _, _ in class_elements(text):
            out.append(text[cursor:open_end])
            out.append(render(text[open_end:close_start]))
            out.append(text[close_start:close_end])
            cursor = close_end
        out.append(text[cursor:])
        return "".join(out)

    def block_sub(m):
        tag, attrs, inner = m.group(1), m.group(2) or "", m.group(3)
        if _has_block(inner):
            return "<%s%s>%s</%s>" % (tag, attrs, render(inner), tag)
        if VERBATIM.search(inner):
            return m.group(0)
        key = normalise(inner)
        if not HAS_LETTER.search(key):
            return m.group(0)
        if key in table:
            return "<%s%s>%s</%s>" % (tag, attrs, table[key], tag)
        if missing is not None:
            missing.add(key)
        return m.group(0)

    def attr_sub(m):
        head, value, tail = (m.group(1), m.group(2), m.group(3)) if m.group(1) \
            else (m.group(4), m.group(5), m.group(6))
        key = normalise(value)
        if not HAS_LETTER.search(key):
            return m.group(0)
        if key in table:
            return head + table[key] + tail
        if missing is not None:
            missing.add(key)
        return m.group(0)

    html = BLOCK_RE.sub(block_sub, html)
    html = translate_classes(html)
    return ATTR_RE.sub(attr_sub, html)
