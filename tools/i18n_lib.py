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
           "metrics-note")

BLOCK_RE = re.compile(
    r"<(%s)(\s[^>]*)?>(.*?)</\1>" % "|".join(BLOCK), re.S)

CLASS_RE = re.compile(
    r'<(a|div|span)(\s[^>]*class="[^"]*\b(?:%s)\b[^"]*"[^>]*)>(.*?)</\1>'
    % "|".join(CLASSES), re.S)

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


def units(html):
    """Yield every translatable string in the page, in document order."""
    seen = set()
    for m in list(BLOCK_RE.finditer(html)) + list(CLASS_RE.finditer(html)):
        inner = m.group(3)
        if _has_block(inner):
            continue
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

    def block_sub(m):
        tag, attrs, inner = m.group(1), m.group(2) or "", m.group(3)
        if _has_block(inner) or VERBATIM.search(inner):
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
    html = CLASS_RE.sub(block_sub, html)
    return ATTR_RE.sub(attr_sub, html)
