#!/usr/bin/env python3
"""A number computed from one capture of this listing should not be quoted.

The top-1,000-by-download listing is not a fixed population. It churns, and the filter
chain in `adoption.py` ends at a threshold -- a paper must reach two independent
organisations -- so a paper sitting at exactly two loses one the moment a single model
drops out of the ranking.

**Drawn as a presence matrix**, one row per paper that ever clears the bar and one
column per capture, because the summary statistic hides which kind of instability it
is. A solid row is a paper that qualifies in every capture. A gappy row is one that
flickers, and every flickering paper sits at exactly two organisations.

The stable core is the number worth quoting. The fragile band is not a defect to be
cleaned up -- it is the honest edge of a threshold applied to a churning population,
and the only wrong move is to report a single capture's total as if it were the answer.

**The churn is mechanical, not subtle.** A sixth of the model ids in this listing are
absent from at least one of the captures. Nothing about the papers changed.
"""
import sys, collections, glob
sys.path.insert(0, ".")
import paperlib as P
from adoption import ALIASES


def main():
    files = sorted(glob.glob(str(P.ARCHIVE/"raw"/"hf.models.top-downloads"/"*"/"*"/"*")))
    caps, ids_seen = [], collections.Counter()
    for fp in files:
        import json, gzip
        op = gzip.open if fp.endswith(".gz") else open
        ms = json.load(op(fp, "rt"))
        indep = collections.defaultdict(set)
        for m in ms:
            ids_seen[m["id"]] += 1
            if P.foreign_base(m): continue
            o = ALIASES.get(m["id"].split("/")[0], m["id"].split("/")[0])
            for a in P.arxiv_ids(m): indep[a].add(o)
        day = fp.split("/")[-1][:8]
        caps.append((f"{day[:4]}-{day[4:6]}-{day[6:8]}",
                     {a for a, s in indep.items() if len(s) >= 2}))
    ever = collections.Counter()
    for _, s in caps:
        for a in s: ever[a] += 1
    rows = sorted(ever.items(), key=lambda kv: (-kv[1], kv[0]))
    core = sum(1 for _, n in rows if n == len(caps))
    churn = sum(1 for i, n in ids_seen.items() if n < len(caps))/len(ids_seen)*100

    from json import loads
    titles = {}
    tp = P.ARCHIVE/"examples"/"paper-titles.json"
    if tp.exists():
        raw = loads(tp.read_text())
        titles = {k: (v.get("title") if isinstance(v, dict) else v) for k, v in raw.items()}

    RH, CW, W, L, T = 19, 46, 1080, 300, 200
    H = T + RH*len(rows) + 132
    body = []
    for j, (d, _) in enumerate(caps):
        x = L + CW*(j + 0.5)
        body.append(P.txt(x, T-26, d[5:], size=10, fill=P.MUTED, anchor="middle", tab=True))
    body.append(P.txt(L, T-48, f"{len(caps)} weekly captures of the same listing", size=12, fill=P.INK2))
    body.append(P.txt(L-16, T-26, "papers clearing two independent orgs", size=11, fill=P.INK2, anchor="end"))

    for i, (a, n) in enumerate(rows):
        y = T + RH*i + RH/2
        full = n == len(caps)
        col = P.COOL if full else P.HOT
        t = (titles.get(a) or a).split(":")[0][:30]
        body.append(P.txt(L-16, y+4, t, size=10.5, fill=P.INK if full else P.INK2, anchor="end"))
        body.append(P.txt(L-16, y-6, "", size=1, fill=P.MUTED))
        for j, (_, s) in enumerate(caps):
            x = L + CW*(j + 0.5)
            if a in s:
                body.append(f'<rect x="{x-9:.1f}" y="{y-6:.1f}" width="18" height="12" rx="2.5" '
                            f'fill="{col}" fill-opacity="0.85"/>')
            else:
                body.append(f'<rect x="{x-9:.1f}" y="{y-6:.1f}" width="18" height="12" rx="2.5" '
                            f'fill="none" stroke="{P.BASELINE}" stroke-width="1"/>')
        body.append(P.txt(L + CW*len(caps) + 16, y+4, f"{n}/{len(caps)}", size=10.5,
                          fill=col, anchor="start", tab=True, weight="600" if not full else "normal"))

    ysep = T + RH*core
    RX = L + CW*len(caps) + 66
    body.append(f'<line x1="{L-280:.1f}" y1="{ysep:.1f}" x2="{RX+150:.1f}" y2="{ysep:.1f}" '
                f'stroke="{P.INK}" stroke-width="1.4" stroke-dasharray="5 3"/>')
    # Annotations to the RIGHT of the matrix: at the left they ran straight through
    # the paper titles, which are right-aligned into the same space.
    body.append(P.txt(RX, ysep-24, "THE STABLE CORE", size=11, fill=P.COOL, weight="600"))
    body.append(P.txt(RX, ysep-11, f"{core} papers, every capture", size=10, fill=P.COOL))
    body.append(P.txt(RX, ysep+18, "THE FRAGILE BAND", size=11, fill=P.HOT, weight="600"))
    body.append(P.txt(RX, ysep+31, f"{len(rows)-core} more qualify sometimes;", size=10, fill=P.HOT))
    body.append(P.txt(RX, ysep+43, "each sits at exactly two orgs", size=10, fill=P.HOT))

    tot = [len(s) for _, s in caps]
    foot = [f"The same filter chain run on each capture gives {min(tot)} to {max(tot)} papers. {core} clear it "
            f"every time, so stability is {core*100//len(rows)}% — {core} of the {len(rows)} that ever qualify.",
            f"The cause is churn in the listing, not in the papers: {churn:.0f}% of model ids are absent from at "
            f"least one capture.",
            "A paper sitting at exactly two orgs drops out the moment one of its models leaves the ranking.",
            "The fragile band is not noise to be cleaned up. It is the honest edge of a threshold applied to a "
            "population that turns over weekly.",
            "Quote the core. A single capture's total is a number that will be different next week."]
    print(P.write("16-capture-churn.svg", P.frame(
        W, H, "The same measurement, eleven times, on a listing that turns over",
        "Every paper that ever clears two independent organisations, and whether it cleared it in each weekly "
        "capture.", body, foot, chars=124)))


main()
