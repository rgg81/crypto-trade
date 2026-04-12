"""Integration test for the engine — ModelRunner warmup and signal flow."""

from pathlib import Path

import pandas as pd

from crypto_trade.live.engine import ModelRunner
from crypto_trade.live.models import LiveConfig, ModelConfig


def _make_master(symbols: list[str], n_candles: int = 100) -> pd.DataFrame:
    """Create a minimal master DataFrame for testing compute_features."""
    rows = []
    for i in range(n_candles):
        ot = 1000000 + i * 28800000  # 8h intervals
        for sym in symbols:
            rows.append(
                {
                    "open_time": ot,
                    "open": 60000.0 + i * 10,
                    "high": 60500.0 + i * 10,
                    "low": 59500.0 + i * 10,
                    "close": 60100.0 + i * 10,
                    "volume": 100.0,
                    "close_time": ot + 28799999,
                    "quote_volume": 6000000.0,
                    "trades": 500,
                    "taker_buy_volume": 50.0,
                    "taker_buy_quote_volume": 3000000.0,
                }
            )
    df = pd.DataFrame(rows)
    syms = symbols * n_candles
    df["symbol"] = pd.Categorical(syms)
    df.sort_values(["open_time", "symbol"], ignore_index=True, inplace=True)
    return df


def test_model_runner_warmup_and_compute():
    """ModelRunner can warmup with compute_features without error."""
    mc = ModelConfig(
        name="A",
        symbols=("BTCUSDT", "ETHUSDT"),
        use_atr_labeling=True,
        atr_tp_multiplier=2.9,
        atr_sl_multiplier=1.45,
    )
    config = LiveConfig(features_dir=Path("/tmp/nonexistent_features"))
    runner = ModelRunner(mc, config)

    master = _make_master(["BTCUSDT", "ETHUSDT"], n_candles=50)
    # Should not raise — compute_features is lightweight
    runner.warmup(master)

    # get_signal should return NO_SIGNAL when no Parquet features exist
    sig = runner.get_signals(
        {
            "BTCUSDT": master["open_time"].iloc[-2],
        }
    )
    assert "BTCUSDT" in sig
    assert sig["BTCUSDT"].direction == 0  # NO_SIGNAL


def test_model_runner_only_processes_own_symbols():
    """ModelRunner ignores symbols not in its model config."""
    mc = ModelConfig(
        name="C",
        symbols=("LINKUSDT",),
        use_atr_labeling=True,
        atr_tp_multiplier=3.5,
        atr_sl_multiplier=1.75,
    )
    config = LiveConfig(features_dir=Path("/tmp/nonexistent_features"))
    runner = ModelRunner(mc, config)

    master = _make_master(["LINKUSDT"], n_candles=50)
    runner.warmup(master)

    # Should only return signal for LINKUSDT, not BTCUSDT
    sigs = runner.get_signals(
        {
            "LINKUSDT": master["open_time"].iloc[-2],
            "BTCUSDT": 999999,  # not in model
        }
    )
    assert "LINKUSDT" in sigs
    assert "BTCUSDT" not in sigs


def test_live_config_all_symbols():
    """LiveConfig.all_symbols deduplicates across models."""
    config = LiveConfig()  # baseline defaults
    syms = config.all_symbols
    assert "BTCUSDT" in syms
    assert "ETHUSDT" in syms
    assert "LINKUSDT" in syms
    assert "BNBUSDT" in syms
    assert len(syms) == 4
