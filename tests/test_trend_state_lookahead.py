"""Look-ahead safety regression tests for the iter-v1/016 TREND-STATE direction override.

The override replaces the EXECUTED entry direction with a stateless 200-SMA
trend-state sign:

    trend_state(t) = +1 if close[t-1] > SMA_W(close)[t-1] else -1

computed PAST-ONLY (only candles whose close_time < open_time(t)). A look-ahead
bug here would invalidate the whole iteration — the direction would peek at the
decision candle's own (or a future) close. These tests are the safety net.

What is protected:

1. ``_compute_trend_state(open_time)`` equals the sign computed from a
   manually-sliced PAST-ONLY close series (closes of candles t-W .. t-1).
2. APPENDING future candles (close_time >= open_time) does NOT change the value
   — the decisive look-ahead property. If the lookup ever read the decision
   candle or a later one, this test fails.
3. Warmup (fewer than W closes before the decision candle) returns None.
4. The exact ``close_time < open_time`` boundary under the Binance 8h candle
   convention (close_time(t-1) = open_time(t) - 1ms): the candle that "closes at"
   the decision open is t-1 and IS used; the decision candle itself (close_time =
   open_time + 8h - 1ms) is NEVER used.

The tests bypass the parquet load by setting ``_trend_state_idx`` directly to a
synthetic sorted ``(close_time_ms, close)`` index — exactly the structure
``compute_features()`` builds.
"""

from __future__ import annotations

import numpy as np
import pytest

from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

# 8h candle geometry (matches the real parquets):
#   open_time[i]  = START_MS + i * INTERVAL_MS
#   close_time[i] = open_time[i] + INTERVAL_MS - 1   (Binance: 1ms before next open)
INTERVAL_MS = 8 * 60 * 60 * 1000  # 28_800_000
START_MS = 1_577_836_800_000  # 2020-01-01 00:00:00 UTC (matches BTCUSDT parquet origin)
SMA_W = 200


def _make_strategy(window: int = SMA_W) -> LightGbmStrategy:
    """Minimal valid LightGbmStrategy with the trend-state override enabled.

    We do NOT call compute_features() (no parquet) — the tests set
    ``_trend_state_idx`` directly, mirroring exactly what compute_features builds.
    """
    strat = LightGbmStrategy(
        feature_columns=["mom_rsi_9"],  # any non-empty list (constructor requires it)
        ensemble_seeds=[42],
        enable_trend_state_dir=True,
        trend_state_sma_window=window,
        trend_state_symbol="BTCUSDT",
        verbose=0,
    )
    return strat


def _build_index(closes: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Build the sorted (close_time_ms, close) index for `len(closes)` 8h candles."""
    n = len(closes)
    open_times = START_MS + np.arange(n, dtype=np.int64) * INTERVAL_MS
    close_times = open_times + INTERVAL_MS - 1  # Binance: close = next_open - 1ms
    return close_times.astype(np.int64), closes.astype(np.float64)


def _manual_trend_state(closes: np.ndarray, t_idx: int, window: int) -> int | None:
    """Reference implementation: sign(close[t-1] - mean(close[t-window .. t-1])).

    `t_idx` is the index of the DECISION candle. Uses ONLY closes strictly before
    `t_idx` (i.e. indices t_idx-window .. t_idx-1). Returns None on warmup.
    """
    lo = t_idx - window
    if lo < 0:
        return None
    window_closes = closes[lo:t_idx]  # indices t-window .. t-1 (PAST-ONLY)
    close_prev = closes[t_idx - 1]
    sma_prev = float(np.mean(window_closes))
    return 1 if close_prev > sma_prev else -1


class TestTrendStatePastOnly:
    def test_matches_manual_past_only_sign_uptrend(self):
        """A clean rising series → close[t-1] > SMA200[t-1] → +1, matching manual slice."""
        n = 260
        closes = np.linspace(100.0, 200.0, n)  # strictly increasing
        ct, cl = _build_index(closes)
        strat = _make_strategy()
        strat._trend_state_idx = (ct, cl)

        t_idx = 250  # decision candle index (>= window so not warmup)
        open_time = int(START_MS + t_idx * INTERVAL_MS)
        got = strat._compute_trend_state(open_time)
        expected = _manual_trend_state(closes, t_idx, SMA_W)
        assert expected == 1  # rising → last close above its trailing mean
        assert got == expected

    def test_matches_manual_past_only_sign_downtrend(self):
        """A clean falling series → close[t-1] < SMA200[t-1] → -1."""
        n = 260
        closes = np.linspace(200.0, 100.0, n)  # strictly decreasing
        ct, cl = _build_index(closes)
        strat = _make_strategy()
        strat._trend_state_idx = (ct, cl)

        t_idx = 250
        open_time = int(START_MS + t_idx * INTERVAL_MS)
        got = strat._compute_trend_state(open_time)
        expected = _manual_trend_state(closes, t_idx, SMA_W)
        assert expected == -1
        assert got == expected

    def test_matches_manual_across_a_cross(self):
        """Series that crosses its SMA → sign matches the manual slice at every candle."""
        rng = np.random.default_rng(7)
        n = 320
        # V-shaped path crossing the trailing SMA, plus mild noise.
        base = np.concatenate([np.linspace(200, 100, n // 2), np.linspace(100, 220, n - n // 2)])
        closes = base + rng.normal(0, 1.5, n)
        closes = np.maximum(closes, 1.0)  # keep positive
        ct, cl = _build_index(closes)
        strat = _make_strategy()
        strat._trend_state_idx = (ct, cl)

        for t_idx in range(SMA_W, n):
            open_time = int(START_MS + t_idx * INTERVAL_MS)
            got = strat._compute_trend_state(open_time)
            expected = _manual_trend_state(closes, t_idx, SMA_W)
            assert got == expected, f"mismatch at t_idx={t_idx}: got {got} expected {expected}"

    def test_appending_future_candles_does_not_change_value(self):
        """THE look-ahead test: extending the series with FUTURE candles (close_time
        >= decision open_time) must not change trend_state at the decision candle."""
        n = 260
        rng = np.random.default_rng(11)
        closes = 150.0 + np.cumsum(rng.normal(0, 2.0, n))
        closes = np.maximum(closes, 1.0)
        ct, cl = _build_index(closes)
        strat = _make_strategy()
        strat._trend_state_idx = (ct, cl)

        t_idx = 240
        open_time = int(START_MS + t_idx * INTERVAL_MS)
        before = strat._compute_trend_state(open_time)

        # Append 50 future candles with WILDLY different closes (e.g. a crash then
        # a spike). If the lookup peeked at any candle with close_time >= open_time,
        # `before` would change. close_time of candle t_idx is open_time + 8h - 1ms,
        # already > open_time, so the decision candle itself must also be excluded.
        future_closes = np.concatenate(
            [np.full(25, 1.0), np.full(25, 10_000.0)]  # crash then moonshot
        )
        all_closes = np.concatenate([closes, future_closes])
        ct2, cl2 = _build_index(all_closes)
        strat._trend_state_idx = (ct2, cl2)
        after = strat._compute_trend_state(open_time)

        assert before == after, (
            f"LOOK-AHEAD LEAK: trend_state at open_time changed from {before} to "
            f"{after} after appending future candles — the lookup peeked at "
            f"close_time >= open_time."
        )

    def test_decision_candle_own_close_never_used(self):
        """The decision candle's OWN close (close_time = open_time + 8h - 1ms) must be
        excluded. Mutating ONLY the decision candle's close must not change the result."""
        n = 260
        closes = np.linspace(100.0, 200.0, n)
        ct, cl = _build_index(closes)
        strat = _make_strategy()
        strat._trend_state_idx = (ct.copy(), cl.copy())

        t_idx = 250
        open_time = int(START_MS + t_idx * INTERVAL_MS)
        before = strat._compute_trend_state(open_time)

        # Slam the decision candle's own close to an extreme; trend_state must NOT move.
        cl_mut = cl.copy()
        cl_mut[t_idx] = 1e9
        strat._trend_state_idx = (ct.copy(), cl_mut)
        after = strat._compute_trend_state(open_time)
        assert before == after, (
            "LOOK-AHEAD LEAK: mutating the decision candle's own close changed "
            "trend_state — close[t] must never be read."
        )

    def test_uses_exactly_close_t_minus_1(self):
        """close[t-1] (the candle that closes 1ms before open_time) IS used. Mutating
        it across the SMA boundary flips the sign — confirming it is the live input."""
        n = 260
        closes = np.full(n, 100.0)  # flat → close[t-1] == SMA → sign on the > comparison
        ct, cl = _build_index(closes)
        t_idx = 250
        open_time = int(START_MS + t_idx * INTERVAL_MS)

        strat = _make_strategy()
        # close[t-1] strictly above the flat mean → +1
        cl_up = cl.copy()
        cl_up[t_idx - 1] = 100.5
        strat._trend_state_idx = (ct.copy(), cl_up)
        assert strat._compute_trend_state(open_time) == 1

        # close[t-1] below the mean → -1
        cl_dn = cl.copy()
        cl_dn[t_idx - 1] = 99.5
        strat._trend_state_idx = (ct.copy(), cl_dn)
        assert strat._compute_trend_state(open_time) == -1


class TestTrendStateWarmupAndGuards:
    def test_warmup_returns_none(self):
        """Fewer than `window` closes before the decision candle → None (fallback)."""
        n = 150  # < SMA_W + 1
        closes = np.linspace(100.0, 200.0, n)
        ct, cl = _build_index(closes)
        strat = _make_strategy()
        strat._trend_state_idx = (ct, cl)

        t_idx = 149
        open_time = int(START_MS + t_idx * INTERVAL_MS)
        assert strat._compute_trend_state(open_time) is None

    def test_exactly_window_history_is_not_warmup(self):
        """With exactly `window` past closes available, the value is defined (not None)."""
        n = SMA_W + 5
        closes = np.linspace(100.0, 200.0, n)
        ct, cl = _build_index(closes)
        strat = _make_strategy()
        strat._trend_state_idx = (ct, cl)

        # The earliest non-warmup decision candle: idx_curr = t-1 must have idx_lo >= 0,
        # i.e. (t-1) - window + 1 >= 0  ->  t >= window. Use t_idx = window.
        t_idx = SMA_W
        open_time = int(START_MS + t_idx * INTERVAL_MS)
        got = strat._compute_trend_state(open_time)
        assert got in (1, -1)
        assert got == _manual_trend_state(closes, t_idx, SMA_W)

    def test_open_time_before_any_candle_returns_none(self):
        n = 260
        closes = np.linspace(100.0, 200.0, n)
        ct, cl = _build_index(closes)
        strat = _make_strategy()
        strat._trend_state_idx = (ct, cl)
        # An open_time before the very first candle's close → idx_curr < 0 → None.
        assert strat._compute_trend_state(int(START_MS - INTERVAL_MS)) is None

    def test_index_none_returns_none(self):
        """Override disabled / parquet not loaded → conservative None."""
        strat = _make_strategy()
        strat._trend_state_idx = None
        assert strat._compute_trend_state(int(START_MS + 250 * INTERVAL_MS)) is None

    def test_nan_or_nonpositive_close_returns_none(self):
        n = 260
        closes = np.linspace(100.0, 200.0, n)
        closes[245] = np.nan  # NaN inside the SMA window of t_idx=250
        ct, cl = _build_index(closes)
        strat = _make_strategy()
        strat._trend_state_idx = (ct, cl)
        t_idx = 250
        open_time = int(START_MS + t_idx * INTERVAL_MS)
        assert strat._compute_trend_state(open_time) is None


def test_disabled_by_default_no_index_built():
    """Default construction (override OFF) leaves the index None and returns None."""
    strat = LightGbmStrategy(
        feature_columns=["mom_rsi_9"],
        ensemble_seeds=[42],
        verbose=0,
    )
    assert strat._enable_trend_state_dir is False
    assert strat._trend_state_idx is None
    assert strat._compute_trend_state(int(START_MS + 250 * INTERVAL_MS)) is None


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
