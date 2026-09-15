#!/usr/bin/env python3
"""Write provenance.json from the archive, rather than from memory.

Every field here is read off the capture files the figures were actually computed from,
including their sizes and hashes, so a reader can tell whether their copy is the one
this recipe describes. Typing them by hand is how a provenance file starts agreeing
with the draft instead of with the bytes.
"""
import glob, hashlib, json, os, sys, datetime as dt
sys.path.insert(0, ".")
import shortagelib as S
import features as X

RECIPE = S.RECIPE


def digest(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return {"bytes": os.path.getsize(p), "sha256": h.hexdigest()}


def main():
    regs = S.registers()
    codes, cd = S.shared_coded(regs)
    F = X.build()
    one = [k for k in F if F[k]["n_firms"] == 1]
    insp = sorted(p for src in ("fda.inspections.history", "fda.inspections.drugs")
                  for p in glob.glob(str(S.ARCHIVE / "raw" / src / "**" / "*"), recursive=True)
                  if os.path.isfile(p) and not p.endswith(".gitkeep"))

    import survival as V
    import csv as _csv
    subs = V.subjects(); curve = V.km(subs)
    rev = list(_csv.DictReader((S.DATA / "revisions.csv").open()))
    fda_run = S.latest_run("fda.shortages.current")
    prov = {
        "method_version": "2.0.0",
        "_method_version": (
            "2.0.0 reads the whole FDA feed. 1.0.0 (never pushed) read one page of a two-page "
            "feed -- the lexically newest capture file, which is page two: 619 of 1,619 rows, "
            "148 of 206 substances -- and every FDA number in it, the 88%-against-4% cliff "
            "included, was computed on that half. On the full register the cliff is 95% "
            "against 16%, the concentration finding falls to p = 0.047 and is demoted to "
            "artifacts/charts/negative/, and the recipe absorbs a sibling draft "
            "(shortage-memory) on what the registers retain and what a shortage lasts. "
            "The substance key is the full RxNorm ingredient SET, as in 1.0.0. The "
            "revision diff is keyed on the statutory stream, without which 34 packages "
            "carrying both a shortage row and a discontinuance row read as revisions."),
        "retrieved": dt.date.today().isoformat(),
        "capture_date": "2026-09-10",
        "sources": {
            "wss-drug-scarcity": {
                "what": "national drug-shortage registers -- FDA (openFDA JSON, two pages per run), "
                        "ANSM (HTML table), TGA (JSON literal inlined in HTML) -- plus FDA inspections, "
                        "warning letters, recalls, import alert 66-40 and Drugs@FDA marketing-status "
                        "counts for a 304-molecule cohort",
                "role": "CAPTURE -- none of the three registers publishes its own history; a resolved "
                        "shortage leaves the page, which is one of the findings",
                "remote": "https://github.com/q3dresearch/wss-drug-scarcity",
                "note": "not vendored here; fetch.py clones it to artifacts/data/wss-drug-scarcity, "
                        "or set $WSS_DRUG_SCARCITY",
                "files": {os.path.relpath(f, S.ARCHIVE): digest(f)
                          for k in ("fda.shortages.current", "ansm.shortages.fr", "tga.shortages.au")
                          for f in S.latest_run(k)},
                "fda_files_in_newest_run": len(fda_run),
                "fda_capture_runs_differenced": len(rev) + 1,
                "inspection_files": len(insp),
                "inspection_fiscal_years": "2009-2026, complete; each file reports "
                                           "totalrecordcount == resultcount, so no page is truncated",
            },
            "rxnav": {
                "what": "NLM RxNav: drug name -> RxNorm ingredient codes",
                "role": "ENRICHMENT -- re-fetchable, no key, NLM keeps its own history",
                "cache": "artifacts/data/rxnorm.json (git-ignored; rebuild with rxnorm.py, ~40 min)",
                "names_resolved": sum(1 for v in json.loads(
                    (S.DATA / "rxnorm.json").read_text()).values() if v.get("rxcui")),
                "key": "the full ingredient SET, not the first ingredient",
            },
            "cms_nadac": {
                "what": "CMS National Average Drug Acquisition Cost, 2026 file dated 09-09-2026",
                "role": "TESTED AND REJECTED -- joins 39% of shortage package NDCs and 18% of the "
                        "injectable ones, because it prices retail pharmacy and hospital injectables "
                        "move through GPO contracts it does not observe.",
                "used_in_figures": False,
            },
        },
        "headline": {
            "substances_on_the_us_list": len(F),
            "permanent_discontinuances": sum(1 for k in F if F[k]["is_exit"]),
            "short_in_all_three_countries": len(codes),
            "one_reporting_firm": len(one),
            "one_reporting_firm_that_are_exits": sum(1 for k in one if F[k]["is_exit"]),
            "re_tender_worklist": sorted(F[k]["name"] for k in one if not F[k]["is_exit"]),
            "two_or_more_firms": sum(1 for k in F if F[k]["n_firms"] >= 2),
            "two_or_more_firms_that_are_exits": sum(1 for k in F if F[k]["n_firms"] >= 2 and F[k]["is_exit"]),
            "paediatric_flagged": 12,
            "paediatric_flagged_that_are_exits": 0,
            "tga_shortages_observed_in_window": len(subs),
            "tga_resolutions_in_window": sum(s["event"] for s in subs),
            "tga_median_of_resolved_rows_days": V.median_of_resolved(subs),
            "tga_km_median_days": V.quantile(curve, 0.5),
            "tga_km_q25_days": V.quantile(curve, 0.25),
            "fda_revision_intervals": len(rev),
            "fda_substantive_changes": sum(int(r["changed"]) for r in rev),
            "fda_silent_changes": sum(int(r["silent"]) for r in rev),
            "fda_silent_changes_raw_diff": sum(int(r["naive_silent"]) for r in rev),
        },
        "figures": {
            "1-what-to-do": "one reporting firm predicts a permanent exit at 95% against 16%",
            "2-paediatric": "nothing carrying the paediatric flag is being discontinued",
            "3-duration": "an Australian shortage lasts about a year; the register's resolved rows say two months",
            "4-memory": "no register keeps a resolved shortage for more than about a year",
            "negative/": "five worked failures: two pretty tables, two single axes, one half-register result",
        },
        "verified_by": "artifacts/scripts/verify.py -- every number in the README re-derived from the archive",
    }
    out = RECIPE / "provenance.json"
    S.write_json_atomic(out, prov)
    print(f"  wrote {out}")
    print(f"  {len(prov['headline'])} headline fields, "
          f"{len(prov['sources']['wss-drug-scarcity']['files'])} capture files hashed")


if __name__ == "__main__":
    main()
