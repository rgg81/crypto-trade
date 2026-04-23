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
    """LiveConfig.all_symbols deduplicates across models — v0.186 portfolio."""
    config = LiveConfig()  # baseline defaults
    syms = config.all_symbols
    assert syms == ("BTCUSDT", "ETHUSDT", "LINKUSDT", "LTCUSDT", "DOTUSDT")
    assert len(syms) == 5


# ---------------------------------------------------------------------------
# Iter 197: baseline model shape (A/C/D/E with R1/R2/R3) and R3 forwarding
# ---------------------------------------------------------------------------


def test_baseline_models_shape():
    """BASELINE_MODELS matches v0.186: A (no R1), C (R1), D=LTC (R1), E=DOT (R1+R2)."""
    from crypto_trade.live.models import BASELINE_MODELS, OOD_FEATURE_COLUMNS

    assert len(BASELINE_MODELS) == 4
    names = [m.name for m in BASELINE_MODELS]
    assert names == ["A", "C", "D", "E"]

    by_name = {m.name: m for m in BASELINE_MODELS}
    # A: BTC+ETH, no R1 or R2
    assert by_name["A"].symbols == ("BTCUSDT", "ETHUSDT")
    assert by_name["A"].risk_consecutive_sl_limit is None
    assert by_name["A"].risk_drawdown_scale_enabled is False
    # C: LINK, R1 on
    assert by_name["C"].symbols == ("LINKUSDT",)
    assert by_name["C"].risk_consecutive_sl_limit == 3
    assert by_name["C"].risk_consecutive_sl_cooldown_candles == 27
    # D: LTC (not BNB), R1 on
    assert by_name["D"].symbols == ("LTCUSDT",)
    assert by_name["D"].risk_consecutive_sl_limit == 3
    # E: DOT, R1 + R2
    assert by_name["E"].symbols == ("DOTUSDT",)
    assert by_name["E"].risk_consecutive_sl_limit == 3
    assert by_name["E"].risk_drawdown_scale_enabled is True
    assert by_name["E"].risk_drawdown_trigger_pct == 7.0
    assert by_name["E"].risk_drawdown_scale_anchor_pct == 15.0
    assert by_name["E"].risk_drawdown_scale_floor == 0.33

    # All four have R3 enabled with uniform config
    for mc in BASELINE_MODELS:
        assert mc.ood_enabled is True
        assert mc.ood_cutoff_pct == 0.70
        assert mc.ood_features == OOD_FEATURE_COLUMNS


def test_model_runner_forwards_r3():
    """ModelRunner passes ood_enabled/features/cutoff_pct from ModelConfig
    through to LightGbmStrategy."""
    from crypto_trade.live.models import OOD_FEATURE_COLUMNS

    mc = ModelConfig(
        name="E",
        symbols=("DOTUSDT",),
        use_atr_labeling=True,
        atr_tp_multiplier=3.5,
        atr_sl_multiplier=1.75,
        ood_enabled=True,
        ood_features=OOD_FEATURE_COLUMNS,
        ood_cutoff_pct=0.55,
    )
    config = LiveConfig(features_dir=Path("/tmp/nonexistent_features"))
    runner = ModelRunner(mc, config)
    assert runner.strategy.ood_enabled is True
    assert tuple(runner.strategy.ood_features or ()) == OOD_FEATURE_COLUMNS
    assert runner.strategy.ood_cutoff_pct == 0.55


def test_model_runner_r3_disabled():
    """If model config disables R3, strategy.ood_features is None."""
    mc = ModelConfig(
        name="A",
        symbols=("BTCUSDT",),
        use_atr_labeling=True,
        atr_tp_multiplier=2.9,
        atr_sl_multiplier=1.45,
        ood_enabled=False,
    )
    config = LiveConfig(features_dir=Path("/tmp/nonexistent_features"))
    runner = ModelRunner(mc, config)
    assert runner.strategy.ood_enabled is False
    assert runner.strategy.ood_features is None


# ---------------------------------------------------------------------------
# Iter 197: R1 / R2 state tracking on the engine
# ---------------------------------------------------------------------------


def _make_closed_live_trade(
    model_name: str,
    symbol: str,
    exit_reason: str,
    exit_time: int,
    *,
    direction: int = 1,
    entry_price: float = 100.0,
    exit_price: float | None = None,
    weight_factor: float = 1.0,
    open_time: int | None = None,
):
    from crypto_trade.live.models import LiveTrade

    if exit_price is None:
        exit_price = entry_price * (1.08 if exit_reason == "take_profit" else 0.96)
    return LiveTrade(
        model_name=model_name,
        symbol=symbol,
        direction=direction,
        entry_price=entry_price,
        amount_usd=1000.0 * weight_factor,
        weight_factor=weight_factor,
        stop_loss_price=entry_price * 0.96,
        take_profit_price=entry_price * 1.08,
        open_time=open_time or exit_time - 86_400_000,
        timeout_time=exit_time + 100,
        signal_time=open_time or exit_time - 86_400_000,
        status="closed",
        exit_price=exit_price,
        exit_time=exit_time,
        exit_reason=exit_reason,
    )


def _make_engine_for_risk_tests(tmp_path, models: tuple[ModelConfig, ...]):
    """Construct a LiveEngine in dry-run mode with a temp DB."""
    from crypto_trade.live.engine import LiveEngine

    cfg = LiveConfig(
        models=models,
        data_dir=tmp_path,
        features_dir=tmp_path / "features",
        db_path=tmp_path / "live.db",
        dry_run=True,
    )
    engine = LiveEngine(cfg)
    return engine


def test_engine_r1_arms_cooldown_after_k_sls(tmp_path):
    """_record_trade_close_for_risk arms R1 cooldown after K consecutive SLs."""
    mc = ModelConfig(
        name="C",
        symbols=("LINKUSDT",),
        use_atr_labeling=True,
        atr_tp_multiplier=3.5,
        atr_sl_multiplier=1.75,
        risk_consecutive_sl_limit=3,
        risk_consecutive_sl_cooldown_candles=27,
    )
    engine = _make_engine_for_risk_tests(tmp_path, (mc,))
    candle_ms = engine._candle_duration_ms

    # 2 consecutive SLs: streak=2, no cooldown yet
    engine._record_trade_close_for_risk(
        _make_closed_live_trade("C", "LINKUSDT", "stop_loss", 1000)
    )
    engine._record_trade_close_for_risk(
        _make_closed_live_trade("C", "LINKUSDT", "stop_loss", 2000)
    )
    assert engine._sl_streak["LINKUSDT"] == 2
    assert "LINKUSDT" not in engine._risk_cooldown_until

    # 3rd SL hits threshold: streak resets, cooldown armed
    engine._record_trade_close_for_risk(
        _make_closed_live_trade("C", "LINKUSDT", "stop_loss", 3000)
    )
    assert engine._sl_streak["LINKUSDT"] == 0
    assert engine._risk_cooldown_until["LINKUSDT"] == 3000 + 27 * candle_ms

    # A TP exit (post cooldown) resets the streak counter.
    engine._record_trade_close_for_risk(
        _make_closed_live_trade("C", "LINKUSDT", "take_profit", 9999)
    )
    assert engine._sl_streak["LINKUSDT"] == 0


def test_engine_r1_disabled_for_model_a(tmp_path):
    """Model A has no R1 — SL streak is not tracked."""
    mc = ModelConfig(
        name="A",
        symbols=("BTCUSDT", "ETHUSDT"),
        use_atr_labeling=True,
        atr_tp_multiplier=2.9,
        atr_sl_multiplier=1.45,
    )
    engine = _make_engine_for_risk_tests(tmp_path, (mc,))
    for t in range(1, 10):
        engine._record_trade_close_for_risk(
            _make_closed_live_trade("A", "BTCUSDT", "stop_loss", t * 1000)
        )
    assert engine._sl_streak == {}
    assert engine._risk_cooldown_until == {}


def test_engine_r2_scale_within_dd_band(tmp_path):
    """R2 drawdown scale: at trigger it's 1.0; at anchor it's floor; linear in between."""
    mc = ModelConfig(
        name="E",
        symbols=("DOTUSDT",),
        use_atr_labeling=True,
        atr_tp_multiplier=3.5,
        atr_sl_multiplier=1.75,
        risk_drawdown_scale_enabled=True,
        risk_drawdown_trigger_pct=7.0,
        risk_drawdown_scale_anchor_pct=15.0,
        risk_drawdown_scale_floor=0.33,
    )
    engine = _make_engine_for_risk_tests(tmp_path, (mc,))

    # No drawdown yet → scale 1.0
    assert engine._r2_scale_for("E") == 1.0

    # Manually set state to simulate a 10% drawdown (between trigger=7 and anchor=15).
    engine._peak_weighted_pnl["E"] = 20.0
    engine._cum_weighted_pnl["E"] = 10.0
    span = (10.0 - 7.0) / (15.0 - 7.0)  # 0.375
    expected = 1.0 - span * (1.0 - 0.33)
    assert abs(engine._r2_scale_for("E") - expected) < 1e-9

    # At anchor drawdown → scale == floor
    engine._cum_weighted_pnl["E"] = 5.0  # dd = 15
    assert abs(engine._r2_scale_for("E") - 0.33) < 1e-9

    # Below trigger → scale 1.0
    engine._cum_weighted_pnl["E"] = 15.0  # dd = 5 < trigger
    assert engine._r2_scale_for("E") == 1.0


def test_engine_r2_records_weighted_pnl_and_peak(tmp_path):
    """_record_trade_close_for_risk accumulates weighted_pnl and updates peak."""
    mc = ModelConfig(
        name="E",
        symbols=("DOTUSDT",),
        use_atr_labeling=True,
        atr_tp_multiplier=3.5,
        atr_sl_multiplier=1.75,
        risk_drawdown_scale_enabled=True,
        risk_drawdown_trigger_pct=7.0,
        risk_drawdown_scale_anchor_pct=15.0,
        risk_drawdown_scale_floor=0.33,
    )
    engine = _make_engine_for_risk_tests(tmp_path, (mc,))

    # TP trade: ~+7.8% net (8% gross - 0.1% fee * 2 = 7.8% net) * weight_factor 1.0
    engine._record_trade_close_for_risk(
        _make_closed_live_trade("E", "DOTUSDT", "take_profit", 1000)
    )
    cum1 = engine._cum_weighted_pnl["E"]
    assert cum1 > 0
    assert engine._peak_weighted_pnl["E"] == cum1

    # SL trade: drops cum below peak
    engine._record_trade_close_for_risk(
        _make_closed_live_trade("E", "DOTUSDT", "stop_loss", 2000)
    )
    cum2 = engine._cum_weighted_pnl["E"]
    assert cum2 < cum1
    assert engine._peak_weighted_pnl["E"] == cum1  # peak unchanged


def test_engine_rebuild_risk_state_from_db(tmp_path):
    """_rebuild_risk_state replays closed trades from DB into R1/R2 state."""
    mc_c = ModelConfig(
        name="C",
        symbols=("LINKUSDT",),
        use_atr_labeling=True,
        atr_tp_multiplier=3.5,
        atr_sl_multiplier=1.75,
        risk_consecutive_sl_limit=3,
        risk_consecutive_sl_cooldown_candles=27,
    )
    mc_e = ModelConfig(
        name="E",
        symbols=("DOTUSDT",),
        use_atr_labeling=True,
        atr_tp_multiplier=3.5,
        atr_sl_multiplier=1.75,
        risk_consecutive_sl_limit=3,
        risk_consecutive_sl_cooldown_candles=27,
        risk_drawdown_scale_enabled=True,
    )
    engine = _make_engine_for_risk_tests(tmp_path, (mc_c, mc_e))

    # Persist 3 consecutive LINK SLs and 2 DOT trades to the state store.
    ts = 1_000_000_000_000
    for i in range(3):
        engine._state.upsert_trade(
            _make_closed_live_trade("C", "LINKUSDT", "stop_loss", ts + i * 100)
        )
    engine._state.upsert_trade(
        _make_closed_live_trade("E", "DOTUSDT", "take_profit", ts + 1000)
    )
    engine._state.upsert_trade(
        _make_closed_live_trade("E", "DOTUSDT", "stop_loss", ts + 2000)
    )

    # Wipe in-memory state, then rebuild from DB.
    engine._sl_streak = {}
    engine._risk_cooldown_until = {}
    engine._cum_weighted_pnl = {"C": 0.0, "E": 0.0}
    engine._peak_weighted_pnl = {"C": 0.0, "E": 0.0}
    engine._rebuild_risk_state()

    # R1: LINK hit 3 SLs → cooldown armed, streak reset.
    assert engine._sl_streak.get("LINKUSDT", 0) == 0
    assert "LINKUSDT" in engine._risk_cooldown_until
    # R2: E has one TP + one SL. Cum = TP_wpnl + SL_wpnl, peak = TP_wpnl only.
    assert engine._cum_weighted_pnl["E"] > -100
    assert engine._peak_weighted_pnl["E"] > 0
    assert engine._peak_weighted_pnl["E"] >= engine._cum_weighted_pnl["E"]
