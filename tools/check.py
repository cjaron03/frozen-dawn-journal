#!/usr/bin/env python3
"""Refuse to ship a broken build.

Run after tools/build.py. Everything here is a mistake that has actually
happened at least once while building this site, so each check earns its
place. Exits non-zero on the first category that fails.
"""
import glob, os, re, shutil, subprocess, sys, tempfile
from pathlib import Path
from urllib.parse import urlparse

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


# ---- 2. the finishers' door stays a finishers' door ----------------------
# Maeve is listed like any other chapter now, but reading all seven still
# opens a second way in, through the Architect page, and that one is a
# reward. the controls it reveals have to stay hidden by default, or the
# reward is just a button.
GATED = [("ap-swap",   "architect-page.html", ".ap-swap { display:none; }"),
         ("ap-replay", "maeve.html",          ".ap-replay { display:none; }")]

for cls, src, rule in GATED:
    if rule not in (SITE / src).read_text(encoding="utf-8"):
        fail("unlock gate missing", f"{src} no longer hides .{cls} by default")


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


# ---- 6. the icons and the card actually reached the build ----------------
# the shell references these by relative path, so a missing copy step gives
# every page a blank tab icon and every pasted link a blank card, and the
# pages themselves still look perfectly fine locally.
for f in sorted(OUT.glob("*.html")):
    s = f.read_text(encoding="utf-8")
    for ref in set(re.findall(r'(?:href|content)="(?:[^"]*/)?(assets/[^"]+)"', s)):
        if not (OUT / ref).exists():
            fail("missing asset", f"{f.name} references {ref}")
    for ph in re.findall(r'__[A-Z]+__', s):
        fail("placeholder left unfilled", f"{f.name}: {ph}")


# ---- 7. the custom domain survived the build -----------------------------
# pages serves the site from whatever host the CNAME file names. lose that
# file and the domain silently reverts to the github.io address, while every
# og:url and og:image in the build keeps naming a host the site is no longer
# served from. checked against the build's own output rather than against
# build.py, so it catches a broken copy as well as a broken constant.
idx = OUT / "index.html"
if idx.exists():
    m = re.search(r'<meta property="og:url" content="([^"]+)"', idx.read_text(encoding="utf-8"))
    host = urlparse(m.group(1)).hostname if m else None
    if host and not host.endswith(".github.io"):
        cname = OUT / "CNAME"
        if not cname.exists():
            fail("missing CNAME", f"pages would fall back off {host}")
        elif cname.read_text(encoding="utf-8").strip() != host:
            fail("CNAME mismatch",
                 f"{cname.read_text(encoding='utf-8').strip()} but og:url says {host}")


# ---- 8. the build produced something -------------------------------------
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
