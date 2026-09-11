"""What each activist short-selling firm lets an outsider read.

    python capture_access.py

This is the census behind question 14. Any study of "the practice" is really a
study of the firms that publish in a readable form, and that set is smaller than
the set of firms — so the selection has to be measured rather than assumed.

For each firm it records, in order: does a sitemap answer, how many report-shaped
URLs it lists, and what a sample report page actually contains — full text, a
teaser in front of a PDF, or a teaser in front of nothing.

The order matters. The first sweep of this recipe asked every firm for
/wp-json/wp/v2/posts and concluded the others "block scraping or publish only
PDFs". Muddy Waters keeps its reports in a custom post type that endpoint cannot
return; the sitemap lists all 146. The REST API is asked LAST here, and only as a
convenience, never as evidence of absence.
"""
import json, re, subprocess, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "raw" / "access-audit.json"
UA = "q3dresearch-cookbook/1.0 (+https://github.com/q3dresearch/cookbook; research use)"

FIRMS = ["muddywatersresearch.com", "citronresearch.com", "blueorcacapital.com",
         "kerrisdalecap.com", "culperresearch.com", "grizzlyresearch.com",
         "bonitasresearch.com", "fuzzypandaresearch.com", "hunterbrookmedia.com",
         "nightmarketresearch.com", "wolfpackresearch.com", "jcapitalresearch.com",
         "scorpioncapital.com", "viceroyresearch.org", "sprucepointcap.com",
         "gothamcityresearch.com", "hindenburgresearch.com"]


def curl(url, timeout=40):
    r = subprocess.run(["curl", "-sS", "-L", "--compressed", "--max-time", str(timeout),
                        "-A", UA, "-w", "\n@@%{http_code}", url], capture_output=True)
    t = r.stdout.decode("utf-8", "replace")
    code = t.rsplit("@@", 1)[-1].strip() if "@@" in t else "000"
    return t.rsplit("\n@@", 1)[0], code


def text_of(h):
    b = re.sub(r"(?is)<(script|style|noscript|svg|nav|header|footer|aside|form)[^>]*>.*?</\1>", " ", h)
    # The container is accepted only if it actually holds a report's worth of
    # WORDS. The old guard counted HTML characters: Viceroy's <article> element is
    # a 557-character stub holding fifteen words, it cleared a 400-character bar,
    # and the firm's 1,714-word reports were measured as 15 — reading as
    # "teaser only" when the text was right there in the body.
    # A word floor rather than a fraction, because Muddy Waters' real 350-word
    # teaser is a small share of its boilerplate-heavy page and must still win.
    for pat in (r'<div[^>]+class="[^"]*entry-content[^"]*"[^>]*>(.*?)</div>\s*(?:</article|<footer)',
                r"<article[^>]*>(.*?)</article>", r"<main[^>]*>(.*?)</main>"):
        m = re.search(pat, b, re.S | re.I)
        if m and len(re.sub(r"<[^>]+>", " ", m.group(1)).split()) >= 250:
            b = m.group(1)
            break
    return re.sub(r"<[^>]+>", " ", b).split()


def probe(dom):
    row = {"domain": dom}
    for path in ("sitemap.xml", "sitemap_index.xml"):
        body, code = curl(f"https://{dom}/{path}")
        if "<loc>" in body:
            row["sitemap"] = code
            locs = re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", body)
            subs = [u for u in locs if u.endswith(".xml")]
            urls = []
            for s in subs[:10]:
                time.sleep(0.8)
                sb, _ = curl(s)
                urls += [u for u in re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", sb)
                         if not u.endswith(".xml")]
            row["urls"] = len(urls or locs)
            row["pages"] = list(dict.fromkeys(urls or locs))
            break
    else:
        row["sitemap"] = code
        row["urls"] = 0
        row["pages"] = []

    # Neither the shallowest nor the deepest URL tier identifies reports.
    # Taking anything past four path segments picked Muddy Waters' per-company
    # index pages; taking the deepest tier instead picked category and tag pages,
    # and reported Hindenburg — whose archive is 737,000 words — at 33 words.
    #
    # So no tier is assumed. Each is sampled and the one carrying the most text is
    # the firm's report tier, because that is what a report tier IS. The tiers that
    # lose are kept in the record, so a later reader can see the choice was made.
    by_depth = {}
    for u in row["pages"]:
        d = len(u.rstrip("/").split("/"))
        if d >= 4:
            by_depth.setdefault(d, []).append(u)

    tiers, best = [], None
    for d in sorted(by_depth, reverse=True)[:4]:
        urls = by_depth[d]
        step = max(1, len(urls) // 4)
        sample = urls[::step][:4]
        words, pdfs, codes, texts = [], 0, [], []
        for u in sample:
            time.sleep(0.7)
            h, c = curl(u)
            codes.append(c)
            if c == "200":
                tx = text_of(h)
                texts.append(tx)
                words.append(len(tx))
                pdfs += len(set(re.findall(r'href="([^"]+\.pdf[^"]*)"', h, re.I)))
        # Muddy Waters appends a 1,668-word terms-of-use block to every report
        # page. Counted raw, its ~350-word teasers read as 1,940-word full text
        # and the firm was classified as publishing in HTML when the report is
        # the linked PDF. Whatever the sampled pages share word-for-word at the
        # start or end is template, not content.
        # Comparing one fixed pair is fragile: if either page is atypical the shared
        # run collapses. On Muddy Waters that returned 27 template words where the
        # real terms-of-use block is 1,617, and the firm was classified as
        # publishing full text. Every pair is measured and the median taken, so one
        # odd page in the sample cannot hide the template.
        def run(a, b):
            i = 0
            while i < min(len(a), len(b)) and a[i] == b[i]:
                i += 1
            j = 0
            while j < min(len(a), len(b)) - i and a[-1 - j] == b[-1 - j]:
                j += 1
            return i, j

        p = s = 0
        if len(texts) >= 2:
            pairs = [run(texts[i], texts[k])
                     for i in range(len(texts)) for k in range(i + 1, len(texts))]
            ps = sorted(x[0] for x in pairs)
            ss = sorted(x[1] for x in pairs)
            p, s = ps[len(ps) // 2], ss[len(ss) // 2]
        words = [max(0, w - p - s) for w in words]
        med = sorted(words)[len(words) // 2] if words else 0
        tier = {"depth": d, "n_urls": len(urls), "sampled": len(sample),
                "codes": codes, "median_words": med, "pdf_links": pdfs,
                "template_words": p + s}
        tiers.append(tier)
        if best is None or med > best["median_words"]:
            best = tier

    row["tiers"] = tiers
    row["depth"] = best["depth"] if best else 0
    row["sampled"] = best["sampled"] if best else 0
    row["codes"] = best["codes"] if best else []
    row["median_words"] = best["median_words"] if best else 0
    row["pdf_links"] = best["pdf_links"] if best else 0
    _, api = curl(f"https://{dom}/wp-json/wp/v2/posts?per_page=1")
    row["rest_api"] = api
    return row


def classify(r):
    """What can an outsider actually read?

    PDF is checked BEFORE length. A firm that puts a real report behind a link and
    a summary on the page is publishing in PDF, however long the page reads.
    """
    if r["urls"] == 0:
        return "unreadable"
    if r["median_words"] >= 1500 and r["pdf_links"] == 0:
        return "full text"
    if r["pdf_links"] > 0 and r["median_words"] < 1500:
        return "PDF only"
    if r["median_words"] >= 1500:
        return "full text + PDF"
    return "teaser only"


def main():
    out = []
    for d in FIRMS:
        r = probe(d)
        r["access"] = classify(r)
        r.pop("pages")
        out.append(r)
        print(f"  {d:<26} sitemap {r['sitemap']:<4} urls {r['urls']:>4} "
              f"median {r['median_words']:>6}w (-{r['tiers'][0].get('template_words',0) if r['tiers'] else 0} template) "
              f"pdf {r['pdf_links']:>3}  -> {r['access']}", flush=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1))
    print(f"  -> {OUT}")


if __name__ == "__main__":
    main()
