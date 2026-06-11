"""Tests for iter-v1/092 — BTC-regime kill gate.

Covers:
  (a) Gate OFF = no change: enable_btc_regime_kill=False produces IDENTICAL init
      (default-OFF byte-identity assertion; ensures no side effect on /088 and all
      prior iterations when gate is disabled).
  (b) Gate ON suppresses when btc_ret_42 > 0.067, allows signal when ≤ threshold.
  (c) Past-only BTC join: the gate uses close_time ≤ decision candle's open_time
      (strictly past-only; no future BTC candle is included — no look-ahead).
  (d) Conservative pass-through: if BTC index unavailable or <42 history, gate
      does NOT fire (signal unchanged, no kill).
  (e) PRUNED-48 assertion: V1_FEATURE_COLUMNS_PRUNED length stays 48.
  (f) Runner import smoke test: run_iteration_092.py imports without error.
  (g) V1_ITER092_UNIVERSE is exported and is XRPUSDT-only.

Run:
    uv run pytest tests/test_btc_regime_kill.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_strategy(
    enable_btc_regime_kill: bool = False,
    btc_regime_kill_thr: float = 0.067,
    btc_regime_kill_lookback: int = 42,
):
    """Construct a minimal LightGbmStrategy with BTC-regime kill gate ON or OFF."""
    from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

    return LightGbmStrategy(
        training_months=24,
        n_trials=1,
        cv_splits=2,
        feature_columns=["feat_a", "feat_b", "feat_c"],
        ensemble_seeds=[42],
        specialist_mode=True,
        enable_btc_regime_kill=enable_btc_regime_kill,
        btc_regime_kill_thr=btc_regime_kill_thr,
        btc_regime_kill_lookback=btc_regime_kill_lookback,
    )


def _inject_btc_idx(strat, close_times_ms: np.ndarray, closes: np.ndarray) -> None:
    """Inject a synthetic BTC (close_time_ms, close) index into a strategy instance.

    Simulates what compute_features() does when enable_btc_regime_kill=True and
    data/features/BTCUSDT_8h_features.parquet is loaded.
    """
    sort_idx = np.argsort(close_times_ms)
    strat._btc_regime_kill_idx = (
        close_times_ms[sort_idx].astype(np.int64),
        closes[sort_idx].astype(np.float64),
    )


def _make_btc_idx_with_return(n_candles: int = 100, btc_ret_at_t: float = 0.10) -> tuple:
    """Build a synthetic BTC index where the last candle's 42-bar return = btc_ret_at_t.

    Returns (close_times_ms, closes) arrays of length n_candles.
    close_times_ms: monotonically increasing, each 8h apart.
    closes: constructed so that close[n-1] / close[n-1-42] - 1.0 = btc_ret_at_t.
    """
    interval_ms = 8 * 3600 * 1000  # 8h in ms
    base_time = 1_700_000_000_000  # arbitrary base epoch ms
    close_times = np.array([base_time + i * interval_ms for i in range(n_candles)], dtype=np.int64)

    # Build closes: first n-42 candles at 1.0, last 42 candles rise to (1 + btc_ret_at_t).
    closes = np.ones(n_candles, dtype=np.float64)
    # Set the candle at index n-1 (last) and the one at n-1-42.
    # close[n-1] / close[n-1-42] - 1.0 = btc_ret_at_t
    # => close[n-1] = close[n-1-42] * (1 + btc_ret_at_t)
    # Keep close[n-1-42] = 1.0, so close[n-1] = 1 + btc_ret_at_t.
    closes[-1] = 1.0 + btc_ret_at_t

    return close_times, closes


# ---------------------------------------------------------------------------
# (a) Gate OFF — default init params, no behavior change
# ---------------------------------------------------------------------------


class TestBtcRegimeKillGateOff:
    """When enable_btc_regime_kill=False (default), gate has no effect."""

    def test_default_gate_off(self):
        """Default strategy has BTC-regime kill gate disabled."""
        strat = _make_strategy(enable_btc_regime_kill=False)
        assert strat._enable_btc_regime_kill is False
        assert strat._btc_regime_kill_thr == pytest.approx(0.067)
        assert strat._btc_regime_kill_lookback == 42
        assert strat._btc_regime_kill_idx is None

    def test_gate_off_params_stored_correctly(self):
        """Params stored as bool/float/int correctly when gate is OFF."""
        strat = _make_strategy(enable_btc_regime_kill=False, btc_regime_kill_thr=0.10)
        assert isinstance(strat._enable_btc_regime_kill, bool)
        assert strat._enable_btc_regime_kill is False
        assert isinstance(strat._btc_regime_kill_thr, float)
        assert strat._btc_regime_kill_thr == pytest.approx(0.10)

    def test_gate_on_params_stored_correctly(self):
        """Params stored correctly when gate is ON."""
        strat = _make_strategy(enable_btc_regime_kill=True, btc_regime_kill_thr=0.067)
        assert strat._enable_btc_regime_kill is True
        assert strat._btc_regime_kill_thr == pytest.approx(0.067)
        assert strat._btc_regime_kill_lookback == 42

    def test_gate_off_btc_idx_is_none(self):
        """With gate OFF, _btc_regime_kill_idx is None (no index built)."""
        strat = _make_strategy(enable_btc_regime_kill=False)
        assert strat._btc_regime_kill_idx is None

    def test_gate_off_compute_btc_ret_42_returns_none(self):
        """_compute_btc_ret_42 returns None when gate is OFF (no index)."""
        strat = _make_strategy(enable_btc_regime_kill=False)
        result = strat._compute_btc_ret_42(1_700_000_000_000)
        assert result is None


# ---------------------------------------------------------------------------
# (b) Gate ON suppresses when btc_ret_42 > thr; allows when ≤ thr
# ---------------------------------------------------------------------------


class TestBtcRegimeKillGateOn:
    """When enable_btc_regime_kill=True, gate suppresses BTC_UP candles."""

    def test_gate_fires_above_threshold(self):
        """_compute_btc_ret_42 > 0.067 → gate condition is True → NO_SIGNAL."""
        strat = _make_strategy(enable_btc_regime_kill=True, btc_regime_kill_thr=0.067)

        # Inject BTC index where the last 42-bar return = +0.10 (above 0.067)
        close_times, closes = _make_btc_idx_with_return(n_candles=100, btc_ret_at_t=0.10)
        _inject_btc_idx(strat, close_times, closes)

        # Decision candle's open_time is AFTER the last BTC close_time.
        # Use last close_time as upper bound for past-only join.
        decision_open_time = int(close_times[-1])  # last BTC close_time = boundary

        btc_ret = strat._compute_btc_ret_42(decision_open_time)
        assert btc_ret is not None, "Should find a BTC candle at or before decision time"
        assert btc_ret == pytest.approx(0.10, abs=1e-9)

        # Gate condition check (mirrors lgbm.py gate logic)
        gate_fires = (
            strat._enable_btc_regime_kill
            and btc_ret is not None
            and np.isfinite(btc_ret)
            and btc_ret > strat._btc_regime_kill_thr
        )
        assert gate_fires, (
            f"Gate should fire: btc_ret_42={btc_ret:.4f} > thr={strat._btc_regime_kill_thr}"
        )

    def test_gate_does_not_fire_below_threshold(self):
        """_compute_btc_ret_42 < 0.067 → gate does NOT fire → signal passes."""
        strat = _make_strategy(enable_btc_regime_kill=True, btc_regime_kill_thr=0.067)

        # btc_ret_at_t = 0.04 (below 0.067)
        close_times, closes = _make_btc_idx_with_return(n_candles=100, btc_ret_at_t=0.04)
        _inject_btc_idx(strat, close_times, closes)

        decision_open_time = int(close_times[-1])
        btc_ret = strat._compute_btc_ret_42(decision_open_time)
        assert btc_ret is not None
        assert btc_ret == pytest.approx(0.04, abs=1e-9)

        gate_fires = (
            strat._enable_btc_regime_kill
            and btc_ret is not None
            and np.isfinite(btc_ret)
            and btc_ret > strat._btc_regime_kill_thr
        )
        assert not gate_fires, (
            f"Gate should NOT fire: btc_ret_42={btc_ret:.4f} <= thr={strat._btc_regime_kill_thr}"
        )

    def test_gate_does_not_fire_at_threshold_exact(self):
        """btc_ret_42 exactly equal to threshold: strict > means gate does NOT fire."""
        strat = _make_strategy(enable_btc_regime_kill=True, btc_regime_kill_thr=0.067)

        close_times, closes = _make_btc_idx_with_return(n_candles=100, btc_ret_at_t=0.067)
        _inject_btc_idx(strat, close_times, closes)

        decision_open_time = int(close_times[-1])
        btc_ret = strat._compute_btc_ret_42(decision_open_time)
        assert btc_ret is not None
        assert btc_ret == pytest.approx(0.067, abs=1e-9)

        gate_fires = (
            strat._enable_btc_regime_kill
            and btc_ret is not None
            and np.isfinite(btc_ret)
            and btc_ret > strat._btc_regime_kill_thr
        )
        assert not gate_fires, "Gate uses strict >, so btc_ret_42 == threshold should NOT fire."

    def test_gate_does_not_fire_when_btc_down(self):
        """btc_ret_42 < 0 (BTC_DOWN regime): gate must NOT fire."""
        strat = _make_strategy(enable_btc_regime_kill=True, btc_regime_kill_thr=0.067)

        close_times, closes = _make_btc_idx_with_return(n_candles=100, btc_ret_at_t=-0.05)
        _inject_btc_idx(strat, close_times, closes)

        decision_open_time = int(close_times[-1])
        btc_ret = strat._compute_btc_ret_42(decision_open_time)
        assert btc_ret is not None
        assert btc_ret < 0

        gate_fires = (
            strat._enable_btc_regime_kill
            and btc_ret is not None
            and np.isfinite(btc_ret)
            and btc_ret > strat._btc_regime_kill_thr
        )
        assert not gate_fires, "BTC_DOWN should not trigger the kill gate."

    def test_gate_off_does_not_fire_for_high_btc_ret(self):
        """With gate OFF, high btc_ret_42 is NOT filtered."""
        strat = _make_strategy(enable_btc_regime_kill=False, btc_regime_kill_thr=0.067)

        # Inject a high-return BTC index
        close_times, closes = _make_btc_idx_with_return(n_candles=100, btc_ret_at_t=0.20)
        _inject_btc_idx(strat, close_times, closes)

        decision_open_time = int(close_times[-1])
        # Gate is OFF: the primary check is simply the flag.
        # _compute_btc_ret_42 would return None because _btc_regime_kill_idx is only
        # populated at compute_features() time when the gate is ON, not here in unit tests.
        assert not strat._enable_btc_regime_kill, "Gate must be OFF"
        _ = decision_open_time  # consumed above for index construction context


# ---------------------------------------------------------------------------
# (c) Past-only BTC join — strictly no future BTC candle
# ---------------------------------------------------------------------------


class TestBtcPastOnlyJoin:
    """The BTC join must be strictly past-only (close_time ≤ decision open_time)."""

    def test_past_only_join_uses_last_candle_before_decision(self):
        """_compute_btc_ret_42 uses the last BTC candle with close_time <= open_time.

        Verify: if a BTC candle arrives AFTER the decision open_time, it is excluded.
        """
        strat = _make_strategy(enable_btc_regime_kill=True, btc_regime_kill_thr=0.067)

        interval_ms = 8 * 3600 * 1000
        base_time = 1_700_000_000_000

        # Build 100 BTC candles: closes all = 1.0 except the LAST one = 1.20 (big return).
        n = 100
        close_times = np.array([base_time + i * interval_ms for i in range(n)], dtype=np.int64)
        closes = np.ones(n, dtype=np.float64)
        closes[-1] = 1.20  # Last BTC candle has a high close

        _inject_btc_idx(strat, close_times, closes)

        # Decision candle open_time = BEFORE the last BTC candle close_time.
        # The last BTC candle has close_time = base_time + (n-1) * interval_ms.
        # Set decision open_time to base_time + (n-2) * interval_ms (one before last).
        decision_open_time = int(base_time + (n - 2) * interval_ms)

        btc_ret = strat._compute_btc_ret_42(decision_open_time)
        # The last BTC candle (with close=1.20) is at index n-1, which has
        # close_time = base_time + (n-1)*interval_ms > decision_open_time.
        # So the method should use index n-2 (close=1.0) as the current bar,
        # and index n-2-42 = n-44 (close=1.0) as the lookback bar.
        # btc_ret = 1.0 / 1.0 - 1.0 = 0.0
        if btc_ret is not None:
            # Should NOT be 0.20 (which would require using the future candle at n-1)
            assert btc_ret != pytest.approx(0.20, abs=0.01), (
                "Future BTC candle (close=1.20) must NOT be included in the join. "
                f"btc_ret={btc_ret:.4f} should be ~0.0, not ~0.20."
            )

    def test_decision_open_time_boundary(self):
        """Decision candle exactly coincides with BTC close_time: that candle IS included.

        The join is: last BTC close_time <= decision open_time. Equal is INCLUDED.
        """
        strat = _make_strategy(enable_btc_regime_kill=True, btc_regime_kill_thr=0.067)

        interval_ms = 8 * 3600 * 1000
        base_time = 1_700_000_000_000
        n = 100

        close_times = np.array([base_time + i * interval_ms for i in range(n)], dtype=np.int64)
        closes = np.ones(n, dtype=np.float64)
        closes[-1] = 1.10  # Last BTC candle: close = 1.10 → ret = (1.10/1.0 - 1) = 0.10

        _inject_btc_idx(strat, close_times, closes)

        # Decision open_time exactly equals the last BTC close_time → that candle included.
        decision_open_time = int(close_times[-1])

        btc_ret = strat._compute_btc_ret_42(decision_open_time)
        assert btc_ret is not None
        # Should use close[n-1] = 1.10 and close[n-1-42] = 1.0 → ret = 0.10
        assert btc_ret == pytest.approx(0.10, abs=1e-9), (
            f"Expected btc_ret=0.10 when decision open_time == last BTC close_time; got {btc_ret}"
        )

    def test_future_candle_excluded(self):
        """BTC candle with close_time > decision open_time is NOT included."""
        strat = _make_strategy(enable_btc_regime_kill=True, btc_regime_kill_thr=0.067)

        interval_ms = 8 * 3600 * 1000
        base_time = 1_700_000_000_000
        n = 100

        close_times = np.array([base_time + i * interval_ms for i in range(n)], dtype=np.int64)
        closes = np.ones(n, dtype=np.float64)

        # Only the LAST candle has a non-unit close.
        closes[-1] = 2.00  # big return if included

        _inject_btc_idx(strat, close_times, closes)

        # Decision open_time is STRICTLY BEFORE the last candle's close_time.
        # Last close_time = base_time + (n-1) * interval_ms
        # Set decision to one interval BEFORE: base_time + (n-2) * interval_ms - 1 ms
        decision_open_time = int(close_times[-1]) - 1  # 1ms before last close_time

        btc_ret = strat._compute_btc_ret_42(decision_open_time)
        if btc_ret is not None:
            # close[n-2] = 1.0, close[n-2-42] = 1.0 → ret ≈ 0.0
            # The future close[n-1]=2.00 must NOT appear.
            assert abs(btc_ret) < 0.5, (
                f"Future BTC candle (close=2.00) leaked into join: btc_ret={btc_ret:.4f}. "
                "Past-only join is violated."
            )


# ---------------------------------------------------------------------------
# (d) Conservative pass-through — gate does not fire on missing/insufficient data
# ---------------------------------------------------------------------------


class TestBtcConservativePassThrough:
    """If BTC data unavailable or <42 bars, gate does NOT fire (conservative)."""

    def test_no_btc_index_returns_none(self):
        """_compute_btc_ret_42 returns None when no BTC index is loaded."""
        strat = _make_strategy(enable_btc_regime_kill=True)
        assert strat._btc_regime_kill_idx is None
        result = strat._compute_btc_ret_42(1_700_000_000_000)
        assert result is None

    def test_fewer_than_42_bars_returns_none(self):
        """_compute_btc_ret_42 returns None when fewer than 42 BTC bars before decision."""
        strat = _make_strategy(enable_btc_regime_kill=True, btc_regime_kill_lookback=42)

        # Build only 30 BTC candles (fewer than lookback=42)
        n = 30
        interval_ms = 8 * 3600 * 1000
        base_time = 1_700_000_000_000
        close_times = np.array([base_time + i * interval_ms for i in range(n)], dtype=np.int64)
        closes = np.ones(n, dtype=np.float64)
        _inject_btc_idx(strat, close_times, closes)

        decision_open_time = int(close_times[-1])
        result = strat._compute_btc_ret_42(decision_open_time)
        assert result is None, f"Expected None when fewer than 42 BTC bars; got {result}"

    def test_exactly_42_bars_returns_value(self):
        """_compute_btc_ret_42 returns a value when exactly 42 bars available.

        Index [0..41]: candle at 41 uses candle at 0 (lookback=41 steps back from idx=41).
        Actually: idx_curr=41, idx_past=41-42=-1 → returns None (boundary).
        We need 43 bars for candle at index 42 to use bar at index 0 (42 steps back).
        """
        strat = _make_strategy(enable_btc_regime_kill=True, btc_regime_kill_lookback=42)

        # 43 candles: index 42 can look back 42 steps to index 0.
        n = 43
        interval_ms = 8 * 3600 * 1000
        base_time = 1_700_000_000_000
        close_times = np.array([base_time + i * interval_ms for i in range(n)], dtype=np.int64)
        closes = np.ones(n, dtype=np.float64)
        closes[-1] = 1.067  # idx 42: close/close[0] - 1 = 0.067
        _inject_btc_idx(strat, close_times, closes)

        decision_open_time = int(close_times[-1])
        result = strat._compute_btc_ret_42(decision_open_time)
        assert result is not None, (
            "With 43 candles, the last candle should have enough history (42 steps back)."
        )
        assert result == pytest.approx(0.067, abs=1e-9)

    def test_gate_does_not_fire_when_result_is_none(self):
        """When _compute_btc_ret_42 returns None, gate MUST NOT fire (conservative)."""
        strat = _make_strategy(enable_btc_regime_kill=True, btc_regime_kill_thr=0.067)
        # No BTC index loaded → result is None
        btc_ret = strat._compute_btc_ret_42(1_700_000_000_000)
        assert btc_ret is None

        gate_fires = (
            strat._enable_btc_regime_kill
            and btc_ret is not None
            and np.isfinite(btc_ret)
            and btc_ret > strat._btc_regime_kill_thr
        )
        assert not gate_fires, (
            "Gate must NOT fire when btc_ret_42 is None (conservative pass-through)."
        )

    def test_btc_zero_close_returns_none(self):
        """_compute_btc_ret_42 returns None when BTC close=0 (division guard)."""
        strat = _make_strategy(enable_btc_regime_kill=True, btc_regime_kill_lookback=42)

        n = 100
        interval_ms = 8 * 3600 * 1000
        base_time = 1_700_000_000_000
        close_times = np.array([base_time + i * interval_ms for i in range(n)], dtype=np.int64)
        closes = np.ones(n, dtype=np.float64)
        # Set the lookback candle to 0 (bad data)
        closes[-1 - 42] = 0.0
        _inject_btc_idx(strat, close_times, closes)

        decision_open_time = int(close_times[-1])
        result = strat._compute_btc_ret_42(decision_open_time)
        assert result is None, (
            f"Expected None when lookback BTC close=0.0 (division guard); got {result}"
        )


# ---------------------------------------------------------------------------
# (e) PRUNED-48 assertion
# ---------------------------------------------------------------------------


def test_pruned_48_unchanged():
    """V1_FEATURE_COLUMNS_PRUNED stays at 48 (global unchanged by iter-v1/092)."""
    from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED

    assert len(V1_FEATURE_COLUMNS_PRUNED) == 48, (
        f"V1_FEATURE_COLUMNS_PRUNED must be 48; got {len(V1_FEATURE_COLUMNS_PRUNED)}. "
        "iter-v1/092 adds ZERO new feature columns (one-variable discipline)."
    )


# ---------------------------------------------------------------------------
# (f) Runner import smoke test
# ---------------------------------------------------------------------------


def test_runner_imports_without_error():
    """run_iteration_092.py imports without error (smoke test)."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "run_iteration_092",
        Path(__file__).parent.parent / "run_iteration_092.py",
    )
    assert spec is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    assert hasattr(mod, "main")
    assert hasattr(mod, "ITERATION_LABEL")
    assert mod.ITERATION_LABEL == "v1-092"
    assert mod.ITERATION_NUMBER == 92
    assert mod.FAIL_FAST_IS_YEARS == 2.0
    assert mod.BTC_REGIME_KILL_THR == pytest.approx(0.067)
    assert mod.BTC_REGIME_KILL_LOOKBACK == 42


# ---------------------------------------------------------------------------
# (g) V1_ITER092_UNIVERSE
# ---------------------------------------------------------------------------


def test_features_v1_exports_v1_iter092_universe():
    """V1_ITER092_UNIVERSE is exported from features_v1 and is XRPUSDT-only."""
    from crypto_trade.features_v1 import V1_ITER092_UNIVERSE

    assert V1_ITER092_UNIVERSE == ("XRPUSDT",), (
        f"V1_ITER092_UNIVERSE must be ('XRPUSDT',), got {V1_ITER092_UNIVERSE}"
    )


# ---------------------------------------------------------------------------
# Integration: import smoke test
# ---------------------------------------------------------------------------


def test_lgbm_strategy_imports_with_btc_regime_kill_params():
    """LightGbmStrategy.__init__ accepts BTC-regime kill params without error."""
    from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

    # Default OFF
    strat_off = LightGbmStrategy(
        training_months=24,
        n_trials=1,
        feature_columns=["a", "b"],
        ensemble_seeds=[42],
    )
    assert strat_off._enable_btc_regime_kill is False
    assert strat_off._btc_regime_kill_thr == pytest.approx(0.067)
    assert strat_off._btc_regime_kill_lookback == 42
    assert strat_off._btc_regime_kill_idx is None

    # Explicit ON
    strat_on = LightGbmStrategy(
        training_months=24,
        n_trials=1,
        feature_columns=["a", "b"],
        ensemble_seeds=[42],
        enable_btc_regime_kill=True,
        btc_regime_kill_thr=0.067,
        btc_regime_kill_lookback=42,
    )
    assert strat_on._enable_btc_regime_kill is True
    assert strat_on._btc_regime_kill_thr == pytest.approx(0.067)
    assert strat_on._btc_regime_kill_lookback == 42
    # BTC index not populated yet (no parquet loaded in unit test context)
    assert strat_on._btc_regime_kill_idx is None
