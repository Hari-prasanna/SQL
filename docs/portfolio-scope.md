# Portfolio Scope

## What this repository is

A sanitized set of case studies drawn from real logistics-data engineering work:
data pipelines, SQL reconciliation logic, and one operational-analysis tool,
rewritten so they can be shared publicly without exposing an employer, its
infrastructure, or its data.

## What this repository is not

- **Not a production system.** Nothing here is deployed or deployable as-is —
  every config is a `.example`/`.template` with placeholder values, and every
  bundle template requires the reader to supply their own workspace, secrets, and
  identity.
- **Not a full copy of the operator's codebase.** Several real projects exist in
  the operator's private repository that are summarized only (see
  [additional-work/](../additional-work/)) or excluded entirely (see
  [reorganisation-plan.md](reorganisation-plan.md) open questions) — this is a
  curated subset chosen to demonstrate specific engineering decisions, not an
  exhaustive export.
- **Not independently re-validated.** Impact figures and validation claims in each
  project's README are labeled by their actual status — Implemented, Manually
  validated, Planned, or Unknown — and historical impact estimates are explicitly
  marked as reported by the operating team, not re-measured in this repository.
  See each project's `docs/validation.md`.

## Why there are no integration tests against Oracle/Databricks/Google Sheets

None of that infrastructure is available outside the original operator's
environment, and this repository does not simulate it with fake integration tests
that would pass without ever exercising real behavior. Test coverage here is
limited to what can run honestly without that infrastructure: path/config
resolution, pure transformation and classification logic, duplicate-key and
date-window calculations, notification-payload construction, and — where the
underlying engine allows it (SQLite for the Oracle-adjacent SQL) — synthetic
fixture-based logic tests. Anything that can't be tested this way is documented as
a gap in that project's `docs/validation.md`, not silently skipped.

## Why history was not carried over

This repository's git history (in the private operational repo it was extracted
from) contains real employer identifiers in plain text across every prior commit.
The public copy of this content was created as a fresh repository, not a clone —
see the warning at the top of [reorganisation-plan.md](reorganisation-plan.md).

## On the operational run identity

The original pipelines run under a named workspace user's credentials because a
dedicated service principal was not available on that workspace at the time. The
public bundle templates in this repository make the run identity a required,
un-defaulted variable (`run_as_user`) instead, and each project's `docs/decisions.md`
notes that a real organizational deployment should use a service principal.
