#!/usr/bin/env python3
"""Sample organismQuantityType across taxa, because the field is free text.

    python3 units.py           # fetch and cache the sample

**Why sample rather than aggregate.** OBIS has no endpoint that counts distinct values of
`organismQuantityType`, so the only way to see the vocabulary is to pull records and look. The
sample is drawn across ten phyla and classes rather than from the head of the index, because a
single dataset's convention would otherwise dominate and the result would say more about the
sampling than about the register.

**It is a sample and the figure says so.** The counts below are of a few thousand records out
of 229 million. They support a claim about the *variety* of units in use, which a sample can
establish, and not about the share of records carrying any particular one, which it cannot.
"""
import json, os, sys, time, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.environ.get("OBIS_DATA") or os.path.join(HERE, "..", "data")
OUT = os.path.join(DATA, "units-sample.json")
UA = "web-snapshots research bot (dl.eeee.nv@gmail.com)"
TAXA = ["Actinopterygii", "Mollusca", "Aves", "Mammalia", "Crustacea", "Cnidaria",
        "Annelida", "Echinodermata", "Bacillariophyta", "Chordata", "Porifera", "Rhodophyta"]
PER = 500


def main():
    if os.path.exists(OUT):
        d = json.load(open(OUT))
        print(f"  cached: {d['sampled']:,} records, {len(d['types'])} distinct unit strings")
        return 0
    types, fields, n = {}, {}, 0
    for t in TAXA:
        u = ("https://api.obis.org/v3/occurrence?"
             + urllib.parse.urlencode({"scientificname": t, "size": PER}))
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": UA}),
                                        timeout=240) as r:
                res = json.load(r).get("results", [])
        except Exception as e:                                          # noqa: BLE001
            print(f"  {t}: {type(e).__name__}")
            continue
        for rec in res:
            n += 1
            q = rec.get("organismQuantityType")
            if q:
                types[q.strip()] = types.get(q.strip(), 0) + 1
            for f in ("organismQuantity", "sampleSizeValue", "samplingProtocol",
                      "individualCount", "coordinateUncertaintyInMeters"):
                if rec.get(f) not in (None, "", 0):
                    fields[f] = fields.get(f, 0) + 1
        print(f"  {t}: {len(res)} records")
        time.sleep(0.3)
    os.makedirs(DATA, exist_ok=True)
    json.dump({"sampled": n, "taxa": TAXA, "per": PER, "types": types, "fields": fields},
              open(OUT, "w"), indent=2)
    print(f"\n  {n:,} records, {len(types)} distinct unit strings, written to {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
