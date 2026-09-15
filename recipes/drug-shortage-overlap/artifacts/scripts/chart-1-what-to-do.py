#!/usr/bin/env python3
"""One reporting firm means the maker is leaving. Two or more means a real shortage.

This figure used to carry four prescribed actions, three labelled regions, two named
worklists and a legend on one pair of integer axes. It answered several questions and
was crowded and largely verbal doing it -- the marks carried position, the words carried
the argument, which is the wrong way round. It now makes **one** claim, quantitatively.

    firms reporting      n     discontinuances    95% CI (Wilson)
    1                  133       127  (95%)       [0.91, 0.98]
    2                   21         7  (33%)       [0.17, 0.55]
    3                   10         3  (30%)       [0.11, 0.60]
    4 or more           32         0  ( 0%)       [0.00, 0.11]

(On the full register. A first version read one page of the two-page feed and printed
96, 84, 88% here; the numbers on the figure are computed, this table is documentation.)

**It is a threshold, not a gradient.** Nothing decays across the axis; the rate falls
off a cliff between one firm and two and never comes back. Drawing a trend line through
it would assert a dose-response that is not there.

The intervals are the point as much as the rates are. At one firm the estimate rests on
133 substances and is tight; at three it rests on ten and spans half the range. A
reader can see exactly where the evidence is, which a bar chart of four percentages
hides.

**Why it matters.** An earlier version of this figure read the same axis as *does a
downstream fix still exist* and prescribed re-tendering for every single-firm
substance. A company that is exiting cannot be re-tendered back, so that advice was
wrong for 127 of 133. The actions, the four regions and the named worklists moved to the
README, where prose belongs.
"""
import sys, json, collections, math
sys.path.insert(0, ".")
import shortagelib as S
from rxnorm import clean

EXIT, CHRON = "#c07a1e", "#1b4f8a"


def wilson(x, n, z=1.96):
    if not n:
        return 0.0, 0.0
    p, den = x / n, 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return max(0.0, (c - h) / den), min(1.0, (c + h) / den)


def load():
    rx = json.loads((S.DATA / "rxnorm.json").read_text())
    d = S.fda_rows()
    flat = lambda v: [] if v is None else (v if isinstance(v, list) else [v])
    rows = collections.defaultdict(list)
    for r in d:
        e = rx.get(clean(r.get("generic_name") or "")) or {}
        if not S.sub_key(e):
            continue
        for f in flat(r.get("company_name")):
            rows[(S.sub_key(e), str(f))].append(r.get("status"))
    firms, leaving = collections.defaultdict(set), collections.defaultdict(set)
    for (k, f), sts in rows.items():
        firms[k].add(f)
        # a firm leaves a molecule only if EVERY package NDC it lists for it is going
        if all(s == "To Be Discontinued" for s in sts):
            leaving[k].add(f)
    return {k: (len(firms[k]), leaving[k] == firms[k]) for k in firms}


def main():
    P = load()
    # 4+ is pooled: individually those counts hold 5, 5, 4, 1, 2, 1 and 2 substances,
    # and seven intervals spanning most of the range say less than one that does not.
    groups = [("1", lambda c: c == 1), ("2", lambda c: c == 2), ("3", lambda c: c == 3),
              ("4 or more", lambda c: c >= 4)]
    stats = []
    for lab, sel in groups:
        ks = [k for k, (c, _e) in P.items() if sel(c)]
        x = sum(1 for k in ks if P[k][1])
        stats.append((lab, len(ks), x, x / len(ks), *wilson(x, len(ks))))
    n1, e1 = stats[0][1], stats[0][2]
    nm, em = sum(s[1] for s in stats[1:]), sum(s[2] for s in stats[1:])
    worklist = n1 - e1
    # two-sided permutation on the difference in exit share, one firm against two or
    # more, seeded so the number printed is the number verify.py checks
    import random as _rnd
    lab_ = [(c == 1, e) for c, e in P.values()]
    obs = e1 / n1 - em / nm
    rng, hits, N = _rnd.Random(20260915), 0, 20000
    ex = [e for _, e in lab_]
    for _ in range(N):
        rng.shuffle(ex)
        a = sum(x for (one, _), x in zip(lab_, ex) if one) / n1
        b = sum(x for (one, _), x in zip(lab_, ex) if not one) / nm
        if abs(a - b) >= abs(obs) - 1e-12:
            hits += 1
    p_perm = (hits + 1) / (N + 1)

    W, L, T, PH = 920, 150, 196, 330
    PW = W - L - 210
    step = PW / len(stats)
    ys = lambda p: T + PH - PH * p
    body = []

    for g in range(0, 101, 25):
        body.append(f'<line x1="{L:.1f}" y1="{ys(g/100):.1f}" x2="{L+PW:.1f}" '
                    f'y2="{ys(g/100):.1f}" stroke="{S.RULE}" stroke-width="1"/>')
        body.append(S.txt(L - 12, ys(g / 100) + 4, f"{g}%", size=11, fill=S.MUTED,
                          anchor="end", tab=True))
    body.append(S.txt(L - 12, T - 34, "of its listings are", size=11, fill=S.INK2, anchor="end"))
    body.append(S.txt(L - 12, T - 20, "permanent exits", size=11, fill=S.INK2, anchor="end"))

    lo2, hi2 = stats[1][4], max(s[5] for s in stats[1:])
    body.append(f'<rect x="{L+step:.1f}" y="{ys(hi2):.1f}" width="{PW-step:.1f}" '
                f'height="{ys(lo2)-ys(hi2):.1f}" fill="{CHRON}" fill-opacity="0.07"/>')
    body.append(S.txt(L + step + 12, ys(hi2) - 10,
                      f"every count above one: {em} exits in {nm} substances", size=10.5, fill=CHRON))

    for i, (lab, n, x, p, lo, hi) in enumerate(stats):
        cx = L + step * (i + 0.5)
        col = EXIT if p > 0.5 else CHRON
        body.append(f'<line x1="{cx:.1f}" y1="{ys(lo):.1f}" x2="{cx:.1f}" y2="{ys(hi):.1f}" '
                    f'stroke="{col}" stroke-width="2" stroke-linecap="round"/>')
        for e in (lo, hi):
            body.append(f'<line x1="{cx-7:.1f}" y1="{ys(e):.1f}" x2="{cx+7:.1f}" '
                        f'y2="{ys(e):.1f}" stroke="{col}" stroke-width="2"/>')
        body.append(f'<circle cx="{cx:.1f}" cy="{ys(p):.1f}" r="{3.2+math.sqrt(n)*0.75:.1f}" '
                    f'fill="{col}"/>')
        body.append(S.txt(cx, ys(p) - 8 - math.sqrt(n) * 0.75, f"{p:.0%}", size=15,
                          fill=col, anchor="middle", weight="600", tab=True))
        body.append(S.txt(cx, T + PH + 24, lab, size=13, fill=S.INK, anchor="middle",
                          weight="600", tab=True))
        body.append(S.txt(cx, T + PH + 41, f"{x} of {n}", size=10.5, fill=S.MUTED,
                          anchor="middle", tab=True))
    body.append(S.txt(L, T + PH + 68, "independent US firms reporting the same molecule short",
                      size=12, fill=S.INK2))
    body.append(S.txt(L + PW + 14, ys(0.87), "the cliff is between", size=11, fill=S.INK2))
    body.append(S.txt(L + PW + 14, ys(0.87) + 15, "one firm and two", size=11, fill=S.INK2))
    note, _h = S.para(L + PW + 14, ys(0.44),
                      "Dot area is the number of substances; the whiskers are 95% Wilson "
                      "intervals. They widen where the evidence thins, which is the half "
                      "of the picture a bar chart of four percentages hides.",
                      size=10, fill=S.MUTED, chars=26, leading=13)
    body += note

    svg = S.frame(
        W, T + PH + 168,
        "One firm reporting a shortage usually means one firm leaving",
        "Every substance on the FDA shortage list, grouped by how many independent US "
        "firms report it, against the share whose listings are all permanent "
        "discontinuances. It is a threshold, not a gradient.",
        body,
        footer=[
            f"If one firm reports it, plan a therapeutic substitution: {e1} of those {n1} are exits, "
            f"and no procurement lever reaches a company that is leaving.",
            f"The {worklist} substances that genuinely are sole-supplier shortages — the real re-tender "
            f"worklist — are named in the README rather than crowded onto this figure.",
            f"Permutation p {'< 0.0001' if p_perm < 1e-4 else f'= {p_perm:.4f}'} between one firm and two "
            f"or more. A firm counts as leaving only when every package NDC it lists for that molecule is discontinued.",
            "Supplier counts are the US column only; France and Australia publish no firm, so a "
            "drug at 1 may have several suppliers elsewhere and this cannot see it.",
        ])
    print(S.write("1-what-to-do.svg", svg))
    print(f"  one firm {e1}/{n1} | two or more {em}/{nm} | worklist {worklist} | p {p_perm:.5f} | "
          + " ".join(f"{l}:{x}/{n}" for l, n, x, *_ in stats))


if __name__ == "__main__":
    main()
