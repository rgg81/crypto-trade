"""Regression test for the BTC-lag deferral in LiveEngine._defer_v2_if_btc_lagging.

Background — the bug this guards against:

The live engine fetches new klines per-symbol via Binance's REST API. Binance
publishes each symbol's new candle independently, with a few seconds of
jitter between symbols. On 8 of 33 ticks during the 2026-05-13 → 05-21
testnet run, v2 symbols (DOGE/SOL/XRP/NEAR) had a new closed candle in the
API response but BTC's new candle hadn't been published yet.

When v2 feature gen ran with stale BTC klines, ``cross_btc`` left-merged
BTC features into the v2 frame by ``open_time`` — got no match for the new
candle's ot — and produced NaN for btc_ret_3d / btc_ret_7d / btc_ret_14d /
btc_vol_14d / sym_vs_btc_ret_7d. LightGBM accepts NaN and routes those
inputs down its default tree branches, generating a DIFFERENT prediction
than the backtest sees with valid BTC features. This broke signal-level
determinism: the engine opened/skipped 23 trades that the backtest
disagreed with.

The fix ``_defer_v2_if_btc_lagging`` runs on every tick:
  1. Identifies v2 symbols with new candles in this tick.
  2. Reads BTC's kline CSV max open_time.
  3. If BTC is already current → return (no-op).
  4. Otherwise fetch BTC once. If now current → return.
  5. Otherwise drop the late v2 symbols from ``new_candles`` so they
     re-fire next poll (by which time BTC will normally have caught up).
     ``last_processed_<symbol>`` is set at end-of-tick, so a deferred
     symbol naturally re-fires.

These tests lock that contract in three flavors:
  - BTC already current  → no fetch, no deferral
  - BTC stale, fetch fixes → one fetch, no deferral
  - BTC stale, fetch doesn't fix → one fetch, v2 symbols deferred
And a v1-only tick is a no-op (the check doesn't fire).
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd

from crypto_trade.live.engine import LiveEngine
from crypto_trade.live.models import LiveConfig, ModelConfig
from crypto_trade.models import Kline


def _write_8h_csv(path: Path, last_open_time_ms: int, n: int = 10) -> None:
    """Write a minimal 8h kline CSV ending at ``last_open_time_ms``."""
    path.parent.mkdir(parents=True, exist_ok=True)
    interval_ms = 8 * 60 * 60 * 1000
    rows = []
    for i in range(n):
        ot = last_open_time_ms - (n - 1 - i) * interval_ms
        ct = ot + interval_ms - 1
        rows.append(
            {
                "open_time": ot,
                "open": 100.0,
                "high": 101.0,
                "low": 99.0,
                "close": 100.5,
                "volume": 1000.0,
                "close_time": ct,
                "quote_asset_volume": 100500.0,
                "number_of_trades": 50,
                "taker_buy_base_asset_volume": 500.0,
                "taker_buy_quote_asset_volume": 50250.0,
                "ignore": 0,
            }
        )
    pd.DataFrame(rows).to_csv(path, index=False)


def _make_engine(tmp_path: Path, *, extra_models: tuple[ModelConfig, ...] = ()) -> LiveEngine:
    """Build a LiveEngine with one or more v2 runners.

    Uses the project's `V2_BASELINE_MODELS` (already wired with a
    `risk_v2_config`) and lets the caller bolt on additional models.
    """
    from crypto_trade.live.models import V2_BASELINE_MODELS

    # ``LiveEngine.__init__`` reads the BTC CSV for the BTC trend filter sanity
    # check, so seed it with a stable file before construction.
    _write_8h_csv(tmp_path / "BTCUSDT" / "8h.csv", 1_700_000_000_000)
    # Pick just V2-SOL (single-symbol) by default — keeps the test surface small.
    sol_only = tuple(m for m in V2_BASELINE_MODELS if m.symbols == ("SOLUSDT",))
    models = sol_only + extra_models
    cfg = LiveConfig(
        data_dir=tmp_path,
        features_dir=tmp_path / "features",
        models=models,
        db_path=tmp_path / "engine.db",
    )
    return LiveEngine(cfg)


def _kline(ot: int) -> Kline:
    """Lightweight Kline stub: only open_time is read by the helper."""
    k = MagicMock(spec=Kline)
    k.open_time = ot
    return k


def test_no_v2_in_tick_is_noop(tmp_path: Path) -> None:
    engine = _make_engine(tmp_path)
    new_candles: dict[str, Kline] = {}
    with patch("crypto_trade.live.engine.refresh_klines") as refresh:
        engine._defer_v2_if_btc_lagging(new_candles)
    assert refresh.call_count == 0
    assert new_candles == {}


def test_btc_already_current_no_fetch_no_defer(tmp_path: Path) -> None:
    engine = _make_engine(tmp_path)
    v2_ot = 1_700_000_000_000
    # BTC CSV ends at the same ot the v2 candle needs.
    _write_8h_csv(tmp_path / "BTCUSDT" / "8h.csv", v2_ot)
    new_candles = {"SOLUSDT": _kline(v2_ot)}
    with patch("crypto_trade.live.engine.refresh_klines") as refresh:
        engine._defer_v2_if_btc_lagging(new_candles)
    assert refresh.call_count == 0  # BTC current, no fetch attempted
    assert "SOLUSDT" in new_candles  # not deferred


def test_btc_lagging_fetch_succeeds_no_defer(tmp_path: Path) -> None:
    engine = _make_engine(tmp_path)
    interval_ms = 8 * 60 * 60 * 1000
    v2_ot = 1_700_000_000_000
    # BTC CSV one candle behind the v2 ot.
    _write_8h_csv(tmp_path / "BTCUSDT" / "8h.csv", v2_ot - interval_ms)
    new_candles = {"SOLUSDT": _kline(v2_ot)}

    # Mock the fetch to append the missing BTC candle.
    def fake_refresh(client, syms, interval, data_dir):
        assert syms == ["BTCUSDT"]
        _write_8h_csv(tmp_path / "BTCUSDT" / "8h.csv", v2_ot)

    with patch("crypto_trade.live.engine.refresh_klines", side_effect=fake_refresh) as refresh:
        engine._defer_v2_if_btc_lagging(new_candles)
    assert refresh.call_count == 1  # one BTC fetch attempted
    assert "SOLUSDT" in new_candles  # not deferred (fetch made BTC current)


def test_btc_lagging_fetch_doesnt_help_v2_deferred(tmp_path: Path) -> None:
    engine = _make_engine(tmp_path)
    interval_ms = 8 * 60 * 60 * 1000
    v2_ot = 1_700_000_000_000
    # BTC CSV one candle behind the v2 ot, and refresh_klines is a no-op
    # (Binance hasn't published BTC's new candle yet).
    _write_8h_csv(tmp_path / "BTCUSDT" / "8h.csv", v2_ot - interval_ms)
    new_candles = {"SOLUSDT": _kline(v2_ot)}

    with patch("crypto_trade.live.engine.refresh_klines") as refresh:
        engine._defer_v2_if_btc_lagging(new_candles)
    assert refresh.call_count == 1  # tried fetching
    assert "SOLUSDT" not in new_candles  # deferred to next tick


def test_only_late_v2_symbols_are_deferred(tmp_path: Path) -> None:
    """A v2 symbol whose ot is <= BTC's extent stays in; only late ones are dropped."""
    from crypto_trade.live.models import V2_BASELINE_MODELS

    interval_ms = 8 * 60 * 60 * 1000
    btc_ot = 1_700_000_000_000
    # SOLUSDT at the same ot as BTC (covered); XRPUSDT one candle past BTC (not).
    xrp_model = tuple(m for m in V2_BASELINE_MODELS if m.symbols == ("XRPUSDT",))
    engine = _make_engine(tmp_path, extra_models=xrp_model)
    _write_8h_csv(tmp_path / "BTCUSDT" / "8h.csv", btc_ot)
    new_candles = {
        "SOLUSDT": _kline(btc_ot),
        "XRPUSDT": _kline(btc_ot + interval_ms),  # one candle past BTC
    }
    with patch("crypto_trade.live.engine.refresh_klines") as refresh:
        engine._defer_v2_if_btc_lagging(new_candles)
    assert refresh.call_count == 1
    assert "SOLUSDT" in new_candles  # covered → kept
    assert "XRPUSDT" not in new_candles  # late → deferred
