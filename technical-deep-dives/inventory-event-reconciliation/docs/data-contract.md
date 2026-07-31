# Data Contract

## Source table

Both queries read from a generic alias `TRANSACTION_HISTORY_V` (the real
production view name is redacted — see
[../../../docs/sanitization-policy.md](../../../docs/sanitization-policy.md)).
Relevant columns:

| Column | Meaning |
|---|---|
| `LOCAL_TRANSACTION_ID` | Join key linking a book-out row to its book-in row |
| `TPARTNR` | Partner/goods-source code — distinguishes normal goods from dummy goods (see below) |
| `ARTNR` | Item/EAN identifier |
| `ZIEL` | Destination location/workstation code |
| `LAGBEZ` | Storage-location classification (e.g. `Overstock`, `SZROV`) |
| `LHMNR` | Load-carrier (tote/container) number |
| `MENGE` | Quantity — negative for book-out, positive for book-in |
| `CREATED` | Transaction timestamp |
| `CREATEDBY` | Operator who performed the transaction |
| `CUST_DATA` | JSON-encoded custom-data field — see below |
| `"SEQUENCE"` | Monotonic per-row sequence value (quoted because it's a reserved word in Oracle); the ordering basis for `ROW_NUMBER()` matching, `manual_sorting_logic.sql` only |

## Normal goods vs. dummy goods

`TPARTNR` splits every transaction into two categories that are reconciled with
different logic:

- **Normal goods** (`NORMAL_GOODS_SOURCE`, illustrative value `1` in this
  sanitized copy) — physical item movements. Book-out (`MENGE < 0`) and book-in
  (`MENGE = 1`) rows are matched with a plain `LEFT JOIN` on
  `LOCAL_TRANSACTION_ID`, because a given transaction ID reliably corresponds to
  exactly one book-out/book-in pair in this flow.
- **Dummy goods** (`DUMMY_GOODS_SOURCE_A`/`DUMMY_GOODS_SOURCE_B`, illustrative
  values `2`/`3`) — stock-adjustment transactions, not physical goods movement.
  In `normal_booking_logic.sql`, these are still matched with a plain ID join.
  In `manual_sorting_logic.sql`, the same dummy-goods category is matched with
  the stricter `ROW_NUMBER()` sequence join described below, because the manual
  sorting area is where the duplicate/out-of-sequence scan problem this query
  was written to fix actually occurs.

The partner-code values themselves (`1`/`2`/`3` in this sanitized copy) are
illustrative placeholders, not real production values — see
[../../../docs/sanitization-policy.md](../../../docs/sanitization-policy.md).

## JSON custom-data extraction (`CUST_DATA`)

`CUST_DATA` is a JSON-encoded CLOB column holding fields that aren't otherwise
columnized in the transaction-history view. Both queries extract individual
fields with Oracle's `JSON_VALUE(column, '$.FIELD_NAME')`, which returns a
scalar (string) pulled out of the JSON document by JSONPath, or `NULL` if the
path doesn't exist or the document isn't valid JSON at that path. Fields pulled
this way include:

| JSON path | Used for |
|---|---|
| `$.REFERENCENUMBER_LHM` | Reference load-carrier number, used in the `:ref_lhm_filter` bind-variable filter |
| `$.QUALITYID_SEKTOR` / `$.QUALITYID_ART` | Quality grade classification (mapped to A–D via `CASE`/`DECODE`) |
| `$.SORTABLE_ART` | Sortability flag — overrides quality grade B in an edge case (see `combined_transactions` CTE, `normal_booking_logic.sql`) |
| `$.CATEGORYID_ART` | Product category, mapped to a readable label via `DECODE` |
| `$.SOURCEID_SEKTOR` | Source channel, mapped via `DECODE` (this is where the sanitized `'Primary Channel'`/`'Partner Channel'` labels live) |
| `$.DISTRIBUTIONCHANNELID_ART` | Distribution channel, used to classify `Outlet` vs. `Overstock` |
| `$.SKU_ART` | SKU identifier |
| `$.SORTINGCRITERIAID_ART` | Sorting criteria code |
| `$.LASTEANGOTFROMMAUS_ZIEL` | Fallback EAN when the primary `ARTNR` value is unusable — see the 3-step EAN fallback below |

**Why extraction happens per-query, not once upstream:** the same `CUST_DATA`
document is read via different JSON paths depending on whether the row came
from the book-out leg (`t1_cust_data`) or the book-in leg (`t2_cust_data`), and
`COALESCE` is used to prefer one leg's value over the other depending on which
one populated that field for a given transaction (see the `Quality` and
`Category` `CASE`/`DECODE` expressions in `normal_booking_logic.sql`'s
`combined_transactions` CTE). Extracting once and joining flat columns would
lose that per-leg precedence.

## `ROW_NUMBER()` sequence matching (`manual_sorting_logic.sql`)

This is the query's central fix and the reason the file exists as a separate
query from `normal_booking_logic.sql`.

**The problem:** for dummy-goods transactions in the manual sorting area, a
single `LOCAL_TRANSACTION_ID` is not guaranteed to correspond to exactly one
book-out/book-in pair — the same ID can appear multiple times if an item is
scanned, rescanned, or re-sorted. A plain
`LEFT JOIN dummy_goods_t2 t2 ON t1.LOCAL_TRANSACTION_ID = t2.LOCAL_TRANSACTION_ID`
would cross-multiply every book-out row sharing that ID against every book-in
row sharing that ID — turning, for example, 2 real book-outs and 2 real
book-ins into 4 joined rows instead of 2, silently doubling the reported scan
count.

**The fix:** each side of the join is assigned an independent, per-transaction
sequence number before the join happens:

```sql
ROW_NUMBER() OVER (PARTITION BY hv.LOCAL_TRANSACTION_ID ORDER BY hv."SEQUENCE" ASC) as rn
```

This numbers every book-out row `1, 2, 3, ...` in the order it actually
occurred (by `"SEQUENCE"`) *within* each `LOCAL_TRANSACTION_ID` group, and does
the same independently for book-in rows. The join condition then becomes:

```sql
LEFT JOIN dummy_goods_t2 t2
    ON t1.LOCAL_TRANSACTION_ID = t2.LOCAL_TRANSACTION_ID
    AND t1.rn = t2.rn
```

This pairs the *first* book-out with the *first* book-in for that transaction
ID, the *second* with the *second*, and so on — a strict positional pairing in
event order, instead of a cardinality-exploding many-to-many join. It assumes
book-outs and book-ins happen in the same relative order on both sides (first
book-out completes before the second book-out begins, etc.); if that ordering
assumption is ever violated upstream, pairs could be matched to the wrong
partner without the query raising any error (see
[../README.md](../README.md#9-trade-offs) and
[limitations.md](limitations.md)).

**Why not `MATCH_RECOGNIZE` or an analytic window join instead:** Oracle's
`MATCH_RECOGNIZE` could express this pattern more declaratively, but
`ROW_NUMBER()` + equi-join was already the idiom used elsewhere in this file
family and keeps the query portable to a wider range of Oracle versions and
easier for another analyst to read without needing to learn a less commonly
used SQL feature — a deliberate trade-off, not an oversight (see
[decisions.md](decisions.md)).

## 3-step EAN fallback (`manual_sorting_logic.sql`, dummy-goods leg)

```sql
CASE
    WHEN t1.ARTNR LIKE '2%' THEN t1.ARTNR
    WHEN JSON_VALUE(t1.CUST_DATA, '$.LASTEANGOTFROMMAUS_ZIEL') IS NOT NULL
         THEN JSON_VALUE(t1.CUST_DATA, '$.LASTEANGOTFROMMAUS_ZIEL')
    WHEN t2.ARTNR LIKE '2%' THEN t2.ARTNR
    ELSE t1.ARTNR
END AS ARTNR
```

Barcode scans in the manual sorting area sometimes fail to resolve to a valid
EAN (in this schema, a valid EAN starts with `2`). The fallback tries, in
order: (1) the book-out row's own `ARTNR` if it looks like a valid EAN; (2) a
JSON-encoded "last known good EAN" field captured earlier in the item's
lifecycle; (3) the book-in row's `ARTNR` if *it* looks like a valid EAN; (4)
give up and use the book-out row's `ARTNR` as-is. This means a single damaged
or unreadable scan on one side of a transaction doesn't drop the row from the
report entirely, at the cost of the reported EAN sometimes coming from a
different physical scan event than the one being reported on.

## Output grain

Both queries emit **one row per matched book-out/book-in transaction pair** (or
per unmatched book-out, since the join is a `LEFT JOIN` — see
[failure-and-recovery.md](failure-and-recovery.md)). Neither query aggregates
beyond that grain; any further rollup (by shift, by employee, by date) is left
to the consumer.

## Known gaps

- `LOCAL_TRANSACTION_ID` uniqueness for the normal-goods flow is assumed, not
  verified — see the Validation table in [../README.md](../README.md#7-validation-evidence).
- The `ROW_NUMBER()` ordering assumption (book-outs and book-ins occur in the
  same relative sequence) is not asserted anywhere in the query itself.
- Neither query is schema-contract-tested against the live Oracle view — a
  column rename or type change would only surface at query-execution time.
