import json
from unittest.mock import MagicMock, patch

from logistics_data_utils.connections import get_connections, run_sql_file
from sqlalchemy import create_engine


def test_run_sql_file_executes_query_against_engine(tmp_path):
    sql_path = tmp_path / "query.sql"
    sql_path.write_text("SELECT 1 AS one")

    engine = create_engine("sqlite://")
    df = run_sql_file(engine, str(sql_path))

    assert df["one"].tolist() == [1]


def test_run_sql_file_passes_bind_params(tmp_path):
    sql_path = tmp_path / "query.sql"
    sql_path.write_text("SELECT :val AS echoed")

    engine = create_engine("sqlite://")
    df = run_sql_file(engine, str(sql_path), params={"val": 42})

    assert df["echoed"].tolist() == [42]


def test_get_connections_uses_the_scope_passed_in_not_a_hardcoded_one():
    """Regression test: the original implementation hardcoded a real secret-scope
    name. This package must resolve every secret through whatever scope the
    caller passes in."""
    fake_dbutils = MagicMock()
    fake_dbutils.secrets.get.side_effect = lambda scope, key: {
        "google_auth": json.dumps({"type": "service_account"}),
        "oracle_auth": json.dumps(
            {"user": "u", "password": "p", "host": "h", "port": 1521, "service": "s"}
        ),
        "chat_webhook_url": '"https://example.invalid/webhook"',
    }[key]

    with patch("logistics_data_utils.connections.gspread") as mock_gspread:
        mock_gspread.service_account_from_dict.return_value = "fake-gspread-client"

        gc, engine, webhook_url = get_connections(fake_dbutils, secret_scope="demo_secrets")

    calls = fake_dbutils.secrets.get.call_args_list
    assert all(call.kwargs["scope"] == "demo_secrets" for call in calls)
    assert webhook_url == "https://example.invalid/webhook"
    assert gc == "fake-gspread-client"
    assert engine is not None
