# Validation

See the validation table in [../README.md](../README.md#7-validation-evidence)
for the full control-by-control status. This page covers exactly what the
automated tests in [../tests/](../tests/) do and don't exercise, and why the
rest of this file's logic isn't unit tested.

## What the tests cover

- `tests/unit/archive.test.js` — the `selectNewUniqueRows` helper extracted
  from `runStep3_ArchiveResults`, run with Node's built-in `node:test` +
  `assert` (no dependencies to install). It covers:
  - Rows are kept when their business key isn't already archived.
  - Rows are dropped when their business key is already present in the
    target sheet.
  - When two rows in the *same* run share a key, only the first is kept
    (matching the original `Set`-based dedup order).
  - Fully empty rows are always skipped.
  - **The header-row edge case is deliberately preserved, not "fixed."**
    The test `skips fully empty rows, and matches the original script by
    scanning from index 0` asserts that a non-empty header row *is*
    archived as if it were a data row, because the original script scanned
    `sourceData` starting at index 0 rather than index 1. This is
    documented behavior, carried forward exactly, not a bug this
    refactor introduced or silently corrected.

Run them with:

```bash
node --test tests/unit/archive.test.js
```

(Confirmed passing — 4/4 — as of this refactor.)

## What is explicitly not covered, and why

- **`runStep1_PrepareData`, `runStep2_RunAnalysis`, and `runStep4_Cleanup`
  have no automated tests.** All three are almost entirely `SpreadsheetApp`
  calls (`getSheetByName`, `getRange`, `setFormula`, `clearContents`, etc.)
  and spreadsheet-native `QUERY()`/`COUNTUNIQUEIFS()`/`XLOOKUP` formula
  strings. Apps Script's `SpreadsheetApp` runtime is not mockable with
  standard Node or Python test tooling, and the formula strings themselves
  only execute inside Google Sheets — there is no way to assert "this
  `COUNTUNIQUEIFS` formula returns the right count" without a live
  spreadsheet. This is recorded here as a **Planned** gap (see the README's
  validation table), the same way `featured/01-clarification-automation`
  documents its own untestable Apps Script reconciliation layer.
- **No test validates the three-source join is actually correct** (i.e.
  that `XLOOKUP(B2:B, TS!F2:F, TS!H2:H)` and similar cross-sheet lookups
  return the row you'd expect for a given order). Confirming that requires
  either a live spreadsheet with known sample data or a from-scratch
  reimplementation of Google Sheets' `QUERY`/`XLOOKUP` semantics in a test
  harness — neither was in scope for this sanitization pass.
- **The underlying "background transport delays orders" finding is not,
  and cannot be, validated by a unit test.** It's an empirical, correlational
  read of one historical dataset — see the README's Measured Impact and
  Trade-offs sections for why that finding is explicitly not treated as a
  proven causal result here.
