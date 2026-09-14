#!/usr/bin/env python3
"""Three axes, no annotation: crowding, payoff, and how often the pipeline runs backwards.

Payoff is counted per PUBLISHER, not per model. A publisher citing a paper counts once
however many variants it ships -- Qwen's 114 models are one opinion, not 114. Counting
models instead inflates every rate by 2.1x and reorders the middle of this ranking.

Even corrected, read it as a direction. It rests on 146 citing publishers in total.

**Dot size is the share of adoptions where the MODEL was created before the paper it
cites** -- a genuinely third quantity, not a redraw of the axes. A hollow ring marks
fields resting on fewer than 20 adoptions.

**It used to be the median wait, and that was wrong.** The median lag over all pairs
mixes two populations: papers that precede their models and papers that document a
model already shipped. The negatives drag the median down, so the statistic read 7
months for embeddings and 18 for vision and looked like a field speed difference.
Restricted to the pairs where the paper genuinely came first, every field lands at
20-25 months -- a five-month spread with overlapping quartiles. The wait does not
differ by field; what differs is how often the paper is documentation. See
`10-shipfirst`, which retracts the same claim.

An earlier version sized dots by paper count, which is the x-axis, and then printed
"2,869 papers, 18 adoptions" beside every mark; adoptions are just x times y over a
thousand, so that text was the two axes multiplied and read back out.
"""
import sys, collections, math, statistics
sys.path.insert(0, ".")
import paperlib as P

def main():
    f = P.feed(); ms = P.models()
    lag = collections.defaultdict(list)
    for m in ms:
        c = m.get("createdAt"); fl = P.FIELD_TAG.get(m.get("pipeline_tag"))
        if not c or not fl: continue
        cm = int(c[:4])*12 + int(c[5:7])
        for a in P.arxiv_ids(m):
            pm = P.pub_month(a)
            if pm and -24 <= cm-pm <= 180: lag[fl].append(cm-pm)
    supply = collections.Counter()
    for pa in f.values():
        for fl in P.paper_field(pa): supply[fl] += 1
    pub = collections.defaultdict(set)
    for m in ms:
        fl = P.FIELD_TAG.get(m.get("pipeline_tag"))
        if not fl: continue
        o = m["id"].split("/")[0]
        for a in P.arxiv_ids(m): pub[fl].add((o, a))
    pts = [(supply[k], len(pub.get(k, ()))/supply[k]*1000, len(pub.get(k, ())), k)
           for k in supply if supply[k] >= 80]
    W, H, L, R, T, B = 860, 516, 78, 60, 150, 156
    pw, ph = W-L-R, H-T-B
    xs = [math.log10(p[0]) for p in pts]; ys = [p[1] for p in pts]
    x0, x1 = min(xs)-.3, max(xs)+.2
    ly0, ly1 = math.log10(min(ys)*.5), math.log10(max(ys)*2.1)
    sx = lambda v: L + (math.log10(v)-x0)/(x1-x0)*pw
    sy = lambda v: T + ph - (math.log10(v)-ly0)/(ly1-ly0)*ph
    body = []
    for g in (3, 10, 30, 100):
        if 10**ly0 <= g <= 10**ly1:
            y = sy(g)
            body.append(f'<line x1="{L}" y1="{y:.1f}" x2="{L+pw:.1f}" y2="{y:.1f}" stroke="{P.GRID}" stroke-width="1"/>')
            body.append(P.txt(L-10, y+4, g, size=11, fill=P.MUTED, anchor="end", tab=True))
    for v in (100, 300, 1000, 3000, 10000):
        if 10**x0 <= v <= 10**x1:
            x = sx(v)
            body.append(f'<line x1="{x:.1f}" y1="{T}" x2="{x:.1f}" y2="{T+ph:.1f}" stroke="{P.GRID}" stroke-width="1"/>')
            body.append(P.txt(x, T+ph+20, f"{v:,}", size=11, fill=P.MUTED, anchor="middle", tab=True))
    body.append(P.txt(L+pw/2, T+ph+42, "papers competing in the field   (log)", size=12, fill=P.INK2, anchor="middle"))
    body.append(P.txt(L-10, T-16, "publisher adoptions per 1,000 papers   (log)", size=12, fill=P.INK2))
    body.append(P.txt(L+pw, T-16, "dot size = share of adoptions where the model came first", size=11, fill=P.MUTED, anchor="end"))
    body.append(P.txt(L+pw, T-2, "hollow = under 20 adoptions", size=11, fill=P.MUTED, anchor="end"))
    # Share of pairs running backwards. NOT the median lag: that mixes the two
    # populations and manufactures a field speed difference -- see the docstring.
    inv = {k: sum(1 for x in v if x < 0)/len(v)*100 for k, v in lag.items() if v}
    lmin, lmax = min(inv.values()), max(inv.values())
    rad = lambda k: 6 + 15 * ((inv.get(k, lmin) - lmin) / max(1e-9, lmax - lmin))
    placed, dots = [], []
    for n, r, ev, k in sorted(pts, key=lambda p: -p[1]):
        x, y = sx(n), sy(r)
        col = P.FIELD_COLOR.get(k, P.COOL); rr = rad(k)
        # Size is the inversion rate, which is a third quantity. Sizing by paper count
        # would have redrawn the x-axis, and printing "n papers, m adoptions" beside
        # each dot was the two axes multiplied and read back out as text.
        thin = ev < 20
        body.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{rr:.1f}" '
                    f'fill="{"none" if thin else col}" fill-opacity="0.85" '
                    f'stroke="{col}" stroke-width="{2.5 if thin else 1.5}"/>')
        dots.append((x, y, rr))
    for n, r, ev, k in sorted(pts, key=lambda p: -p[1]):
        x, y = sx(n), sy(r)
        col = P.FIELD_COLOR.get(k, P.COOL); rr = rad(k)
        # Labels dodge other labels AND every dot: vision sits a few pixels from
        # speech and its label was landing inside speech's circle. Dodging upward
        # alone then walked them into the axis titles, so a label that would leave
        # the plot flips below its dot and dodges down instead.
        def free(ty):
            return not (any(abs(x-px) < 150 and abs(ty-py) < 17 for px, py in placed) or
                        any(abs(x-dx) < drr + 78 and abs(ty-dy) < drr + 11 for dx, dy, drr in dots))
        ty = y - rr - 10
        while ty > T + 8 and not free(ty): ty -= 17
        if not free(ty) or ty <= T + 8:
            ty = y + rr + 20
            while ty < T + ph - 8 and not free(ty): ty += 17
        placed.append((x, ty))
        body.append(P.txt(x, ty, f"{k}  {inv.get(k, 0):.0f}% model-first", size=12, fill=col,
                          anchor="middle", weight="600", tab=True))
    best = max(pts, key=lambda p: p[1]); worst = min(pts, key=lambda p: p[1])
    foot = [f"{best[3]} pays {best[1]/worst[1]:.0f}x what {worst[3]} does per paper — down from 62x when models were "
            f"counted instead of publishers.",
            "Up and left is the cheap seat. A BIG dot means much of that field's adoption runs backwards, so "
            "paper-watching works least there.",
            "Dot size used to be the median wait — a statistic that mixes paper-first and model-first pairs and "
            "faked a 2.5x field speed difference.",
            "The real wait is 20-25 months in every field. See 10-shipfirst.",
            "Agents and RL cannot be drawn: no pipeline_tag exists for them, so they land under LLM-core."]
    print(P.write("4-where-to-work.svg", P.frame(W, H, "The one prescription that survives",
        "Fields by competition and payoff, counting each publisher once however many model variants it ships.",
        body, foot, chars=100)))

main()
