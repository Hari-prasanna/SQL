# Failure and Recovery

This is a query library, not a scheduled pipeline — there is no job to retry,
no notification webhook, and no orchestration. "Failure" here means a query
executes successfully but a row in its output doesn't represent a real,
correctly-matched transaction pair, or a real transaction pair is missing from
the output entirely.

## Failure modes

| Failure mode | Cause | Detection | Current behavior |
|---|---|---|---|
| Orphaned book-out (no book-in yet) | Item hasn't completed its second-leg transaction at query time | Not automatically flagged — surfaces as a row with `ZIEL_LHM` = `NULL` | `LEFT JOIN` keeps the row; it still passes the final `WHERE NVL(...) <>` filter, so it appears in output rather than being dropped, but nothing distinguishes it from a normal matched row except the `NULL` |
| Orphaned book-in (no book-out) | A book-in event exists with no corresponding book-out on record | Not detected at all | Because the join direction is book-out `LEFT JOIN` book-in, an unmatched book-in never appears in the output — this is a silent asymmetry, not a bug fix included here (see [../README.md](../README.md#9-trade-offs) and [limitations.md](limitations.md)) |
| Duplicate/out-of-sequence manual-sorting scans | Item scanned more than once, or scanned out of chronological order, in the same transaction ID | Not surfaced as an error — handled at match time | `ROW_NUMBER()` sequence matching (see [data-contract.md](data-contract.md)) pairs scans positionally in sequence order rather than flagging the duplicate; a truly extra/erroneous scan with no real partner still gets assigned an `rn` and will pair with whatever shares that rank, which may be a mismatch rather than a rejection |
| `"SEQUENCE"` ordering assumption violated | Upstream system's sequence values stop being a reliable proxy for real event order | Not detected | `ROW_NUMBER()` matching would silently produce wrong pairings — no assertion checks this assumption still holds |
| Malformed or missing `CUST_DATA` JSON | A row's custom-data field isn't valid JSON, or lacks an expected path | `JSON_VALUE` returns `NULL` for that path (Oracle default `NULL ON ERROR` behavior) | Downstream `CASE`/`DECODE` expressions fall through to their `'Unknown'` branch rather than raising an error — a bad row degrades to "Unknown" classification instead of failing the query |
| Reference-carrier filter matches nothing | `:ref_lhm_filter` bind value doesn't match any row | Query returns zero rows | No explicit handling distinguishes "no data for this filter" from "filter typo" — same as the analogous gap noted in the sibling `featured/01-clarification-automation` project |

## Recovery

There is no automated recovery path because there is no automated run — these
are ad hoc analyst-run queries. Recovery, in practice, means:

1. **Suspected missing rows (orphaned book-in problem):** re-run with a wider
   date range, or write a supplementary anti-join query (book-in rows with no
   matching book-out) to check for the asymmetry described above — no such
   query exists in this repository today (see
   [../README.md](../README.md#11-what-i-would-improve-next)).
2. **Suspected duplicate/mismatched manual-sorting pairs:** manually inspect the
   `"SEQUENCE"` values for the affected `LOCAL_TRANSACTION_ID` to confirm the
   ordering assumption held for that specific transaction.
3. **Unexpected `'Unknown'` classifications:** inspect the raw `CUST_DATA` JSON
   for the affected rows directly — the query itself won't distinguish "field
   genuinely absent" from "field present but an unmapped code value" beyond
   both falling through to `'Unknown'`.

## What is not automated

Nothing in this project runs unattended. There is no retry policy, no failure
notification, and no scheduled re-run — every execution is a deliberate,
manual analyst action against a chosen date range.
