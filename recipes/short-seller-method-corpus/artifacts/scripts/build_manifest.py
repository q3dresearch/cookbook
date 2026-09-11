"""Write a capture manifest for everything this recipe fetched.

    python build_manifest.py

Why this recipe needs one when the others did not. The promoted recipes in the
cookbook read eCFR, FDA and USDA — public registries that keep their history and
answer the same query next year. This one reads eight private firms that can delete
a report the day it becomes inconvenient, and one of them, Hindenburg, has already
wound down. The archive is closed; the site is somebody's to switch off.

So the public recipe ships a record of WHAT was captured and WHEN, even though it
cannot ship the captures themselves. Each row is one fetched resource: its URL, the
hour it was read, its size and its sha256. A reader who re-fetches and gets the same
hash knows they are holding what these charts were computed from. A reader who gets
a 404 knows exactly what is gone, which is itself worth publishing.

Columns follow the wss fleet convention so the file reads the same as
wss-openrouter/manifest/*.csv.
"""
import csv, hashlib, json, re, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAW = HERE.parent / "raw"
OUT = HERE.parent / "manifest"
COLS = ["source_id", "url", "fetched_at", "http_status", "content_type",
        "content_length", "content_sha256", "outcome", "raw_ref", "reason"]


def stamp(p):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(p.stat().st_mtime))


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def rows():
    out = []

    # Hindenburg — one JSON dump of the WordPress REST API.
    # Newest capture, not a fixed date — capture_hindenburg.py stamps the day it runs.
    caps = sorted((RAW / "hindenburg").glob("hindenburg-corpus-*.json"))
    hb = caps[-1] if caps else None
    if hb:
        out.append(dict(source_id="hindenburg.posts", url="https://hindenburgresearch.com/wp-json/wp/v2/posts",
                        fetched_at=stamp(hb), http_status=200, content_type="application/json",
                        content_length=hb.stat().st_size, content_sha256=sha(hb),
                        outcome="captured", raw_ref=str(hb.relative_to(RAW.parent)), reason=""))

    man = RAW / "control" / "manifest.json"
    if man.exists():
        firms = json.loads(man.read_text())
        for firm, cfg in firms.items():
            d = RAW / "control" / firm
            for rec in cfg["reports"]:
                p = d / rec["file"]
                if not p.exists():
                    continue
                out.append(dict(source_id=f"{firm}.page", url=rec["url"], fetched_at=stamp(p),
                                http_status=200, content_type="text/html",
                                content_length=p.stat().st_size, content_sha256=sha(p),
                                outcome="captured", raw_ref=str(p.relative_to(RAW.parent)),
                                reason="sampled" if cfg.get("sampled_from") else ""))
            for rec in cfg.get("failed", []):
                out.append(dict(source_id=f"{firm}.page", url=rec["url"], fetched_at="",
                                http_status="", content_type="", content_length="",
                                content_sha256="", outcome="failed", raw_ref="",
                                reason=rec.get("err", "")[:80]))

    # The PDFs each firm links — for three firms these ARE the reports.
    for sf in sorted((RAW / "control").glob("*-pdftext/sha256.json")):
        firm = sf.parent.name.replace("-pdftext", "")
        for name, meta in json.loads(sf.read_text()).items():
            pdf = RAW / "control" / "pdf" / f"{name}.pdf"
            out.append(dict(source_id=f"{firm}.report_pdf", url=meta["url"],
                            fetched_at=stamp(pdf) if pdf.exists() else "",
                            http_status=200, content_type="application/pdf",
                            content_length=meta.get("bytes", ""), content_sha256=meta["sha256"],
                            outcome="captured" if pdf.exists() else "text_only",
                            raw_ref=f"raw/control/pdf/{name}.pdf" if pdf.exists() else
                                    f"raw/control/{firm}-pdftext/{name}.txt",
                            reason="" if pdf.exists() else "binary not retained; extracted text kept"))

    # Prices, share counts and the SEC registry — the market-side captures.
    prices = RAW / "prices"
    if (prices / "coverage.json").exists():
        cov = json.loads((prices / "coverage.json").read_text())
        for sym, meta in cov.items():
            f = prices / f"{sym}.json"
            out.append(dict(source_id="stockanalysis.history",
                            url=f"https://stockanalysis.com/api/symbol/s/{sym.lower()}/history"
                                "?period=Daily&range=Max",
                            fetched_at=stamp(f) if f.exists() else "",
                            http_status=200 if f.exists() else "",
                            content_type="application/json",
                            content_length=f.stat().st_size if f.exists() else "",
                            content_sha256=sha(f) if f.exists() else "",
                            outcome="captured" if f.exists() else meta.get("outcome", "absent"),
                            raw_ref=f"raw/prices/{sym}.json" if f.exists() else "",
                            reason=meta.get("reason", "")))
    shares = RAW / "shares"
    if shares.exists():
        for f in sorted(shares.glob("*.json")):
            if f.name == "coverage.json":
                continue
            out.append(dict(source_id="sec.shares_outstanding",
                            url=f"https://data.sec.gov/api/xbrl/companyconcept/"
                                f"CIK/dei/EntityCommonStockSharesOutstanding.json ({f.stem})",
                            fetched_at=stamp(f), http_status=200,
                            content_type="application/json",
                            content_length=f.stat().st_size, content_sha256=sha(f),
                            outcome="captured", raw_ref=f"raw/shares/{f.name}", reason=""))
    reg = RAW / "sec" / "company_tickers_exchange.json"
    if reg.exists():
        out.append(dict(source_id="sec.ticker_registry",
                        url="https://www.sec.gov/files/company_tickers_exchange.json",
                        fetched_at=stamp(reg), http_status=200, content_type="application/json",
                        content_length=reg.stat().st_size, content_sha256=sha(reg),
                        outcome="captured", raw_ref="raw/sec/company_tickers_exchange.json",
                        reason="ticker -> company -> exchange, used to validate extractions"))

    # The access census — firms that answered, and the four that refused.
    aa = RAW / "access-audit.json"
    if aa.exists():
        for r in json.loads(aa.read_text()):
            out.append(dict(source_id="access_audit", url=f"https://{r['domain']}/sitemap.xml",
                            fetched_at=stamp(aa), http_status=r.get("sitemap", ""),
                            content_type="application/xml", content_length="", content_sha256="",
                            outcome="captured" if r["urls"] else "refused",
                            raw_ref="raw/access-audit.json",
                            reason=r.get("access", "")))
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    data = rows()
    # A row with no fetch time is a resource that REFUSED — a 403 sitemap, a ticker
    # with no history. Those are findings and belong in the month the attempt was
    # made, not in a shard called "unknown" that reads like a filing error.
    run_month = time.strftime("%Y-%m")
    by_month = {}
    for r in data:
        by_month.setdefault((r["fetched_at"][:7] if r["fetched_at"] else run_month), []).append(r)
    for month, rs in sorted(by_month.items()):
        f = OUT / f"{month}.csv"
        with f.open("w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=COLS)
            w.writeheader()
            w.writerows(rs)
        print(f"  manifest/{f.name}: {len(rs)} rows")
    outcomes = {}
    for r in data:
        outcomes[r["outcome"]] = outcomes.get(r["outcome"], 0) + 1
    print(f"  {len(data)} resources total: " + ", ".join(f"{v} {k}" for k, v in sorted(outcomes.items())))
    total = sum(int(r["content_length"]) for r in data if str(r["content_length"]).isdigit())
    print(f"  {total/1e6:.0f} MB captured, recorded in {sum(f.stat().st_size for f in OUT.glob('*.csv'))/1024:.0f} KB of manifest")


if __name__ == "__main__":
    main()
