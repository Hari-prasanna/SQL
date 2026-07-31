import json
import logging
import urllib.request
from datetime import datetime

import pytz


def setup_logging(name=__name__):
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    logging.getLogger("py4j").setLevel(logging.WARNING)
    return logging.getLogger(name)


_log = setup_logging(__name__)


def build_webhook_card(job_name: str, status: str, error: Exception = None, tz_name: str = "Europe/Berlin") -> dict:
    """Builds the Google Chat card payload — split out from send_webhook_notification
    so the payload shape can be unit tested without a network call."""
    tz = pytz.timezone(tz_name)
    timestamp = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S %Z")

    if status == "failure":
        header = f"❌ {job_name} — Job Failed"
        widgets = [
            {"keyValue": {"topLabel": "Job", "content": job_name}},
            {"keyValue": {"topLabel": "Date", "content": timestamp}},
            {"keyValue": {"topLabel": "Reason", "content": str(error) if error else "Unknown error"}},
        ]
    else:
        header = f"✅ {job_name} — Completed"
        widgets = [
            {"keyValue": {"topLabel": "Job", "content": job_name}},
            {"keyValue": {"topLabel": "Date", "content": timestamp}},
        ]

    return {
        "cards": [
            {
                "header": {"title": header},
                "sections": [{"widgets": widgets}],
            }
        ]
    }


def send_webhook_notification(webhook_url: str, job_name: str, status: str, error: Exception = None, logger=None):
    """Posts a Google Chat card to the webhook for job success or failure."""
    log = logger or _log
    card = build_webhook_card(job_name, status, error)

    try:
        payload = json.dumps(card).encode("utf-8")
        req = urllib.request.Request(
            webhook_url,
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        urllib.request.urlopen(req, timeout=10)
        log.info(f"Webhook notification sent: {status}")
    except Exception as exc:
        log.error(f"Failed to send webhook notification: {exc}")
