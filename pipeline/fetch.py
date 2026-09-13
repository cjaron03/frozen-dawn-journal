"""Pull the mod's commit history into data/commits.tsv.

Runs at build time, never in the browser. Re-runnable and idempotent.
Unauthenticated GitHub allows 60 requests an hour, and a 480 commit
history costs 5 of them, so this is safe to run on every deploy.
Set GITHUB_TOKEN in the environment to raise that ceiling.
"""
import json, os, sys, urllib.request, pathlib

REPO   = os.environ.get("FD_REPO", "cjaron03/frozen-dawn")
BRANCH = os.environ.get("FD_BRANCH", "main")
OUT    = pathlib.Path(__file__).parent / "data" / "commits.tsv"


def get(url):
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "frozen-dawn-journal-build",
    })
    tok = os.environ.get("GITHUB_TOKEN")
    if tok:
        req.add_header("Authorization", "Bearer " + tok)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def main():
    rows, page = [], 1
    while True:
        batch = get("https://api.github.com/repos/%s/commits?sha=%s&per_page=100&page=%d"
                    % (REPO, BRANCH, page))
        if not batch:
            break
        for c in batch:
            date = c["commit"]["author"]["date"][:10]
            subject = c["commit"]["message"].split("\n")[0].strip()
            rows.append((date, subject))
        if len(batch) < 100:
            break
        page += 1
        if page > 40:
            sys.exit("refusing to page past 4000 commits")

    rows.sort()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        for date, subject in rows:
            f.write("%s\t%s\n" % (date, subject.replace("\t", " ")))
    print("wrote %d commits, %s to %s" % (len(rows), rows[0][0], rows[-1][0]))


if __name__ == "__main__":
    main()
