import json
from pathlib import Path

from logistics_data_utils import get_utc_window

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "sample_config.json"


def test_shared_get_utc_window_accepts_this_projects_config_shape():
    config = json.loads(FIXTURE.read_text())

    start_utc, end_utc, target_date = get_utc_window(config, days_back=0)

    assert start_utc and end_utc and target_date
