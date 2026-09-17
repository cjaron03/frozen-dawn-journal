#!/usr/bin/env python3
"""Wrap the site/ fragments into standalone browsable pages under preview/.

Each file in site/ is authored as a fragment for the brainstorm companion:
it opens with an <h2> plus a <p class="subtitle"> that are my working notes,
not site content, and it carries no doctype or head. This strips the notes
and wraps the rest in the shared shell.

Everything under site/ ships. The design documents that used to build
alongside it now live in docs/workbench/ and are never emitted.
"""
import re, sys, shutil
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
OUT  = ROOT / "preview"

# the public site, in nav order. (source stem, output name, nav label)
PAGES = [
    ("timeline",                  "index.html",     "Home"),
    ("world-doesnt-wait",         "chapter-1.html", "I. The World That Doesn't Wait"),
    ("architect-page",            "architect.html", "II. Building a Mind"),
    ("they-called-it-continuity", "chapter-3.html", "III. They Called it Continuity"),
    ("holding-back-the-cold",     "chapter-4.html", "IV. Holding Back the Cold"),
    ("what-the-cold-made",        "chapter-5.html", "V. What the Cold Made"),
    ("the-ones-who-stayed",       "chapter-6.html", "VI. The Ones Who Stayed"),
    ("welcome-home",              "chapter-7.html", "VII. Welcome Home"),
]

# built, but deliberately absent from every index, nav and card on the site.
# there is exactly one intended way in and it is not a link.
UNLISTED = [
    ("maeve", "director.html", "Maeve"),
]

TITLE = "Frozen Dawn"

# where the built site actually lives. og:image has to be absolute, because
# the machine reading it is not the browser and has no page to resolve
# against.
BASE = "https://frozendawn.jaronc.com/"

# one line per page, for the search result and for the card that appears
# when someone pastes the link into chat.
DESC = {
    "index.html": "A dev journal for Frozen Dawn, a rogue planet survival mod. "
                  "How one person built a world that freezes, and a thing "
                  "that learned to think.",
    "chapter-1.html": "Building Frozen Dawn's six phase collapse: vacuum, cold, "
                      "snow, and a chunk loader that had to keep up with a dying world.",
    "architect.html": "How the Architect learned to think. The decision loop, the "
                      "mistakes it made, and a simulation you can run yourself.",
    "chapter-3.html": "ORSA promised continuity and delivered an evacuation. The "
                      "corporate layer of Frozen Dawn, and the breadcrumbs it left.",
    "chapter-4.html": "Heaters, capacitors, insulated glass and sealed rooms. Every "
                      "system the player has for holding one room above freezing.",
    "chapter-5.html": "Frostbitten, Hollows, Mimics and Frostmites. What kinds of "
                      "things survive when the world itself turns hostile.",
    "chapter-6.html": "Hearths, the Returned, Thaeven and Maeve. ORSA left. "
                      "Humanity left. They stayed.",
    "chapter-7.html": "Warmth begins as life and ends as fuel. Building a way off a "
                      "dead planet, and what home turns out to mean.",
    "director.html": "A chapter of the Frozen Dawn dev journal.",
}

# the hidden chapter is reachable by anyone who types the address, which is
# fine. it should not turn up in a search for it, which is the difference
# between a secret and a listing.
NOINDEX = {"director.html"}

def esc(t: str) -> str:
    """These land inside double quoted attributes, so they get escaped."""
    return (t.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;").replace('"', "&quot;"))


# leading <h2>...</h2> then <p class="subtitle">...</p>, both my annotations.
ANNOT = re.compile(r'\A\s*<h2>.*?</h2>\s*<p class="subtitle">.*?</p>\s*', re.S)


def strip_notes(src: str) -> tuple[str, bool]:
    out, n = ANNOT.subn("", src, count=1)
    return out, bool(n)


def nav_html(current: str) -> str:
    bits = []
    for stem, out, label in PAGES:
        exists = (SITE / f"{stem}.html").exists()
        if not exists:
            bits.append(f'<a class="soon" title="not built yet">{label}</a>')
        elif out == current:
            bits.append(f'<a class="on" href="{out}">{label}</a>')
        else:
            bits.append(f'<a href="{out}">{label}</a>')
    return "\n    ".join(bits)


def wrap(shell: str, title: str, current: str, body: str) -> str:
    # the homepage supplies its own masthead, so it hides the shared site bar.
    robots = ('<meta name="robots" content="noindex">\n'
              if current in NOINDEX else "")
    return (shell.replace("__TITLE__", esc(title))
                 .replace("__DESC__", esc(DESC.get(current, DESC["index.html"])))
                 .replace("__URL__", BASE + ("" if current == "index.html" else current))
                 .replace("__BASE__", BASE)
                 .replace("__ROBOTS__", robots)
                 .replace("__BODYCLASS__", "home" if current == "index.html" else "")
                 .replace("__NAV__", nav_html(current))
                 .replace("__BODY__", body))


def main() -> int:
    shell = (SITE / "_shell.html").read_text(encoding="utf-8")
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    # the icons and the social card, drawn by tools/art/make_icons.py.
    assets = SITE / "assets"
    if assets.is_dir():
        shutil.copytree(assets, OUT / "assets")

    # pages takes the custom domain from a CNAME file at the root of whatever
    # gets published, and a deploy without one can drop the site back to the
    # github.io address. this is derived from BASE so the two cannot drift:
    # the address changes in one place and the deploy follows it.
    host = urlparse(BASE).hostname or ""
    if host and not host.endswith(".github.io"):
        (OUT / "CNAME").write_text(host + "\n", encoding="utf-8")

    built, skipped, kept_notes = [], [], []

    for stem, out, label in PAGES:
        src = SITE / f"{stem}.html"
        if not src.exists():
            skipped.append(stem)
            continue
        body, ok = strip_notes(src.read_text(encoding="utf-8"))
        if not ok:
            kept_notes.append(stem)
        (OUT / out).write_text(
            wrap(shell, f"{label} · {TITLE}" if out != "index.html" else TITLE,
                 out, body), encoding="utf-8")
        built.append(out)

    for stem, out, label in UNLISTED:
        src = SITE / f"{stem}.html"
        if not src.exists():
            skipped.append(stem)
            continue
        body, ok = strip_notes(src.read_text(encoding="utf-8"))
        if not ok:
            kept_notes.append(stem)
        (OUT / out).write_text(
            wrap(shell, f"{label} · {TITLE}", out, body), encoding="utf-8")
        built.append(out)

    print(f"built {len(built)} pages into preview/")
    if skipped:
        print(f"  not yet written: {', '.join(skipped)}")
    if kept_notes:
        print(f"  WARNING annotation block not found (notes may still ship): "
              f"{', '.join(kept_notes)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
