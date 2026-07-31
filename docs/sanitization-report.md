# Sanitization Report

> ⚠️ **Internal review document — do not publish verbatim.** The "patterns
> searched" section below names the real values that were searched for and
> removed. Exclude this file from the public copy, or rewrite it to reference
> categories instead of literal values, before publishing — see
> [reorganisation-summary.md](reorganisation-summary.md).

Results of the sensitive-identifier sweep run against the final public structure
(`featured/`, `technical-deep-dives/`, `shared/`, `additional-work/`, `docs/`,
and root-level files) after the reorganisation described in
[reorganisation-plan.md](reorganisation-plan.md), using the substitution table in
[sanitization-policy.md](sanitization-policy.md).

## Patterns searched

Case-insensitive search across every file in the public structure for:
`zalando`, `ludwigsfelde`, `hari.prasanna` (the operator's email local-part),
`zircle`, the real cluster policy ID (`000294BBB7FAF7AF`), the real cost-allocation
code (`50019562`), the real secret scope (`luu_qm_secrets`), the two real workspace
hostnames (`zalando-e2.cloud.databricks.com`, `dbc-0c31c458-b8aa.cloud.databricks.com`),
`tgw` (vendor name), `kaizando`, `forms.gle` (a live Google Form shortlink found in
one excluded source project), and `simone` (a real colleague's first name found in
the same excluded source project) — plus separate passes for long alphanumeric
strings that look like Google Sheet IDs, `docs.google.com`/`lookerstudio.google.com`
URLs, and a bare `LUU` token.

## Result

**Zero matches** for every pattern above across the entire public structure, as of
the final sweep run after all four featured/deep-dive/additional-work migrations
and the root-level cleanup completed. Each project's own agent-run sweep (recorded
in the per-project `docs/decisions.md` / final reports) also came back clean before
this consolidated final pass.

## Files affected (substitutions applied)

| File(s) | Action taken |
|---|---|
| `featured/01-clarification-automation/{README.md, src/*.py, sql/*.sql, config/*, src/apps_script/*.js}` | Employer/site name, employee email, workspace host, secret scope, cluster policy ID, cost-allocation code, real table names, workstation codes, and two "LUU-QM Taskmanager"-style comments replaced per the substitution table |
| `featured/02-dangerous-goods-data-product/{README.md, src/*.py, sql/*.sql, config/*}` | Same categories, plus the vendor name ("TGW Infosystem" export terminal) genericized and the Chat card title/job name replaced |
| `featured/03-order-flow-bottleneck-analysis/src/order_transport_duration_analysis.js` | Internal sheet/tab names and WCS status-code literals genericized to English constants (no company/PII was present in this source) |
| `technical-deep-dives/inventory-event-reconciliation/sql/{normal_booking_logic.sql, manual_sorting_logic.sql}` | Real table name, workstation codes, partner codes, and the two literal `'Zalando SE'`/`'Zircle'` DECODE output values replaced |
| `additional-work/*.md` | Vendor name, colleague first name, live Google Form URL, and company/site name all omitted (prose-only summaries, no code copied) |
| `shared/logistics_data_utils/*` | Secret scope name removed entirely — now a required, un-defaulted parameter (`secret_scope`) instead of a hardcoded string |
| All `config/databricks.bundle.example.yml` files | Real workspace hosts, cluster policy IDs, cost-allocation codes, and the operator's email replaced with un-defaulted bundle variables (`workspace_host`, `run_as_user`, `secret_scope`, `cluster_policy_id`) |
| All `config/config.example.json` files | Real Google Sheet IDs and one real Looker Studio dashboard URL replaced with `<TARGET_GOOGLE_SHEET_ID>` / `<DASHBOARD_URL>` placeholders |

## Files/directories excluded rather than sanitized (never copied into the public structure)

- 6 live `config.json` files (real Sheet IDs) across the original source projects — deleted from disk, not copied.
- `outet-booking/.databricks/` — gitignored Terraform/CLI build state containing a real workspace ID, job ID, and the operator's email — deleted from disk.
- `cups-clarification-booking/` (untracked, contains a live Sheet ID in `src/config.json`) — left untouched in place, out of scope per user decision (2026-07-31); never staged, moved, or referenced by any public file.
- `luu-volumes/` (3 SQL files under the inventory-reconciliation source) — left in place, out of scope per user decision (2026-07-31); mentioned once, by category only, in `additional-work/operational-kpi-monitoring.md`.
- 8 screenshots across 4 source projects — none copied anywhere, per user decision (2026-07-31); each affected project's README/docs describes the relevant dashboard or UI in prose or a Mermaid diagram instead.
- 3 scratch/test notebooks that duplicated `.py` entry points with unsanitized hardcoded paths — not referenced or copied.
- `kaizando-automation-appscript/` source — not copied at all (not even sanitized) because a live Google Form URL and a real colleague's name were embedded in its actual logic (a mail-merge template), not just its config; summarized in prose only in `additional-work/scheduled-reporting-automations.md`.

## Unresolved items requiring manual review

1. **`cups-clarification-booking/` and `luu-volumes/`** still physically exist on
   disk in this working tree (untouched, per the exclusion decisions above) — they
   are not staged for commit and were never part of any commit, but if this
   directory tree is ever copied wholesale (rather than committed via `git`) to
   prepare the public repository, these two paths must be excluded manually, since
   they still contain a live secret (`cups-clarification-booking/src/config.json`).
2. **Git history of this private repository** contains all of the real values
   listed above in plain text across its existing commits. As documented at the
   top of [reorganisation-plan.md](reorganisation-plan.md), the public repository
   must be created as a fresh `git init`, never a clone or history-preserving
   export of this repository.
3. **No image content was inspected pixel-by-pixel** — the 8 screenshots were
   excluded outright rather than reviewed, so no claim is made about what they
   actually contained; this was the safe default given the user's decision, not a
   verification that they were checked and found sensitive.
