import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    binance_api_key: str
    binance_api_secret: str
    base_url: str = "https://fapi.binance.com"
    data_dir: Path = Path("data")
    symbols: tuple[str, ...] = ("BTCUSDT", "ETHUSDT")
    intervals: tuple[str, ...] = ("1h",)
    kline_limit: int = 1500
    rate_limit_pause: float = 0.25
    data_vision_base: str = "https://data.binance.vision"
    bulk_rate_pause: float = 0.1


def _parse_tuple(value: str) -> tuple[str, ...]:
    """Parse a comma-separated string into a tuple of stripped strings."""
    return tuple(s.strip() for s in value.split(",") if s.strip())


def load_settings() -> Settings:
    """Load settings from environment variables."""
    api_key = os.environ.get("BINANCE_API_KEY", "")
    api_secret = os.environ.get("BINANCE_API_SECRET", "")

    kwargs: dict = {
        "binance_api_key": api_key,
        "binance_api_secret": api_secret,
    }

    if base_url := os.environ.get("BINANCE_BASE_URL"):
        kwargs["base_url"] = base_url
    if data_dir := os.environ.get("DATA_DIR"):
        kwargs["data_dir"] = Path(data_dir)
    if symbols := os.environ.get("SYMBOLS"):
        kwargs["symbols"] = _parse_tuple(symbols)
    if intervals := os.environ.get("INTERVALS"):
        kwargs["intervals"] = _parse_tuple(intervals)
    if kline_limit := os.environ.get("KLINE_LIMIT"):
        kwargs["kline_limit"] = int(kline_limit)
    if rate_limit_pause := os.environ.get("RATE_LIMIT_PAUSE"):
        kwargs["rate_limit_pause"] = float(rate_limit_pause)
    if data_vision_base := os.environ.get("DATA_VISION_BASE"):
        kwargs["data_vision_base"] = data_vision_base
    if bulk_rate_pause := os.environ.get("BULK_RATE_PAUSE"):
        kwargs["bulk_rate_pause"] = float(bulk_rate_pause)

    return Settings(**kwargs)
