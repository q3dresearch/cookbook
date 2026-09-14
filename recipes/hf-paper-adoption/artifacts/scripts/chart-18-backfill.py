#!/usr/bin/env python3
"""What capture bought, and what a backfill could still recover.

The registry marked this feed `destroys_own_history: true`, and that was taken to mean
the whole record was perishable. It is half right, and the half matters.

**Membership is recoverable.** `?date=YYYY-MM-DD` serves the daily list back to
2023-05-04, so one backfill run recovered **865 days and 17,534 papers** -- everything
to the left of the capture window in this chart exists only because of that call.
Believing the registry note covered membership too is what made this recipe look like
it needed until 2029.

**Upvote trajectories are not.** The feed returns today's count, not the count as it
stood. A paper's *position* in the list is recoverable; how attention accrued to it is
gone the moment it rolls off. That is the one genuinely irreplaceable series here, and
it is why Q14 -- does attention predict uptake, or only accompany it -- cannot be
answered by any amount of backfilling and needs forward capture instead.

**So the distinction that matters is not old-versus-new, it is membership-versus-
trajectory.** Enrichment sources archive themselves: arXiv keeps its LaTeX, OpenAlex
keeps its references, GitHub keeps its repository dates, and all three can be re-fetched
whenever. A count that a provider overwrites in place cannot.

The line is papers per month across the whole recovered feed. The shaded region is
what weekly capture has held since it started -- a small fraction of the record, and
the only part where anything beyond membership was preserved.
"""
import sys, collections, glob, datetime as dt
sys.path.insert(0, ".")
import paperlib as P


def main():
    f = P.feed(one_extractor=False)
    mon = collections.Counter(p["publishedAt"][:7] for p in f.values())
    caps = sorted(glob.glob(str(P.ARCHIVE/"raw"/"hf.papers.daily"/"*"/"*"/"*")))
    first_cap = caps[0].split("/")[-1][:8] if caps else "20260831"
    fc = f"{first_cap[:4]}-{first_cap[4:6]}"
    # Drop the current month: it is partial and its dive reads as a collapse.
    import datetime as _dt
    this_month = _dt.date.today().strftime("%Y-%m")
    ms = sorted(m for m in mon if "2023-05" <= m < this_month)

    W, L, R, T, B = 940, 88, 82, 190, 160
    PH = 280
    H = T + PH + B
    pw = W - L - R
    mx = max(mon[m] for m in ms)*1.12
    sx = lambda i: L + i/(len(ms)-1)*pw
    sy = lambda v: T + PH - v/mx*PH
    body = []
    ci = next((i for i, m in enumerate(ms) if m >= fc), len(ms)-1)
    body.append(f'<rect x="{sx(ci):.1f}" y="{T}" width="{L+pw-sx(ci):.1f}" height="{PH}" '
                f'fill="{P.COOL}" fill-opacity="0.10"/>')
    for g in (0, 200, 400, 600, 800):
        if g > mx: continue
        body.append(f'<line x1="{L}" y1="{sy(g):.1f}" x2="{L+pw:.1f}" y2="{sy(g):.1f}" '
                    f'stroke="{P.INK if g == 0 else P.GRID}" stroke-width="{1.3 if g == 0 else 1}"/>')
        body.append(P.txt(L-10, sy(g)+4, g, size=11, fill=P.MUTED, anchor="end", tab=True))
    d = " ".join(("M" if i == 0 else "L") + f"{sx(i):.1f} {sy(mon[m]):.1f}" for i, m in enumerate(ms))
    body.append(f'<path d="{d}" fill="none" stroke="{P.HOT}" stroke-width="2.4"/>')
    for i, m in enumerate(ms):
        if m.endswith("-01") or i == 0:
            body.append(P.txt(sx(i), T+PH+20, m, size=10, fill=P.MUTED, anchor="middle"))
    body.append(P.txt(L-10, T-44, "papers on the daily feed, per month", size=12, fill=P.INK2))
    body.append(P.txt(L-10, T-26, f"{len(f):,} in total, across {len(ms)} months", size=11, fill=P.MUTED))
    # Both annotations live on the left: the capture window is two months of 41 and a
    # label sitting over it runs straight off the right edge.
    body.append(P.txt(sx(1), T+18, "RECOVERED BY BACKFILL", size=11.5, fill=P.HOT, weight="600"))
    body.append(P.txt(sx(1), T+33, "membership only — the feed serves today's upvotes,", size=10.5, fill=P.MUTED))
    body.append(P.txt(sx(1), T+46, "so trajectories are gone the moment a paper rolls off", size=10.5, fill=P.MUTED))
    body.append(P.txt(sx(1), T+74, "HELD BY WEEKLY CAPTURE", size=11.5, fill=P.COOL, weight="600"))
    body.append(P.txt(sx(1), T+89, f"the shaded band — {len(ms)-ci} of {len(ms)} months, and the only window",
                      size=10.5, fill=P.MUTED))
    body.append(P.txt(sx(1), T+102, "where anything beyond membership survives", size=10.5, fill=P.MUTED))
    body.append(f'<line x1="{sx(1):.1f}" y1="{T+78:.1f}" x2="{sx(ci)-4:.1f}" y2="{T+78:.1f}" '
                f'stroke="{P.COOL}" stroke-width="1" stroke-dasharray="3 3" stroke-opacity="0.5"/>')
    body.append(f'<line x1="{sx(ci):.1f}" y1="{T}" x2="{sx(ci):.1f}" y2="{T+PH:.1f}" '
                f'stroke="{P.INK}" stroke-width="1.4" stroke-dasharray="5 3"/>')

    foot = [f"{len(f):,} papers recovered from 865 days of ?date=YYYY-MM-DD. The registry's "
            f"'destroys_own_history' is right about trajectories and wrong about membership.",
            "Believing it covered both is what made this recipe look like it needed until 2029.",
            "What a backfill cannot return is a count as it STOOD: the feed serves today's upvotes. That is why "
            "Q14 needs forward capture and cannot be fixed by fetching harder.",
            "Enrichment archives itself — arXiv keeps its LaTeX, OpenAlex its references, GitHub its repo dates. "
            "A number a provider overwrites in place does not."]
    print(P.write("18-backfill.svg", P.frame(
        W, H, "Membership was recoverable; the trajectories were not",
        "Papers per month across the whole daily-papers feed, with the part that weekly capture has actually held "
        "marked.", body, foot, chars=124)))


main()
