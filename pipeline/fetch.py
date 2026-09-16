"""Pull the mod's history into data/commits.tsv.

Runs at build time, never in the browser. Re-runnable and idempotent.

This reads the repository with git rather than the REST API, for two
reasons. The homepage curve is drawn from how much code moved on a day,
not how many commits were made, and per commit line counts over the REST
API cost one request each, which is a rate limit problem the moment the
history grows. Git gives the whole history, every branch, and the line
counts, in one network operation and no token.

The clone is a bare mirror kept in .cache, so the second run and every
run after it is a fetch of whatever is new.
"""
import os, pathlib, subprocess, sys

REPO   = os.environ.get("FD_REPO", "cjaron03/frozen-dawn")
ROOT   = pathlib.Path(__file__).parent
CACHE  = ROOT / ".cache" / (REPO.split("/")[-1] + ".git")
OUT    = ROOT / "data" / "commits.tsv"
URL    = os.environ.get("FD_URL", "https://github.com/%s.git" % REPO)

# Art, audio and archives are real work, but they are not lines, and a
# single texture import would otherwise outweigh a week of engine code.
ASSETS = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".svg",
          ".ogg", ".wav", ".mp3", ".ttf", ".otf",
          ".jar", ".zip", ".gz", ".bin", ".nbt", ".schem", ".lock")

REC = "\x01"   # record separator, so a subject can hold anything it likes


def git(*args, **kw):
    return subprocess.run(("git",) + args, check=True, text=True,
                          capture_output=kw.get("capture", True)).stdout


def sync():
    if (CACHE / "HEAD").exists():
        git("-C", str(CACHE), "remote", "update", "--prune", capture=False)
    else:
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        git("clone", "--mirror", URL, str(CACHE), capture=False)


def history():
    """Every commit on every branch, newest first, with its line counts.

    Branches only. A mirror also carries GitHub's refs/pull/*, and those
    are synthetic merge previews of work that is already on a branch, so
    counting them would invent commits that were never written.
    """
    raw = git("-C", str(CACHE), "log", "--branches", "--numstat", "--date=short",
              "--pretty=format:%s%%ad%%x09%%s" % REC)
    rows = []
    for block in raw.split(REC):
        if not block.strip():
            continue
        head, _, body = block.partition("\n")
        date, _, subject = head.partition("\t")
        added = removed = 0
        for line in body.splitlines():
            parts = line.split("\t")
            if len(parts) != 3:
                continue
            a, d, path = parts
            # a binary file reports its counts as dashes.
            if a == "-" or path.lower().endswith(ASSETS):
                continue
            added += int(a); removed += int(d)
        rows.append((date.strip(), added, removed,
                     subject.strip().replace("\t", " ")))
    return rows


def main():
    sync()
    rows = history()
    if not rows:
        sys.exit("no commits found, is %s reachable?" % URL)
    rows.sort()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        for date, added, removed, subject in rows:
            f.write("%s\t%d\t%d\t%s\n" % (date, added, removed, subject))
    print("wrote %d commits, %s to %s, %d lines added, %d removed"
          % (len(rows), rows[0][0], rows[-1][0],
             sum(r[1] for r in rows), sum(r[2] for r in rows)))


if __name__ == "__main__":
    main()
