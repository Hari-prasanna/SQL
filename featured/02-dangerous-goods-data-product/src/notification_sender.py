# Databricks notebook source
import importlib
import os
from pathlib import Path
from typing import Any

# logistics_data_utils is installed as a package (see shared/logistics_data_utils) —
# no sys.path manipulation or personal workspace path needed. In a Databricks bundle
# this would be added to the job's `libraries` block as a wheel/workspace library.
import logistics_data_utils as u
import requests

PROJECT_DIR = str(Path(__file__).resolve().parent)

CARD_TITLE = "DG_Stock_Monitor"
SECRET_SCOPE_ENV_VAR = "SECRET_SCOPE"
DEFAULT_SECRET_SCOPE_PLACEHOLDER = "<SECRET_SCOPE>"

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


def get_secret_scope() -> str:
    """Same resolution as etl_pipeline.get_secret_scope — duplicated rather than
    imported because each notebook task is deployed and run as a standalone
    entry point (see docs/decisions.md)."""
    return os.environ.get(SECRET_SCOPE_ENV_VAR, DEFAULT_SECRET_SCOPE_PLACEHOLDER)


def get_webhook_url(dbx_utils, secret_scope: str) -> str:
    """Fetches only the chat-webhook secret — deliberately not the full
    logistics_data_utils.get_connections() set, since this task never needs
    Oracle or Sheets access."""
    raw_url = dbx_utils.secrets.get(scope=secret_scope, key="chat_webhook_url")
    return raw_url.strip().strip('"').strip("'")


def build_card(status, rows, total_vol, ready_vol, time_str, config_links, error_msg=None) -> dict:
    """Builds the Google Chat V2 Card payload. Split out from send_card so the
    payload shape can be unit-tested without a network call."""
    is_success = status == "SUCCESS"
    header_title = CARD_TITLE

    if is_success:
        header_subtitle = "✅ Aktualisierung erfolgreich"
        header_icon = "https://fonts.gstatic.com/s/i/short_term/release/googlesymbols/check_circle/default/24px.svg"
    else:
        header_subtitle = "❌ Aktualisierung fehlgeschlagen"
        header_icon = "https://fonts.gstatic.com/s/i/short_term/release/googlesymbols/warning/default/24px.svg"

    sections = []

    if is_success:
        # --- SUCCESS LAYOUT ---
        fmt_rows = f"{int(rows):,}".replace(",", ".")
        fmt_tot = f"{float(total_vol):,.0f}".replace(",", ".") + " ml"
        fmt_rdy = f"{float(ready_vol):,.0f}".replace(",", ".") + " ml"
        clean_time = str(time_str).split(" ")[1] if " " in str(time_str) else str(time_str)

        sections.append({
            "widgets": [{"columns": {"columnItems": [
                {"horizontalAlignment": "START", "widgets": [{"decoratedText": {"topLabel": "Uhrzeit", "text": clean_time, "startIcon": {"knownIcon": "CLOCK"}}}]},
                {"horizontalAlignment": "START", "widgets": [{"decoratedText": {"topLabel": "Zeilen verarbeitet", "text": fmt_rows, "startIcon": {"knownIcon": "DESCRIPTION"}}}]}
            ]}}]
        })
        sections.append({
            "widgets": [{"columns": {"columnItems": [
                {"horizontalAlignment": "START", "widgets": [{"decoratedText": {"topLabel": "Gesamtvolumen", "text": fmt_tot, "startIcon": {"knownIcon": "STORE"}}}]},
                {"horizontalAlignment": "START", "widgets": [{"decoratedText": {"topLabel": "Outlet bereit", "text": fmt_rdy, "startIcon": {"knownIcon": "SHOPPING_CART"}}}]}
            ]}}]
        })
        sections.append({
            "widgets": [{"buttonList": {"buttons": [
                {"text": "DASHBOARD ÖFFNEN \U0001F4CA", "color": {"red": 0, "green": 0, "blue": 1, "alpha": 1}, "onClick": {"openLink": {"url": config_links["looker_dashboard"]}}},
                {"text": "ÜBERSICHT ÖFFNEN \U0001F4D1", "onClick": {"openLink": {"url": config_links["sheet_overview"]}}}
            ]}}]
        })
    else:
        # --- FAILURE LAYOUT ---
        sections.append({
            "widgets": [
                {"textParagraph": {"text": f"<b>⚠️ Automatisierung fehlgeschlagen</b><br>Grund: {str(error_msg)[:250]}..."}},
                {"textParagraph": {"text": "<b>Handlung erforderlich:</b><br>Bitte führen Sie den manuellen Standardprozess durch."}},
                {"buttonList": {"buttons": [{"text": "MANUELLE TABELLE ÖFFNEN \U0001F4DD", "onClick": {"openLink": {"url": config_links["sheet_manual"]}}}]}}
            ]
        })

    return {
        "cardsV2": [{
            "cardId": "stock-card",
            "card": {
                "header": {"title": header_title, "subtitle": header_subtitle, "imageUrl": header_icon, "imageType": "CIRCLE"},
                "sections": sections
            }
        }]
    }


def send_card(webhook_url: str, payload: dict) -> None:
    logger.info("Sending card to Google Chat...")
    response = requests.post(webhook_url, json=payload)
    # This ensures Python throws an error if Google Chat rejects our JSON.
    response.raise_for_status()
    logger.info("Card notification sent successfully.")


def main():
    dbx_utils = resolve_dbutils()

    # The exact name of Notebook 1 as defined in the Databricks Workflow Job
    dbx_utils.widgets.text("previous_task_name", "ETL_Task", "Previous Task Name")
    previous_task_key = dbx_utils.widgets.get("previous_task_name")

    try:
        config = u.load_config(base_dir=PROJECT_DIR)
        secret_scope = get_secret_scope()
        webhook_url = get_webhook_url(dbx_utils, secret_scope)

        logger.info("Fetching results from task: '%s'...", previous_task_key)

        # Retrieve values set by etl_pipeline.py
        status = dbx_utils.jobs.taskValues.get(taskKey=previous_task_key, key="status", default="FAILURE")
        error_msg = dbx_utils.jobs.taskValues.get(
            taskKey=previous_task_key, key="error_msg", default="Unknown system error / task failed to report"
        )
        rows = dbx_utils.jobs.taskValues.get(taskKey=previous_task_key, key="rows", default=0)
        total_vol = dbx_utils.jobs.taskValues.get(taskKey=previous_task_key, key="total_vol", default=0)
        ready_vol = dbx_utils.jobs.taskValues.get(taskKey=previous_task_key, key="ready_vol", default=0)
        time_str = dbx_utils.jobs.taskValues.get(taskKey=previous_task_key, key="run_time", default="--:--")

        logger.info("Status received: %s", status)

        payload = build_card(status, rows, total_vol, ready_vol, time_str, config["dashboard_links"], error_msg)
        send_card(webhook_url, payload)

    except requests.exceptions.HTTPError as http_err:
        logger.error("HTTP error from Google Chat: %s", http_err.response.text)
        raise
    except Exception as e:
        logger.error("Notification script error: %s", e)
        raise


if __name__ == "__main__":
    main()
