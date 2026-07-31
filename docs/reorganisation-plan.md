# Reorganisation Plan — Curated Logistics Data Portfolio

> ⚠️ **Internal review document — do not publish verbatim.** This plan names real
> values (employer/site name, employee email, real secret scope, real Sheet IDs,
> real cluster policy ID and cost-allocation code) so the reorganisation could be
> audited against the actual source repository. Exclude this file from the public
> copy, or rewrite it to reference categories instead of literal values, before
> publishing — see [reorganisation-summary.md](reorganisation-summary.md).

Status: **Reorganisation executed on this branch; not yet committed or pushed.**
Branch: `refactor/curated-logistics-data-portfolio` (created from `Hari`, not `main`).

This document is the required first deliverable of the reorganisation. It records the
current repository structure, the proposed target structure, sanitization risks
discovered during inventory, and the items that need a manual decision before work
proceeds. No `git mv`, edit, or deletion has happened yet.

## ⚠️ Git history warning (required by task rule 9)

**When this content is copied into the new public repository
(`logistics-data-case-studies`), do NOT carry over this repo's Git history.**
Every commit currently on `Hari`/`main` contains unsanitized values in plain text —
real employee email, real workspace hostname, real Google Sheet IDs, the literal
company name, secret-scope name, cluster policy ID, and cost-allocation code (see
inventory below). Sanitizing only the working tree does **not** remove these from
history; anyone can `git log -p` or `git show <old-sha>` and recover them.

The public repository must be created as a **fresh `git init`** with the sanitized
files added as a first commit — never `git clone`, `git filter-repo`, or
`git push` from this private repo into the public one. This plan does not attempt
history rewriting (e.g. `git filter-repo`/BFG) because it's error-prone and
unnecessary when a clean re-init is available; that decision is recorded here so it
isn't silently forgotten later.

## 1. Current structure (as discovered)

```
.
├── README.md
├── LICENSE
├── internal-team-projects/
│   ├── README.md
│   ├── kaizando-automation-appscript/        (README, images/, scripts/*.js)
│   └── order-duration-efficiency-analysis/   (README, order_transport_duration_analysis.js)
└── prod-projects/
    ├── databricks-pipelines/
    │   ├── README.md
    │   ├── clarification-bookings/           (apps-script/, src/, docs/ stubs, README, databricks.yml)
    │   ├── cups-clarification-booking/       ⚠ UNTRACKED, not in git, not requested as source material
    │   ├── dbricks-utils/                    (common_utils.py, requirements.txt)
    │   ├── oracle-to-looker-etl/              (src/, README, databricks.yml)
    │   ├── outet-booking/                     (src/, README, databricks.yml, .databricks/ gitignored)
    │   ├── realtime-data-stream/              (src/, transport_kpis_queries/, data_dict/, assets/)
    │   ├── receive-booking-monthly-backup/    (src/, assets/, databricks.yml)
    │   ├── receive-uph-kpis/                  (src/, databricks.yml)
    │   └── shift-report-daily-update/         (src/, databricks.yml)
    ├── inventory-reconciliation-sql/
    │   └── inbound-booking-report/            (README, normal_booking_logic.sql, manual_sorting_logic.sql, luu-volumes/)
    ├── looker-reporting-etl/
    │   ├── README.md
    │   ├── dg-compliance-pipeline/            (README, images/dg-monitor.png — no code)
    │   └── qa-intelligence-engine/            (README, images/*.png — not featured)
    └── sql-kitchen/
        ├── README.md
        ├── booking/                          (3 .sql files)
        ├── kpis/                              (1 .sql file)
        └── tgw-infosystem-live/               (2 .sql files, named after a real vendor product)
```

## 2. Sensitive-data findings (summary — full detail will go in `docs/sanitization-report.md`)

A repo-wide sweep (text + targeted checks) found the same handful of identifiers
repeated across nearly every file:

| Category | Value found | Where |
|---|---|---|
| Employer name | `Zalando` / `Zalando SE` | prose in ~9 READMEs; hardcoded literal in 8+ SQL files as a `DECODE`/business value |
| Site/team name | `LUU`, `Ludwigsfelde`, `Kaizando`, `LUU-QM`, `LUU Kaizen` | root README, internal-team-projects, sql-kitchen, looker-reporting-etl, dbricks-pipelines READMEs, secret-scope name, ticket-ID prefix |
| Employee PII | `hari.prasanna.ravichandran@zalando.de` | 6 `databricks.yml` failure-notification blocks; hardcoded in `/Workspace/Users/...` paths in 9 Python/notebook files |
| Workspace hostname | `zalando-e2.cloud.databricks.com`, `dbc-0c31c458-b8aa.cloud.databricks.com` | every `databricks.yml` |
| Secret scope | `luu_qm_secrets` | ~15 files (READMEs + Python) |
| Cluster policy ID | `000294BBB7FAF7AF` | 6 `databricks.yml` |
| Cost-allocation code | `50019562` | 6 `databricks.yml` |
| Google Sheet IDs / URLs | 6 distinct real IDs, 1 real Google Doc SOP link, 1 real Looker Studio report URL, 1 real Google Form link | `config.json` files (gitignored but present on disk), 1 README, 1 Apps Script file |
| Internal schema/tables | `HISTORIE_V`, `ZAL_BESTAND`, `zalando_shared.prod.d_outlet_article_simple` | ~25 SQL/Python files |
| Vendor name | `TGW` (TGW Logistics Group) | `sql-kitchen/tgw-infosystem-live/` (dir name + file contents) |
| Personal name | "Simone" (colleague, mail-merge pickup location) | `kaizando-automation-appscript/scripts/gamification.js` |
| Cron schedules | 5 distinct quartz cron expressions | every `databricks.yml`, restated in 2 READMEs |

**Files with live secrets currently on disk (gitignored, never committed, but present
in the working tree and must not be copied anywhere):**
`clarification-bookings` has none live (uses `.example`/`.template` convention correctly);
the following do carry live `config.json` with real Sheet IDs:
`cups-clarification-booking/src/config.json`, `outet-booking/src/config.json`,
`receive-uph-kpis/src/config.json`, `shift-report-daily-update/src/config.json`,
`receive-booking-monthly-backup/src/config.json`, `oracle-to-looker-etl/src/config.json`.
Also `outet-booking/.databricks/` (Terraform state with workspace ID, job ID, real
email) — build output, gitignored, must never be copied.

Every one of these `config.json` files already has a sanitized `config.template.json`
sibling with placeholder values — the template is what will ship publicly; the live
file will simply not be copied into `featured/`, `technical-deep-dives/`, or
`additional-work/` at any point.

## 3. Proposed source → target mapping

| Target | Source(s) | Notes |
|---|---|---|
| `featured/01-clarification-automation/` | `prod-projects/databricks-pipelines/clarification-bookings/` | `git mv` for tracked files, then sanitize in place. **Does not include** `cups-clarification-booking` — see Open Question 1. |
| `featured/02-dangerous-goods-data-product/` | `prod-projects/databricks-pipelines/oracle-to-looker-etl/` + `prod-projects/looker-reporting-etl/dg-compliance-pipeline/` | Code comes from the first; the second contributes only README narrative + 1 screenshot (no code duplication to resolve). Screenshot needs Open Question 2. |
| `featured/03-order-flow-bottleneck-analysis/` | `internal-team-projects/order-duration-efficiency-analysis/` | Already fairly portfolio-ready prose; code needs sheet/tab-name genericization. |
| `technical-deep-dives/inventory-event-reconciliation/` | `prod-projects/inventory-reconciliation-sql/inbound-booking-report/` (excluding `luu-volumes/`, which is supporting/non-essential — see Open Question 3) | Contains the one direct literal `'Zalando SE'` value inside SQL `DECODE` output — highest-priority redaction. |
| `shared/logistics_data_utils/` | `prod-projects/databricks-pipelines/dbricks-utils/common_utils.py` | Split into `connections.py`, `config.py`, `sheets.py`, `time_windows.py`, `notifications.py` per target spec; secret-scope name parameterized, not hardcoded. |
| `additional-work/operational-kpi-monitoring.md` | `realtime-data-stream/`, `receive-uph-kpis/` | Case-study summary only, no code copied verbatim. |
| `additional-work/quality-metric-governance.md` | `qa-intelligence-engine/` | Screenshots not included (see Open Question 2); described in prose only. |
| `additional-work/scheduled-reporting-automations.md` | `receive-booking-monthly-backup/`, `shift-report-daily-update/`, `outet-booking/`, `sql-kitchen/` (incl. `tgw-infosystem-live/`, vendor name dropped), `kaizando-automation-appscript/` | One consolidated page per target spec lists 3 files; this groups 5 source projects. Kaizando automation touches employee data (gamification email with a name) — summarized narratively only, no script content copied. |
| *(not migrated)* | `cups-clarification-booking/` | Untracked, not committed, not named in the task's source list. Flagged, not moved — see Open Question 1. |

## 4. Per-project sanitization risk detail

### featured/01-clarification-automation
- Redact employer name, employee email, workspace host, secret scope, policy ID,
  cost-allocation code from `databricks.yml`, `README.md`, both `.py` files, and
  `config.template.json`.
- Replace hardcoded `/Workspace/Users/<email>/team-repo/...` in
  `clarification_bookings.py` and `backlog_clarification_webhook.py` with
  `Path(__file__).resolve().parent`-style resolution.
- Genericize `src/clarification_booking.sql` and `src/backlog_clarification.sql`:
  table `HISTORIE_V`/`ZAL_BESTAND` → `<SOURCE_TABLE>` placeholders in docs, generic
  aliases in code; workstation codes (`OV_AP29`–`OV_AP32`), partner codes
  (`TPARTNR=520/614/207`) → described generically in `docs/data-contract.md` rather
  than left as unexplained magic numbers.
- `apps-script/06_Notifications.js` references "LUU-QM Taskmanager" by name — reword.
- Five `docs/*.md` files under the source are empty stubs — the new project docs
  will be written fresh, not copied.
- `apps-script/00_Config.js` "Klärfall" business term: this is a German logistics
  process word (roughly "clarification case"), not a company identifier — safe to
  keep as domain vocabulary, already what the portfolio angle calls
  "duplicate WMS/spreadsheet entry."

### featured/02-dangerous-goods-data-product
- Redact `luu_beauty_stock_pipeline`/`LUU_Beauty_Stock_Update` job names,
  `LUU_DG_Stock_Monitor` Chat-card title, secret scope, workspace host, cron.
- Genericize `zal_bestand_query.sql` (`ZAL_BESTAND`, `BEZ` column, `'T%'`/`'BSF_T%'`
  filters) and the OUTLET/OLAP/FIN masking logic in `etl_pipeline.py` — described,
  not renamed to something misleading.
- `dg-compliance-pipeline/README.md` describes UN-number/hazard-class classification
  and a "days difference" metric that do **not** appear anywhere in the committed
  Python — flagged so the new README doesn't overstate the code (rule: no fabricated
  capabilities). New README will describe that classification as happening
  downstream in the dashboard layer, not in this pipeline's code.
- `dg-monitor.png` screenshot is a real dashboard — Open Question 2.
- Merge will drop the now-obsolete cross-repo relative links
  (`../../databricks-pipelines/oracle-to-looker-etl`) in favor of same-directory links.

### featured/03-order-flow-bottleneck-analysis
- `order_transport_duration_analysis.js`: sheet/tab names
  (`Transport Statistik`, `Änderungen des Auftragsstatus`, `AuftragsmonitorAp`,
  `Übersicht`) are internal report names — genericize to descriptive constants
  (e.g. `ORDER_STATUS_LOG`, `TRANSPORT_LOG`, `SUMMARY_SHEET`).
- README already states the causal-vs-correlation caveat is needed per the task
  brief — will keep/strengthen that language rather than overstate impact.
- No PII, hostnames, or secrets found in this project — lowest-risk of the three.

### technical-deep-dives/inventory-event-reconciliation
- `normal_booking_logic.sql` line 179 and `manual_sorting_logic.sql` line 88: literal
  `'Zalando SE'` **and** `'Zircle'` as DECODE output values — highest-priority fix,
  replace with a neutral label (e.g. `'Primary Channel'`/`'Partner Channel'`) since
  these are business classification labels, not identifiers that affect query logic.
- Table `HISTORIE_V`, columns `TPARTNR`, `LOCAL_TRANSACTION_ID`, `CUST_DATA`,
  `LHMNR` — genericized in the public copy; the `docs/data-contract.md` will explain
  the *shape* (JSON-encoded custom-data column, transaction-ID join key) without the
  real names.
- `luu-volumes/` subfolder: directory name itself contains the site code, and its
  3 files are supporting/secondary queries not mentioned in the task's "Technical
  Deep Dive" emphasis list — Open Question 3 on whether to fold a genericized
  version in or drop it.

### shared/logistics_data_utils
- `common_utils.py` hardcodes secret-scope name `luu_qm_secrets` and its 3 keys —
  becomes a constructor/config parameter, no hardcoded scope name shipped.
- This is the cleanest source file found (no PII, no hostnames) — lowest rewrite risk.
- Per task rule: characterization tests will be added **before** splitting into
  `connections.py`/`config.py`/`sheets.py`/`time_windows.py`/`notifications.py`, and
  business behavior will not change in this pass.

### additional-work/*
- `kaizando-automation-appscript/scripts/gamification.js` contains a live Google Form
  URL and a colleague's first name ("Simone") in a mail-merge template — this project
  will be summarized in prose only; no script content will be copied into the public
  repo at all (not even sanitized), since the source is a mass-email/gamification
  tool with real-person references baked into its logic, not just its config.
- `tgw-infosystem-live/`: vendor name TGW is a real third-party product; case-study
  text will describe it generically ("a legacy warehouse-management terminal") rather
  than name the vendor, since the vendor relationship isn't the employer's IP to
  disclose and isn't relevant to the engineering story.
- 3 scratch/test notebooks (`booking_script_test.ipynb`, `ui_test_notebook.ipynb`,
  `report_script_notebook.ipynb`) are near-duplicates of their `.py` siblings with
  unsanitized hardcoded paths — will not be referenced or copied; the case studies
  describe behavior, not paste code.
- 8 PNG screenshots across `realtime-data-stream/`, `receive-booking-monthly-backup/`,
  `qa-intelligence-engine/`, `kaizando-automation-appscript/` — Open Question 2.

## 5. Files requiring manual review (cannot be resolved by text sanitization alone)

1. **8 PNG screenshots** (dashboards, chat cards, email previews) — a text sweep
   cannot verify what's rendered inside an image (real KPI numbers, real branding,
   real names may be visible). Default proposal: **do not carry any screenshot into
   the public repo**; describe visuals in prose/Mermaid diagrams instead. Flagging
   for explicit confirmation rather than assuming.
2. **`cups-clarification-booking/`** — untracked, not part of the task's named
   source material, and its `src/config.json` has a live Sheet ID sitting on disk.
   Proposal: leave it untouched (not committed, not moved, not deleted) and note it
   in `docs/sanitization-report.md` as "found on disk, out of scope, contains a live
   secret — recommend the user `.gitignore`/remove it independently of this
   reorganisation." Not treating it as "the current version of clarification
   automation" since the task explicitly scoped source material to
   `clarification-bookings` only.
3. **`luu-volumes/` subfolder** under `inbound-booking-report` — not explicitly named
   in the Technical Deep Dive emphasis list. Needs an explicit include/exclude call.
4. **Prior commit history on `Hari`/`main`** — contains all the same identifiers in
   plain text across 5 commits (`ca47b6b`, `8d4fb3e`, `985c5aa`, `cdf53f3`, `6e6d479`).
   This branch's own history will therefore also carry them. Since rule 9 already
   establishes the public repo will be a fresh `git init` (not a clone), this is not
   a blocker for the sanitized working tree itself, but it means **this private repo's
   history must never be pushed anywhere public** — noted here so it's explicit.

## 6. Open questions — RESOLVED (user sign-off obtained before any file changes)

1. **`cups-clarification-booking`: excluded entirely.** Left untouched on disk — not
   moved, not committed, not referenced anywhere in the public structure.
2. **Screenshots: excluded entirely.** No image files are copied into the public
   repo. Architecture/behavior is described via Mermaid diagrams and prose instead.
   `assets/` folders are created empty (with a short note) where the target
   structure calls for them, so the layout is ready if the user supplies redacted
   images later.
3. **`luu-volumes/`: excluded from the deep dive, folded into `additional-work/` as
   a one-line mention only.** No SQL from that subfolder is copied anywhere, not
   even genericized.

## 7. Controls status convention

Every validation table in this reorganisation will mark each control as exactly one
of: **Implemented**, **Manually validated**, **Planned**, or **Unknown** — never
"Implemented" without code or documented evidence, per task rule 7. Given no
automated test suite exists in any source project today, most data-correctness
controls will start as **Unknown** or **Planned** until/unless synthetic-fixture
tests are added in this refactor, and any claim of "manually validated" will only be
used where the user confirms they actually performed that validation historically —
this assistant will not infer or fabricate that a check was performed.
