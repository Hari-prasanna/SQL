from pathlib import Path

import pytest
from sqlalchemy import create_engine

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


def build_sqlite_engine(seed_filename: str):
    """Build an in-memory SQLite engine loaded with the shared test schema
    plus one seed file.

    This is test infrastructure only. The schema and seed data are a
    hand-translated, SQLite-compatible stand-in for the real Oracle
    TRANSACTION_HISTORY_V source table (see ../docs/data-contract.md) — they
    exist so the core matching/dedup ALGORITHMS can be exercised without a
    live Oracle connection, which is not available to this repository. See
    ../docs/validation.md for exactly what this does and does not prove
    about the production SQL in ../sql/.
    """
    engine = create_engine("sqlite://")
    schema_sql = (FIXTURES_DIR / "schema.sql").read_text()
    seed_sql = (FIXTURES_DIR / seed_filename).read_text()

    raw_conn = engine.raw_connection()
    try:
        raw_conn.executescript(schema_sql)
        raw_conn.executescript(seed_sql)
        raw_conn.commit()
    finally:
        raw_conn.close()

    return engine


@pytest.fixture
def sqlite_engine_factory():
    """Pytest fixture exposing build_sqlite_engine to test modules without
    requiring a package-relative import (tests/unit has no __init__.py)."""
    return build_sqlite_engine
