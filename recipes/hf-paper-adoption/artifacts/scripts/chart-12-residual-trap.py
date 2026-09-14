#!/usr/bin/env python3
"""The undervalued-paper detector that looks right and is not. Kept as a warning.

The obvious way to find an underrated paper: regress uptake on attention and read the
residuals. Papers far above the line got more use than their popularity explains.
It fits -- r = 0.47 on logs across 9,868 papers -- and the residuals are large and
interpretable-looking. **Every one of the top ones is an artifact.**

**A star count belongs to a repository, not to a paper.** When an established project
posts a technical report, the report inherits the project's entire accumulated star
history:

- *PaddleOCR-VL-1.6* links `PaddlePaddle/PaddleOCR` -- 89,437 stars, a repo years older
  than the paper.
- *Ultralytics YOLO26* links `ultralytics/ultralytics` -- 61,552.
- *VideoGLUE* shows 5 upvotes against 77,659 stars.

**The other tail is as bad.** *Mixtral of Experts* reads 162 upvotes and 2 stars,
*GrandCode* 641 and 4, because the linked repo is a stub. So the detector's two ends
are "old project posts a report" and "bad repo link", and neither is a judgement about
the idea.

**The tempting fix does not work.** The first guess was that several papers share one
repo and the count is double-attributed. It is not: **10,076 papers hold 10,076
distinct repos**, one each. The attribution is one-to-one and still wrong, because the
problem is the repo's *age*, not its reuse.

**Fetched for the labelled points, which settles it.** `tensorflow/models` was created
in **2016** and carries VideoGLUE's 77,659 stars; PaddleOCR's repo is from 2020 and is
credited to a 2026 paper. Against that, the two legitimate cases are unmistakable:
`state-spaces/mamba` and its paper are the same month, `openai/shap-e` one month apart.
And Mixtral's linked repo, `pwc-1/Paper-9`, was created **six months after** the paper —
it is a scrape artifact, not the authors' repository, which is what the low tail really
is.

**What would fix it at scale is `created_at` for every repo** -- stars accrued since the
paper appeared rather than since the repo did. That is enrichment, not capture: GitHub
serves repo creation dates permanently, so no window is closing and it can be added
whenever. Until then, no residual-based ranking from this field should be published.

**Drawn rather than deleted** because it is symmetric, well-fitted and persuasive.
A merely bad chart is clutter; a convincing wrong one earns its place -- and now it
carries the dates that convict it.
"""
import sys, math, statistics
sys.path.insert(0, ".")
import paperlib as P

# Repository creation dates, fetched from the GitHub API on 2026-09-14 for the
# labelled points only (60 requests/hour unauthenticated makes the full 10,076
# infeasible without a token). Hand-recorded here the way chart 5 records ids.
#
# The rule this establishes: compare repo creation to paper date. A repo made for
# the paper is 0-1 months older. Everything in the high tail is years older, and the
# one in the low tail is NEWER than its paper, which means it is not the authors'
# repo at all.
REPO_AGE = {
    "2307.03166": ("tensorflow/models", "2016-02", "2023-07"),
    "2510.13913": ("facebookresearch/sam2", "2024-07", "2025-10"),
    "2311.04931": ("nomic-ai/gpt4all", "2023-03", "2023-11"),
    "2606.03264": ("PaddlePaddle/PaddleOCR", "2020-05", "2026-06"),
    "2606.03748": ("ultralytics/ultralytics", "2022-09", "2026-06"),
    "2309.06180": ("vllm-project/vllm", "2023-02", "2023-09"),
    "2305.02463": ("openai/shap-e", "2023-04", "2023-05"),
    "2401.04088": ("pwc-1/Paper-9", "2024-07", "2024-01"),
    "2502.06394": ("s-nlp/synthdetoxm", "2025-02", "2025-02"),
}


def _months(a, b):
    return (int(b[:4])-int(a[:4]))*12 + int(b[5:7])-int(a[5:7])


NOTE = {
    "2606.03264": "PaddleOCR monorepo,\nyears older than the paper",
    "2606.03748": "ultralytics/ultralytics",
    "2307.03166": "VideoGLUE",
    "2311.04931": "GPT4All",
    "2309.06180": "vLLM",
    "2401.04088": "Mixtral — stub repo link",
    "2604.02721": "GrandCode",
    "2409.12186": "Qwen2.5-Coder",
}

def main():
    f = P.feed()
    pts = [(k, v, v["upvotes"], v["githubStars"]) for k, v in f.items()
           if v.get("githubStars") and v["upvotes"] > 0]
    xs = [math.log10(u) for _, _, u, _ in pts]
    ys = [math.log10(s) for _, _, _, s in pts]
    mx_, my_ = statistics.mean(xs), statistics.mean(ys)
    b = sum((x-mx_)*(y-my_) for x, y in zip(xs, ys))/sum((x-mx_)**2 for x in xs)
    a = my_ - b*mx_
    r = statistics.correlation(xs, ys)
    res = sorted(((y-(a+b*x), k, v, x, y) for (k, v, _, _), x, y in zip(pts, xs, ys)), reverse=True)

    W, H, L, R, T, B = 900, 600, 84, 250, 140, 134
    pw, ph = W-L-R, H-T-B
    sx = lambda v: L + v/3.1*pw
    sy = lambda v: T + ph - v/5.2*ph
    body = []
    for g in range(0, 4):
        body.append(f'<line x1="{sx(g):.1f}" y1="{T}" x2="{sx(g):.1f}" y2="{T+ph:.1f}" '
                    f'stroke="{P.GRID}" stroke-width="1"/>')
        body.append(P.txt(sx(g), T+ph+20, f"{10**g:,}", size=11, fill=P.MUTED, anchor="middle", tab=True))
    for g in range(0, 6):
        body.append(f'<line x1="{L}" y1="{sy(g):.1f}" x2="{L+pw:.1f}" y2="{sy(g):.1f}" '
                    f'stroke="{P.GRID}" stroke-width="1"/>')
        body.append(P.txt(L-10, sy(g)+4, f"{10**g:,}", size=11, fill=P.MUTED, anchor="end", tab=True))
    body.append(P.txt(L+pw/2, T+ph+44, "upvotes   (log)", size=12, fill=P.INK2, anchor="middle"))
    body.append(P.txt(L-10, T-24, "GitHub stars   (log)", size=12, fill=P.INK2))

    for _, _, x, y in ((0, 0, x, y) for x, y in zip(xs, ys)):
        body.append(f'<circle cx="{sx(x):.2f}" cy="{sy(y):.2f}" r="1.5" fill="{P.MUTED}" fill-opacity="0.16"/>')
    body.append(f'<line x1="{sx(0):.1f}" y1="{sy(a):.1f}" x2="{sx(3.1):.1f}" y2="{sy(a+b*3.1):.1f}" '
                f'stroke="{P.INK}" stroke-width="1.8" stroke-dasharray="6 4"/>')
    body.append(P.txt(sx(0.12), sy(a+b*0.12)-12, f"fit: r = {r:.2f}", size=11, fill=P.INK2))

    # One list per side. A shared list made GrandCode, which sits near the right
    # column in x, dodge against labels it never touches and climb out of the plot.
    placed = {1: [], -1: []}
    for sign, group in ((1, res[:5]), (-1, res[-3:])):
        for d, k, v, x, y in group:
            col = P.HOT if sign > 0 else P.COOL
            body.append(f'<circle cx="{sx(x):.1f}" cy="{sy(y):.1f}" r="5" fill="{col}" '
                        f'fill-opacity="0.85" stroke="{P.SURFACE}" stroke-width="1.4"/>')
            label = NOTE.get(k, (v["title"].replace("\n", " ")[:22]))
            # Low-side labels dodge UPWARD: placed below, they ran into the axis.
            # Three lines per label now that repo ages are shown, so spacing is 40.
            # The collision test must include x: a y-only test made the low-side
            # labels dodge against the right-hand column they never overlap, and they
            # climbed out of the plot and into the title.
            ly = sy(y) if sign > 0 else sy(y) - 46
            step = 40 if sign > 0 else -40
            # A low-side point in the right third gets its label to the LEFT, or it
            # runs into the right-hand column.
            rightish = sign < 0 and sx(x) > L + pw*0.62
            anc = 'end' if rightish else 'start'
            tx0 = L+pw+14 if sign > 0 else (sx(x)-12 if rightish else sx(x)+12)
            for _ in range(12):
                if not any(abs(tx0-px) < 150 and abs(ly-u) < 40 for px, u in placed[sign]):
                    break
                ly += step
            placed[sign].append((tx0, ly))
            tx = tx0
            body.append(f'<line x1="{sx(x):.1f}" y1="{sy(y):.1f}" x2="{tx-4:.1f}" y2="{ly:.1f}" '
                        f'stroke="{col}" stroke-width="0.9" stroke-opacity="0.5"/>')
            body.append(P.txt(tx, ly+4, label.split("\n")[0], size=10.5, fill=col, weight="600", anchor=anc))
            body.append(P.txt(tx, ly+16, f'{v["upvotes"]} up · {v["githubStars"]:,} stars',
                              size=10, fill=P.MUTED, anchor=anc))
            if k in REPO_AGE:
                repo, made, paper = REPO_AGE[k]
                m = _months(made, paper)
                age = (f"repo {abs(m)//12}y{abs(m)%12}mo older than the paper" if m >= 12 else
                       f"repo {m}mo older" if m > 1 else
                       "repo made FOR the paper" if 0 <= m <= 1 else
                       f"repo {-m}mo NEWER — not theirs")
                body.append(P.txt(tx, ly+27, age, size=9.5, anchor=anc,
                                  fill=P.INK2 if 0 <= m <= 1 else col))

    foot = [f"Fits well — r = {r:.2f} on {len(pts):,} papers — and both tails are measurement artifacts, not "
            f"undervalued or overvalued ideas.",
            "High side: an established project posts a technical report and the report inherits the repo's whole "
            "star history. Low side: the linked repo is a stub.",
            "Not double-attribution — 10,076 papers hold 10,076 distinct repos, one each. The problem is the "
            "repo's age, not its reuse.",
            "Repo dates fetched 2026-09-14 for the labelled points. Legitimate ones are made FOR the paper; the "
            "rest are years older, and Mixtral's is newer than its paper.",
            "At scale this needs created_at for all 10,076 repos — 60 requests/hour unauthenticated, so it needs "
            "a token."]
    print(P.write("12-residual-trap.svg", P.frame(
        W, H, "A convincing way to find undervalued papers, and why it fails",
        "GitHub stars against upvotes for every feed paper carrying both. The labelled points are the largest "
        "residuals in each direction.", body, foot, chars=120)))

main()
