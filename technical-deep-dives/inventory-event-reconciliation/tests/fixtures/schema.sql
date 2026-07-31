-- Minimal SQLite-compatible schema used ONLY by the tests in ../unit/.
-- This is NOT the production Oracle schema. It keeps just the columns needed
-- to exercise the matching/dedup algorithms documented in
-- ../../docs/data-contract.md, translated to run against SQLite instead of
-- Oracle (see ../../docs/validation.md for what this reimplementation does
-- and does not prove about the real production SQL).

CREATE TABLE transactions (
    local_transaction_id TEXT NOT NULL,
    lhmnr                TEXT NOT NULL,   -- load-carrier number (source or destination)
    menge                INTEGER NOT NULL, -- negative = book-out, positive = book-in
    sequence              INTEGER NOT NULL  -- monotonic event order within a transaction ID
);
