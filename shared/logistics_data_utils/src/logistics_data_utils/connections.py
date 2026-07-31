import json

import gspread
import pandas as pd
from sqlalchemy import create_engine, text

from .notifications import setup_logging

_log = setup_logging(__name__)


def get_connections(dbutils, secret_scope: str, logger=None):
    """Sets up connections to Google Sheets, Oracle, and grabs the webhook URL.

    `secret_scope` is the Databricks secret scope holding `google_auth`,
    `oracle_auth`, and `chat_webhook_url` keys. It is a required parameter
    (not a hardcoded default) so this package never ships a real scope name.
    """
    log = logger or _log
    log.info("Setting up database, sheets, and webhook connections...")
    try:
        google_secret = dbutils.secrets.get(scope=secret_scope, key="google_auth")
        gc = gspread.service_account_from_dict(json.loads(google_secret))

        oracle_secret = dbutils.secrets.get(scope=secret_scope, key="oracle_auth")
        cfg = json.loads(oracle_secret)
        conn_str = (
            f"oracle+oracledb://{cfg['user']}:{cfg['password']}"
            f"@{cfg['host']}:{cfg['port']}/?service_name={cfg['service']}"
        )
        engine = create_engine(conn_str)

        webhook_url = dbutils.secrets.get(scope=secret_scope, key="chat_webhook_url").strip().strip('"')

        return gc, engine, webhook_url
    except Exception as error:
        log.error(f"Connection setup failed: {error}")
        raise


def run_sql_file(engine, sql_path, params=None):
    with open(sql_path) as f:
        query_text = f.read()
    with engine.connect() as conn:
        df = pd.read_sql(text(query_text), conn, params=params or {})
    return df
