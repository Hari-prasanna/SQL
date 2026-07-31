# Databricks notebook source
# MAGIC %pip install oracledb==2.1.2 gspread==6.1.0 oauth2client==4.1.3 sqlalchemy==2.0.25
# MAGIC dbutils.library.restartPython()
import importlib
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any

# logistics_data_utils is installed as a package (see shared/logistics_data_utils) —
# no sys.path manipulation or personal workspace path needed. In a Databricks bundle
# this would be added to the job's `libraries` block as a wheel/workspace library.
import logistics_data_utils as u
import pandas as pd
import pytz

PROJECT_DIR = str(Path(__file__).resolve().parent)
SQL_DIR = Path(__file__).resolve().parent.parent / "sql"

JOB_NAME = "DG Stock Pipeline"
SECRET_SCOPE_ENV_VAR = "SECRET_SCOPE"
DEFAULT_SECRET_SCOPE_PLACEHOLDER = "<SECRET_SCOPE>"

logger = u.setup_logging(__name__)
# Silence the noisy background logs from Py4J and the Google API client, same as
# the original notebook.
logging.getLogger("urllib3").setLevel(logging.WARNING)


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


def get_secret_scope() -> str:
    """Resolves the Databricks secret scope holding google_auth / oracle_auth /
    chat_webhook_url. No real scope name ships with this repository — set the
    SECRET_SCOPE environment variable (or the job's cluster spark env) at deploy
    time. Wrapped in a function (rather than bound once at import time) so it can
    be unit-tested with a monkeypatched environment variable."""
    return os.environ.get(SECRET_SCOPE_ENV_VAR, DEFAULT_SECRET_SCOPE_PLACEHOLDER)


def clean_stock_dataframe(df_raw: pd.DataFrame) -> pd.DataFrame:
    """Keeps only rows whose handling-unit reference (MAINLHM) starts with a
    digit, then trims to the first 22 columns the downstream Sheet formulas
    expect. If MAINLHM isn't present in the extract, no row filter is applied —
    only the column trim runs."""
    lhm_col = next((col for col in df_raw.columns if col.lower() == "mainlhm"), None)
    df_clean = df_raw[df_raw[lhm_col].astype(str).str.match(r'^\d')] if lhm_col else df_raw
    return df_clean.iloc[:, :22].fillna('')


def compute_volumes(df_calc: pd.DataFrame) -> tuple:
    """Recomputes total and 'ready for removal' volume from the calc tab, after
    the Sheet's own formulas have run on the freshly uploaded data. Column
    positions (not names) are used because the calc tab is a formula sheet, not a
    clean export — see docs/data-contract.md for what columns B, F, L, and O hold.

    This is category filtering and volume arithmetic only. It does not classify
    anything by UN number or hazard class — see docs/decisions.md for why that
    isn't (and shouldn't be assumed to be) part of this pipeline."""
    vol_series = pd.to_numeric(
        df_calc.iloc[:, 11].astype(str).str.replace(',', '').str.strip(), errors='coerce'
    ).fillna(0)
    total_vol = vol_series.sum()

    mask_outlet = df_calc.iloc[:, 5].astype(str).str.strip().str.upper() == "OUTLET"
    mask_not_olap = ~df_calc.iloc[:, 1].astype(str).str.strip().str.upper().str.startswith("OLAP")
    mask_not_fin = ~df_calc.iloc[:, 1].astype(str).str.strip().str.upper().str.startswith("FIN")
    mask_starts_50 = df_calc.iloc[:, 14].astype(str).str.strip().str.startswith("50")

    final_mask = mask_outlet & mask_not_olap & mask_not_fin & mask_starts_50
    ready_vol = vol_series[final_mask].sum()

    return float(total_vol), float(ready_vol)


def main():
    logger.info("Starting job: %s", JOB_NAME)
    dbx_utils = resolve_dbutils()

    dbx_utils.widgets.text("category", "Beauty", "1. Product Category")
    category = dbx_utils.widgets.get("category")

    berlin_tz = pytz.timezone('Europe/Berlin')
    current_time = datetime.now(berlin_tz).strftime("%d/%m/%Y %H:%M:%S")

    try:
        config = u.load_config(base_dir=PROJECT_DIR)
        secret_scope = get_secret_scope()

        gc, engine, _ = u.get_connections(dbx_utils, secret_scope, logger=logger)

        sql_path = str(SQL_DIR / config["file_paths"]["sql_query"])
        logger.info("Querying source for category=%s", category)
        df_raw = u.run_sql_file(engine, sql_path, params={"category": category})
        logger.info("Raw data extracted: %s rows.", len(df_raw))

        if len(df_raw) == 0:
            raise ValueError("Source query returned 0 rows. Aborting job.")

        # --- TRANSFORM ---
        logger.info("Transforming data...")
        df_clean = clean_stock_dataframe(df_raw)
        final_count = len(df_clean)

        # --- LOAD ---
        # Full overwrite of the upload tab, not an idempotent per-date append like
        # featured/01's write — this Sheet holds current-state stock, not a
        # historical log, so replacing it wholesale on every run is the intended
        # semantics here. See docs/decisions.md.
        logger.info("Uploading to Sheets...")
        sh = gc.open_by_key(config["google_sheet"]["sheet_id"])

        worksheet_upload = sh.worksheet(config["google_sheet"]["upload_tab"])
        worksheet_upload.batch_clear(["A:V"])
        worksheet_upload.update(
            range_name="A1",
            values=[df_clean.columns.values.tolist()] + df_clean.values.tolist()
        )

        try:
            sh.worksheet(config["google_sheet"]["time_tab"]).update_acell("C2", current_time)
        except Exception as e:
            logger.warning("Could not update time tab: %s", e)

        # Fixed wait for the Sheet's own formulas to recompute before reading the
        # calc tab back. This is a known fragile point — see docs/limitations.md.
        logger.info("Waiting 5 seconds for Google Sheets formulas to sync...")
        time.sleep(5)

        # --- CALCULATE ---
        logger.info("Reading '%s' for calculations...", config["google_sheet"]["calc_tab"])
        worksheet_calc = sh.worksheet(config["google_sheet"]["calc_tab"])
        raw_data = worksheet_calc.get_all_values()

        if len(raw_data) <= 1:
            raise ValueError("Calculation sheet was empty after sync.")

        df_calc = pd.DataFrame(raw_data[1:], columns=raw_data[0])
        total_vol, ready_vol = compute_volumes(df_calc)

        logger.info("Total volume: %s | Ready volume: %s", total_vol, ready_vol)

        # --- SUCCESS HANDOFF ---
        logger.info("Saving task values for downstream notification task...")
        dbx_utils.jobs.taskValues.set(key="status", value="SUCCESS")
        dbx_utils.jobs.taskValues.set(key="rows", value=final_count)
        dbx_utils.jobs.taskValues.set(key="total_vol", value=total_vol)
        dbx_utils.jobs.taskValues.set(key="ready_vol", value=ready_vol)
        dbx_utils.jobs.taskValues.set(key="run_time", value=current_time)
        dbx_utils.jobs.taskValues.set(key="error_msg", value="")

    except Exception as e:
        logger.error("Critical error caught: %s", str(e))
        # --- FAILURE HANDOFF ---
        # NOTE: this handoff is only useful if Notify_Task actually runs when this
        # task fails. See docs/failure-and-recovery.md for a gap found in the
        # original job's task dependency configuration.
        dbx_utils.jobs.taskValues.set(key="status", value="FAILURE")
        dbx_utils.jobs.taskValues.set(key="error_msg", value=str(e))
        dbx_utils.jobs.taskValues.set(key="rows", value=0)
        dbx_utils.jobs.taskValues.set(key="total_vol", value=0.0)
        dbx_utils.jobs.taskValues.set(key="ready_vol", value=0.0)
        dbx_utils.jobs.taskValues.set(key="run_time", value=current_time)

        # Ensure the Databricks UI flags this task as FAILED
        raise e


if __name__ == "__main__":
    main()
