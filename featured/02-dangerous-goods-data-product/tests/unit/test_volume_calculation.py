import json
from pathlib import Path

import pandas as pd
from etl_pipeline import compute_volumes

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "sample_calc_rows.json"


def _load_calc_df() -> pd.DataFrame:
    data = json.loads(FIXTURE.read_text())
    return pd.DataFrame(data["rows"], columns=data["header"])


def test_total_volume_sums_every_row_regardless_of_mask():
    df_calc = _load_calc_df()

    total_vol, _ = compute_volumes(df_calc)

    assert total_vol == 3150.0


def test_ready_volume_only_counts_outlet_non_olap_non_fin_50_prefixed_rows():
    df_calc = _load_calc_df()

    _, ready_vol = compute_volumes(df_calc)

    # Only rows 1 ("WH01"/"OUTLET"/1,200/"500123") and 6 ("WH02"/"OUTLET"/800/"502")
    # satisfy all four conditions.
    assert ready_vol == 2000.0


def test_returns_floats_not_numpy_or_pandas_scalar_types():
    df_calc = _load_calc_df()

    total_vol, ready_vol = compute_volumes(df_calc)

    assert isinstance(total_vol, float)
    assert isinstance(ready_vol, float)
