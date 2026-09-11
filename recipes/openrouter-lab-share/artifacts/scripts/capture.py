"""Capture OpenRouter's daily model rankings. Fetch once; the publisher keeps history.

    OPENROUTER_API_KEY=... python capture.py [work_dir]

OpenRouter is a ROUTER. A developer calls one API and it forwards to whichever
lab's model they asked for. It therefore sees the traffic of everyone who routes
through it and nobody who calls a lab directly — which is the caveat that governs
every number this recipe produces.

`rankings-daily` returns the top 50 models per day plus one aggregated `other`
row, back to 2025-01-01, in windows of at most 366 days. Fields are exactly
three: date, model_permaslug, total_tokens. There is no request count and no
price here, so "share" in this recipe always means share of TOKENS SERVED.

Also captured: the models catalog, which carries pricing and context length, so
the token-versus-requests and price questions have something to join to.

CC BY 4.0. Citation required wherever a figure from this is published:
  Source: OpenRouter (openrouter.ai/rankings), as of {meta.as_of}.
"""
import csv, hashlib, json, os, subprocess, sys, time
from datetime import date, timedelta

WORK = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.getcwd(), "work")
DEST = os.path.join(WORK, "openrouter")
START = date(2025, 1, 1)
TODAY = date.today()
WINDOW = 360                      # the API caps at 366; leave room
UA = "q3dresearch-cookbook/1.0 (+https://github.com/q3dresearch/cookbook; research use)"
KEY = os.environ.get("OPENROUTER_API_KEY", "")


def get(url, auth=True):
    cmd = ["curl", "-sS", "--compressed", "--max-time", "180", "-A", UA]
    if auth:
        cmd += ["-H", f"Authorization: Bearer {KEY}"]
    p = subprocess.run(cmd + [url], capture_output=True)
    if p.returncode != 0 or not p.stdout:
        raise RuntimeError(f"curl rc={p.returncode}: {p.stderr.decode()[:200]}")
    return p.stdout


def check(name, body):
    """An error page is not a capture. The first run of this stored a 113-byte
    JSON error under session-cost-cline.json and it looked like a small file
    rather than a failure — `cline` is not a valid app_slug, only four are."""
    try:
        d = json.loads(body)
    except Exception:
        return body
    if isinstance(d, dict) and "error" in d:
        raise RuntimeError(f"{name}: API returned an error, not data: "
                           f"{str(d['error'])[:160]}")
    if isinstance(d, dict) and not (d.get("data") or d.get("classifications")):
        raise RuntimeError(f"{name}: response carries no data key")
    return body


def save(name, body, note):
    check(name, body)
    os.makedirs(DEST, exist_ok=True)
    path = os.path.join(DEST, name)
    open(path, "wb").write(body)
    man = os.path.join(DEST, "manifest.csv")
    new = not os.path.exists(man)
    with open(man, "a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["file", "bytes", "sha256", "fetched_at", "note"])
        w.writerow([name, len(body), hashlib.sha256(body).hexdigest()[:16],
                    time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), note])
    print(f"  {name}: {len(body):,} bytes", file=sys.stderr)
    return path


def main():
    if not KEY:
        print("OPENROUTER_API_KEY is not set", file=sys.stderr)
        return 2
    rows, as_of = [], None
    lo = START
    while lo <= TODAY:
        hi = min(lo + timedelta(days=WINDOW - 1), TODAY)
        url = ("https://openrouter.ai/api/v1/datasets/rankings-daily"
               f"?start_date={lo}&end_date={hi}")
        body = get(url)
        d = json.loads(body)
        save(f"rankings-{lo}_{hi}.json", body, f"{lo} to {hi}")
        chunk = d.get("data") or []
        as_of = (d.get("meta") or {}).get("as_of") or as_of
        # Top 50 per day plus one `other` row: 51 is the expected width, and a
        # day short of that is the API truncating, not a quiet market.
        per_day = {}
        for r in chunk:
            per_day[r["date"]] = per_day.get(r["date"], 0) + 1
        thin = sorted(k for k, v in per_day.items() if v < 51)
        if thin:
            print(f"  note: {len(thin)} day(s) returned fewer than 51 rows, "
                  f"first {thin[0]}", file=sys.stderr)
        rows += chunk
        lo = hi + timedelta(days=1)

    save("models-catalog.json", get("https://openrouter.ai/api/v1/models", auth=False),
         "pricing, context length and hugging_face_id — the bridge to wss-hugging-face")

    # The rest of the publisher's index. Probed rather than assumed; `providers`
    # and `app-rankings` were not in the wss-openrouter registry. These 404:
    # apps, datasets/apps, datasets/rankings-weekly, datasets/model-usage,
    # classifications/app, datasets/providers, analytics, datasets.
    save("providers.json", get("https://openrouter.ai/api/v1/providers"),
         "106 providers with headquarters and datacenters")
    save("classifications-task.json",
         get("https://openrouter.ai/api/v1/classifications/task?window=7d"),
         "what the traffic is FOR, rather than which model served it")
    for src in ("artificial-analysis", "design-arena", "openrouter"):
        save(f"benchmarks-{src}.json",
             get(f"https://openrouter.ai/api/v1/benchmarks?source={src}&max_results=100"),
             f"capability scores, keyed on model_permaslug like the rankings")
    # Only these four are valid; the API rejects anything else with a 400.
    for app in ("claude-code", "codex", "kilo-code", "hermes-agent"):
        save(f"session-cost-{app}.json",
             get(f"https://openrouter.ai/api/v1/datasets/session-cost?app_slug={app}"),
             "median USD per session by model and turn range")
    # app-rankings honours an arbitrary window, so the app mix is a time series
    # too — which is how the "did the user base change" question gets an answer
    # instead of a shrug.
    for lo2, hi2 in [(date(y, m, 1), date(y + (m == 12), (m % 12) + 1, 1) - timedelta(days=1))
                     for y, m in ((2025, 2), (2025, 8), (2026, 2), (2026, 8))]:
        save(f"app-rankings-{lo2}.json",
             get("https://openrouter.ai/api/v1/datasets/app-rankings"
                 f"?start_date={lo2}&end_date={hi2}"), f"apps, {lo2} to {hi2}")

    out = os.path.join(DEST, "rankings-daily.csv")
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, ["date", "model_permaslug", "total_tokens"])
        w.writeheader()
        w.writerows({k: r.get(k) for k in w.fieldnames} for r in rows)
    days = len({r["date"] for r in rows})
    print(f"  {len(rows):,} rows over {days} days -> {out}", file=sys.stderr)
    print(f"  as_of {as_of}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
