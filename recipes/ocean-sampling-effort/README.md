# How to get a biological answer out of a register that is mostly sampling effort

**Status: proven** · method 1.0.0 · computed 2026-09-19 from OBIS, the Ocean Biodiversity
Information System, 229,671,953 records fetched by
[`artifacts/scripts/fetch.py`](artifacts/scripts/fetch.py). No key, no dependencies, no data
committed — the fetcher retrieves everything and prints the drift against `provenance.json`.

OBIS is the reference record of where sea life has been observed. Marine protected areas are
sited from it, extinction risk is assessed against it, and national biodiversity indicators are
computed on it. **It is an excellent register of where people have looked, and it is read as a
register of where life is.**

This recipe is not a complaint about that. It is the method for getting a real biological
answer out of it anyway, and the check that tells you when you have failed.

## The decision it changes

**Stop comparing units, and start comparing composition within a stratum — then check that the
stratum has many contributors before you believe it.**

A within-bin share divides out the sampling effort that produced the bin, because every taxon
in it was reached by the same cruises. That is what turns an unusable register into a usable
one. It only works where the bin is many programmes: in OBIS's shallow water the largest
dataset holds 9–12% of a depth band, and below 5,000 m one cruise holds 47%. Above that line
the ratio is a measurement; below it, it is one ship's itinerary wearing a ratio's clothes.

*Who acts on this:* anyone computing a biodiversity indicator, siting a reserve, or reading a
species' recorded range as its ecological niche — and anyone doing the equivalent on any
register built from volunteered records rather than a designed survey.

## 1. The map is five monitoring programmes

![The world map of marine life is about five monitoring programmes](artifacts/charts/sampling.svg)

27,168 grid cells hold the register; **27 of them hold a third of it**, and 42% hold under a
hundred records. The hotspots are addresses, not ecosystems — every one within reach of a
marine laboratory.

The sharper finding is what is inside them. **The median cell takes 45% of its records from a
single dataset**, and it is worst where the data is thinnest: in cells holding 100–1,000
records the median top dataset is 67%. A remote cell is not thinly sampled by many people; it
is one survey that went there once.

The busiest cells carry 120–290 datasets each and still take 30–65% from one: 16S sequencing at
Sydney, kelp forest surveys at Santa Barbara, herring gull telemetry off Belgium, beach-washup
monitoring off the Netherlands. **A cell filled by 16S sequencing contains bacteria; a cell
filled by beach washup contains what floats.**

## 2. For some groups the attribute *is* the instrument

![For plants and single cells, depth is the instrument](artifacts/charts/producers.svg)

Pull recorded depth per taxonomic class and for animals you get biology — sea cucumbers really
are the deepest group. Do it for plants, algae and single cells and you get the sampling gear:
**rank correlation +0.97 between a class's DNA-sequencing share and the share of its records
below 50 m.** Alphaproteobacteria is 96% sequencing and 44% below 50 m; kelp is 0.8% and 0.3%.
A CTD rosette fires bottles down the water column and a diver does not.

**Forams are the control that names the mechanism.** They break the correlation — 2.2%
sequencing but 39.6% below 50 m — because their largest dataset is the Deep Sea Drilling
Project. A third instrument, a sediment core. Dropping them moves rho from +0.73 to +0.97. An
outlier that turns out to be another instrument confirms the mechanism instead of denting it.

**The generalisable move:** build a per-unit number for *how each unit was measured*, then
rank-correlate it against your finding. "This is biased" is a caveat nobody acts on. A number
for the bias is an axis, and if it ranks with your claim at 0.97 there is no claim left.

## 3. What survives: light

![Light is the only cliff this register can prove](artifacts/charts/cliffs.svg)

Now the method. "How deep does kelp go" is unanswerable — that is the gear. "What lives at
40 m" is answerable, because everything in that bin was reached by the same cruises.

Benthic photosynthesisers have to do two things at once: attach to the bottom and be lit. They
disappear within tens of metres, measured as a share of each bin scaled to their own share of
the top 20 m:

| group | falls under a tenth of its shallow share at |
| --- | --- |
| seagrasses | **20 m** |
| kelp | **30 m** |
| red algae | **50 m** |
| green algae | **70 m** |
| sponges, bristle worms, ray-finned fish | *never* |

Nothing that does not photosynthesise moves at all over the same range. The ordering is
mechanism, not ranking — seagrass is a flowering plant needing lit soft sediment; red and green
algae include low-light crustose corallines and run twice as deep.

**Stony corals were put in as a designed intermediate** — reef corals carry photosynthetic
symbionts, deep-water corals do not — and they behave like one: a floor of 9.2 × 10⁻², an order
of magnitude above every true photosynthesiser and an order below every control.

And this is not the cruises running out: 14.9M records sit in 50–100 m, from 1,189 datasets.

**Where the method stops.** The right-hand panel measures it directly. Shallow bands run to
2,665 datasets with the largest at 9–12%; 5,000–6,000 m is **46.6% one cruise**. So the other
cliff worth hunting — the carbonate compensation depth, where calcite dissolves — is **blocked,
not negative**. Forams do fall from 2.04% of the 3–4 km band to 0.39% of the 4–5 km band, the
right size in the right place, and sea cucumbers are 26.7% of that band on their own.

## 4. The positive control: where it really is the animals

![Sea cucumbers live a kilometre down. Squid live in the Falkland Islands](artifacts/charts/classes.svg)

A method that only ever returns "it's the sampling" is not a method. Run the same pull over
animal classes and most of it is biology: sea cucumbers are genuinely the deepest group, corals
are bimodal on both axes because reef corals and deep-sea corals share a class, marine mammals
carry more sub-zero records than anything else because the ice edge is where the seals are.

The exception proves the test works. **Squid and octopus look like the strangest class in the
file** — a depth band of 130–200 m and 83% of records from 5 °C water — and **80% of all
cephalopod records come from one dataset**, three decades of Falkland Islands trawl surveys.
The niche is a study area. A class whose largest dataset holds 13–27% is describing itself; a
class at 80% is describing a project.

Both temperature panels are ordered by **mean, not mode**: 14 of 16 animal classes peak in the
same 10 °C bin, so a modal ordering ties almost everything.

## 5. Do not clean this register first

![A fifth of this register is flagged on land](artifacts/charts/flags.svg)

OBIS publishes its own error signature and it looks alarming: **43.2M records flagged ON_LAND**
out of 229.7M, 8.5M deeper than the sea floor beneath them, half a million impossible
coordinates. The routine first step is to drop them.

**Do not.** The flags are a habitat map:

| class | flagged ON_LAND | flagged deeper than the sea floor |
| --- | --- | --- |
| seabirds | **52.7%** | 1.4% |
| seagrasses | 31.7% | 0.2% |
| clams and mussels | 21.6% | 1.5% |
| sea urchins | 5.3% | **10.1%** |
| kelp | 6.8% | 9.7% |

Birds are counted from the shore. Seagrass grows in estuaries. Clams are dug out of a beach.
The second flag picks the opposite set — benthic animals on rugged bottom, where a coarse
bathymetry raster disagrees by a few metres. **Nothing sits high on both.** Excluding the
flagged rows would have deleted more than half of all seabird records from a recipe whose third
figure is about where seagrass lives.

**And dropping them changes nothing**: all seven light-cliff crossings identical, with up to 23%
of a class removed; 88.0% → 87.6% in the top 200 m. The flags land roughly where each group
already is, so the within-bin ratio divides them out — the same reason the method worked.

## What this cannot support

**Not abundance, anywhere.** The register holds presences and never absences, so an empty cell
and an unvisited one are the same object.

**Not a trend.** Coverage has grown; whether it has *improved* needs the grid by year.

**Not one fetch twice.** The record count moved by 62,000 between two probes minutes apart.
Every figure is a statement about one fetch, and `provenance.json` records which.

## Four traps in this API, each of which returns a plausible wrong answer

**A parameter that is not supported returns the unfiltered total.** `startbathymetry`,
`startshoredistance`, `startsst` and `startsss` all come back equal to no filter at all — and so
does `startbanana`, which is how that was established. **Send the nonsense parameter.** By
contrast `flags=BANANA` returns 0, which is what a working filter does with a value it does not
know.

**The checklist caps at 10,000 rows and is sorted by record count.** Taking the first page would
have put the gastropod median description year at 1864 instead of 1911 — half a century of bias,
pointing at the conclusion being written. The paging parameter is `skip`; `from`, `offset` and
`after` are accepted and ignored.

**Unaccepted taxonomic names resolve silently.** `Fragilariophyceae` and `Bacillariophyceae`
both return 6,389,742 records. Drawing a synonym pair on one axis plots the same records twice
under two names. Every class here is checked against `/v3/taxon` for rank Class and status
accepted.

**The depth bins are not equal width** — 10 m to 200 m, then 100 m, then 1,000 m. The raw
histogram steps up at 200 m and 1,000 m and both are the bin widening: per metre, 190–200 m
holds 67,390 records and 200–300 m holds 45,865, a fall drawn as a rise.

## Reproducing

    cd recipes/ocean-sampling-effort
    python3 artifacts/scripts/fetch.py       # retrieves everything; prints drift
    python3 artifacts/scripts/sampling.py    # or any other figure script
    python3 artifacts/scripts/verify.py      # recomputes every number in this file

Standard library only. `verify.py` is authoritative: if a number here disagrees with it, the
prose is the bug.

[`artifacts/research-questions/questions.md`](artifacts/research-questions/questions.md) records
what was asked, what died and why, and what is still open.
