"""Shared loading for the OpenRouter recipe. Reads the capture, joins nothing silently."""
import os, csv, json, collections

HERE = os.path.dirname(os.path.abspath(__file__))
RECIPE = os.path.dirname(os.path.dirname(HERE))
CHARTS = os.path.join(RECIPE, "artifacts", "charts")
WORK = os.environ.get("OR_WORK") or os.path.join(os.getcwd(), "work")
RAW = os.path.join(WORK, "openrouter")

# Labs headquartered in China, for the one grouping this recipe makes by hand.
CN = {"deepseek", "tencent", "xiaomi", "z-ai", "minimax", "alibaba", "moonshotai",
      "qwen", "stepfun", "baidu", "01-ai", "inclusionai", "dots-studio"}


def lab(slug):
    return slug.split("/")[0] if "/" in slug else slug


def rankings():
    p = os.path.join(RAW, "rankings-daily.csv")
    if not os.path.exists(p):
        raise SystemExit("no capture — run capture.py first")
    rows = list(csv.DictReader(open(p)))
    for r in rows:
        r["tok"] = int(r["total_tokens"])
    return rows


def prices():
    """Input list price per token, from the benchmarks feed.

    NOT from the models catalog: that is a CURRENT snapshot against 21 months of
    history, so retired models are unpriceable and only 162 of 352 slugs match
    even after stripping the date suffix. The benchmarks feed keys on
    model_permaslug, exactly like the rankings.
    """
    out = {}
    for src in ("artificial-analysis", "openrouter", "design-arena"):
        f = os.path.join(RAW, f"benchmarks-{src}.json")
        if not os.path.exists(f):
            continue
        for m in json.load(open(f))["data"]:
            p = m.get("pricing")
            if isinstance(p, dict) and p.get("prompt"):
                try:
                    out.setdefault(m["model_permaslug"], float(p["prompt"]))
                except (TypeError, ValueError):
                    pass
    return out


def scores(src="artificial-analysis"):
    f = os.path.join(RAW, f"benchmarks-{src}.json")
    out = {}
    for m in json.load(open(f))["data"]:
        d = {}
        for k in ("intelligence_index", "coding_index", "agentic_index"):
            try:
                d[k] = float(m[k])
            except (TypeError, ValueError, KeyError):
                pass
        if d:
            out[m["model_permaslug"]] = d
    return out


def window(rows, start):
    return [r for r in rows if r["date"] >= start]


def by_lab(rows):
    c = collections.Counter()
    for r in rows:
        c[lab(r["model_permaslug"])] += r["tok"]
    return c
