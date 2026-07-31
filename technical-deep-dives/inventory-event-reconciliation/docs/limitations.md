# Limitations

- **Orphaned book-ins are invisible.** Because both queries join book-out
  `LEFT JOIN` book-in, a book-in row with no matching book-out never appears in
  either query's output — there is no anti-join or `FULL OUTER JOIN` variant in
  this repository that would surface that asymmetry. See
  [failure-and-recovery.md](failure-and-recovery.md) and
  [../README.md](../README.md#11-what-i-would-improve-next).
- **`ROW_NUMBER()` sequence matching depends on an unverified ordering
  assumption.** It assumes book-outs and book-ins for a given transaction ID
  occur in the same relative order on both sides. If that assumption is ever
  violated upstream, pairs can be silently mismatched rather than the query
  failing loudly — no assertion checks this in either the SQL or the tests.
- **`LOCAL_TRANSACTION_ID` uniqueness for the normal-goods flow is assumed, not
  verified.** Only the dummy-goods leg of `manual_sorting_logic.sql` uses
  sequence matching; the normal-goods leg (in both files) and the dummy-goods
  leg of `normal_booking_logic.sql` still use a plain ID join, which would
  cross-multiply if that leg's uniqueness assumption is ever violated the same
  way it apparently was for manual-sorting dummy goods.
- **No automated test validates the production Oracle SQL directly.** The
  tests in this repository validate a simplified, hand-translated SQLite
  reimplementation of the core matching logic only — see
  [validation.md](validation.md) for exactly what is and isn't covered. There
  is no CI step, schema-contract test, or live-data comparison anywhere in this
  repository.
- **No row-count reconciliation exists.** Neither query's output is compared
  against an independent count of the true number of transaction pairs in a
  given date range — correctness relies entirely on the join/matching logic
  being right, with no independent cross-check.
- **A third subfolder of site-specific supporting volume queries is not
  represented here at all**, even in genericized form — see
  [decisions.md](decisions.md) for why, and
  [../../../docs/reorganisation-plan.md](../../../docs/reorganisation-plan.md)
  for the source decision record.
- **These are ad hoc, analyst-run queries, not a monitored system.** There is
  no scheduling, no alerting, and no historical run log — correctness is only
  as good as the person running the query and interpreting its output.
