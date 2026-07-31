from unittest.mock import patch

from logistics_data_utils.notifications import build_webhook_card, send_webhook_notification


def test_success_card_has_no_reason_field():
    card = build_webhook_card("Test Job", "success")

    widgets = card["cards"][0]["sections"][0]["widgets"]
    labels = [w["keyValue"]["topLabel"] for w in widgets]

    assert "Reason" not in labels
    assert card["cards"][0]["header"]["title"].startswith("✅")


def test_failure_card_includes_error_reason():
    card = build_webhook_card("Test Job", "failure", error=ValueError("boom"))

    widgets = card["cards"][0]["sections"][0]["widgets"]
    reason = next(w["keyValue"]["content"] for w in widgets if w["keyValue"]["topLabel"] == "Reason")

    assert reason == "boom"
    assert card["cards"][0]["header"]["title"].startswith("❌")


def test_failure_card_defaults_reason_when_no_error_given():
    card = build_webhook_card("Test Job", "failure")

    widgets = card["cards"][0]["sections"][0]["widgets"]
    reason = next(w["keyValue"]["content"] for w in widgets if w["keyValue"]["topLabel"] == "Reason")

    assert reason == "Unknown error"


def test_send_webhook_notification_swallows_network_errors():
    with patch("logistics_data_utils.notifications.urllib.request.urlopen", side_effect=OSError("no network")):
        # Should not raise — failures to notify must not crash the calling job.
        send_webhook_notification("https://example.invalid/webhook", "Test Job", "failure")
