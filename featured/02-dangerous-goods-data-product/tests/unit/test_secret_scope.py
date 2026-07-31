from etl_pipeline import get_secret_scope as etl_get_secret_scope
from notification_sender import get_secret_scope as notify_get_secret_scope


def test_etl_pipeline_returns_the_scope_from_the_environment_variable(monkeypatch):
    monkeypatch.setenv("SECRET_SCOPE", "test-scope-from-env")

    assert etl_get_secret_scope() == "test-scope-from-env"


def test_etl_pipeline_falls_back_to_the_placeholder_when_unset(monkeypatch):
    monkeypatch.delenv("SECRET_SCOPE", raising=False)

    assert etl_get_secret_scope() == "<SECRET_SCOPE>"


def test_notification_sender_uses_the_same_resolution(monkeypatch):
    monkeypatch.setenv("SECRET_SCOPE", "test-scope-from-env")

    assert notify_get_secret_scope() == "test-scope-from-env"


def test_notification_sender_falls_back_to_the_same_placeholder(monkeypatch):
    monkeypatch.delenv("SECRET_SCOPE", raising=False)

    assert notify_get_secret_scope() == "<SECRET_SCOPE>"
