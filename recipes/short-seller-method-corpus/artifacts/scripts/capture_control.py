"""Capture a control corpus: activist short reports from firms OTHER than Hindenburg.

Why this exists. The first probe of this recipe asked every firm for
/wp-json/wp/v2/posts and concluded that the others "block scraping or publish only
PDFs". That conclusion was about the probe, not the sources. Muddy Waters keeps its
reports in a custom post type (/research/<company>/<slug>/) which wp/v2/posts never
returns and which only the sitemap reveals. Sitemap-first finds report text at six
firms. Silence was not data; it was a wrong endpoint.

Capture is the irreversible step, so this stores raw bytes and nothing else. All
parsing happens later, in ctrllib.py, against files on disk.
"""
import json, re, sys, time, urllib.request, urllib.error
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAW = HERE.parent / "raw" / "control"
UA = "q3dresearch-cookbook/1.0 (+https://github.com/q3dresearch/cookbook; research use)"
PAUSE = 1.2  # one request per ~1.2s per host, sequential across hosts

# Each firm: the sitemap entry point, and the URL shape that means "this is a report".
# The shapes come from reading each sitemap, not from guessing: see notes.md.
FIRMS = {
    "muddywaters": dict(
        home="https://muddywatersresearch.com",
        sitemap="https://muddywatersresearch.com/sitemap.xml",
        is_report=lambda p: p.startswith("research/") and p.count("/") >= 2,
        text="pdf",  # page is a teaser; the report is the linked PDF
    ),
    "fuzzypanda": dict(
        home="https://fuzzypandaresearch.com",
        sitemap="https://fuzzypandaresearch.com/sitemap.xml",
        is_report=lambda p: p.count("/") == 0 and p not in SKIP_SLUGS,
        text="html",
    ),
    "sprucepoint": dict(
        home="https://sprucepointcap.com",
        sitemap="https://sprucepointcap.com/sitemap.xml",
        is_report=lambda p: p.startswith("research/") and p.count("/") == 1,
        text="pdf",   # every page is a ~618-word teaser over 9,525 words of boilerplate
    ),
    "viceroy": dict(
        home="https://viceroyresearch.org",
        sitemap="https://viceroyresearch.org/sitemap.xml",
        is_report=lambda p: p.startswith("publications/") and p.count("/") == 1,
        text="html",
    ),
    "nightmarket": dict(
        home="https://nightmarketresearch.com",
        sitemap="https://nightmarketresearch.com/sitemap.xml",
        is_report=lambda p: p.count("/") == 0 and p not in SKIP_SLUGS,
        text="html",
    ),
    "jcapital": dict(
        home="https://jcapitalresearch.com",
        sitemap="https://jcapitalresearch.com/sitemap.xml",
        is_report=lambda p: p.endswith(".html") and p not in SKIP_HTML,
        text="pdf",   # the .html page is a ~530-word teaser; the report is the PDF
    ),
}

SKIP_SLUGS = {"", "about", "about-us", "contact", "contact-us", "disclaimer", "terms",
              "privacy", "privacy-policy", "legal", "media", "news", "press", "team",
              "careers", "subscribe", "mailing-list-signup", "home", "research",
              "reports", "publications", "tip", "tips", "submit-an-idea", "lander"}
SKIP_HTML = {"in-the-news.html", "about.html", "contact.html", "team.html",
             "ex-china-equities.html", "index.html", "disclaimer.html",
             "access-denied.html", "blog.html", "careers.html", "china-equities.html"}
# Half of J Capital's sitemap is <ticker>-terms-of-service.html, and Night Market
# carries one too. They are legal boilerplate with a target's name on them, so a
# slug filter alone lets them through — and a page that cites nothing scores as
# "reachable from a desk", which is the exact distortion the Muddy Waters
# follow-ups caused. Anything matching this is not a report.
BOILERPLATE = re.compile(r"terms[-_]of[-_]service|privacy[-_]policy|^disclaimer|"
                         r"^terms|cookie[-_]policy|access[-_]denied", re.I)


def fetch(url, binary=False):
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                               "Accept-Language": "en-US,en;q=0.9"})
    with urllib.request.urlopen(req, timeout=45) as r:
        return r.read() if binary else r.read().decode("utf-8", "replace")


def sitemap_urls(entry):
    """Expand a sitemap, following one level of <sitemapindex>."""
    seen, out = set(), []
    try:
        root = fetch(entry)
    except Exception as e:
        print(f"    sitemap {entry}: {type(e).__name__}")
        return out
    locs = re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", root)
    subs = [u for u in locs if u.endswith(".xml")]
    if not subs:
        return [u for u in locs if not u.endswith(".xml")]
    for s in subs:
        if s in seen:
            continue
        seen.add(s)
        time.sleep(PAUSE)
        try:
            out += [u for u in re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", fetch(s))
                    if not u.endswith(".xml")]
        except Exception as e:
            print(f"    sub-sitemap {s.split('/')[-1]}: {type(e).__name__}")
    return out


def path_of(url, home):
    return url.split(home.split("//")[-1], 1)[-1].lstrip("/").rstrip("/") \
        if home.split("//")[-1] in url else url


def main(only=None, sample=None):
    """Capture one firm, or all of them.

    The manifest is READ before it is written. Running one firm at a time used to
    start from an empty dict and write it back, so capturing fuzzypanda silently
    erased muddywaters' entry — the HTML was still on disk but nothing knew about it.
    """
    RAW.mkdir(parents=True, exist_ok=True)
    mf = RAW / "manifest.json"
    manifest = json.loads(mf.read_text()) if mf.exists() else {}
    for firm, cfg in FIRMS.items():
        if only and firm != only:
            continue
        print(f"  {firm}", flush=True)
        urls = sitemap_urls(cfg["sitemap"])
        reports = [u for u in dict.fromkeys(urls)
                   if cfg["is_report"](path_of(u, cfg["home"]))
                   and not BOILERPLATE.search(path_of(u, cfg["home"]))]
        print(f"    {len(urls)} sitemap urls -> {len(reports)} look like reports", flush=True)
        # Viceroy lists 331 reports and Spruce Point 134. Captured whole they take
        # hours, and a share estimate does not need a census: a systematic sample
        # across the sorted list covers the firm's whole history evenly, which a
        # head-of-list slice would not. The sample size is recorded so no later
        # reader mistakes it for the full archive.
        sampled_from = None
        if sample and len(reports) > sample:
            sampled_from = len(reports)
            step = len(reports) / sample
            reports = [reports[int(i * step)] for i in range(sample)]
            print(f"    sampling {len(reports)} of {sampled_from}, evenly spaced", flush=True)
        d = RAW / firm
        d.mkdir(exist_ok=True)
        got, failed = [], []
        for i, u in enumerate(reports, 1):
            slug = re.sub(r"[^a-z0-9]+", "-", path_of(u, cfg["home"]).lower()).strip("-")[:90]
            f = d / f"{slug}.html"
            if f.exists() and f.stat().st_size > 0:
                got.append({"url": u, "file": f.name})
                continue
            time.sleep(PAUSE)
            try:
                f.write_bytes(fetch(u, binary=True))
                got.append({"url": u, "file": f.name})
            except Exception as e:
                failed.append({"url": u, "err": f"{type(e).__name__}: {str(e)[:90]}"})
                print(f"      fail {path_of(u, cfg['home'])[:44]}: {type(e).__name__}", flush=True)
            if i % 25 == 0:
                print(f"    {i}/{len(reports)}", flush=True)
        print(f"    captured {len(got)}, failed {len(failed)}", flush=True)
        # Re-read immediately before writing. Two captures running at once each
        # read the manifest at start and wrote it at the end, so the second to
        # finish erased the first — Spruce Point's 45 reports vanished from the
        # manifest while its HTML sat on disk, invisible to every loader.
        live = json.loads(mf.read_text()) if mf.exists() else {}
        live.update(manifest)
        live[firm] = {"home": cfg["home"], "text": cfg["text"],
                      "sampled_from": sampled_from,
                      "reports": got, "failed": failed}
        manifest = live
        mf.write_text(json.dumps(manifest, indent=1))
    print(f"  manifest holds: " + ", ".join(f"{k} {len(v['reports'])}" for k, v in manifest.items()))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None,
         int(sys.argv[2]) if len(sys.argv) > 2 else None)
