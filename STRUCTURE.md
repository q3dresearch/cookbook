# How this repo is laid out

One repo, one folder per published recipe. Not one repo per recipe: nobody
knows us yet, so stars, topics and inbound links are worth more concentrated
on a single URL than spread across ten. It also gives one Zenodo DOI per
release, versioned like a journal volume — a finding is cited as DOI plus
recipe path.

    recipes/<slug>/
        README.md          the answer, written for a stranger
        provenance.json    what the published figures were computed from
        history.csv        the longitudinal series, append-only
        artifacts/
            research-questions/   asked, with status: answered, partial, open
            scripts/              the code that produced everything
            charts/               the figures
            data/                 fetched, never committed

The three files at the root are the recipe's identity — what it claims, what it
claimed it from, and how that has moved. Everything under `artifacts/` is
working material.

`research-questions/` is what makes a return visit cheap. It records what was
asked and what is still open, with the reason, so a second pass resumes rather
than restarts.

## Two rules that are easy to get wrong

**Self-containment beats DRY.** Each recipe carries its own tool, even where
that duplicates palette constants across folders. The unit of use is one
folder: a stranger copies it and it runs. A shared `lib/` saves a few dozen
lines and breaks that, so the duplication is deliberate.

**Never commit data.** Ship the fetcher instead, so a fork is cheap — one recipe
here reads 1.5 GB and clones in 45 KB. The cost is that the source moves and a
forker's numbers will differ, which is what `provenance.json` is for: it records
the SHA-256 and size of exactly what the published figures came from, and the
fetcher prints the comparison. Drift becomes visible rather than silent.

## Promotion is an explicit act

`larder/` is the private draft workspace and holds every candidate, proven and
unproven. Nothing is published by sitting there. Moving a recipe here means
choosing it, rewriting it for someone who has never seen the project, and
checking what its data contains before it becomes public.

Never promote a directory. Promote named files.
