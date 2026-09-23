# What this register can be asked, once you know what is in it

EBA is 4.35 GB of hourly series per balancing authority from 2019 to last week. A first read
assumed it carried demand and generation by fuel. It carries four more things, and two of them
change which questions are worth asking.

| measure | series | what it is |
| --- | --- | --- |
| `D` | 258 | demand, hourly |
| `NG.{fuel}` | ~840 | net generation by fuel: NG, COL, WAT, SUN, WND, NUC, OIL, OTH, UNK |
| `TI` | 164 | total net interchange |
| **`ID`** | **534** | **directed flow between a specific pair of balancing authorities** |
| **`CO2.CON`** | **126** | **CO2 from electricity *consumed*, imports included** |
| `CO2.IMPR` | 118 | CO2 arriving inside imported power |

## The question that rescues Q2, and it is about shape rather than place

**A data centre is a flat 24/7 load. Almost nothing else on a grid is.** Air conditioning
peaks in the afternoon, heating in the morning and evening, industry follows shifts. So a
balancing authority that gains compute should get *flatter*: its load factor -- mean demand
over peak demand -- should rise, and its overnight trough should rise faster than its peak.

**That is a far better instrument than counting buildings**, which failed at r = +0.03. It
measures the thing itself rather than a directory's opinion about where the buildings are, and
it needs no join at all.

*Falsifier:* load factor also rises when a grid loses peaky load, so a BA that deindustrialised
would look identical. The test has to separate a rising trough from a falling peak, and only
the first is new load.

## The question EIA already answered, which I was about to model badly

**`CO2.CON` is consumption-based carbon per balancing authority, hourly.** Q3 was going to
approximate this by weighting a BA's own generation mix. That would have been wrong in a
specific direction: **a grid can generate clean and consume dirty**, by importing. `CO2.IMPR`
isolates exactly that term and `ID` says who it came from.

So the honest Q3 is not "what is the mix where compute sits" but **"what did the wires actually
deliver, after imports"** -- and the register computes it already. Any figure here that uses a
BA's own generation share where a consumption figure exists is choosing the flattering number.

## Six more the file can carry

**1. Average against realised.** A flat load consumes every hour equally, so its realised
carbon is the *time-weighted mean of hourly intensity*, not the annual average. Where solar is
large those differ a lot, and every corporate "100% renewable" claim on an annual basis lives
in that gap. Directly computable: hourly `CO2.CON` divided by hourly `D`, averaged flat,
against the annual ratio.

**2. Who is clean because of their neighbours.** Rank BAs by their own generation mix, then by
`CO2.CON`. The ones that move are importing their virtue. `ID` names the counterparty.

**3. Is the peak growing faster than the energy?** Annual demand and annual peak demand are
different series with different capacity consequences. A grid whose energy is flat and whose
peak is rising needs plant it will barely use.

**4. Has weather sensitivity changed?** Heat pumps move heating onto the grid and should show
as rising winter-morning demand per degree. This needs an outside temperature series, so it is
a join, and the join is the risk rather than the data.

**5. What does the marginal hour burn?** The last unit dispatched at 3am is not the average
unit. This is the number that decides whether new flat load is clean, and it is why the
annual average is the wrong denominator for a data centre.

**6. Does the fuel mix at a given hour predict the next hour's imports?** A grid that runs out
of its own clean generation imports; the shape of that handover is the physical meaning of
"how much can this grid absorb".

## What is deliberately not here

**No prices.** Curtailment, negative pricing and the economics of siting are invisible in this
file, and the questions that need them belong to a different source.

**No customer class.** Demand is demand. Nothing separates a data centre from a smelter, which
is exactly why the shape question above is worth more than any attempt to attribute load by
sector.
