# What the facility directory can and cannot say

Measured 2026-09-23 on 5,877 facilities fetched from PeeringDB, 1,376 of them in the US.

## It can locate compute. 98.3% carry coordinates.

1,353 of 1,376 US facilities have latitude and longitude, and only 9 have no state. That is
the join Q2 and Q3 both rest on, and it holds.

| state | facilities | share | network presences | share | networks per facility |
| --- | --- | --- | --- | --- | --- |
| CA | 148 | 10.8% | 2,185 | 17.7% | 14.8 |
| TX | 113 | 8.3% | 1,279 | 10.3% | 11.3 |
| VA | 85 | 6.2% | 1,006 | 8.1% | 11.8 |
| NY | 84 | 6.1% | 835 | 6.8% | 9.9 |
| IL | 71 | 5.2% | 823 | 6.7% | 11.6 |
| **OH** | **60** | **4.4%** | **209** | **1.7%** | **3.5** |

**Half of all US network presence sits in 54 facilities -- 4.0% of them.** Counting buildings
and counting interconnection are different measurements, and the recipe must name which base
any share is on, exactly as the procurement recipe had to.

**Ohio is the tell.** Seventh by facility count and eighteenth by network count, at 3.5
networks per facility against California's 14.8. That is the signature of single-tenant or
wholesale space rather than carrier hotels -- which is the population this directory is
supposed to be blind to. So the blindness is partial, and the ratio may be a usable
discriminator between colocation and hyperscale rather than a defect to apologise for. **Worth
testing**, not yet tested.

## It cannot date construction, and the field that looks like it does is a trap

`created` runs 2010-07-29 to 2026-04-27, with **165 rows created in 2010** -- PeeringDB's own
seed import, not a building boom. `updated` runs only 2025-09-26 to 2026-09-18, so every row
was touched in one recent refresh.

Facilities by creation year: 2010:165, 2016:172, 2020:111, 2024:50, 2025:62.

Read naively that is a **construction slowdown during the largest data-centre buildout in
history**, which should be disqualifying on sight. It is not construction. It is the
directory's adoption curve: 44% of US rows were created on or before 2016, when PeeringDB was
filling up.

**Nothing in this recipe may use `created` as a build date.** The same shape as
[`an-adoption-curve-can-be-a-code-migration`] -- a field that increments when a *record*
appears, read as if it increments when a *thing* appears.

## What is still unknown

- Whether facility density predicts balancing-authority load growth. If it does not, the
  directory is not measuring load and Q2 loses its proxy rather than gaining a caveat.
- Whether networks-per-facility separates colocation from hyperscale, or just separates big
  metros from small ones.
- How much of the hyperscale fleet is absent entirely. By construction this cannot be measured
  from inside PeeringDB, and the honest answer is a bound from an outside count, not a
  correction factor.
