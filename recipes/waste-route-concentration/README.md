# Four ways a national register lies about who is concentrated

**Status: proven** · method 1.0.0 · computed 2026-09-18 from the EPA RCRA Biennial
Report, twelve cycles 2001–2023, 8.0M records fetched by
[`artifacts/scripts/fetch.py`](artifacts/scripts/fetch.py). No data is committed; the
cache directory is an argument and every figure regenerates from a clean fetch.

America's hazardous waste register names every facility, every route it uses and every
ton it handles. It is exactly the file you would reach for to ask which part of the
industry is concentrated — and **four different reasonable ways of asking return four
wrong answers**, each wrong in a way that generalises past this dataset.

## The decision it changes

**If you are about to quote a concentration figure from a register that people file
into, pin the denominator before you trend it and count owners rather than gates.**
On the obvious measure, American hazardous waste management has not concentrated at all
since 2001 — Gini across every firm is 0.96 then 0.96 for wastewater treatment, 0.66 then
0.63 for deep-well injection. Holding each route's firm count fixed at its largest thirty,
**seven of eight routes concentrated**, one of them from 0.38 to 0.60. The flat answer is
the sum of two real movements that cancel.

*Who acts on this:* a competition authority or regulator assessing market structure; an
entrant or acquirer sizing a route; anyone publishing an inequality trend computed over a
filing population rather than a fixed universe.

## Four traps, in the order you will hit them

### 1. A record count measures how finely activity was written down

![Record counts and tonnage move in opposite directions, by category](artifacts/charts/records.svg)

Rows are the first thing a register offers and the easiest thing to count. Per route,
records and tonnage move in **opposite** directions almost everywhere:

| route | records 2001 → 2023 | tonnage |
| --- | --- | --- |
| other recovery | ×23.8 | ×0.5 |
| landfill | ×3.5 | ×0.7 |
| wastewater treatment | ×1.4 | ×0.2 |
| other treatment | ×0.1 | ×0.7 |

Nobody made twenty-four times more waste. The filing granularity changed. **Plot the row
count against the quantity it supposedly tracks, one category at a time** — pooled, the
opposite movements average into a reassuring flat line.

The exception is the finding: **deep-well injection holds its tonnage (21.6M to 20.6M)
while its rows halve**, the only genuine consolidation in the file, and invisible in the
pooled view.

### 2. Few participants is not concentration, and can invert it

![The route with the fewest firms is the least concentrated of them all](artifacts/charts/hands.svg)

The route with the **fewest** firms in the register — deep-well injection, 31 companies —
has the **lowest** Gini, 0.63. Its plants are comparable in size. Other treatment has 77
companies and a Gini of 0.98, because one of them is 86% of it.

A first version of this figure plotted firm count against share of *national* tonnage and
read off "tons per firm": 31 companies, 666,000 tons each, therefore the most concentrated
route in America. **That statistic is average firm size.** It divides a national numerator
by a category denominator and says nothing about how evenly the route is divided. It
ranked the most equal route first.

**Draw one Lorenz curve per category with both axes normalised inside it**, so a route with
31 members and one with 367 overlay honestly. Scarcity of participants and inequality among
them are separate facts, and here they point opposite ways.

The curve also shows what neither summary does: **one plant — Ascend Performance Materials
at Chocolate Bayou, Texas — is 86% of "other treatment" and 18% of deep-well injection,
so 11.96M tons, 17.0% of every ton of hazardous waste managed in America, is one address.**

### 3. An inequality trend over a shrinking population measures two things

![Nothing concentrated, until you stop letting firms leave the sample](artifacts/charts/ginitrend.svg)

| route | firms 2001 → 2023 | Gini, all firms | Gini, largest 30 |
| --- | --- | --- | --- |
| other treatment | 258 → 77 | 0.96 → 0.98 | **0.70 → 0.95** |
| energy recovery | 84 → 54 | 0.74 → 0.77 | **0.38 → 0.60** |
| incineration | 135 → 104 | 0.83 → 0.88 | **0.43 → 0.63** |
| solvents recovery | 521 → 242 | 0.95 → 0.96 | **0.57 → 0.72** |
| wastewater treatment | 962 → 367 | 0.96 → 0.96 | 0.59 → 0.65 |
| metals recovery | 162 → 73 | 0.96 → 0.92 | 0.80 → 0.81 |

Firm counts fall 34% to 70% in every route. **Exits come off the bottom of the
distribution**, so losing small members *reduces* measured inequality at exactly the moment
the survivors pull apart. The two effects cancel almost exactly and produce a confident
flat line.

**Draw the member count as its own panel beside the statistic.** If it trends, the raw
series is uninterpretable. The same applies to a top-N share or an HHI.

### 4. A facility identifier is a gate, not an owner

`handler_id` names a site. Clean Harbors runs 21 of them, Safety-Kleen 18, Veolia 11.
Counting sites instead of owners moves landfill from 51 to 37 and fuel blending from 77 to
55. It changed no rank here — but it is a different question, and the register only labels
the gate. Names are normalised to an owner in every cycle independently, so a firm that
renames between cycles cannot distort a within-cycle Gini.

## What this cannot support

**Not a market-share analysis.** A route's tonnage is what a facility *handled*, not what
it was *paid for*. 97% of aqueous tonnage never leaves the site that made it, so a large
share of this register is captive volume that was never contestable. The concentration
measured here is of handling, not of trade.

**Not a causal account of why anything concentrated.** The register prices nothing — no
gate fee, no commodity price, no cost per ton. A companion analysis joined USGS metal
prices to the recovery series and found no relationship at all (rho −0.002 for lead plants
against the lead price, n=53, powered to detect 0.20), which rules a price story out as an
explanation of *throughput* but does not supply the real one.

**Not a statement about hazard.** A ton of contaminated soil and a ton of mercury are the
same number here.

**The 2021 cycle publishes no tonnage** and is omitted from every series. **`management_
category` contains a typo** — `SLUDGE TRTMNT / STAG / ENCAP` on 60 records in 2023 — which
any group-by on the raw string files as a thirteenth category. It is normalised, and the
figures say so.

## Reproducing

    cd recipes/waste-route-concentration
    python3 artifacts/scripts/fetch.py --all      # ~35 min, 8.0M rows, resumable
    python3 artifacts/scripts/records.py
    python3 artifacts/scripts/hands.py
    python3 artifacts/scripts/ginitrend.py
    python3 artifacts/scripts/verify.py           # recomputes every number above

`BR_CACHE` points the scripts at an existing pull if you have one. `verify.py` also fails
any figure whose SVG is older than the script that draws it — which is how a stale caption
survived in the workspace this came from, claiming a figure covered six management
categories long after the code had been loading twelve.
