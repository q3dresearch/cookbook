# The fetch constraint, measured before anything was built

Recorded here because it decided the design, and because a reproducer on a different vantage
point will get different numbers and needs to know what to compare against.

## What was measured

Six requests from a residential connection, each opening a fresh TCP+TLS connection via
`urllib`:

| request | payload | elapsed |
| --- | --- | --- |
| `/studies?pageSize=1&countTotal=true` | 10,030 B | 133.3 s |
| the same, again | 10,030 B | 134.5 s |
| the same, a third time | 10,030 B | 135.2 s |
| `/stats/field/values?fields=OverallStatus` | 818 B | 135.2 s |
| `/stats/size` | 7,302 B | 135.1 s |
| `/studies/download?format=csv&…` | HTTP 400 | 133.1 s |

A bare TCP connect to port 443 took **15.0 s**. For comparison, `search.rcsb.org` on the same
machine, in the same session, connected in 0.3 s and answered in under a second.

## What that rules out

**Payload is not the cost.** 818 bytes and 10,030 bytes took the same time to within a second.
A server doing work does not behave like that; a fixed toll does.

**Paging is not available.** 603,730 studies at the API's maximum 1,000 per page is 604
requests. At 135 s that is **22 hours**, so any design that walks the register row by row is
not a design.

**A bad request fails loudly.** The 400 above is a *good* screen result: this API validates and
rejects rather than silently returning the unfiltered total, which is the failure mode that
has cost this project real findings elsewhere. The 400 is a syntax error in the request, not
evidence the endpoint is missing.

## What it forces

**Batch every marginal into one call.** `/stats/field/values` takes a comma-separated list of
fields and returns each one's value distribution together with a `missingStudiesCount`. Twelve
marginals cost one request rather than twelve — the difference between two minutes and
twenty-seven.

**Cache beside the artifact, never refetch.** At this price a cache is not a temporary file,
and `/tmp` is the wrong place for it.

## Resolved: the cost is per connection, and it is the whole cost

One `http.client.HTTPSConnection`, held open, four requests down it:

| step | payload | elapsed |
| --- | --- | --- |
| connect (TCP + TLS) | — | **134.3 s** |
| `/studies` count, all | 10,030 B | **0.3 s** |
| `/studies` count, completed | 40,149 B | **0.3 s** |
| `/studies` count, terminated | 18,740 B | **0.3 s** |
| `/stats/field/values?fields=Phase` | 386 B | **0.3 s** |

Four requests, 135.5 s total, of which 134.3 s was getting the socket open. **Requests on an
established connection are about 450x faster than the same requests measured through
`urllib`**, which opens a fresh connection each time and so pays the toll again on every call.

The 135 s was never the API. It was connection setup, and the earlier measurements could not
see that because every one of them included a new handshake.

**What this changes.** Everything. Paging the whole register is 604 requests, which at 0.3 s
is about three minutes rather than twenty-two hours. The reporting-lag question — two dates
from the same row, the one the statute makes worth asking — is affordable after all, and the
scope does not need to shrink.

**What it costs to get wrong.** Had the fetcher been written against the first six
measurements, it would have been built to avoid requests at any price: no paging, no
per-study values, and the central question quietly dropped as unaffordable. The whole recipe
would have been shaped around an artefact of the HTTP client.

**The general form, for the next source.** A latency that barely moves across an order of
magnitude of payload is not a server working, it is a fixed toll. Before designing around it,
find out what it is charged on — per request, per connection, per host — because a toll paid
once is not a constraint at all.

## A correction, added 2026-09-22

This file reads as though ~135 s of connection setup is a property of
`clinicaltrials.gov`. It is not, and the numbers that show it were collected later against a
different host:

| host | connect | measured |
| --- | --- | --- |
| `search.rcsb.org` | **0.3 s** | same machine, same session |
| `clinicaltrials.gov` | ~134 s | three times |
| `aact.ctti-clinicaltrials.org` | **180 s, then 240 s** | twice, minutes apart |

So the toll is **per host-pair and highly variable**, not a fixed cost of this API, and a
reproducer on another connection may see none of it. **The finding that survives is the one
that mattered: the cost is charged on the connection, not the request.** That is what makes a
held-open session worth writing, and it holds regardless of how big the toll happens to be
from where you are sitting.

## What is still open

**The CSV download returned HTTP 400** and has not been retried with corrected syntax. It is
now optional rather than load-bearing: with a persistent connection, paging JSON is cheap
enough that a bulk endpoint buys little. The 400 is kept in the screens as evidence this API
rejects bad input loudly instead of silently returning the unfiltered total.
