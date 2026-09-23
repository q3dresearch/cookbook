# The facility directory is not a load proxy, by its own pre-registered test

Measured 2026-09-23. Q2 was written with an explicit falsifier: *if facility density and
balancing-authority load growth are uncorrelated, the directory is not measuring load and
should be dropped rather than caveated.* Run at state resolution, it fired.

## What predicts a state's 2015-2024 electricity growth

| predictor | r |
| --- | --- |
| PeeringDB facility count (log) | **+0.03** |
| PeeringDB network presences (log) | **+0.07** |
| facilities per million people | +0.20 |
| networks per million people | +0.18 |
| state electricity total (log) | +0.10 |
| **electricity per head, 2024** | **+0.64** |

**California is the counterexample that makes it concrete.** 148 facilities and 2,185 network
presences, the largest concentration in the country, and its electricity consumption **fell
5.9%** over the decade. Massachusetts, Connecticut and DC do the same thing on a smaller scale.

## What does predict it, and it is not compute or population

Electricity is growing where electricity was **already heavy per head**, and shrinking in the
dense low-intensity states.

| by electricity per head | median growth 2015-2024 |
| --- | --- |
| bottom third (~8,055 kWh/head) | **-3.4%** |
| top third (~16,503 kWh/head) | **+4.0%** |

Pearson +0.64, **Spearman +0.60**, and it survives every drop tried: without North Dakota
+0.57, without DC +0.64, without Wyoming +0.61, restricted to the 28 states above 50 TWh
+0.57. The rank statistic is the steadier one, which is what to quote when a single state
sits at 37,541 kWh per head.

The top of the growth table is North Dakota, New Mexico, Texas, Oregon, Virginia, Nebraska.
That is an industrial and extractive signal, not a population one.

## What this costs the recipe

**Q2's proxy is gone at state resolution.** Not weakened -- gone. r = +0.03 is not a small
effect, it is no effect, and the honest move is to say so rather than keep the directory
around with a caveat attached.

**Virginia is the only state in both the compute top three and the growth top five**, and one
state is an anecdote. It is the reason to go finer rather than a reason to believe the proxy.

## What survives

The question, at a resolution where it could still be answered. A state is too coarse:
Loudoun County is a rounding error inside Virginia and Virginia is one inside the nation. The
balancing authority is the next cut down, and the hourly EBA series carry demand and
generation by fuel for each of them from 2019.

**That is the test, not a rescue.** If BA-level load growth is also uncorrelated with compute
presence, then this register cannot see compute at any resolution it publishes, and *that*
becomes the finding -- which would be a more useful result than a weak correlation, because
it is checkable and it tells anyone else where not to look.
