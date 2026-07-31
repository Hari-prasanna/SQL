# Data Contract

## Source (Oracle)

`sql/stock_balance_query.sql` reads from a generic alias `STOCK_BALANCE` (the real
production view name is redacted — see
[../../../docs/sanitization-policy.md](../../../docs/sanitization-policy.md)).
The query is parameterized on `:category` (e.g. `Beauty`, supplied as a job
widget/parameter default) and excludes rows whose `BEZ` (description/carrier)
column starts with `T` or `BSF_T` — internal prefixes marking non-sellable or
transit handling units that don't belong in the dangerous-goods stock view.

No explicit column list is projected — the query is `SELECT *`, and the Python
layer trims to a fixed 22-column window afterward (see below). This means the
contract with Oracle is "whatever columns the view currently returns, in the
current order," not a named, versioned column list.

## Transform

`clean_stock_dataframe()` in `src/etl_pipeline.py`:

1. Finds a `MAINLHM` column (case-insensitive) if present, and keeps only rows
   where its value starts with a digit — filters out handling-unit references
   that aren't numeric load-carrier IDs.
2. Trims the result to the **first 22 columns** (`iloc[:, :22]`), regardless of
   what those columns actually are. This is positional, not name-based — a
   column reordering upstream in Oracle would silently change what ends up in
   the Sheet without raising an error.
3. Fills remaining nulls with empty strings (Sheets-friendly, not
   `NaN`/`None`).

## Output grain — `JOIN` tab (Google Sheet)

One row per stock/handling-unit record returned by the query for the given
`category`, after the cleaning filter above. Written as a **full overwrite**
(`batch_clear(["A:V"])` then `update`) — not an idempotent per-date append like
[featured/01](../../01-clarification-automation)'s write. The Sheet represents
current stock state, so there's no "grain" beyond "one row per record as of the
last successful run."

## Output grain — `DG Stocks` calc tab (read-back)

This tab is **not written by Python** — it's a Sheet-formula tab that recomputes
derived columns from the freshly uploaded `JOIN` data. `etl_pipeline.py` waits 5
seconds (see [limitations.md](limitations.md)) and then reads it back with
`get_all_values()` to compute two numbers via `compute_volumes()`:

| Column (0-indexed) | Sheet column letter | Used for |
|---|---|---|
| 11 | L | The numeric volume figure (comma-formatted; parsed with `str.replace(',', '')`) |
| 5 | F | Category — must equal `OUTLET` to count toward "ready volume" |
| 1 | B | Location-type prefix — rows starting `OLAP` or `FIN` are excluded from "ready volume" |
| 14 | O | A code checked for a `50` prefix — must match to count toward "ready volume" |

`total_vol` sums column L across every row. `ready_vol` sums column L only for
rows where column F is `OUTLET`, column B does **not** start with `OLAP` or
`FIN`, and column O starts with `50`. These four conditions are kept exactly as
found in the source project — they're described here, not renamed to something
that implies a meaning this assistant can't confirm from the code alone (see
[../../../docs/sanitization-policy.md](../../../docs/sanitization-policy.md)).

## Output grain — `Block_dash` tab

A single cell (`C2`) is stamped with the run's local timestamp
(`DD/MM/YYYY HH:MM:SS`, Europe/Berlin). No other grain.

## What this data contract does not include

UN-number, hazard-class, or any regulatory classification field. Nothing in the
Oracle query, `clean_stock_dataframe()`, or `compute_volumes()` classifies a row
by hazard type — see [decisions.md](decisions.md) for why the README doesn't
claim that as part of this pipeline.

## Known gaps

- No named-column contract for the Oracle extract — a column reorder upstream
  would silently change what lands in columns 1–22 of the Sheet.
- No reconciliation between rows extracted and rows written (see
  [validation.md](validation.md)).
- The calc-tab column positions (B, F, L, O) are undocumented anywhere in the
  original source beyond a single inline comment (`# Calculate Total Vol (Index
  11 / Col L)`) — this table is this repository's best-effort reconstruction of
  that contract, not a verified spreadsheet schema.
