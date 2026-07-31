# Validation

See the validation table in [../README.md](../README.md#7-validation-evidence) for
the full control-by-control status. This page covers what the automated tests in
[../tests/](../tests/) actually exercise.

## What the tests cover

- `tests/unit/test_idempotent_write.py` — synthetic-fixture test of the
  delete-then-insert-by-date merge logic used for the `auto_raw` write, using an
  in-memory fake sheet object (no live Google Sheets call).
- `tests/unit/test_utc_window.py` — date/shift-window calculation for a given
  `days_back` value, using the shift config shape from `config.example.json`.
- `tests/unit/test_notification_payload.py` — the chat-notification JSON payload
  shape for both success and failure cases, without making a network call.

## What is explicitly not covered

- No test connects to a real Oracle database, Databricks cluster, or Google
  Sheets/Chat API — none of those are available outside the operator's
  infrastructure, and this repository does not fabricate integration tests against
  them (see the root [SECURITY.md](../../../SECURITY.md) /
  [docs/portfolio-scope.md](../../../docs/portfolio-scope.md) for why).
- The ~90% manual-entry-reduction figure quoted in the README is the operating
  team's own historical before/after comparison, not something re-derived from
  data in this repository — it is reported, not measured here.
- The Apps Script reconciliation logic (`src/apps_script/`) has no automated tests
  in this repository — Apps Script's `SpreadsheetApp`/`PropertiesService` runtime
  is not mockable with the tooling used here. This is recorded as a **Planned**
  gap, not silently skipped.
