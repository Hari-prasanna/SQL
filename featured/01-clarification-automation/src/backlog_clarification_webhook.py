import importlib
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

# logistics_data_utils is installed as a package (see shared/logistics_data_utils) —
# no sys.path manipulation or personal workspace path needed. In a Databricks bundle
# this would be added to the job's `libraries` block as a wheel/workspace library.
import logistics_data_utils as u

PROJECT_DIR = str(Path(__file__).resolve().parent)
SQL_DIR = Path(__file__).resolve().parent.parent / "sql"

JOB_NAME = "Backlog Clarification Webhook"
WEBHOOK_SECRET_SCOPE = os.environ.get("SECRET_SCOPE", "<SECRET_SCOPE>")
WEBHOOK_SECRET_KEY = "kf_audit_chat_url"
DEFAULT_WEBHOOK_SECRET_KEY = "chat_webhook_url"
TEST_WEBHOOK_URL = ""

logger = u.setup_logging(__name__)


def resolve_dbutils() -> Any:
    try:
        return dbutils  # type: ignore[name-defined]
    except NameError:
        try:
            spark_session = importlib.import_module("pyspark.sql").SparkSession
            dbutils_class = importlib.import_module("pyspark.dbutils").DBUtils
            return dbutils_class(spark_session.builder.getOrCreate())
        except Exception as exc:
            raise RuntimeError("dbutils is not available. Run this script in Databricks.") from exc


def get_webhook_url(dbx_utils) -> str:
    if TEST_WEBHOOK_URL:
        return TEST_WEBHOOK_URL

    try:
        return dbx_utils.secrets.get(
            scope=WEBHOOK_SECRET_SCOPE,
            key=WEBHOOK_SECRET_KEY,
        ).strip().strip('"')
    except Exception:
        logger.warning(
            "Secret '%s' not found. Falling back to '%s'.",
            WEBHOOK_SECRET_KEY,
            DEFAULT_WEBHOOK_SECRET_KEY,
        )
        return dbx_utils.secrets.get(
            scope=WEBHOOK_SECRET_SCOPE,
            key=DEFAULT_WEBHOOK_SECRET_KEY,
        ).strip().strip('"')


def fetch_backlog_total(engine) -> int:
    sql_path = str(SQL_DIR / "backlog_clarification.sql")

    logger.info("Executing backlog query from: %s", sql_path)

    df = u.run_sql_file(engine, sql_path, params={})

    if df.empty:
        logger.warning("Backlog query returned no rows")
        return 0

    df.columns = df.columns.str.upper()

    if "COMBINED_TOTAL" not in df.columns:
        logger.error("Missing 'COMBINED_TOTAL' column. Returned columns: %s", df.columns.tolist())
        raise KeyError(f"Expected column 'COMBINED_TOTAL' not found in query results: {df.columns.tolist()}")

    raw_val = df.iloc[0]["COMBINED_TOTAL"]
    combined_total = int(raw_val) if raw_val not in (None, "") else 0

    logger.info("Backlog query result: combined_total=%d", combined_total)

    return combined_total


def build_payload(combined_total: int) -> str:
    message_text = f"*Backlog Klärfälle - {combined_total}*"

    payload = {
        "text": message_text
    }

    return json.dumps(payload)


def post_webhook(
    webhook_url: str,
    payload: str,
    max_retries: int = 3,
    initial_backoff_seconds: float = 1.0,
) -> bool:
    headers = {"Content-Type": "application/json"}
    backoff = initial_backoff_seconds
    attempt = 0

    while attempt <= max_retries:
        attempt += 1
        try:
            logger.info("Posting to webhook (attempt %d/%d)", attempt, max_retries + 1)

            req = urllib.request.Request(
                webhook_url,
                data=payload.encode("utf-8"),
                headers=headers,
                method="POST",
            )

            with urllib.request.urlopen(req, timeout=30) as response:
                status_code = response.status
                logger.info("Webhook POST successful. Status: %d", status_code)
                return True

        except urllib.error.HTTPError as http_error:
            status_code = http_error.code

            if 400 <= status_code < 500:
                logger.error(
                    "Webhook POST failed with client error %d: %s",
                    status_code,
                    http_error.read().decode("utf-8", errors="ignore"),
                )
                return False

            if 500 <= status_code < 600:
                if attempt <= max_retries:
                    logger.warning(
                        "Webhook POST failed with server error %d. Retrying in %.1f seconds...",
                        status_code,
                        backoff,
                    )
                    time.sleep(backoff)
                    backoff *= 2
                else:
                    logger.error(
                        "Webhook POST failed after %d retries with server error %d. Giving up.",
                        max_retries,
                        status_code,
                    )
                    return False
            else:
                logger.info("Webhook POST completed with status: %d", status_code)
                return True

        except urllib.error.URLError as url_error:
            logger.error(
                "Webhook POST network error (attempt %d): %s",
                attempt,
                url_error.reason,
            )
            if attempt <= max_retries:
                logger.warning("Retrying in %.1f seconds...", backoff)
                time.sleep(backoff)
                backoff *= 2
            else:
                logger.error("Webhook POST failed after %d retries. Giving up.", max_retries)
                return False

        except Exception as error:
            logger.error("Unexpected error during webhook POST: %s", error, exc_info=True)
            return False

    return False


def main():
    logger.info("Starting job: %s", JOB_NAME)

    try:
        dbx_utils = resolve_dbutils()
        _, engine, _ = u.get_connections(dbx_utils, logger=logger)

        webhook_url = get_webhook_url(dbx_utils)
        combined_total = fetch_backlog_total(engine)
        payload = build_payload(combined_total)
        logger.info("Payload prepared (size: %d bytes)", len(payload))

        success = post_webhook(webhook_url, payload, max_retries=3)

        if success:
            logger.info("Job completed successfully: %s", JOB_NAME)
        else:
            logger.warning(
                "Webhook delivery failed: %s",
                JOB_NAME,
            )

    except Exception as error:
        logger.error("Job failed during execution: %s", error, exc_info=True)


if __name__ == "__main__":
    main()
