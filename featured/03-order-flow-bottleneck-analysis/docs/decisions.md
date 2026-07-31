# Engineering Decisions

## Why `config/` has no config file

The target project layout in this portfolio includes a `config/` directory,
and other featured projects ship a `config.example.json`/`.yml` there. This
project doesn't, because its actual source code doesn't load any external
runtime configuration — every setting (sheet names, WCS status literals, the
order-carton ID prefix) is a hardcoded constant inside
`src/order_transport_duration_analysis.js` (`CONFIG`, `TRANSPORT_STATUS`,
`ORDER_CARTON_ID_PREFIX`). That was true of the original script too — it was
a one-off analysis tool bound directly to one spreadsheet, not a
parameterized job meant to run against different targets.

Shipping a `config.example.json` here would misrepresent what the code
actually does (per this portfolio's rule against fabricating capabilities
that don't exist in the source). If this were reworked into a reusable
tool, externalizing `CONFIG.SHEET_NAMES` into a real config file would be a
reasonable first step — see [limitations.md](limitations.md) — but that
rework hasn't happened, so `config/` stays empty rather than shipping a file
with nothing real behind it.

## Why `sql/` has no separate SQL files

Unlike the Databricks-based featured projects, this script has no Oracle/SQL
component at all — every query against the three source logs is a
spreadsheet-native `QUERY()`/`COUNTUNIQUEIFS()`/`XLOOKUP` formula
constructed as a JS template literal and written directly into a cell via
`setFormula()`. These formula strings are inseparable from the
`SpreadsheetApp` calls that place them (they reference sheet ranges like
`${SHEETS.TRANSPORT_LOG}!A1:G`, not a standalone queryable data source), so
splitting them into a `sql/` directory would create files that can't run or
be validated on their own and would misrepresent the project as more
SQL-centric than it is. This is a deliberate, documented deviation from the
general portfolio template, not an oversight — consistent with how
`featured/01-clarification-automation/docs/decisions.md` documents its own
deliberate deviation (JSON config kept instead of YAML, because that's what
the real loader does).

## Why the sheet-name and status-literal sanitization is narrower than in other featured projects

This was the lowest-risk source project in the whole portfolio audit — no
company name, employee PII, hostnames, or secrets were found anywhere in the
original script (see
[../../../docs/reorganisation-plan.md](../../../docs/reorganisation-plan.md),
"featured/03-order-flow-bottleneck-analysis" section). The only identifiers
worth changing were:

- The five `CONFIG.SHEET_NAMES` values, which were internal report/tab
  titles in German.
- Four WCS transport-status literal strings used inside `QUERY()` filter
  conditions (`Transportrequest erledigt`/`erstellt`/`gestartet`,
  `Finalisierung gestartet`) — genericized to a `TRANSPORT_STATUS` constants
  object so the same English vocabulary is used consistently everywhere the
  status appears (Step 1 and Step 2), rather than genericizing only the two
  literals explicitly called out and leaving `'Transportrequest gestartet'`
  in German in Step 2 — that inconsistency would have made the redaction
  easy to reverse-engineer by comparison.
- One carton-ID `LIKE`-prefix filter, genericized to
  `ORDER_CARTON_ID_PREFIX`.

The many WCS zone/movement-type literals used inside Step 2's
`COUNTUNIQUEIFS` formulas (`AKL`, `AKL_G`, `PALL`, `PALLPZU`, `ZU`, `VD`,
`GS`, `OL`, `Outletbehälter`, `Versandkarton`) were deliberately **left
unchanged**. These are generic German-language warehouse-automation zone and
movement-type abbreviations used broadly across WCS systems, not identifiers
unique to one employer or one vendor — the same reasoning
[../../../docs/sanitization-policy.md](../../../docs/sanitization-policy.md)
applies to keeping generic Oracle/WMS column names as-is elsewhere in this
portfolio. Genericizing every one of these values would also have made the
Step 2 formulas harder to follow without reducing identifiability.

## Why `selectNewUniqueRows` was extracted

`runStep3_ArchiveResults`'s dedup loop was the one piece of this script's
logic that doesn't touch `SpreadsheetApp` beyond reading/writing whole
arrays — it operates on plain JS arrays and a `Set`. Pulling it into a
standalone function made it possible to add real unit tests
(`tests/unit/archive.test.js`) without needing the Apps Script runtime,
following the same "characterization test before/instead of rewriting
behavior" approach used for `shared/logistics_data_utils` elsewhere in this
portfolio. The extraction is behavior-preserving — including the header-row
edge case (see [data-contract.md](data-contract.md)) — not a rewrite. A
guarded `module.exports` block at the end of the file makes the same file
loadable by Node for tests while remaining a valid, unmodified-behavior
single-file Apps Script project (the export block is a no-op inside the
Apps Script V8 runtime, where `module` is undefined).
