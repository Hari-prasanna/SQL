# logistics_data_utils

Shared connection, config, sheet-write, time-window, and notification helpers used
by the featured Databricks pipeline projects in this portfolio
([../../featured/01-clarification-automation](../../featured/01-clarification-automation),
[../../featured/02-dangerous-goods-data-product](../../featured/02-dangerous-goods-data-product)).

This is a straight extraction of a single shared `common_utils.py` module used
across the operator's Databricks pipelines, split into one file per responsibility.
**Business behavior was intentionally not changed in this refactor** — the one
deliberate exception is that `get_connections` now takes `secret_scope` as a
required parameter instead of a hardcoded scope name, since shipping a real scope
name publicly isn't possible (see
[../../docs/sanitization-policy.md](../../docs/sanitization-policy.md)).

## Install (editable, for local development)

```bash
pip install -e ".[dev]"
```

## Modules

| Module | Responsibility |
|---|---|
| `connections.py` | `get_connections` (Sheets/Oracle/webhook), `run_sql_file` |
| `config.py` | `load_config` — loads a JSON config from a project directory |
| `sheets.py` | `update_google_sheet_idempotent` — delete-then-insert-by-key sheet write |
| `time_windows.py` | `get_utc_window` — shift-window → UTC string conversion |
| `notifications.py` | `setup_logging`, `build_webhook_card`, `send_webhook_notification` |

Everything is re-exported from the package root, so existing call sites can use
`import logistics_data_utils as u; u.get_connections(...)`.

## Tests

```bash
pytest tests/
```

Tests are characterization tests written against the pre-split behavior — they use
an in-memory fake sheet object, a local SQLite engine, and mocked secrets/webhooks.
None of them require Oracle, Databricks, or live Google credentials.
