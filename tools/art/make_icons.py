#!/usr/bin/env python3
"""Draw the journal's icon, its social card, and a card for each chapter.

The icon and the main card are the same object: the Earth from the
homepage, caught partway through the freeze. The colours and the freeze
keyframes are lifted from the <g class="tl-earth"> group in
site/timeline.html so the icon and the page it belongs to cannot drift
apart. The chapter cards share its type and layout, and each carries one
thing out of its own chapter.

    python3 tools/art/make_icons.py
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parent.parent.parent
OUT = ROOT / "site" / "assets"
SS = 4  # supersample, then downscale. cheap antialiasing.

BG    = (15, 18, 22)
OCEAN = (43, 116, 168)
LAND  = (79, 156, 100)
CAP   = (234, 244, 251)
FROST = (207, 226, 240)
DARK  = (4, 6, 11)
SUN   = (255, 220, 120)
ICE   = (125, 211, 252)
HEAD  = (242, 246, 248)
MUTED = (124, 136, 145)
DIM   = (90, 102, 114)
PATH  = (44, 104, 138)

# the animate keyframes, verbatim from the homepage.
GREEN  = ([0, .3, .45, .62, .85, 1], [1, 1, .85, .45, .1, .05])
CAPRY  = ([0, .3, .5, .7, .88, 1], [1.1, 2.2, 4.6, 7.2, 9, 9])
FROSTO = ([0, .3, .5, .7, .88, 1], [0, .05, .3, .68, .92, .95])
DARKO  = ([0, .5, .68, .82, .94, 1], [0, 0, .1, .42, .7, .78])


def at(frames, t):
    ks, vs = frames
    for i in range(len(ks) - 1):
        if ks[i] <= t <= ks[i + 1]:
            span = ks[i + 1] - ks[i]
            f = 0 if span == 0 else (t - ks[i]) / span
            return vs[i] + (vs[i + 1] - vs[i]) * f
    return vs[-1]


def veil(base, disc, rgb, alpha):
    """Lay a flat colour over the disc at the given opacity.

    paste() takes its alpha from the mask and ignores the layer's own, so
    the opacity has to be folded into the mask or the veil lands solid.
    """
    if alpha <= 0:
        return
    m = disc.point(lambda v, a=alpha: int(v * a))
    base.paste(Image.new("RGBA", base.size, rgb + (255,)), (0, 0), m)


def earth(size, t, shade=True):
    """The planet as an RGBA tile of the given size, frozen to position t."""
    s = size * SS
    r = s / 2
    k = r / 9.0  # the homepage draws this at r=9.

    disc = Image.new("L", (s, s), 0)
    ImageDraw.Draw(disc).ellipse([0, 0, s - 1, s - 1], fill=255)

    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse([0, 0, s - 1, s - 1], fill=OCEAN + (255,))

    # the landmasses, fading out as the ice takes them.
    g = at(GREEN, t)
    if g > 0.02:
        land = Image.new("RGBA", (s, s), (0, 0, 0, 0))
        ld = ImageDraw.Draw(land)
        for bx, by, bw, bh in ((-7.2, -4.4, 5.6, 4.4), (1.1, -1.3, 6.2, 5.2),
                               (-3.3, 4.2, 4.4, 3.0), (5.4, -6.1, 3.6, 2.6)):
            x0, y0 = r + bx * k, r + by * k
            ld.ellipse([x0, y0, x0 + bw * k, y0 + bh * k], fill=LAND + (255,))
        m = land.split()[3].point(lambda v, a=g: int(v * a))
        m = Image.composite(m, Image.new("L", (s, s), 0), disc)
        im.paste(land, (0, 0), m)
        d = ImageDraw.Draw(im)

    # the polar caps grow from both poles until they meet in the middle.
    ry = at(CAPRY, t) * k
    caps = Image.new("L", (s, s), 0)
    cd = ImageDraw.Draw(caps)
    for cy in (0, s):
        cd.ellipse([0, cy - ry, s - 1, cy + ry], fill=255)
    im.paste(Image.new("RGBA", (s, s), CAP + (255,)), (0, 0),
             Image.composite(caps, Image.new("L", (s, s), 0), disc))

    veil(im, disc, FROST, at(FROSTO, t))
    veil(im, disc, DARK, at(DARKO, t))

    if shade:
        # light from the upper left, terminator falling away to the lower
        # right. this is the gshade gradient the homepage lays over the top.
        sh = Image.new("L", (s, s), 0)
        sd = ImageDraw.Draw(sh)
        steps, lx, ly = 64, r * 0.62, r * 0.58
        for i in range(steps, 0, -1):
            rad = r * 2.35 * i / steps
            v = int(175 * (i / steps) ** 1.8)
            sd.ellipse([lx - rad, ly - rad, lx + rad, ly + rad], fill=v)
        sh = sh.filter(ImageFilter.GaussianBlur(s / 22))
        im.paste(Image.new("RGBA", (s, s), DARK + (255,)), (0, 0),
                 Image.composite(sh, Image.new("L", (s, s), 0), disc))

    return im.resize((size, size), Image.LANCZOS)


def font(name, size):
    for p in (f"/System/Library/Fonts/{name}",
              f"/System/Library/Fonts/Supplemental/{name}"):
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except OSError:
                pass
    return ImageFont.load_default(size)


def tracked(d, xy, text, f, fill, track=0.0):
    """Draw text with letter spacing, which PIL has no setting for."""
    x, y = xy
    for ch in text:
        d.text((x, y), ch, font=f, fill=fill)
        x += d.textlength(ch, font=f) + track
    return x - xy[0]


def bezier(p0, p1, p2, p3, n=260):
    pts = []
    for i in range(n + 1):
        t = i / n
        u = 1 - t
        pts.append((u**3 * p0[0] + 3*u*u*t * p1[0] + 3*u*t*t * p2[0] + t**3 * p3[0],
                    u**3 * p0[1] + 3*u*u*t * p1[1] + 3*u*t*t * p2[1] + t**3 * p3[1]))
    return pts


def card():
    """1200x630, the size every unfurler crops to."""
    W, H = 1200, 630
    im = Image.new("RGBA", (W, H), BG + (255,))

    # the sun, held low and left, the way the homepage opens.
    cx, cy = 176, 250
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for rad, a in ((250, 9), (165, 15), (98, 24), (52, 52)):
        gd.ellipse([cx - rad, cy - rad, cx + rad, cy + rad], fill=SUN + (a,))
    im = Image.alpha_composite(im, glow.filter(ImageFilter.GaussianBlur(30)))
    d = ImageDraw.Draw(im)
    # the drift path. it leaves, and it does not come back.
    pts = bezier((cx, cy), (440, 128), (790, 142), (1152, 268))
    for i in range(len(pts) - 1):
        f = i / (len(pts) - 1)
        d.line([pts[i], pts[i + 1]], fill=PATH + (int(34 + 165 * f),), width=3)
    d.ellipse([cx - 18, cy - 18, cx + 18, cy + 18], fill=SUN + (240,))

    # earth, three quarters of the way out and most of the way frozen.
    ex, ey = pts[int(0.735 * (len(pts) - 1))]
    size = 132
    im.alpha_composite(earth(size, 0.58), (int(ex - size / 2), int(ey - size / 2)))
    d = ImageDraw.Draw(im)

    # the masthead, set the way the page sets it.
    x = 86
    fb, fi = font("SFNS.ttf", 31), font("SFNS.ttf", 19)
    w = tracked(d, (x, 74), "Frozen Dawn", fb, HEAD)
    tracked(d, (x + w + 17, 86), "DEV JOURNAL", fi, MUTED, 1.2)

    fh = font("SFNS.ttf", 53)
    d.text((x, 420), "One person, hundreds of commits,", font=fh, fill=HEAD)
    d.text((x, 420 + 64), "and a thing that learned to think.", font=fh, fill=HEAD)

    # nothing here that an image cannot keep true. no commit tally, because
    # it moves every day, and no address, because a move to a real domain is
    # the one change a baked in address could not follow. every surface that
    # shows this card shows the link beside it anyway.

    OUT.mkdir(parents=True, exist_ok=True)
    im.convert("RGB").save(OUT / "social-card.png", optimize=True)


def banner():
    """1200x260, for the mod's README. Same scene, laid on its side.

    The README shows it at width 900, and the whole image is one link, so
    the only job the type has is to say what it opens.
    """
    W, H = 1200, 260
    im = Image.new("RGBA", (W, H), BG + (255,))

    cx, cy = 52, 34
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for rad, a in ((200, 8), (130, 13), (76, 21), (40, 46)):
        gd.ellipse([cx - rad, cy - rad, cx + rad, cy + rad], fill=SUN + (a,))
    im = Image.alpha_composite(im, glow.filter(ImageFilter.GaussianBlur(26)))
    d = ImageDraw.Draw(im)
    # the arc is routed high over the type, so the words keep the left side
    # and the planet keeps the right.
    pts = bezier((cx, cy), (380, 2), (770, 34), (1148, 156))
    for i in range(len(pts) - 1):
        f = i / (len(pts) - 1)
        d.line([pts[i], pts[i + 1]], fill=PATH + (int(30 + 165 * f),), width=3)
    d.ellipse([cx - 12, cy - 12, cx + 12, cy + 12], fill=SUN + (240,))

    ex, ey = pts[int(0.80 * (len(pts) - 1))]
    size = 96
    im.alpha_composite(earth(size, 0.58), (int(ex - size / 2), int(ey - size / 2)))
    d = ImageDraw.Draw(im)

    x = 62
    fb, fi = font("SFNS.ttf", 30), font("SFNS.ttf", 18)
    w = tracked(d, (x, 92), "Frozen Dawn", fb, HEAD)
    tracked(d, (x + w + 16, 103), "DEV JOURNAL", fi, MUTED, 1.2)

    fs = font("SFNS.ttf", 21)
    d.text((x, 140), "How one person built a world that freezes, and a thing\n"
                     "that learned to think.".replace("\n", " "),
           font=fs, fill=(150, 161, 170))

    # the whole banner is a link, so this says where it goes rather than
    # naming an address that would have to be redrawn to change.
    fc = font("SFNS.ttf", 15)
    tracked(d, (x, 184), "READ THE DEV JOURNAL", fc, ICE, 1.6)

    OUT.mkdir(parents=True, exist_ok=True)
    im.convert("RGB").save(OUT / "journal-banner.png", optimize=True)


def icons():
    OUT.mkdir(parents=True, exist_ok=True)
    # a touch further into the freeze than the card, so the caps still read
    # once this is sixteen pixels wide in a browser tab.
    for px in (32, 180, 512):
        earth(px, 0.60).save(OUT / f"icon-{px}.png", optimize=True)
    # the tab icon wants a little air or it looks larger than its neighbours.
    ico = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    ico.alpha_composite(earth(60, 0.60), (2, 2))
    ico.resize((32, 32), Image.LANCZOS).save(OUT / "favicon-32.png", optimize=True)


def glow(im, cx, cy, rgb, rings, blur, sy=1.0):
    """A soft light, as stacked ellipses blurred together."""
    g = Image.new("RGBA", im.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(g)
    for rad, a in rings:
        gd.ellipse([cx - rad, cy - rad * sy, cx + rad, cy + rad * sy], fill=rgb + (a,))
    return Image.alpha_composite(im, g.filter(ImageFilter.GaussianBlur(blur)))


def eyes(im, cx, cy, p, rows, bloom=True):
    """The pair of eyes the Architect and the Returned share: each one two
    texture pixels wide and three tall, one pixel apart, a colour per row.
    p is the size of one texture pixel on the card."""
    x0, y0 = cx - 2.5 * p, cy - 1.5 * p
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)
    for ex in (x0, x0 + 3 * p):
        for i, rgb in enumerate(rows):
            ld.rectangle([ex, y0 + i * p, ex + 2 * p - 1, y0 + (i + 1) * p - 1], fill=rgb + (255,))
    if bloom:
        im = Image.alpha_composite(im, lay.filter(ImageFilter.GaussianBlur(max(2, p * .7))))
    return Image.alpha_composite(im, lay)


ARCH = ((0, 140, 180), (0, 210, 255), (0, 80, 100))       # architect.png
RETD = ((122, 95, 168), (169, 140, 216), (74, 56, 102))    # maeve.html, the lids
AMBER = (255, 180, 84)
VIOLET = (169, 140, 216)


def m_phases(im):
    # the drift path again, with the planet caught at each of the six phases.
    cx, cy = 150, 246
    im = glow(im, cx, cy, SUN, ((230, 9), (150, 15), (90, 24), (48, 52)), 30)
    d = ImageDraw.Draw(im)
    pts = bezier((cx, cy), (430, 118), (800, 128), (1164, 262))
    for i in range(len(pts) - 1):
        f = i / (len(pts) - 1)
        d.line([pts[i], pts[i + 1]], fill=PATH + (int(34 + 165 * f),), width=3)
    d.ellipse([cx - 16, cy - 16, cx + 16, cy + 16], fill=SUN + (240,))
    for n in range(6):
        ex, ey = pts[int((.34 + n * .118) * (len(pts) - 1))]
        size = 58 + n * 6
        im.alpha_composite(earth(size, n / 5), (int(ex - size / 2), int(ey - size / 2)))
    return im


def m_architect(im):
    cx, cy = 884, 214
    im = glow(im, cx, cy, ARCH[1], ((280, 12), (170, 22), (90, 38)), 44, .62)
    return eyes(im, cx, cy, 36, ARCH)


def m_orsa(im):
    # the real masthead from the mod, with its three gold bars slid home.
    art = ROOT / "site" / "assets" / "ch3"
    m = Image.open(art / "orsa-base.png").convert("RGBA")
    for key, x, y in (("tl", 0, 214), ("tr", 408, 214), ("ml", 0, 241),
                      ("mr", 408, 241), ("bl", 0, 266), ("br", 408, 266)):
        m.alpha_composite(Image.open(art / f"orsa-{key}.png").convert("RGBA"), (x, y))
    w = 480
    m = m.resize((w, round(m.height * w / m.width)), Image.LANCZOS)
    # the texture sits on solid black. feather its edges so the box dissolves
    # into the card rather than reading as a sticker on top of it.
    edge = Image.new("L", m.size, 0)
    ImageDraw.Draw(edge).rectangle([34, 30, m.width - 35, m.height - 31], fill=255)
    edge = edge.filter(ImageFilter.GaussianBlur(16))
    m.putalpha(Image.composite(m.getchannel("A"), Image.new("L", m.size, 0), edge))
    cx, cy = 880, 208
    im = glow(im, cx, cy, AMBER, ((260, 7), (160, 12)), 48, .55)
    im.alpha_composite(m, (cx - m.width // 2, cy - m.height // 2))
    return im


def m_rooms(im):
    # a block of rooms, one of them held above freezing, the warmth thinning
    # out through the walls around it.
    cols, rows, t, gap = 9, 4, 46, 8
    x0, y0 = 646, 102
    hx, hy = 5, 1
    im = glow(im, x0 + hx * (t + gap) + t / 2, y0 + hy * (t + gap) + t / 2,
              AMBER, ((150, 16), (80, 34)), 30)
    # drawn on a layer of its own. ImageDraw writes alpha straight into the
    # pixels rather than blending, so faint fills would otherwise land solid.
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for c in range(cols):
        for r in range(rows):
            dist = ((c - hx) ** 2 + (r - hy) ** 2) ** .5
            w = max(0.0, 1 - dist / 2.6)
            x, y = x0 + c * (t + gap), y0 + r * (t + gap)
            if dist == 0:
                d.rectangle([x, y, x + t, y + t], fill=AMBER + (255,))
                continue
            rgb = tuple(int(ICE[i] + (AMBER[i] - ICE[i]) * w) for i in range(3))
            d.rectangle([x, y, x + t, y + t], fill=rgb + (int(14 + 60 * w),),
                        outline=rgb + (int(70 + 140 * w),), width=2)
    return Image.alpha_composite(im, lay)


def m_crystal(im):
    # what the cold made, drawn the way the cold draws.
    import math
    cx, cy, R = 884, 214, 128
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)
    for k in range(6):
        a = math.radians(90 + k * 60)
        ux, uy = math.cos(a), -math.sin(a)
        ld.line([cx, cy, cx + ux * R, cy + uy * R], fill=ICE + (255,), width=5)
        for f, L in ((.36, 42), (.62, 34), (.84, 20)):
            bx, by = cx + ux * R * f, cy + uy * R * f
            for s in (-1, 1):
                b = a + s * math.radians(60)
                ld.line([bx, by, bx + math.cos(b) * L, by - math.sin(b) * L],
                        fill=ICE + (255,), width=4)
    im = glow(im, cx, cy, ICE, ((170, 10), (90, 18)), 36)
    im = Image.alpha_composite(im, lay.filter(ImageFilter.GaussianBlur(6)))
    return Image.alpha_composite(im, lay)


def m_stayed(im):
    # a hearth, and the ones still sitting at the edge of its light.
    hx, hy = 884, 318
    im = glow(im, hx, hy, AMBER, ((230, 14), (130, 26), (60, 60), (22, 140)), 24, .45)
    ImageDraw.Draw(im).ellipse([hx - 9, hy - 5, hx + 9, hy + 5], fill=(255, 226, 170, 255))
    for x, y, p in ((706, 214, 13), (1064, 196, 12), (884, 150, 16)):
        im = glow(im, x, y, VIOLET, ((p * 5, 30),), p)
        im = eyes(im, x, y, p, RETD)
    return im


def m_home(im):
    # the planet at the far end of its drift, and a way back towards the sun.
    sx, sy = 600, 96
    im = glow(im, sx, sy, SUN, ((110, 12), (54, 30)), 20)
    d = ImageDraw.Draw(im)
    d.ellipse([sx - 9, sy - 9, sx + 9, sy + 9], fill=SUN + (230,))
    ex, ey, size = 1046, 262, 150
    pts = bezier((ex - 40, ey - 60), (950, 120), (820, 80), (sx + 30, sy + 8))
    n = len(pts) - 1
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)
    for i in range(int(.62 * n)):
        f = i / (.62 * n)
        ld.line([pts[i], pts[i + 1]], fill=AMBER + (int(70 + 185 * f),), width=3)
    im = Image.alpha_composite(im, lay)
    hx, hy = pts[int(.62 * n)]
    im = glow(im, hx, hy, AMBER, ((26, 60), (12, 120)), 8)
    ImageDraw.Draw(im).ellipse([hx - 5, hy - 5, hx + 5, hy + 5], fill=(255, 236, 200, 255))
    im.alpha_composite(earth(size, .94), (ex - size // 2, ey - size // 2))
    return im


def m_maeve(im):
    # the Master, and the five Returned she can hold her attention on at once.
    cx, cy = 884, 176
    im = glow(im, cx, cy, VIOLET, ((250, 12), (150, 22), (80, 34)), 42, .6)
    im = eyes(im, cx, cy, 26, RETD)
    for x, y, p in ((702, 300, 7), (806, 326, 9), (962, 338, 10),
                    (1070, 302, 8), (1146, 244, 6)):
        im = glow(im, x, y, VIOLET, ((p * 5, 26),), p)
        im = eyes(im, x, y, p, RETD)
    return im


# one card per chapter: (built page, hook, accent, background, motif). the
# numeral and title come from the nav in tools/build.py, so a renamed
# chapter only has to be renamed once.
CHAPTERS = [
    ("chapter-1.html", "Vacuum, cold, snow. Six phases, and the world does not wait.",
     ICE, BG, m_phases),
    ("architect.html", "The decision loop, the mistakes, and a simulation you can run.",
     ARCH[1], BG, m_architect),
    ("chapter-3.html", "ORSA promised continuity and delivered an evacuation.",
     AMBER, BG, m_orsa),
    ("chapter-4.html", "Heaters, capacitors and sealed rooms. One room above freezing.",
     AMBER, BG, m_rooms),
    ("chapter-5.html", "Frostbitten, Hollows, Mimics and Frostmites.",
     ICE, BG, m_crystal),
    ("chapter-6.html", "ORSA left. Humanity left. They stayed.",
     VIOLET, BG, m_stayed),
    ("chapter-7.html", "Warmth begins as life and ends as fuel.",
     AMBER, BG, m_home),
    ("director.html", "The director that learns how you play.",
     VIOLET, (20, 15, 29), m_maeve),
]


def cards():
    import sys
    sys.path.insert(0, str(ROOT / "tools"))
    from build import PAGES
    label = {out: lab for _, out, lab in PAGES}
    (OUT / "cards").mkdir(parents=True, exist_ok=True)
    W, H = 1200, 630
    for out, hook, acc, bg, motif in CHAPTERS:
        num, title = label[out].split(". ", 1)
        im = motif(Image.new("RGBA", (W, H), bg + (255,)))
        d = ImageDraw.Draw(im)
        x = 86
        fb, fi = font("SFNS.ttf", 31), font("SFNS.ttf", 19)
        w = tracked(d, (x, 74), "Frozen Dawn", fb, HEAD)
        tracked(d, (x + w + 17, 86), "DEV JOURNAL", fi, MUTED, 1.2)
        tracked(d, (x, 392), f"CHAPTER {num}", font("SFNS.ttf", 18), acc, 2.6)
        d.text((x, 418), title, font=font("SFNS.ttf", 62), fill=HEAD)
        d.text((x, 506), hook, font=font("SFNS.ttf", 27), fill=(150, 161, 170))
        im.convert("RGB").save(OUT / "cards" / out.replace(".html", ".png"), optimize=True)


if __name__ == "__main__":
    card()
    banner()
    icons()
    cards()
    for f in sorted(OUT.glob("*.png")):
        print(f"  {f.relative_to(ROOT)}  {f.stat().st_size // 1024}K")
