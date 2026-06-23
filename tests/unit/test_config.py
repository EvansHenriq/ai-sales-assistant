from app.core.config import Settings


def test_cors_origins_parsed_from_csv_string() -> None:
    settings = Settings(cors_allow_origins="http://a.com, http://b.com")  # type: ignore[arg-type]
    assert settings.cors_allow_origins == ["http://a.com", "http://b.com"]


def test_cors_origins_accepts_list() -> None:
    settings = Settings(cors_allow_origins=["http://a.com"])
    assert settings.cors_allow_origins == ["http://a.com"]


def test_json_logs_enabled_outside_local() -> None:
    assert Settings(environment="production").json_logs is True
    assert Settings(environment="local").json_logs is False


def test_api_key_is_secret() -> None:
    settings = Settings(openai_api_key="super-secret")  # type: ignore[arg-type]
    # Secret value must not leak via repr/str.
    assert "super-secret" not in repr(settings.openai_api_key)
    assert settings.openai_api_key.get_secret_value() == "super-secret"
