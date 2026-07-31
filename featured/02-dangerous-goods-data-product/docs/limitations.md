# Limitations

- **No independent row-count reconciliation.** The pipeline trusts that the SQL
  extract and the full-tab overwrite together produce the right rows; there is no
  separate check that compares "rows extracted from Oracle" to "rows present in
  the Sheet after the write."
- **The 5-second sleep between writing raw data and reading back formula-derived
  columns is a fixed constant, not a detected value.** If the Sheet's formulas
  take longer than 5 seconds to recompute (larger extracts, Sheets API
  throttling, etc.), `total_vol`/`ready_vol` could be computed from a partially
  or fully stale calc tab, with no error raised.
- **No named-column contract with the Oracle source.** `SELECT *` plus a fixed
  `iloc[:, :22]` trim means a column reorder upstream would silently change what
  lands in the Sheet, without a schema check catching it.
- **The task-dependency `run_if` gap is disclosed but not verified.** This
  repository's bundle template fixes what looks like a real gap in the original
  job config (see [failure-and-recovery.md](failure-and-recovery.md)), but there
  is no access to the original workspace's job history to confirm the gap ever
  caused a missed alert in production, or that the fix behaves as expected
  against a real Databricks workspace.
- **No automated tests exist for the calc-tab column-position contract.** The
  mapping documented in [data-contract.md](data-contract.md) (columns B, F, L,
  O) is reconstructed from the original code's inline comments and logic, not
  from an authoritative spreadsheet schema this repository has access to.
- **UN-number/hazard-class classification and the "days difference" forecast
  described in the original dashboard narrative are not implemented, tested, or
  verifiable anywhere in this repository.** If they exist at all, they live in
  Sheet formulas or the Looker Studio report configuration — neither of which
  was available to this reorganisation. See [decisions.md](decisions.md).
- **The ~100-minutes/day manual-work-removed figure is a reported estimate**, not
  an independently re-derived measurement — see [validation.md](validation.md).
- **No dashboard screenshot is included** (per the 2026-07-31 decision recorded
  in [../../../docs/sanitization-policy.md](../../../docs/sanitization-policy.md)),
  so the dashboard's actual current appearance, exact column layout, and real
  numbers cannot be independently verified by a reader of this repository — only
  the prose description in the README and the Mermaid diagram in
  [architecture.md](architecture.md) are available.
