# Clarification Bookings

Nightly + mid-shift job that aggregates clarification-case ("Klärfall") bookings from Oracle/WMS into Google Sheets, then a scheduled Apps Script pipeline rolls that up into the team's manual reporting workbook. Runs Mon–Fri at 14:40 and 23:40 CET.

---

## Business Problem

Employees previously had to record clarification case work twice:

1. Book the activity in WMS.
2. Manually enter the same result into a Google Sheet for reporting.

This created duplicate effort, delay, and risk of inconsistent reporting.

## Solution

The pipeline uses Oracle/WMS data as the source of truth and automatically feeds the Google Sheets reporting layer. A second Databricks task posts the current clarification backlog total to Google Chat, and an Apps Script pipeline reconciles the automated data against manually-logged entries into the team's final Taskmanager sheet.

## Impact

- Reduced manual Google Sheet entry effort by ~90%.
- Removed duplicate entry between WMS and reporting sheets.
- Improved reporting consistency for team leaders.
- Added idempotent refresh logic to prevent duplicate rows.
- Added scheduled recovery window for late or corrected data.

---

## Architecture

```text
Oracle / WMS
  ↓
Databricks Asset Bundle (clarification_bookings, backlog_clarification_webhook)
  ↓                                   ↓
Google Sheets: auto_raw          Google Chat (backlog total)
  ↓
Apps Script scheduled orchestration (00_Config … 07_Triggers)
  ↓
KL_Auto staging table
  ↓
LUU-QM Taskmanager final reporting sheet ("01.10.2021" form-response tab)
```

See [docs/architecture.md](docs/architecture.md) and [docs/data-flow.md](docs/data-flow.md) for the full breakdown.

---

## Files

| File | Purpose |
|---|---|
| `databricks.yml` | Bundle definition — schedule, cluster, two-task job |
| `src/clarification_bookings.py` | Task 1 — Oracle → `auto_raw` sheet, idempotent per-day refresh |
| `src/clarification_booking.sql` | Oracle query for clarification bookings (bind params: `:start_datetime`, `:end_datetime`, `:ref_lhm_filter`) |
| `src/backlog_clarification_webhook.py` | Task 2 — runs after Task 1, posts the current backlog total to Google Chat |
| `src/backlog_clarification.sql` | Oracle query for the current open backlog total |
| `src/config.template.json` | Copy to `config.json` (gitignored) — sheet ID, shift windows, SQL/webhook config |
| `apps-script/` | Google Apps Script project — see [apps-script/README.md](apps-script/README.md) |
| `docs/` | Architecture, data flow, runbook, failure-handling notes |

---

## Config (`src/config.json`)

Copy `src/config.template.json` → `src/config.json` and fill in your Sheet ID:

```json
{
  "google_sheet": { "sheet_id": "<TARGET_GOOGLE_SHEET_ID>", "upload_tab": "auto_raw" },
  "shift_settings": { "timezone": "Europe/Berlin", "shifts": [...] },
  "file_paths": { "sql_query": "clarification_booking.sql", "backlog_query": "backlog_clarification.sql" },
  "run_settings": { "days_back": 0 },
  "webhook_settings": {
    "backlog_clarification": {
      "secret_key": "backlog_clarification_webhook_url",
      "secret_scope": "luu_qm_secrets",
      "retry_config": { "max_retries": 3, "initial_backoff_seconds": 1.0 }
    }
  }
}
```

To backfill a specific date, pass `day=YYYY-MM-DD` as a job parameter when triggering `clarification_bookings` manually.

---

## Deploy & Run

```bash
cd clarification-bookings

# Validate YAML
databricks bundle validate --target dev

# Deploy to dev
databricks bundle deploy --target dev

# Trigger manually
databricks bundle run clarification_bookings --target dev
```

To test a specific date:

```bash
databricks bundle run clarification_bookings --target dev --python-params '["--day", "2025-06-15"]'
```

---

## Secrets

Scope: `luu_qm_secrets`

| Key | Used for |
|---|---|
| `google_auth` | Google Sheets service account |
| `oracle_auth` | Oracle DB connection |
| `chat_webhook_url` | Default failure alert channel |
| `kf_audit_chat_url` | Backlog total channel (falls back to `chat_webhook_url` if unset) |
| `backlog_clarification_webhook_url` | Configured via `webhook_settings.backlog_clarification.secret_key` |

Apps Script side stores its own values as **Script Properties** (`PIPELINE_TOKEN_PROPERTY`, `CHAT_WEBHOOK_URL_PROPERTY`) — never hardcoded in `.js` source. See [apps-script/README.md](apps-script/README.md).

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Duplicate rows in `auto_raw` | Job is idempotent — re-run will delete existing rows for that date and re-insert |
| Backlog webhook posts 0 | Check `backlog_clarification.sql` filters (`Lager`/`MainLhmdef`/`MainLhm`) still match current WMS naming |
| No rows returned from main query | Check `:start_datetime` / `:end_datetime` UTC conversion; confirm `ZIEL` values in `clarification_booking.sql` still match the active workstations |
| Apps Script pipeline out of sync | Run `Klärfall Pipeline > Run full sequence` from the Taskmanager sheet menu; check Apps Script executions log |
| `doPost` returns 401/Unauthorized | Script Property `PIPELINE_TOKEN_PROPERTY` missing or token mismatch between Databricks caller and Apps Script project
