# Questions this recipe asks

Status is honest, not aspirational. Last reviewed 2026-09-09 · method 1.0.0

## Answered

**Does this register lose records, or only appear to?**
Both, and they are separable. Of 380 disappearances over two days, 318 returned
the next day and every one was a 2025 case; 62 did not and 61 of those were
2021. The split is exact. → `register-churn.svg`

**Is the clustering at the front of each partition a bug in our query?**
No. Three explanations were tested and rejected: a `>=` versus `>` boundary
error (the partitions use correct half-open intervals on `Inkomdatum`), a
division artefact from single-record partitions (the smallest holds 24), and
contamination from quarantined captures (excluded). Partitions are ordered by
case number, so the front of one is the oldest case of that year — the
clustering *is* the expiry signal.

## Open

**What is the actual expiry rate?**
Three capture days cannot establish one. Sixty-two departures over two days is
consistent with a five-year window, and with what this archive already expected,
but it is one observation. *Would need:* twelve monthly runs appended to
`history.csv`.

**Why do 2025 records flicker?**
This measures the symptom — the service returns different result sets on
different days — not the cause. Replication lag, index rebuilds and load
shedding would all look like this from outside.

**Does the same pattern appear in the other register captured here?**
`calfire.harvest.proposed` shows a 9.9% shrink, the largest in the fleet scan,
and has not been diffed record-by-record. It is the obvious next case and the
tools already exist.

**Do other archives in the fleet show expiry versus flicker?**
`what-publishers-destroy.py` scans whatever archives are present and found 87
shrink events in this one alone. Most are rolling-window endpoints behaving as
designed. Separating those from registers has been done by hand, not by rule.
