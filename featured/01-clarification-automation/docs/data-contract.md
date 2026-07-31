# Data Contract

## Source (Oracle / WMS)

`sql/clarification_booking.sql` reads from a generic alias `TRANSACTION_HISTORY_V`
(the real production view name is redacted — see
[../../../docs/sanitization-policy.md](../../../docs/sanitization-policy.md)).
Relevant columns: `LOCAL_TRANSACTION_ID`, `ARTNR`, `ZIEL` (destination/workstation),
`CREATEDBY`, `LHMNR` (load-carrier number), `CREATED`, `MENGE` (quantity),
`CUST_DATA` (JSON-encoded custom fields — quality/sortability are read out of this
via `JSON_VALUE`).

Rows are split into **normal goods** (one partner code) and **dummy goods**
(a different partner code — used for stock adjustments rather than physical goods
movement), then matched book-out ↔ book-in on `LOCAL_TRANSACTION_ID` to determine
where an item ended up.

`WORKSTATION_1`–`WORKSTATION_4` are placeholder aliases for the four real
clarification workstation codes; the partner-code integers (`1`/`2`/`3` in the
sanitized query) are illustrative, not the real production values — see
[../../../docs/sanitization-policy.md](../../../docs/sanitization-policy.md).

`sql/backlog_clarification.sql` reads from a second generic alias `STOCK_BALANCE`
and sums quantity for rows matching either a specific storage-location/carrier-type
combination or a carrier-name prefix.

## Output grain

`auto_raw` tab: one row per **(date, shift, employee, workstation)**, with columns
`A`/`B`/`C`/`D` holding the summed quantity per quality grade. The write is
idempotent per **date** — an update deletes and re-inserts all rows for the target
date, not per (date, shift, employee, workstation) key. Two rows sharing a date but
differing only in shift/employee/workstation are both kept; the idempotency
guarantee is "re-running today doesn't duplicate today," not "this exact key is
globally unique across runs."

## Known gaps

- No explicit uniqueness constraint on the full (date, shift, employee,
  workstation) key is enforced by the write logic itself — it relies on the SQL
  `GROUP BY` producing at most one row per key, which has not been covered by a
  regression test in this repository.
- Late-arriving WMS data outside the 5-day lookback window is not automatically
  recovered — a manual re-run with an explicit `day` parameter is required.
