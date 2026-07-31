from logistics_data_utils.time_windows import get_utc_window


def _config_with_shifts():
    return {
        "shift_settings": {
            "timezone": "Europe/Berlin",
            "shifts": [
                {"shift_number": 1, "start_time": "05:50:00", "end_time": "14:44:59"},
                {"shift_number": 2, "start_time": "14:45:00", "end_time": "23:35:00"},
            ],
        }
    }


def _config_with_explicit_window():
    return {
        "shift_settings": {
            "timezone": "Europe/Berlin",
            "start_time": "00:00:00",
            "end_time": "23:59:59",
        }
    }


def test_window_uses_first_shift_start_and_last_shift_end():
    start_utc, end_utc, target_date = get_utc_window(_config_with_shifts(), days_back=0)

    assert target_date.count("-") == 2
    assert start_utc != end_utc


def test_window_respects_days_back():
    _, _, target_today = get_utc_window(_config_with_shifts(), days_back=0)
    _, _, target_yesterday = get_utc_window(_config_with_shifts(), days_back=1)

    assert target_today != target_yesterday


def test_window_falls_back_to_explicit_start_end_when_no_shifts_list():
    start_utc, end_utc, target_date = get_utc_window(_config_with_explicit_window(), days_back=0)

    assert start_utc and end_utc and target_date


def test_window_output_format_is_dd_mm_yyyy_hh_mm_ss():
    start_utc, end_utc, _ = get_utc_window(_config_with_shifts(), days_back=0)

    for value in (start_utc, end_utc):
        date_part, time_part = value.split(" ")
        assert len(date_part.split(".")) == 3
        assert len(time_part.split(":")) == 3
