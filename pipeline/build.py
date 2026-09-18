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
WEIGHT   = [7, 6, 5, 4, 3, 2, 1]   # trailing days, today weighted heaviest
T0, DRAW = 0.15, 3.6       # when the line starts, how long it takes
TRAV     = 72.0            # seconds for Earth to cross the header
SPIN     = 7.0             # seconds per rotation
ARC      = "M 34 46 C 250 14, 640 11, 1078 40"
STAGE_H  = 238.0           # .tl-stage height in px, for the lifted dot stems
RANK     = {"arch": 0, "maeve": 0, "arch2": 1, "major": 1, "minor": 2}
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
            date, added, removed, subject = line.split("\t", 3)
            rows.append((datetime.date.fromisoformat(date),
                         int(added), int(removed), subject))
    if not rows:
        sys.exit("no commits in data/commits.tsv, run fetch.py first")
    rows.sort()
    return rows


def curve(rows, first, span):
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
    pts = [(i / float(span - 1) * W, y_of(v)) for i, v in enumerate(sm)]
    return pts, per, raw, y_of


def grain(raw, y_of):
    """One column per day at its true, unsmoothed height.

    The line is a week of work averaged into a shape. This is what the days
    themselves looked like: the single biggest day of the project moved 7,920
    lines and the smoothed line draws it at a quarter of that, because the six
    days around it were quiet. The columns tile the full width, so the 105 days
    with no commit at all read as gaps rather than as a low flat run.
    """
    span = len(raw)
    step = W / float(span - 1)
    base = H - 18
    return "".join("M%.2f %.1fh%.2fV%.1fH%.2fZ"
                   % (i * step - step / 2.0, y_of(v), step, base, i * step - step / 2.0)
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
    pts, per, raw, y_of = curve(rows, first, span)
    cum = arclen(pts)
    total_len = cum[-1]
    x_of = lambda d: (d - first).days / float(span - 1) * W
    delay = lambda frac: T0 + frac * DRAW

    # ---- the silence, measured rather than remembered ----
    gap_days, gap_from, gap_to = longest_gap(rows)
    sil_x = x_of(gap_from) / W * 100.0
    sil_w = (x_of(gap_to) - x_of(gap_from)) / W * 100.0

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
                # Maeve's dots are hidden until the page is unlocked, so
                # they are not allowed to push a visible dot anywhere. A
                # public dot moved out of the way of something nobody can see
                # reads as a dot floating for no reason, with a stem pointing
                # at empty line. The secret pays for its own crowding: when
                # one of a pair is Maeve's, that is the one that climbs, and
                # the locked graph is laid out as though she were not there.
                if (a["m"]["kind"] == "maeve") != (b["m"]["kind"] == "maeve"):
                    lo = a if a["m"]["kind"] == "maeve" else b
                # a dot already off the line climbs again in preference to
                # pushing its neighbour off too: the second step costs nothing
                # but stem, while moving the neighbour costs a whole new one.
                # only then does rank decide, and equal rank sends the later
                # dot up, so the older milestone keeps its place.
                elif bool(a["lift"]) != bool(b["lift"]):
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
                           short(k["d"]), m["title"], k["subject"])))

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
    subtitle = ("The line is how much code moved each day across %d days, so drawing it in draws the real "
                "shape of the project. Hover a dot to read the commit, click it to open the chapter. The "
                "amber dots are the Architect. Every number here is read from the repository at build "
                "time." % span)
    meta = "%d commits &middot; %s to %s &middot; one person" % (len(rows), short(first), longd(last))

    tpl = (ROOT / "templates" / "home.tpl").read_text(encoding="utf-8")
    out = (tpl
        .replace("__POLY__", " ".join("%.1f,%.1f" % p for p in pts))
        .replace("__LEN__", "%.0f" % total_len)
        .replace("__SCANAT__", "%.1f" % (T0 + DRAW + 1.2))
        .replace("__GRAIN__", grain(raw, y_of))
        .replace("__GRAINAT__", "%.2f" % (T0 + DRAW + 0.15))
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
