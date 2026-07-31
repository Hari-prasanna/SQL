# Data Contract

## Sources

All three sources are spreadsheet tabs populated by an external OLAP export
process outside this script's scope (the script only reads them via
`QUERY()` once they exist — it does not populate them).

| Source (`CONFIG.SHEET_NAMES` key) | Represents | Columns referenced |
|---|---|---|
| `TRANSPORT_LOG` | Every automated (WCS/AKL) transport movement, facility-wide | `A` (transport ID), `B` (movement description, filtered `LIKE 'Versand%'`), `C` (status — see below), `E` (zone/type code), `F` (movement direction/type code), `F` also used for an order-carton ID prefix filter, `G`/`H`/`I` (timestamps) |
| `ORDER_STATUS_LOG` | Order status change events, including finalization | `A`/`B` (order key + status), `C` (order type, filtered to `'OUTLET'`), `D`/`E`/`F` (carton count and related fields) |
| `WORKSTATION_SCAN_LOG` | Carton scans at palletization workstations | `A` (order key), `C` (filtered `LIKE '4%'`), `F`, `S` (order type, filtered `'OUTLET'`), `X`, `B` (filtered `<> 'Deleted'`) |

## WCS status vocabulary (`TRANSPORT_STATUS`)

The source WCS export encodes transport lifecycle as free-text status
values. This project reads (and, for `ORDER_STATUS_LOG`, filters on) four
of them:

- `TRANSPORT_STATUS.CREATED` — a transport request was created.
- `TRANSPORT_STATUS.STARTED` — a transport request began moving.
- `TRANSPORT_STATUS.COMPLETED` — a transport request finished.
- `TRANSPORT_STATUS.FINALIZATION_STARTED` — an order entered its
  finalization phase (used against `ORDER_STATUS_LOG`, not `TRANSPORT_LOG`).

These are sanitized placeholders for the real German status strings in the
source system — see
[../../../docs/sanitization-policy.md](../../../docs/sanitization-policy.md).
The *filter logic* (which status marks which lifecycle point) is unchanged.

## Order-carton identification

`TRANSPORT_LOG` rows are further filtered by `ORDER_CARTON_ID_PREFIX`, a
`LIKE`-prefix match on column `F`, to isolate order-driven transports (used
for the initial wait-time calculation in Step 1) from the routine/background
transports counted separately in Step 2's congestion formulas. The real
production prefix is not shown; `ORDER_CARTON_ID_PREFIX` in
`src/order_transport_duration_analysis.js` is an illustrative placeholder.

## Output grain

`Step2Formulas` (Step 2 output) and `Summary` (Step 3 archive): **one row
per unique order key** (column `C`), derived from `UNIQUE(QUERY(...))` over
the `AF` staging sheet. Per order key, the row carries:

- Initial wait and total processing duration (time deltas).
- Two independently-looked-up carton counts and their respective
  duration-per-carton rates.
- Nine congestion counts (columns `S`–`AA`), each a
  `COUNTUNIQUEIFS` over `TRANSPORT_LOG` for a distinct
  concurrent-transport zone/type/status combination within the order's
  active window.
- A shift-bucket flag (1 or 2).

## Known gaps

- **The Step 3 archive scan includes row index 0 (the header row) as a
  candidate row**, not just data rows. `selectNewUniqueRows` (see
  `src/order_transport_duration_analysis.js` and
  `tests/unit/archive.test.js`) preserves this exactly as the original
  script behaved: if a header row is non-empty and its column-C value isn't
  already in the target sheet's key set, it gets archived like any other
  row. This was not "fixed" during sanitization because doing so would
  silently change historically-produced behavior without any way to verify
  the change against the original spreadsheet — see
  [decisions.md](decisions.md).
- **No schema/column-position contract is enforced.** Every formula
  addresses source columns by letter (`A`, `B`, `C`, ...), not by header
  name — a column reorder in any of the three source tabs would silently
  break the analysis rather than fail loudly.
- **No explicit type/format validation** on the source data (e.g. that
  column `G`/`H`/`I` timestamps in `TRANSPORT_LOG` are well-formed) — a
  malformed timestamp would surface as a spreadsheet formula error (e.g.
  `#VALUE!`) at analysis time, not as an upstream data-quality alert.
