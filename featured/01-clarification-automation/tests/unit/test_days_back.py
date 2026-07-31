from unittest.mock import MagicMock

from clarification_bookings import get_days_back


def test_uses_widget_value_when_a_day_is_provided():
    dbx_utils = MagicMock()
    dbx_utils.widgets.get.return_value = "2020-01-01"

    days_back = get_days_back(dbx_utils, config={})

    assert days_back > 0  # any date in the past relative to "today" in the test run


def test_falls_back_to_config_default_when_no_widget_value():
    dbx_utils = MagicMock()
    dbx_utils.widgets.get.return_value = ""

    days_back = get_days_back(dbx_utils, config={"run_settings": {"days_back": 3}})

    assert days_back == 3


def test_falls_back_to_zero_when_no_widget_and_no_config_default():
    dbx_utils = MagicMock()
    dbx_utils.widgets.get.return_value = ""

    days_back = get_days_back(dbx_utils, config={})

    assert days_back == 0
