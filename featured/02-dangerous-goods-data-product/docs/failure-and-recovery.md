# Failure and Recovery

## Failure paths

| Failure | Detection | Response |
|---|---|---|
| `ETL_Task` raises an exception (e.g. Oracle returns 0 rows, connection error, Sheet write error) | Caught in `main()`'s `try`/`except` | `taskValues` set to `status=FAILURE` with the error message, then the exception is re-raised so Databricks marks the task failed |
| `ETL_Task` fails and `Notify_Task` needs to alert on it | **Depends on the job's task-dependency condition** | See "The `run_if` gap" below — in the original job config, this may not have worked at all |
| `Notify_Task` raises an exception (e.g. bad webhook URL, Chat API rejects the payload) | `requests.exceptions.HTTPError` / generic `except` in `main()` | Logged and re-raised; no job-level retry (`max_retries: 0`) — a duplicate/stale notification is treated as worse than a missed one |
| Chat webhook POST is rejected (4xx/5xx) | `response.raise_for_status()` in `send_card()` | Exception propagates; `Notify_Task` fails; no built-in retry/backoff in this pipeline (unlike `featured/01`'s `backlog_clarification_webhook.py`, which has explicit exponential backoff) |
| Sheet formulas haven't finished recomputing when the calc tab is read back | Not detected — `time.sleep(5)` is a fixed wait, not a poll | Silent risk of reading stale/partial `total_vol`/`ready_vol`; see [limitations.md](limitations.md) |

## The `run_if` gap

The original `oracle-to-looker-etl/databricks.yml` declared:

```yaml
tasks:
  - task_key: ETL_Task
    notebook_task:
      notebook_path: ./src/etl_pipeline.py
  - task_key: Notify_Task
    depends_on:
      - task_key: ETL_Task
    notebook_task:
      notebook_path: ./src/notification_sender.py
```

`depends_on` with no `run_if` defaults to `ALL_SUCCESS` in Databricks Jobs. That
means if `ETL_Task` raised an exception, `Notify_Task` — the only task in this job
with any failure-alerting logic — would likely **not have run at all**, and no
Chat card (success or failure) would have been posted. The source README's own
Troubleshooting section only documents "the ETL succeeded and the notifier
failed," never "the ETL failed and nothing arrived," which is consistent with
this being an unnoticed gap rather than an intentional trade-off.

`config/databricks.bundle.example.yml` in this repository sets
`run_if: ALL_DONE` explicitly on `Notify_Task`'s dependency, with an inline
comment. This is a **fix applied in the public template**, not a verified
correction of the original production job's behavior — this repository has no
access to the original workspace's job run history to confirm whether the gap
ever actually caused a missed alert. See
[decisions.md](decisions.md#why-the-task-dependency-run_if-gap-was-fixed-in-the-template-not-silently-carried-forward)
for the full reasoning, and the README's Validation Evidence table for how this
control is scored (**Planned**, not **Implemented**, because it's unverified
against the real system).

## Recovery procedure

1. **A run failed and the Sheet wasn't updated**: re-run `ETL_Task` manually —
   `databricks bundle run dangerous_goods_data_product --target dev`. The full
   overwrite means a successful re-run fully replaces whatever partial/stale
   state was left behind; there's no "which date" parameter to supply, unlike
   [featured/01](../../01-clarification-automation).
2. **Chat card never arrives but the Sheet updated**: `ETL_Task` succeeded and
   `Notify_Task` failed or didn't run — check the secret scope's
   `chat_webhook_url` value and `Notify_Task`'s logs directly in the Databricks
   UI (the chat channel itself won't show this failure).
3. **Volumes look wrong (total/ready)**: check whether the calc tab had finished
   recomputing before it was read back (the 5-second sleep is a known fragile
   point) before assuming the boolean-mask logic in `compute_volumes()` is at
   fault.
4. **Dashboard looks stale**: confirm the job actually ran (it ships `PAUSED` on
   `dev`) and that the dashboard's data source still points at the `sheet_id` in
   `src/config.json`.

## What is not automated

There is no automatic retry/backoff on the Chat webhook POST in this pipeline
(contrast with `backlog_clarification_webhook.py` in featured/01, which has
explicit exponential backoff), no automatic recovery from a mid-run failure
between clearing and rewriting the upload tab, and no automated check that the
Sheet's formulas actually finished recomputing before the calc tab is read.
