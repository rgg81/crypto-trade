import os

from crypto_trade.config import Settings, load_settings


def test_load_settings_defaults():
    """Settings load with empty defaults when env vars are not set."""
    os.environ.pop("BINANCE_API_KEY", None)
    os.environ.pop("BINANCE_API_SECRET", None)
    settings = load_settings()
    assert settings.binance_api_key == ""
    assert settings.binance_api_secret == ""


def test_load_settings_from_env(monkeypatch):
    """Settings load values from environment variables."""
    monkeypatch.setenv("BINANCE_API_KEY", "test_key")
    monkeypatch.setenv("BINANCE_API_SECRET", "test_secret")
    settings = load_settings()
    assert settings.binance_api_key == "test_key"
    assert settings.binance_api_secret == "test_secret"


def test_settings_immutable():
    """Settings dataclass is frozen."""
    settings = Settings(binance_api_key="k", binance_api_secret="s")
    try:
        settings.binance_api_key = "other"
        assert False, "Should have raised FrozenInstanceError"
    except AttributeError:
        pass
