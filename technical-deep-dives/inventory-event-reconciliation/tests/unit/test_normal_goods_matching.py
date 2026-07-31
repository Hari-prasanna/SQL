"""Tests for the plain LOCAL_TRANSACTION_ID join used for the normal-goods
leg in both sql/normal_booking_logic.sql and sql/manual_sorting_logic.sql.

IMPORTANT: this test does NOT run the production Oracle SQL. It runs a
hand-translated, SQLite-compatible REIMPLEMENTATION of only the core
book-out/book-in join, against synthetic fixture data, so the matching
algorithm can be exercised without a live Oracle connection (none is
available to this repository). See ../../docs/validation.md for what this
does and does not prove about the production query.
"""

from sqlalchemy import text

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


def test_single_pair_matches_cleanly(sqlite_engine_factory):
    """N1 has exactly one book-out and one book-in -- the assumption the
    normal-goods leg relies on. The plain join must produce exactly 1 row."""
    engine = sqlite_engine_factory("normal_goods_seed.sql")

    rows = [r for r in _run(engine, PLAIN_JOIN_QUERY) if r["local_transaction_id"] == "N1"]

    assert len(rows) == 1
    assert rows[0]["source_lhm"] == "SRC1"
    assert rows[0]["ziel_lhm"] == "DST1"


def test_documents_cross_multiplication_risk_if_uniqueness_assumption_breaks(sqlite_engine_factory):
    """N2 has TWO book-out/book-in pairs sharing one LOCAL_TRANSACTION_ID --
    a violation of the uniqueness assumption the normal-goods leg's plain
    join depends on (see ../../docs/limitations.md). This test documents the
    resulting cross-multiplication; it does NOT assert this is fixed, because
    the production normal-goods leg does not apply ROW_NUMBER() sequence
    matching the way the dummy-goods leg of manual_sorting_logic.sql does."""
    engine = sqlite_engine_factory("normal_goods_seed.sql")

    rows = [r for r in _run(engine, PLAIN_JOIN_QUERY) if r["local_transaction_id"] == "N2"]

    # 2 real book-outs x 2 real book-ins = 4 joined rows, only 2 of which
    # are "correct" pairings. This is the exact risk documented in
    # ../../docs/limitations.md for the normal-goods leg.
    assert len(rows) == 4
