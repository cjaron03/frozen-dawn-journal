#!/usr/bin/env python3
"""Wrap the site/ fragments into standalone browsable pages under preview/.

Each file in site/ is authored as a fragment for the brainstorm companion:
it opens with an <h2> plus a <p class="subtitle"> that are my working notes,
not site content, and it carries no doctype or head. This strips the notes
and wraps the rest in the shared shell.
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

# design docs, reachable from the workbench index but out of the main nav.
WORKBENCH = [
    ("page-map",        "Section 1: page map and the gate"),
    ("dev-layer",       "Section 1 revised: public first, dev on request"),
    ("chapters",        "Section 4a: chapters from first-appearance dates"),
    ("architect-sim",   "Section 3: the Architect and the sim"),
    ("sim-friendly",    "Section 3 revised: plain language"),
    ("visual-style",    "Visual direction, three options"),
    ("direction-locked","Locked: Deep Field with ORSA amber"),
    ("homepage-vibes",  "What gives a homepage homepage vibes"),
    ("homepage-motion", "More motion on the homepage"),
    ("decisions-board", "Decisions locked so far"),
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


def workbench_index() -> str:
    rows = []
    for stem, label in WORKBENCH:
        if not (SITE / f"{stem}.html").exists():
            continue
        rows.append(
            f'<li><a href="wb-{stem}.html">{label}</a>'
            f'<code>{stem}.html</code></li>'
        )
    return f"""
<div class="wb">
  <h1>Workbench</h1>
  <p>Design documents from building the site. These are working notes, not
     part of the public journal, and none of them ship.</p>
  <ul>{''.join(rows)}</ul>
</div>
<style>
.wb {{ max-width:720px; font-family:ui-sans-serif,-apple-system,sans-serif; }}
.wb h1 {{ font-size:22px; font-weight:650; color:#f2f6f8; letter-spacing:-.02em; }}
.wb > p {{ margin:8px 0 26px; font-size:13.5px; line-height:1.66; color:#8d98a1; }}
.wb ul {{ list-style:none; display:flex; flex-direction:column; gap:1px; }}
.wb li {{ display:flex; align-items:baseline; gap:12px;
          padding:11px 14px; background:#141920; border:1px solid #1c242e; border-radius:6px; }}
.wb li a {{ font-size:13.5px; color:#d4dade; text-decoration:none; flex:1; }}
.wb li:hover {{ border-color:#5c4620; }}
.wb li:hover a {{ color:#ffb454; }}
.wb code {{ font-family:ui-monospace,"SF Mono",Menlo,monospace;
            font-size:10px; letter-spacing:.06em; color:#5f6b76; }}
</style>"""


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

    for stem, label in WORKBENCH:
        src = SITE / f"{stem}.html"
        if not src.exists():
            skipped.append(stem)
            continue
        body, ok = strip_notes(src.read_text(encoding="utf-8"))
        if not ok:
            kept_notes.append(stem)
        out = f"wb-{stem}.html"
        (OUT / out).write_text(
            wrap(shell, f"{label} · Workbench", out, body), encoding="utf-8")
        built.append(out)

    (OUT / "workbench.html").write_text(
        wrap(shell, f"Workbench · {TITLE}", "workbench.html", workbench_index()),
        encoding="utf-8")
    built.append("workbench.html")

    print(f"built {len(built)} pages into preview/")
    if skipped:
        print(f"  not yet written: {', '.join(skipped)}")
    if kept_notes:
        print(f"  WARNING annotation block not found (notes may still ship): "
              f"{', '.join(kept_notes)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
