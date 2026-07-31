# Reorganisation Summary

> ⚠️ **Internal review document — do not publish verbatim.** The "Internal
> identifiers removed" section below names a couple of the real values for
> audit purposes (same reasoning as the warning on
> [reorganisation-plan.md](reorganisation-plan.md),
> [sanitization-policy.md](sanitization-policy.md), and
> [sanitization-report.md](sanitization-report.md)). Exclude all four documents
> from the public copy, or rewrite them to reference categories instead of literal
> values, before publishing.

Executed on branch `refactor/curated-logistics-data-portfolio`, created from `Hari`
(not `main`). **Nothing has been committed or pushed** — this branch's working
tree reflects the full reorganisation, ready for review and diff.

## Files moved (via `git mv`, history preserved as renames)

| From | To |
|---|---|
| `prod-projects/databricks-pipelines/clarification-bookings/{src,apps-script}/*` | `featured/01-clarification-automation/{src,sql}/*` |
| `prod-projects/databricks-pipelines/oracle-to-looker-etl/src/*.py`, `zal_bestand_query.sql` | `featured/02-dangerous-goods-data-product/{src,sql}/*` |
| `internal-team-projects/order-duration-efficiency-analysis/order_transport_duration_analysis.js` | `featured/03-order-flow-bottleneck-analysis/src/` |
| `prod-projects/inventory-reconciliation-sql/inbound-booking-report/{normal_booking_logic,manual_sorting_logic}.sql` | `technical-deep-dives/inventory-event-reconciliation/sql/` |

## Files merged

- `featured/02-dangerous-goods-data-product/` merges two source projects:
  `oracle-to-looker-etl` (all the code) and `looker-reporting-etl/dg-compliance-pipeline`
  (narrative-only — it had no code, just a README and a screenshot that was
  excluded). See that project's `docs/decisions.md` for why they were combined
  into one featured case study instead of two.

## Files archived / represented only as case studies (no code copied)

Summarized in prose in `additional-work/` with no source code carried forward:

- `realtime-data-stream/`, `receive-uph-kpis/` → `additional-work/operational-kpi-monitoring.md`
- `looker-reporting-etl/qa-intelligence-engine/` → `additional-work/quality-metric-governance.md`
- `receive-booking-monthly-backup/`, `shift-report-daily-update/`, `outet-booking/`,
  `sql-kitchen/` (all 3 subfolders), `kaizando-automation-appscript/` →
  `additional-work/scheduled-reporting-automations.md`

`kaizando-automation-appscript/` specifically was not sanitized-and-copied like the
others — it was excluded from code-copying entirely because a live Google Form URL
and a real colleague's name were embedded in its actual logic, not just its config.

## Excluded entirely (per your 2026-07-31 decisions, recorded in reorganisation-plan.md)

- `prod-projects/databricks-pipelines/cups-clarification-booking/` — untracked,
  out of scope, left untouched on disk (still contains a live Sheet ID in its
  `src/config.json` — not staged, not referenced anywhere in the public structure).
- `prod-projects/inventory-reconciliation-sql/inbound-booking-report/luu-volumes/`
  — left in place, out of scope; mentioned once, by category only, in
  `additional-work/operational-kpi-monitoring.md`.
- 8 real screenshots across 4 source projects — none copied; described in prose/Mermaid instead.

## Internal identifiers removed

See [sanitization-report.md](sanitization-report.md) for the full sweep (final
result: **zero matches** across the entire public structure for employer/site name,
employee email, real workspace hostnames, real secret-scope name, real cluster
policy ID, real cost-allocation code, real Google Sheet IDs, a real dashboard URL,
a real vendor name, and a real colleague's name). Highlights:

- Employer name ("Zalando") and site name ("LUU"/"Ludwigsfelde") — never named anywhere in the public structure.
- Employee email, hardcoded `/Workspace/Users/<email>/...` paths — removed; replaced with `Path(__file__).resolve().parent` and an installable shared package (no `sys.path` hacks).
- 2 real workspace hostnames, 1 secret-scope name, 1 cluster policy ID, 1 cost-allocation code — replaced with un-defaulted bundle template variables.
- 6 real Google Sheet IDs, 1 real Looker Studio dashboard URL, 1 real Google Doc SOP link, 1 real Google Form link — none shipped; placeholders only.
- 2 real internal Oracle table names (`HISTORIE_V`, `ZAL_BESTAND`) and 4 real workstation codes — replaced with generic aliases in every SQL file that carried them forward.
- 2 literal `'Zalando SE'` / `'Zircle'` values baked into SQL `DECODE` output — replaced with neutral labels.
- 1 real vendor product name (TGW Infosystem) — described generically, never named.

## Tests added

44 Python tests (pytest, all passing) + 4 JavaScript tests (Node's built-in test
runner, all passing) = **48 tests total**, none requiring live Oracle, Databricks,
Google Sheets/Chat, or Looker Studio access:

| Project | Tests | What they cover |
|---|---|---|
| `shared/logistics_data_utils` | 17 | Idempotent sheet-write logic (fake sheet), UTC window calc, webhook payload shape, config loading, SQL execution via SQLite, secret-scope parameterization |
| `featured/01-clarification-automation` | 6 | Backlog notification payload, days-back widget resolution, config-shape compatibility with the shared package |
| `featured/02-dangerous-goods-data-product` | 15 | Stock-row cleaning filter, volume-threshold masking, notification card shape, secret-scope resolution |
| `featured/03-order-flow-bottleneck-analysis` | 4 (Node) | Archive-step dedup logic extracted from the Apps Script |
| `technical-deep-dives/inventory-event-reconciliation` | 6 | ROW_NUMBER sequence-matching and plain-join book-out/book-in logic, reimplemented in SQLite and clearly labeled as such |

## Tests that could not be written

Documented honestly (marked Unknown/Planned, not silently skipped) in each
project's `docs/validation.md`:

- Any Apps Script logic that runs inside `SpreadsheetApp`/`PropertiesService` —
  unmockable outside the Google Apps Script runtime (`featured/01`'s reconciliation
  pipeline, most of `featured/03`'s 4-step script).
- Row-count reconciliation (extracted-from-Oracle vs. written-to-Sheet) — no such
  check exists in any source project.
- The actual Oracle-specific SQL (`JSON_VALUE`, `DECODE`, `TO_DATE` with Oracle
  format masks) cannot run against SQLite — the deep-dive tests exercise a
  hand-translated, explicitly-labeled reimplementation of the core matching logic,
  not the production query itself.
- UN-number/hazard-class classification and a "days difference" forecast metric
  described in the original `dg-compliance-pipeline` README were found to not
  exist anywhere in the committed Python — nothing was written to test logic that
  doesn't exist in this codebase; the README/validation table say so explicitly
  instead of implying test coverage for a feature that isn't there.

## Manual decisions still required (before this can be published)

1. **Redact or exclude 4 internal review documents before publishing.**
   `docs/reorganisation-plan.md`, `docs/sanitization-policy.md`,
   `docs/sanitization-report.md`, and this file name the real values that were
   found and removed (real employer/site name, employee email, secret scope,
   cluster policy ID, cost code) so this branch could be audited. Each now carries
   a warning banner, but they must be either excluded from the public repo or
   rewritten to reference categories instead of literal values — publishing them
   as-is would re-expose exactly what the rest of the reorganisation redacts.
2. **`prod-projects/looker-reporting-etl/README.md` was deleted** as part of
   umbrella-directory cleanup (its whole parent tree is retired in the target
   structure), so its stale reference to the now-removed `dg-compliance-pipeline`
   is moot — flagging only so you know that page didn't need a live fix, it needed
   removal, and that's already done.
3. **8 screenshots need your manual review** if you want visuals in the public
   repo at all — none were carried forward; each affected project currently ships
   with a prose/Mermaid description instead.
4. **`cups-clarification-booking/` and `luu-volumes/`** still physically exist in
   this working tree (untouched, per your decisions) — if you ever copy this
   directory tree by hand (rather than via `git`) to seed the public repo, exclude
   both manually; `cups-clarification-booking/src/config.json` has a live secret.
5. **Git history**: when this content moves to the public
   `logistics-data-case-studies` repository, it must be a fresh `git init`, never a
   clone of this repository or a history-preserving export — this repo's commit
   history contains the same real identifiers in plain text.
6. **The `run_if: ALL_DONE` fix** applied to `featured/02`'s bundle template
   (documented in that project's `docs/decisions.md`) was based on documented
   Databricks Jobs default behavior, not verified against the real production job
   — worth a real-world check if you still have access to that workspace.

## Final checks run

- **Tests**: 44/44 Python (pytest) + 4/4 JavaScript (Node) passing.
- **Lint**: `ruff check .` — all checks passed (repo-wide `pyproject.toml`, `prod-projects/` excluded from lint scope as out-of-portfolio material).
- **Markdown links**: all 38 markdown files in the public structure resolve correctly (one path bug found and fixed in `featured/02-dangerous-goods-data-product/docs/decisions.md`).
- **Sensitive-identifier sweep**: zero matches across the public structure — see [sanitization-report.md](sanitization-report.md).
