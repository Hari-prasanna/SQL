from datetime import datetime, timedelta

import pytz


def get_utc_window(config, days_back=0):
    """Resolves a shift window (start, end, target-date) to UTC strings.

    `config["shift_settings"]` must have a `timezone` and either a `shifts` list
    (uses the first shift's start and the last shift's end) or explicit
    `start_time`/`end_time` keys.
    """
    local_tz = pytz.timezone(config["shift_settings"]["timezone"])
    target_day = datetime.now(local_tz) - timedelta(days=days_back)
    ymd = target_day.strftime("%Y-%m-%d")

    shifts = config["shift_settings"].get("shifts")
    if shifts:
        start_time = shifts[0]["start_time"]
        end_time = shifts[-1]["end_time"]
    else:
        start_time = config["shift_settings"]["start_time"]
        end_time = config["shift_settings"]["end_time"]

    b_start = local_tz.localize(datetime.strptime(f"{ymd} {start_time}", "%Y-%m-%d %H:%M:%S"))
    b_end = local_tz.localize(datetime.strptime(f"{ymd} {end_time}", "%Y-%m-%d %H:%M:%S"))

    return (
        b_start.astimezone(pytz.utc).strftime("%d.%m.%Y %H:%M:%S"),
        b_end.astimezone(pytz.utc).strftime("%d.%m.%Y %H:%M:%S"),
        ymd,
    )
