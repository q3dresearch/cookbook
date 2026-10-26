#!/usr/bin/env python3
"""
LLM unit-economics & cost forecast.

Two sides of the same request:
  * USER  cost  = what the API bill charges (input/output/cached, tier cliffs, batch).
  * SERVER cost = what it costs the operator in GPU-seconds (roofline: prefill is
                  compute-bound, decode is KV-read / memory-bandwidth bound).

margin = user_price - server_cost.  Where the two diverge is where the
optimization opportunities live.

No external deps.  Run:  python3 llm_econ.py
"""
from dataclasses import dataclass

# ----------------------------------------------------------------------------
# Pricing registry  ($ per 1M tokens, USD, list prices, early 2026)
# tier_threshold: if in_tokens > threshold, the WHOLE request re-prices by the mults.
# ----------------------------------------------------------------------------
@dataclass
class Pricing:
    name: str
    in_rate: float
    out_rate: float
    cached_in: float = 0.0          # $/M cached input read
    cache_write_mult: float = 1.25  # cache write costs this x base input
    tier_threshold: int = 0         # 0 = flat pricing, no cliff
    tier_mult_in: float = 1.0
    tier_mult_out: float = 1.0
    batch_discount: float = 0.0
    cache_storage_m_hr: float = 0.0  # $ per 1M cached tokens per hour held (Gemini: 4.50)

PRICING = {
    # flat-priced across a 1M window -> "biggest window is free" is true here
    "sonnet-4.6":  Pricing("Claude Sonnet 4.6", 3.0, 15.0, cached_in=0.30),
    "gpt-5.5":     Pricing("GPT-5.5", 5.0, 30.0, cached_in=0.50, batch_discount=0.5),
    # tiered -> a 200K cliff re-prices the whole request at 2x / 1.5x
    "gemini-3.1":  Pricing("Gemini 3.1 Pro", 2.0, 12.0, cached_in=0.20,
                           tier_threshold=200_000, tier_mult_in=2.0, tier_mult_out=1.5,
                           cache_storage_m_hr=4.50),
    "sonnet-4.5":  Pricing("Claude Sonnet 4.5", 3.0, 15.0, cached_in=0.30,
                           tier_threshold=200_000, tier_mult_in=2.0, tier_mult_out=1.5),
    # cheap-per-token long-context model (what the market actually routes to)
    "ds-v4-flash": Pricing("DeepSeek V4 Flash", 0.09, 0.50, cached_in=0.02),
}

# ----------------------------------------------------------------------------
# Server side.  KV bytes/token = kv_per_layer_token * n_layers * kv_bytes.
# (paper: n_kv_head * d_head * n_layers * l_input * b * p, with K and V counted)
# ----------------------------------------------------------------------------
@dataclass
class Arch:
    name: str
    resident_params_b: float   # weights that must sit in memory
    active_params_b: float     # params touched per token (MoE active)
    n_layers: int
    n_heads: int
    attn_dim: int              # head_dim used in prefill attention arithmetic
    kv_per_layer_token: int    # cached scalars per layer per token, K+V
    decode_attn_dim: int = 0   # effective head dim during DECODE (MLA: d_latent)
    weight_bytes: float = 1.0  # fp8 weights
    kv_bytes: float = 1.0      # fp8 KV cache
    full_attn_frac: float = 1.0  # fraction of layers doing full O(L^2) attention
                                 # (hybrid/sliding-window models < 1.0)

ARCH = {
    # GQA, group size 8 -> fat KV cache (~160 KB/token fp8), vanilla attention
    "gqa-70b":   Arch("70B GQA (grp 8)", 70, 70, 80, 64, 128, 2 * 8 * 128,
                      decode_attn_dim=128),
    # same model, hybrid attention (1 in 4 layers full) -> 4x cheaper prefill
    "gqa-70b-h": Arch("70B GQA hybrid", 70, 70, 80, 64, 128, 2 * 8 * 128,
                      decode_attn_dim=128, full_attn_frac=0.25),
    # MLA (DeepSeek-V3 style): tiny KV cache (~35 KB/token fp8); decode arithmetic
    # uses the 512-dim latent, so it is ~4x heavier per token than vanilla GQA.
    "mla-600b":  Arch("671B MLA (act. 40B)", 671, 40, 61, 128, 128, 512 + 64,
                      decode_attn_dim=512),
}

@dataclass
class Instance:
    name: str
    flops: float       # total dense FLOP/s
    bw: float          # total HBM bytes/s
    vram_gb: float     # total memory for weights + KV
    usd_hr: float
    mfu: float = 0.50
    mbu: float = 0.75

INST = {
    "h100":   Instance("1x H100", 990e12, 3.35e12, 80, 2.50),
    "h100x8": Instance("8x H100", 8 * 990e12, 8 * 3.35e12, 640, 20.0),
}

def kv_per_token(a: Arch) -> float:
    return a.kv_per_layer_token * a.n_layers * a.kv_bytes

def server_cost(a: Arch, inst: Instance, in_tokens: int, out_tokens: int,
                avg_context: int, batch: int) -> dict:
    # prefill: compute-bound (weight MACs + quadratic attention, scaled by full_attn_frac)
    attn = 4 * a.n_layers * a.n_heads * a.attn_dim * in_tokens ** 2 * a.full_attn_frac
    prefill_s = (2 * a.active_params_b * 1e9 * in_tokens + attn) / (inst.flops * inst.mfu)
    # decode: max(memory-bandwidth-bound KV read, arithmetic), per step, whole batch
    weight_bytes = a.resident_params_b * 1e9 * a.weight_bytes
    kv = kv_per_token(a) * avg_context
    mem_step = (weight_bytes + batch * kv) / (inst.bw * inst.mbu)
    arith_step = (2 * a.active_params_b * 1e9
                  + 4 * a.n_layers * a.n_heads * (a.decode_attn_dim or a.attn_dim) * avg_context
                  ) * batch / (inst.flops * inst.mfu)
    step_s = max(mem_step, arith_step)
    decode_s = out_tokens * step_s / batch
    gpu_s = prefill_s + decode_s
    return {"gpu_s": gpu_s, "usd": gpu_s * inst.usd_hr / 3600,
            "prefill_s": prefill_s, "decode_s": decode_s,
            "prefill_share": prefill_s / gpu_s if gpu_s else 0,
            "decode_mem_bound": mem_step >= arith_step,
            "kv_gb_seq": kv / 1e9,
            "max_batch": max((inst.vram_gb * 1e9 - weight_bytes) / max(kv, 1), 0)}

# ----------------------------------------------------------------------------
# Workloads
# ----------------------------------------------------------------------------
@dataclass
class Workload:
    name: str
    turns: int
    base_context: int
    growth_per_turn: int
    output_per_turn: int
    cacheable_prefix: int = 0    # used only by cache="fixed"
    compaction_at: int = 0
    turn_gap_s: int = 60         # wall-clock seconds between turns (tool calls, human)
    cache_ttl_s: int = 300       # 5-min Anthropic-style TTL
    cache_hit_rate: float = 1.0  # fraction of the cacheable prefix that is a hit
                                 # (models partial invalidation / dynamic content)

    def turn_contexts(self):
        ctx, out = self.base_context, []
        for _ in range(self.turns):
            out.append((ctx, self.output_per_turn))
            ctx += self.growth_per_turn + self.output_per_turn
            if self.compaction_at and ctx > self.compaction_at:
                ctx = self.base_context
        return out


# ----------------------------------------------------------------------------
# Task layer: workload + economics.  cache_hit_rate priors come from production
# telemetry (Requesty coding-agent hit rates; GitHub Copilot session study),
# NOT from the ideal 100%.
# ----------------------------------------------------------------------------
@dataclass
class Task:
    name: str
    category: str
    w: Workload
    p_success: float = 1.0        # chance one attempt solves it
    remediation_usd: float = 0.0  # cleanup cost on a failed attempt
    human_hours: float = 0.0      # expert time to do it by hand
    value_usd: float = 0.0        # economic value of the deliverable
    source: str = ""

def wl_tokens(w: Workload):
    tc = w.turn_contexts()
    return sum(c for c, _ in tc), sum(o for _, o in tc)

def cost_per_task(p: Pricing, t: Task, cache: str = "append") -> dict:
    c_attempt = user_cost(p, t.w, cache)
    e_cost = c_attempt / max(t.p_success, 1e-9) + (1 - t.p_success) * t.remediation_usd
    ins, outs = wl_tokens(t.w)
    return {"usd_attempt": c_attempt, "usd_solved": e_cost,
            "in_tokens": ins, "out_tokens": outs,
            "usd_per_hour": e_cost / t.human_hours if t.human_hours else 0.0,
            "roi": t.value_usd / e_cost if e_cost else 0.0}

# cache_hit_rate: session-level priors from telemetry (0.85 ~ Claude Code/OpenCode;
# 0.0 = no stable prefix).  Sources noted per task.
TASKS = {
    "chat": Task("chat / QA", "chat",
                 Workload("chat", 6, 1_000, 400, 400, cache_hit_rate=0.0),
                 p_success=0.90, remediation_usd=0.1, human_hours=0.10, value_usd=5,
                 source="practitioner; ~4-5x out:in"),
    "code": Task("agentic code task", "code",
                 Workload("code", 50, 8_000, 300, 500, cache_hit_rate=0.85),
                 p_success=0.70, remediation_usd=2.0, human_hours=4.0, value_usd=400,
                 source="Vantage 1M-in/40K-out; SR ~90% session, 55% turn-boundary"),
    "knowledge": Task("knowledge deliverable", "knowledge",
                 Workload("knowledge", 12, 15_000, 2_000, 1_500, cache_hit_rate=0.60),
                 p_success=0.60, remediation_usd=15.0, human_hours=7.5, value_usd=400,
                 source="OpenAI GDPval: ~$400/task, 7-9 expert hrs"),
    "svg": Task("SVG / vector art", "creative",
                 Workload("svg", 1, 1_000, 0, 6_000, cache_hit_rate=0.0),
                 p_success=0.50, remediation_usd=1.0, human_hours=0.5, value_usd=60,
                 source="Playcode MacBook SVG: output 2-9x model variance"),
    "cad": Task("CAD / 3D script", "engineering",
                 Workload("cad", 3, 3_000, 1_000, 2_000, cache_hit_rate=0.20),
                 p_success=0.40, remediation_usd=3.0, human_hours=1.5, value_usd=150,
                 source="thin public data; assumes OpenSCAD/CadQuery emit"),
    "rag": Task("RAG / doc summarization", "knowledge",
                 Workload("rag", 1, 100_000, 0, 1_200, cache_hit_rate=0.95),
                 p_success=0.95, remediation_usd=5.0, human_hours=0.5, value_usd=40,
                 source="stable corpus; caching helps ACROSS tasks, not within"),
}

# Loaded hourly cost of the human being replaced.
LOADED_HOURLY = 70.0

# Agent cache-hit priors, Apr 2026 (Requesty) + Copilot study
CACHE_PRIORS = {
    "Claude Code": 0.919, "OpenCode": 0.890, "Aider": 0.840, "Zed": 0.801,
    "Roo Code": 0.736, "Forge": 0.639, "Cline": 0.614, "Kilo Code": 0.455,
    "Copilot (turn boundary)": 0.550, "Copilot (model switch)": 0.080,
}


def user_cost(p: Pricing, w: Workload, cache: str = "none") -> float:
    """cache: 'none' | 'fixed' (stable prefix only) | 'append' (full grown history).
    Models cache TTL expiry and provider cache-storage fees."""
    total = 0.0
    prev_cached = 0        # tokens resident in the cache from last turn
    last_write_t = -1e18
    t = 0
    for ctx, out in w.turn_contexts():
        mi = mo = 1.0
        if p.tier_threshold and ctx > p.tier_threshold:
            mi, mo = p.tier_mult_in, p.tier_mult_out
        if cache == "none":
            cached, writes, fresh = 0, 0, ctx
        else:
            warm = (t - last_write_t) <= w.cache_ttl_s
            prev = prev_cached if warm else 0
            if cache == "fixed":
                cacheable = min(ctx, w.cacheable_prefix)
                cached = w.cache_hit_rate * min(prev, cacheable)
                # A fixed prefix is written once, then only re-read. Charging
                # the write premium to the whole request (as an earlier version
                # did) made fixed-prefix caching look 4% cheaper than no cache.
                writes = max(0, cacheable - prev)
                fresh = ctx - cached - writes
            else:                                             # append: whole grown history
                cached = w.cache_hit_rate * min(prev, ctx)
                writes = ctx - cached
                fresh = 0
        total += (cached * (p.cached_in or p.in_rate) * mi
                  + writes * p.in_rate * p.cache_write_mult * mi
                  + fresh * p.in_rate * mi
                  + out * p.out_rate * mo) / 1e6
        # accrue storage fee on whatever is held in cache during this turn
        if p.cache_storage_m_hr and cache != "none":
            total += ctx * p.cache_storage_m_hr * (w.turn_gap_s / 3600) / 1e6
        prev_cached = (ctx if cache == "append"
                       else min(ctx, w.cacheable_prefix))
        last_write_t = t
        t += w.turn_gap_s
    return total

# ----------------------------------------------------------------------------
def report():
    W = 104
    print("=" * W)
    print("PART 1  USER BILL ($ / session) — does the window choice change the cost?")
    print("=" * W)
    loads = [
        Workload("short chat",             10,   4_000,    500,   400, 2_000),
        Workload("RAG doc QA",              3,  50_000,  2_000,   800, 20_000),
        Workload("codebase review",        20, 120_000,  3_000,   500, 100_000),
        Workload("agent loop (no cap)",    30,  10_000, 12_000,   500, 8_000),
        Workload("agent loop @200K cap",   30,  10_000, 12_000,   500, 8_000, 200_000),
        Workload("1M deep analysis",        1, 800_000,      0, 5_000, 0),
    ]
    print(f"{'workload (uncached)':26} {'peak ctx':>9} " + "".join(f"{m:>15}" for m in PRICING))
    for w in loads:
        peak = max(c for c, _ in w.turn_contexts())
        print(f"{w.name:26} {peak:>9,} " + "".join(
            f"{user_cost(p, w):>14.2f} " for p in PRICING.values()))

    print("\n" + "=" * W)
    print("PART 1b  THE CACHING QUESTION — agent loop, 30 turns, grows 10K -> 372K")
    print("=" * W)
    lo_nocap = Workload("loop", 30, 10_000, 12_000, 500, 8_000)
    lo_cap   = Workload("loop", 30, 10_000, 12_000, 500, 8_000, 200_000)
    print(f"{'model':20} {'policy':22} {'none':>9} {'fixed 8K':>9} {'append full':>12}")
    for k in ["sonnet-4.6", "gemini-3.1", "ds-v4-flash"]:
        p = PRICING[k]
        for lab, w in [("no cap", lo_nocap), ("200K cap", lo_cap)]:
            a = user_cost(p, w, "none")
            b = user_cost(p, w, "fixed")
            c = user_cost(p, w, "append")
            print(f"{p.name:20} {lab:22} {a:>9.2f} {b:>9.2f} {c:>12.2f}")
    print("\n  append = cache the WHOLE grown history (append-only). This is the realistic")
    print("  agent case: the prefix from turn t-1 is a cheap cache read at turn t.")

    print("\n  [a] cost per turn is no longer flat when the window grows — append caching:")
    for lab, w in [("500K window", Workload("l",30,10_000,12_000,500,8_000,500_000)),
                   ("200K cap   ", lo_cap)]:
        p = PRICING["sonnet-4.6"]
        print(f"      {lab}  appended-cached session = ${user_cost(p,w,'append'):.2f}")

    print("\n  [b] cache TTL is the silent killer (Sonnet, agent loop, append caching):")
    p = PRICING["sonnet-4.6"]
    for gap, ttl, note in [(60,300,"fast loop, 5-min TTL -> cache stays warm"),
                           (600,300,"10 min between turns -> cache EXPIRES each turn")]:
        w = Workload("l", 30, 10_000, 12_000, 500, 8_000, turn_gap_s=gap, cache_ttl_s=ttl)
        print(f"      gap={gap:>3}s  {note:52} ${user_cost(p,w,'append'):.2f}")

    print("\n  [c] Gemini charges cache STORAGE ($4.50 / 1M / hour); TTL vs storage:")
    pg = PRICING["gemini-3.1"]
    for gap in [20, 60, 120]:
        w = Workload("l", 30, 10_000, 12_000, 500, 8_000, turn_gap_s=gap)
        read_only = user_cost(Pricing("x", pg.in_rate, pg.out_rate, cached_in=pg.cached_in), w, "append")
        with_storage = user_cost(pg, w, "append")
        print(f"      turn gap {gap:>3}s: reads only ${read_only:6.2f}  + storage ${with_storage:6.2f}"
              f"  (storage = ${with_storage-read_only:.2f})")

    print("\n" + "=" * W)
    print("PART 2  SERVER UNIT ECONOMICS — one request: context C, 1,000 output tokens")
    print("=" * W)
    p = PRICING["sonnet-4.6"]
    print(f"{'arch':>11} {'instance':>9} {'context':>9} {'batch':>6} {'KV GB/seq':>10} "
          f"{'prefill%':>9} {'server $/req':>13} {'user $/req':>11} {'margin':>9}")
    for ak, instk in [("gqa-70b", "h100"), ("gqa-70b-h", "h100"), ("mla-600b", "h100x8")]:
        a, inst = ARCH[ak], INST[instk]
        for ctx in [10_000, 200_000, 1_000_000]:
            for batch in [16, 64]:
                r = server_cost(a, inst, ctx, 1_000, ctx, batch)
                user = (ctx * p.in_rate + 1_000 * p.out_rate) / 1e6
                print(f"{ak:>11} {inst.name:>9} {ctx:>9,} {batch:>6} {r['kv_gb_seq']:>10.2f} "
                      f"{r['prefill_share']*100:>8.0f}% {r['usd']:>13.4f} {user:>11.4f} "
                      f"{user - r['usd']:>8.4f}")
    print("\n  server $/req = GPU rental only (no overhead/margin). It is the FLOOR.")
    print("  prefill% = share of GPU time spent on the prompt (attention-dominated at length).")
    print("  A prompt-cache HIT removes the prefill term, but NOT the KV reads during decode.")

if __name__ == "__main__":
    report()
