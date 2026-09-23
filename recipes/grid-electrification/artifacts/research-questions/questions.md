# How much of civilisation runs on electricity, how much of that is compute, and what burns to feed it

Three questions in a chain. Each one is only worth asking if the one before it has an answer
in the data, and the chain is where this can go wrong: a tidy number at step three is easy to
produce and easy to be wrong about.

## The statute, read before the schema

Nobody files any of this because a law obliges them to name a data centre. That matters more
here than in a compliance register:

- **EIA's forms** oblige utilities and generators to report *sales by sector* and *generation
  by fuel*. A data centre is a commercial or industrial customer and is not separated out.
  There is no line on any form that says "data centre".
- **PeeringDB** is filled in *voluntarily*, by networks that want to be found for peering. It
  is a directory of interconnection, not an inventory of compute.
- **CBECI** is a model, not a return. It estimates from hash rate and an assumed hardware mix.

So every number about compute load in this recipe is a **proxy**, and the recipe's job is to
say how each proxy is biased rather than to launder it into a total.

## Q1. How much of the energy a place uses arrives as electricity?

EIA's **SEDS** gives total final energy and electricity by state and year, back decades. The
electrification share is a direct ratio and needs no modelling.

*What would make it misleading:* the denominator contains transport fuel, so the share moves
when oil demand moves and not only when electrification happens. **Falsifier:** if the share
rises in a year when electricity consumption per head was flat, it is the denominator moving.
Test it by holding transport out and reporting both.

## Q2. Where does compute sit, and how much of the load is it?

**No source answers the second half directly.** Candidate proxies, each with its bias named:

- **PeeringDB facilities** with latitude, longitude and a network count. Biased *toward*
  network-dense colocation and *away* from single-tenant hyperscale campuses, which often have
  no public peering presence at all. So it undercounts exactly the largest loads.
- **Balancing-authority load growth** (EIA **EBA**, hourly). Catches the load regardless of who
  owns it, but cannot attribute it: a BA that grew 30% may have gained data centres, air
  conditioning or a smelter.
- **CBECI** for bitcoin, which is a model with a stated uncertainty band and a geographic split.

*The honest form of Q2 is a bound, not a total.* **Falsifier:** if facility density and BA load
growth are uncorrelated across BAs, the directory proxy is not measuring load at all and should
be dropped rather than caveated.

## Q3. What is burning to feed it, and is "renewable" true for the right reason?

**EBA** gives hourly generation by fuel per balancing authority, so the mix where compute sits
is directly observable. Three traps sit on top of it:

1. **An annual average mix is the wrong denominator for a flat load.** A data centre running
   24/7 consumes the *marginal* mix at 3am, which in most of the US is gas or coal, not the
   solar that lifts the daytime average. Matching exposure means comparing the load's own hours,
   not the year.
2. **Crypto is sited on cheap and stranded power on purpose.** A high hydro share next to a
   mining farm is a fact about where hydro is cheap, not about a choice to be clean. The
   correlation is real and the causal reading is backwards.
3. **A grid mix is not a contract.** Power purchase agreements let a buyer claim renewable
   supply while consuming whatever the wires deliver. Nothing here can see a PPA, so the
   recipe measures **what the wires carried**, and must say so in those words.

**Falsifier for the headline:** if the fuel mix in high-compute BAs is indistinguishable from
the national mix once you match on hour and on region, then compute is not sited by carbon
intensity and the interesting claim collapses to "data centres are in places with electricity".

## What this recipe will refuse to produce

**A single number for "data centre share of national electricity".** Every input to it is a
proxy with a known direction of bias, and multiplying proxies is how a screen becomes
unfalsifiable -- the mistake this project already recorded as
[`dont-multiply-screening-signals`](../../../../webprobes/doctrine/). Bounds and per-region
comparisons, or nothing.

## Screened and gated

ERCOT returns **403** to an honest bot user-agent with a robots directive, so the Texas
large-flexible-load queue -- the best public record of crypto interconnection anywhere -- is
out of reach by that route. ENTSO-E and the EIA v2 API both want a free account. See
[`screens.md`](screens.md).
