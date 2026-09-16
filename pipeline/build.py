"""Render the homepage from the commit history.

Every number, position and duration on the page is derived here from
data/commits.tsv. Nothing about the project's shape is typed by hand,
so a rebuild after new commits produces a correct page with no edits.
Hand authored input is limited to two small files: chapters.json (where
the chapter boundaries fall) and milestones.json (which commits are
worth a dot), and both are editorial choices, not facts about the repo.
"""
import collections, datetime, json, math, pathlib, random, sys

ROOT = pathlib.Path(__file__).parent
OUT  = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "out" / "timeline.html"
REPO_URL = "https://github.com/cjaron03/frozen-dawn"

W, H     = 1000.0, 200.0   # stage viewBox
SMOOTH   = 7               # days in the moving average
T0, DRAW = 0.15, 3.6       # when the line starts, how long it takes
TRAV     = 72.0            # seconds for Earth to cross the header
SPIN     = 7.0             # seconds per rotation
ARC      = "M 34 46 C 250 14, 640 11, 1078 40"
LAND = ('<path d="M -7.2 -4.4 q 3.1 -2.2 5.2 .9 q 2 3.1 -1.1 4.1 q -4.1 1 -5.1 -2 z"/>'
        '<path d="M 1.1 -1.3 q 4 -3 6 .2 q 1 3.9 -3 4.8 q -3.9 0 -3 -5 z"/>'
        '<path d="M -3.3 4.2 q 3 -1 4.1 1.9 q -1 2 -4.1 1 z"/>'
        '<path d="M 5.4 -6.1 q 2.6 -1 3.4 1.4 q -1.2 1.8 -3.6 .9 z"/>')

MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
def short(d):  return "%02d %s" % (d.day, MONTHS[d.month - 1])
def longd(d):  return "%02d %s %d" % (d.day, MONTHS[d.month - 1], d.year)


def load():
    rows = []
    for line in (ROOT / "data" / "commits.tsv").read_text(encoding="utf-8").splitlines():
        if line.strip():
            date, subject = line.split("\t", 1)
            rows.append((datetime.date.fromisoformat(date), subject))
    if not rows:
        sys.exit("no commits in data/commits.tsv, run fetch.py first")
    rows.sort()
    return rows


def curve(rows, first, span):
    """Commits per day, smoothed, as a polyline in the stage viewBox."""
    per = collections.Counter(d for d, _ in rows)
    raw = [per[first + datetime.timedelta(days=i)] for i in range(span)]
    # Trailing, not centred. A centred window lets a commit lift the line on the
    # days BEFORE it was made, which on a journal is just false. Trailing means
    # each day shows the week behind it, so a return to work lands on its real date.
    sm = [sum(raw[max(0, i - SMOOTH + 1):i + 1]) / float(min(i + 1, SMOOTH))
          for i in range(span)]
    peak = max(sm) or 1.0
    pts = [(i / float(span - 1) * W, H - 18 - (v / peak) * (H - 40)) for i, v in enumerate(sm)]
    return pts, per


def arclen(pts):
    """Cumulative length, so a dot's delay matches when the line reaches it."""
    cum = [0.0]
    for i in range(len(pts) - 1):
        cum.append(cum[-1] + math.dist(pts[i], pts[i + 1]))
    return cum


def at_x(pts, cum, x):
    """Interpolate y and the length fraction at a given x on the curve."""
    for i in range(len(pts) - 1):
        if pts[i][0] <= x <= pts[i + 1][0]:
            f = 0.0 if pts[i + 1][0] == pts[i][0] else (x - pts[i][0]) / (pts[i + 1][0] - pts[i][0])
            y = pts[i][1] + f * (pts[i + 1][1] - pts[i][1])
            return y, (cum[i] + f * (cum[i + 1] - cum[i])) / cum[-1]
    return pts[-1][1], 1.0


def longest_gap(rows):
    """The real quiet stretch: the largest span between two commits."""
    days = sorted(set(d for d, _ in rows))
    best = (0, None, None)
    for i in range(len(days) - 1):
        g = (days[i + 1] - days[i]).days
        if g > best[0]:
            best = (g, days[i], days[i + 1])
    return best


def main():
    rows = load()
    first, last = rows[0][0], rows[-1][0]
    span = (last - first).days + 1
    pts, per = curve(rows, first, span)
    cum = arclen(pts)
    total_len = cum[-1]
    x_of = lambda d: (d - first).days / float(span - 1) * W
    delay = lambda frac: T0 + frac * DRAW

    # ---- the silence, measured rather than remembered ----
    gap_days, gap_from, gap_to = longest_gap(rows)
    sil_x = x_of(gap_from) / W * 100.0
    sil_w = (x_of(gap_to) - x_of(gap_from)) / W * 100.0

    # ---- milestone dots, placed on the curve at their real dates ----
    dots = []
    for m in json.loads((ROOT / "data" / "milestones.json").read_text(encoding="utf-8")):
        hits = sorted(set((d, s) for d, s in rows if s.startswith(m["match"])
                          and (not m.get("date") or str(d) == m["date"])))
        if len(hits) != 1:
            sys.exit("milestone %r matched %d commits, expected exactly 1%s"
                     % (m["match"], len(hits),
                        "; add a \"date\" to disambiguate" if len(hits) > 1 else ""))
        d, subject = hits[0]
        x = x_of(d)
        y, frac = at_x(pts, cum, x)
        edge = " edgeL" if x / W * 100 < 12 else (" edgeR" if x / W * 100 > 88 else "")
        if not m.get("go"):
            sys.exit("milestone %r has no \"go\"; every dot has to lead somewhere"
                     % m["match"])
        dots.append((x, '<a class="tl-d %s" href="%s" style="left:%.2f%%;top:%.2f%%;animation-delay:%.2fs">'
                        '<i></i><span class="tl-card %s%s"><em>%s</em><b>%s</b><code>%s</code></span></a>'
                        % (m["kind"], m["go"], x / W * 100, y / H * 100, delay(frac), m["place"], edge,
                           short(d), m["title"], subject)))
    dots.sort()

    # ---- chapter bands, counts and widths both derived ----
    chapters = json.loads((ROOT / "data" / "chapters.json").read_text(encoding="utf-8"))
    bands = []
    for i, c in enumerate(chapters):
        s = datetime.date.fromisoformat(c["start"])
        e = (datetime.date.fromisoformat(chapters[i + 1]["start"]) - datetime.timedelta(days=1)
             ) if i + 1 < len(chapters) else last
        n = sum(v for k, v in per.items() if s <= k <= e)
        days = (e - s).days + 1
        _, frac = at_x(pts, cum, x_of(s))
        cls = (' class="%s"' % c["class"]) if c.get("class") else ""
        bands.append('<div%s style="flex:%.2f;animation-delay:%.2fs">%s<br><b>%d</b></div>'
                     % (cls, days / float(span) * 100.0, delay(frac) + 0.05, c["name"], n))

    # ---- counters, pure CSS so the hero needs no script ----
    stats = [(len(rows), "commits", False), (span, "days", False),
             (gap_days, "days dark", True), (1, "person", False)]
    css, html = [], []
    for i, (val, label, dim) in enumerate(stats):
        v = "v%d" % i
        css.append("@property --%s { syntax:'<integer>'; initial-value:0; inherits:false }\n"
                   ".tl-stats div:nth-child(%d) b { --%s:%d; counter-reset:c var(--%s); animation:k%d 1.7s cubic-bezier(.15,.85,.25,1) %.2fs; }\n"
                   ".tl-stats div:nth-child(%d) b:after { content:counter(c) }\n"
                   "@keyframes k%d { from { --%s:0 } }"
                   % (v, i + 1, v, val, v, i, 0.35 + i * 0.08, i + 1, i, v))
        html.append('<div%s><b></b><span>%s</span></div>' % (' class="dim"' if dim else '', label))

    # ---- snow ----
    random.seed(7)
    snow = []
    for i in range(26):
        lay = i % 3
        size = [1.6, 2.3, 3.2][lay]; op = [.16, .26, .4][lay]
        dur = [26, 19, 14][lay] + random.random() * 7
        snow.append('<span style="left:%.1f%%;width:%spx;height:%spx;opacity:%s;animation-duration:%.1fs;'
                    'animation-delay:-%.1fs;--dx:%dpx"></span>'
                    % (random.random() * 100, size, size, op, dur, random.random() * dur,
                       random.randint(-40, 40)))

    headline = ("One person, %s commits, and a thing that learned to think."
                % "{:,}".format(len(rows)).replace(",", " hundred and ") if False else
                "One person, %d commits, and a thing that learned to think." % len(rows))
    subtitle = ("The line is commits per day across %d days, so drawing it in draws the real shape of the "
                "project. Hover any dot. The amber dot is the Architect. Every number here is read from the "
                "repository at build time." % span)
    meta = "%d commits &middot; %s to %s &middot; one person" % (len(rows), short(first), longd(last))

    tpl = (ROOT / "templates" / "home.tpl").read_text(encoding="utf-8")
    out = (tpl
        .replace("__POLY__", " ".join("%.1f,%.1f" % p for p in pts))
        .replace("__LEN__", "%.0f" % total_len)
        .replace("__SCANAT__", "%.1f" % (T0 + DRAW + 1.2))
        .replace("__DOTS__", "\n      ".join(d for _, d in dots))
        .replace("__BANDS__", "\n      ".join(bands))
        .replace("__SNOW__", "\n      ".join(snow))
        .replace("__SILX__", "%.2f" % sil_x).replace("__SILW__", "%.2f" % sil_w)
        .replace("__DARK__", str(gap_days))
        .replace("__META__", meta).replace("__HEADLINE__", headline).replace("__SUBTITLE__", subtitle)
        .replace("__STATS__", "".join(html)).replace("__COUNTERCSS__", "\n".join(css))
        .replace("__REPO__", REPO_URL)
        .replace("__ARC__", ARC).replace("__LAND__", LAND)
        .replace("__TRAV__", "%.1f" % TRAV).replace("__SPIN__", "%.1f" % SPIN)
        .replace("__SPINS__", "%.1f" % (TRAV / SPIN)))

    left = [tok for tok in ("__",) if "__" in out]
    if left:
        sys.exit("unfilled placeholders remain: " + str(set(__import__("re").findall(r"__[A-Z]+__", out))))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(out, encoding="utf-8")
    print("%s\n  %d commits, %s to %s, %d days"
          % (OUT, len(rows), first, last, span))
    print("  longest gap %d days, %s to %s" % (gap_days, gap_from, gap_to))
    print("  line length %.0f, %d dots, %d chapters" % (total_len, len(dots), len(bands)))


if __name__ == "__main__":
    main()
