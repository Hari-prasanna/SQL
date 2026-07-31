# Validation

See the validation table in [../README.md](../README.md#7-validation-evidence)
for the full control-by-control status. This page explains exactly what the
automated tests in [../tests/](../tests/) do and don't prove.

## What the tests cover

Oracle-specific syntax (`JSON_VALUE`, `DECODE`, `TO_DATE` with Oracle format
masks, `/*+ MATERIALIZE */` hints, `REGEXP_LIKE`) does not run against SQLite,
and there is no Oracle instance available to this repository to test against
directly. Rather than skip testing entirely or fabricate an integration test
against infrastructure that doesn't exist here, `tests/unit/` contains a
**hand-translated, SQLite-compatible reimplementation of only the core
matching/dedup logic** — explicitly documented in the test file itself as a
simplified reimplementation for testability, not the production query.

- `tests/unit/test_row_number_sequence_matching.py` — reimplements the
  `ROW_NUMBER() OVER (PARTITION BY LOCAL_TRANSACTION_ID ORDER BY "SEQUENCE")`
  + `t1.rn = t2.rn` join from `manual_sorting_logic.sql`'s dummy-goods leg using
  SQLite's `ROW_NUMBER()` window function (supported since SQLite 3.25), against
  synthetic fixture data in [../tests/fixtures/](../tests/fixtures/) that
  includes: a transaction ID with exactly one book-out/book-in pair (the normal
  case), a transaction ID with two book-out/book-in pairs sharing the same ID
  (the case the sequence join exists to fix), and a transaction ID with an
  unmatched book-out (no book-in yet). It asserts that sequence-matching
  produces exactly the expected number of paired rows and that the unmatched
  book-out surfaces with a `NULL` book-in side rather than being dropped or
  duplicated.
- `tests/unit/test_normal_goods_matching.py` — reimplements the plain
  `LEFT JOIN ... ON LOCAL_TRANSACTION_ID` matching used for the normal-goods
  leg in both production files, against fixture data that includes a
  transaction ID appearing exactly once, to confirm the baseline join behaves
  as expected and to document, via a second fixture case, what happens if that
  uniqueness assumption is violated (the plain join does cross-multiply, which
  is exactly the failure mode `ROW_NUMBER()` matching was introduced to avoid
  for the manual-sorting flow).

## What this does and does not prove

- **Does prove:** the sequence-matching *algorithm* — partition by transaction
  ID, order by sequence, join same-rank rows — behaves correctly against known
  synthetic inputs, including the specific duplicate-transaction-ID case it was
  designed to fix.
- **Does not prove:** that the real Oracle query, with real `JSON_VALUE`/
  `DECODE` extraction, real Oracle date-arithmetic, and real production data,
  produces correct output. The SQLite reimplementation omits all JSON
  extraction, quality/category classification, and the 3-step EAN fallback
  entirely — those are not covered by any automated test in this repository.
- **Does not prove:** anything about `LOCAL_TRANSACTION_ID` uniqueness
  assumptions in the real data, row-count reconciliation against a source
  system, or schema-drift resilience — all marked **Unknown** in the
  [README validation table](../README.md#7-validation-evidence), not silently
  skipped.

## What is explicitly not covered

- No test connects to a real Oracle database — none is available outside the
  operator's infrastructure, and this repository does not fabricate
  integration tests against it.
- The quality/category `DECODE`/`CASE` mappings and the 3-step EAN fallback
  logic are not exercised by any test — flagged as a **Planned** gap in
  [../README.md](../README.md#11-what-i-would-improve-next), not silently
  omitted.
- No production dataset or historical query output exists in this repository
  to validate against, so no "matches production" claim is made anywhere in
  this project's documentation.
