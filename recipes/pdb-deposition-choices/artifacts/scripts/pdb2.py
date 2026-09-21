#!/usr/bin/env python3
"""Second fetch phase: target identity, publication lag, depositor names, model counts.

    python3 pdb2.py            # appends to pdb.json, skips what is already there

Split from pdb.py because these came from questions the first two figures raised rather than
from the original list, and because one of them is slow: the deposit-to-publication lag needs
`rcsb_primary_citation.year` faceted inside each deposition year, which is one request per year.

**Why the lag matters.** Figure 1 marks the last three deposition years as right-censored and
draws them dashed. That was reasoning, not measurement. With the citation year available the
censoring can be measured: if the median paper appears one year after deposition, a 2025 cohort
is half-resolved and a 2023 one is essentially complete.

**Protein identity is a UniProt accession, not a name.** `rcsb_uniprot_protein.name.value`
groups by a free-text protein name and `..reference_sequence_identifiers.database_accession`
groups by accession. The accession is the key; the name is what it is called this week.
"""
import json, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pdb as P                                                          # noqa: E402

ACC = ("rcsb_polymer_entity_container_identifiers."
       "reference_sequence_identifiers.database_accession")
NAME = "rcsb_uniprot_protein.name.value"


def main():
    d = P.load()
    add = {}

    if "accessions" not in d:
        add["accessions"] = P.terms(P.ALL, ACC, 200)
        add["accession_names"] = P.terms(P.ALL, NAME, 60)
        print(f"  {len(add['accessions'])} accessions, top {add['accessions'][0]}")

    if "citation_year_by_deposit" not in d:
        # one request per deposition year: citation years inside that cohort
        out = {}
        for y in range(2000, 2027):
            q = P.AND(P.term("rcsb_accession_info.deposit_date",
                             {"from": f"{y}-01-01", "to": f"{y}-12-31"}, "range"))
            try:
                r = P.q({"query": q, "return_type": "entry", "request_options": {
                    "paginate": {"start": 0, "rows": 0},
                    "facets": [{"name": "c", "aggregation_type": "terms",
                                "attribute": "rcsb_primary_citation.year",
                                "max_num_intervals": 40}]}})
                out[y] = {int(float(b["label"])): b["population"]
                          for b in (r.get("facets") or [{}])[0].get("buckets", [])
                          if str(b["label"])[:4].isdigit()}
            except Exception as e:                                       # noqa: BLE001
                print(f"    {y}: {type(e).__name__}")
            time.sleep(0.25)
        add["citation_year_by_deposit"] = out
        print(f"  publication lag for {len(out)} deposition cohorts")

    if "covid_by_year" not in d:
        cov = {}
        for acc, label in (("P0DTD1", "replicase polyprotein 1ab"),
                           ("P0DTC2", "spike glycoprotein"),
                           ("P0DTC9", "nucleoprotein")):
            cov[acc] = {"label": label,
                        "by_year": P.by_year(P.term(ACC, acc)),
                        "total": P.count(P.term(ACC, acc))}
            print(f"  {acc} {label:<26}{cov[acc]['total']:>7,}")
        add["covid_by_year"] = cov

    if "model_counts" not in d:
        add["model_counts"] = P.terms(P.ALL, "rcsb_entry_info.deposited_model_count", 20)
        add["entity_types"] = P.terms(P.ALL, "rcsb_entry_info.selected_polymer_entity_types", 12)

    if not add:
        print("  everything already cached")
        return 0
    d.update(add)
    json.dump(d, open(P.OUT, "w"), indent=1)
    print(f"\n  added {', '.join(add)} to pdb.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
