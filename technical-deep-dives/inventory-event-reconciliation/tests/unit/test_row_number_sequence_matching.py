"""Tests for the ROW_NUMBER() sequence-matching join used for the dummy-goods
leg of sql/manual_sorting_logic.sql.

IMPORTANT: this test does NOT run the production Oracle SQL. It runs a
hand-translated, SQLite-compatible REIMPLEMENTATION of only the core
ROW_NUMBER() + equi-join matching algorithm, against synthetic fixture data,
so the algorithm itself can be exercised without a live Oracle connection
(none is available to this repository). It intentionally omits JSON_VALUE
extraction, DECODE classification, and the 3-step EAN fallback — those are
not covered by any automated test in this repository. See
../../docs/validation.md for the full explanation of what this does and does
not prove about the production query in ../../sql/manual_sorting_logic.sql.
"""

from sqlalchemy import text

SEQUENCE_MATCH_QUERY = """
WITH book_out AS (
    SELECT
        local_transaction_id,
        lhmnr AS source_lhm,
        ROW_NUMBER() OVER (
            PARTITION BY local_transaction_id ORDER BY sequence ASC
        ) AS rn
    FROM transactions
    WHERE menge < 0
),
book_in AS (
    SELECT
        local_transaction_id,
        lhmnr AS ziel_lhm,
        ROW_NUMBER() OVER (
            PARTITION BY local_transaction_id ORDER BY sequence ASC
        ) AS rn
    FROM transactions
    WHERE menge > 0
)
SELECT
    book_out.local_transaction_id,
    book_out.source_lhm,
    book_in.ziel_lhm,
    book_out.rn
FROM book_out
LEFT JOIN book_in
    ON book_out.local_transaction_id = book_in.local_transaction_id
    AND book_out.rn = book_in.rn
ORDER BY book_out.local_transaction_id, book_out.rn
"""

# A plain ID-only join, with no sequence matching -- kept here to prove the
# duplicate-transaction-ID scenario really would cross-multiply without the
# ROW_NUMBER() fix, which is the exact failure mode documented in
# ../../docs/data-contract.md.
PLAIN_JOIN_QUERY = """
SELECT
    book_out.local_transaction_id,
    book_out.lhmnr AS source_lhm,
    book_in.lhmnr AS ziel_lhm
FROM transactions AS book_out
LEFT JOIN transactions AS book_in
    ON book_out.local_transaction_id = book_in.local_transaction_id
    AND book_in.menge > 0
WHERE book_out.menge < 0
ORDER BY book_out.local_transaction_id, source_lhm, ziel_lhm
"""


def _run(engine, query):
    with engine.connect() as conn:
        return conn.execute(text(query)).mappings().all()


def test_single_pair_matches_one_to_one(sqlite_engine_factory):
    engine = sqlite_engine_factory("sequence_matching_seed.sql")

    rows = [r for r in _run(engine, SEQUENCE_MATCH_QUERY) if r["local_transaction_id"] == "T1"]

    assert len(rows) == 1
    assert rows[0]["source_lhm"] == "SRC1"
    assert rows[0]["ziel_lhm"] == "DST1"


def test_duplicate_transaction_id_pairs_positionally_not_cross_multiplied(sqlite_engine_factory):
    """This is the exact scenario ROW_NUMBER() sequence matching exists to
    fix: transaction T2 has TWO book-out/book-in pairs sharing one
    LOCAL_TRANSACTION_ID. Sequence matching must produce 2 correctly paired
    rows, not 4 cross-multiplied rows."""
    engine = sqlite_engine_factory("sequence_matching_seed.sql")

    rows = [r for r in _run(engine, SEQUENCE_MATCH_QUERY) if r["local_transaction_id"] == "T2"]

    assert len(rows) == 2
    pairs = {(r["source_lhm"], r["ziel_lhm"]) for r in rows}
    assert pairs == {("SRC2A", "DST2A"), ("SRC2B", "DST2B")}
    # The wrong (cross-multiplied) pairings must NOT be present.
    assert ("SRC2A", "DST2B") not in pairs
    assert ("SRC2B", "DST2A") not in pairs


def test_plain_join_would_have_cross_multiplied_the_duplicate_case(sqlite_engine_factory):
    """Documents the bug ROW_NUMBER() sequence matching fixes: without it, a
    plain ID-only join turns 2 real pairs into 4 joined rows."""
    engine = sqlite_engine_factory("sequence_matching_seed.sql")

    rows = [r for r in _run(engine, PLAIN_JOIN_QUERY) if r["local_transaction_id"] == "T2"]

    assert len(rows) == 4  # 2 book-outs x 2 book-ins, the failure mode being fixed


def test_orphaned_book_out_surfaces_with_null_destination(sqlite_engine_factory):
    """Transaction T3 has a book-out with no matching book-in. It must still
    appear in the output (not be silently dropped), with a NULL destination
    side -- matching the LEFT JOIN semantics documented in
    ../../docs/failure-and-recovery.md."""
    engine = sqlite_engine_factory("sequence_matching_seed.sql")

    rows = [r for r in _run(engine, SEQUENCE_MATCH_QUERY) if r["local_transaction_id"] == "T3"]

    assert len(rows) == 1
    assert rows[0]["source_lhm"] == "SRC3"
    assert rows[0]["ziel_lhm"] is None
