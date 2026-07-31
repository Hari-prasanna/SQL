import os
import sys
import importlib
from datetime import date
from datetime import datetime
from typing import Any

import pandas as pd


PROJECT_DIR = "/Workspace/Users/hari.prasanna.ravichandran@zalando.de/team-repo/databricks/cups-clarification-booking/src"
UTILS_DIR = "/Workspace/Users/hari.prasanna.ravichandran@zalando.de/team-repo/databricks/dbricks-utils"

JOB_NAME = "CUPS Clarification Booking"

if UTILS_DIR not in sys.path:
    sys.path.append(UTILS_DIR)

import common_utils as u

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
    day_str = None
    try:
        dbx_utils.widgets.text("day", "", "Target date (YYYY-MM-DD, leave blank for today)")
        day_str = dbx_utils.widgets.get("day")
    except Exception as exc:
        logger.warning("Could not read 'day' widget, falling back to config days_back: %s", exc)

    if day_str:
        try:
            return (date.today() - date.fromisoformat(day_str)).days
        except ValueError as exc:
            logger.warning(
                "Widget 'day' value %r is not a valid ISO date, falling back to config days_back: %s",
                day_str, exc,
            )

    return int(config.get("run_settings", {}).get("days_back", 0))


def setup_connections(config: dict, dbx_utils):
    gc, engine, _ = u.get_connections(dbx_utils, logger=logger)
    workbook = gc.open_by_key(config["google_sheet"]["sheet_id"])
    return workbook, engine


def run_query(engine, sql_file: str, params: dict) -> pd.DataFrame:
    sql_path = os.path.join(PROJECT_DIR, sql_file)
    df = u.run_sql_file(engine, sql_path, params=params)
    logger.info("Query %s returned %s rows", sql_file, len(df))
    return df


def format_target_date(target_date: str, fmt: str) -> str:
    target = date.fromisoformat(target_date)
    if fmt == "dd.mm.yyyy":
        return target.strftime("%d.%m.%Y")
    return target.strftime("%Y-%m-%d")


def with_date_column(df: pd.DataFrame, column_name: str, value: str) -> pd.DataFrame:
    result = df.copy()
    result.insert(0, column_name, value)
    return result


def normalize_date_replace_df(df: pd.DataFrame, dataset: dict, target_date: str) -> pd.DataFrame:
    result = df.copy()
    date_column = dataset["date_column"]
    match_value = format_target_date(target_date, dataset.get("date_format", "yyyy-mm-dd"))

    if dataset.get("inject_date_column"):
        return with_date_column(result, date_column, match_value)

    if date_column in result.columns:
        result[date_column] = result[date_column].astype(str)

    return result


def extract_sheet_date(value: str) -> str:
    if not value:
        return ""

    text = str(value).strip()
    for fmt in ("%d.%m.%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(text[:19], fmt).strftime("%d.%m.%Y")
        except ValueError:
            continue

    return text[:10]


def column_letter(index: int) -> str:
    result = ""
    while index > 0:
        index, remainder = divmod(index - 1, 26)
        result = chr(65 + remainder) + result
    return result


def write_matrix(sheet, matrix: list[list[object]], width: int, clear_rows: int):
    end_col = column_letter(width)
    sheet.batch_clear([f"A1:{end_col}{max(clear_rows, 1)}"])
    sheet.update(range_name="A1", values=matrix, value_input_option="USER_ENTERED")


def rows_matching_date(column_values: list[str], match_value: str) -> list[int]:
    return [
        row_number
        for row_number, value in enumerate(column_values[1:], start=2)
        if extract_sheet_date(value) == str(match_value)
    ]


def delete_rows_batch(sheet, row_numbers: list[int]):
    if not row_numbers:
        return

    requests = [
        {
            "deleteDimension": {
                "range": {
                    "sheetId": sheet.id,
                    "dimension": "ROWS",
                    "startIndex": row_number - 1,
                    "endIndex": row_number,
                }
            }
        }
        for row_number in sorted(set(row_numbers), reverse=True)
    ]
    sheet.spreadsheet.batch_update({"requests": requests})


def replace_rows_by_date(sheet, df: pd.DataFrame, date_column: str, match_value: str):
    new_headers = [str(col) for col in df.columns]
    new_data = df.fillna("").astype(object).values.tolist()

    header = sheet.row_values(1)
    if not header:
        write_matrix(sheet, [new_headers] + new_data, len(new_headers), len(new_data) + 1)
        return

    date_index = header.index(date_column) if date_column in header else 0
    if date_column not in header:
        logger.warning(
            "Date column %r not found in header %r for worksheet %r; defaulting to column A.",
            date_column, header, sheet.title,
        )

    column_values = sheet.col_values(date_index + 1)
    stale_rows = rows_matching_date(column_values, match_value)
    delete_rows_batch(sheet, stale_rows)
    sheet.append_rows(new_data, value_input_option="USER_ENTERED")


def replace_tab_prefix(sheet, df: pd.DataFrame):
    width = len(df.columns)
    data_rows = df.fillna("").astype(object).values.tolist()
    matrix = [[str(col) for col in df.columns]] + data_rows
    existing_rows = len(sheet.get_all_values())
    clear_rows = max(existing_rows, len(matrix))
    write_matrix(sheet, matrix, width, clear_rows)


def update_dataset(sheet, dataset: dict, df: pd.DataFrame, target_date: str):
    if dataset["write_mode"] == "date_replace":
        match_value = format_target_date(target_date, dataset.get("date_format", "yyyy-mm-dd"))
        dated_df = normalize_date_replace_df(df, dataset, target_date)
        replace_rows_by_date(sheet, dated_df, dataset["date_column"], match_value)
        return

    if dataset["write_mode"] == "replace_tab":
        replace_tab_prefix(sheet, df)
        return

    raise ValueError(f"Unsupported write_mode: {dataset['write_mode']}")


def main():
    logger.info("Starting job: %s", JOB_NAME)

    try:
        config = u.load_config(base_dir=PROJECT_DIR)
        dbx_utils = resolve_dbutils()
        workbook, engine = setup_connections(config, dbx_utils)

        days_back = get_days_back(dbx_utils, config)
        start_dt, end_dt, target_date = u.get_utc_window(config, days_back=days_back)
    except Exception as error:
        logger.critical("Job setup failed before processing any dataset: %s", error, exc_info=True)
        raise

    failures = []
    for dataset in config["datasets"]:
        worksheet_name = dataset.get("worksheet", "<unknown>")
        try:
            params = {}
            if dataset.get("include_window_params"):
                params = {
                    "start_datetime": start_dt,
                    "end_datetime": end_dt,
                    "ref_lhm_filter": dataset.get("ref_lhm_filter"),
                }

            df = run_query(engine, dataset["sql_file"], params)
            sheet = workbook.worksheet(dataset["worksheet"])
            update_dataset(sheet, dataset, df, target_date)
            logger.info("Updated worksheet %s", worksheet_name)

        except Exception as error:
            logger.error(
                "Dataset %r failed, continuing with remaining datasets: %s",
                worksheet_name, error, exc_info=True,
            )
            failures.append((worksheet_name, error))

    if failures:
        failed_names = ", ".join(name for name, _ in failures)
        logger.critical(
            "Job finished with %d/%d dataset(s) failed: %s",
            len(failures), len(config["datasets"]), failed_names,
        )
        raise RuntimeError(f"{len(failures)} dataset(s) failed: {failed_names}") from failures[0][1]

    logger.info("Job completed successfully: %s", JOB_NAME)


if __name__ == "__main__":
    main()