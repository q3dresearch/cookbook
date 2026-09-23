# Screening: can four grids be compared at regional granularity without an account?

Probed 2026-09-23 with an honest bot user-agent. Every timing below is a first request to
that host on this machine.

## What answered

| source | status | first request | granularity below the country |
| --- | --- | --- | --- |
| **EIA bulk** (US) | 200, **no key** | **540s** for the manifest | balancing authority (EBA), state (ELEC, SEDS) |
| **OPSD** (EU) | 200, no key | 2.1s | bidding zone -- 21 codes, including `IT_NORD`, `IT_CSUD`, `IT_SUD`, `DE_LU`, `GB_GBN`/`GB_NIR` |
| **NESO** (UK) | 200, no key | 1.1s | DNO licence area, generation charging zone; 129 datasets |
| **AEMO** (AU) | 200, no key | 2.3s | NEM region (state); 104 report directories, 37 relevant, including per-unit SCADA |

## What did not

| source | status | what it wants |
| --- | --- | --- |
| EIA API v2 | **403** `API_KEY_MISSING` | a free key |
| ENTSO-E Transparency | **401** | a free account token |
| IRENA | **403** | blocked outright to this UA |
| Ember monthly CSV | 200 but `text/html` | the guessed URL is a landing page, not the file |

**The account question arrives again, and this time it does not block.** ENTSO-E is the
canonical European source and it is gated, exactly like AACT and EIA-860M. But the EIA *bulk*
endpoint needs no key even though the v2 API does, and OPSD republishes ENTSO-E's series under
an open licence. So the recipe can be built keyless, and the gated sources become a stated
limitation rather than a dependency. That is worth knowing before anyone registers for
anything.

## The toll, again

**EIA 540s for a 28 KB manifest. Ember 162s. OPSD, NESO and AEMO 1-2s.** The pattern is the
one this project already recorded: latency is charged on connection setup for certain host
pairs, not on payload. Any EIA fetcher must hold one connection open for the whole walk, as
`usa.py` does for USAspending -- see
[`find-what-the-toll-is-charged-on`](../../../../webprobes/doctrine/).

## The risk that actually threatens this recipe

**It is not a key join, so "verify the join before selling it" does not apply in its usual
form.** Nothing here shares an identifier. The comparison is definitional, and the ways it can
fail are:

1. **A "region" means four different things.** A US balancing authority is an operational
   control area, an Italian bidding zone is a price area, a UK DNO area is a wires franchise,
   an Australian NEM region is a state. They are not the same object and no reconciliation
   makes them one.
2. **"Capacity" means nameplate in one place and de-rated in another**, and the vintage of a
   monthly inventory differs from an annual statistical return.
3. **Electrification and decarbonisation are different questions** and generation data speaks
   mostly to the second. Fuel mix is directly observable; end-use electrification shows only
   as demand growth, which is confounded by weather, efficiency and industrial composition.

The screen's verdict is that the recipe is buildable **as four parallel measurements with
their own definitions stated**, and not as a pooled cross-country table. A pooled table is the
failure mode to avoid, and it is the one that looks most like a finished product.
