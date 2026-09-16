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
    return (shell.replace("__TITLE__", title)
                 .replace("__BODYCLASS__", "home" if current == "index.html" else "")
                 .replace("__NAV__", nav_html(current))
                 .replace("__BODY__", body))


def main() -> int:
    shell = (SITE / "_shell.html").read_text(encoding="utf-8")
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

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
