# Questions this recipe asks

Written **before** the model was built, which is the point of doing it in this
order. The list is the work queue: what was asked, what was answered, and what is
open with the reason it is open and what would close it.

## What the source is

There is no corpus. The source is a price sheet, a roofline and a set of cited
priors about workloads. `llm_econ.py` prices the same request from three sides —
the user bill, the provider's GPU floor and the cost of a solved task — and every
dollar is arithmetic on assumptions rather than a captured invoice.

The measured inputs are external: coding-agent cache-hit rates (Requesty, GitHub
Copilot), token profiles (Vantage, OpenAI GDPval, Playcode) and list prices. They
are named in [`../../provenance.json`](../../provenance.json).

## The caveat that governs everything below

**This is a model, not an invoice.** A sentence of the form *"model X costs $Y"*
is conditional on the workload, the cache policy and the `p(success)` assumption.
What the recipe can support is a direction and a boundary: which lever moves the
bill, by roughly how much, and at what point it stops paying. What it cannot
support is a claim about a specific contract, provider margin or worker
replacement.

*Who has a stake:* a team budgeting an agent · a provider pricing a long-context
tier · anyone comparing models on "cost per token".

| # | question | status | answer |
| --- | --- | --- | --- |
| 1 | Does a 5× bigger window cost 5×? | `answered` | **No.** 4.6× flat, 8.9× tiered. The tier re-prices the whole request, not the excess |
| 2 | Does caching make re-sent history free? | `answered` | **No.** 82% saving when the grown history is cached and warm; the same loop costs $21.74 when the cache is cold. A fixed 8K prefix saves 3.6% |
| 3 | Is a cache hit all-or-nothing? | `answered` | **No.** A 70% hit rate costs $8.78, 2.7× the warm bill. Below roughly a 23% hit rate, append caching costs more than not caching |
| 4 | What hit rates do real agents see? | `answered` | **8–92%.** Claude Code 91.9%, OpenCode 89.0%, Kilo Code 45.5%, Copilot on a model switch 8.0% |
| 5 | Does a cache hit remove the provider's cost? | `answered` | **Prefill yes, decode no.** The KV cache is still read every output token, so the 1M floor does not fall to zero |
| 6 | At 1M, does the provider make money on a flat $3/M price? | `answered` | **No in this model.** The 70B GQA floor is $3.92 against a $3.02 list price. Hybrid attention: $1.16, above water |
| 7 | Does the architecture or the price sheet matter more? | `answered` | **Architecture.** Hybrid attention cuts the 1M floor 3.4×. MLA's small KV does not save it, because its prefill arithmetic is heavier |
| 8 | Which tasks can caching help? | `answered` | **Input-heavy ones.** RAG 83:1, code 55:1. SVG is 1:6 output-heavy; caching cannot help generation |
| 9 | Is token price the main cost of a hard task? | `answered` | **No.** 77% of a knowledge deliverable's bill is failure cleanup; moving DeepSeek → Sonnet is only 1.3× |
| 10 | What does an hour of replaced human work cost? | `answered` | **$0.74–$1.45**, before review and integration; 48–95× below a $70 loaded rate |
| 11 | What number should a budget use? | `answered` | **P90.** It is 2.4–2.9× the deterministic point estimate |
| 12 | What should be optimized? | `answered` | **Tokens for reliable work, reliability for judgment work.** Code is driven by token volume ($6.18 swing); knowledge by remediation ($12.27) |
| 13 | Is there a canonical tokens-per-worker index? | `open` | **No.** The fragments are the Anthropic Economic Index, GDPval and Artificial Analysis' cost-per-task. This recipe builds $/human-hour, not tokens/worker |
| 14 | Does the model hold across tasks? | `open` | **Only six profiles, thin on CAD/3D and video.** The task layer is the least measured part |
| 15 | Can the model be calibrated to real spend? | `open` | **No real invoice.** No public dataset joins the same workload to a provider bill |
| 16 | Does cross-task caching change the RAG answer? | `open` | **The model caches within a task, not across tasks.** A shared corpus could make RAG cheaper than modelled |
| 17 | Do real contracts pay list? | `open` | **No.** The model uses list prices; enterprise discounts are invisible and not public |
| 18 | Is the 1M floor a deployable configuration? | `answered` (no) | **No.** The 70B GQA KV is 164 GB per sequence at 1M, beyond one 80 GB H100. The floor is compute-only; deployment needs tensor parallelism and a memory-feasibility check |

## What is still open, and what would close it

**13. A tokens-per-worker index.** There is no canonical construction. The
closest is `occupation → task decomposition (ONET) → tokens/task × $/token ×
attempts / p(success) → $/task → $/FTE-equivalent`. Closing it needs an
occupation-level task decomposition and a real token-per-task measurement, not
another top-down estimate.

**14. Task coverage.** CAD/3D and video are thin. The CAD profile assumes an
OpenSCAD/CadQuery emit; video is mostly not LLM-token driven. Closing it needs
per-task token and success data from a real workflow.

**15. Calibration.** The model has never been reconciled to a bill. Closing it
needs either OpenRouter generations or a provider invoice joined to the same
workload and cache policy. Until then, the point estimates are priors with
arithmetic, and the P90 is the honest planning number.

**16. Cross-task caching.** The model caches the prefix within one task. RAG over
a stable corpus is the case where the cache could be shared across tasks, which
would lower the RAG cost and weaken the "cache is a code lever" split. Closing it
needs a multi-task session model.

**17. Contract pricing.** List prices are the only public number. Enterprise
discounts, committed-use rates and batch agreements would move every margin
statement. They are not observable here, so the recipe states the direction and
does not claim a provider's actual margin.

## What was tried and failed

- **Caching a fixed prefix.** The first simulator cached only the system prompt
  and concluded caching was nearly worthless. It was right about that policy and
  wrong about the realistic one: an agent loop is append-only, so the whole grown
  history is the prefix. Fixing the policy changed the saving from 4% to 82%.
- **Charging the write premium with caching off.** The first version applied the
  1.25× cache-write multiplier to fresh tokens even in the `none` case. That
  inflated the uncached bill from $17.44 to $21.74 and the append saving from 82%
  to 85%. The cold-cache $21.74 is real; the no-cache baseline is not. The
  published figures use the corrected model.
- **Treating the 1M floor as a deployment.** The roofline computes a GPU cost but
  does not check whether the KV cache fits the device. At 1M it does not. The
  chart now says "compute only" and names the 164 GB/sequence constraint.
