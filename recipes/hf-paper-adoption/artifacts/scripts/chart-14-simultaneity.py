#!/usr/bin/env python3
"""New ideas never arrive alone.

The speculation this tests: labs hold their own work and release it reactively once
someone else has made the subject safe, so publication clusters are conformity rather
than discovery.

**The clustering is real and total.** Take every keyword that goes from essentially
absent to 0.3% or more of a quarter's papers -- genuinely new vocabulary, not a term
drifting upward -- and count the papers carrying it in that first quarter, and the
distinct author lists among them. **Nine terms qualify, and in nine of nine every
single paper comes from a different group.** Not one is a group publishing twice.

**But the mechanism splits in two, and only one of them is interesting.**

*Product triggers.* `gpt-4v` arrives with nineteen groups, `deepseek-r1` with
seventeen, `gpt-4o` with eight. A vendor shipped something and everybody pointed an
existing benchmark at it. That is weeks of work, not held-back research, and it says
nothing about hoarding.

*Technique triggers.* `3d gaussian splatting` with nine groups, `large reasoning
models` with ten, `group relative policy optimization` with six. These are the ones
that would support the hypothesis -- and the timing argues against it. GRPO's
originating paper is 2024-02 and the keyword does not cross 0.3% until **2025Q1**,
roughly a year later. That is diffusion, not a coordinated release.

**What this cannot reach.** Every test here runs inside the set of papers that were
published. Work that was never shipped and never written up is invisible by
construction, so the strong form of the claim -- that visible capability is the tip of
an iceberg -- is not falsifiable with this data and is not claimed either way. What is
measurable is that within the published set, the gap between an artifact appearing and
its paper appearing is a median of **two months** (`10-shipfirst`), and that the labs
themselves publish for most of what they ship: deepseek-ai leaves 19% of its models
untagged, meta-llama 20%, against 84% for a redistributor like `unsloth`.
"""
import sys, collections, statistics
sys.path.insert(0, ".")
import paperlib as P

PRODUCT = {"gpt-4v", "gpt-4o", "gpt-5", "deepseek-r1"}


def main():
    f = P.feed()
    kq = collections.defaultdict(list); tot = collections.Counter()
    for p in f.values():
        q = P.quarter(p["publishedAt"]); tot[q] += 1
        for k in set(x.lower() for x in (p.get("ai_keywords") or [])): kq[(q, k)].append(p)
    qs = [q for q in sorted(tot) if tot[q] >= 200]
    allk = collections.Counter()
    for (q, k), v in kq.items():
        if q in qs: allk[k] += len(v)
    rows = []
    for k, _ in allk.most_common(400):
        ser = [(q, len(kq.get((q, k), []))/tot[q]*100) for q in qs]
        first = next((i for i, (q, v) in enumerate(ser) if v >= 0.3), None)
        if first is None or first < 2: continue
        if max((v for _, v in ser[:first]), default=0) > 0.05: continue
        q0 = ser[first][0]; papers = kq.get((q0, k), [])
        if len(papers) < 5: continue
        auth = len({tuple(sorted(a.get("name", "") for a in (p.get("authors") or []))) for p in papers})
        rows.append((len(papers), auth, k, q0))
    rows.sort(reverse=True)

    RH, W, L, R, T = 46, 940, 258, 212, 178
    H = T + RH*len(rows) + 112
    pw = W - L - R
    mx = max(r[0] for r in rows) + 2
    sx = lambda v: L + v/mx*pw
    body = []
    for g in range(0, mx, 5):
        body.append(f'<line x1="{sx(g):.1f}" y1="{T-14:.1f}" x2="{sx(g):.1f}" y2="{T+RH*len(rows)-20:.1f}" '
                    f'stroke="{P.GRID}" stroke-width="1"/>')
        body.append(P.txt(sx(g), T-22, g, size=11, fill=P.MUTED, anchor="middle", tab=True))
    body.append(P.txt(L, T-44, "papers carrying the keyword in its very first quarter", size=12, fill=P.INK2))
    body.append(P.txt(28, T-44, "a vendor shipped", size=10.5, fill=P.HOT, weight="600"))
    body.append(P.txt(28, T-30, "a technique appeared", size=10.5, fill=P.COOL, weight="600"))

    for i, (n, auth, k, q0) in enumerate(rows):
        y = T + RH*i + RH/2 - 20
        col = P.HOT if k in PRODUCT else P.COOL
        body.append(f'<line x1="{L}" y1="{y:.1f}" x2="{sx(n):.1f}" y2="{y:.1f}" '
                    f'stroke="{col}" stroke-width="8" stroke-opacity="0.22" stroke-linecap="round"/>')
        for j in range(n):
            body.append(f'<circle cx="{sx(j+0.5):.1f}" cy="{y:.1f}" r="3.6" fill="{col}" fill-opacity="0.9"/>')
        body.append(P.txt(L-16, y+5, k[:30], size=12, fill=P.INK, anchor="end", weight="600"))
        body.append(P.txt(sx(n)+14, y+5, f"{n} papers", size=11, fill=col, weight="600"))
        body.append(P.txt(sx(n)+14, y+18, f"{auth} distinct groups", size=10,
                          fill=P.INK2 if auth == n else P.HOT))
        body.append(P.txt(L-16, y+18, q0, size=10, fill=P.MUTED, anchor="end"))

    same = sum(1 for n, a, _, _ in rows if a == n)
    foot = [f"One dot is one paper. In {same} of {len(rows)} terms every paper comes from a different author "
            f"group — no group publishes twice in the quarter a term appears.",
            "ORANGE is a vendor shipping and everyone evaluating it — weeks of work, not held research. BLUE is a "
            "technique, the case that would support hoarding.",
            "And the blue cases diffuse slowly. GRPO's originating paper is 2024-02; the keyword does not cross "
            "0.3% until 2025Q1, about a year later.",
            "Every test here sits inside the published set. Work never shipped and never written up is invisible "
            "by construction,",
            "so the strong 'tip of the iceberg' claim is not falsifiable with this data, and is not claimed either "
            "way."]
    print(P.write("14-simultaneity.svg", P.frame(
        W, H, "A new idea has never once arrived from a single group",
        "Every keyword that goes from absent to 0.3% of a quarter, by how many papers carried it in that first "
        "quarter and how many distinct author groups wrote them.", body, foot, chars=124)))


main()
