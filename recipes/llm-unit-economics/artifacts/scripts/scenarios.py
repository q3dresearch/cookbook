"""The scenarios every figure in this recipe is drawn from.

One place for the assumptions, so a chart script never re-invents a workload or
quietly changes a parameter. `llm_econ.py` is the model; this file is the set of
questions put to it.

Everything here is deterministic except `monte_carlo`, which seeds random on
every call and is therefore reproducible run to run.
"""
from __future__ import annotations

import math
import random
import statistics

from llm_econ import (
    ARCH, CACHE_PRIORS, INST, LOADED_HOURLY, PRICING, TASKS, Pricing, Task,
    Workload, cost_per_task, server_cost, user_cost, wl_tokens,
)

MODELS = list(PRICING)
TIER_MODELS = ["ds-v4-flash", "gemini-3.1", "sonnet-4.6"]

# A 30-turn coding agent with no compaction, and the same loop capped at 200K.
LOOP_NOCAP = Workload("agent loop (no cap)", 30, 10_000, 12_000, 500, 8_000)
LOOP_CAP = Workload("agent loop @200K cap", 30, 10_000, 12_000, 500, 8_000, 200_000)


# ── user-side scenarios ─────────────────────────────────────────────────────

def caching_rows():
    """(model, policy, no cache, fixed prefix, append history) per model."""
    rows = []
    for key in MODELS:
        price = PRICING[key]
        rows.append([
            key,
            price.name,
            round(user_cost(price, LOOP_NOCAP, "none"), 4),
            round(user_cost(price, LOOP_NOCAP, "fixed"), 4),
            round(user_cost(price, LOOP_NOCAP, "append"), 4),
        ])
    return rows


def ttl_rows(gaps=(10, 20, 30, 60, 120, 180, 240, 300, 360, 420, 600, 900)):
    """Session cost against idle time between turns, append caching, 300s TTL."""
    rows = []
    for gap in gaps:
        row = [gap]
        for key in MODELS:
            w = Workload("l", 30, 10_000, 12_000, 500, 8_000,
                         turn_gap_s=gap, cache_ttl_s=300)
            row.append(round(user_cost(PRICING[key], w, "append"), 4))
        rows.append(row)
    return list(gaps), rows


def hit_rows(rates=None):
    """Session cost against the fraction of the cacheable prefix that hits."""
    if rates is None:
        rates = [i / 20 for i in range(0, 21)]
    rows = []
    for hit in rates:
        row = [hit]
        for key in MODELS:
            w = Workload("l", 30, 10_000, 12_000, 500, 8_000, cache_hit_rate=hit)
            row.append(round(user_cost(PRICING[key], w, "append"), 4))
        rows.append(row)
    return list(rates), rows


def window_rows(caps=(100_000, 150_000, 200_000, 300_000, 400_000, 600_000, 1_000_000)):
    """Does the compaction cap matter once the history is cached?"""
    rows = []
    for cap in caps:
        row = [cap]
        for key in MODELS:
            w = Workload("l", 30, 10_000, 12_000, 500, 8_000, compaction_at=cap)
            row.append(round(user_cost(PRICING[key], w, "append"), 4))
        rows.append(row)
    return list(caps), rows


def context_cliff_rows(prompts=(10_000, 25_000, 50_000, 100_000, 150_000,
                                200_000, 250_000, 500_000, 1_000_000),
                       output=5_000, models=("sonnet-4.6", "gemini-3.1", "ds-v4-flash")):
    """One request: prompt size against the bill, for flat and tiered pricing."""
    rows = {key: [] for key in models}
    for ctx in prompts:
        for key in models:
            price = PRICING[key]
            mult_in = mult_out = 1.0
            if price.tier_threshold and ctx > price.tier_threshold:
                mult_in, mult_out = price.tier_mult_in, price.tier_mult_out
            cost = (ctx * price.in_rate * mult_in
                    + output * price.out_rate * mult_out) / 1e6
            rows[key].append((ctx, cost))
    return list(prompts), rows


# ── server-side scenarios ───────────────────────────────────────────────────

def server_rows(model="sonnet-4.6",
                configs=(("gqa-70b", "h100"), ("gqa-70b-h", "h100"), ("mla-600b", "h100x8")),
                contexts=(10_000, 50_000, 200_000, 500_000, 1_000_000),
                out_tokens=1_000, batch=64):
    """GPU floor and flat list price for one request at each context length."""
    price = PRICING[model]
    rows = []
    for arch_key, inst_key in configs:
        arch, inst = ARCH[arch_key], INST[inst_key]
        for ctx in contexts:
            result = server_cost(arch, inst, ctx, out_tokens, ctx, batch)
            user = (ctx * price.in_rate + out_tokens * price.out_rate) / 1e6
            rows.append({
                "arch": arch_key,
                "arch_name": arch.name,
                "instance": inst.name,
                "context": ctx,
                "kv_gb_seq": result["kv_gb_seq"],
                "prefill_share": result["prefill_share"],
                "server_usd": result["usd"],
                "user_usd": user,
                "margin": user - result["usd"],
            })
    return rows


# ── task layer ──────────────────────────────────────────────────────────────

def workload_rows():
    rows = []
    for task in TASKS.values():
        ins, outs = wl_tokens(task.w)
        rows.append({
            "key": task.name,
            "task": task.name,
            "category": task.category,
            "turns": task.w.turns,
            "tokens_in": ins,
            "tokens_out": outs,
            "ratio": ins / outs if outs else float("inf"),
            "human_hours": task.human_hours,
            "value_usd": task.value_usd,
            "p_success": task.p_success,
            "source": task.source,
        })
    return rows


def cost_per_task_rows(models=TIER_MODELS):
    rows = []
    for task in TASKS.values():
        row = {"task": task.name}
        for key in models:
            detail = cost_per_task(PRICING[key], task)
            row[key] = round(detail["usd_solved"], 4)
            row[f"{key}_attempt"] = round(detail["usd_attempt"], 4)
            row[f"{key}_per_hour"] = round(detail["usd_per_hour"], 3)
        row["human_cost"] = task.human_hours * LOADED_HOURLY
        row["value_usd"] = task.value_usd
        rows.append(row)
    return rows


def replacement_rows(model="sonnet-4.6"):
    """AI $ per human-hour equivalent, against the loaded human rate."""
    rows = []
    for task in TASKS.values():
        detail = cost_per_task(PRICING[model], task)
        rows.append({
            "task": task.name,
            "human_hours": task.human_hours,
            "human_cost": task.human_hours * LOADED_HOURLY,
            "ai_usd_solved": detail["usd_solved"],
            "ai_usd_per_hour": detail["usd_per_hour"],
            "human_x": (task.human_hours * LOADED_HOURLY) / detail["usd_solved"]
            if detail["usd_solved"] else 0.0,
        })
    return rows


def failure_rows(model="sonnet-4.6"):
    """Expected cost per solved task, split into attempt and failure cleanup."""
    rows = []
    for task in TASKS.values():
        detail = cost_per_task(PRICING[model], task)
        solved = detail["usd_solved"]
        attempt = detail["usd_attempt"] / max(task.p_success, 1e-9)
        failure = solved - attempt
        rows.append({
            "task": task.name,
            "p_success": task.p_success,
            "attempt_usd": attempt,
            "failure_usd": failure,
            "solved_usd": solved,
            "failure_share": failure / solved if solved else 0.0,
        })
    return rows


# ── uncertainty ─────────────────────────────────────────────────────────────

def _beta(mean, concentration=25.0):
    mean = min(max(mean, 1e-3), 1 - 1e-3)
    return random.betavariate(mean * concentration, (1 - mean) * concentration)


def _q(sorted_values, quantile):
    return sorted_values[min(len(sorted_values) - 1,
                             max(0, int(quantile * len(sorted_values))))]


def _scaled(workload, mult_in, mult_out, hit):
    return Workload(
        workload.name, workload.turns,
        max(int(workload.base_context * mult_in), 1),
        max(int(workload.growth_per_turn * mult_in), 0),
        max(int(workload.output_per_turn * mult_out), 1),
        workload.cacheable_prefix, workload.compaction_at,
        workload.turn_gap_s, workload.cache_ttl_s, hit,
    )


def monte_carlo(price, task, n=2000, seed=7):
    """Sample p_success, cache hit, run-to-run token variance and remediation."""
    random.seed(seed)
    values = []
    for _ in range(n):
        p_success = _beta(task.p_success, 25)
        hit = _beta(task.w.cache_hit_rate, 40) if task.w.cache_hit_rate > 0 else 0.0
        run = random.lognormvariate(0, 0.85)
        out_mult = run * random.lognormvariate(0, 0.5)
        workload = _scaled(task.w, run, out_mult, hit)
        remediation = task.remediation_usd * random.lognormvariate(0, 0.7)
        values.append(user_cost(price, workload, "append") / max(p_success, 1e-6)
                      + (1 - p_success) * remediation)
    values.sort()
    return {
        "p10": _q(values, .10), "p50": _q(values, .50), "p90": _q(values, .90),
        "mean": statistics.mean(values), "vals": values,
    }


def mc_rows(model="sonnet-4.6", n=2000):
    rows = []
    for task in TASKS.values():
        result = monte_carlo(PRICING[model], task, n)
        row = {"task": task.name}
        row.update({k: round(v, 4) for k, v in result.items() if k != "vals"})
        row["point"] = round(cost_per_task(PRICING[model], task)["usd_solved"], 4)
        rows.append(row)
    return rows


def tornado_rows(model="sonnet-4.6", n=4000):
    """Swing each driver from its P10 to P90, one at a time."""
    price = PRICING[model]
    rows = []
    for task in TASKS.values():
        def cost(p_success, hit, run, remediation):
            workload = _scaled(task.w, run, run, hit)
            return (user_cost(price, workload, "append") / max(p_success, 1e-6)
                    + (1 - p_success) * remediation)

        base_p, base_hit = task.p_success, task.w.cache_hit_rate
        random.seed(11)
        p_samples = sorted(_beta(base_p, 25) for _ in range(n))
        hit_samples = (sorted(_beta(base_hit, 40) for _ in range(n))
                       if base_hit > 0 else [0.0, 0.0])
        drivers = [
            ("p(success)", _q(p_samples, .10), _q(p_samples, .90),
             lambda v: cost(v, base_hit, 1.0, task.remediation_usd)),
            ("cache hit", _q(hit_samples, .10), _q(hit_samples, .90),
             lambda v: cost(base_p, v, 1.0, task.remediation_usd)),
            ("token volume", math.exp(-1.2816 * .85), math.exp(1.2816 * .85),
             lambda v: cost(base_p, base_hit, v, task.remediation_usd)),
            ("remediation $", task.remediation_usd * math.exp(-1.2816 * .7),
             task.remediation_usd * math.exp(1.2816 * .7),
             lambda v: cost(base_p, base_hit, 1.0, v)),
        ]
        base = cost(base_p, base_hit, 1.0, task.remediation_usd)
        for name, low, high, fn in drivers:
            cost_low, cost_high = fn(low), fn(high)
            rows.append({
                "task": task.name,
                "driver": name,
                "driver_low": round(low, 3),
                "driver_high": round(high, 3),
                "cost_low": round(cost_low, 4),
                "cost_high": round(cost_high, 4),
                "base": round(base, 4),
                "swing": round(abs(cost_high - cost_low), 4),
            })
    return rows


# ── headline figures ────────────────────────────────────────────────────────

def headline():
    cache = {row[0]: {"none": row[2], "fixed": row[3], "append": row[4]}
             for row in caching_rows()}
    sonnet = cache["sonnet-4.6"]
    _, cliff = context_cliff_rows()
    server = {row["arch"]: row for row in server_rows()
              if row["context"] == 1_000_000}
    failure = {row["task"]: row for row in failure_rows()}
    replacement = {row["task"]: row for row in replacement_rows()}
    tornado = tornado_rows()
    knowledge_drivers = {row["driver"]: row["swing"] for row in tornado
                         if row["task"] == "knowledge deliverable"}
    code_drivers = {row["driver"]: row["swing"] for row in tornado
                    if row["task"] == "agentic code task"}

    # Cache fragility: the cold-cache bill, the 70% mark, and where append
    # caching stops beating no caching.
    gaps, ttl = ttl_rows()
    cold = next(row[1] for gap, row in zip(gaps, ttl) if gap == 360)
    warm = sonnet["append"]
    hit_rates, hits = hit_rows([i / 1000 for i in range(1001)])
    at_70 = next(row[1] for rate, row in zip(hit_rates, hits) if rate == 0.7)
    break_even = next(rate for rate, row in zip(hit_rates, hits)
                      if row[1] <= sonnet["none"])

    mc = mc_rows()
    return {
        "session_cost_none": sonnet["none"],
        "session_cost_fixed": sonnet["fixed"],
        "session_cost_append": sonnet["append"],
        "append_saving_pct": round(100 * (1 - sonnet["append"] / sonnet["none"]), 1),
        "fixed_saving_pct": round(100 * (1 - sonnet["fixed"] / sonnet["none"]), 1),
        "context_200k_flat": round(dict(cliff["sonnet-4.6"])[200_000], 4),
        "context_1m_flat": round(dict(cliff["sonnet-4.6"])[1_000_000], 4),
        "context_ratio_flat": round(dict(cliff["sonnet-4.6"])[1_000_000]
                                    / dict(cliff["sonnet-4.6"])[200_000], 1),
        "context_200k_tiered": round(dict(cliff["gemini-3.1"])[200_000], 4),
        "context_1m_tiered": round(dict(cliff["gemini-3.1"])[1_000_000], 4),
        "context_ratio_tiered": round(dict(cliff["gemini-3.1"])[1_000_000]
                                     / dict(cliff["gemini-3.1"])[200_000], 1),
        "server_floor_1m_gqa": round(server["gqa-70b"]["server_usd"], 3),
        "server_floor_1m_hybrid": round(server["gqa-70b-h"]["server_usd"], 3),
        "server_floor_1m_mla": round(server["mla-600b"]["server_usd"], 3),
        "list_price_1m": round(server["gqa-70b"]["user_usd"], 3),
        "knowledge_failure_share": round(failure["knowledge deliverable"]["failure_share"], 3),
        "knowledge_cost_solved": round(failure["knowledge deliverable"]["solved_usd"], 2),
        "knowledge_cost_per_hour": round(replacement["knowledge deliverable"]["ai_usd_per_hour"], 2),
        "replacement_range_low": round(min(r["ai_usd_per_hour"] for r in replacement.values()), 2),
        "replacement_range_high": round(max(r["ai_usd_per_hour"] for r in replacement.values()), 2),
        "tornado_code_token_swing": round(code_drivers["token volume"], 2),
        "tornado_code_p_success_swing": round(code_drivers["p(success)"], 2),
        "tornado_knowledge_remediation_swing": round(knowledge_drivers["remediation $"], 2),
        "tornado_knowledge_token_swing": round(knowledge_drivers["token volume"], 2),
        "cache_prior_min": min(CACHE_PRIORS.values()),
        "cache_prior_max": max(CACHE_PRIORS.values()),
        "cache_cold_cost": round(cold, 4),
        "cache_ttl_multiple": round(cold / warm, 1),
        "cache_hit70_cost": round(at_70, 4),
        "cache_hit70_multiple": round(at_70 / warm, 1),
        "cache_break_even_hit": round(break_even, 3),
        "server_floor_1m_gqa_shortfall": round(
            server["gqa-70b"]["server_usd"] - server["gqa-70b"]["user_usd"], 3),
        "server_hybrid_multiple": round(
            server["gqa-70b"]["server_usd"] / server["gqa-70b-h"]["server_usd"], 1),
        "knowledge_vs_deepseek_multiple": round(
            cost_per_task(PRICING["sonnet-4.6"], TASKS["knowledge"])["usd_solved"]
            / cost_per_task(PRICING["ds-v4-flash"], TASKS["knowledge"])["usd_solved"],
            2),
        "mc_p90_multiple_low": round(min(r["p90"] / r["point"] for r in mc), 1),
        "mc_p90_multiple_high": round(max(r["p90"] / r["point"] for r in mc), 1),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(headline(), indent=2))
