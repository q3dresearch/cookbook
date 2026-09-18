# America is not running out of landfill room. Eight states are.

**Status: proven** · method 1.0.0 · computed 2026-09-17 from the EPA Landfill Methane
Outreach Program database, 2,641 sites across 42 fields, two editions three years apart.
**Both workbooks are committed**, against this repo's usual rule, because one of them can no
longer be obtained from anywhere — see *What makes this recipe unusual* below.

Nationally there is **more** permitted room than there was: 14.5 billion tons in 2021, 14.8
billion in 2024, after burying a billion — because 1.3 billion tons of new capacity was
permitted, and it was permitted where the clock was short.

**Eight states have a median landfill with under twenty years left.** Half the country's
remaining room belongs to two companies. Both are true at once and neither is visible from a
national total.

## The decision it changes

**If you are a municipality signing a disposal contract, you are not negotiating in a
national market and probably not in a competitive one.** Half of America's remaining
permitted room sits with two firms; the 510 single-site owners hold 33% between them at a
median of 3.3M tons each. Your alternative is capacity you do not own and cannot build
quickly — new capacity takes a permit, and the permits are going to the states that are
already short.

*Who acts on this:* a county or municipal authority pricing a disposal contract; a state
regulator deciding where to grant capacity; a hauler or investor assessing where room runs
out first.

## What makes this recipe unusual

**Half its evidence no longer exists at source.** EPA publishes the database at a dated path
and overwrites the listing. Only the current edition resolves — September 2021 returns 404
and no web archive holds it. The three-year interval this recipe is built on exists *by
accident*, because a copy was taken before the overwrite.

That is why both workbooks are committed here at 756 KB each. The repo's rule is that data is
never committed and the fetcher ships instead; its stated exception is a snapshot that cannot
be reconstructed, and this is one. Without the 2021 edition there is one edition, no interval,
and the central finding cannot be computed at all.

## Eleven figures, each with the decision it serves on its face

Every figure declares who it is for, the choice in front of them, and what would falsify it.

- **[Eighty American landfills are full within five years](artifacts/charts/1-countdown.svg)** —
  and they run out by filling up, not by accelerating.
- **[Half of America's remaining landfill room belongs to two companies](artifacts/charts/2-owners.svg)** —
  the tail of 510 single-site owners is drawn as its own study, because pooling it with
  Waste Management flattened both.
- **[The countdown misses small landfills, and small landfills barely matter](artifacts/charts/3-coverage.svg)** —
  the bound on what the missing sites could change.
- **[Landfills run out of room by filling up, not by speeding up](artifacts/charts/4-fullness.svg)**
- **[The clock runs down, and the room gets put back where it is shortest](artifacts/charts/5-clock.svg)**
- **[Whether your landfill is nearly full is mostly a question of which state you are in](artifacts/charts/6-where.svg)**
- **[The methane nobody is collecting is in the middle-sized landfills](artifacts/charts/7-methane.svg)**
- **[Most captured landfill gas is burned off, not used](artifacts/charts/8-gas.svg)**
- **[New Jersey has six tons of landfill room per resident. Nevada has 385.](artifacts/charts/9-percapita.svg)**
- **[The landfills that need attention first, named](artifacts/charts/10-triage.svg)**
- **[Whether an abandoned landfill is controlled depends on its size, not its era](artifacts/charts/11-abandoned.svg)**

## Two things found while promoting it, both worth inheriting

**A dependency swap is only safe if you diff the output.** `openpyxl` was replaced with a
sixty-line standard-library xlsx reader so this recipe needs nothing installed. It was checked
cell by cell against openpyxl on both editions — **2,642 rows, no disagreement** — and then
every figure was rebuilt and compared byte for byte against the previous build. Ten of eleven
were identical.

**The eleventh had never been reproducible.** `chart-5-clock.py` iterated `set(a) & set(b)` to
place dots, and Python randomises string hashing per process, so two landfills at the same
coordinates swapped draw order between runs. The render was pixel-identical and the bytes were
not, which is exactly why nothing had ever caught it — it surfaced only because an unrelated
change was being diffed byte-for-byte. Anything unsorted that reaches output does this.

## What this cannot say

**Not a forecast.** The countdown divides remaining capacity by a current annual acceptance
rate. It assumes the rate holds, which it will not, and the recipe's own fourth figure shows
sites run out by filling rather than by accelerating — so the arithmetic is a statement about
today's rate, not a prediction.

**One interval, by accident.** Everything longitudinal here rests on a single three-year
comparison that exists because a copy survived. Two points cannot distinguish a trend from an
event, and the recipe says so wherever it uses them.

**Ownership, status and capacity are current-state fields with no history.** A site whose
owner changed between editions shows only its latest owner. Owner names are normalised before
any comparison: raw, the register reports 304 ownership changes between its two editions and
**250 of those are one company renaming itself**.

**Nothing here is about hazard or about what is in the hole.** The register records volume and
rate, not contents.

## Reproducing

    cd recipes/landfill-countdown
    python3 artifacts/scripts/fetch.py           # verifies the workbooks, pulls Census files
    python3 artifacts/scripts/measure.py         # countdown, owners, the three-year diff
    python3 artifacts/scripts/followup.py        # coverage bound and the closure test
    python3 artifacts/scripts/geo.py             # Census population and distance features
    python3 artifacts/scripts/features.py        # one table of every measurable attribute
    for f in artifacts/scripts/chart-*.py; do python3 "$f"; done

`fetch.py --verify` hashes what is present against `provenance.json`. Nothing needs
installing — standard library only, verified by AST walk.
