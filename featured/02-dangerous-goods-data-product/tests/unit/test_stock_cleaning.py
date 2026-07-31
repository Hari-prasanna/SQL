import pandas as pd
from etl_pipeline import clean_stock_dataframe


def test_keeps_only_rows_with_a_numeric_handling_unit_reference():
    df = pd.DataFrame({
        "MAINLHM": ["123456", "ABC000", "987000", None],
        **{f"col{i}": [1, 2, 3, 4] for i in range(25)},
    })

    cleaned = clean_stock_dataframe(df)

    assert cleaned["MAINLHM"].tolist() == ["123456", "987000"]


def test_trims_to_the_first_22_columns():
    df = pd.DataFrame({
        "MAINLHM": ["123456"],
        **{f"col{i}": [1] for i in range(30)},
    })

    cleaned = clean_stock_dataframe(df)

    assert len(cleaned.columns) == 22


def test_applies_no_row_filter_when_mainlhm_is_missing():
    df = pd.DataFrame({f"col{i}": [None, None] for i in range(25)})

    cleaned = clean_stock_dataframe(df)

    assert len(cleaned) == 2
    assert len(cleaned.columns) == 22


def test_fills_missing_values_with_empty_string():
    df = pd.DataFrame({f"col{i}": [None] for i in range(25)})

    cleaned = clean_stock_dataframe(df)

    assert (cleaned == '').all().all()
