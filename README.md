# Frozen Dawn, Dev Journal

A dev journal site documenting the development of the Frozen Dawn
Minecraft mod (NeoForge 1.21.1).

Mod repo: https://github.com/cjaron03/frozen-dawn

## Layout

    site/       the pages themselves, hand written HTML
    pipeline/   data extraction, and the numbers the pages read
    tools/      the build and the checks
    preview/    the built site, what actually gets served
    docs/       design documents and decision records

## site/

The pages that make up the journal.

    timeline.html           homepage, the animated timeline
    architect-page.html     The Architect, the centerpiece
    world-doesnt-wait.html  Chapter One, the six phase collapse

The rest are design explorations and decision records kept for the
history of how the look was settled.

## pipeline/

    fetch.py        pulls commit history out of the mod repo
    build.py        turns that into the data the pages read
    data/           commits.tsv, chapters.json, milestones.json
    src/            copies of the mod classes the pages document,
                    the source of truth for every number on the site

Numbers shown on the site are read out of the real mod source rather
than retyped, so PhaseManager.java and ChunkCatchUpManager.java here
are reference copies, not a second implementation.

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
