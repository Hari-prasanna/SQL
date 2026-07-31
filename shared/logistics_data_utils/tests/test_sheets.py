import pandas as pd
from logistics_data_utils.sheets import update_google_sheet_idempotent


class FakeSheet:
    """In-memory stand-in for a gspread Worksheet, just enough surface area for
    update_google_sheet_idempotent."""

    def __init__(self, initial_rows=None):
        self.rows = initial_rows or []  # list of lists, row[0] is index 1

    def col_values(self, index):
        return [row[index - 1] for row in self.rows]

    def delete_rows(self, start, end):
        del self.rows[start - 1 : end]

    def append_row(self, row):
        self.rows.append(row)

    def append_rows(self, rows, value_input_option="USER_ENTERED"):
        self.rows.extend(rows)


def test_empty_dataframe_is_a_noop():
    sheet = FakeSheet(initial_rows=[["header"], ["2026-01-01", "5"]])
    update_google_sheet_idempotent(sheet, pd.DataFrame(), match_value="2026-01-01")

    assert sheet.rows == [["header"], ["2026-01-01", "5"]]


def test_first_write_appends_header_and_rows():
    sheet = FakeSheet(initial_rows=[])
    df = pd.DataFrame({"date": ["2026-01-01"], "count": [3]})

    update_google_sheet_idempotent(sheet, df, match_value="2026-01-01", date_col_index=1)

    assert sheet.rows[0] == ["DATE", "COUNT"]
    assert sheet.rows[1] == ["2026-01-01", 3]


def test_rerun_for_same_date_replaces_rows_not_duplicates_them():
    sheet = FakeSheet(
        initial_rows=[
            ["DATE", "COUNT"],
            ["2026-01-01", 3],
            ["2026-01-02", 7],
        ]
    )
    df = pd.DataFrame({"date": ["2026-01-01"], "count": [99]})

    update_google_sheet_idempotent(sheet, df, match_value="2026-01-01", date_col_index=1)

    dates = [row[0] for row in sheet.rows]
    assert dates.count("2026-01-01") == 1
    assert ["2026-01-02", 7] in sheet.rows


def test_rerun_does_not_touch_other_dates():
    sheet = FakeSheet(initial_rows=[["DATE", "COUNT"], ["2026-01-02", 7]])
    df = pd.DataFrame({"date": ["2026-01-01"], "count": [1]})

    update_google_sheet_idempotent(sheet, df, match_value="2026-01-01", date_col_index=1)

    assert ["2026-01-02", 7] in sheet.rows
