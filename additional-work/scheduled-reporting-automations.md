# Scheduled Reporting Automations

This page groups a family of smaller scheduled-reporting projects that share a
common shape: pull a defined slice of operational data on a fixed cadence, apply
a light transform (enrichment, aggregation, or backfill), and land it somewhere a
non-technical stakeholder already looks — a shared spreadsheet, a chat channel, or
a query library other engineers reuse. None of these is individually complex
enough to warrant its own featured case study, but together they show the same
engineering discipline applied repeatedly: idempotent writes, config-driven
secrets, and failure notifications, rather than one-off scripts.

## Month-end overstock booking snapshot

A month-end job pulls a full month of overstock booking data from the source
database, enriches each product identifier with its brand name via a lookup
table, archives the previous month's tab, and writes a fresh tab into a shared
reporting workbook, followed by a summary notification to a team chat channel on
success or failure. It replaced a recurring manual routine of downloading raw
reports, filtering them, and looking up brand names by hand.

The engineering technique worth noting is the **enrichment-with-fallback join**:
rather than leaving unresolved product identifiers as blank cells (which silently
degrades the report), unresolved rows are explicitly written as a "no brand info"
placeholder, and a small number of known non-standard identifiers are labeled from
a configurable override map. That combination means a lookup-table gap produces a
visibly labeled gap in the output, not a silent one.

**Sanitization notes:** the enrichment lookup is against an internal
catalog table; this page describes it generically as a warehouse-management
reference table rather than naming the real table. The pipeline screenshot and
any code are excluded. Live report identifiers and a recovery-procedure link that
lived in this project's config are not carried forward.

## Nightly shift report with manual backfill

A nightly job runs a single parameterized query for the day's shift window and
writes the result into a reporting sheet, following the same idempotent
delete-then-load pattern used across this job family. The one distinguishing
feature is a **manual backfill widget**: the job accepts an optional target-date
parameter (defaulting to "today" when left blank), letting an operator re-run the
job for a specific past date — for example after a late correction — without
needing to edit code or redeploy anything.

**Sanitization notes:** no code copied; describes the backfill-widget pattern in
prose only.

## Nightly outlet booking extract

A structurally similar nightly job aggregates outlet-channel booking data,
grouping by date, shift, and several categorical dimensions, and replaces the
current day's rows in a target sheet (safe to re-run without creating duplicates).
On failure it posts a notification to a team chat channel.

**Sanitization notes:** this project's working directory also contains a build
artifacts folder produced by the deployment tool, holding a live workspace
identifier and an internal email address. That folder is not source code, was
never treated as such, and nothing from it is referenced anywhere in this
portfolio.

## SQL query library

A reference library of standalone warehouse queries, organized by purpose:
transaction-level booking queries (receive, manual receive, outlet variants), an
aggregated KPI query that pivots quality grade, source channel, and disposition by
shift, and a small set of queries wired directly into a legacy warehouse-management
terminal's UI. The library exists because several of the query patterns above
recur with small variations (a different location filter, a different aggregation
grain), and keeping them alongside each other made the overlap and the
differences easy to see side by side rather than rediscovering them independently
inside each pipeline.

**Sanitization notes:** the legacy warehouse-management terminal referenced by
one subfolder is a specific real third-party product; per this portfolio's
sanitization policy it's described generically here rather than naming the
vendor, since the vendor relationship isn't relevant to the engineering story. No
SQL is reproduced in this page.

## Continuous-improvement idea automation

A separate small automation supported the site's continuous-improvement idea
program: incoming submissions were auto-translated to a common working language,
new ideas triggered a chat notification to management with a link back to the
submission, and contributors received a periodic email summarizing their
participation. Together, these removed the manual translation and daily
spreadsheet-checking that previously gated the program.

**Sanitization notes:** this source project is summarized narratively only, with
no code, config, or screenshots carried forward. Its notification template
embedded a live external form link and a named individual inside mail-merge
logic — not just configuration — so, per the portfolio's sanitization policy, the
project is described here without any code reference at all rather than
attempting to redact those values out of a code sample.
