import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    binance_api_key: str
    binance_api_secret: str


def load_settings() -> Settings:
    """Load settings from environment variables."""
    api_key = os.environ.get("BINANCE_API_KEY", "")
    api_secret = os.environ.get("BINANCE_API_SECRET", "")
    return Settings(binance_api_key=api_key, binance_api_secret=api_secret)
