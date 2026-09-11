#!/usr/bin/env python3
"""Any study of activist short sellers is a study of the ones that publish readably.

    python chart-who-can-be-studied.py

Each firm placed by how many reports its sitemap lists against how many words a
reader can actually extract from one. The corner at the top right is the only part
of this field that can be studied at all; four firms are not on the plot, because
they refuse the connection.

Filled marks are firms whose whole archive was captured and measured here. Open
marks are estimates from a four-page sample, and they are drawn differently because
they are worth less: the same sampler read Muddy Waters at 1,940 words per report
when its full 146-page corpus measures 319, by landing on a mixed tier of URLs.
Where a measured corpus exists it overrides the sample, and where it does not, the
mark says so.

This is the selection the recipe sits inside, drawn rather than assumed.
"""
import json, re, statistics, sys
from pathlib import Path
from xml.sax.saxutils import escape

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ctrllib, corpuslib, palette

OUT = Path(__file__).resolve().parents[1] / "charts" / "who-can-be-studied.svg"
AUDIT = Path(__file__).resolve().parents[1] / "raw" / "access-audit.json"
SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
GRID, BASELINE = "#e1e0d9", "#c3c2b7"
FULL, PDF, TEASER = "#2361b0", "#b8912a", "#7a4a1e"
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'
CLASS_COL = {"full text": FULL, "PDF": PDF, "teaser": TEASER}

# Firms whose archive this recipe actually captured — these override the sample.
MEASURED = {"muddywatersresearch.com": ("muddywaters", "PDF"),
            "nightmarketresearch.com": ("nightmarket", "full text"),
            "jcapitalresearch.com": ("jcapital", "PDF")}
# Captured but not in the manifest — these runs were cut short, so the pages are
# on disk without a manifest entry. Measured from the files directly, with the
# count shown so a partial capture is never mistaken for an archive.
PARTIAL = {"viceroyresearch.org": ("viceroy", "full text"),
           "fuzzypandaresearch.com": ("fuzzypanda", "full text"),
           "sprucepointcap.com": ("sprucepoint", "full text")}
SHORT = {"muddywatersresearch.com": "Muddy Waters", "citronresearch.com": "Citron",
         "blueorcacapital.com": "Blue Orca", "kerrisdalecap.com": "Kerrisdale",
         "culperresearch.com": "Culper", "grizzlyresearch.com": "Grizzly",
         "bonitasresearch.com": "Bonitas", "fuzzypandaresearch.com": "Fuzzy Panda",
         "hunterbrookmedia.com": "Hunterbrook", "nightmarketresearch.com": "Night Market",
         "wolfpackresearch.com": "Wolfpack", "jcapitalresearch.com": "J Capital",
         "scorpioncapital.com": "Scorpion", "viceroyresearch.org": "Viceroy",
         "sprucepointcap.com": "Spruce Point", "gothamcityresearch.com": "Gotham City",
         "hindenburgresearch.com": "Hindenburg"}


def txt(x, y, s, *, size, fill, anchor="start", weight="normal", tab=False):
    st = "font-variant-numeric: tabular-nums;" if tab else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family=\'{FONT}\' font-size="{size}" '
            f'fill="{fill}" text-anchor="{anchor}" font-weight="{weight}" '
            f'style="{st}">{escape(s)}</text>')


def para(x, y, s, *, size, fill, chars, leading=17.0):
    words, line, out, n = s.split(), [], [], 0
    for w in words:
        if sum(len(t) + 1 for t in line) + len(w) > chars and line:
            out.append(txt(x, y + n * leading, " ".join(line), size=size, fill=fill))
            line, n = [], n + 1
        line.append(w)
    if line:
        out.append(txt(x, y + n * leading, " ".join(line), size=size, fill=fill))
        n += 1
    return out, n * leading


def klass(access):
    if "full text" in access:
        return "full text"
    if "PDF" in access:
        return "PDF"
    return "teaser"


def rows():
    audit = {r["domain"]: r for r in json.loads(AUDIT.read_text())}
    out, blocked = [], []
    for dom, r in audit.items():
        name = SHORT.get(dom, dom)
        if r["urls"] == 0:
            blocked.append((name, r["sitemap"]))
            continue
        if dom in MEASURED:
            key, cls = MEASURED[dom]
            docs, _ = ctrllib.load(key, with_pdf=True)
            docs = [d for d in docs if d["words"] >= ctrllib.MIN_WORDS]
            out.append(dict(name=name, urls=r["urls"], words=statistics.median(d["words"] for d in docs),
                            cls=cls, measured=True, n=len(docs), partial=False))
        elif dom in PARTIAL:
            key, cls = PARTIAL[dom]
            d = ctrllib.RAW / key
            # Shared boilerplate is subtracted here exactly as ctrllib.load does it.
            # Skipping that step put Spruce Point on this chart at 10,136 words of
            # "full text" when 9,525 of them are the same legal block on every page
            # and the real content is 618 — the third time in this recipe that an
            # unsubtracted template turned a teaser into an archive.
            texts = [ctrllib.strip_html(p.read_text("utf-8", "replace")).split()
                     for p in sorted(d.glob("*.html"))]
            if len(texts) < 2:
                continue
            pre, suf = ctrllib.shared_boilerplate(texts)
            ws = [max(0, len(x) - pre - suf) for x in texts]
            ws = [w for w in ws if w >= ctrllib.MIN_WORDS]
            if not ws:
                continue
            out.append(dict(name=name, urls=r["urls"], words=statistics.median(ws),
                            cls=cls, measured=True, n=len(ws), partial=True))
        elif dom == "hindenburgresearch.com":
            hb = corpuslib.load("initial")
            out.append(dict(name=name, urls=r["urls"],
                            words=statistics.median(len(corpuslib.body(p).split()) for p in hb),
                            cls="full text", measured=True, n=len(hb), partial=False))
        else:
            out.append(dict(name=name, urls=r["urls"], words=r["median_words"],
                            cls=klass(r["access"]), measured=False, n=None, partial=False))
    return out, blocked


def main():
    data, blocked = rows()
    assert palette.check([FULL, PDF, TEASER], label="access palette")

    W, H = 980.0, 730.0
    L, R, T, B = 92.0, 262.0, 242.0, 172.0
    XMAX = 400.0
    YMAX = max(14000.0, max(d["words"] for d in data) * 1.1)
    def X(v): return L + min(v, XMAX) / XMAX * (W - L - R)
    def Y(v): return (H - B) - min(v, YMAX) / YMAX * (H - B - T)

    el = [f'<rect width="{W}" height="{H}" fill="{SURFACE}"/>']
    el.append(txt(24, 34, "Only part of this field can be studied", size=19, fill=INK, weight="600"))
    lead, dy = para(24, 58, "Every activist short-research firm probed. Horizontal: how many pages "
                    "its sitemap lists. Vertical: how many words a reader can extract from one "
                    "report. Filled marks were measured from a captured archive; open marks are "
                    "a four-page sample.", size=12.5, fill=INK2, chars=118)
    el += lead
    y0 = 58 + dy + 22
    el.append(txt(24, y0, f"{len(blocked)} of {len(data)+len(blocked)} firms are not on this plot at "
                 "all — they refuse the connection.", size=13, fill=INK, weight="600"))
    el.append(txt(24, y0 + 20, "Of those that answer, the ones you can actually read are a corner of "
                 "it. That corner is what every finding here rests on.", size=13, fill=INK2))

    for v in range(0, int(XMAX) + 1, 100):
        el.append(f'<line x1="{X(v):.1f}" y1="{T}" x2="{X(v):.1f}" y2="{Y(0):.1f}" stroke="{GRID}" stroke-width="1"/>')
        el.append(txt(X(v), Y(0) + 20, str(v), size=11, fill=MUTED, anchor="middle", tab=True))
    for v in range(0, int(YMAX) + 1, 2000):
        el.append(f'<line x1="{L}" y1="{Y(v):.1f}" x2="{W-R}" y2="{Y(v):.1f}" stroke="{GRID}" stroke-width="1"/>')
        el.append(txt(L - 10, Y(v) + 4, f"{v//1000}k" if v else "0", size=11, fill=MUTED, anchor="end", tab=True))
    el.append(f'<line x1="{L}" y1="{Y(0):.1f}" x2="{W-R}" y2="{Y(0):.1f}" stroke="{BASELINE}" stroke-width="1.5"/>')
    el.append(txt(L, Y(0) + 44, "pages listed in the sitemap", size=12, fill=INK2))
    el.append(f'<text x="{-(T + (H-B-T)/2):.1f}" y="26" transform="rotate(-90)" '
              f'font-family=\'{FONT}\' font-size="12" fill="{INK2}" text-anchor="middle">'
              "words extractable per report</text>")

    # A readable-corpus threshold, stated rather than implied.
    el.append(f'<line x1="{L}" y1="{Y(1500):.1f}" x2="{W-R}" y2="{Y(1500):.1f}" '
              f'stroke="{MUTED}" stroke-width="1.2" stroke-dasharray="4 4"/>')
    # The threshold is named at the axis, not written across the plot: the firms
    # it separates sit exactly where that sentence would have to run.
    el.append(txt(L - 10, Y(1500) + 4, "1.5k", size=10.5, fill=MUTED, anchor="end", tab=True))
    el.append(txt(L - 10, Y(1500) - 8, "readable", size=9.5, fill=MUTED, anchor="end"))

    placed = []
    for d in sorted(data, key=lambda r: -r["words"]):
        x, y = X(d["urls"]), Y(d["words"])
        c = CLASS_COL[d["cls"]]
        if d["measured"]:
            el.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="7.5" fill="{c}" fill-opacity="0.55" '
                      f'stroke="{c}" stroke-width="2"/>')
        else:
            el.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="6" fill="{SURFACE}" '
                      f'stroke="{c}" stroke-width="2" stroke-dasharray="3 2"/>')
        # Nudge a label down when it would land on one already placed.
        # Marks near the baseline get their label ABOVE them: below, the labels
        # land on the axis ticks and on the axis title.
        low = y > Y(0) - 60
        right = x > X(XMAX) - 170        # else the label runs into the legend
        ly = (y - 14) if low else (y + 4)
        step = -13 if low else 13
        while any(abs(ly - p) < 13 and abs(x - px) < 140 for px, p in placed):
            ly += step
        placed.append((x, ly))
        suffix = (f"  n={d['n']}" + ("*" if d.get("partial") else "")) if d["measured"] else ""
        if low:
            ax, anc = x, "middle"
        elif right:
            ax, anc = x - 13, "end"
        else:
            ax, anc = x + 13, "start"
        el.append(txt(ax, ly, f"{d['name']}{suffix}", size=11.5,
                      fill=INK if d["measured"] else MUTED, anchor=anc,
                      weight="600" if d["measured"] else "normal", tab=True))

    lx = W - R + 16
    el.append(txt(lx, T + 2, "what you can read", size=12, fill=INK, weight="600"))
    yy = T + 28
    for cls, lab in (("full text", "full text in HTML"), ("PDF", "a teaser, plus a PDF"),
                     ("teaser", "a teaser, and nothing")):
        el.append(f'<circle cx="{lx+7:.1f}" cy="{yy-4:.1f}" r="6.5" fill="{CLASS_COL[cls]}" '
                  f'fill-opacity="0.55" stroke="{CLASS_COL[cls]}" stroke-width="2"/>')
        el.append(txt(lx + 22, yy, lab, size=11.5, fill=INK2))
        yy += 24
    yy += 10
    el.append(f'<circle cx="{lx+7:.1f}" cy="{yy-4:.1f}" r="7.5" fill="{MUTED}" fill-opacity="0.55" stroke="{MUTED}" stroke-width="2"/>')
    el.append(txt(lx + 22, yy, "archive captured here", size=11.5, fill=INK2))
    yy += 22
    el.append(f'<circle cx="{lx+7:.1f}" cy="{yy-4:.1f}" r="6" fill="{SURFACE}" stroke="{MUTED}" stroke-width="2" stroke-dasharray="3 2"/>')
    el.append(txt(lx + 22, yy, "four-page sample", size=11.5, fill=MUTED))
    yy += 20
    el.append(txt(lx, yy, "* capture cut short — n is what", size=10.5, fill=MUTED))
    el.append(txt(lx, yy + 13, "  was read, not what exists", size=10.5, fill=MUTED))

    yy += 34
    el.append(txt(lx, yy, "not on the plot", size=12, fill=INK, weight="600"))
    yy += 20
    for name, code in blocked:
        el.append(txt(lx, yy, f"{name} — HTTP {code}", size=11, fill=MUTED, tab=True))
        yy += 16

    cap, _ = para(24, H - 74, "A firm counts as readable when a report yields 1,500 words or more. "
                  "Sitemap page counts include index and tag pages, so they are an upper bound on "
                  "reports, not a count of them. For PDF firms the height is the PDF, which is "
                  "the report; their HTML pages hold a few hundred words. The sampled marks are "
                  "weak — the same sampler read Muddy Waters' teaser pages as 1,940 words of "
                  "report by landing on a mixed tier of URLs, which is why a measured corpus "
                  "overrides a sample wherever one exists.",
                  size=11, fill=MUTED, chars=150, leading=15)
    el += cap
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {H:.0f}" '
                   f'width="{W:.0f}" height="{H:.0f}">' + "".join(el) + "</svg>")
    print(f"  charts/who-can-be-studied.svg — {len(data)} plotted, {len(blocked)} refuse connection")
    for d in sorted(data, key=lambda r: -r["words"]):
        print(f"    {d['name']:<14}{d['urls']:>5} pages  {d['words']:>7,.0f}w  {d['cls']:<10}"
              f"{'measured n=' + str(d['n']) if d['measured'] else 'sampled'}")


if __name__ == "__main__":
    main()
