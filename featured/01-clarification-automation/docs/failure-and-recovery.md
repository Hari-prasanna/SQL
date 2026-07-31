# Failure and Recovery

## Failure paths

| Failure | Detection | Response |
|---|---|---|
| `clarification_bookings_task` raises an exception | Databricks job retry (max 2) exhausted | `send_failure_notification` posts to the default chat webhook; job marked failed |
| `backlog_clarification_webhook_task` raises an exception | No job-level retry (`max_retries: 0`) | Job marked failed; no further chat post is attempted (avoids posting a stale/duplicate total) |
| Chat webhook POST fails (5xx) | HTTP error caught in `post_webhook` | Exponential backoff, up to 3 retries, before giving up |
| Chat webhook POST fails (4xx) | HTTP error caught in `post_webhook` | No retry — treated as a permanent failure (e.g. bad URL/auth), logged and returned as failure |
| Apps Script pipeline step fails | Uncaught exception in the orchestrator | `06_Notifications.js` posts a failure card with remediation steps to the team's chat space |

## Recovery procedure

1. **Missed or wrong date in `auto_raw`**: re-run `clarification_bookings_task`
   manually with an explicit date —
   `databricks bundle run clarification_automation --target dev --python-params '["--day", "YYYY-MM-DD"]'`.
   The write is idempotent per date, so this is safe to repeat.
2. **Late-arriving WMS data outside the lookback window**: same as above — the
   `day` parameter re-pulls that specific date's shift window regardless of how old
   it is; the automatic 5-day lookback only covers *recent* days without manual
   intervention.
3. **Backlog webhook posted 0 or looks wrong**: check that the storage-location and
   carrier-type filters in `sql/backlog_clarification.sql` still match current WMS
   naming — this query has no automated regression test against schema drift
   (see [validation.md](validation.md)).
4. **Apps Script pipeline out of sync with `auto_raw`**: run
   `Klärfall Pipeline > Run full sequence` from the reporting workbook's custom
   menu, then check the Apps Script execution log for the failing step.

## What is not automated

There is no automatic retry of the Apps Script pipeline itself, and no automatic
reconciliation between the Databricks-written `auto_raw` tab and the final
reporting workbook beyond what the Apps Script pipeline does on its own schedule —
recovery there is currently a manual menu action.
