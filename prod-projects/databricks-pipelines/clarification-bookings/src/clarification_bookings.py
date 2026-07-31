import os
import sys
import importlib
from datetime import date
from typing import Any


PROJECT_DIR = "/Workspace/Users/hari.prasanna.ravichandran@zalando.de/team-repo/databricks/clarification-bookings/src"
UTILS_DIR = "/Workspace/Users/hari.prasanna.ravichandran@zalando.de/team-repo/databricks/dbricks-utils"

JOB_NAME = "Clarification Bookings"
TEST_WEBHOOK_URL = ""

if UTILS_DIR not in sys.path:
    sys.path.append(UTILS_DIR)

import common_utils as u

importlib.reload(u)

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


def get_days_back(dbx_utils, config: dict) -> int:
    try:
        dbx_utils.widgets.text("day", "", "Target date (YYYY-MM-DD, leave blank for today)")
        day_str = dbx_utils.widgets.get("day")

        if day_str:
            return (date.today() - date.fromisoformat(day_str)).days

    except Exception:
        logger.info("No day widget value provided. Using config default.")

    return int(config.get("run_settings", {}).get("days_back", 0))


def setup_connections(config: dict, dbx_utils):
    gc, engine, webhook_url = u.get_connections(dbx_utils, logger=logger)

    if TEST_WEBHOOK_URL:
        webhook_url = TEST_WEBHOOK_URL

    sheet = (
        gc.open_by_key(config["google_sheet"]["sheet_id"])
        .worksheet(config["google_sheet"]["upload_tab"])
    )

    return sheet, engine, webhook_url


def fetch_data(engine, config: dict, start_dt: str, end_dt: str):
    sql_path = os.path.join(PROJECT_DIR, config["file_paths"]["sql_query"])

    params = {
        "start_datetime": start_dt,
        "end_datetime": end_dt,
        "ref_lhm_filter": None,
    }

    df = u.run_sql_file(engine, sql_path, params=params)

    logger.info("Query completed. Rows returned: %s", len(df))

    return df


def update_sheet(sheet, df, target_date: str):
    u.update_google_sheet_idempotent(
        sheet=sheet,
        df=df,
        match_value=target_date,
        date_col_index=1,
        logger=logger,
    )

    logger.info("Google Sheet update completed for target_date=%s", target_date)


def send_failure_notification(error: Exception):
    try:
        dbx_utils = resolve_dbutils()
        _, _, webhook_url = u.get_connections(dbx_utils, logger=logger)

        if TEST_WEBHOOK_URL:
            webhook_url = TEST_WEBHOOK_URL

        u.send_webhook_notification(
            webhook_url,
            job_name=JOB_NAME,
            status="failure",
            error=error,
            logger=logger,
        )

    except Exception as notify_error:
        logger.error("Failed to send failure notification: %s", notify_error, exc_info=True)


def main():
    logger.info("Starting job: %s", JOB_NAME)

    try:
        config = u.load_config(base_dir=PROJECT_DIR)
        dbx_utils = resolve_dbutils()

        sheet, engine, _ = setup_connections(config, dbx_utils)

        days_back = get_days_back(dbx_utils, config)
        start_dt, end_dt, target_date = u.get_utc_window(config, days_back=days_back)

        logger.info(
            "Resolved run window. start_dt=%s, end_dt=%s, target_date=%s",
            start_dt,
            end_dt,
            target_date,
        )

        df = fetch_data(engine, config, start_dt, end_dt)

        if df.empty:
            logger.warning("No rows returned for target_date=%s", target_date)

        update_sheet(sheet, df, target_date)

        logger.info("Job completed successfully: %s", JOB_NAME)

    except Exception as error:
        logger.critical("Job failed: %s", error, exc_info=True)
        send_failure_notification(error)
        raise


if __name__ == "__main__":
    main()