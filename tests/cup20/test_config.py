# tests/cup20/test_config.py
from pathlib import Path

import pytest

from crypto_trade.cup20.config import IS_END, SEALED_END, SEALED_START, load_config, validate_config

CONFIG_PATH = Path("tournament/cup20/config.toml")


def test_windows_are_frozen_utc_timestamps():
    assert str(IS_END) == "2024-08-01 00:00:00+00:00"
    assert str(SEALED_START) == "2024-08-01 00:00:00+00:00"
    assert str(SEALED_END) == "2026-08-01 00:00:00+00:00"


def test_load_config_returns_bytes_hash_and_policy():
    loaded = load_config(CONFIG_PATH)
    assert len(loaded.sha256) == 64
    assert loaded.raw["universe"]["target_size"] == 20
    assert loaded.raw["universe"]["entry_rank"] == 20
    assert loaded.raw["universe"]["exit_rank"] == 25
    assert loaded.raw["universe"]["lookback_days"] == 180
    assert loaded.raw["execution"]["taker_fee_bps_per_side"] == 5.0
    assert loaded.raw["execution"]["slippage_bps_per_side"] == 2.5
    assert loaded.raw["risk_unit"]["target_annualized_volatility"] == 0.10
    assert loaded.raw["research"]["trial_budget"] == 12
    assert loaded.raw["selection"]["advancing_slots"] == 3
    assert len(loaded.raw["mandates"]) == 12


def test_validate_config_rejects_drift():
    loaded = load_config(CONFIG_PATH)
    tampered = {
        key: dict(value) if isinstance(value, dict) else value for key, value in loaded.raw.items()
    }
    tampered["universe"]["target_size"] = 40
    with pytest.raises(ValueError):
        validate_config(tampered)


def test_validate_config_rejects_unknown_table():
    loaded = load_config(CONFIG_PATH)
    tampered = dict(loaded.raw)
    tampered["surprise"] = {}
    with pytest.raises(ValueError):
        validate_config(tampered)
