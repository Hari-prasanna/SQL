'use strict';

/**
 * Unit tests for selectNewUniqueRows(), extracted from
 * runStep3_ArchiveResults() in ../../src/order_transport_duration_analysis.js.
 *
 * This is the only piece of that file's logic that doesn't depend on the
 * Apps Script SpreadsheetApp runtime, so it's the only piece covered by
 * automated tests here. See ../../docs/validation.md for what is and isn't
 * covered.
 *
 * Run with: node --test tests/unit/archive.test.js
 * (uses the built-in node:test + assert modules — no dependencies to install)
 */

const test = require('node:test');
const assert = require('node:assert/strict');

const { selectNewUniqueRows } = require('../../src/order_transport_duration_analysis.js');

const KEY_COLUMN_INDEX = 2; // Column C, matching the real call site

test('keeps rows whose key is not already archived', () => {
  const sourceRows = [
    ['a', 'b', 'key-1', 'd'],
    ['a', 'b', 'key-2', 'd'],
  ];
  const existingKeys = ['key-9'];

  const result = selectNewUniqueRows(sourceRows, existingKeys, KEY_COLUMN_INDEX);

  assert.deepEqual(result, sourceRows);
});

test('drops rows whose key is already present in the target sheet', () => {
  const sourceRows = [
    ['a', 'b', 'key-1', 'd'],
    ['a', 'b', 'key-2', 'd'],
  ];
  const existingKeys = ['key-1'];

  const result = selectNewUniqueRows(sourceRows, existingKeys, KEY_COLUMN_INDEX);

  assert.deepEqual(result, [['a', 'b', 'key-2', 'd']]);
});

test('drops the second row of an in-run duplicate key, keeping the first', () => {
  const sourceRows = [
    ['a', 'b', 'key-1', 'd'],
    ['x', 'y', 'key-1', 'z'],
  ];

  const result = selectNewUniqueRows(sourceRows, [], KEY_COLUMN_INDEX);

  assert.deepEqual(result, [['a', 'b', 'key-1', 'd']]);
});

test('skips fully empty rows, and matches the original script by scanning from index 0 (including a non-empty header row)', () => {
  const sourceRows = [
    ['h1', 'h2', 'header-key', 'h4'], // header row: not empty, so it IS considered a candidate
    ['', '', '', ''], // fully empty row: always skipped
    ['a', 'b', 'key-1', 'd'],
  ];

  const result = selectNewUniqueRows(sourceRows, [], KEY_COLUMN_INDEX);

  // Documents actual (not idealized) behavior: the header row is archived
  // as if it were a data row because the original script never special-
  // cased row 0. See the function's JSDoc and docs/validation.md.
  assert.deepEqual(result, [
    ['h1', 'h2', 'header-key', 'h4'],
    ['a', 'b', 'key-1', 'd'],
  ]);
});
