# Failure and Recovery

This tool has no automated failure handling, retry logic, or alerting — it
is a manually/menu-triggered analysis script, not a monitored production
job. Failures surface as spreadsheet formula errors or Apps Script
execution exceptions visible in the editor/execution log, to whoever ran it.

## Failure paths

| Failure | Detection | Response |
|---|---|---|
| A source tab was renamed or deleted | `spreadsheet.getSheetByName(...)` returns `null`; the next `.getRange(...)` call throws | Apps Script execution log shows a `TypeError` on a `null` sheet reference; run stops at that step |
| A `QUERY()`/`COUNTUNIQUEIFS()`/`XLOOKUP` formula's source range or filter no longer matches the source schema | Cell shows a Sheets error value (e.g. `#N/A`, `#VALUE!`, `#REF!`) | No automatic alert — visible only if someone opens the sheet and looks at the affected column |
| Step 1 or Step 2 is re-run without first running Step 4 (cleanup) | Staging sheets still have prior-run data mixed with new data | Formulas overwrite most staging cells, but stale rows beyond the new data's row count can persist; no explicit guard against this |
| Step 3 (archive) is re-run against unchanged `Step2Formulas` data | No error — dedup-by-key silently produces zero new rows | This is the intended, safe behavior (see `selectNewUniqueRows` and its tests) |
| `runAllScripts` fails partway through (e.g. Step 2 throws) | Apps Script execution log shows the exception and which step it occurred in | Steps already completed (e.g. Step 1) are not rolled back; sheets are left in a partially-updated state |

## Recovery procedure

1. **A step failed with an execution error**: open the Apps Script editor's
   execution log to identify which step and which line failed. Fix the
   underlying cause (renamed tab, changed source schema, malformed source
   data), then re-run from the failing step using the spreadsheet's custom
   menu (`Extract > Step N: ...`) rather than `runAllScripts`, to avoid
   re-running steps that already completed correctly.
2. **A congestion or duration column shows a Sheets error value**: check
   that the source range/status-literal filters in the corresponding
   formula (Step 1 or Step 2, in
   `src/order_transport_duration_analysis.js`) still match the current
   source tab's column layout and status vocabulary — there is no automated
   schema-drift detection for this (see
   [validation.md](validation.md)).
3. **Staging sheets look like they have leftover data from a prior run**:
   run `Step 4: Clean Up` first, then re-run from `Step 1`. Step 4 clears
   all staging and source tabs, so this is always a safe reset point,
   though it does mean any not-yet-archived Step 2/3 results should be
   confirmed as archived (or intentionally discarded) before running it.
4. **The `Summary` sheet appears to be missing expected orders after Step
   3**: this most likely means those order keys were already present in
   `Summary`'s column C from a prior run — check
   `selectNewUniqueRows`'s dedup-by-key behavior in
   [data-contract.md](data-contract.md) before assuming data was lost.

## What is not automated

There is no chat/email notification on failure, no scheduled retry, and no
reconciliation check comparing rows expected to rows actually archived.
Recovery is entirely a manual, menu-driven process performed by whoever is
running the analysis.
