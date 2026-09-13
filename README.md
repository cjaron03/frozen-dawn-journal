# Frozen Dawn, Dev Journal

A dev journal site documenting the development of the Frozen Dawn
Minecraft mod (NeoForge 1.21.1).

Mod repo: https://github.com/cjaron03/frozen-dawn

## Layout

    site/       the pages themselves, hand written HTML
    pipeline/   data extraction and build scripts

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

## Status

Work in progress. Not yet deployed.
