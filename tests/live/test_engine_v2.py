"""Live-engine tests for v2 wrapper, V2 baseline models, and combined-track guards.

This file accumulates as Tasks 1-9 land. It mirrors `test_engine.py` for
v1, but covers the new code paths that v2 introduces:
  - Per-model `ModelConfig` overrides (Task 1)
  - `ModelRunner` field resolution with `LiveConfig` fallback (Task 2)
  - `RiskV2Wrapper` wrapping when `risk_wrapper="v2"` (Task 3)
  - `V2_BASELINE_MODELS` / `COMBINED_MODELS` shape (Task 5)
  - `LiveEngine` exclusion + disjointness guards (Task 6)
  - BTC trend filter helper (Task 7)
  - `LiveEngine.catch_up_only()` smoke (Task 9)
"""
from __future__ import annotations

from pathlib import Path

import pytest

from crypto_trade.live.models import LiveConfig, ModelConfig


# ----------------------------- Task 1 ---------------------------------------


def test_v1_model_config_keeps_defaults_unchanged():
    """All new override fields default to None ⇒ v1 ModelConfigs preserve pre-change behavior."""
    mc = ModelConfig(
        name="A",
        symbols=("BTCUSDT", "ETHUSDT"),
        use_atr_labeling=True,
        atr_tp_multiplier=2.9,
        atr_sl_multiplier=1.45,
    )
    assert mc.feature_columns is None
    assert mc.features_dir is None
    assert mc.atr_column is None
    assert mc.cooldown_candles is None
    assert mc.vol_targeting is None
    assert mc.ensemble_seeds is None
    assert mc.risk_wrapper == "none"
    assert mc.risk_v2_config is None


# ----------------------------- Task 2 ---------------------------------------


def test_model_runner_resolves_with_fallback():
    """ModelRunner exposes resolved fields and inner_strategy / inner_atr_column.

    A v1-style ModelConfig (all overrides None) resolves to LiveConfig values.
    A v2-style ModelConfig with overrides resolves to its own values, and its
    inner_atr_column reflects the explicit atr_column kwarg passed to LightGbm.
    """
    from crypto_trade.live.engine import ModelRunner

    live = LiveConfig()  # cooldown_candles=2, features_dir=Path("data/features"), ...

    mc_default = ModelConfig(
        name="A",
        symbols=("BTCUSDT",),
        use_atr_labeling=True,
        atr_tp_multiplier=2.9,
        atr_sl_multiplier=1.45,
    )
    mc_override = ModelConfig(
        name="V2-DOGE",
        symbols=("DOGEUSDT",),
        use_atr_labeling=True,
        atr_tp_multiplier=2.9,
        atr_sl_multiplier=1.45,
        cooldown_candles=4,
        features_dir=Path("data/features_v2"),
        atr_column="natr_21_raw",
        vol_targeting=False,
    )

    r1 = ModelRunner(mc_default, live)
    r2 = ModelRunner(mc_override, live)

    # v1 defaults fall back to LiveConfig
    assert r1.cooldown_candles == 2
    assert str(r1.features_dir) == "data/features"
    assert r1.vol_targeting is True
    assert r1.inner_atr_column == "vol_natr_21"  # LightGbmStrategy default
    assert r1.inner_strategy is r1.strategy  # no wrapping yet (Task 3)

    # v2 overrides take precedence
    assert r2.cooldown_candles == 4
    assert str(r2.features_dir) == "data/features_v2"
    assert r2.vol_targeting is False
    assert r2.inner_atr_column == "natr_21_raw"


# ----------------------------- Task 3 ---------------------------------------


def test_v2_runner_wraps_strategy_with_riskv2():
    """When risk_wrapper='v2', ModelRunner wraps the inner LGBM in RiskV2Wrapper."""
    from crypto_trade.live.engine import ModelRunner
    from crypto_trade.strategies.ml.risk_v2 import RiskV2Config, RiskV2Wrapper

    live = LiveConfig()
    mc = ModelConfig(
        name="V2-DOGE",
        symbols=("DOGEUSDT",),
        use_atr_labeling=True,
        atr_tp_multiplier=2.9,
        atr_sl_multiplier=1.45,
        atr_column="natr_21_raw",
        features_dir=Path("data/features_v2"),
        cooldown_candles=4,
        vol_targeting=False,
        ood_enabled=False,
        risk_wrapper="v2",
        risk_v2_config=RiskV2Config(zscore_threshold=2.5),
    )
    runner = ModelRunner(mc, live)
    assert isinstance(runner.strategy, RiskV2Wrapper)
    # Inner strategy stays accessible — patcher relies on this
    assert runner.inner_strategy is not runner.strategy
    assert runner.inner_strategy is runner.strategy.inner
    # Wrapper must expose atr_column for use by the patcher and any caller
    # that currently reads strategy.atr_column directly.
    assert runner.strategy.atr_column == runner.inner_atr_column == "natr_21_raw"


def test_v2_runner_requires_risk_v2_config():
    """risk_wrapper='v2' without a config must raise — no silent default."""
    from crypto_trade.live.engine import ModelRunner

    live = LiveConfig()
    mc = ModelConfig(
        name="V2-bad",
        symbols=("DOGEUSDT",),
        use_atr_labeling=True,
        atr_tp_multiplier=2.9,
        atr_sl_multiplier=1.45,
        risk_wrapper="v2",
        risk_v2_config=None,
    )
    with pytest.raises(ValueError, match="risk_v2_config"):
        ModelRunner(mc, live)


# ----------------------------- Task 5 ---------------------------------------


def test_v2_baseline_models_shape():
    """V2_BASELINE_MODELS mirrors run_baseline_v2.V2_MODELS field-for-field."""
    from crypto_trade.live.models import V2_BASELINE_MODELS, V2_EXCLUDED_SYMBOLS

    expected_symbols = {"DOGEUSDT", "SOLUSDT", "XRPUSDT", "NEARUSDT"}
    actual_symbols = {s for mc in V2_BASELINE_MODELS for s in mc.symbols}
    assert actual_symbols == expected_symbols
    assert len(V2_BASELINE_MODELS) == 4

    for mc in V2_BASELINE_MODELS:
        assert mc.risk_wrapper == "v2"
        assert mc.risk_v2_config is not None
        # ood_enabled MUST be False — v2's z-score OOD lives in the wrapper;
        # leaving v1's R3 Mahalanobis enabled would double-gate.
        assert mc.ood_enabled is False
        assert mc.atr_column == "natr_21_raw"
        assert mc.cooldown_candles == 4
        assert mc.vol_targeting is False
        assert str(mc.features_dir) == "data/features_v2"
        assert mc.atr_tp_multiplier == 2.9
        assert mc.atr_sl_multiplier == 1.45
        assert set(mc.symbols).isdisjoint(V2_EXCLUDED_SYMBOLS)


def test_combined_models_unions_v1_and_v2():
    from crypto_trade.live.models import (
        BASELINE_MODELS,
        COMBINED_MODELS,
        V2_BASELINE_MODELS,
    )
    assert len(COMBINED_MODELS) == len(BASELINE_MODELS) + len(V2_BASELINE_MODELS)
    # Symbols disjoint across the two presets
    v1_syms = {s for mc in BASELINE_MODELS for s in mc.symbols}
    v2_syms = {s for mc in V2_BASELINE_MODELS for s in mc.symbols}
    assert v1_syms.isdisjoint(v2_syms)


def test_v2_excluded_symbols_constant():
    from crypto_trade.live.models import V2_EXCLUDED_SYMBOLS
    assert set(V2_EXCLUDED_SYMBOLS) == {"BTCUSDT", "ETHUSDT", "LINKUSDT", "BNBUSDT"}


# ----------------------------- Task 6 ---------------------------------------


def test_engine_rejects_v2_with_v1_symbol(tmp_path):
    """A v2 ModelConfig naming any V2_EXCLUDED_SYMBOLS symbol must fail at engine init."""
    from crypto_trade.live.engine import LiveEngine
    from crypto_trade.strategies.ml.risk_v2 import RiskV2Config

    bad = ModelConfig(
        name="bad-v2",
        symbols=("BTCUSDT",),  # v1 baseline symbol — disallowed
        use_atr_labeling=True,
        atr_tp_multiplier=2.9,
        atr_sl_multiplier=1.45,
        atr_column="natr_21_raw",
        features_dir=Path("data/features_v2"),
        risk_wrapper="v2",
        risk_v2_config=RiskV2Config(),
    )
    cfg = LiveConfig(
        models=(bad,),
        dry_run=True,
        db_path=tmp_path / "x.db",
        data_dir=tmp_path,
    )
    with pytest.raises(ValueError, match="V2_EXCLUDED_SYMBOLS"):
        LiveEngine(cfg)


def test_engine_rejects_overlapping_symbols(tmp_path):
    """Two ModelConfigs sharing a symbol corrupt R1/VT state — reject at init."""
    from crypto_trade.live.engine import LiveEngine

    a = ModelConfig(
        name="A1", symbols=("BTCUSDT",),
        use_atr_labeling=True, atr_tp_multiplier=2.9, atr_sl_multiplier=1.45,
    )
    b = ModelConfig(
        name="A2", symbols=("BTCUSDT",),  # collides with A1
        use_atr_labeling=True, atr_tp_multiplier=2.9, atr_sl_multiplier=1.45,
    )
    cfg = LiveConfig(
        models=(a, b),
        dry_run=True,
        db_path=tmp_path / "y.db",
        data_dir=tmp_path,
    )
    with pytest.raises(ValueError, match="overlapping symbols"):
        LiveEngine(cfg)


def test_engine_combined_models_construct_ok(tmp_path):
    """COMBINED_MODELS must satisfy both guards (disjoint v1+v2 symbols)."""
    from crypto_trade.live.engine import LiveEngine
    from crypto_trade.live.models import COMBINED_MODELS

    cfg = LiveConfig(
        models=COMBINED_MODELS,
        dry_run=True,
        db_path=tmp_path / "z.db",
        data_dir=tmp_path,
    )
    LiveEngine(cfg)  # must not raise


# ----------------------------- Task 7 ---------------------------------------


def test_btc_trend_filter_kills_short_in_rally():
    import numpy as np

    from crypto_trade.strategies.ml.risk_v2 import (
        BtcTrendFilterConfig,
        evaluate_btc_trend_filter_one_signal,
    )

    times = np.arange(50, dtype=np.int64) * 28_800_000
    closes = np.concatenate([np.full(36, 50000.0), np.linspace(50000.0, 62500.0, 14)])
    cfg = BtcTrendFilterConfig(enabled=True, lookback_bars=14, threshold_pct=20.0)

    # Short during +25% rally → kill
    assert (
        evaluate_btc_trend_filter_one_signal(times, closes, int(times[-1]), -1, cfg)
        is True
    )
    # Long during +25% rally → no kill
    assert (
        evaluate_btc_trend_filter_one_signal(times, closes, int(times[-1]), 1, cfg)
        is False
    )


def test_btc_trend_filter_kills_long_in_crash():
    import numpy as np

    from crypto_trade.strategies.ml.risk_v2 import (
        BtcTrendFilterConfig,
        evaluate_btc_trend_filter_one_signal,
    )

    times = np.arange(50, dtype=np.int64) * 28_800_000
    closes = np.concatenate([np.full(36, 50000.0), np.linspace(50000.0, 37500.0, 14)])  # -25%
    cfg = BtcTrendFilterConfig(enabled=True, lookback_bars=14, threshold_pct=20.0)

    assert (
        evaluate_btc_trend_filter_one_signal(times, closes, int(times[-1]), 1, cfg)
        is True
    )
    assert (
        evaluate_btc_trend_filter_one_signal(times, closes, int(times[-1]), -1, cfg)
        is False
    )


def test_btc_trend_filter_warmup_passes():
    """Idx < lookback_bars ⇒ warmup, no kill regardless of direction."""
    import numpy as np

    from crypto_trade.strategies.ml.risk_v2 import (
        BtcTrendFilterConfig,
        evaluate_btc_trend_filter_one_signal,
    )

    times = np.arange(10, dtype=np.int64) * 28_800_000  # only 10 bars
    closes = np.linspace(50000.0, 100000.0, 10)
    cfg = BtcTrendFilterConfig(enabled=True, lookback_bars=14, threshold_pct=20.0)

    assert (
        evaluate_btc_trend_filter_one_signal(times, closes, int(times[-1]), -1, cfg)
        is False
    )


def test_btc_trend_filter_disabled_never_kills():
    import numpy as np

    from crypto_trade.strategies.ml.risk_v2 import (
        BtcTrendFilterConfig,
        evaluate_btc_trend_filter_one_signal,
    )

    times = np.arange(50, dtype=np.int64) * 28_800_000
    closes = np.concatenate([np.full(36, 50000.0), np.linspace(50000.0, 62500.0, 14)])
    cfg = BtcTrendFilterConfig(enabled=False)

    assert (
        evaluate_btc_trend_filter_one_signal(times, closes, int(times[-1]), -1, cfg)
        is False
    )


# ----------------------------- Task 8 ---------------------------------------


def test_cli_live_track_flag_defaults_to_v1():
    from crypto_trade.main import build_parser

    parser = build_parser()
    args = parser.parse_args(["live"])
    assert args.track == "v1"


def test_cli_live_track_flag_accepts_v2_and_both():
    from crypto_trade.main import build_parser

    parser = build_parser()
    args_v2 = parser.parse_args(["live", "--track", "v2"])
    assert args_v2.track == "v2"
    args_both = parser.parse_args(["live", "--track", "both"])
    assert args_both.track == "both"


def test_cmd_live_track_dispatches_to_correct_model_set(tmp_path):
    """_cmd_live must hand the right preset to LiveConfig based on args.track."""
    from unittest.mock import patch
    from crypto_trade.main import _cmd_live, build_parser
    from crypto_trade.live.models import (
        BASELINE_MODELS,
        COMBINED_MODELS,
        V2_BASELINE_MODELS,
    )

    class _StubSettings:
        binance_api_key = ""
        binance_api_secret = ""
        base_url = ""
        data_dir = str(tmp_path)

    parser = build_parser()
    for track, expected in (
        ("v1", BASELINE_MODELS),
        ("v2", V2_BASELINE_MODELS),
        ("both", COMBINED_MODELS),
    ):
        args = parser.parse_args(["live", "--track", track])
        with patch("crypto_trade.live.engine.LiveEngine") as engine_cls:
            engine_cls.return_value.run.return_value = None
            _cmd_live(args, _StubSettings())
            cfg = engine_cls.call_args.kwargs["config"]
            assert cfg.models == expected, f"track={track} got {cfg.models}"


# ----------------------------- Task 9 ---------------------------------------


def test_engine_exposes_catch_up_only(tmp_path):
    """LiveEngine.catch_up_only must exist and be safe to call on an empty model set."""
    from crypto_trade.live.engine import LiveEngine

    cfg = LiveConfig(
        models=(),  # no models → no runners → catch_up loop is a no-op
        dry_run=True,
        db_path=tmp_path / "smoke.db",
        data_dir=tmp_path,
    )
    engine = LiveEngine(cfg)
    assert hasattr(engine, "catch_up_only")
    engine.catch_up_only()  # smoke: must not raise


def test_engine_catch_up_only_skips_poll_loop(tmp_path, monkeypatch):
    """catch_up_only must run setup methods but never enter the poll loop."""
    from crypto_trade.live.engine import LiveEngine

    cfg = LiveConfig(
        models=(),
        dry_run=True,
        db_path=tmp_path / "ticks.db",
        data_dir=tmp_path,
    )
    engine = LiveEngine(cfg)

    # If catch_up_only ever calls _tick, the test fails.
    tick_calls = []
    monkeypatch.setattr(engine, "_tick", lambda: tick_calls.append(1))
    engine.catch_up_only()
    assert tick_calls == []


# ----------------------------- Task 1: catch_up_lookback_days field ---------


def test_live_config_catch_up_lookback_default_90():
    """Default lookback covers VT's 45-day window plus buffer."""
    cfg = LiveConfig()
    assert cfg.catch_up_lookback_days == 90

    cfg2 = LiveConfig(catch_up_lookback_days=400)
    assert cfg2.catch_up_lookback_days == 400

    cfg3 = LiveConfig(catch_up_lookback_days=None)
    assert cfg3.catch_up_lookback_days is None  # explicit opt-out


# ----------------------------- Task 2: catch-up start helper ---------------


def test_compute_catch_up_start_ms_lookback_modes():
    """The helper handles None (legacy) and N-days (new) lookback modes."""
    import pandas as pd
    from crypto_trade.live.engine import _compute_catch_up_start_ms

    now = int(pd.Timestamp("2026-04-26 12:00", tz="UTC").value // 1_000_000)

    # None preserves legacy previous-month behavior
    legacy = _compute_catch_up_start_ms(now, lookback_days=None)
    assert legacy == int(pd.Timestamp("2026-03-01", tz="UTC").value // 1_000_000)

    # N-day lookback returns now - N days exactly
    ninety = _compute_catch_up_start_ms(now, lookback_days=90)
    expected = int((pd.Timestamp("2026-04-26 12:00", tz="UTC") - pd.Timedelta(days=90)).value // 1_000_000)
    assert ninety == expected

    # Larger lookback works too (full OOS replay)
    full_oos = _compute_catch_up_start_ms(now, lookback_days=400)
    expected_400 = int((pd.Timestamp("2026-04-26 12:00", tz="UTC") - pd.Timedelta(days=400)).value // 1_000_000)
    assert full_oos == expected_400


# ----------------------------- Task 3: CLI catch-up flags ------------------


def test_cli_live_catch_up_days_flag():
    from crypto_trade.main import build_parser

    parser = build_parser()
    args = parser.parse_args(["live", "--catch-up-days", "120"])
    assert args.catch_up_days == 120
    assert args.catch_up_from is None


def test_cli_live_catch_up_from_flag():
    from crypto_trade.main import build_parser

    parser = build_parser()
    args = parser.parse_args(["live", "--catch-up-from", "2025-03-24"])
    assert args.catch_up_from == "2025-03-24"
    assert args.catch_up_days is None


def test_cli_live_catch_up_flags_mutually_exclusive():
    from crypto_trade.main import build_parser

    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(
            ["live", "--catch-up-days", "60", "--catch-up-from", "2025-03-24"]
        )


def test_cmd_live_propagates_catch_up_days_to_config(tmp_path):
    """`--catch-up-days N` flows into LiveConfig.catch_up_lookback_days."""
    from unittest.mock import patch
    from crypto_trade.main import _cmd_live, build_parser

    class _StubSettings:
        binance_api_key = ""
        binance_api_secret = ""
        base_url = ""
        data_dir = str(tmp_path)

    parser = build_parser()
    args = parser.parse_args(["live", "--catch-up-days", "120"])
    with patch("crypto_trade.live.engine.LiveEngine") as engine_cls:
        engine_cls.return_value.run.return_value = None
        _cmd_live(args, _StubSettings())
        cfg = engine_cls.call_args.kwargs["config"]
        assert cfg.catch_up_lookback_days == 120


def test_cmd_live_propagates_catch_up_from_to_config(tmp_path):
    """`--catch-up-from YYYY-MM-DD` is converted to lookback_days based on now."""
    import pandas as pd
    from unittest.mock import patch
    from crypto_trade.main import _cmd_live, build_parser

    class _StubSettings:
        binance_api_key = ""
        binance_api_secret = ""
        base_url = ""
        data_dir = str(tmp_path)

    parser = build_parser()
    args = parser.parse_args(["live", "--catch-up-from", "2025-03-24"])
    with patch("crypto_trade.live.engine.LiveEngine") as engine_cls:
        engine_cls.return_value.run.return_value = None
        _cmd_live(args, _StubSettings())
        cfg = engine_cls.call_args.kwargs["config"]
        days = (pd.Timestamp.now("UTC") - pd.Timestamp("2025-03-24", tz="UTC")).days
        assert abs(cfg.catch_up_lookback_days - days) <= 1


def test_cmd_live_omits_flags_uses_default(tmp_path):
    """No catch-up flag ⇒ LiveConfig keeps its 90-day default."""
    from unittest.mock import patch
    from crypto_trade.main import _cmd_live, build_parser

    class _StubSettings:
        binance_api_key = ""
        binance_api_secret = ""
        base_url = ""
        data_dir = str(tmp_path)

    parser = build_parser()
    args = parser.parse_args(["live"])
    with patch("crypto_trade.live.engine.LiveEngine") as engine_cls:
        engine_cls.return_value.run.return_value = None
        _cmd_live(args, _StubSettings())
        cfg = engine_cls.call_args.kwargs["config"]
        assert cfg.catch_up_lookback_days == 90  # LiveConfig default


# ----------------------------- Task 5: catch-up pre-load filter ------------


def test_catch_up_pre_load_filter_excludes_real_numeric_ids(tmp_path):
    """Real numeric-ID open trades from a prior --live session must NOT be
    pre-loaded into catch-up's open_trades dict (that's reconciler/poll-loop's
    domain). Pre-loading would let catch-up's check_order simulate exits
    and falsely close DB rows whose Binance positions are still open."""
    from crypto_trade.live.models import LiveTrade, ModelConfig, is_paper_trade
    from crypto_trade.live.state_store import StateStore


    db = tmp_path / "test.db"
    state = StateStore(db)

    state.upsert_trade(LiveTrade(
        id="paper-1", model_name="A", symbol="BTCUSDT", direction=1,
        entry_price=60000.0, amount_usd=1000.0, weight_factor=1.0,
        stop_loss_price=57600.0, take_profit_price=64800.0,
        open_time=1, timeout_time=10**13, signal_time=0,
        entry_order_id="CATCHUP-deadbeef",
        sl_order_id="CATCHUP-feedface", tp_order_id="CATCHUP-12345678",
    ))
    state.upsert_trade(LiveTrade(
        id="real-1", model_name="A", symbol="ETHUSDT", direction=1,
        entry_price=3000.0, amount_usd=1000.0, weight_factor=1.0,
        stop_loss_price=2880.0, take_profit_price=3240.0,
        open_time=1, timeout_time=10**13, signal_time=0,
        entry_order_id="9876543210", sl_order_id="111", tp_order_id="222",
    ))
    state.close()

    # Reproduce the engine's pre-load logic exactly:
    state2 = StateStore(db)
    mc = ModelConfig(
        name="A", symbols=("BTCUSDT", "ETHUSDT"),
        use_atr_labeling=True, atr_tp_multiplier=2.9, atr_sl_multiplier=1.45,
    )
    pre_loaded = {
        seeded.symbol: seeded
        for seeded in state2.get_open_trades(model_name=mc.name)
        if seeded.symbol in mc.symbols and is_paper_trade(seeded)
    }
    state2.close()

    assert "BTCUSDT" in pre_loaded
    assert "ETHUSDT" not in pre_loaded, (
        "Real numeric-ID trades must not be pre-loaded — they belong to reconciler/poll-loop"
    )

    # Belt-and-suspenders integration anchor — the engine source must use the helper.
    import re
    from pathlib import Path
    src = Path("src/crypto_trade/live/engine.py").read_text()
    pre_load_block = re.search(
        r"open_trades:\s*dict\[str,\s*LiveTrade\]\s*=\s*\{\}.*?cooldown_until",
        src, flags=re.DOTALL,
    )
    assert pre_load_block is not None
    assert "is_paper_trade" in pre_load_block.group(0), (
        "engine._catch_up_model must filter pre-loaded open trades via is_paper_trade()"
    )


# ----------------------------- Testnet support ------------------------------


def test_live_config_testnet_default_false():
    """testnet defaults to False — existing dry-run / live behavior unchanged."""
    cfg = LiveConfig()
    assert cfg.testnet is False


def test_live_config_testnet_explicit_true_with_live():
    cfg = LiveConfig(testnet=True, dry_run=False)
    assert cfg.testnet is True
    assert cfg.dry_run is False


def test_engine_auth_base_url_routes_signed_traffic(tmp_path):
    """auth_base_url targets the AuthenticatedBinanceClient. The kline
    BinanceClient instances keep targeting base_url — testnet kline data
    is gappy and would break catch-up replay."""
    from crypto_trade.live.engine import LiveEngine

    cfg = LiveConfig(
        models=(),
        dry_run=False,
        testnet=True,
        db_path=tmp_path / "tn.db",
        data_dir=tmp_path,
    )
    engine = LiveEngine(
        config=cfg,
        api_key="k",
        api_secret="s",
        base_url="https://fapi.binance.com",
        auth_base_url="https://testnet.binancefuture.com",
    )
    # Auth client → testnet
    assert engine._auth_client is not None
    assert engine._auth_client._base_url == "https://testnet.binancefuture.com"
    assert str(engine._auth_client._client.base_url).rstrip("/") == "https://testnet.binancefuture.com"
    # Kline clients → production (must stay on full-history feed)
    assert engine._read_client.base_url == "https://fapi.binance.com"
    assert engine._fetch_client.base_url == "https://fapi.binance.com"


def test_engine_auth_base_url_falls_back_to_base_url(tmp_path):
    """auth_base_url=None ⇒ AuthenticatedBinanceClient uses base_url
    (preserves the pre-testnet single-URL behavior)."""
    from crypto_trade.live.engine import LiveEngine

    cfg = LiveConfig(
        models=(),
        dry_run=False,
        db_path=tmp_path / "x.db",
        data_dir=tmp_path,
    )
    engine = LiveEngine(
        config=cfg,
        api_key="k",
        api_secret="s",
        base_url="https://fapi.binance.com",
        auth_base_url=None,
    )
    assert engine._auth_client is not None
    assert engine._auth_client._base_url == "https://fapi.binance.com"
