# The Economics of Long Context and Agentic Work

*A research note for future sessions. What we asked, what we found, what we built,
and — importantly — where the first answers were wrong. Written 2026-10-25.*

> **Post-publication correction (2026-10-26).** The first draft charged the 25%
> cache-write premium even when caching was off. That inflated the uncached
> 30-turn Sonnet loop from **$17.44 to $21.74** and the append saving from
> **82% to 85%**. The published figures use the corrected model; the $21.74
> cold-cache number is unchanged, because a configured cache that has expired
> does re-write every turn. The numbers below are the pre-correction draft and
> are kept as the record of what was tried.

---

## TL;DR

- **Long context is now the majority of token volume, and it is exploding.** On
  OpenRouter, requests in the 100K–1M context bucket were **49.8%** of all tokens
  (Apr–Sep 2026) and grew **10.7× in six months** (31.5T → 338T/month). Requests
  above 1M are **0.07%** — the advertised window is far ahead of actual use.
- **Both naive cost models are wrong.** "Only output is valued" ignores prefill
  compute and KV residency. "5× input ⇒ 5× cost" is only true for flat-priced
  models with short outputs; tiered pricing makes it ~9×, and caching pushes it
  back toward ~2.6×.
- **Caching is the dominant user-side lever — but it is ~10%, not ~1%, and only
  when the cache is warm.** Append-only caching cut an agent loop ~85%. A cold
  cache (TTL expiry) restores the full bill exactly.
- **Server-side, prefill attention is 95–100% of GPU time at long context.** The
  O(L²) term is the whole story. Hybrid attention cut 1M-context serving ~3.4×.
- **Workloads split by which side of the ratio dominates:** code is
  input-dominated (~25:1), SVG/CAD are output-dominated.
- **Reliability beats token price for hard knowledge work.** At `p_success = 0.6`
  with `$15` remediation, ~77% of cost-per-solved-task is failure cleanup.
- **Budget with P90, not the point estimate.** Simulated P90 is ~2.5–3× the
  deterministic estimate; the distribution is right-skewed.
- **No canonical "tokens per knowledge worker" index exists.** The closest
  fragments are the Anthropic Economic Index, OpenAI GDPval, and the emerging
  "cost per task" metric. We built a `$/human-hour-equivalent` replacement index.

---

## 1. The question

Started from a simple-sounding question: **if a 200K-context model and a 1M-context
model differ 5× in input capacity, what are the unit economics, and how should a
user (and a server operator) expect the bill and the hardware cost to behave?**

Sub-questions that turned out to matter more than the original:

1. Is the cost difference "identical" (output-only) or "5×" (input-proportional)?
2. Does prompt caching make re-sending history free?
3. Do providers/aggregators measure this? (OpenRouter, OpenCode)
4. Do data centers serve fewer users at 1M because of KV-cache reservation?
5. Is there an index for "tokens to replace a knowledge worker"?

---

## 2. What we built

A small, dependency-light model plus an exporter. Everything lives in `llm-econ/`.

| File | Purpose |
|---|---|
| `llm_econ.py` | Pricing registry, architectures, hardware, workloads, `user_cost`, `server_cost`, `Task`, `cost_per_task`, Monte Carlo |
| `export.py` | Builds `out/llm-econ.xlsx` (13 sheets), 12 CSVs, 11 plots |
| `out/` | Generated artifacts (workbook, CSVs, PNGs) |
| `README.md` | Short usage notes |

Reproduce:

```bash
# system python is enough for the model; the repo .venv has openpyxl+matplotlib
.venv/bin/python llm-econ/export.py
```

The workbook is **live**: the `Inputs` sheet drives a formula-based `Turn Model`
sheet (395 formulas, 0 errors). It reproduces the Python model to 4 decimals.
`recalc.py` (LibreOffice) is used to cache formula values.

### Core formulas

```
User bill per turn   = cached·cache_read + fresh·in_rate·write_mult + out·out_rate
                       (whole request × tier multiplier if context > cliff)
KV bytes / token     = kv_per_layer_token · n_layers · kv_bytes
Prefill FLOPs        = 2·N_active·L + 4·n_layers·n_heads·d_head·L²·full_attn_frac
Decode step time     = max( (weight_bytes + batch·KV) / bandwidth,
                            arithmetic ) / batch
Cost per solved task = attempt / p_success + (1 − p_success)·remediation
```

---

## 3. Findings

### 3.1 Long context dominates, and the tail is a power law

OpenRouter `datasets/rankings-daily`, `context_bucket` ∈ {1K,10K,100K,1M,10M},
Apr–Sep 2026:

| Bucket (context) | Share of tokens |
|---|---:|
| ≤1K | 0.8% |
| 1K–10K | 9.9% |
| 10K–100K | 39.5% |
| **100K–1M** | **49.8%** |
| >1M | 0.07% |

Monthly 1M-bucket volume: 31.5T (Apr) → 110.9T (Jul) → 338.1T (Sep).

**Interpretation:** the *average request* is short (~6K tokens per OpenRouter's
State of AI), but the *average token* lives in a long context. A small share of
sessions drives most spend. Cheap/open-weight models dominate the long-context
bucket (MiMo, DeepSeek V4 Flash, Hunyuan, GLM, MiniMax, free Nemotron) — the
market already routes length to low per-token price.

### 3.2 Both naive cost models are wrong

- "Output-only" fails because input has real costs: **prefill compute** (quadratic
  attention) and **KV residency** (linear in context × concurrency).
- "5× input ⇒ 5× cost" holds only for flat-priced models with near-zero output.
  Tiered pricing (Gemini, older Claude, xAI) re-prices the **whole request** above
  200K at 2× input / 1.5× output, making it ~9×.

Worked examples (200K vs 1M prompt, 5K output):

| Model | 200K | 1M | Ratio |
|---|---:|---:|---:|
| Sonnet 4.6 (flat) | $0.675 | $3.08 | ~4.6× |
| Sonnet 4.5 (tiered) | $0.675 | $6.11 | ~9.1× |
| Gemini 2.5 Pro (tiered) | $0.30 | $2.58 | ~8.6× |

### 3.3 Caching is the dominant lever — and the first model got it wrong

**Correction for future sessions:** the initial simulator cached only a *fixed*
prefix (system prompt). That is nearly worthless. Real agent loops are
**append-only**, so the entire prior context is the prefix. Fixing this changed
the answer:

| Sonnet 4.6, 30-turn loop (10K→372K) | Cost |
|---|---:|
| no cache | $21.74 |
| fixed 8K cache | $20.94 (≈ no help) |
| **append cache** | **$3.23** (~85% saving) |

Cache also **collapses the window penalty**: uncached, no-cap vs 200K-cap was 48%
apart; with append caching it is 27% ($3.23 vs $2.35). This substantially
vindicates the "just use the bigger window" instinct — *when the cache is warm*.

But the "~1%" intuition is wrong: cache reads are **~10%** of input price
(Anthropic/Gemini), ~3–22% for DeepSeek. Per-turn cost still scales linearly with
context; caching scales the whole curve down, it does not flatten it.

### 3.4 TTL and storage are the silent killers

- **TTL expiry is a cliff, not a slope.** Sonnet loop: $3.23 with 60s between
  turns; **$21.74** with 600s (5-min TTL expires every turn). Claude Code's cache
  TTL was reportedly cut 1h→5m, so this is a live operational issue.
- **Partial invalidation is brutal.** At 70% cache-hit rate you have already lost
  ~two-thirds of the benefit ($8.78 vs $3.23 at 100%).
- **Some providers charge storage.** Gemini $4.50/1M/hr; for a 30-turn session,
  storage was ~40% of the cached bill and grew with turn gap.
- **Real cache-hit rates are 8–92%**, not 100% (Requesty coding-agent data;
  GitHub Copilot: ~90% within session, 55% at turn boundaries, **8% on model
  switch**; compaction erases a median 66% and ≥90% in 34% of events).

### 3.5 Server-side: prefill attention dominates; architecture > pricing

Roofline model, one request, 1,000 output tokens, batch 64:

| Context | Prefill share of GPU time | Server floor | Flat user price ($3/M) |
|---:|---:|---:|---:|
| 10K | 58% | $0.004 | $0.045 |
| 200K | 95% | $0.197 | $0.615 |
| 1M | **99%** | **$3.92** | $3.02 |
| 1M, hybrid attention (¼ full layers) | 96% | **$1.16** | $3.02 |

- **At 1M, a flat $3/M price sits below the GPU floor** in this model — the reason
  tier cliffs exist. Anthropic later removed its premium for 4.6+, implying
  efficiency gains closed the gap.
- **Hybrid/sparse attention is the biggest server lever** (~3.4× at 1M).
- **KV cache sets concurrency**: ~160 KB/token for 70B GQA (fp8) → 164 GB/seq at
  1M, which does not fit a single 80 GB H100. MLA (DeepSeek) is ~35 KB/token
  (~35 GB/seq at 1M) — the reason cheap long-context models exist.
- **A cache hit removes prefill but not decode KV reads.** Decode still reads the
  full KV every token, so provider cost stays linear in context. This is the part
  caching does not fix.

### 3.6 Workloads split by ratio

| Task | Tokens in | Tokens out | in:out | Dominant side |
|---|---:|---:|---:|---|
| chat / QA | 18K | 2.4K | ~7:1 | input |
| agentic code | **1.38M** | 25K | **~55:1** | **input** |
| knowledge deliverable | 411K | 18K | ~23:1 | input |
| SVG / vector art | 1K | **6K** | 1:6 | **output** |
| CAD / 3D script | 18K | 6K | ~3:1 | output-leaning |
| RAG / summarize | 100K | 1.2K | ~83:1 | input |

External anchors: Vantage's 50-turn coding session ≈ 1M in / 40K out; Bai et al.
(arXiv 2604.22750) find agentic coding consumes ~1,200× a chat turn, input:output
>150:1, with up to **30× run-to-run variance**; Gartner puts agentic at 5–30× a
chatbot. Playcode found identical SVG tasks where one model emitted **8.8×** the
output tokens of another.

### 3.7 Reliability beats token price for hard knowledge work

Expected cost per solved task (Sonnet 4.6): chat $0.13, RAG $0.66, SVG $0.69,
CAD $2.18, code $2.95, **knowledge deliverable $7.79**.

For the knowledge deliverable at `p_success = 0.6`, `$15` remediation:
attempt = $1.07 → solved = $7.79. **~77% of the cost is failure cleanup.**
Moving from DeepSeek to Sonnet changes this only ~1.3× despite a ~30× token-price
gap — because remediation dominates. For reliable tasks, token price is the whole
story; for unreliable ones, it barely matters.

### 3.8 Uncertainty: P90 is the planning number

2,000-run Monte Carlo (Beta for `p_success`/cache-hit, lognormal σ=0.85 for token
variance, lognormal for remediation):

| Task (Sonnet) | Point | P50 | **P90** | Mean |
|---|---:|---:|---:|---:|
| chat | $0.125 | $0.13 | $0.37 | $0.18 |
| agentic code | $2.95 | $3.28 | **$8.62** | $4.39 |
| knowledge deliverable | $7.79 | $8.59 | **$19.45** | $10.50 |
| SVG | $0.69 | $0.77 | $1.74 | $0.94 |
| CAD | $2.18 | $2.37 | $5.33 | $2.90 |
| RAG | $0.66 | $0.71 | $1.68 | $0.90 |

P90 ≈ 2.5–3× the deterministic estimate. **Tornado (what moves the bill):**
- code → **token volume** ($6.18 swing) > p(success) ($1.30) > remediation ($1.23)
- knowledge deliverable → **remediation** ($12.27) > token volume ($4.71) > p(success) ($4.58)
- CAD → **remediation** ($3.68) > p(success) ($1.00)
- chat/RAG → token volume

So: optimize tokens for reliable work; optimize **reliability** for judgment-heavy
work. Cache is a code/agent lever, not a knowledge-work lever (one-shot tasks
never reuse the prefix within the task).

### 3.9 Replacement index

`$/human-hour-equivalent = AI $/solved task ÷ human hours`, against a $70 loaded
hourly rate (Sonnet 4.6):

| Task | AI $/hr-eq | vs $70 human |
|---|---:|---:|
| chat | $1.25 | 56× cheaper |
| agentic code | $0.74 | 95× cheaper |
| knowledge deliverable | $1.04 | 67× cheaper |
| SVG | $1.38 | 51× cheaper |
| CAD | $1.45 | 48× cheaper |
| RAG | $1.33 | 53× cheaper |

**~50–95× cheaper per hour of work replaced**, *before* HITL, verification,
integration, and error remediation. The weakest case is the highest-value one
(knowledge deliverables), because failure rate eats the margin. That is the honest
boundary of "replacing a knowledge worker."

---

## 4. External cross-references

- **Epoch AI, Erdil, "Inference economics of language models"** (arXiv 2506.04645)
  — the canonical roofline; KV formula; long-context is memory-bandwidth bound;
  MLA ~6× cheaper than GQA at slow inference.
- **OpenRouter State of AI / datasets API** — context buckets, category splits.
- **Requesty** — coding-agent cache hit rates (46–92%).
- **GitHub Copilot production study** (arXiv 2608.00101) — cache lifecycle,
  turn-boundary 55%, model-switch 8%, compaction erases cache.
- **Anthropic Economic Index** — tokens per occupation/task; higher-wage
  occupations use ~2.07× the tokens; 57% augmentation vs 43% automation.
- **OpenAI GDPval** (arXiv 2510.04374) — 44 occupations, ~$400/task, 7–9 expert hrs.
- **Artificial Analysis** — GDPval-AA and Coding Agent Index (cost per task).
- **Bai et al.** (arXiv 2604.22750) — agentic token consumption, 30× variance.
- **Gartner (Mar 2026)** — agentic 5–30× chatbot tokens.
- **Playcode** — SVG output-token variance.

### On "tokens to replace a knowledge worker"

There is **no canonical index**. The fragments are: Anthropic Economic Index
(tokens per occupation), GDPval (task → value/time), Artificial Analysis (cost per
task), and practitioner "cost per usable token" (~$25–40/M for a $100k worker).
The emerging unit is **cost per completed task**, and the right construction is:

```
occupation → task decomposition (ONET) → tokens/task × $/token
           × attempts / p_success → $/task → $/FTE-equivalent
```

---

## 5. Caveats: modeled vs measured

- **Measured:** OpenRouter bucket shares and growth; external cache-hit rates;
  external token profiles (code, SVG, GDPval).
- **Modeled:** all dollar figures, server GPU costs, `p_success`, remediation,
  human hours, and the Monte Carlo distributions. These are assumptions with
  cited priors, not invoices.
- **Server numbers** are single-instance GPU-rental floors with assumed
  MFU/MBU (0.5/0.75); real providers have quantization, cache-hit rates, and
  hardware we cannot observe. Treat them as directional.
- **Vendor/model names in 2026 sources** are reported as the sources state them.
- The model is deterministic per scenario except in the Monte Carlo layer.

---

## 6. Open questions / next steps

1. **Routing optimizer** — cheapest model per task subject to a `p_success` floor.
2. **FTE / org rollup** — task mix × volume → annual spend and headcount-equivalent.
3. **Real-spend calibration** — pull actual OpenRouter generations and fit the model.
4. **Cache across tasks** — current model only caches within a task; cross-task
   corpus caching is the real RAG lever.
5. **Workload coverage** — 3D/CAD and video editing are thin; video is mostly not
   LLM-token driven.

---

## 7. File map

```
llm-econ/
├── llm_econ.py            # model: pricing, arch, workloads, tasks, Monte Carlo
├── export.py              # workbook + CSV + plots
├── README.md
├── RESEARCH-NOTES.md      # this file
└── out/
    ├── llm-econ.xlsx      # 13 sheets: Inputs, Turn Model, Scenario Summary,
    │                      #   TTL Break-even, Window vs Cost, Cache Hit Sensitivity,
    │                      #   Server Econ, Workloads, Cost Per Task,
    │                      #   Replacement Index, Cache Priors, Monte Carlo, Tornado
    ├── *.csv              # billing, caching, ttl, hit, window, server, workloads,
    │                      #   cost_per_task, replacement_index, cache_priors, mc, tornado
    └── plot_*.png         # 11 plots
```

**If you only read one thing:** the point estimate is P50; budget P90; and the
first-order lever is *task reliability*, not the context window.
