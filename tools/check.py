#!/usr/bin/env python3
"""Refuse to ship a broken build.

Run after tools/build.py. Everything here is a mistake that has actually
happened at least once while building this site, so each check earns its
place. Exits non-zero on the first category that fails.
"""
import glob, os, re, shutil, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
OUT = ROOT / "preview"

fails: list[str] = []
notes: list[str] = []


def fail(what: str, detail: str) -> None:
    fails.append(f"{what}: {detail}")


# ---- 1. my working notes must not ship ----------------------------------
# every page in site/ opens with an <h2> and a subtitle that are annotations
# to me, not content. the build strips them. if the markup ever drifts, the
# strip silently misses and the notes go live.
for f in sorted(OUT.glob("*.html")):
    s = f.read_text(encoding="utf-8")
    if '<p class="subtitle">' in s:
        fail("annotation leaked", f.name)
    head = s[s.index("__BODY__") if "__BODY__" in s else 0:]
    if re.search(r'<div class="sb-page">\s*<h2>', s):
        fail("annotation leaked", f"{f.name} (leading h2)")


# ---- 2. the hidden chapter stays hidden ----------------------------------
# there is one intended way into director.html and it is not a link anyone
# can see. the single exception is the swap control on the architect page,
# which the unlock reveals. that one is allowed, but only for as long as it
# is still hidden by default, so the gate itself is what gets checked.
for f in sorted(OUT.glob("*.html")):
    if f.name == "director.html":
        continue
    for tag in re.findall(r'<a\b[^>]*href="[^"]*director\.html"[^>]*>', f.read_text(encoding="utf-8")):
        if "ap-swap" not in tag:
            fail("director.html linked", f"{f.name}: {tag[:60]}")

gate = (SITE / "architect-page.html").read_text(encoding="utf-8")
if ".ap-swap { display:none; }" not in gate:
    fail("unlock gate missing", "architect-page.html no longer hides .ap-swap by default")


# ---- 3. no dead internal links -------------------------------------------
have = {f.name for f in OUT.glob("*.html")}
for f in sorted(OUT.glob("*.html")):
    for href in re.findall(r'href="([^"#?:]+\.html)[^"]*"', f.read_text(encoding="utf-8")):
        target = os.path.basename(href)
        if target not in have:
            fail("dead link", f"{f.name} -> {href}")


# ---- 4. no em dashes, anywhere -------------------------------------------
# a standing style rule for this project. the exemptions are the places a
# double hyphen is not punctuation: css custom properties, the js decrement,
# comment delimiters, section dividers and base64 payloads.
for f in sorted(SITE.glob("*.html")):
    s = f.read_text(encoding="utf-8")
    if s.count("—"):
        fail("em dash", f"{f.name} x{s.count('—')}")
    t = re.sub(r"base64,[A-Za-z0-9+/=\s]+", "base64,X", s)
    t = t.replace("<!--", "").replace("-->", "")
    t = re.sub(r"/\*[^*]*?-{4,}.*?\*/", "", t, flags=re.S)
    t = re.sub(r"//\s*-{3,}[^\n]*", "", t)
    t = re.sub(r"--[A-Za-z][\w-]*", "VAR", t)
    t = re.sub(r"\w--", "", t)
    hits = re.findall(r"--", t)
    if hits:
        fail("double hyphen", f"{f.name} x{len(hits)}")


# ---- 5. every script block parses ----------------------------------------
# a page whose script throws on load loses its intro, its tabs and its nav.
node = shutil.which("node")
if not node:
    notes.append("node not found, script syntax check skipped")
else:
    with tempfile.TemporaryDirectory() as tmp:
        for f in sorted(SITE.glob("*.html")):
            s = f.read_text(encoding="utf-8")
            for i, block in enumerate(re.findall(r"<script>(.*?)</script>", s, re.S)):
                p = os.path.join(tmp, f"{f.stem}_{i}.js")
                Path(p).write_text(block, encoding="utf-8")
                r = subprocess.run([node, "--check", p], capture_output=True, text=True)
                if r.returncode:
                    fail("script syntax", f"{f.name} block {i}: "
                                          f"{r.stderr.strip().splitlines()[0]}")


# ---- 6. the build produced something -------------------------------------
if not (OUT / "index.html").exists():
    fail("missing", "preview/index.html")
if len(have) < 8:
    fail("too few pages", f"{len(have)} built")


for n in notes:
    print(f"  note: {n}")
if fails:
    print(f"FAILED ({len(fails)})")
    for x in fails:
        print(f"  {x}")
    sys.exit(1)
print(f"checks passed ({len(have)} pages)")
