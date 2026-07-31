import json

from backlog_clarification_webhook import build_payload


def test_payload_contains_the_combined_total():
    payload = json.loads(build_payload(42))

    assert "42" in payload["text"]


def test_payload_is_valid_json_with_a_text_key():
    payload = json.loads(build_payload(0))

    assert set(payload.keys()) == {"text"}
