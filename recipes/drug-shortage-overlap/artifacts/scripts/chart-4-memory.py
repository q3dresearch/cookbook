#!/usr/bin/env python3
"""What each register still has on screen, by year: three rows, one per register;
year across; count up; colour by state.

Every register is folded to the same three states -- open shortage, discontinuance
notice, resolved -- and stacked per year, so the reader compares where the orange
(resolved) bars reach against where the blue (open) bars reach. Open rows reach back
decades; resolved rows reach back a year, everywhere. The single older resolved bar
in Australia and in France is the control: a resolved row CAN survive for years, so
the empty years beside it are sweeping, not a young field.

Position, not area: an earlier version drew this as bubbles, and a count encoded as
area was the thing the eye read worst. Each row has its own count axis because the
registers differ five-fold in size and the claim is about the x-extent of the bars.
"""
import collections
import csv
import sys
sys.path.insert(0, ".")
import shortagelib as S

COL = {"shortage": "#1b4f8a", "discontinuance": "#7b9cc4", "resolved": "#d17b00"}
ORDER = ["FDA (US)", "ANSM (FR)", "TGA (AU)"]


def main():
    rows = [r for r in csv.DictReader((S.DATA / "memory.csv").open()) if r["year"]]
    cells = collections.Counter((r["register"], int(r["year"]), r["cls"]) for r in rows)
    loads = collections.Counter((r["register"], int(r["year"])) for r in rows if r["bulk_load"] == "True")
    years = sorted({y for _, y, _ in cells})
    y0, y1 = years[0], years[-1]
    dur = {reg: sorted(int(r["duration_days"]) for r in rows
                       if r["register"] == reg and r["duration_days"] not in ("", None)) for reg in ORDER}

    W, L, T, R = 1040, 150, 160, 300
    PW, FH, GAP = W - L - R, 150, 34
    bw = PW / (y1 - y0 + 1) * 0.78
    xs = lambda y: L + PW * (y - y0 + 0.5) / (y1 - y0 + 1)
    body = []
    for i, reg in enumerate(ORDER):
        top = T + i * (FH + GAP)
        tot = {y: sum(cells.get((reg, y, c), 0) for c in COL) for y in years}
        ymax = max(tot.values()) or 1
        ys = lambda n: top + FH - FH * n / ymax
        body.append(S.txt(18, top + 16, reg, size=14, fill=S.INK, weight="600"))
        for g in (0, ymax):
            body.append(f'<line x1="{L}" y1="{ys(g):.1f}" x2="{L+PW:.1f}" y2="{ys(g):.1f}" '
                        f'stroke="{S.RULE}" stroke-width="1"/>')
            body.append(S.txt(L - 8, ys(g) + 4, f"{g}", size=10.5, fill=S.MUTED, anchor="end", tab=True))
        for y in years:
            base = 0
            for c in ("shortage", "discontinuance", "resolved"):
                n = cells.get((reg, y, c), 0)
                if not n:
                    continue
                body.append(f'<rect x="{xs(y)-bw/2:.1f}" y="{ys(base+n):.1f}" width="{bw:.1f}" '
                            f'height="{ys(base)-ys(base+n):.1f}" fill="{COL[c]}"/>')
                base += n
            if loads.get((reg, y)) == tot[y] and tot[y]:
                body.append(S.txt(xs(y), ys(tot[y]) - 6, f"{tot[y]} rows on two dates: a bulk load",
                                  size=10, fill=S.MUTED, anchor="middle"))
        # survivors: every resolved bar older than the newest resolved year
        ry = sorted(y for (r_, y, c) in cells if r_ == reg and c == "resolved")
        for y in ry[:-1]:
            n = cells[(reg, y, "resolved")]
            body.append(S.txt(xs(y), ys(tot[y]) - 8, f"{n} survivor{'s' if n > 1 else ''}", size=10.5,
                              fill=COL["resolved"], anchor="middle", weight="600"))
        # verdict, right gutter
        res_n = sum(cells.get((reg, y, "resolved"), 0) for y in years)
        d = dur[reg]
        head = (f"{len(d)} resolved rows carry a duration" if d else f"{res_n} resolved rows, no duration")
        why = {"FDA (US)": "retention: fields exist, rows purged",
               "ANSM (FR)": "schema: no column is the start of a shortage",
               "TGA (AU)": f"median {d[len(d)//2] if d else '—'} d; corrected, a year (fig. 3)"}[reg]
        body.append(S.txt(L + PW + 14, top + 14, head, size=12, fill=S.INK, weight="600"))
        body.append(S.txt(L + PW + 14, top + 30, why, size=10.5, fill=S.MUTED))
        if i == len(ORDER) - 1:
            for y in years:
                if y % 2 == 0 or y in (y0, y1):
                    body.append(S.txt(xs(y), top + FH + 18, str(y), size=11, fill=S.MUTED, anchor="middle"))
    ly = T - 34
    for c, lab in (("shortage", "open shortage"), ("discontinuance", "discontinuance notice"), ("resolved", "resolved")):
        body.append(f'<rect x="{L:.1f}" y="{ly-9}" width="11" height="11" fill="{COL[c]}"/>')
        body.append(S.txt(L + 16, ly, lab, size=11, fill=S.INK2))
        L += 150
    L = 150
    H = T + len(ORDER) * (FH + GAP) + 110
    svg = S.frame(
        W, H,
        "No register keeps a resolved shortage for more than about a year",
        "Every record each register still shows, by the year it sits at — open rows at the year "
        "the shortage began, resolved rows at the year it was resolved. Open rows reach back "
        "decades; resolved rows reach back twelve months, in all three countries.",
        body,
        footer=[
            "If you need how long shortages last, only Australia can answer, and only for shortages "
            "open in the last year — and its resolved rows understate it six-fold (figure 3).",
            "If you need a trend — are shortages getting longer? — no register can give it and none "
            "ever will; each deletes the evidence at about twelve months. Only an archive can.",
            "The lone older resolved rows are the control: a resolved row CAN persist, so the "
            "emptiness beside it is deletion rather than a field that was only recently kept.",
        ])
    print(S.write("4-memory.svg", svg))


if __name__ == "__main__":
    main()
