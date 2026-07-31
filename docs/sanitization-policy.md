# Sanitization Policy

> ⚠️ **Internal review document — do not publish verbatim.** This file names the
> real values being redacted (real employer/site name, real employee email
> fragment, real secret-scope name, real cluster policy ID, real cost-allocation
> code) so the reorganisation's substitutions can be audited. That makes it useful
> for reviewing this branch, but unsafe to copy as-is into the public repository —
> doing so would re-expose exactly what the rest of this reorganisation redacts.
> Before publishing, either exclude this file from the public copy or rewrite it to
> reference categories ("the real employer name", "the real secret scope") instead
> of literal values. See [reorganisation-summary.md](reorganisation-summary.md).

This is the canonical substitution table for the portfolio reorganisation. Every
featured project, technical deep dive, and additional-work page uses these exact
replacements so the sanitized repo reads consistently. See
[reorganisation-plan.md](reorganisation-plan.md) for the full inventory this was
built from and [sanitization-report.md](sanitization-report.md) for the file-by-file
sweep results.

## Prose (READMEs, docs/*.md)

| Real value | Replacement in prose |
|---|---|
| Zalando / Zalando SE | "a large European e-commerce fulfillment site" (first mention), "the operator" thereafter |
| LUU / Ludwigsfelde | "the site" / "this site" (dropped as a named identifier entirely) |
| `hari.prasanna.ravichandran@zalando.de` | not mentioned — authorship is covered once in the root README, not per-project |
| Employee "Simone" (mail-merge reference) | not carried into any public file — the source project is summarized narratively only |
| TGW (vendor name) | "a legacy warehouse-management terminal" |
| Kaizando / LUU Kaizen | "the site's continuous-improvement program" |

## Code / config (YAML, JSON, Python, SQL, JS)

| Real value | Placeholder token | Used in |
|---|---|---|
| `hari.prasanna.ravichandran@zalando.de` (as notification recipient) | `<RUN_AS_USER>` | bundle templates |
| `/Workspace/Users/hari.prasanna.ravichandran@zalando.de/team-repo/...` | *removed* — replaced with `Path(__file__).resolve().parent` | all Python entry points |
| `zalando-e2.cloud.databricks.com`, `dbc-0c31c458-b8aa.cloud.databricks.com` | `<WORKSPACE_HOST>` | bundle templates |
| `luu_qm_secrets` | `<SECRET_SCOPE>` (bundle var), `secret_scope` config field with no shipped default | bundle templates, config examples, shared package |
| `000294BBB7FAF7AF` | `<CLUSTER_POLICY_ID>` | bundle templates |
| `50019562` | `<COST_ALLOCATION_CODE>` | bundle templates |
| Real Google Sheet IDs (6 distinct) | `<TARGET_GOOGLE_SHEET_ID>` | config examples |
| Real Looker Studio report URL | `<DASHBOARD_URL>` | config examples, docs |
| Real Google Doc/Form links | *removed* | not referenced anywhere public |
| `HISTORIE_V` | `TRANSACTION_HISTORY_V` (generic alias, not the real name) | featured/deep-dive SQL |
| `ZAL_BESTAND` | `STOCK_BALANCE` (generic alias) | featured/deep-dive SQL |
| `zalando_shared.prod.d_outlet_article_simple` | `<REFERENCE_CATALOG_TABLE>` | additional-work docs (no code copied) |
| Workstation codes `OV_AP29`–`OV_AP32` | `WORKSTATION_1`–`WORKSTATION_4` | featured SQL |
| Partner codes `TPARTNR = 520/614/207` | Named constants (e.g. `NORMAL_GOODS_SOURCE = 1`, `DUMMY_GOODS_SOURCE_A = 2`, `DUMMY_GOODS_SOURCE_B = 3`) documented as illustrative, non-production values in each project's `docs/data-contract.md` | featured/deep-dive SQL |
| Literal `'Zalando SE'` DECODE output value | `'Primary Channel'` | technical deep dive SQL |
| Literal `'Zircle'` DECODE output value | `'Partner Channel'` | technical deep dive SQL |
| Cron expressions (exact) | Described qualitatively ("twice daily on weekdays", "nightly") in prose; bundle templates keep a schedule field but with a placeholder-safe example, not the real production cadence | READMEs, bundle templates |

## What is intentionally left unchanged

Generic warehouse/Oracle column names (`MENGE`, `ZIEL`, `LAGBEZ`, `LHMNR`,
`CUST_DATA`, `CREATEDBY`, `ARTNR`, `TPARTNR` as a column name — only its *values*
are placeholders) are standard German-language WMS abbreviations used across many
logistics systems, not unique to one employer. They are kept as-is because
genericizing every column name would make the SQL harder to follow without
reducing identifiability, and rule 8 calls out *exact internal table names* and
*workstation codes*, not generic column vocabulary.

## Non-negotiable exclusions (not sanitized — simply never copied)

- Any `config.json` with live values (only the `.template`/`.example` siblings ship).
- All 8 screenshots found in source projects (per user decision, 2026-07-31).
- `cups-clarification-booking/` (per user decision, 2026-07-31 — out of scope, untouched).
- `luu-volumes/` SQL subfolder (per user decision, 2026-07-31 — mentioned once in
  additional-work, no code copied).
- The 3 scratch/test notebooks that duplicate `.py` entry points with unsanitized paths.
- `outet-booking/.databricks/` Terraform/build state.
