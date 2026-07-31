# Limitations

- **No independent row-count reconciliation.** The pipeline trusts that the SQL
  extract and the idempotent write together produce the right rows; there is no
  separate check that compares "rows extracted from Oracle" to "rows present in
  the sheet after the write."
- **The 5-day recovery window is a fixed constant, not a detected value.** Data
  that arrives later than 5 days after the fact requires a manual backfill run.
- **The Apps Script reconciliation layer is untested.** It runs outside any CI or
  test harness available to this repository (Google Apps Script's runtime isn't
  mockable with standard Python/JS test tooling used here), so its merge-key logic
  is only as correct as its last manual review.
- **A related, newer redesign of this pipeline exists in the operator's private
  repository** (adds an additional data source and replaces the Apps Script
  reconciliation step with pure Python) but is out of scope for this portfolio and
  not represented here — see
  [../../../docs/reorganisation-plan.md](../../../docs/reorganisation-plan.md) for
  why it was excluded.
- **The ~90% manual-entry-reduction figure is a reported estimate**, not an
  independently re-derived measurement — see [validation.md](validation.md).
