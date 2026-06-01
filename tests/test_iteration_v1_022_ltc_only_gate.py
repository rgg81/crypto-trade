"""Smoke tests for iter-v1/022: LTC-only + asymmetric long-suppress BTC-trend gate.

Tests verify:
1.  V1_ITER022_UNIVERSE is exactly {"LTCUSDT"} — F-AXIS-MECHANISM #1 precondition.
2.  Gate constants match brief Section 3.3 pinned values.
3.  LTCUSDT is not in V1_EXCLUDED_SYMBOLS — dispatch guard won't false-positive.
4.  assert_v1_universe() accepts {LTCUSDT} — universe check passes.
5.  /022 dispatch condition fires correctly (set equality).
6.  /022 dispatch does NOT fire for baseline / /017 / /018 / /019 / /020 universes.
7.  BtcTrendFilterConfig long_only_mode kwarg accepted and defaults to False.
8.  Asymmetric kill_mask logic: kills longs at BTC bear; preserves shorts.
9.  Symmetric behavior unchanged (long_only_mode=False preserves /019 behavior).
10. V1_ITER022_BTC_GATE_LONG_ONLY is True — asymmetric mode enabled for /022.
11. BtcTrendFilterConfig instantiates with long_only_mode=True cleanly.
12. evaluate_btc_trend_filter_one_signal respects long_only_mode=True.
13. evaluate_btc_trend_filter_one_signal symmetric mode unchanged.
14. apply_btc_trend_filter warmup pass-through still correct.
15. /019 gate constants unchanged — no regression from /022 code additions.
"""

from __future__ import annotations

import numpy as np
import pytest

from crypto_trade.features_v1 import V1_EXCLUDED_SYMBOLS, assert_v1_universe

# ---------------------------------------------------------------------------
# Helper fixtures
# ---------------------------------------------------------------------------


def _make_bear_btc(n: int = 50, threshold_bar: int = 42) -> tuple[np.ndarray, np.ndarray]:
    """Return (open_times, closes) with a -5% BTC drop starting at threshold_bar."""
    open_times = np.arange(n, dtype=np.int64) * 28800000  # 8h in ms
    closes = np.where(np.arange(n) < threshold_bar, 100.0, 95.0)
    return open_times, closes


def _make_bull_btc(n: int = 50, threshold_bar: int = 42) -> tuple[np.ndarray, np.ndarray]:
    """Return (open_times, closes) with a +5% BTC rally starting at threshold_bar."""
    open_times = np.arange(n, dtype=np.int64) * 28800000
    closes = np.where(np.arange(n) < threshold_bar, 100.0, 105.0)
    return open_times, closes


def _make_flat_btc(n: int = 50) -> tuple[np.ndarray, np.ndarray]:
    """Return (open_times, closes) flat at 100."""
    open_times = np.arange(n, dtype=np.int64) * 28800000
    closes = np.full(n, 100.0)
    return open_times, closes


# ---------------------------------------------------------------------------
# Test classes
# ---------------------------------------------------------------------------


class TestIter022Universe:
    """V1_ITER022_UNIVERSE must be exactly ("LTCUSDT",)."""

    def test_iter022_universe_is_ltcusdt_only(self) -> None:
        from run_baseline_v1 import V1_ITER022_UNIVERSE

        assert set(V1_ITER022_UNIVERSE) == {"LTCUSDT"}

    def test_iter022_universe_tuple_length(self) -> None:
        from run_baseline_v1 import V1_ITER022_UNIVERSE

        assert len(V1_ITER022_UNIVERSE) == 1

    def test_ltcusdt_not_excluded(self) -> None:
        """LTCUSDT must not be in V1_EXCLUDED_SYMBOLS."""
        assert "LTCUSDT" not in V1_EXCLUDED_SYMBOLS

    def test_assert_v1_universe_accepts_iter022(self) -> None:
        """assert_v1_universe() must accept {LTCUSDT} without raising."""
        from run_baseline_v1 import V1_ITER022_UNIVERSE

        assert_v1_universe(V1_ITER022_UNIVERSE)


class TestIter022GateConstants:
    """Gate constants must match brief Section 3.3 pinned values (frozen for /022)."""

    def test_lookback_bars_frozen_at_42(self) -> None:
        from run_baseline_v1 import V1_ITER022_BTC_GATE_LOOKBACK_BARS

        # 42 bars = 14 days at 8h cadence; matches /019 lookback per brief §3.3
        assert V1_ITER022_BTC_GATE_LOOKBACK_BARS == 42

    def test_threshold_pct_frozen_at_4(self) -> None:
        from run_baseline_v1 import V1_ITER022_BTC_GATE_THRESHOLD_PCT

        # -4% BTC 14d return (TIGHTER than /019's 8%); frozen per brief §3.3
        assert V1_ITER022_BTC_GATE_THRESHOLD_PCT == pytest.approx(4.0)

    def test_gate_enabled_true(self) -> None:
        from run_baseline_v1 import V1_ITER022_BTC_GATE_ENABLED

        assert V1_ITER022_BTC_GATE_ENABLED is True

    def test_gate_long_only_true(self) -> None:
        """CRITICAL: /022 MUST use asymmetric long-only mode — brief Section 3.3."""
        from run_baseline_v1 import V1_ITER022_BTC_GATE_LONG_ONLY

        assert V1_ITER022_BTC_GATE_LONG_ONLY is True


class TestIter022DispatchCondition:
    """Dispatch elif fires correctly for LTCUSDT only; all other universes excluded."""

    def test_dispatch_fires_for_ltcusdt(self) -> None:
        from run_baseline_v1 import V1_ITER022_UNIVERSE

        symbols = ("LTCUSDT",)
        assert set(symbols) == set(V1_ITER022_UNIVERSE)

    def test_dispatch_does_not_fire_for_baseline(self) -> None:
        from run_baseline_v1 import V1_BASELINE_UNIVERSE, V1_ITER022_UNIVERSE

        assert set(V1_BASELINE_UNIVERSE) != set(V1_ITER022_UNIVERSE)

    def test_dispatch_does_not_fire_for_iter017(self) -> None:
        from run_baseline_v1 import V1_ITER017_UNIVERSE, V1_ITER022_UNIVERSE

        assert set(V1_ITER017_UNIVERSE) != set(V1_ITER022_UNIVERSE)

    def test_dispatch_does_not_fire_for_iter018(self) -> None:
        from run_baseline_v1 import V1_ITER018_UNIVERSE, V1_ITER022_UNIVERSE

        # LINK-only vs LTC-only — must not collide
        assert set(V1_ITER018_UNIVERSE) != set(V1_ITER022_UNIVERSE)

    def test_dispatch_does_not_fire_for_iter019(self) -> None:
        from run_baseline_v1 import V1_ITER019_UNIVERSE, V1_ITER022_UNIVERSE

        # ETH-only vs LTC-only — must not collide
        assert set(V1_ITER019_UNIVERSE) != set(V1_ITER022_UNIVERSE)

    def test_dispatch_does_not_fire_for_iter020(self) -> None:
        from run_baseline_v1 import V1_ITER020_UNIVERSE, V1_ITER022_UNIVERSE

        # BTC-only vs LTC-only — must not collide
        assert set(V1_ITER020_UNIVERSE) != set(V1_ITER022_UNIVERSE)

    def test_iter022_universe_is_subset_of_baseline(self) -> None:
        """LTCUSDT is in V1_BASELINE_UNIVERSE — parquet will exist for training."""
        from run_baseline_v1 import V1_BASELINE_UNIVERSE, V1_ITER022_UNIVERSE

        assert set(V1_ITER022_UNIVERSE).issubset(set(V1_BASELINE_UNIVERSE))


class TestLongOnlyModeKwarg:
    """BtcTrendFilterConfig long_only_mode kwarg: default=False, /022=True."""

    def test_long_only_mode_default_false(self) -> None:
        """Default long_only_mode=False preserves symmetric /019 behavior."""
        from crypto_trade.strategies.ml.risk_v2 import BtcTrendFilterConfig

        cfg = BtcTrendFilterConfig(lookback_bars=42, threshold_pct=8.0, enabled=True)
        assert cfg.long_only_mode is False

    def test_long_only_mode_can_be_set_true(self) -> None:
        """long_only_mode=True can be set for /022 asymmetric variant."""
        from crypto_trade.strategies.ml.risk_v2 import BtcTrendFilterConfig

        cfg = BtcTrendFilterConfig(
            lookback_bars=42,
            threshold_pct=4.0,
            enabled=True,
            long_only_mode=True,
        )
        assert cfg.long_only_mode is True
        assert cfg.threshold_pct == pytest.approx(4.0)
        assert cfg.lookback_bars == 42

    def test_config_is_frozen_dataclass(self) -> None:
        """BtcTrendFilterConfig is frozen — attributes cannot be mutated."""
        from crypto_trade.strategies.ml.risk_v2 import BtcTrendFilterConfig

        cfg = BtcTrendFilterConfig(
            lookback_bars=42,
            threshold_pct=4.0,
            enabled=True,
            long_only_mode=True,
        )
        with pytest.raises((AttributeError, TypeError)):
            cfg.long_only_mode = False  # type: ignore[misc]


class TestAsymmetricKillMaskLogic:
    """Core logic: long_only_mode=True kills longs in BTC bear; shorts pass through."""

    def test_long_killed_in_btc_bear_with_long_only(self) -> None:
        """LTC long at bar 49 (BTC -5% over 42 bars at 4% threshold) → killed."""
        from crypto_trade.strategies.ml.risk_v2 import (
            BtcTrendFilterConfig,
            evaluate_btc_trend_filter_one_signal,
        )

        btc_open_times, btc_closes = _make_bear_btc()
        cfg = BtcTrendFilterConfig(
            lookback_bars=42, threshold_pct=4.0, enabled=True, long_only_mode=True
        )
        # bar 49: BTC close = 95, close_then = closes[49-42=7] = 100 → ret = -5%
        signal_open_time_ms = int(btc_open_times[49])
        should_kill = evaluate_btc_trend_filter_one_signal(
            btc_open_times, btc_closes, signal_open_time_ms, direction=1, config=cfg
        )
        assert should_kill is True, "Long must be killed when BTC ret < -4% in long_only_mode"

    def test_short_preserved_in_btc_bear_with_long_only(self) -> None:
        """LTC short at bar 49 (BTC -5%) → NOT killed in long_only_mode."""
        from crypto_trade.strategies.ml.risk_v2 import (
            BtcTrendFilterConfig,
            evaluate_btc_trend_filter_one_signal,
        )

        btc_open_times, btc_closes = _make_bear_btc()
        cfg = BtcTrendFilterConfig(
            lookback_bars=42, threshold_pct=4.0, enabled=True, long_only_mode=True
        )
        signal_open_time_ms = int(btc_open_times[49])
        should_kill = evaluate_btc_trend_filter_one_signal(
            btc_open_times, btc_closes, signal_open_time_ms, direction=-1, config=cfg
        )
        assert should_kill is False, "Short must NOT be killed in long_only_mode (even in bear)"

    def test_short_killed_in_btc_bull_with_symmetric(self) -> None:
        """Symmetric mode (long_only_mode=False) kills shorts in BTC bull — /019 behavior."""
        from crypto_trade.strategies.ml.risk_v2 import (
            BtcTrendFilterConfig,
            evaluate_btc_trend_filter_one_signal,
        )

        open_times, closes = _make_bull_btc()

        # Disabled → no kill regardless
        cfg_off = BtcTrendFilterConfig(
            lookback_bars=42, threshold_pct=4.0, enabled=False, long_only_mode=False
        )
        signal_open_time_ms = int(open_times[49])
        assert (
            evaluate_btc_trend_filter_one_signal(
                open_times, closes, signal_open_time_ms, direction=-1, config=cfg_off
            )
            is False
        )

        # Enabled symmetric → kills short in BTC bull (+5% > +4%)
        cfg_on = BtcTrendFilterConfig(
            lookback_bars=42, threshold_pct=4.0, enabled=True, long_only_mode=False
        )
        assert (
            evaluate_btc_trend_filter_one_signal(
                open_times, closes, signal_open_time_ms, direction=-1, config=cfg_on
            )
            is True
        ), "Symmetric mode must kill shorts in BTC bull"

    def test_long_not_killed_when_btc_below_threshold(self) -> None:
        """Long at bar 43 (BTC flat → |ret| < 4%) → NOT killed."""
        from crypto_trade.strategies.ml.risk_v2 import (
            BtcTrendFilterConfig,
            evaluate_btc_trend_filter_one_signal,
        )

        open_times, closes = _make_flat_btc()
        cfg = BtcTrendFilterConfig(
            lookback_bars=42, threshold_pct=4.0, enabled=True, long_only_mode=True
        )
        signal_open_time_ms = int(open_times[43])
        should_kill = evaluate_btc_trend_filter_one_signal(
            open_times, closes, signal_open_time_ms, direction=1, config=cfg
        )
        assert should_kill is False, "Long must NOT be killed when BTC ret is flat"


class TestWarmupPassThrough:
    """apply_btc_trend_filter warmup pass-through: insufficient BTC history → no kill."""

    def test_warmup_trade_passes_through(self) -> None:
        """Trade before 42 BTC bars are available → warmup; weight preserved."""
        from crypto_trade.backtest_models import TradeResult
        from crypto_trade.strategies.ml.risk_v2 import (
            BtcTrendFilterConfig,
            apply_btc_trend_filter,
        )

        # Only 10 BTC bars → warmup for any trade
        n_btc = 10
        open_times = np.arange(n_btc, dtype=np.int64) * 28800000
        closes = np.full(n_btc, 100.0)

        trade = TradeResult(
            symbol="LTCUSDT",
            direction=1,
            open_time=int(open_times[9]),
            entry_price=50.0,
            exit_price=51.0,
            pnl_pct=2.0,
            fee_pct=0.04,
            net_pnl_pct=1.96,
            weight_factor=1.0,
            weighted_pnl=2.0,
            exit_reason="take_profit",
            close_time=int(open_times[9]) + 28800000,
        )
        cfg = BtcTrendFilterConfig(
            lookback_bars=42, threshold_pct=4.0, enabled=True, long_only_mode=True
        )
        filtered, stats = apply_btc_trend_filter([trade], open_times, closes, cfg)

        assert stats.n_warmup == 1
        assert stats.n_killed == 0
        assert filtered[0].weight_factor == pytest.approx(1.0)

    def test_filter_disabled_no_kills(self) -> None:
        """When enabled=False, nothing is killed."""
        from crypto_trade.backtest_models import TradeResult
        from crypto_trade.strategies.ml.risk_v2 import (
            BtcTrendFilterConfig,
            apply_btc_trend_filter,
        )

        n_btc = 50
        open_times = np.arange(n_btc, dtype=np.int64) * 28800000
        closes = np.where(np.arange(n_btc) < 42, 100.0, 90.0)  # -10% move

        trade = TradeResult(
            symbol="LTCUSDT",
            direction=1,
            open_time=int(open_times[49]),
            entry_price=50.0,
            exit_price=48.0,
            pnl_pct=-4.0,
            fee_pct=0.04,
            net_pnl_pct=-4.04,
            weight_factor=1.0,
            weighted_pnl=-4.0,
            exit_reason="stop_loss",
            close_time=int(open_times[49]) + 28800000,
        )
        cfg = BtcTrendFilterConfig(
            lookback_bars=42, threshold_pct=4.0, enabled=False, long_only_mode=True
        )
        filtered, stats = apply_btc_trend_filter([trade], open_times, closes, cfg)

        assert stats.n_killed == 0
        assert stats.n_normal == 1
        assert filtered[0].weight_factor == pytest.approx(1.0)


class TestIter019Regression:
    """/019 ETH call site backward compatibility: long_only_mode not passed → default False."""

    def test_iter019_config_still_symmetric(self) -> None:
        """BtcTrendFilterConfig at /019 pinned values (no long_only_mode kwarg) is symmetric."""
        from crypto_trade.strategies.ml.risk_v2 import BtcTrendFilterConfig

        # Exactly as /019 constructs it — no long_only_mode kwarg
        cfg = BtcTrendFilterConfig(
            lookback_bars=42,
            threshold_pct=8.0,
            enabled=True,
        )
        assert cfg.long_only_mode is False

    def test_iter019_constants_unchanged(self) -> None:
        """V1_ITER019 gate constants must remain unchanged — /022 does not touch them."""
        from run_baseline_v1 import (
            V1_ITER019_BTC_GATE_ENABLED,
            V1_ITER019_BTC_GATE_LOOKBACK_BARS,
            V1_ITER019_BTC_GATE_THRESHOLD_PCT,
        )

        assert V1_ITER019_BTC_GATE_LOOKBACK_BARS == 42
        assert V1_ITER019_BTC_GATE_THRESHOLD_PCT == pytest.approx(8.0)
        assert V1_ITER019_BTC_GATE_ENABLED is True
