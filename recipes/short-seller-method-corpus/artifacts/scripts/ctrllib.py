"""Load the control corpus and measure it with the SAME probes used on Hindenburg.

Two things had to be fixed before the comparison could be honest.

1. One Hindenburg probe was `Hindenburg (Researcher|Investigator)` — the firm's own
   name. Run verbatim on other firms it can only ever return zero, so "needs
   presence" would read as a Hindenburg speciality by construction. Here the firm
   name is a parameter and the generic form `our (investigator|researcher)` carries
   the rest.

2. Muddy Waters pages carry 1,668 words of identical footer disclaimer. Counted raw,
   every page looks like a 2,000-word report. Content is measured after the shared
   boilerplate is removed, and pages that fall under MIN_WORDS are recorded as
   teasers rather than silently averaged in as short reports.
"""
import hashlib, html, json, re, subprocess, statistics
from collections import Counter
from pathlib import Path
from urllib.parse import urljoin

HERE = Path(__file__).resolve().parent
RAW = HERE.parent / "raw" / "control"
MIN_WORDS = 400          # below this a page is a teaser, not a report
# Applied at LOAD time as well as capture time, so corpora captured before the
# filter existed are still measured correctly.
BOILERPLATE = re.compile(r"terms[-_]of[-_]service|privacy[-_]policy|^disclaimer|"
                         r"^terms-|cookie[-_]policy|access[-_]denied", re.I)
FIRM_NAMES = {"muddywaters": "Muddy Waters", "fuzzypanda": "Fuzzy Panda",
              "sprucepoint": "Spruce Point", "viceroy": "Viceroy",
              "nightmarket": "Night Market", "jcapital": "J Capital",
              "hindenburg": "Hindenburg"}

# Identical to chart-independent-barrier.py, with the firm name parameterised.
def tiers(firm_name):
    return [
        ("free & remote", [
            r"10-K|10-Q|8-K|proxy|DEF 14A|prospectus|SEC filing",
            r"\bInstagram\b|\bLinkedIn\b|\bFacebook\b|\bYouTube\b|\bTikTok\b|\bTwitter\b",
            r"wayback machine|web\.archive\.org|archive\.org",
            r"\bQCC\b|Qichacha|SAIC|companies house|entity search|secretary of state|UCC",
            r"\bcomplaint\b|\blawsuit\b|\bdocket\b|\bcourt filing|indictment"]),
        ("needs money", [
            r"\bBloomberg\b|\bFactSet\b|\bYCharts\b|\bRefinitiv\b|\bCapital IQ\b|Morningstar",
            r"Import ?Genius|Panjiva|bill of lading|customs record",
            r"expert network|industry experts?"]),
        ("needs presence", [
            r"onsite visit|site visit|visited the (facility|site|office|plant)",
            r"our (investigator|researcher)s?|" + re.escape(firm_name) + r" (Researcher|Investigator)"]),
        ("needs luck", [
            r"whistleblower",
            r"leaked (documents?|recordings?)|internal documents obtained"]),
    ]


# Containers that hold the report itself, most specific first.
ARTICLE = [r'<div[^>]+class="[^"]*entry-content[^"]*"[^>]*>(.*?)</div>\s*(?:</article|<footer|<aside)',
           r"<article[^>]*>(.*?)</article>",
           r"<main[^>]*>(.*?)</main>"]


def strip_html(h):
    """Text of the report, not of the page.

    Night Market's navigation bar contains a link reading "Twitter". Because each
    page's nav embeds that page's own title, the shared-prefix stripper matched
    nothing and the word survived into every document — scoring the firm at 100%
    social-media citation, which is a fact about a menu. Chrome elements go first,
    then the article container is preferred over the whole body.
    """
    b = re.sub(r"(?is)<(script|style|noscript|svg|nav|header|footer|aside|form)[^>]*>.*?</\1>", " ", h)
    # The container is accepted only if it actually holds a report's worth of
    # WORDS. The old guard counted HTML characters: Viceroy's <article> element is
    # a 557-character stub holding fifteen words, it cleared a 400-character bar,
    # and the firm's 1,714-word reports were measured as 15 — reading as
    # "teaser only" when the text was right there in the body.
    # A word floor rather than a fraction, because Muddy Waters' real 350-word
    # teaser is a small share of its boilerplate-heavy page and must still win.
    for pat in ARTICLE:
        m = re.search(pat, b, re.S | re.I)
        if m and len(html.unescape(re.sub(r"<[^>]+>", " ", m.group(1))).split()) >= 250:
            b = m.group(1)
            break
    return html.unescape(re.sub(r"<[^>]+>", " ", b))


def shared_boilerplate(docs):
    """Longest common prefix and suffix across a firm's pages, in words."""
    if len(docs) < 2:
        return 0, 0
    a, b = docs[0], docs[len(docs) // 2]
    p = 0
    while p < min(len(a), len(b)) and a[p] == b[p]:
        p += 1
    s = 0
    while s < min(len(a), len(b)) - p and a[-1 - s] == b[-1 - s]:
        s += 1
    return p, s


# The PDFs are 4-8 MB each; 146 of them is ~700 MB, too much to keep in the recipe.
# The binaries are cached outside it and only the extracted text is stored, with a
# sha256 per PDF so any later run can prove it read the same bytes. That is the
# trade: the source is live and re-fetchable, the hash makes the extraction checkable.
PDF_CACHE = Path("/tmp/claude-1000/-home-david-Desktop-programming-web-snapshots"
                 "/c3f1a220-c569-4e6b-9999-c3a995bd8549/scratchpad/pdfcache")


def pdf_text(url, textdir):
    """Fetch a linked PDF once, extract with pdftotext, record its sha256."""
    textdir.mkdir(parents=True, exist_ok=True)
    PDF_CACHE.mkdir(parents=True, exist_ok=True)
    name = re.sub(r"[^A-Za-z0-9]+", "-", url.split("/")[-1])[:80]
    pdf, txt = PDF_CACHE / f"{name}.pdf", textdir / f"{name}.txt"
    sums = textdir / "sha256.json"
    if txt.exists():
        return txt.read_text("utf-8", "replace")
    if not pdf.exists() or pdf.stat().st_size < 1000:
        r = subprocess.run(["curl", "-sS", "-L", "--max-time", "90", "-o", str(pdf),
                            "-A", "q3dresearch-cookbook/1.0 (+https://github.com/q3dresearch/cookbook)",
                            url], capture_output=True)
        if r.returncode != 0 or not pdf.exists() or pdf.read_bytes()[:4] != b"%PDF":
            return None
    subprocess.run(["pdftotext", "-q", str(pdf), str(txt)], capture_output=True)
    if not txt.exists():
        return None
    d = json.loads(sums.read_text()) if sums.exists() else {}
    d[name] = {"url": url, "sha256": hashlib.sha256(pdf.read_bytes()).hexdigest(),
               "bytes": pdf.stat().st_size}
    sums.write_text(json.dumps(d, indent=1))
    return txt.read_text("utf-8", "replace")


# Each firm stamps its publication date somewhere different — Muddy Waters in
# JSON-LD, Night Market in an OpenGraph meta tag. The first extractor only knew
# JSON-LD and quietly returned None for everyone else, which would have dropped a
# whole firm out of any era-matched comparison without saying so.
DATE_FIELDS = [
    r'"datePublished"\s*:\s*"(\d{4}-\d{2}-\d{2})',
    r'property=["\']article:published_time["\']\s+content=["\'](\d{4}-\d{2}-\d{2})',
    r'content=["\'](\d{4}-\d{2}-\d{2})[^"\']*["\']\s+property=["\']article:published_time',
    r'<time[^>]+datetime=["\'](\d{4}-\d{2}-\d{2})',
    r'"dateModified"\s*:\s*"(\d{4}-\d{2}-\d{2})',
    # J Capital stamps nothing in the HTML but names every report PDF
    # 2019_09_05_bgne_1.pdf. The filename is the only date the site exposes.
    r'href="[^"]*?/(\d{4})[_-](\d{2})[_-](\d{2})[_-][^"/]*\.pdf',
    # Spruce Point names its PDFs twou_research_thesis_7-19-2018.pdf — month first,
    # no zero padding, and the year last.
    r'href="[^"]*?_(\d{1,2})-(\d{1,2})-(\d{4})\.pdf',
]


def published(h):
    for pat in DATE_FIELDS:
        m = re.search(pat, h, re.I)
        if not m:
            continue
        g = m.groups()
        if len(g) == 1:
            return g[0]
        if len(g[0]) == 4:                       # YYYY MM DD
            return f"{g[0]}-{int(g[1]):02d}-{int(g[2]):02d}"
        return f"{g[2]}-{int(g[0]):02d}-{int(g[1]):02d}"   # M D YYYY
    return None


def pick_pdf(links, rec):
    """Which PDF on the page is THE report for this page?

    A J Capital ticker page lists that target's whole history, so the first link
    is the newest report, not the one the page is about. The page slug carries the
    ticker; prefer a PDF whose filename carries it too, and among those the
    earliest — the first look, which is what every comparison here counts.
    """
    slug = re.sub(r"[-_]?html$", "", rec["file"][:-5]).strip("-_")
    key = slug.split("-")[0].lower()
    named = [u for u in links if re.search(rf"\d{{4}}[_-]\d\d[_-]\d\d[_-]{re.escape(key)}\b",
                                           u.split("/")[-1], re.I)]
    if named:
        return sorted(named, key=lambda u: u.split("/")[-1])[0]
    return links[0]


def load(firm, *, with_pdf=True, limit=None):
    """Return [{slug, url, words, text, kind}] for one firm."""
    man = json.loads((RAW / "manifest.json").read_text())
    cfg = man[firm]
    d = RAW / firm
    raws, meta = [], []
    for rec in cfg["reports"][:limit]:
        f = d / rec["file"]
        if not f.exists() or BOILERPLATE.search(rec["file"]):
            continue
        h = f.read_text("utf-8", "replace")
        raws.append(strip_html(h).split())
        meta.append((rec, h))
    pre, suf = shared_boilerplate(raws)
    out = []
    for (rec, h), w in zip(meta, raws):
        body = w[pre:len(w) - suf] if suf else w[pre:]
        kind, text = "html", " ".join(body)
        if cfg["text"] == "pdf" and with_pdf:
            # Muddy Waters links PDFs absolutely, J Capital relatively
            # (/uploads/2/0/0/3/20032477/2019_09_05_bgne_1.pdf). Matching only
            # https:// found nothing at J Capital and the firm loaded as 530-word
            # teasers — a whole corpus of 215 reports invisible behind a missing
            # slash rule.
            links = [urljoin(cfg["home"], u) for u in
                     re.findall(r'href="([^"]+\.pdf[^"]*)"', h, re.I)]
            links = [u for u in links if u.startswith("http")]
            if links:
                t = pdf_text(pick_pdf(links, rec), RAW / f"{firm}-pdftext")
                # When a firm is marked text="pdf" the page is a shell and the PDF
                # is the report, so the PDF wins outright — not "whichever is
                # longer". J Capital's shell opens with its entire ticker menu
                # (AAN ACMR AMLI AOS AXTI ...) and that site has no <nav> element
                # to strip, so the menu alone made some pages read longer than the
                # report they link to.
                if t and len(t.split()) >= MIN_WORDS:
                    kind, text = "pdf", t
        # Era matters more than firm for some probes — social-media citation rose
        # sharply across the 2010s — so every document carries its date and the
        # comparison can be restricted to the years both corpora cover.
        out.append({"slug": rec["file"][:-5], "url": rec["url"], "kind": kind,
                    "date": published(h),
                    "words": len(text.split()), "text": text})
    # PDF corpora get a second pass. The HTML template is bracketed by the content
    # and comes off with a shared prefix/suffix; a PDF's legal block is scattered
    # through the extracted text by pdftotext and only repetition finds it.
    pdf_removed = 0
    pdfs = [d for d in out if d["kind"] == "pdf"]
    if len(pdfs) >= 5:
        cleaned, pdf_removed = strip_boilerplate([d["text"] for d in pdfs])
        for d, c in zip(pdfs, cleaned):
            d["text"], d["words"] = c, len(c.split())
    return out, {"boiler_prefix": pre, "boiler_suffix": suf, "pdf_boiler": pdf_removed}


def measure(docs, firm):
    """Share of reports hitting each probe, on reports only (teasers excluded)."""
    T = tiers(FIRM_NAMES.get(firm, firm))
    reports = [d for d in docs if d["words"] >= MIN_WORDS]
    hits = Counter()
    for d in reports:
        for tier, pats in T:
            for p in pats:
                if re.search(p, d["text"], re.I):
                    hits[(tier, p)] += 1
                    hits[tier] += 1
                    break
    return reports, hits


# ---------------------------------------------------------------------------
# One target rule for every firm.
#
# Muddy Waters names the target in the URL (/research/<target>/<slug>/). Nobody
# else does — Night Market and J Capital lead the slug with the ticker instead
# ("zentek", "zentek-update"; "zyxi", "zyxi-undisclosed-loss"). Comparing firms
# classified by different rules is how the first pass ended up measuring 94
# Hindenburg INITIAL reports against 76 Muddy Waters reports that included
# rebuttals, so the rule is defined once and applied to everyone.
#
# The first report on a target is the initial one; everything later about the same
# target is a follow-up. Where a slug also says "update" outright, that is recorded
# too, and the two signals are reported separately so neither is taken on faith.
# ---------------------------------------------------------------------------

SAYS_UPDATE = re.compile(r"(^|-)(update|updated|part-?\d|part-(two|three|iii|ii)|"
                         r"response|reply|revisited|redux|round-?\d)(-|$)", re.I)


def target_of(doc):
    """The company a report is about, from whatever the firm's URLs expose."""
    m = re.search(r"/research/([^/]+)/[^/]", doc["url"])
    if m:                                   # Muddy Waters: target is a path segment
        return m.group(1)
    slug = re.sub(r"\.html?$", "", doc["slug"])
    slug = SAYS_UPDATE.sub("-", slug).strip("-")
    return slug.split("-")[0]               # everyone else: leading ticker token


def split_reports(docs):
    """(initial, follow_ups). Dateless docs cannot be ordered, so they are
    reported rather than guessed at — the caller sees the count."""
    dated = [d for d in docs if d.get("date")]
    undated = [d for d in docs if not d.get("date")]
    for d in dated:
        d["target"] = target_of(d)
        d["says_update"] = bool(SAYS_UPDATE.search(d["slug"]))
    first = {}
    for d in sorted(dated, key=lambda x: (x["date"], x["slug"])):
        first.setdefault(d["target"], d)
    init = list(first.values())
    return init, [d for d in dated if d not in init], undated


def audit_probes(corpora):
    """Flag probes that saturate or vanish on a corpus. Returns a list of warnings.

    Two bugs in this recipe would have been caught by running it:

    * Night Market scored 100% on social media. Its navigation bar contains a link
      reading "Twitter", and because each page's nav embeds that page's own title,
      the shared-prefix stripper never removed it. A probe that matches EVERY
      document is usually matching the template.
    * Night Market scored 0% on every original-sourcing probe. It was not a desk
      shop; it files FOIA requests and interviews companies at trade conferences,
      and the probe list — written by reading Hindenburg — had no name for either.
      A probe that matches NO document is either a real absence or a blind spot,
      and the two look identical until someone reads the text.

    `corpora` is {name: (docs, probes, get_text)}.
    """
    warn = []
    for name, (docs, P, get) in corpora.items():
        if len(docs) < 10:
            continue
        for lab, pat in P.items():
            share = sum(1 for d in docs if re.search(pat, get(d), re.I)) / len(docs)
            if share >= 0.97:
                warn.append(f"{name}: '{lab}' matches {share:.0%} — check for page template text")
            elif share == 0:
                warn.append(f"{name}: '{lab}' matches nothing — real absence, or a word this firm uses differently?")
    return warn


def corpus_health(firm, docs, info):
    """Warnings about a firm's corpus, before anything is measured on it.

    Three separate figures in this recipe were wrong because a page's template was
    counted as its content:

    * Muddy Waters appends 1,613 words of terms-of-use to every report page, so its
      319-word teasers read as 1,940-word reports.
    * Night Market's navigation bar contains a link saying "Twitter", which scored
      the firm at 100% social-media citation.
    * Spruce Point carries 9,525 words of boilerplate against 618 words of content,
      and went onto a published chart as a 10,136-word full-text archive.

    Each was found by hand, late, after the number had already been used. The ratio
    that gives it away is cheap to compute, so it is computed every time.
    """
    warn = []
    boiler = info["boiler_prefix"] + info["boiler_suffix"]
    if docs:
        med = statistics.median(d["words"] for d in docs)
        if boiler > med:
            warn.append(f"{firm}: {boiler:,} words of template against {med:,.0f} of content "
                        f"— the page is mostly boilerplate, so check what 'the report' is")
        undated = sum(1 for d in docs if not d.get("date"))
        if undated:
            warn.append(f"{firm}: {undated}/{len(docs)} reports carry no date — they cannot be "
                        f"ordered, so first-look and follow-up cannot be told apart")
        kinds = Counter(d["kind"] for d in docs)
        if len(kinds) > 1:
            warn.append(f"{firm}: mixed extraction — {dict(kinds)}. Word counts are not "
                        f"comparable across a PDF and an HTML shell")
    return warn


def repeated_sentences(texts, threshold=0.6):
    """Sentences that appear in most documents of a corpus — i.e. its boilerplate.

    The shared prefix/suffix trick works on HTML, where the template brackets the
    content. It fails on PDFs: pdftotext interleaves page headers and footers with
    the body, so the legal block is neither at the start nor the end and the shared
    run measures zero. Spruce Point's disclaimer — which states outright that the
    firm "frequently speaks with industry experts and former employees" — sits in
    all 45 of its reports and was being counted as report text.

    Position-free: a sentence in more than `threshold` of the documents is template.
    """
    # pdftotext breaks lines differently in every file, so the SAME sentence is a
    # different string in each one. Whitespace is collapsed before comparing —
    # without it only 11 words of Spruce Point's disclaimer matched across 45
    # reports instead of the whole block.
    df = Counter()
    for t in texts:
        df.update(norm_sentences(t).keys())
    n = len(texts)
    return {s for s, c in df.items() if c >= threshold * n}


def norm_sentences(t):
    """{normalised sentence: original} for sentences long enough to be prose."""
    out = {}
    for s in re.split(r"(?<=[.!?])\s+", t):
        k = re.sub(r"\s+", " ", s).strip()
        if 30 < len(k) < 400:
            out[k] = s
    return out


def strip_boilerplate(texts, threshold=0.6):
    """Remove the corpus's repeated sentences from each document."""
    common = repeated_sentences(texts, threshold)
    if not common:
        return texts, 0
    out = []
    for t in texts:
        keep = [s for s in re.split(r"(?<=[.!?])\s+", t)
                if re.sub(r"\s+", " ", s).strip() not in common]
        out.append(" ".join(keep))
    removed = statistics.median(len(a.split()) - len(b.split()) for a, b in zip(texts, out))
    return out, removed


def first_look(firm, with_pdf=True):
    """The set of first reports for a firm, by whatever rule that firm's site allows.

    Three shapes, one entry point, because getting this wrong is how the first pass
    compared 94 Hindenburg first reports against 76 Muddy Waters reports that
    included rebuttals:

    * A firm whose page IS the report (Night Market, Fuzzy Panda): order by date and
      keep the first report per target.
    * A firm whose page lists a target's PDFs (J Capital, Spruce Point): the PDF
      picked per page is already that target's first look, so the PDFs are the set.
    * Muddy Waters: a page per report, so date-order them — but drop the 7 pages
      that link no PDF, since an HTML teaser and an extracted PDF are not the same
      measurement and mixing them moved its interview share by 2 points.
    """
    docs, info = load(firm, with_pdf=with_pdf)
    docs = [d for d in docs if d["words"] >= MIN_WORDS]
    cfg = json.loads((RAW / "manifest.json").read_text())[firm]
    if cfg["text"] == "pdf":
        docs = [d for d in docs if d["kind"] == "pdf"]
        if firm in ("jcapital", "sprucepoint"):
            return docs, info
    init, _, _ = split_reports(docs)
    return init, info
