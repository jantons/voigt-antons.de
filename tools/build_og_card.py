#!/usr/bin/env python3
"""
Draw images/og-card.png — the preview image shown when a link to this site is
shared on LinkedIn, Slack, Mastodon, WhatsApp or posted in a mail client.

251 pages point at this one file. Without it, every share of every publication
page renders as a bare grey box.

The card repeats the site's visual language: light background, faint grid,
the accent violet, mono type for figures. The figures are **read from
data/publications.json and data/projects.json**, never typed here, so the card
cannot end up claiming a different number of publications than the page it is
attached to — the exact failure the start page had with "226 publications".

Fonts: Inter is used when it can be read out of assets/fonts/, which needs
fontTools with brotli (pip install fonttools brotli). Without them the script
falls back to the closest grotesque installed on the system and says so. The
card is a one-off asset — render it once, commit the PNG.

Requires Pillow (pip install Pillow). Unlike the other tools in this folder,
this one is not part of the build: it is run by hand when the figures move.

Usage:
    python3 tools/build_og_card.py
    python3 tools/build_og_card.py --dark
"""

import argparse
import io
import json
import pathlib
import sys

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    sys.exit("this script needs Pillow:  pip install Pillow")

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "images" / "og-card.png"
W, H = 1200, 630

LIGHT = dict(bg="#fdfdfe", grid="#e6e8ee", fg="#0b0d13", fg2="#525a68",
             fg3="#858d9b", accent="#5645f5", glow=(86, 69, 245, 26))
DARK = dict(bg="#08090c", grid="#23272f", fg="#edf0f4", fg2="#a2aab5",
            fg3="#6b7380", accent="#9b8cff", glow=(155, 140, 255, 30))

# Tried in order; the first that exists wins.
SYSTEM_FONTS = {
    "regular": ["/usr/share/fonts/opentype/urw-base35/NimbusSans-Regular.otf",
                "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
             "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/System/Library/Fonts/Helvetica.ttc"],
    "bold": ["/usr/share/fonts/opentype/urw-base35/NimbusSans-Bold.otf",
             "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
             "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
             "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
             "/System/Library/Fonts/Helvetica.ttc"],
    "mono": ["/usr/share/fonts/truetype/liberation2/LiberationMono-Regular.ttf",
             "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
             "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
             "/System/Library/Fonts/Menlo.ttc"],
}


def repo_font(name):
    """Inter or JetBrains Mono out of assets/fonts/, if woff2 can be read."""
    try:
        import logging
        logging.getLogger("fontTools").setLevel(logging.CRITICAL)
        from fontTools.ttLib import TTFont
    except ImportError:
        return None
    for path in sorted((ROOT / "assets" / "fonts").glob("%s-latin.woff2" % name)):
        try:
            buffer = io.BytesIO()
            TTFont(str(path)).save(buffer)
            buffer.seek(0)
            return buffer.read()
        except Exception:
            return None          # brotli missing, or a format we cannot read
    return None


def load(kind, size, cache={}):
    key = (kind, size)
    if key in cache:
        return cache[key]
    blob = repo_font("inter" if kind != "mono" else "jetbrains-mono")
    if blob:
        try:
            font = ImageFont.truetype(io.BytesIO(blob), size)
            font.set_variation_by_axes([700 if kind == "bold" else 400])
            cache[key] = font
            return font
        except Exception:
            pass
    for candidate in SYSTEM_FONTS[kind]:
        if pathlib.Path(candidate).exists():
            cache[key] = ImageFont.truetype(candidate, size)
            return cache[key]
    cache[key] = ImageFont.load_default()
    return cache[key]


def figures():
    pubs = json.loads((ROOT / "data" / "publications.json").read_text(encoding="utf-8"))
    proj = json.loads((ROOT / "data" / "projects.json").read_text(encoding="utf-8"))
    bib = pubs["meta"]["bibliometrics"]
    total = sum(p["volume"] for p in proj["projects"])
    return [
        "€%.3fM third-party funding" % (total / 1000.0),
        "%d publications" % len(pubs["items"]),
        "%s citations" % format(bib["citations"], ","),
        "h-index %d" % bib["h_index"],
    ]


def draw_backdrop(img, c):
    d = ImageDraw.Draw(img)
    for x in range(0, W, 60):
        d.line([(x, 0), (x, H)], fill=c["grid"], width=1)
    for y in range(0, H, 60):
        d.line([(0, y), (W, y)], fill=c["grid"], width=1)

    # Fade the grid out towards the bottom, as the site does with a mask.
    mask = Image.new("L", (W, H))
    md = ImageDraw.Draw(mask)
    for y in range(H):
        md.line([(0, y), (W, y)], fill=max(0, 255 - int(255 * (y / (H * 0.75)))))
    img.paste(Image.new("RGB", (W, H), c["bg"]), (0, 0), Image.eval(mask, lambda v: 255 - v))

    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for r in range(360, 0, -6):
        alpha = int(c["glow"][3] * (1 - r / 360.0) ** 1.6)
        gd.ellipse([600 - r * 1.5, -180 - r * 0.7, 600 + r * 1.5, -180 + r * 1.7],
                   fill=c["glow"][:3] + (alpha,))
    img.alpha_composite(glow) if img.mode == "RGBA" else img.paste(
        Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB"), (0, 0))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dark", action="store_true", help="dark variant")
    ap.add_argument("-o", "--out", default=str(OUT))
    args = ap.parse_args()
    c = DARK if args.dark else LIGHT

    img = Image.new("RGB", (W, H), c["bg"])
    draw_backdrop(img, c)
    d = ImageDraw.Draw(img)

    d.rectangle([0, 0, 8, H], fill=c["accent"])

    x = 78
    d.text((x, 92), "PROF. DR.-ING.", font=load("mono", 21), fill=c["accent"])
    d.text((x, 142), "Jan-Niklas", font=load("bold", 86), fill=c["fg"])
    d.text((x, 232), "Voigt-Antons", font=load("bold", 86), fill=c["fg"])

    d.text((x, 348), "Professor of Computer Science (Immersive Media)",
           font=load("regular", 30), fill=c["fg2"])
    d.text((x, 390), "Hamm-Lippstadt University of Applied Sciences",
           font=load("regular", 30), fill=c["fg2"])

    d.line([(x, 470), (W - 78, 470)], fill=c["grid"], width=2)

    mono = load("mono", 22)
    cursor = x
    for i, item in enumerate(figures()):
        if i:
            d.text((cursor, 508), "·", font=mono, fill=c["fg3"])
            cursor += d.textlength("·  ", font=mono)
        d.text((cursor, 508), item, font=mono, fill=c["fg2"])
        cursor += d.textlength(item + "  ", font=mono)

    domain = "voigt-antons.de"
    df = load("mono", 24)
    d.text((W - 78 - d.textlength(domain, font=df), 552), domain, font=df,
           fill=c["accent"])

    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, "PNG", optimize=True)

    used = "Inter (from assets/fonts/)" if repo_font("inter") else \
        "a system fallback — pip install fonttools brotli to use Inter itself"
    print("wrote %s (%d×%d, %.0f KB)"
          % (out.relative_to(ROOT) if out.is_relative_to(ROOT) else out,
             W, H, out.stat().st_size / 1024.0))
    print("typeface: %s" % used)
    print("figures taken from data/publications.json and data/projects.json")


if __name__ == "__main__":
    main()
