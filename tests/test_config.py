import os
from pathlib import Path

import pytest

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
    with pytest.raises(AttributeError):
        settings.binance_api_key = "other"


def test_new_fields_defaults():
    """New settings fields have correct defaults."""
    settings = Settings(binance_api_key="", binance_api_secret="")
    assert settings.base_url == "https://fapi.binance.com"
    assert settings.data_dir == Path("data")
    assert settings.symbols == ("BTCUSDT", "ETHUSDT")
    assert settings.intervals == ("1h",)
    assert settings.kline_limit == 1500
    assert settings.rate_limit_pause == 0.25


def test_load_new_fields_from_env(monkeypatch):
    """New settings load from environment variables."""
    monkeypatch.setenv("BINANCE_BASE_URL", "https://testnet.example.com")
    monkeypatch.setenv("DATA_DIR", "/tmp/mydata")
    monkeypatch.setenv("SYMBOLS", "SOLUSDT, BTCUSDT")
    monkeypatch.setenv("INTERVALS", "15m,1h")
    monkeypatch.setenv("KLINE_LIMIT", "500")
    monkeypatch.setenv("RATE_LIMIT_PAUSE", "0.5")
    settings = load_settings()
    assert settings.base_url == "https://testnet.example.com"
    assert settings.data_dir == Path("/tmp/mydata")
    assert settings.symbols == ("SOLUSDT", "BTCUSDT")
    assert settings.intervals == ("15m", "1h")
    assert settings.kline_limit == 500
    assert settings.rate_limit_pause == 0.5


def test_bulk_fields_defaults():
    """Bulk download settings have correct defaults."""
    settings = Settings(binance_api_key="", binance_api_secret="")
    assert settings.data_vision_base == "https://data.binance.vision"
    assert settings.bulk_rate_pause == 0.1


def test_bulk_fields_from_env(monkeypatch):
    """Bulk download settings load from environment variables."""
    monkeypatch.setenv("DATA_VISION_BASE", "https://custom.vision.url")
    monkeypatch.setenv("BULK_RATE_PAUSE", "0.5")
    settings = load_settings()
    assert settings.data_vision_base == "https://custom.vision.url"
    assert settings.bulk_rate_pause == 0.5
