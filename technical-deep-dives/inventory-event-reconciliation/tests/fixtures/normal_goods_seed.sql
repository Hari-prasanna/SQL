-- Fixture data for tests/unit/test_normal_goods_matching.py
--
-- N1: one book-out, one book-in -> the normal-goods leg's assumption (a
--     transaction ID has exactly one book-out/book-in pair) holds, and the
--     plain LEFT JOIN on local_transaction_id alone produces exactly 1 row.
-- N2: TWO book-out/book-in pairs sharing the same transaction ID -> this
--     fixture documents what happens if the normal-goods uniqueness
--     assumption is ever violated: a plain ID join cross-multiplies to 4
--     rows instead of 2, which is exactly the failure mode that
--     ROW_NUMBER() sequence matching (see the other test file) was
--     introduced to avoid for the manual-sorting dummy-goods leg. The
--     normal-goods leg does NOT have that fix applied in production (see
--     ../../docs/limitations.md) — this test documents the risk, it does
--     not assert the risk is mitigated.

INSERT INTO transactions (local_transaction_id, lhmnr, menge, sequence) VALUES
    ('N1', 'SRC1',  -1, 1),
    ('N1', 'DST1',   1, 2),

    ('N2', 'SRC2A', -1, 1),
    ('N2', 'DST2A',  1, 2),
    ('N2', 'SRC2B', -1, 3),
    ('N2', 'DST2B',  1, 4);
