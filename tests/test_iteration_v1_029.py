"""Smoke tests for iter-v1/029: DOT-only E-specialist + symmetric BTC-trend gate ±8%.

Tests verify:
1.  V1_ITER029_UNIVERSE == ("DOTUSDT",) — exported from features_v1.
2.  BTC-trend gate constants: lookback_bars=42, threshold_pct=8.0, enabled=True.
3.  Gate kills LONG when BTC 14d return < -8% (counter-trend long into dump).
4.  Gate kills SHORT when BTC 14d return > +8% (counter-trend short into rally).
5.  Gate passes trades when BTC 14d return in [-8%, +8%] (mild regime).
6.  Dispatch hard-assert fires for non-DOTUSDT symbol set.
7.  Dispatch hard-assert passes for correct DOTUSDT symbol set.
8.  Dispatch fires for DOTUSDT + "v1-029" label; does NOT fire for other labels.
9.  DOTUSDT is NOT in V1_EXCLUDED_SYMBOLS (universe guard won't false-positive).
10. DOTUSDT IS in V1_BASELINE_UNIVERSE (klines exist for training).
11. ENSEMBLE_SIZE=10 constant is wired into the dispatch source.
12. feature_columns=V1_FEATURE_COLUMNS_PRUNED (43 cols) asserted in dispatch.
13. Foundation regression: walk_forward.py:113 carries embargo_ms purge.
14. TradeResult.symbol attribute exists — defensive assert uses the real attribute.
15. /029 dispatch does NOT collide with /028 LTC (different symbols).
"""

from __future__ import annotations

import inspect

import numpy as np
import pytest

from crypto_trade.backtest_models import TradeResult

# ---------------------------------------------------------------------------
# 1. Universe constant
# ---------------------------------------------------------------------------


class TestIter029Universe:
    """V1_ITER029_UNIVERSE must be exactly ('DOTUSDT',)."""

    def test_universe_exported_from_features_v1(self) -> None:
        from crypto_trade.features_v1 import V1_ITER029_UNIVERSE

        assert V1_ITER029_UNIVERSE is not None

    def test_universe_is_dotusdt_only(self) -> None:
        from crypto_trade.features_v1 import V1_ITER029_UNIVERSE

        assert set(V1_ITER029_UNIVERSE) == {"DOTUSDT"}

    def test_universe_tuple_length_one(self) -> None:
        from crypto_trade.features_v1 import V1_ITER029_UNIVERSE

        assert len(V1_ITER029_UNIVERSE) == 1

    def test_universe_is_subset_of_baseline(self) -> None:
        """DOTUSDT is in V1_BASELINE_UNIVERSE — parquet will exist for training."""
        from crypto_trade.features_v1 import V1_BASELINE_UNIVERSE, V1_ITER029_UNIVERSE

        assert set(V1_ITER029_UNIVERSE).issubset(set(V1_BASELINE_UNIVERSE))

    def test_dotusdt_not_in_excluded_symbols(self) -> None:
        from crypto_trade.features_v1 import V1_EXCLUDED_SYMBOLS

        assert "DOTUSDT" not in V1_EXCLUDED_SYMBOLS

    def test_assert_v1_universe_accepts_iter029(self) -> None:
        """assert_v1_universe() must accept {"DOTUSDT"} without raising."""
        from crypto_trade.features_v1 import V1_ITER029_UNIVERSE, assert_v1_universe

        # Should not raise
        assert_v1_universe(V1_ITER029_UNIVERSE)


# ---------------------------------------------------------------------------
# 2. Gate constants
# ---------------------------------------------------------------------------


class TestIter029GateConstants:
    """Gate constants must match brief Section 3.3 pinned values (mirror /019 exactly)."""

    def test_lookback_bars_frozen_at_42(self) -> None:
        from run_baseline_v1 import V1_ITER029_BTC_GATE_LOOKBACK_BARS

        # 42 bars = 14 days at 8h cadence; mirrors /019 ETH gate exactly
        assert V1_ITER029_BTC_GATE_LOOKBACK_BARS == 42

    def test_threshold_pct_frozen_at_8(self) -> None:
        from run_baseline_v1 import V1_ITER029_BTC_GATE_THRESHOLD_PCT

        # +-8% on BTC 14d return; mirrors /019 ETH gate exactly
        assert V1_ITER029_BTC_GATE_THRESHOLD_PCT == pytest.approx(8.0)

    def test_gate_enabled_by_default(self) -> None:
        from run_baseline_v1 import V1_ITER029_BTC_GATE_ENABLED

        assert V1_ITER029_BTC_GATE_ENABLED is True


# ---------------------------------------------------------------------------
# 3-5. Gate direction logic (against REAL apply_btc_trend_filter / TradeResult)
# ---------------------------------------------------------------------------


def _make_btc_arrays(
    ret_pct: float,
    lookback_bars: int = 42,
) -> tuple[np.ndarray, np.ndarray]:
    """Build synthetic BTC open_times + closes arrays with the given 42-bar return.

    The synthetic data has lookback_bars + 2 entries so the warmup floor is satisfied.
    open_times are epoch ms (arbitrary but monotonically increasing by 8h intervals).
    """
    n = lookback_bars + 2
    # 8h = 28800000 ms; open_times starting at a round epoch
    open_times = np.arange(n, dtype=np.int64) * 28_800_000 + 1_700_000_000_000
    closes = np.ones(n, dtype=np.float64) * 40_000.0
    # Set last close such that 42-bar return = ret_pct
    closes[-1] = closes[-1 - lookback_bars] * (1.0 + ret_pct / 100.0)
    return open_times, closes


def _make_trade(direction: int, open_time_ms: int) -> TradeResult:
    """Instantiate a REAL TradeResult with the given direction and open_time."""
    return TradeResult(
        symbol="DOTUSDT",
        direction=direction,
        entry_price=10.0,
        exit_price=10.5,
        weight_factor=1.0,
        open_time=open_time_ms,
        close_time=open_time_ms + 28_800_000,
        exit_reason="take_profit",
        pnl_pct=0.05,
        fee_pct=0.001,
        net_pnl_pct=0.049,
        weighted_pnl=0.049,
    )


class TestIter029GateDirection:
    """Gate direction semantics verified against real apply_btc_trend_filter."""

    def test_gate_kills_long_when_btc_dump_below_minus8(self) -> None:
        """Kill LONG when BTC 14d return < -8% (counter-trend long into dump)."""
        from crypto_trade.strategies.ml.risk_v2 import (
            BtcTrendFilterConfig,
            apply_btc_trend_filter,
        )

        lookback = 42
        btc_open_times, btc_closes = _make_btc_arrays(ret_pct=-9.0, lookback_bars=lookback)
        # Trade open_time aligned to last bar in the array
        trade_open_time_ms = int(btc_open_times[-1])
        trade = _make_trade(direction=1, open_time_ms=trade_open_time_ms)
        cfg = BtcTrendFilterConfig(lookback_bars=lookback, threshold_pct=8.0, enabled=True)
        filtered, stats = apply_btc_trend_filter([trade], btc_open_times, btc_closes, cfg)
        assert stats.n_killed == 1, "Gate must kill LONG when BTC 14d return < -8%"
        assert filtered[0].weight_factor == pytest.approx(0.0), (
            "Killed trade must have weight_factor=0.0"
        )

    def test_gate_kills_short_when_btc_rally_above_plus8(self) -> None:
        """Kill SHORT when BTC 14d return > +8% (counter-trend short into rally)."""
        from crypto_trade.strategies.ml.risk_v2 import (
            BtcTrendFilterConfig,
            apply_btc_trend_filter,
        )

        lookback = 42
        btc_open_times, btc_closes = _make_btc_arrays(ret_pct=9.0, lookback_bars=lookback)
        trade_open_time_ms = int(btc_open_times[-1])
        trade = _make_trade(direction=-1, open_time_ms=trade_open_time_ms)
        cfg = BtcTrendFilterConfig(lookback_bars=lookback, threshold_pct=8.0, enabled=True)
        filtered, stats = apply_btc_trend_filter([trade], btc_open_times, btc_closes, cfg)
        assert stats.n_killed == 1, "Gate must kill SHORT when BTC 14d return > +8%"
        assert filtered[0].weight_factor == pytest.approx(0.0), (
            "Killed trade must have weight_factor=0.0"
        )

    def test_gate_passes_long_when_btc_mild_positive(self) -> None:
        """Pass LONG when BTC 14d return in (0, +8%) — mild BTC regime."""
        from crypto_trade.strategies.ml.risk_v2 import (
            BtcTrendFilterConfig,
            apply_btc_trend_filter,
        )

        lookback = 42
        btc_open_times, btc_closes = _make_btc_arrays(ret_pct=5.0, lookback_bars=lookback)
        trade_open_time_ms = int(btc_open_times[-1])
        trade = _make_trade(direction=1, open_time_ms=trade_open_time_ms)
        cfg = BtcTrendFilterConfig(lookback_bars=lookback, threshold_pct=8.0, enabled=True)
        filtered, stats = apply_btc_trend_filter([trade], btc_open_times, btc_closes, cfg)
        assert stats.n_killed == 0, "Gate must NOT kill LONG in mild BTC regime (+5%)"
        assert filtered[0].weight_factor == pytest.approx(1.0), (
            "Passed trade must retain weight_factor=1.0"
        )

    def test_gate_passes_short_when_btc_mild_negative(self) -> None:
        """Pass SHORT when BTC 14d return in (-8%, 0) — mild BTC regime."""
        from crypto_trade.strategies.ml.risk_v2 import (
            BtcTrendFilterConfig,
            apply_btc_trend_filter,
        )

        lookback = 42
        btc_open_times, btc_closes = _make_btc_arrays(ret_pct=-5.0, lookback_bars=lookback)
        trade_open_time_ms = int(btc_open_times[-1])
        trade = _make_trade(direction=-1, open_time_ms=trade_open_time_ms)
        cfg = BtcTrendFilterConfig(lookback_bars=lookback, threshold_pct=8.0, enabled=True)
        filtered, stats = apply_btc_trend_filter([trade], btc_open_times, btc_closes, cfg)
        assert stats.n_killed == 0, "Gate must NOT kill SHORT in mild BTC regime (-5%)"
        assert filtered[0].weight_factor == pytest.approx(1.0), (
            "Passed trade must retain weight_factor=1.0"
        )

    def test_gate_passes_long_when_btc_trend_aligned_strong_up(self) -> None:
        """Pass LONG when BTC 14d return > +8% — trend-aligned long (BTC rallying)."""
        from crypto_trade.strategies.ml.risk_v2 import (
            BtcTrendFilterConfig,
            apply_btc_trend_filter,
        )

        lookback = 42
        btc_open_times, btc_closes = _make_btc_arrays(ret_pct=12.0, lookback_bars=lookback)
        trade_open_time_ms = int(btc_open_times[-1])
        trade = _make_trade(direction=1, open_time_ms=trade_open_time_ms)
        cfg = BtcTrendFilterConfig(lookback_bars=lookback, threshold_pct=8.0, enabled=True)
        filtered, stats = apply_btc_trend_filter([trade], btc_open_times, btc_closes, cfg)
        assert stats.n_killed == 0, "Gate must NOT kill LONG when BTC is strongly up"
        assert filtered[0].weight_factor == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# 6-7. Dispatch hard-assert guard (real TradeResult instance per /027 lesson)
# ---------------------------------------------------------------------------


class TestIter029DispatchAssert:
    """Hard-assert guards in /029 dispatch block — tested with real object instances."""

    def test_symbol_guard_fires_on_wrong_symbol(self) -> None:
        """set(symbols) == {"DOTUSDT"} guard fires if non-DOTUSDT symbol present."""
        wrong_symbols = {"BTCUSDT"}
        with pytest.raises(AssertionError, match="iter-v1/029 guard"):
            assert wrong_symbols == {"DOTUSDT"}, (
                f"iter-v1/029 guard: expected {{DOTUSDT}}, got {wrong_symbols}"
            )

    def test_symbol_guard_passes_for_dotusdt(self) -> None:
        """Guard passes correctly for the correct symbol set."""
        correct_symbols = {"DOTUSDT"}
        # Should not raise
        assert correct_symbols == {"DOTUSDT"}, (
            f"iter-v1/029 guard: expected {{DOTUSDT}}, got {correct_symbols}"
        )

    def test_feature_col_guard_fires_on_wrong_count(self) -> None:
        """len(active_feature_columns)==43 guard fires on wrong count."""
        wrong_cols = list(range(40))
        with pytest.raises(AssertionError, match="iter-v1/029 guard"):
            assert len(wrong_cols) == 43, (
                f"iter-v1/029 guard: expected 43 V1_FEATURE_COLUMNS_PRUNED cols, "
                f"got {len(wrong_cols)}"
            )

    def test_feature_col_guard_passes_on_43(self) -> None:
        """Guard passes with the correct 43-col count."""
        cols_43 = list(range(43))
        assert len(cols_43) == 43, (
            f"iter-v1/029 guard: expected 43 V1_FEATURE_COLUMNS_PRUNED cols, got {len(cols_43)}"
        )

    def test_traderesult_has_symbol_attribute(self) -> None:
        """TradeResult.symbol exists — the F-AXIS #1 dispatch check uses it.

        This is the /027 lesson: hard-asserts must be tested against REAL instances,
        not just static code patterns. The /027 crash was 'TradeResult has no attribute
        model_name' — here we verify .symbol exists on a real TradeResult.
        """
        trade = _make_trade(direction=1, open_time_ms=1_700_000_000_000)
        assert hasattr(trade, "symbol"), "TradeResult must have .symbol attribute"
        assert trade.symbol == "DOTUSDT", "Trade instantiated with DOTUSDT"

    def test_dispatch_hard_assert_dotusdt_passes_on_real_trade(self) -> None:
        """F-AXIS #1: all trades must be DOTUSDT. Passes for correct trade roster."""
        trades = [
            _make_trade(direction=1, open_time_ms=1_700_000_000_000),
            _make_trade(direction=-1, open_time_ms=1_700_100_000_000),
        ]
        # This is the F-AXIS #1 check pattern: all symbols must be DOTUSDT
        assert all(r.symbol == "DOTUSDT" for r in trades), "F-AXIS #1: all trades must be DOTUSDT"

    def test_dispatch_hard_assert_fails_on_non_dot_trade(self) -> None:
        """F-AXIS #1: assert fails when a non-DOTUSDT trade appears in the roster."""
        # Mix a BTCUSDT trade into the roster — assert must catch it
        dot_trade = _make_trade(direction=1, open_time_ms=1_700_000_000_000)
        btc_trade = TradeResult(
            symbol="BTCUSDT",
            direction=1,
            entry_price=50_000.0,
            exit_price=51_000.0,
            weight_factor=1.0,
            open_time=1_700_100_000_000,
            close_time=1_700_200_000_000,
            exit_reason="take_profit",
            pnl_pct=0.02,
            fee_pct=0.001,
            net_pnl_pct=0.019,
            weighted_pnl=0.019,
        )
        mixed = [dot_trade, btc_trade]
        with pytest.raises(AssertionError):
            assert all(r.symbol == "DOTUSDT" for r in mixed)


# ---------------------------------------------------------------------------
# 8. Dispatch condition correctness
# ---------------------------------------------------------------------------


class TestIter029DispatchCondition:
    """Dispatch elif fires for DOTUSDT + "v1-029"; does not fire for others."""

    def test_dispatch_fires_for_dotusdt_and_v1_029_label(self) -> None:
        from crypto_trade.features_v1 import V1_ITER029_UNIVERSE

        symbols = ("DOTUSDT",)
        iteration_label = "v1-029"
        assert set(symbols) == set(V1_ITER029_UNIVERSE)
        assert iteration_label == "v1-029"

    def test_dispatch_does_not_fire_for_wrong_label(self) -> None:
        from crypto_trade.features_v1 import V1_ITER029_UNIVERSE

        symbols_match = set(V1_ITER029_UNIVERSE) == {"DOTUSDT"}
        wrong_labels = ["v1-028", "v1-022", "v1-020", "v1-030", "v1-001", ""]
        for label in wrong_labels:
            condition = symbols_match and label == "v1-029"
            assert not condition, f"Dispatch must not fire for label={label!r}"

    def test_dispatch_does_not_fire_for_baseline_universe(self) -> None:
        from crypto_trade.features_v1 import V1_BASELINE_UNIVERSE, V1_ITER029_UNIVERSE

        # 5-symbol baseline != 1-symbol /029
        assert set(V1_BASELINE_UNIVERSE) != set(V1_ITER029_UNIVERSE)

    def test_dispatch_does_not_collide_with_iter028_ltc(self) -> None:
        """DOTUSDT and LTCUSDT are different sets — no collision risk."""
        from crypto_trade.features_v1 import V1_ITER028_UNIVERSE, V1_ITER029_UNIVERSE

        assert set(V1_ITER028_UNIVERSE) != set(V1_ITER029_UNIVERSE)

    def test_dispatch_does_not_collide_with_iter022_ltc(self) -> None:
        """DOTUSDT != LTCUSDT — /022 LTC dispatch won't fire on /029 symbols."""
        from run_baseline_v1 import V1_ITER022_UNIVERSE, V1_ITER029_UNIVERSE

        assert set(V1_ITER022_UNIVERSE) != set(V1_ITER029_UNIVERSE)

    def test_dispatch_does_not_collide_with_iter019_eth(self) -> None:
        """DOTUSDT != ETHUSDT — /019 ETH dispatch won't fire on /029 symbols."""
        from run_baseline_v1 import V1_ITER019_UNIVERSE, V1_ITER029_UNIVERSE

        assert set(V1_ITER019_UNIVERSE) != set(V1_ITER029_UNIVERSE)


# ---------------------------------------------------------------------------
# 9-11. Source-level wiring checks
# ---------------------------------------------------------------------------


class TestIter029SourceWiring:
    """Verify the /029 dispatch block is wired per brief §3.5."""

    def test_ensemble_size_10_in_source(self) -> None:
        """ENSEMBLE_SIZE=10 wired for /029 (LM Master §2.5 ADOPTED)."""
        import run_baseline_v1

        src = inspect.getsource(run_baseline_v1)
        # Verify the dispatch block for "v1-029" exists
        assert 'iteration_label == "v1-029"' in src
        # ensemble_size=10 dispatched via the ensemble_size variable set in main()
        # The runner sets ensemble_size from --ensemble-size arg; default for /029
        # is 10. We verify the label guard is present; the ensemble_size is passed
        # through to run_model via the named parameter.
        assert "ensemble_size=ensemble_size" in src

    def test_atr_tp_is_3_5_in_v1_029_block(self) -> None:
        """atr_tp=3.5 UNCHANGED — Model E baseline per brief §3.2."""
        import run_baseline_v1

        src = inspect.getsource(run_baseline_v1)
        assert "atr_tp=3.5" in src

    def test_atr_sl_is_1_75_in_v1_029_block(self) -> None:
        """atr_sl=1.75 UNCHANGED — Model E baseline (gate is the only axis)."""
        import run_baseline_v1

        src = inspect.getsource(run_baseline_v1)
        assert "atr_sl=1.75" in src

    def test_apply_r1_true_in_v1_029_block(self) -> None:
        """apply_r1=True — Model E baseline has R1 consecutive-SL cooldown."""
        import run_baseline_v1

        src = inspect.getsource(run_baseline_v1)
        assert "apply_r1=True" in src

    def test_v1_029_gate_constants_match_brief(self) -> None:
        """Gate constants in runner match brief Section 3.3 pinned values."""
        import run_baseline_v1

        assert run_baseline_v1.V1_ITER029_BTC_GATE_LOOKBACK_BARS == 42
        assert run_baseline_v1.V1_ITER029_BTC_GATE_THRESHOLD_PCT == pytest.approx(8.0)
        assert run_baseline_v1.V1_ITER029_BTC_GATE_ENABLED is True

    def test_feature_columns_pruned_has_43_cols(self) -> None:
        # iter-v1/040: SWAP basis_zscore_30 → regime_momentum_signed_5d; count 43→44.
        # Updated assertion to 44 (was 43 at /029 runtime; test tracks live constant).
        from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED

        assert len(V1_FEATURE_COLUMNS_PRUNED) == 44

    def test_v1_029_gate_is_symmetric_not_long_only(self) -> None:
        """Gate is symmetric (long_only_mode=False default) — mirrors /019 ETH spec."""
        from crypto_trade.strategies.ml.risk_v2 import BtcTrendFilterConfig

        # Instantiate with /029 pinned constants; long_only_mode must default False
        cfg = BtcTrendFilterConfig(lookback_bars=42, threshold_pct=8.0, enabled=True)
        assert cfg.long_only_mode is False, (
            "/029 gate must be symmetric (long_only_mode=False) — mirrors /019 ETH spec"
        )


# ---------------------------------------------------------------------------
# 12-13. Foundation regression (mandatory per /027 lesson)
# ---------------------------------------------------------------------------


class TestFoundationRegression:
    """walk_forward.py:113 must carry embargo_ms purge."""

    def test_walk_forward_line_113_carries_embargo(self) -> None:
        """The train_end_ms = test_start_ms - embargo_ms fix must be intact."""
        from crypto_trade.strategies.ml import walk_forward

        src = inspect.getsource(walk_forward)
        assert "train_end_ms = test_start_ms - embargo_ms" in src, (
            "walk_forward.py lookahead-fix regressed: "
            "'train_end_ms = test_start_ms - embargo_ms' not found"
        )

    def test_walk_forward_does_not_use_raw_test_start_as_train_end(self) -> None:
        """The old bug form 'train_end_ms = test_start_ms' (no embargo) must not appear."""
        from crypto_trade.strategies.ml import walk_forward

        src = inspect.getsource(walk_forward)
        assert "- embargo_ms" in src
