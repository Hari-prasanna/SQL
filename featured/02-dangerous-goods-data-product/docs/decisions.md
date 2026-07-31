# Engineering Decisions

## Why two source projects were merged into one featured case study

The source material for this project comes from two places in the original
repository: `oracle-to-looker-etl` (all the code — the Oracle extract, the Pandas
clean, the Sheet write, and the Chat notifier) and `dg-compliance-pipeline` (a
README-only project describing the downstream Looker Studio dashboard and a
screenshot). There was no code to merge from the second project — it contributed
narrative and one image. Rather than create a second, near-empty featured project
that just links back to this one, the dashboard narrative was folded into this
README's Business Problem, Users, and Architecture sections, and the screenshot
was dropped entirely (see below). [docs/architecture.md](architecture.md) and
[docs/data-contract.md](data-contract.md) are explicit about which parts of the
merged narrative are actually backed by code in this repository and which are
not.

## Why no dashboard screenshot is included

The original `dg-compliance-pipeline/images/dg-monitor.png` is a real dashboard
screenshot — it could show real stock volumes, real hazard-class breakdowns, or
other operationally identifying detail that a text sweep can't verify. Per the
user's 2026-07-31 decision recorded in
[../../../docs/reorganisation-plan.md](../../../docs/reorganisation-plan.md) and
[../../../docs/sanitization-policy.md](../../../docs/sanitization-policy.md), no
screenshot from any source project was carried into the public repository. The
dashboard's shape and drill-down behavior are described in prose (README section
1–4) and the Mermaid diagram in [architecture.md](architecture.md) instead. The
`assets/` folder in this project is intentionally empty, ready if redacted images
are supplied later.

## Why the README doesn't claim UN-number/hazard-class classification or a "days difference" forecast

`dg-compliance-pipeline/README.md` (the narrative-only source) described the
dashboard as applying "UN-number classification" and computing a "days
difference" (DD) forecast metric to flag items approaching a storage-time limit.
**Neither of those exists anywhere in the committed Python** in
`oracle-to-looker-etl`. The actual code (`etl_pipeline.py`) does exactly three
things to the data: filters by category (an Oracle bind parameter), filters rows
by a handling-unit regex (`clean_stock_dataframe`), and computes two volume sums
from boolean masks over specific Sheet columns (`compute_volumes`). There is no
UN-number lookup, no hazard-class mapping, and no date-difference/forecast
calculation in this repository.

This project's README, architecture doc, and validation table are written to
reflect that directly: classification and forecasting are described as
happening — if they happen at all — in the Sheet's own formulas or in the Looker
Studio report configuration, both of which are outside this repository and were
never available to sanitize or verify. The validation table marks both controls
**Unknown — not present in this codebase** rather than inventing a status that
would imply this pipeline's Python does something it doesn't. This is a direct
application of this portfolio's no-fabricated-capabilities rule.

## Why the Sheet write is a full overwrite, not an idempotent per-date append

[featured/01](../../01-clarification-automation) appends and de-duplicates by
date because it's building a historical log (clarification bookings per day).
This pipeline's `JOIN` tab represents **current** dangerous-goods stock — there is
no "which date" question, because a new run simply supersedes the last one. The
original `etl_pipeline.py` already did this via `batch_clear` + `update`, and
that behavior was preserved as-is rather than converted to the
`logistics_data_utils.update_google_sheet_idempotent` helper used elsewhere in
this portfolio, because that helper's date-match semantics don't apply to a
current-state tab and forcing them in would have changed what actually gets
written.

## Why `logistics_data_utils` is used for some things and not others

`get_connections`, `run_sql_file`, `load_config`, and `setup_logging` from
[shared/logistics_data_utils](../../../shared/logistics_data_utils) are reused here
because they do exactly what this pipeline's original inline code did — connect
to Oracle/Sheets, run a parameterized SQL file, load a JSON config, and set up
logging with the same Py4J-noise suppression. The Sheet-write logic, the volume
masking, and the Google Chat card layout were **not** moved onto the shared
package's generic equivalents (`update_google_sheet_idempotent`,
`build_webhook_card`) because those generic helpers implement different
behavior — a date-keyed idempotent write and a plain pass/fail card — and this
pipeline's actual behavior (full overwrite; a rich metrics-and-buttons card) is
materially different. Forcing reuse there would have either changed what the
code does or required misrepresenting the shared helper's actual shape.

## Why widget/secret resolution moved into `main()`

The original `etl_pipeline.py` and `notification_sender.py` called
`dbutils.widgets.text(...)` at module import time, which made both files
unimportable (and therefore untestable) outside a live Databricks notebook
context. Both files now resolve `dbutils` via a small `resolve_dbutils()` helper
and read widgets from inside `main()`, matching the pattern already established
in [featured/01](../../01-clarification-automation)'s entry points. The pure
functions (`clean_stock_dataframe`, `compute_volumes`, `build_card`,
`get_secret_scope`) have no dependency on `dbutils` at all and are what
[tests/](../tests) actually exercises.

## Why the secret scope is an environment variable, not a config field

`featured/01-clarification-automation/src/backlog_clarification_webhook.py`
already established the pattern used here:
`os.environ.get("SECRET_SCOPE", "<SECRET_SCOPE>")`. This project follows the
same convention (wrapped in a small `get_secret_scope()` function in both entry
points so it can be unit-tested with a monkeypatched environment variable,
instead of bound once at import time) rather than inventing a second,
config-file-based way to supply the same value.

## Why the task-dependency `run_if` gap was fixed in the template, not silently carried forward

While tracing the failure-handoff logic, this project's original
`databricks.yml` was found to declare `Notify_Task`'s `depends_on: [ETL_Task]`
with no explicit `run_if`. Databricks Jobs defaults task-dependency conditions to
`ALL_SUCCESS`, which means `Notify_Task` — the only task with any failure-alerting
logic — would not run at all when `ETL_Task` raised an exception. The original
source README's own troubleshooting section only describes "ETL succeeded but the
Chat card never arrived," never "ETL failed and no alert arrived," which is
consistent with this gap having gone unnoticed rather than intentionally accepted.

`config/databricks.bundle.example.yml` sets `run_if: ALL_DONE` explicitly, with an
inline comment explaining why, rather than reproducing the same gap in the public
template. This is disclosed as a **fix applied here, not verified against the
original production job** (see the README's Validation Evidence table and
[failure-and-recovery.md](failure-and-recovery.md)) — this repository has no way
to confirm the original job's actual behavior in production, only what the
committed YAML implies.

## Why configuration ships from `config/` but loads from `src/`

`etl_pipeline.py` and `notification_sender.py` both call
`logistics_data_utils.load_config(base_dir=PROJECT_DIR)`, where `PROJECT_DIR` is
`src/`. `config/config.example.json` in this repository is the shape to copy —
locally, `cp config/config.example.json src/config.json` before running either
script. This mirrors [featured/01](../../01-clarification-automation)'s code
pattern (`PROJECT_DIR = str(Path(__file__).resolve().parent)` +
`load_config(base_dir=PROJECT_DIR)`), which separates the shipped `config/`
example from the runtime `src/config.json` the same way, even though that
project's own README doesn't spell out the copy step explicitly either — noted
here so this project's setup instructions aren't silently missing it.
