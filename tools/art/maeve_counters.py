#!/usr/bin/env python3
"""Draw the isometric scenes in Chapter VIII's first section, What she does
to you, and write them into site/maeve.html in place.

Everything is a box in block units. The camera looks from +x,+y, so the
visible faces are top, +x and +y. Her Architects stand at small x and face
+x, toward the camera; you stand at large x with your back to it.

Each drawing replaces the <svg class="iso"> whose title id it owns, and the
two exit panels replace the <div class="iso2"> that holds them. Nothing
else on the page is touched, so running it twice changes nothing.

    python3 tools/art/maeve_counters.py
"""
import math, re
from pathlib import Path

PAGE = Path(__file__).resolve().parent.parent.parent / "site" / "maeve.html"

C = math.cos(math.radians(30))
S = 24.0  # px per block


def P(x, y, z):
    return ((x - y) * C * S, ((x + y) * 0.5 - z) * S)


def hexc(h):
    h = h.lstrip('#'); return [int(h[i:i+2], 16) for i in (0, 2, 4)]


def shade(h, f):
    r, g, b = hexc(h)
    return '#%02x%02x%02x' % tuple(max(0, min(255, int(c * f))) for c in (r, g, b))


class Scene:
    def __init__(self):
        self.items = []   # (depth, svg)
        self.pts = []
        self.over = []    # drawn last, in order

    def poly(self, pts3, fill, extra=''):
        pts = [P(*p) for p in pts3]
        self.pts += pts
        d = ' '.join('%.1f,%.1f' % p for p in pts)
        return '<polygon points="%s" fill="%s"%s/>' % (d, fill, extra)

    def box(self, x0, y0, z0, dx, dy, dz, col, depth=None, extra='', top=None, faces='txy'):
        x1, y1, z1 = x0 + dx, y0 + dy, z0 + dz
        out = []
        if 'y' in faces:
            out.append(self.poly([(x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)], shade(col, .62), extra))
        if 'x' in faces:
            out.append(self.poly([(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)], shade(col, .82), extra))
        if 't' in faces:
            out.append(self.poly([(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], top or col, extra))
        if depth is None:
            depth = (x0 + x1) / 2 + (y0 + y1) / 2 + z0 * .01
        self.items.append((depth, ''.join(out)))

    def xface(self, x, y0, z0, dy, dz, fill, depth, extra=''):
        """a flat rectangle lying on an x = const plane, facing +x."""
        self.items.append((depth, self.poly([(x, y0, z0), (x, y0 + dy, z0), (x, y0 + dy, z0 + dz), (x, y0, z0 + dz)], fill, extra)))

    def line(self, pts3, cls, depth=None, marker=None):
        pts = [P(*p) for p in pts3]
        self.pts += pts
        d = 'M' + ' L'.join('%.1f,%.1f' % p for p in pts)
        m = ' marker-end="url(#%s)"' % marker if marker else ''
        svg = '<path class="%s" d="%s"%s/>' % (cls, d, m)
        if depth is None:
            self.over.append(svg)
        else:
            self.items.append((depth, svg))

    def curve(self, f, n, cls, marker=None, depth=None):
        self.line([f(i / n) for i in range(n + 1)], cls, depth, marker)

    def svg(self, title, tid, pad=8):
        xs = [p[0] for p in self.pts]; ys = [p[1] for p in self.pts]
        x0, y0 = min(xs) - pad, min(ys) - pad
        w, h = max(xs) - min(xs) + 2 * pad, max(ys) - min(ys) + 2 * pad
        body = ''.join(s for _, s in sorted(self.items, key=lambda t: t[0])) + ''.join(self.over)
        return ('<svg class="iso" viewBox="%.0f %.0f %.0f %.0f" role="img" aria-labelledby="%s">'
                '<title id="%s">%s</title>%s</svg>' % (x0, y0, w, h, tid, tid, title, body))


SNOW = '#dfe8ed'
GROUND = '#c9d6dd'


def ground(sc, nx, ny, x0=0, y0=0):
    for i in range(nx):
        for j in range(ny):
            t = SNOW if (i + j) % 2 else shade(SNOW, .96)
            sc.box(x0 + i, y0 + j, -0.5, 1, 1, 0.5, GROUND, depth=-100 + i + j, top=t,
                   faces=('t' + ('x' if i == nx - 1 else '') + ('y' if j == ny - 1 else '')))


def snow_block(sc, x, y, z):
    sc.box(x, y, z, 1, 1, 1, '#d5e0e6', top='#eef3f6')
    # a couple of pixel speckles on the +x face
    for (yy, zz) in ((.2, .7), (.65, .35), (.4, .15)):
        sc.xface(x + 1.001, y + yy, z + zz, .12, .12, '#b7c6ce', depth=x + .5 + y + .5 + z * .01 + .001)


ARCH = '#2a3340'


def architect(sc, x, y, eyes=True, held=None):
    """x,y is the centre of the feet. faces +x."""
    d = x + y
    sc.box(x - .12, y - .25, 0, .24, .22, 1.15, shade(ARCH, .9), depth=d - .01)   # leg
    sc.box(x - .12, y + .03, 0, .24, .22, 1.15, shade(ARCH, .9), depth=d)
    sc.box(x - .14, y - .28, 1.15, .28, .56, .85, ARCH, depth=d + .01)           # body
    sc.box(x - .27, y - .27, 2.0, .54, .54, .54, ARCH, depth=d + .02)            # head
    if eyes:
        fx = x + .27 + .002
        dep = d + .03
        for (yy) in (-.2, .05):
            for k, c in enumerate(('#7a5fa8', '#a98cd8', '#4a3866')):
                sc.xface(fx, y + yy, 2.33 - k * .055, .15, .055, c, dep, ' class="eye"')
    return d


def you(sc, x, y, col='#c3ccd3'):
    """seen from behind: x,y the centre of the feet, facing -x."""
    d = x + y
    sc.box(x - .12, y - .25, 0, .24, .24, .75, shade(col, .78), depth=d - .02)
    sc.box(x - .12, y + .01, 0, .24, .24, .75, shade(col, .78), depth=d - .01)
    sc.box(x - .12, y - .25, .75, .24, .5, .75, col, depth=d)
    sc.box(x - .25, y - .25, 1.5, .5, .5, .5, '#8a6a4c', top='#7a5a3e', depth=d + .01)  # hair from behind
    return d


def scene_shield():
    sc = Scene(); ground(sc, 7, 2, 0, .5)
    ax, ay = 1.6, 1.5
    architect(sc, ax, ay)
    sc.box(ax - .26, ay - .55, .45, .12, .24, .6, ARCH, depth=ax + ay - .3)          # arm behind the shield
    # the shield: an iron rim and a wooden face, held in front
    sc.box(ax + .3, ay - .5, .5, .1, .9, 1.25, '#7d878e', top='#a7b0b6', depth=ax + ay + .4)
    sc.xface(ax + .401, ay - .42, .58, .74, 1.09, '#5a4128', depth=ax + ay + .41)
    sc.xface(ax + .402, ay + .03, .58, .06, 1.09, '#7d878e', depth=ax + ay + .42)
    # you, sword raised and swinging in
    px, py = 4.6, 1.5
    you(sc, px, py)
    sc.box(px - .55, py - .5, 1.25, .55, .22, .22, '#c3ccd3', depth=px + py - .3)     # sword arm, reaching
    sc.box(px - 1.6, py - .45, 1.33, 1.05, .1, .07, '#e6edf1', top='#ffffff', depth=px + py - .9)  # blade
    sc.box(px - .62, py - .52, 1.28, .08, .26, .14, '#6c7883', depth=px + py - .35)   # guard
    # sparks where it lands
    for a in (-35, 0, 35):
        r = math.radians(a)
        sc.line([(ax + .55, ay - .1 + .0, 1.35), (ax + .55 + .45 * math.cos(r), ay - .1 - .3 * math.sin(r), 1.35 + .35 * math.sin(r))], 'spk')
    return sc.svg('An Architect with purple eyes holds a shield up in front of it. You, seen from behind, swing a sword into the shield and it sparks.', 'ct1t')


def scene_pillar():
    sc = Scene(); ground(sc, 8, 2, 0, .5)
    ax, ay = 1.3, 1.5
    architect(sc, ax, ay)
    snow_block(sc, 2.0, 1.0, 0); snow_block(sc, 2.0, 1.0, 1)
    # stuck arrows on the face of the pillar
    for (yy, zz) in ((.3, 1.4), (.65, .8)):
        sc.box(3.0, 1.0 + yy, zz, .55, .04, .04, '#c9d6dd', depth=3.6 + yy)
        sc.box(3.5, 1.0 + yy - .04, zz - .04, .1, .12, .12, '#8a949b', depth=3.7 + yy)
    px, py = 6.4, 1.5
    you(sc, px, py)
    bow(sc, px - .45, py, 1.15)
    sc.line([(px - .6, py - .05, 1.25), (4.0, 1.4, 1.35)], 'fly', marker='ctHy')
    return sc.svg('An Architect crouches behind a pillar two snow blocks high. Your arrows are stuck in the snow. You, seen from behind, draw a bow.', 'ct3t')


def bow(sc, x, y, z, facing=-1, dep=None):
    """a bow in the y-z plane at x. its belly bows toward facing."""
    dep = dep if dep is not None else x + y - .5
    pts = []
    for i in range(7):
        t = i / 6
        zz = z - .55 + 1.1 * t
        xx = x + facing * .22 * math.sin(math.pi * t)
        sc.box(xx - .04, y - .04, zz - .07, .08, .08, .16, '#8b6a43', depth=dep)
        pts.append((xx, y, zz))
    sc.items.append((dep + .001, '<path class="st" d="M%.1f,%.1f L%.1f,%.1f L%.1f,%.1f"/>' % (
        *P(x, y, z - .55), *P(x - facing * .18, y, z), *P(x, y, z + .55))))


def scene_archer():
    sc = Scene(); ground(sc, 9, 2, 0, .5)
    ax, ay = 1.4, 1.5
    architect(sc, ax, ay)
    bow(sc, ax + .55, ay - .35, 1.55, facing=1, dep=ax + ay + .5)
    sc.box(ax + .05, ay - .45, 1.5, .5, .16, .16, ARCH, depth=ax + ay + .3)          # bow arm
    # backing away: an arrow on the snow, pointing away from you
    sc.line([(ax - .2, ay + .8, .01), (ax - 1.3, ay + .8, .01)], 'back', depth=-50, marker='ctHd')
    # you, charging, sword out
    px, py = 6.6, 1.5
    you(sc, px, py)
    sc.box(px - .5, py - .5, 1.05, .5, .22, .22, '#c3ccd3', depth=px + py - .3)
    sc.box(px - 1.45, py - .45, 1.0, .95, .1, .07, '#e6edf1', top='#ffffff', depth=px + py - .9)
    for k in range(3):
        sc.line([(px + .6 + k * .1, py - .5 + k * .45, .5 + k * .3), (px + 1.2 + k * .1, py - .5 + k * .45, .5 + k * .3)], 'mvl')
    # the shot, arcing in over the gap
    sc.curve(lambda t: (ax + .8 + (px - .6 - ax - .8) * t, ay - .35 + .2 * t, 1.6 + 1.2 * math.sin(math.pi * t) - .3 * t), 20, 'fire', marker='ctHd')
    return sc.svg('You, seen from behind, charge at an Architect with a sword. It backs away across the snow and fires a bow at you instead.', 'ct2t')


def scene_mantlet():
    sc = Scene(); ground(sc, 9, 2, 0, .5)
    # the screen it used last, coming down behind it
    gx = .2
    for z in (0, 1):
        for yy in (1.0,):
            sc.items.append((gx + yy + 1 + z * .01, '<g class="ghost">' + Scene_poly_outline(sc, gx, yy, z) + '</g>'))
    for (x, y, z, s) in ((.6, .9, .1, .18), (.9, 1.5, .0, .14), (.4, 1.9, .0, .12), (1.0, 1.2, .55, .12)):
        sc.box(x, y, z, s, s, s, '#b7c6ce', depth=x + y)
    ax, ay = 2.0, 1.5
    architect(sc, ax, ay)
    # the new screen, between it and you
    snow_block(sc, 2.9, 1.0, 0); snow_block(sc, 2.9, 1.0, 1)
    sc.line([(ax - .9, ay + .8, .01), (ax + .3, ay + .8, .01)], 'back', depth=-50, marker='ctHd')
    sc.box(3.9, 1.6, 1.2, .6, .04, .04, '#c9d6dd', depth=4.6)
    px, py = 7.2, 1.5
    you(sc, px, py)
    bow(sc, px - .45, py, 1.15)
    sc.line([(px - .6, py - .05, 1.25), (5.0, 1.55, 1.3)], 'fly', marker='ctHy')
    return sc.svg('An Architect walks toward you behind a wall of snow two blocks high. Behind it, the wall it used last is crumbling. You, seen from behind, shoot at the wall.', 'ct4t')


def Scene_poly_outline(sc, x, y, z):
    x1, y1, z1 = x + 1, y + 1, z + 1
    faces = [[(x, y1, z), (x1, y1, z), (x1, y1, z1), (x, y1, z1)],
             [(x1, y, z), (x1, y1, z), (x1, y1, z1), (x1, y, z1)],
             [(x, y, z1), (x1, y, z1), (x1, y1, z1), (x, y1, z1)]]
    out = ''
    for f in faces:
        pts = [P(*p) for p in f]; sc.pts += pts
        out += '<polygon points="%s"/>' % ' '.join('%.1f,%.1f' % p for p in pts)
    return out


def token(sc, x, y, scale=.55):
    """a small Architect for the maps."""
    d = x + y
    s = scale
    sc.box(x - .14 * s, y - .25 * s, 0, .28 * s, .5 * s, 1.9 * s, ARCH, depth=d)
    sc.box(x - .27 * s, y - .27 * s, 1.9 * s, .54 * s, .54 * s, .54 * s, ARCH, depth=d + .01)
    fx = x + .27 * s + .002
    for yy in (-.2, .05):
        sc.xface(fx, y + yy * s, (2.2) * s, .15 * s, .1 * s, '#a98cd8', d + .02, ' class="eye"')


def walls(sc, x0, y0, n, gaps):
    """a square of single-block walls, one block high, with doorways."""
    cells = []
    for i in range(n):
        cells += [(x0 + i, y0), (x0 + i, y0 + n - 1)]
    for j in range(1, n - 1):
        cells += [(x0, y0 + j), (x0 + n - 1, y0 + j)]
    for (cx, cy) in cells:
        if (cx, cy) in gaps:
            continue
        sc.box(cx, cy, 0, 1, 1, 1, '#5b6773', top='#7a8692')


def label(sc, x, y, z, text, cls='ex'):
    px, py = P(x, y, z)
    sc.over.append('<text class="%s" x="%.1f" y="%.1f">%s</text>' % (cls, px, py, text))


def flat_ground(sc, nx, ny):
    for i in range(nx):
        for j in range(ny):
            t = SNOW if (i + j) % 2 else shade(SNOW, .96)
            sc.box(i, j, -.3, 1, 1, .3, GROUND, depth=-100 + i + j, top=t,
                   faces='t' + ('x' if i == nx - 1 else '') + ('y' if j == ny - 1 else ''))


def scene_exit(now):
    """one base, seen from above at an angle. A is the doorway on the +x
    wall, B the one on the +y wall."""
    sc = Scene(); flat_ground(sc, 8, 8)
    walls(sc, 1, 1, 5, {(5, 3), (3, 5)})
    if now:
        token(sc, 3.5, 6.4, .8)
        sc.box(3.35, 3.35, 0, .3, .3, .3, '#e8eef2', depth=6.9)
        sc.line([(3.5, 5.9, 1.2), (3.5, 4.0, .3)], 'watch')
    else:
        token(sc, 6.4, 3.5, .8)
        sc.box(3.35, 3.35, 0, .3, .3, .3, '#e8eef2', depth=6.9)
        sc.line([(3.5, 3.9, .15), (3.5, 7.4, .15)], 'out', marker='ctHy')
    label(sc, 7.3, 3.5, .3, 'A', 'lb'); label(sc, 3.5, 7.6, .3, 'B', 'lb')
    return sc


def scene_exits():
    a = scene_exit(False).svg('Last time: an Architect waited outside your usual way out, A. You left through B instead, and it saw.', 'ct5a', pad=6)
    b = scene_exit(True).svg('Now: an Architect waits outside B.', 'ct5b', pad=6)
    return ('<div class="iso2"><div><span>last time</span>' + a + '</div><div><span>now</span>' + b + '</div></div>')


def scene_hotspot():
    sc = Scene(); flat_ground(sc, 9, 7)
    cx, cy = 6.0, 4.2
    sc.curve(lambda t: (cx + 1.8 * math.cos(2 * math.pi * t), cy + 1.8 * math.sin(2 * math.pi * t), .02), 48, 'soulf', depth=-41)
    for (dx, dy) in ((-.6, -.4), (.3, -.7), (.7, .2), (-.2, .5), (-.9, .4), (.4, .8)):
        x, y = cx + dx, cy + dy
        sc.line([(x - .2, y - .2, .01), (x + .2, y + .2, .01)], 'ded', depth=-40)
        sc.line([(x - .2, y + .2, .01), (x + .2, y - .2, .01)], 'ded', depth=-40)
    sc.curve(lambda t: (cx + 1.8 * math.cos(2 * math.pi * t), cy + 1.8 * math.sin(2 * math.pi * t), .02), 48, 'soul', depth=-39)
    for (x, y) in ((.9, 1.0), (.9, 5.6), (3.6, .6)):
        token(sc, x, y, .8)
        tx, ty = cx + (x - cx) * .5, cy + (y - cy) * .5
        sc.line([(x + .5, y + .15, .02), (tx, ty, .02)], 'walk', depth=-38, marker='ctHd')
    return sc.svg('Six of her Architects have died in one spot. A ring of blue light grows around it, and three more Architects walk toward it from far away.', 'ct6t', pad=8)


def write(page=PAGE):
    s = page.read_text()
    scenes = {'ct1t': scene_shield(), 'ct3t': scene_pillar(), 'ct2t': scene_archer(),
              'ct4t': scene_mantlet(), 'ct6t': scene_hotspot()}
    for tid, svg in scenes.items():
        pat = r'<svg class="iso" viewBox="[^"]+" role="img" aria-labelledby="%s">.*?</svg>' % tid
        s, n = re.subn(pat, lambda m: svg, s, count=1, flags=re.S)
        if n != 1:
            raise SystemExit('no drawing for %s in %s' % (tid, page))
    s, n = re.subn(r'<div class="iso2">.*?</div></div>', lambda m: scene_exits(), s, count=1, flags=re.S)
    if n != 1:
        raise SystemExit('no exit panels in %s' % page)
    page.write_text(s)
    print('drew 7 scenes into %s' % page.relative_to(PAGE.parent.parent))


if __name__ == '__main__':
    write()
