# Frozen Dawn, Dev Journal

A dev journal site documenting the development of the Frozen Dawn
Minecraft mod (NeoForge 1.21.1).

Mod repo: https://github.com/cjaron03/frozen-dawn

## Layout

    site/       the pages themselves, hand written HTML
    pipeline/   data extraction, and the numbers the pages read
    tools/      the build, the checks and the artwork
    preview/    the built site, what actually gets served
    docs/       design documents and decision records

## site/

The journal, one file per page, in reading order. The build wraps each
one in _shell.html and gives it the address on the right.

    timeline.html                   index.html      the homepage, an animated timeline
    world-doesnt-wait.html          chapter-1.html  I. The World That Doesn't Wait
    architect-page.html             architect.html  II. Building a Mind
    they-called-it-continuity.html  chapter-3.html  III. They Called it Continuity
    holding-back-the-cold.html      chapter-4.html  IV. Holding Back the Cold
    what-the-cold-made.html         chapter-5.html  V. What the Cold Made
    the-ones-who-stayed.html        chapter-6.html  VI. The Ones Who Stayed
    welcome-home.html               chapter-7.html  VII. Welcome Home
    maeve.html                      director.html   VIII. Maeve

The Architect is the centrepiece. Maeve is listed like any other chapter,
but a reader who finishes all seven before her also finds a second way in,
through the Architect page, and the check below keeps that door a reward.

    assets/         the icons and the social cards, plus assets/ch3/, the
                    ORSA textures and campaign posters Chapter III loads
    assets/chapter.js
                    what every chapter shares: the typed title, the deck,
                    the cards, the reading marker and the layer switch

## tools/

    build.py            wraps site/ into preview/, one page per chapter
    check.py            refuses a broken build: notes left in, dead links,
                        missing assets, a script that will not parse, an
                        em dash anywhere
    art/make_icons.py   draws the icons, the journal's social card and a
                        card per chapter into site/assets/

To build and look at it:

    python3 tools/build.py
    python3 tools/check.py
    python3 -m http.server 8788 -d preview

The cards are committed, so they only need drawing again when a chapter
is renamed or its card changes. That needs Pillow and the macOS system font:

    python3 tools/art/make_icons.py

## docs/

docs/workbench/ holds the design explorations and decision records kept
for the history of how the look was settled: the chapter plan, the page
map, the visual style, the homepage motion studies and the early Architect
simulations. None of it ships.

## pipeline/

    fetch.py        pulls commit history out of the mod repo
    build.py        writes that history into the homepage graph
    data/           commits.tsv, chapters.json, milestones.json
    src/            copies of the mod classes the pages document,
                    the source of truth for every number on the site

Numbers shown on the site are read out of the real mod source rather
than retyped, so PhaseManager.java and ChunkCatchUpManager.java here
are reference copies, not a second implementation.

The homepage graph refreshes itself. Once a day the deploy workflow runs
fetch.py and build.py, commits whatever changed and ships it; a day with
no new commits in the mod ships nothing. To do the same by hand:

    python3 pipeline/fetch.py
    python3 pipeline/build.py

build.py only rewrites the parts of site/timeline.html fenced with
build: markers, plus the line's length where the stylesheet uses it.
Everything else on that page is hand written and safe to edit. Editing
inside a fence is not: every deploy runs build.py --check, which fails
if the page and the data disagree.

## Licence

The mod is one thing and the journal is another, so they are licensed
separately.

This repository is the writing, the artwork and the site design, and it is
licensed under Creative Commons Attribution-NonCommercial-ShareAlike 4.0
International. See LICENSE for the legal code, or
https://creativecommons.org/licenses/by-nc-sa/4.0/ for the summary. In
short: reuse it with credit, share changes on the same terms, and not
commercially.

The mod itself lives in cjaron03/frozen-dawn under LGPL-3.0.

## Status

Live at https://frozendawn.jaronc.com. Still being written.
