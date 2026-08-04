#!/usr/bin/env python3
"""
Find the typefaces the PDF documents are set in — wherever the system put them.

Four generators each hard-coded /usr/share/fonts/truetype/liberation2/. The CI
runner installs the package "fonts-liberation", which writes to
/usr/share/fonts/truetype/liberation/ — no "2" — so every path missed, every
script took its silent Helvetica fallback, and the documents on the live site
were served in a different typeface from the ones tested locally. The machine
this was written on happened to have both packages installed, which is exactly
why it went unnoticed: the failure needed a machine with only one of them.

The lesson is not "use the other path". It is that a font lives wherever the
distribution decided to put it, so the resolver searches and reports what it
found, and the build fails loudly instead of quietly changing typeface.

Usage:
    from pdf_fonts import resolve, FALLBACK
    paths = resolve()          # {} if nothing was found
"""

import pathlib

# Both Liberation packages, and the macOS locations for a local run. Order is
# preference: Liberation 2 is the newer metric-compatible set.
FONT_DIRS = (
    "/usr/share/fonts/truetype/liberation2",
    "/usr/share/fonts/truetype/liberation",
    "/usr/share/fonts/liberation2",
    "/usr/share/fonts/liberation",
    "/opt/homebrew/share/fonts",
    "/usr/local/share/fonts",
    str(pathlib.Path.home() / "Library" / "Fonts"),
)

FILES = {
    "sans": "LiberationSans-Regular.ttf",
    "sans-bold": "LiberationSans-Bold.ttf",
    "sans-italic": "LiberationSans-Italic.ttf",
    "mono": "LiberationMono-Regular.ttf",
    "mono-bold": "LiberationMono-Bold.ttf",
}

FALLBACK = {"sans": "Helvetica", "sans-bold": "Helvetica-Bold",
            "sans-italic": "Helvetica-Oblique", "mono": "Courier",
            "mono-bold": "Courier-Bold"}

# What a finished PDF must contain if the real fonts were used. check_site.py
# looks for this, because file size alone is a weak signal and the difference
# is otherwise invisible until someone opens the document.
EMBEDDED_MARKER = b"LiberationSans"


def resolve():
    """Full paths for every needed face, or {} if the set is incomplete.

    All or nothing on purpose: a document set half in Liberation and half in
    Helvetica is worse than one set consistently in either.
    """
    for folder in FONT_DIRS:
        base = pathlib.Path(folder)
        found = {key: base / name for key, name in FILES.items()}
        if all(path.exists() for path in found.values()):
            return {key: str(path) for key, path in found.items()}
    return {}


def describe():
    paths = resolve()
    if paths:
        return "Liberation fonts from %s" % pathlib.Path(paths["sans"]).parent
    return ("Liberation fonts not found in any of: %s — falling back to "
            "Helvetica, which changes the metrics and the file size. Install "
            "fonts-liberation or fonts-liberation2." % ", ".join(FONT_DIRS[:2]))


if __name__ == "__main__":
    print(describe())
