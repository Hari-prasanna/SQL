# Validation

See the validation table in [../README.md](../README.md#7-validation-evidence) for
the full control-by-control status. This page covers what the automated tests in
[../tests/](../tests/) actually exercise.

## What the tests cover

- `tests/unit/test_stock_cleaning.py` — `clean_stock_dataframe()`'s handling-unit
  regex filter and fixed 22-column trim, using synthetic in-memory DataFrames (no
  live Oracle call).
- `tests/unit/test_volume_calculation.py` — `compute_volumes()`'s total/ready
  volume boolean-mask logic, using a synthetic fixture of calc-tab rows
  (`tests/fixtures/sample_calc_rows.json`) shaped like `worksheet.get_all_values()`
  output. No live Google Sheets call.
- `tests/unit/test_notification_card.py` — the Chat card payload shape for both
  success and failure cases (`build_card()`), without making a network call.
- `tests/unit/test_secret_scope.py` — the `SECRET_SCOPE` environment-variable
  resolution and placeholder fallback, in both `etl_pipeline.py` and
  `notification_sender.py`.

## What is explicitly not covered

- No test connects to a real Oracle database, Databricks cluster, or Google
  Sheets/Chat API — none of those are available outside the operator's
  infrastructure, and this repository does not fabricate integration tests
  against them (see the root
  [SECURITY.md](../../../SECURITY.md) /
  [docs/portfolio-scope.md](../../../docs/portfolio-scope.md) for why).
- The `run_if: ALL_DONE` fix in `config/databricks.bundle.example.yml` is not
  tested here — Databricks Jobs task-dependency behavior can't be exercised
  outside a real workspace. It's disclosed as **Planned**, not **Implemented**,
  in the README's validation table for exactly that reason.
- UN-number/hazard-class classification and the "days difference" forecast
  described in the source dashboard narrative have no tests here because they
  have no implementation here — see [decisions.md](decisions.md).
- The ~100-minutes/day manual-work-removed figure quoted in the README is the
  operating team's own historical estimate, not something re-derived from data
  in this repository — it is reported, not measured here.
- The Sheet-formula sync wait (`time.sleep(5)`) and the calc-tab's actual column
  contract are not covered by any test — there is no way to exercise Google
  Sheets recalculation timing from a synthetic fixture; this is recorded as a
  **Planned** gap in [limitations.md](limitations.md), not silently skipped.
