# Clarification Case Automation

A duplicate-entry elimination pipeline: employees at a large European e-commerce
fulfillment site were logging the same "clarification case" work twice — once in
the warehouse management system (WMS) and again by hand in a Google Sheet used for
team reporting. This project makes the WMS/Oracle data the single source of truth
and automates the reporting sheet, with a scheduled recovery window for late or
corrected data and a downstream Apps Script pipeline that reconciles automated and
manually-logged entries into the team's final reporting workbook.

## 1. Business Problem

Clarification cases ("Klärfälle" — inventory items needing manual review before
they can be booked back into stock) were tracked twice: once as a normal WMS
booking, and a second time by hand in a spreadsheet so team leads could see daily
counts. Manual double-entry meant:

- Recurring per-shift effort spent re-typing numbers that already existed in the WMS.
- Drift between the WMS and the reporting sheet whenever someone forgot, mistyped,
  or logged a case after the sheet had already been checked for the day.
- No systematic way to recover from a missed or corrected entry days later.

## 2. Users and Decisions Supported

- **Team leads / shift leads** use the daily clarification counts (by quality
  grade, workstation, and shift) to staff the clarification area and spot backlog
  building up.
- **The backlog webhook** gives anyone watching the team chat a same-day signal of
  how much unresolved clarification stock is sitting in the relevant storage zones,
  without needing to open a report.

## 3. Measured Impact

- Manual spreadsheet entry for this workflow was reduced by an estimated **~90%**,
  based on the original team's before/after comparison of manual line-entry volume
  (see [docs/validation.md](docs/validation.md) — this is a **manually validated,
  historical estimate reported by the operating team, not a re-derived or
  independently re-measured figure in this repository**).
- Eliminated the duplicate WMS-vs-spreadsheet entry step entirely for the automated
  portion of the workflow.
- Added idempotent per-date refresh so re-running a day never creates duplicate rows.

## 4. Architecture

```text
Oracle / WMS
  |
  v
Databricks job: clarification_bookings_task  ---->  Google Sheet (auto_raw tab)
  |                                                         |
  v                                                         v
Databricks job: backlog_clarification_webhook_task   Apps Script pipeline
  |                                                   (Config -> Utils -> Step1 ->
  v                                                    Step2 -> Step3 -> Menu ->
Chat notification (current backlog total)             Notifications -> Triggers)
                                                              |
                                                              v
                                                  Final team reporting workbook
```

Two independent trigger paths write to the same downstream reporting workbook: the
Databricks job refreshes the automated data on a schedule; the Apps Script pipeline
(run on a daily trigger or manually from a Sheets menu) reconciles that automated
data against manually-logged entries and rolls both into the final sheet.

## 5. Data Flow and Grain

1. `sql/clarification_booking.sql` extracts book-out/book-in transactions for the
   clarification workstations from the WMS transaction history, classifies each row
   into a quality grade (A–D) from JSON-encoded custom-data fields, and groups by
   **(date, shift, employee, workstation)**.
2. `src/clarification_bookings.py` runs that query for a UTC-converted shift window,
   then writes the result into the `auto_raw` tab, replacing only the rows for the
   target date (idempotent per-date refresh — see
   [docs/failure-and-recovery.md](docs/failure-and-recovery.md)).
3. `sql/backlog_clarification.sql` independently sums the current open clarification
   backlog from stock-balance data; `src/backlog_clarification_webhook.py` posts
   that single number to a chat webhook after Task 1 completes.
4. The Apps Script pipeline (`src/apps_script/`) runs later: it copies manually
   logged rows into `manual_raw`, merges `auto_raw` + `manual_raw` into a `KL_Auto`
   staging tab keyed by (date, email, task area), then aggregates that into the
   final reporting workbook.

## 6. Engineering Decisions

- **Oracle/WMS as source of truth, not the spreadsheet.** The pipeline reads from
  the WMS and writes to the sheet — never the reverse — so there's one place the
  data can drift from.
- **Idempotent per-date write, not append-only.** Re-running the job for a given
  date deletes and re-inserts only that date's rows, so backfills and retries
  can't create duplicates.
- **A configurable recovery window (default 5 days back), not a fixed one-shot
  run.** Clarification cases can be logged in the WMS a few days after the fact;
  the Apps Script layer's `LOOKBACK_DAYS_BACK` setting re-pulls that window so
  late/corrected data still lands in the reporting sheet.
- **Two independently schedulable Databricks tasks, not one monolith.** The backlog
  webhook depends on the main task but is a separate task with its own retry
  policy (`max_retries: 0` — a stale/duplicate backlog post is worse than a missed
  one), so a chat-notification failure can't block the sheet refresh from succeeding.
- **`logistics_data_utils` is installed as a package, not vendored via `sys.path`
  manipulation into a personal workspace directory** — see
  [decisions.md](docs/decisions.md) for why the original implementation used a
  hardcoded `/Workspace/Users/<email>/...` path and what changed here.

## 7. Validation Evidence

| Control | Purpose | Method | Status | Evidence |
|---|---|---|---|---|
| Idempotent rerun | Re-running a date doesn't duplicate rows | Delete-then-insert by target date before write | **Implemented** | `update_google_sheet_idempotent` call in `clarification_bookings.py`, matching on the date column |
| Late/corrected-data handling | Late WMS entries still reach the sheet | Configurable lookback window re-pulls recent dates | **Implemented** | `LOOKBACK_DAYS_BACK` in `apps_script/00_Config.js`; `days_back` in `config.example.json` |
| Failure notification | On-call/team is alerted when either task fails | Webhook POST on exception, with retry/backoff | **Implemented** | `send_failure_notification` in both `.py` files; `06_Notifications.js` for the Apps Script side |
| Business-key uniqueness (Apps Script merge) | No duplicate rows across manual/auto merge | Key-map built from date+email+task-area before upsert | **Implemented** | `01_Utils.js` key-map builder, used in `02_Step1...js` / `03_Step2...js` |
| Source/output row reconciliation | Row counts extracted vs. written match | — | **Unknown** | No logging or test found that compares extracted vs. written row counts; not implemented in the source project |
| Duplicate handling within a single run | Two rows for the same key in one extract don't create two sheet rows | — | **Unknown** | Not covered by any test in the source project; the idempotent write matches on date only, not a full business key |
| Missing-reference handling | Behavior when `ref_lhm_filter` bind values don't match anything | — | **Planned** | Query returns zero rows; no explicit handling or alerting differentiates "no work today" from "filter broken" |
| Schema-change regression | WMS column/type changes are caught before they break the query | — | **Unknown** | No schema contract test exists |
| Manual spot validation | Someone periodically checks the sheet against the WMS by hand | Ad hoc, by team leads | **Manually validated** (historical, not reproducible here) | Not documented in the source repo; carried forward from the original README's implied practice, not verified by this assistant |
| Recovery procedure | Documented steps to recover from a failed run | Rerun with `day=YYYY-MM-DD` job parameter | **Implemented** | `get_days_back` widget handling in `clarification_bookings.py`; documented in [failure-and-recovery.md](docs/failure-and-recovery.md) |

Synthetic-fixture unit tests were added in this refactor for the parts that don't
require live Oracle/Sheets access — see [tests/](tests/) and
[docs/validation.md](docs/validation.md) for exactly what they do and don't cover.

## 8. Failure and Recovery

See [docs/failure-and-recovery.md](docs/failure-and-recovery.md) for the full
runbook. Summary: both Databricks tasks post a chat notification on failure; the
main task is retried automatically (up to 2 retries) before alerting; the webhook
task is not retried at the job level (it has its own internal HTTP retry/backoff)
because a duplicate backlog post is a worse outcome than a missed one. Recovery for
a missed or wrong date is a manual re-run with an explicit `day` parameter.

## 9. Trade-offs

- The Apps Script reconciliation layer trades simplicity for reach: it lives inside
  the reporting spreadsheet itself, which non-engineers can trigger from a menu,
  but that also means its business logic is harder to unit test and version than
  the Databricks side.
- The 5-day lookback window is a fixed compromise, not a dynamically detected "how
  late can data really be" — it costs a small amount of repeated query volume every
  run in exchange for not having to detect late writes explicitly.
- The backlog webhook and the main sheet refresh are two separate tasks with
  different retry semantics; this adds a small amount of orchestration complexity
  in exchange for isolating a "nice to have" notification from the "must succeed"
  sheet refresh.

## 10. Sanitization Notes

This project touched real production identifiers more than any other in this
portfolio. See [docs/sanitization-report.md](../../docs/sanitization-report.md) and
[docs/sanitization-policy.md](../../docs/sanitization-policy.md) for the full
substitution table. In summary: employer name, employee email, workspace hostname,
secret-scope name, cluster policy ID, cost-allocation code, and internal
table/workstation codes were all replaced with placeholders or generic aliases;
none of them affect the shape of the query logic itself.

## 11. What I Would Improve Next

- Add a real source/output row-reconciliation check (compare Oracle extract row
  count to sheet rows written) instead of relying on idempotent-write correctness alone.
- Add a schema-contract test against the WMS extract so a column rename or type
  change fails loudly instead of silently breaking downstream quality classification.
- Move the Apps Script reconciliation logic's key business rules (the merge-key
  definition in particular) into a form that can be unit tested outside the
  Google Apps Script runtime.
