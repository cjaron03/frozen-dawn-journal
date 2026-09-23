"""Write the commit history into the homepage.

Every number, position and duration on the graph is derived here from
data/commits.tsv. Nothing about the project's shape is typed by hand,
so a rebuild after new commits produces a correct page with no edits.
Hand authored input is limited to two small files: chapters.json (where
the chapter boundaries fall) and milestones.json (which commits are
worth a dot), and both are editorial choices, not facts about the repo.

The page itself, site/timeline.html, is hand written, and this only owns
the parts of it that are facts about the repo. Those sit between
build: markers and are replaced whole; everything outside them is left
exactly as it was found, so the page can be edited like any other and a
rebuild never undoes the edit. The exceptions are two numbers that sit
inside hand written text, the line's length, which the stylesheet needs
in seven places, and the day count in the page's working note, and those
are filled in where they stand rather than fenced.

    python3 pipeline/build.py           rewrite the page
    python3 pipeline/build.py --check   fail if the page is out of date
"""
import collections, datetime, difflib, html, json, math, pathlib, re, sys

ROOT = pathlib.Path(__file__).parent
PAGE = ROOT.parent / "site" / "timeline.html"

W, H     = 1000.0, 200.0   # stage viewBox
WEIGHT   = [7, 6, 5, 4, 3, 2, 1]   # trailing days, today weighted heaviest
T0, DRAW = 0.15, 3.6       # when the line starts, how long it takes
NARROW   = 3.5             # a band under this percentage of the width is too
                           # thin to hold its own name; see the bands below
FOLD_TO  = 8.0             # days of width the longest silence keeps, folded
ZOOM_DAYS, ZOOM = 28, 2.0  # the last four weeks, drawn twice as wide
# The width is time, with two marked exceptions, and both are in widths()
# below. On a plain calendar the chapter being written right now is the
# thinnest thing on the page: three chapters in three weeks came to about a
# ninth of the width, while forty two days with nothing in them took a fifth.
STAGE_H  = 238.0           # .tl-stage height in px, for the lifted dot stems;
                           # the stylesheet owns that number, so change both
RANK     = {"arch": 0, "arch2": 1, "maeve": 1, "major": 1, "minor": 2}
NEAR_X, NEAR_Y, LIFT = 24.0, 12.0, 28.0   # collision box and lift, in stage units
# LIFT is 28 because TAP_MIN below is 26. A stage unit is a pixel on the
# phone stage, so a step of 24 could never pull two dots sharing an x
# apart by the 26 the tap rule asks for: they climbed in lockstep until
# the ceiling stopped them, still crowded. A lift step has to clear a
# whole tap box or it cannot solve the thing it exists to solve.
# NEAR_Y is the moment two dots actually touch, not a comfortable gap: 12 stage
# units is 14.3px on the rendered stage, and the Architect dot with its halo
# measures 11px from centre to edge against a plain dot's 3.5px. Anything
# looser lifts dots that were never overlapping, and a lifted dot reads worse
# than a tight one.
#
# That box is in stage units, so it holds at every window width: the graph
# scales as one piece. Reach does not. On a phone the stage is 343px and the
# same two dots are a third as far apart under a finger, so the ones that are
# still targets there get measured again in millimetres. Which ones those are
# is decided by pointer-events in the stylesheet, and this set has to agree
# with it.
PHONE_W, PHONE_H = 343.0, 200.0
PHONE_LIVE = {"major", "arch", "arch2", "maeve"}
TAP_MIN  = 26.0            # px between two live targets on the phone stage
# 26 is the tap box itself, so it is the width at which two boxes stop
# overlapping at all and every pixel of the stage belongs to exactly one
# target. Picking any smaller number means picking how much overlap is
# tolerable, and there is no honest answer to that: the last version used
# 20, which left a pair sitting at 20.018px, clearing the bar by two
# hundredths of a pixel and only until the next commit shifted it.
CEIL     = 24.0            # stop climbing here, or the cards leave the stage

MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
def short(d):  return "%02d %s" % (d.day, MONTHS[d.month - 1])


def load():
    rows = []
    for line in (ROOT / "data" / "commits.tsv").read_text(encoding="utf-8").splitlines():
        if line.strip():
            date, added, removed, subject = line.split("\t", 3)
            rows.append((datetime.date.fromisoformat(date),
                         int(added), int(removed), subject))
    if not rows:
        sys.exit("no commits in data/commits.tsv, run fetch.py first")
    rows.sort()
    return rows


def widths(first, span, last, gap_from, gap_to):
    """Where each day sits across the stage, and how wide it is.

    Every day is the same width, except two runs that are marked on the page
    where they happen. The longest silence is folded down to FOLD_TO days of
    width under a bracket that still says how long it really was, since a
    flat line at zero reads the same at any length. The last ZOOM_DAYS are
    drawn ZOOM times as wide behind a seam that says so, because that is the
    part still being written and the part with the most dots on it. Order is
    never touched, only spacing, so every date still falls where it did
    relative to every other date.
    """
    inner = (gap_to - gap_from).days - 1
    fold = FOLD_TO / inner if inner > FOLD_TO else 1.0
    w = []
    for i in range(span):
        d = first + datetime.timedelta(days=i)
        k = fold if gap_from < d < gap_to else 1.0
        if (last - d).days < ZOOM_DAYS:
            k *= ZOOM
        w.append(k)
    # a day's centre is half its own width past the previous centre plus
    # half the previous width, so a wide day and a narrow one meet at their
    # shared edge; then the whole run is stretched so the first day sits at
    # 0 and the last at W, which is where the old even spacing put them.
    xs = [0.0]
    for i in range(1, span):
        xs.append(xs[-1] + (w[i - 1] + w[i]) / 2.0)
    k = W / xs[-1]
    return [x * k for x in xs], [x * k for x in w]


def curve(rows, first, span, xs):
    """How much code moved per day, smoothed, as a polyline in the stage viewBox."""
    per = collections.Counter(d for d, _a, _r, _s in rows)
    moved = collections.Counter()
    for d, added, removed, _s in rows:
        moved[d] += added + removed
    raw = [moved[first + datetime.timedelta(days=i)] for i in range(span)]
    # Lines, not commits. A commit is a habit, not a quantity. The crunch was
    # 261 commits averaging 148 lines and Homo Reliquus was 104 averaging 933,
    # so counting commits draws the smaller of the two as the mountain.
    # Trailing, not centred. A centred window lets a day's work lift the line on
    # the days BEFORE it was done, which on a journal is just false. Trailing
    # means each day shows the week behind it, so a return to work lands on its
    # real date.
    # The divisor is the whole window even at the start, because dividing by the
    # days actually available would hand day one a sevenfold bonus and make the
    # initial commit the tallest thing on the page.
    # Weighted toward today. A flat window splits one big day across seven, so
    # the day the Architect landed, the largest single day of the first six
    # weeks, drew as a dip because the five silent days before it were still in
    # the average. Weighting the near days heavier lets a day's own work show on
    # its own date while the week behind it still shapes the slope.
    span_w = float(sum(WEIGHT))
    sm = [sum(raw[i - k] * w for k, w in enumerate(WEIGHT) if i - k >= 0) / span_w
          for i in range(span)]
    # Square root, not linear. Linear height is honest about ratios and useless
    # about shape: 105 of these days are zero and 86 more sit under a tenth of
    # the peak, so nearly half the width draws as one flat line and every quiet
    # month looks like every other quiet month. A square root leaves the order
    # of the days untouched and gives the small ones somewhere to go.
    # Both layers divide by the same number, the largest single day, so the
    # grain and the line share one vertical axis and a spike standing above the
    # line really was a day bigger than the week around it.
    peak = float(max(max(raw), max(sm))) or 1.0
    y_of = lambda v: H - 18 - math.sqrt(v / peak) * (H - 40)
    pts = [(xs[i], y_of(v)) for i, v in enumerate(sm)]
    return pts, per, raw, y_of


def grain(raw, y_of, xs, ws):
    """One column per day at its true, unsmoothed height.

    The line is a week of work averaged into a shape. This is what the days
    themselves looked like: the single biggest day of the project moved 7,920
    lines and the smoothed line draws it at a quarter of that, because the six
    days around it were quiet. The columns tile the full width, so the 105 days
    with no commit at all read as gaps rather than as a low flat run.
    """
    base = H - 18
    return "".join("M%.2f %.1fh%.2fV%.1fH%.2fZ"
                   % (xs[i] - ws[i] / 2.0, y_of(v), ws[i], base, xs[i] - ws[i] / 2.0)
                   for i, v in enumerate(raw) if v)


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
    days = sorted(set(r[0] for r in rows))
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
    gap_days, gap_from, gap_to = longest_gap(rows)
    xs, ws = widths(first, span, last, gap_from, gap_to)
    pts, per, raw, y_of = curve(rows, first, span, xs)
    cum = arclen(pts)
    total_len = cum[-1]
    x_of = lambda d: xs[(d - first).days]
    delay = lambda frac: T0 + frac * DRAW

    # ---- the silence, measured rather than remembered ----
    sil_x = x_of(gap_from) / W * 100.0
    sil_w = (x_of(gap_to) - x_of(gap_from)) / W * 100.0

    # ---- the seam where the last weeks start drawing wider ----
    z = max(0, span - ZOOM_DAYS)
    zoom_x = (xs[z - 1] + xs[z]) / 2.0 / W * 100.0 if z else None
    zoom_t = delay(at_x(pts, cum, zoom_x / 100.0 * W)[1]) if z else 0

    # ---- milestone dots, placed on the curve at their real dates ----
    marks = []
    for m in json.loads((ROOT / "data" / "milestones.json").read_text(encoding="utf-8")):
        hits = sorted(set((d, s) for d, _a, _r, s in rows if s.startswith(m["match"])
                          and (not m.get("date") or str(d) == m["date"])))
        if len(hits) != 1:
            sys.exit("milestone %r matched %d commits, expected exactly 1%s"
                     % (m["match"], len(hits),
                        "; add a \"date\" to disambiguate" if len(hits) > 1 else ""))
        d, subject = hits[0]
        x = x_of(d)
        y, frac = at_x(pts, cum, x)
        if not m.get("go"):
            sys.exit("milestone %r has no \"go\"; every dot has to lead somewhere"
                     % m["match"])
        marks.append({"x": x, "y": y, "frac": frac, "m": m, "d": d,
                      "subject": subject, "lift": 0.0})
    marks.sort(key=lambda k: k["x"])

    # Milestones a couple of days apart land on top of each other, and a dot
    # is a 26px tap box however small it draws. Where a crowd forms the
    # quieter dots climb a row at a time until they are clear, each keeping a
    # stem down to where it really sits, so nothing moves in time, only out of
    # the way.
    #
    # Crowding is measured where the dots have ended up rather than where they
    # started, so a dot already moved aside does not drag its neighbour up
    # with it, and a third dot in the same crowd takes a row of its own
    # instead of the one already occupied. That second part is why this
    # relaxes in rounds instead of deciding each pair once.
    def crowded(a, b):
        # measured where the dots have ended up, not where they started, so a
        # dot already moved out of the way does not drag its neighbour up too.
        dx = b["x"] - a["x"]
        dy = (b["y"] - b["lift"]) - (a["y"] - a["lift"])
        if abs(dx) < NEAR_X and abs(dy) < NEAR_Y:
            return True          # they overlap on screen, at any width
        if a["m"]["kind"] in PHONE_LIVE and b["m"]["kind"] in PHONE_LIVE:
            # diagonal distance, because two dots offset on both axes are two
            # targets even when neither axis alone says so.
            return math.hypot(dx / W * PHONE_W, dy / H * PHONE_H) < TAP_MIN
        return False

    # The first dot is where the line starts, and a line whose first dot
    # floats above its own beginning reads as starting from nowhere. So it
    # is pinned, and a crowd it is part of simply stays crowded, the same
    # way a crowd with no headroom left does. Today that is the origin and
    # the Architect at 23px: their boxes overlap by three pixels at the far
    # left edge, where one of the two wears a halo and the other is the
    # first thing on the graph. Nobody misses which is which.
    #
    # Every pair, not just neighbours in date order. On a phone the dots that
    # are still targets have quiet ones sitting between them, so a crowd's two
    # halves can be three dots apart in this list and still land on the same
    # square centimetre of glass.
    for _ in range(len(marks)):
        moved = False
        for i, a in enumerate(marks):
            for b in marks[i + 1:]:
                if not crowded(a, b):
                    continue
                # a dot already off the line climbs again in preference to
                # pushing its neighbour off too: the second step costs nothing
                # but stem, while moving the neighbour costs a whole new one.
                # only then does rank decide, and equal rank sends the later
                # dot up, so the older milestone keeps its place.
                if bool(a["lift"]) != bool(b["lift"]):
                    lo = a if a["lift"] else b
                else:
                    lo = a if RANK[a["m"]["kind"]] > RANK[b["m"]["kind"]] else b
                if lo is marks[0]:
                    continue      # see below: the first dot does not move
                if lo["y"] - lo["lift"] - LIFT < CEIL:
                    continue      # out of headroom, so it stays crowded
                lo["lift"] += LIFT
                moved = True
        if not moved:
            break

    dots = []
    for k in marks:
        m, x, y = k["m"], k["x"], k["y"]
        edge = " edgeL" if x / W * 100 < 12 else (" edgeR" if x / W * 100 > 88 else "")
        stem = ('<u style="height:%.1fpx"></u>' % (k["lift"] / H * STAGE_H)) if k["lift"] else ""
        # a lift takes away the room a card above the dot was relying on, and
        # it takes it from the one direction that matters, so a dot that has
        # been moved opens its card downward whatever the file asked for.
        # place is an editorial choice about which side reads better, not a
        # claim that there is space on that side.
        place = "below" if k["lift"] else m["place"]
        dots.append((x, '<a class="tl-d %s" href="%s" style="left:%.2f%%;top:%.2f%%;animation-delay:%.2fs">'
                        '<i></i>%s<span class="tl-card %s%s"><em>%s</em><b>%s</b><code>%s</code></span></a>'
                        % (m["kind"], m["go"], x / W * 100, (y - k["lift"]) / H * 100,
                           delay(k["frac"]), stem, place, edge,
                           short(k["d"]), m["title"], html.escape(k["subject"], quote=False))))

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
        a, b = (s - first).days, (e - first).days
        flex = sum(ws[a:b + 1]) / sum(ws) * 100.0
        # a chapter a few days old is a sliver, and its name is wider than
        # its band. Rather than let the name shove the band wider and knock
        # every boundary out of line with the graph above, a narrow band keeps
        # its true width and hangs its label off the right hand edge, one row
        # down, clear of its neighbour's. As the chapter grows past NARROW it
        # goes back to being labelled like the rest.
        cls = " ".join(filter(None, [c.get("class"), "n" if flex < NARROW else ""]))
        cls = (' class="%s"' % cls) if cls else ""
        label = ("<span>%s <b>%d</b></span>" if flex < NARROW else "%s<br><b>%d</b>") % (c["name"], n)
        bands.append('<div%s style="flex:%.2f;animation-delay:%.2fs">%s</div>'
                     % (cls, flex, delay(frac) + 0.05, label))

    # ---- counters, pure CSS so the hero needs no script ----
    stats = [len(rows), span, gap_days, 1]   # commits, days, days dark, person
    css = []
    for i, val in enumerate(stats):
        v = "v%d" % i
        css.append("@property --%s { syntax:'<integer>'; initial-value:0; inherits:false }\n"
                   ".tl-stats div:nth-child(%d) b { --%s:%d; counter-reset:c var(--%s); animation:k%d 1.7s cubic-bezier(.15,.85,.25,1) %.2fs; }\n"
                   ".tl-stats div:nth-child(%d) b:after { content:counter(c) }\n"
                   "@keyframes k%d { from { --%s:0 } }"
                   % (v, i + 1, v, val, v, i, 0.35 + i * 0.08, i + 1, i, v))

    poly = " ".join("%.1f,%.1f" % p for p in pts)
    regions = {
        "line": ['<path class="tl-grain" d="%s"/>' % grain(raw, y_of, xs, ws)] +
                ['<polyline class="tl-%s" points="%s"/>' % (c, poly)
                 for c in ("glow", "trace", "scan")],
        "dots": [d for _, d in dots] +
                ['<div class="tl-sil" style="left:%.2f%%;width:%.2f%%"><div></div><span>%d days, folded</span></div>'
                 % (sil_x, sil_w, gap_days)] +
                (['<div class="tl-zm" style="left:%.2f%%;animation-delay:%.2fs"><span>last %d weeks, %g&times; wide</span></div>'
                  % (zoom_x, zoom_t, ZOOM_DAYS // 7, ZOOM)] if zoom_x is not None else []),
        "bands": bands,
        "counters": "\n".join(css).split("\n"),
    }
    length = "%.0f" % total_len
    slots = [  # (what, pattern, value, how many times it has to appear)
        ("line length", r"(?<=stroke-dasharray:)\d+(?=; stroke-dashoffset:\d+; animation:tldraw)", length, 2),
        ("line length", r"(?<=stroke-dashoffset:)\d+(?=; animation:tldraw)", length, 2),
        ("line length", r"(?<=stroke-dasharray:52 )\d+(?=;)", length, 1),
        ("line length", r"(?<=stroke-dashoffset:-)\d+(?= })", length, 2),
        ("day span",    r"(?<=each day across )\d+(?= days)", str(span), 1),
    ]

    page = PAGE.read_text(encoding="utf-8")
    out = page
    for name, lines in regions.items():
        # either comment syntax, since three of these are markup and one is CSS
        fence = re.compile(r"^([ \t]*)(?:<!--|/\*) build:%s (?:-->|\*/)\n"
                           r"(.*?)^[ \t]*(?:<!--|/\*) /build:%s (?:-->|\*/)$" % (name, name),
                           re.S | re.M)
        found = list(fence.finditer(out))
        if len(found) != 1:
            sys.exit("%s: expected one build:%s region, found %d" % (PAGE, name, len(found)))
        m = found[0]
        body = "".join(m.group(1) + ln + "\n" for ln in lines)
        out = out[:m.start(2)] + body + out[m.end(2):]
    for what, pat, val, want in slots:
        out, n = re.subn(pat, val, out)
        if n != want:
            sys.exit("%s: the %s appears %d times, expected %d; a hand edit moved "
                     "one of the anchors in pipeline/build.py" % (PAGE, what, n, want))

    print("%s\n  %d commits, %s to %s, %d days"
          % (PAGE.relative_to(ROOT.parent), len(rows), first, last, span))
    print("  longest gap %d days, %s to %s" % (gap_days, gap_from, gap_to))
    print("  line length %s, %d dots, %d chapters" % (length, len(dots), len(bands)))

    if out == page:
        print("  already up to date")
    elif "--check" in sys.argv[1:]:
        sys.stdout.writelines(list(difflib.unified_diff(
            page.splitlines(True), out.splitlines(True),
            "site/timeline.html", "what build.py would write", n=0))[:40])
        sys.exit("site/timeline.html is out of date: run python3 pipeline/build.py")
    else:
        PAGE.write_text(out, encoding="utf-8")
        print("  rewritten")


if __name__ == "__main__":
    main()
