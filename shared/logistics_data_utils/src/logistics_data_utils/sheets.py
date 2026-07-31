import pandas as pd

from .notifications import setup_logging

_log = setup_logging(__name__)


def update_google_sheet_idempotent(sheet, df, match_value, date_col_index=1, logger=None):
    """Deletes existing rows matching `match_value` in `date_col_index`, then
    appends `df`. Idempotent per `match_value` (typically a target date) — safe
    to re-run for the same date without creating duplicate rows."""
    log = logger or _log
    if df.empty:
        return
    df.columns = [str(col).upper() for col in df.columns]
    df = df.where(pd.notnull(df), None)

    vals = sheet.col_values(date_col_index)
    rows = [i + 1 for i, v in enumerate(vals) if v == str(match_value)]
    if rows:
        log.info(f"Deleting {len(rows)} rows for {match_value}")
        sheet.delete_rows(rows[0], rows[-1])
        vals = sheet.col_values(date_col_index)

    if not vals:
        sheet.append_row(df.columns.tolist())
    sheet.append_rows(df.values.tolist(), value_input_option="USER_ENTERED")
