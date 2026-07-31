-- Fixture data for tests/unit/test_row_number_sequence_matching.py
--
-- T1: one book-out, one book-in -> the ordinary case, should produce one
--     matched pair.
-- T2: TWO book-out/book-in pairs sharing the same transaction ID -> this is
--     the exact duplicate-scan scenario that ROW_NUMBER() sequence matching
--     in manual_sorting_logic.sql was introduced to fix. A plain ID-only join
--     would cross-multiply this into 4 rows instead of 2.
-- T3: one book-out with NO matching book-in yet -> an orphaned book-out,
--     should surface with a NULL destination side rather than being dropped.

INSERT INTO transactions (local_transaction_id, lhmnr, menge, sequence) VALUES
    ('T1', 'SRC1',  -1, 1),
    ('T1', 'DST1',   1, 2),

    ('T2', 'SRC2A', -1, 1),
    ('T2', 'DST2A',  1, 2),
    ('T2', 'SRC2B', -1, 3),
    ('T2', 'DST2B',  1, 4),

    ('T3', 'SRC3',  -1, 1);
