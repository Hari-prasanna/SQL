import json

from logistics_data_utils.config import load_config


def test_load_config_reads_json_from_base_dir(tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({"a": 1, "b": {"c": 2}}))

    result = load_config(base_dir=str(tmp_path))

    assert result == {"a": 1, "b": {"c": 2}}


def test_load_config_supports_custom_filename(tmp_path):
    (tmp_path / "custom.json").write_text(json.dumps({"x": True}))

    result = load_config(base_dir=str(tmp_path), filename="custom.json")

    assert result == {"x": True}
