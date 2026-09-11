# Questions this recipe asks

Written **before the fetch**, which is the point of doing it in this order.

## What the source is

**OpenRouter is a router.** A developer calls one API and OpenRouter forwards the
request to whichever lab's model they asked for, handling billing and failover.
It therefore sees the traffic of everyone who routes through it — and nobody who
calls Anthropic, OpenAI or Google directly.

`GET /api/v1/datasets/rankings-daily` returns the top 50 models per day plus an
aggregated `other` row, back to **2025-01-01**, in windows up to 366 days. The
unit is **tokens served**, not requests, downloads or benchmark votes. CC BY 4.0,
citation required. Needs an API key.

The publisher keeps its own history, which is why this is a larder recipe and not
a `wss` capture job.

## The caveat that governs everything below

**This is a router's traffic, not the market's.** Its mix reflects who routes
through OpenRouter — indie developers, agent frameworks, people who want to swap
models without swapping SDKs — and not the enterprise contracts that make up most
lab revenue. Any sentence of the form *"lab X is winning"* is wrong; the most
this can support is *"among developers who route, lab X is winning"*.

Whether even that holds depends on Q8, which is the one that could invalidate the
whole recipe.

*Who has a stake:* a developer choosing which model to build on · an investor
pricing a lab · anyone writing about AI market share who currently cites
download counts or leaderboard position.

| # | question | status | answer |
| --- | --- | --- | --- |
| 1 | Which labs gained and lost share? | `answered` | **The sketch was wrong about Anthropic.** 49.3% → 5.6% over 20 months. DeepSeek 4.3% → 22.4%, Google 16.8% → 7.5% |
| 2 | Is a lab's move one model, or all? | `answered` | **One or two.** Every lab runs 6–13 models and 23–82% of its tokens sit in the single biggest |
| 3 | How fast does a release peak? | `answered` | **Median 18 days** from first appearance to peak share (p25 7, p75 49) |
| 4 | What is a model's half-life? | `answered` | **10 days from peak.** All 194 models end below half their peak. Absolute half-life is also 10 days — the decay is real, not a denominator effect |
| 5 | Is the shift price-driven? | `answered` | **Yes.** corr(log price, share) = −0.33, and a 50-turn session spans 130× on price. See Q14 and Q16 |
| 6 | Tokens or requests? | `answered` | **Opposite orders.** Classification is 21.7% of requests and 5.4% of tokens; workflow execution 9.2% and 24.6% |
| 7 | Concentrating or fragmenting? | `answered` | **Fragmenting.** Top-3 share 73.4% → 43.4%; the `other` tail is flat at 4–7%, so it is new named labs, not a long tail |
| 8 | **Did the denominator move?** | `answered` | **Yes, and it is the finding.** Total routed volume grew **170×** in 20 months. Almost nobody shrank |
| 9 | Is the surge free-tier volume? | `tested and failed` | No. DeepSeek, Tencent, Z-AI and Xiaomi are **0% free-tier**. Only NVIDIA's volume is free |
| 10 | Do different workloads pick different labs? | `answered` | **Yes.** Code: OpenAI 29%, Z-AI 24%. Agent: Tencent 32%. General: DeepSeek 42%. OpenAI tilts 2.1× to code, DeepSeek 0.4× |


## The publisher's index — eight endpoints, not one

Probed rather than assumed. The `wss-openrouter` registry already knew six;
**`providers` and `app-rankings` were not in it.**

| endpoint | what it carries | key |
| --- | --- | --- |
| `datasets/rankings-daily` | top 50 models/day + `other`, back to 2025-01-01 | `model_permaslug` |
| **`datasets/app-rankings`** | top 50 **apps**, tokens **and requests**, any date window | `app_id` |
| `datasets/session-cost` | median USD per session by app, model and turn range | `model_permaslug` |
| `benchmarks?source=…` | three sources: artificial-analysis, design-arena, openrouter's own | `model_permaslug` |
| `classifications/task` | what the traffic is *for* — code, summarisation, roleplay, search | task |
| `models` | catalog: pricing, context length, **`hugging_face_id`** | `id` |
| **`providers`** | 106 providers with **`headquarters`** and **`datacenters`** | `slug` |
| `credits` | account balance; no research value |

404s worth recording so nobody re-probes: `apps`, `datasets/apps`,
`datasets/rankings-weekly`, `datasets/model-usage`, `classifications/app`,
`datasets/providers`, `analytics`, `datasets`.

**Join overlaps, measured not assumed.** Against August 2026 traffic:

| join | models matched | **share of tokens** |
| --- | --- | --- |
| rankings × benchmarks | 50 of 93 | **61%** |
| rankings × session-cost | 36 of 93 | **66%** |
| catalog → `hugging_face_id` | 183 of 437 | the bridge to `wss-hugging-face` |

Model-count overlap understates these badly: the matched models are the big ones.
The catalog's own join to rankings is the weak one — it is a *current* snapshot
against 21 months of history, so retired models are unpriceable, and even after
stripping the `-YYYYMMDD` suffix only 162 of 352 slugs match.

## Round two: what the other seven endpoints allow

| # | question | status | answer |
| --- | --- | --- | --- |
| 11 | **Who routes, and did that change?** | `answered` | **Feb 2025: Cline 45%, Roo Code 29%, SillyTavern. Aug 2026: Hermes Agent 37%, Claude Code, Kilo Code.** Assistants became agents |
| 12 | Tokens per request — did the workload change shape? | `answered` | **13.8k → 73.9k, a 5.4× rise.** The market grew in requests AND in length per request |
| 13 | Does capability predict usage? | `tested and failed` | **No, at all.** corr(intelligence, share) = **+0.02**; coding +0.09; agentic +0.14 |
| 14 | Does price predict usage? | `answered` | **Yes, negatively.** corr(log price, share) = **−0.33**. Under \$0.30/Mtok: 29% of tokens. Over \$5: 2.6% |
| 15 | Do downloads predict usage? | `tested and failed` | **No.** Spearman **+0.12** across 15 models holding 39% of tokens. gpt-oss-20b: 6.55M downloads, **0.22%** of tokens |
| 16 | What does a session cost? | `answered` | **A 50-turn kilo-code session: \$0.10 on mimo-v2.5, \$13.24 on claude-opus-5 — 130×** |
| 17 | What is the traffic FOR? | `answered` | Code+agent is **28% of requests and 72% of tokens**. General (classification, extraction) is 50% of requests and 22% of tokens |
| 18 | Where is inference served from? | `answered` | 106 providers: 55 US-headquartered, 6 Chinese, 32 unstated |
| 19 | Chinese models from Chinese datacenters? | `not observable` | **80 of 106 providers name no datacenter at all.** Exactly one names CN. The field exists and is mostly empty |
| 20 | Did the roleplay apps and labs die together? | `tested and failed` | **No — the timing does not match.** Labs hit zero by 2025-08; the apps held 7.5% and 7.2% into 2026 before falling. The use case outlived its specialist models |

## Labs are not interchangeable, they are specialised

Weighting each task's model breakdown by that task's token share:

| kind of work | top labs by tokens within it |
| --- | --- |
| **code** | openai 29%, z-ai 24%, deepseek 18%, tencent 12% |
| **agent** | tencent 32%, deepseek 20%, z-ai 20%, openai 14% |
| **general** | **deepseek 42%**, z-ai 15%, openai 14%, google 13% |
| **data** | deepseek 36%, openai 31%, z-ai 19% |

OpenAI tilts 2.1× toward code against general; DeepSeek tilts the other way at
0.4×, and dominates the high-volume, low-value general work — classification and
extraction — which is exactly the work that is 50% of requests and 22% of tokens.

Which is the mechanism under the tokens-versus-spend split: DeepSeek's volume is
concentrated in the cheapest work there is.

## A model's shelf life is about a month

Smoothed on a 7-day mean, across 194 models that ever held more than 0.5%:

* **18 days** from first appearance to peak share (p25 7, p75 49)
* **10 days** from peak to half of peak (p25 6, p75 25)
* **Zero of 194** end the record above half their peak

The first version of this measured a 2-day half-life, which was daily noise being
read as a peak. Smoothing fixed it. And because share is relative in a market
that grew 170×, the same thing was recomputed on **absolute tokens**: also 10
days. The decay is real, not the market growing around a model.

Claude 3.5 Sonnet peaked at 30.6% of all routed tokens on day 13 and halved in
31 days. Gemini 2.0 Flash peaked at 29.0% and halved in 41.

**Which is the answer to "what should I build on": whatever you pick has roughly
a month at the top, so the thing worth optimising is switching cost, not choice.**

## Why cheap wins: a 130× spread

`session-cost` gives the median USD per session by app, model and turn range. At
50-plus turns in Kilo Code:

| model | median session |
| --- | --- |
| mimo-v2.5 | **\$0.10** |
| claude-opus-5 | **\$13.24** |

In Codex at 50+ turns it is \$0.03 on deepseek-v4-flash against \$5.31 on
gpt-5.5. Agents run long sessions, so at the margin the model choice is a two
orders of magnitude cost decision — which is the mechanism behind every "cheap
wins" result above.

## Downloads are not use either

The catalog's `hugging_face_id` bridges to the `wss-hugging-face` archive, so
stated interest and revealed use are observable on the same models. They barely
relate — **Spearman +0.12**.

| model | HF downloads, 30d | share of tokens |
| --- | --- | --- |
| **openai/gpt-oss-20b** | **6,551,191** | **0.22%** |
| openai/gpt-oss-120b | 5,414,162 | 0.50% |
| **deepseek/deepseek-v4-flash** | 1,779,052 | **17.13%** |
| poolside/laguna-s-2.1 | 44,657 | 1.60% |

The most-downloaded model serves a fifth of a percent of tokens. DeepSeek-v4-flash
has four times fewer downloads and seventy-eight times more traffic.

**Downloads measure an intent to self-host** — or to evaluate, or simply to have.
**Tokens measure what people ran repeatedly and paid for.** Using one as a proxy
for the other, which is most AI coverage, is measuring the wrong verb.

**Scope, and it is a hard one.** This join only sees OPEN-WEIGHT models: a closed
model has no Hugging Face presence, so Claude and the GPT-5 series are absent by
construction. It says how open-weight popularity relates to open-weight use, not
how the market works. 15 models, so ranks are shown rather than a fitted line.

**Join arithmetic, measured:** 183 catalog rows carry a `hugging_face_id`; 72 of
those appear in the HF top-1000 by downloads; 15 of those carried August traffic.
Thin in models, 39% in tokens.

## The second reframing: tokens are not money

Multiplying each model's tokens by its input list price turns share of traffic
into share of spend, and it picks a different winner.

| lab | share of TOKENS | share of SPEND | ratio |
| --- | --- | --- | --- |
| **anthropic** | 8.4% | **41.3%** | **4.9×** |
| openai | 18.7% | 18.0% | 1.0× |
| z-ai | 15.0% | 12.2% | 0.8× |
| **deepseek** | **33.1%** | 9.4% | **0.3×** |
| moonshotai | 2.8% | 6.4% | 2.3× |
| xiaomi | 11.5% | 1.7% | 0.2× |

**Chinese labs are 65.7% of tokens and 31.4% of spend. Anthropic is 8.4% of
tokens and 41.3% of spend.**

So "DeepSeek is winning" is true in tokens and false in money, and the whole
first half of this recipe picked the denominator that makes it true. Both numbers
are real; the word "share" is doing the lying.

**What this is not.** Input-token list price only — completion tokens cost
several times more and are not counted, nobody large pays list, and it covers the
57% of tokens that join to a price. It is a direction, not an invoice.

And it sits *inside* the router caveat: this is spend routed through OpenRouter,
which is not lab revenue.

## Q13 in one line

**Measured capability does not predict usage.** The correlation between
Artificial Analysis's intelligence index and share of tokens is **+0.02**. The
most-used model in August scores 34.5; Claude Opus 5 scores 50.7 and serves 1.8%.
Benchmark leaderboards are not a demand forecast.

## The answer that reframes everything else

**The market grew 170× in twenty months.** Almost no lab shrank; they grew at
different speeds, and "losing share" here means "growing slower than 170×".

| lab | share Jan 2025 | share Aug 2026 | points | absolute growth | vs market |
| --- | --- | --- | --- | --- | --- |
| deepseek | 4.3% | **22.4%** | +18.2 | 894× | 5.3× |
| openai | 4.7% | 10.7% | +6.0 | 385× | 2.3× |
| tencent | — | 10.3% | +10.3 | new | — |
| xiaomi | — | 8.5% | +8.5 | new | — |
| google | 16.8% | 7.5% | −9.3 | 76× | 0.4× |
| **anthropic** | **49.3%** | **5.6%** | **−43.7** | **19×** | **0.11×** |
| mistralai | 4.2% | 0.1% | −4.1 | 5× | 0.03× |

**Anthropic's absolute volume grew nineteen-fold while its share fell
forty-four points.** Any sentence of the form "Anthropic is losing" is false on
this data. It grew, slower than a market that went up 170×.

The only labs whose absolute volume actually fell are a cohort of 2024-era
open-weight and roleplay models — meta-llama, microsoft, gryphe, nousresearch,
sao10k, thedrummer, openchat, neversleep. Those genuinely died.

And the surge is **paid traffic**: DeepSeek, Tencent, Z-AI and Xiaomi serve 0%
of their tokens through free-tier variants. Only NVIDIA's volume is free-tier.
Chinese labs are **55.8% of tokens routed** in August 2026.

## What I expect to find, written down now so it can be wrong

* Q1 will hold, because it came from a real query.
* Q2 will show the moves are **one or two models each**, not a lab-wide tide.
* Q6 will show token share and request share disagree, and that the disagreement
  is largest for whichever lab sells the longest context.
* Q8 is unanswerable from this endpoint alone and will end up the recipe's
  binding limit, the way coverage was for the CFR and the self-determination
  branch was for GRAS.

**Scored afterwards:** Q1 was wrong — the sketch in the old README had Anthropic
flat at 15%, and it is 5.6% and falling. Q8 was half right: the denominator *did*
move and it is measurable, but it does not invalidate the recipe. It changes what
the recipe is about, from "who is winning" to "the pie grew 170× and the new
volume went somewhere different from the old".

Recording the prediction because a guess written afterwards is not a prediction.
