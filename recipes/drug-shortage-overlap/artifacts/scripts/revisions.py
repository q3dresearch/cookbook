#!/usr/bin/env python3
"""What the FDA feed changes between captures, and whether update_date says so.

    python revisions.py         # writes artifacts/data/revisions.csv

A register that publishes only current state destroys every transition it makes.
`update_date` is supposed to announce a change. Holding consecutive captures and
differencing them is the only way anyone, FDA included, can check that it does.

This is a derive-layer script: it fetches nothing, and it improves on its own -- four
intervals today, about fifty-two a year from now.

TRAP 1. SORT THE LISTS BEFORE COMPARING. The `openfda` block holds lists in no stable
order. A raw comparison reports 626 silent changes across the four intervals held
on 2026-09-15; sorted, 3. The `naive_silent` column re-derives the wrong number
every run so the size of the trap stays visible.

TRAP 2. CHECK THE KEY IS UNIQUE WITHIN ONE CAPTURE BEFORE DIFFING TWO. The obvious
identity (drug, company, package NDC) is not unique: 43 keys carry two rows in one
capture, 34 of them one `Current` beside one `To Be Discontinued` for the same
package -- the register's two statutory streams. Keyed without the stream, a
last-wins dict plus an unstable API order made those twins "flip" between captures
with update_date frozen, and a draft of this recipe showcased that as the register
rewriting its own past. The key here carries the stream; the nine keys still
duplicated after that are excluded as ambiguous and counted.
"""
import collections, csv, datetime as dt, json, os, re, sys
sys.path.insert(0, ".")
import shortagelib as S

STREAM = {"Current": "shortage", "Resolved": "shortage",
          "To Be Discontinued": "discontinuance", "Discontinued": "discontinuance"}
FIELDS = ("generic_name", "company_name", "package_ndc")
ENRICHMENT = {"openfda"}


def canon(v):
    if isinstance(v, list):
        return sorted((canon(x) for x in v), key=repr)
    if isinstance(v, dict):
        return {k: canon(v[k]) for k in sorted(v)}
    return v


def runs():
    """Every capture run of the FDA feed, oldest first, pages merged."""
    import glob
    stamped = []
    for p in glob.glob(str(S.ARCHIVE / "raw" / "fda.shortages.current" / "**" / "*"), recursive=True):
        m = re.match(r"(\d{8}T\d{6}Z)", os.path.basename(p))
        if os.path.isfile(p) and m:
            stamped.append((dt.datetime.strptime(m.group(1), "%Y%m%dT%H%M%SZ"), p))
    stamped.sort()
    groups = []
    for when, p in stamped:
        if groups and (when - groups[-1][0][0]).total_seconds() <= 600:
            groups[-1].append((when, p))
        else:
            groups.append([(when, p)])
    return [(g[0][0].isoformat(timespec="minutes"),
             [r for _, p in g for r in json.loads(S._read(p))["results"]]) for g in groups]


def keyed(rows):
    key = lambda r: tuple(str(r.get(f)) for f in FIELDS) + (STREAM.get(r.get("status"), str(r.get("status"))),)
    count = collections.Counter(key(r) for r in rows)
    amb = {k for k, n in count.items() if n > 1}
    return {key(r): r for r in rows if key(r) not in amb}, amb


def diff(x, y):
    X, ax = keyed(x); Y, ay = keyed(y)
    changed, silent, naive, moved = 0, [], 0, collections.Counter()
    for k in set(X) & set(Y):
        if X[k] != Y[k] and X[k].get("update_date") == Y[k].get("update_date"):
            naive += 1
        cx, cy = canon(X[k]), canon(Y[k])
        if cx == cy:
            continue
        mv = {f for f in set(cx) | set(cy) if cx.get(f) != cy.get(f)}
        if mv <= ENRICHMENT:
            continue
        changed += 1
        moved.update(mv - ENRICHMENT)
        if X[k].get("update_date") == Y[k].get("update_date"):
            silent.append((k, sorted(mv - ENRICHMENT)))
    return {"rows_to": len(y), "ambiguous_keys": len(ax | ay),
            "departed": len(set(X) - set(Y)), "arrived": len(set(Y) - set(X)),
            "changed": changed, "silent": len(silent), "naive_silent": naive,
            "_silent": silent, "_moved": moved}


def main():
    rs = runs()
    if len(rs) < 2:
        print(f"  {len(rs)} capture run(s) -- a revision needs two.")
        return 0
    out, moved, silents = [], collections.Counter(), []
    for (t1, x), (t2, y) in zip(rs, rs[1:]):
        r = diff(x, y); moved.update(r.pop("_moved")); silents += [(t1, t2, k, mv) for k, mv in r.pop("_silent")]
        out.append({"from": t1, "to": t2, **r})
    S.DATA.mkdir(parents=True, exist_ok=True)
    with open(S.DATA / "revisions.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
    print(f"  {len(rs)} runs, {len(out)} intervals -> artifacts/data/revisions.csv")
    print(f"  {'from':<17}{'to':<17}{'rows':>6}{'ambig':>7}{'left':>6}{'new':>5}{'changed':>9}{'silent':>8}{'naive':>7}")
    for r in out:
        print(f"  {r['from']:<17}{r['to']:<17}{r['rows_to']:>6}{r['ambiguous_keys']:>7}{r['departed']:>6}"
              f"{r['arrived']:>5}{r['changed']:>9}{r['silent']:>8}{r['naive_silent']:>7}")
    tot, sil, nai = (sum(r[k] for r in out) for k in ("changed", "silent", "naive_silent"))
    print(f"  {sil} of {tot} substantive changes moved no update_date; a raw diff says {nai}.")
    print("  fields that moved:", ", ".join(f"{f} {n}" for f, n in moved.most_common(7)))
    for t1, t2, k, mv in silents:
        print(f"    silent {t1[5:]} -> {t2[5:]}  {k[0][:36]:<36} {k[2]:<14} {', '.join(mv)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
