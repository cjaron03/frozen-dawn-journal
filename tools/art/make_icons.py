#!/usr/bin/env python3
"""Draw the journal's icon and its social card.

Both are the same object: the Earth from the homepage, caught partway
through the freeze. The colours and the freeze keyframes are lifted from
the <g class="tl-earth"> group in site/timeline.html so the icon and the
page it belongs to cannot drift apart.

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
    d.text((x, 404), "One person, 535 commits,", font=fh, fill=HEAD)
    d.text((x, 404 + 64), "and a thing that learned to think.", font=fh, fill=HEAD)

    # no stat row. the headline already carries every number one would hold,
    # and a card that says 535 twice looks like it was assembled twice.
    fm = font("Menlo.ttc", 16)
    tracked(d, (x, 548), "cjaron03.github.io/frozen-dawn-journal", fm, ICE, 0.7)

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
    d.text((x, 140), "535 commits, eight chapters, and a thing that learned to think.",
           font=fs, fill=(150, 161, 170))

    fm = font("Menlo.ttc", 15)
    tracked(d, (x, 186), "cjaron03.github.io/frozen-dawn-journal", fm, ICE, 0.7)

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


if __name__ == "__main__":
    card()
    banner()
    icons()
    for f in sorted(OUT.glob("*.png")):
        print(f"  {f.relative_to(ROOT)}  {f.stat().st_size // 1024}K")
