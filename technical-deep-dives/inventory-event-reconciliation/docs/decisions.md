# Engineering Decisions

## Why two separate SQL files instead of one parameterized query

`normal_booking_logic.sql` and `manual_sorting_logic.sql` both reconcile
book-out/book-in transaction pairs from the same source table, but they exist
as separate files because they serve different consumers with genuinely
different matching logic for the dummy-goods leg (plain ID join vs.
`ROW_NUMBER()` sequence-matched join — see
[data-contract.md](data-contract.md)) and different output shapes (quality/
category classification vs. sequence-matched EAN resolution). Threading a mode
flag through every CTE to merge them into one query would have made each
matching strategy harder to read in isolation, for no real reuse benefit since
they're run independently by different people for different purposes.

## Why `ROW_NUMBER()` + equi-join instead of `MATCH_RECOGNIZE`

Oracle supports `MATCH_RECOGNIZE` for exactly this kind of ordered-pattern
matching, and it would express "match the Nth book-out to the Nth book-in"
more declaratively. `ROW_NUMBER()` + a join on matching rank was kept instead
because it was already the idiom used in the original query, is portable to a
wider range of Oracle versions and tooling, and is more immediately readable to
another analyst without requiring them to learn a less commonly used SQL
feature. This is a deliberate readability/portability trade-off, not an
oversight — see [../README.md](../README.md#9-trade-offs).

## Why a third supporting-queries subfolder was excluded from this deep dive entirely

The original source directory
(`prod-projects/inventory-reconciliation-sql/inbound-booking-report/`)
contained a third subfolder of three site-specific supporting volume queries,
separate from the two reconciliation queries this deep dive is built from. It
was excluded from this technical deep dive — not moved, not sanitized, not
copied in any form — for two reasons:

1. **Scope.** The task brief's emphasis list for this deep dive (transaction
   lifecycle reconstruction, normal-vs-dummy handling, JSON extraction,
   `ROW_NUMBER()` sequence matching, duplicate prevention, parameterized SQL) is
   fully covered by `normal_booking_logic.sql` and `manual_sorting_logic.sql`
   alone. The excluded subfolder contained secondary/supporting volume queries
   that weren't part of that narrative.
2. **Naming.** The subfolder's directory name itself contains the site
   identifier that this entire portfolio reorganisation is redacting (see
   [../../../docs/sanitization-policy.md](../../../docs/sanitization-policy.md)),
   which was a further reason not to fold it in under its original name.

Per the explicit exclusion decision recorded in
[../../../docs/reorganisation-plan.md](../../../docs/reorganisation-plan.md#6-open-questions--resolved-user-sign-off-obtained-before-any-file-changes)
and [../../../docs/sanitization-policy.md](../../../docs/sanitization-policy.md#non-negotiable-exclusions-not-sanitized--simply-never-copied),
that subfolder is covered narratively elsewhere in this portfolio as a
one-line mention only — no SQL from it is copied, sanitized, or reproduced
anywhere in this project. The original folder remains untouched on disk at
its original path, outside this project.

## Why the tests reimplement the matching logic in SQLite instead of skipping tests

Oracle-specific syntax (`JSON_VALUE`, `DECODE`, `TO_DATE` format masks,
`/*+ MATERIALIZE */` hints) doesn't run against SQLite, and no Oracle instance
is available to this repository. Rather than ship no tests at all, or write a
misleading test that claims to validate the production query, `tests/unit/`
contains a hand-translated SQLite-compatible reimplementation of only the
`ROW_NUMBER()` sequence-matching and plain-ID-join logic — clearly documented
in the test files as a simplified reimplementation for testability, not the
production query. See [validation.md](validation.md) for exactly what this
does and doesn't prove.
