# Limitations

- **This was a one-off analysis tool, not a continuously scheduled
  production pipeline.** The source project's own README describes it as a
  "one-click" analysis "run over a bounded date range" via a spreadsheet
  menu or manual trigger — there is no time-based Apps Script trigger, no
  job scheduler, and no evidence in the source code of it running on a
  recurring cadence. Every claim in this project's docs about "a run"
  refers to a manual or menu-triggered execution, not a scheduled job.
- **No automated tests cover the majority of the pipeline logic.** Only the
  Step 3 archive-dedup helper (`selectNewUniqueRows`) is unit tested; Steps
  1, 2, and 4 are almost entirely `SpreadsheetApp` calls and spreadsheet
  formula strings that can't be exercised outside the Apps Script/Google
  Sheets runtime — see [validation.md](validation.md).
- **No schema/column-position contract.** Every formula addresses source
  columns by letter, not by header name. A column reorder in any of the
  three source logs would silently produce wrong results (or a visible
  Sheets error) rather than fail with a clear message.
- **No monitoring, alerting, or scheduled retry** — see
  [failure-and-recovery.md](failure-and-recovery.md). A failed or
  partially-completed run is only visible to whoever happens to open the
  spreadsheet or the Apps Script execution log.
- **The archive step's header-row edge case is a known, un-fixed
  quirk**, preserved intentionally during this sanitization pass rather
  than silently corrected — see [data-contract.md](data-contract.md) and
  [decisions.md](decisions.md).
- **The headline finding is correlational, not causal, and this repository
  does not attempt to close that gap.** No confounder-control analysis,
  controlled experiment, or formal statistical test was performed here or
  (as far as this repository's source material shows) by the original team
  — see the README's Measured Impact and Trade-offs sections.
- **Nine near-duplicate `COUNTUNIQUEIFS` formulas** implement the
  concurrent-transport congestion count instead of one parameterized
  calculation, which makes future changes to the WCS zone/status vocabulary
  more error-prone to apply consistently — see
  [../README.md#11-what-i-would-improve-next](../README.md#11-what-i-would-improve-next).
