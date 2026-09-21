#!/usr/bin/env python3
"""The unpublished structures are not neglect, and they are not a size effect either.

    python3 chart-2-depositors.py

Figure 1 found that 15.8% of the PDB cites "To be published". This is the mechanism, and it is
not diffuse.

**Structural genomics consortia run four to five times the baseline.** The Joint Center for
Structural Genomics is **86.4% unpublished**, the Midwest Center 80.6%, RIKEN's initiative
74.0%. Those programmes were funded to populate fold space against a target list; the deposited
coordinate file was the deliverable and a paper was not.

**Size is ruled out as the explanation.** Across the 40 most prolific depositors the correlation
between log entry count and unpublished share is **rho +0.16** -- nothing. Every one of the
eight consortia sits high regardless of how many entries it has, and the individuals span 3.3%
to 73.3% at every size. The register's unpublished pile is not "prolific depositors don't write
up"; it is a specific programme, and the horizontal axis is here to rule the alternative out
rather than to show a trend.

**Rate and volume pick different leaders.** JCSG has the highest share at 86.4% and owns about
1,386 unwritten entries. Von Delft sits at half the rate, 48.7%, and owns **2,760** -- twice the
pile. Bubble area is the absolute count for exactly this reason: the largest bubble is not the
highest point, and a plan to close the gap would start somewhere different from a plan to
explain it.

**One trap binds every reading of this facet.** `audit_author.name` is multi-valued: an entry
carries many authors, so entries cannot be summed across depositors and no "the top N account
for X%" is computable. Shares *within* one depositor are fine, which is why the figure plots
only those.
"""
import math, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pdb as P, plate                                                   # noqa: E402
from plate import txt, halo, wrap, INK, INK2, MUTED, RULE, GRID          # noqa: E402

OUT = os.path.join(HERE, "..", "charts", "2-depositors.svg")
RED, AMBER, GREEN, BLUE, SLATE = "#8c2318", "#c07a1e", "#1b7f5a", "#4a7fa8", "#9aa4ad"
PERSON = re.compile(r"^[^,]+,\s*[A-Z]")
# named on the plate because they anchor a reading; everything else stays an unlabelled mark
LABEL = {"Joint Center for Structural Genomics (JCSG)": ("JCSG", "e"),
         "Midwest Center for Structural Genomics (MCSG)": ("MCSG", "e"),
         "Northeast Structural Genomics Consortium (NESG)": ("NESG", "w"),
         "RIKEN Structural Genomics/Proteomics Initiative (RSGI)": ("RIKEN RSGI", "e"),
         "Structural Genomics Consortium (SGC)": ("SGC", "e"),
         "Joachimiak, A.": ("Joachimiak", "n"),
         "Almo, S.C.": ("Almo", "w"),
         "von Delft, F.": ("von Delft", "w"),
         "Weiss, M.S.": ("Weiss", "e"),
         "Dias, A.": ("Dias", "e")}


def rho(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    den = math.sqrt(sum((a - mx) ** 2 for a in xs) * sum((b - my) ** 2 for b in ys))
    return num / den if den else 0.0


def main():
    d = P.load()
    base = d["unpublished_total"] / d["total"]
    rows = [{"name": n, "person": bool(PERSON.match(n)),
             "entries": v["entries"], "unpub": v["unpublished"],
             "share": v["unpublished"] / max(v["entries"], 1)}
            for n, v in d["depositor_unpub"].items()]
    rows.sort(key=lambda r: -r["unpub"])
    r_all = rho([math.log10(r["entries"]) for r in rows], [r["share"] for r in rows])

    W, H = 1200, 880
    s = plate.open_svg(W, H, "The unpublished structures are not neglect, and they are "
                             "not a size effect either")
    fr, _ = plate.frame(W, 62,
                        who="anyone reading the PDB's unpublished share as a failure of the "
                            "literature",
                        decide="whether an unwritten structure is a gap or a deliverable",
                        wrong="unpublished share climbs with depositor size")
    s += fr

    AX, AY, AH, AW = 28, 150, 470, 790
    lo, hi = 1000, 7000
    x0, pw = AX + 46, AW - 92
    px = lambda v: x0 + pw * ((math.log10(v) - math.log10(lo))
                              / (math.log10(hi) - math.log10(lo)))
    py = lambda f: AY + AH - 58 - (AH - 92) * f
    for f in (0, .25, .5, .75, 1.0):
        s.append(f'<line x1="{x0:.1f}" y1="{py(f):.1f}" x2="{px(hi):.1f}" y2="{py(f):.1f}" '
                 f'stroke="{GRID}"/>')
        s.append(txt(x0 - 8, py(f) + 3, f"{f:.0%}", size=9, fill=MUTED, anchor="end"))
    s.append(txt(AX, AY - 18, "share of this depositor's entries that were never written up",
                 size=11, fill=INK2))
    for v in (1000, 1500, 2000, 3000, 5000, 7000):
        s.append(f'<line x1="{px(v):.1f}" y1="{py(0):.1f}" x2="{px(v):.1f}" '
                 f'y2="{py(0)+5:.1f}" stroke="{MUTED}"/>')
        s.append(txt(px(v), py(0) + 18, f"{v:,}", size=9, fill=MUTED, anchor="middle"))
    s.append(txt(AX, py(0) + 36, "entries this depositor's name appears on (log scale)",
                 size=10, fill=MUTED))

    s.append(f'<line x1="{x0:.1f}" y1="{py(base):.1f}" x2="{px(hi):.1f}" y2="{py(base):.1f}" '
             f'stroke="{INK2}" stroke-width="1.4" stroke-dasharray="5 3"/>')
    s += halo(px(hi), py(base) - 8, f"register-wide {base:.1%}", size=10, fill=INK2,
              anchor="end", weight="700")

    area = lambda u: math.sqrt(u / math.pi) * 0.62
    for r in sorted(rows, key=lambda r: -r["unpub"]):
        col = BLUE if r["person"] else RED
        cx, cy, rr = px(r["entries"]), py(r["share"]), area(r["unpub"])
        s.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{rr:.1f}" fill="{col}" '
                 f'fill-opacity="0.22" stroke="{col}" stroke-width="1.3"/>')
        s.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="1.8" fill="{col}"/>')
        lab = LABEL.get(r["name"])
        if lab:
            t, side = lab
            if side == "n":
                s += halo(cx, cy - rr - 6, t, size=9.5, fill=col, anchor="middle",
                          weight="700")
            else:
                dx = rr + 7 if side == "e" else -(rr + 7)
                s += halo(cx + dx, cy + 3.5, t, size=9.5, fill=col,
                          anchor="start" if side == "e" else "end", weight="700")

    ly = AY + 6
    for col, t in ((RED, "a consortium filing under its own name"), (BLUE, "a person")):
        s.append(f'<circle cx="{px(hi)-262:.1f}" cy="{ly-3.5:.1f}" r="4.6" fill="{col}" '
                 f'fill-opacity="0.22" stroke="{col}" stroke-width="1.3"/>')
        s.append(txt(px(hi) - 250, ly, t, size=10, fill=INK2))
        ly += 17
    for u in (500, 2000):
        rr = area(u)
        s.append(f'<circle cx="{px(hi)-256+rr:.1f}" cy="{ly+8:.1f}" r="{rr:.1f}" '
                 f'fill="none" stroke="{MUTED}" stroke-width="1.1"/>')
        s.append(txt(px(hi) - 252 + 2 * rr + 6, ly + 11, f"{u:,} unwritten entries",
                     size=9, fill=MUTED))
        ly += 2 * rr + 8

    by = AY + AH + 4
    s.append(txt(AX, by, "the horizontal axis is here to rule something out", size=12.5,
                 fill=INK, weight="600"))
    s += wrap(AX, by + 20,
              f"Across these 40 depositors the correlation between log entry count and "
              f"unpublished share is rho {r_all:+.2f} — nothing. Every consortium sits high "
              f"whatever its size, and the individuals span 3.3% to 73.3% at every size. The "
              f"pile is not prolific depositors failing to write up; it is a specific "
              f"programme. The individuals sitting up among the consortia are structural "
              f"genomics principal investigators, which is an inference from outside this "
              f"table — its falsifier is that their depositions should cluster in 2004–2011, "
              f"and that is not tested here.",
              size=11, fill=INK2, chars=104, leading=15)
    s += halo(AX + 830, by + 2, "rate and volume disagree", size=10.5, fill=GREEN,
              weight="700")
    s += wrap(AX + 830, by + 20,
              "JCSG has the highest rate, 86.4%, and about 1,386 unwritten entries. Von Delft "
              "runs 48.7% and owns 2,760 — twice the pile at half the rate.",
              size=10.5, fill=INK2, chars=42, leading=14)

    fy = H - 24 - 14 * 4
    s.append(f'<line x1="28" y1="{fy-20:.1f}" x2="{W-28}" y2="{fy-20:.1f}" stroke="{RULE}"/>')
    s += wrap(28, fy,
              f"RCSB PDB search API, fetched {d['fetched']}. Depositor is `audit_author.name`, "
              f"a multi-valued field: an entry carries many authors, so entries cannot be "
              f"summed across depositors and no “top N account for X%” is computable "
              f"from it — shares within a single depositor are fine, which is why only those "
              f"are drawn. Names also split: `Edwards, A.` has 2,698 entries and `Edwards, "
              f"A.M.` has 2,331, one person in two buckets; one name in sixty splits this way, "
              f"which bounds the damage but had to be measured. Only names with 800 or more "
              f"entries are shown, forty of them. “Unpublished” means the primary "
              f"citation reads “To be published”, recorded at deposition and never "
              f"revisited.",
              size=11, fill=MUTED, chars=150, leading=14)
    s.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.abspath(OUT), "w").write("\n".join(s))
    print(f"  wrote {os.path.abspath(OUT)}")
    print(f"    rho(log entries, share) = {r_all:+.3f} over {len(rows)} depositors")
    return 0


if __name__ == "__main__":
    sys.exit(main())
