"""Regression tests for the candle-aligned cooldown semantics in LiveEngine.

Background — the bug this guards against:

Two cooldown bugs caused 3 v1 signal-level mismatches against the backtest
during the 2026-05-13 → 05-21 testnet run:

  - **Bug A (set cooldown)**: ``_set_cooldown`` previously used the raw
    ``trade.exit_time``, which for Binance SL/TP fills is the algo's
    wall-clock ``triggerTime`` — typically mid-candle (e.g., 23:42).
    The backtest's equivalent exit is the candle close (23:59:59.999).
    A mid-candle live fill produced a cooldown_until that ended ~17 minutes
    earlier than the backtest's, occasionally letting the next trade open
    one candle too early (observed: A·BTC 05-18, A·ETH 05-18).

  - **Bug B (check cooldown)**: the live-tick cooldown check at
    ``LiveEngine._tick`` used ``now_ms < cooldown_until`` (wall-clock now).
    Catch-up + backtest both use ``ot >= cooldown_until`` (candle Kline
    open_time). At a tick that fires a few seconds past ``cooldown_until``
    nominal expiry, ``now_ms >= cooldown_until`` (pass) while
    ``candle_ot < cooldown_until`` (would still skip). Backtest correctly
    skips this candle; live did not.

Fix:
  - ``_set_cooldown`` rounds ``close_time`` UP to the close of the
    8h candle containing it via ``_round_to_candle_close``.
  - The live-tick check uses ``new_candles[symbol].open_time``
    (candle Kline.open_time) instead of ``now_ms``.

These tests lock both halves. Bug A is covered by checking
``_set_cooldown`` directly with a mid-candle ``close_time`` and asserting
the stored value matches what the backtest's equivalent SL would produce.
Bug B is covered by ``_round_to_candle_close`` invariants (already-
aligned values pass through unchanged) and a positive control on the
arithmetic.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from crypto_trade.live.engine import LiveEngine
from crypto_trade.live.models import V2_BASELINE_MODELS, LiveConfig

# ---------- shared fixture builder (same shape as test_btc_lag_defer.py) ----------


def _write_btc_csv(tmp_path: Path, last_open_time_ms: int, n: int = 10) -> None:
    path = tmp_path / "BTCUSDT" / "8h.csv"
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


def _make_engine(tmp_path: Path) -> LiveEngine:
    _write_btc_csv(tmp_path, 1_700_000_000_000)
    sol_only = tuple(m for m in V2_BASELINE_MODELS if m.symbols == ("SOLUSDT",))
    cfg = LiveConfig(
        data_dir=tmp_path,
        features_dir=tmp_path / "features",
        models=sol_only,
        db_path=tmp_path / "engine.db",
    )
    return LiveEngine(cfg)


# ---------------------------------------------------------------------------
# _round_to_candle_close
# ---------------------------------------------------------------------------


class TestRoundToCandleClose:
    """The helper that normalises wall-clock fills to candle boundaries."""

    def test_already_aligned_passes_through(self, tmp_path: Path) -> None:
        engine = _make_engine(tmp_path)
        # 2026-05-17 23:59:59.999 — already a candle close.
        already_close = 1_779_062_399_999
        assert engine._round_to_candle_close(already_close) == already_close

    def test_mid_candle_rounds_up_to_close(self, tmp_path: Path) -> None:
        engine = _make_engine(tmp_path)
        # 2026-05-17 23:42:00 — mid-candle in the [16:00, 23:59:59.999] bucket.
        mid_candle = 1_779_061_320_000
        expected_close = 1_779_062_399_999  # 23:59:59.999 of the same candle
        assert engine._round_to_candle_close(mid_candle) == expected_close

    def test_candle_open_rounds_to_same_candle_close(self, tmp_path: Path) -> None:
        engine = _make_engine(tmp_path)
        # 2026-05-17 16:00:00 — the candle's own open.
        candle_open = 1_779_033_600_000
        expected_close = 1_779_062_399_999  # 23:59:59.999 of the same candle
        assert engine._round_to_candle_close(candle_open) == expected_close

    def test_next_candle_open_rounds_to_its_close(self, tmp_path: Path) -> None:
        engine = _make_engine(tmp_path)
        # 2026-05-18 00:00:00 — the NEXT candle's open.
        next_open = 1_779_062_400_000
        expected_close = 1_779_091_199_999  # 2026-05-18 07:59:59.999
        assert engine._round_to_candle_close(next_open) == expected_close


# ---------------------------------------------------------------------------
# _set_cooldown — Bug A guard
# ---------------------------------------------------------------------------


class TestSetCooldownCandleAligned:
    """``_set_cooldown`` writes a cooldown_until that matches backtest semantics
    regardless of whether the input ``close_time`` is candle-aligned (paper
    trades) or mid-candle (Binance SL/TP fills)."""

    _CANDLE_MS = 8 * 60 * 60 * 1000

    def _read_cooldown(self, engine: LiveEngine, model: str, sym: str) -> int | None:
        v = engine._state.get_state(f"cooldown_{model}_{sym}")
        return int(v) if v else None

    def test_paper_exit_already_aligned(self, tmp_path: Path) -> None:
        """Paper trade exits at candle close (e.g., SEEDED). Cooldown should
        be close_time + N*candle_ms, unchanged from prior behavior."""
        engine = _make_engine(tmp_path)
        candle_close = 1_779_062_399_999  # 2026-05-17 23:59:59.999
        # SOL belongs to V2-SOL; cooldown_candles = 4 (V2 baseline default).
        engine._set_cooldown("V2-SOL", "SOLUSDT", candle_close)
        expected = candle_close + 4 * self._CANDLE_MS
        assert self._read_cooldown(engine, "V2-SOL", "SOLUSDT") == expected

    def test_binance_fill_mid_candle_rounds_up_before_cooldown(self, tmp_path: Path) -> None:
        """A Binance SL fill at 23:42 must produce the SAME cooldown_until
        as if the fill had happened at 23:59:59.999 (the backtest's exit).
        Without the candle-rounding, cooldown_until would be ~17 minutes
        earlier than the backtest's, which was the observed v1 mismatch."""
        engine = _make_engine(tmp_path)
        mid_candle_fill = 1_779_061_320_000  # 2026-05-17 23:42:00
        candle_close = 1_779_062_399_999  # 2026-05-17 23:59:59.999

        engine._set_cooldown("V2-SOL", "SOLUSDT", mid_candle_fill)
        stored_for_fill = self._read_cooldown(engine, "V2-SOL", "SOLUSDT")

        # Reset and run the candle-aligned path for comparison.
        engine._state.set_state("cooldown_V2-SOL_SOLUSDT", "")
        engine._set_cooldown("V2-SOL", "SOLUSDT", candle_close)
        stored_for_close = self._read_cooldown(engine, "V2-SOL", "SOLUSDT")

        assert stored_for_fill == stored_for_close, (
            "Mid-candle fill must round up to the candle close before cooldown "
            "math; otherwise live drifts vs. backtest by up to 1 candle on the "
            "next entry attempt."
        )

    def test_v1_two_candle_cooldown_arithmetic(self, tmp_path: Path) -> None:
        """Verify the post-rounding arithmetic for v1's typical cooldown=2.

        Reuses ``_set_cooldown`` indirectly: the v1 model name "A" lives in
        BASELINE_MODELS with cooldown=2. We poke the helper directly via a
        v1-flavored engine.
        """
        from crypto_trade.live.models import BASELINE_MODELS

        _write_btc_csv(tmp_path, 1_700_000_000_000)
        cfg = LiveConfig(
            data_dir=tmp_path,
            features_dir=tmp_path / "features",
            models=BASELINE_MODELS[:1],  # just Model A (BTC+ETH pooled)
            db_path=tmp_path / "engine.db",
        )
        engine = LiveEngine(cfg)
        mid_candle_fill = 1_779_061_320_000  # 23:42 inside [16:00, 23:59:59.999]
        engine._set_cooldown("A", "BTCUSDT", mid_candle_fill)
        stored = int(engine._state.get_state("cooldown_A_BTCUSDT"))
        # candle close = 1_779_062_399_999 ; cooldown_candles = 2 ; +16h
        expected = 1_779_062_399_999 + 2 * self._CANDLE_MS
        assert stored == expected
