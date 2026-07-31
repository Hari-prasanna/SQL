from notification_sender import CARD_TITLE, build_card

CONFIG_LINKS = {
    "looker_dashboard": "<DASHBOARD_URL>",
    "sheet_overview": "<GOOGLE_SHEET_OVERVIEW_URL>",
    "sheet_manual": "<GOOGLE_SHEET_MANUAL_IMPORT_URL>",
}


def test_success_card_uses_the_generic_card_title():
    payload = build_card(
        status="SUCCESS",
        rows=120,
        total_vol=3150.0,
        ready_vol=2000.0,
        time_str="31/07/2026 05:40:12",
        config_links=CONFIG_LINKS,
    )

    card = payload["cardsV2"][0]["card"]

    assert card["header"]["title"] == CARD_TITLE


def test_success_card_links_to_the_configured_dashboard():
    payload = build_card(
        status="SUCCESS",
        rows=120,
        total_vol=3150.0,
        ready_vol=2000.0,
        time_str="31/07/2026 05:40:12",
        config_links=CONFIG_LINKS,
    )

    card = payload["cardsV2"][0]["card"]
    buttons = card["sections"][-1]["widgets"][0]["buttonList"]["buttons"]
    urls = [b["onClick"]["openLink"]["url"] for b in buttons]

    assert CONFIG_LINKS["looker_dashboard"] in urls
    assert CONFIG_LINKS["sheet_overview"] in urls


def test_failure_card_includes_the_manual_fallback_link_and_error_reason():
    payload = build_card(
        status="FAILURE",
        rows=0,
        total_vol=0.0,
        ready_vol=0.0,
        time_str="--:--",
        config_links=CONFIG_LINKS,
        error_msg="Source query returned 0 rows. Aborting job.",
    )

    card = payload["cardsV2"][0]["card"]
    widgets = card["sections"][0]["widgets"]

    reason_text = widgets[0]["textParagraph"]["text"]
    assert "Source query returned 0 rows" in reason_text

    button = widgets[-1]["buttonList"]["buttons"][0]
    assert button["onClick"]["openLink"]["url"] == CONFIG_LINKS["sheet_manual"]


def test_is_valid_json_serializable_payload():
    import json

    payload = build_card(
        status="SUCCESS",
        rows=1,
        total_vol=1.0,
        ready_vol=1.0,
        time_str="01/01/2026 00:00:00",
        config_links=CONFIG_LINKS,
    )

    # Round-trips cleanly, which is what requests.post(json=payload) relies on.
    json.loads(json.dumps(payload))
