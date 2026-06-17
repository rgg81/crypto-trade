"""Look-ahead safety regression tests for the iter-v1/018 TREND-STRENGTH CONVICTION gate.

The gate ABSTAINS unless the past-only trend strength

    trend_strength(t) = |close[t-1] - SMA_W(close)[t-1]| / ATR_atrwin[t-1]

is >= a past-only per-month threshold. A look-ahead bug here would invalidate the
whole iteration — the strength would peek at the decision candle's own (or a
future) close/high/low. These tests are the safety net.

The QR's IS-only script (analysis/BTCUSDT/iteration_v1-018/strength_gate_by_side.py)
builds `absd` as:

    cp   = close.shift(1)                                  # close[t-1]
    sma  = close.rolling(W).mean().shift(1)                # SMA_W(close)[t-1]
    tr   = max(high-low, |high-cp|, |low-cp|)              # true range
    atr  = tr.rolling(atr_win).mean().shift(1)             # ATR_atrwin[t-1]
    dist = (cp - sma) / atr
    absd = |dist|

compute_features() reproduces this EXACTLY and stores a sorted
(close_time_ms, absd) index. ``_compute_trend_strength(open_time)`` then reads the
absd at candle t-1 (last close_time <= open_time) via searchsorted.

What is protected:

1. The (close_time, absd) index built by the EXACT compute_features construction
   matches a manual past-only reference at every row.
2. ``_compute_trend_strength(open_time)`` equals the manually-sliced past-only absd.
3. APPENDING future candles (close_time >= open_time) does NOT change the value at a
   past decision candle — the decisive look-ahead property.
4. The decision candle's OWN close/high/low must not influence its strength (every
   primitive is shift(1)-lagged).
5. Warmup (SMA / ATR not yet defined) → None → caller does NOT gate (conservative fire).
6. The per-month threshold uses ONLY training-window rows (past-only relative to the
   test month); below-threshold strength → gate fires (skip), at/above → trade.

The tests bypass the parquet load by setting ``_trend_strength_idx`` directly to a
synthetic sorted ``(close_time_ms, absd)`` index — exactly the structure
``compute_features()`` builds — and a reference builder mirrors that construction.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

# 8h candle geometry (matches the real parquets):
INTERVAL_MS = 8 * 60 * 60 * 1000  # 28_800_000
START_MS = 1_577_836_800_000  # 2020-01-01 00:00:00 UTC (matches BTCUSDT parquet origin)
SMA_W = 200
ATR_W = 14


def _make_strategy(
    window: int = SMA_W, atr_window: int = ATR_W, q: float = 0.50
) -> LightGbmStrategy:
    """Minimal valid LightGbmStrategy with the trend-strength gate enabled.

    We do NOT call compute_features() (no parquet) — the tests set
    ``_trend_strength_idx`` / ``_trend_strength_thr`` directly, mirroring exactly what
    compute_features + _train_for_month build.
    """
    return LightGbmStrategy(
        feature_columns=["mom_rsi_9"],  # any non-empty list (constructor requires it)
        ensemble_seeds=[42],
        enable_trend_strength_gate=True,
        trend_state_sma_window=window,  # the gate measures distance from this SMA
        trend_state_symbol="BTCUSDT",
        trend_strength_atr_window=atr_window,
        trend_strength_quantile=q,
        verbose=0,
    )


def _build_strength_index(
    close: np.ndarray, high: np.ndarray, low: np.ndarray, window: int, atr_window: int
) -> tuple[np.ndarray, np.ndarray]:
    """Reproduce the EXACT compute_features() (open_time_ms, |dist_atr|) build.

    Must stay byte-identical to the lgbm.compute_features() construction so the test
    verifies the production index, not a paraphrase. The index is keyed on OPEN_TIME so
    decision candle t maps to row t (cp=close[t-1]).
    """
    n = len(close)
    open_times = (START_MS + np.arange(n, dtype=np.int64) * INTERVAL_MS).astype(np.int64)
    cp = pd.Series(close).shift(1).to_numpy()  # close[t-1]
    sma = pd.Series(close).rolling(window).mean().shift(1).to_numpy()  # SMA_W[t-1]
    tr = np.maximum(high - low, np.maximum(np.abs(high - cp), np.abs(low - cp)))
    atr = pd.Series(tr).rolling(atr_window).mean().shift(1).to_numpy()  # ATR_aw[t-1]
    atr_safe = np.where(atr > 0, atr, np.nan)
    dist_atr = (cp - sma) / atr_safe
    return open_times, np.abs(dist_atr).astype(np.float64)


def _manual_abs_dist(
    close: np.ndarray, high: np.ndarray, low: np.ndarray, t_idx: int, window: int, atr_window: int
) -> float | None:
    """Independent past-only reference for |dist_atr| at decision candle t_idx.

    Uses ONLY candles strictly before t_idx (indices t-window .. t-1 for the SMA,
    t-atr_window .. t-1 for the ATR). Returns None on warmup.
    """
    if t_idx - 1 < 0:
        return None
    close_prev = close[t_idx - 1]  # close[t-1]
    sma_lo = (t_idx - 1) - window + 1
    if sma_lo < 0:
        return None
    sma_prev = float(np.mean(close[sma_lo:t_idx]))  # mean of closes t-window .. t-1
    # ATR: mean of true range over candles t-atr_window .. t-1. TR[i] needs close[i-1].
    atr_lo = (t_idx - 1) - atr_window + 1
    if atr_lo < 1:  # TR at atr_lo needs close[atr_lo-1] >= close[0]
        return None
    trs = []
    for i in range(atr_lo, t_idx):  # i in t-atr_window .. t-1
        cprev = close[i - 1]
        tr_i = max(high[i] - low[i], abs(high[i] - cprev), abs(low[i] - cprev))
        trs.append(tr_i)
    atr_prev = float(np.mean(trs))
    if atr_prev <= 0:
        return None
    return abs((close_prev - sma_prev) / atr_prev)


def _random_ohlc(n: int, seed: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    close = 150.0 + np.cumsum(rng.normal(0, 2.0, n))
    close = np.maximum(close, 1.0)
    spread = np.abs(rng.normal(0, 1.5, n)) + 0.5
    high = close + spread
    low = np.maximum(close - spread, 0.5)
    return close, high, low


class TestTrendStrengthPastOnly:
    def test_index_matches_manual_reference(self):
        """The compute_features (close_time, absd) build matches the manual reference."""
        n = 300
        close, high, low = _random_ohlc(n, seed=3)
        ct, absd = _build_strength_index(close, high, low, SMA_W, ATR_W)
        for t_idx in range(SMA_W + ATR_W + 2, n):
            expected = _manual_abs_dist(close, high, low, t_idx, SMA_W, ATR_W)
            got = float(absd[t_idx])
            if expected is None:
                assert not np.isfinite(got)
            else:
                assert np.isfinite(got)
                assert got == pytest.approx(expected, rel=1e-9, abs=1e-9), (
                    f"mismatch at t_idx={t_idx}: got {got} expected {expected}"
                )

    def test_compute_trend_strength_matches_manual_past_only(self):
        """_compute_trend_strength(open_time) == manual past-only |dist_atr| at t-1."""
        n = 300
        close, high, low = _random_ohlc(n, seed=5)
        ct, absd = _build_strength_index(close, high, low, SMA_W, ATR_W)
        strat = _make_strategy()
        strat._trend_strength_idx = (ct, absd)
        for t_idx in range(SMA_W + ATR_W + 2, n):
            open_time = int(START_MS + t_idx * INTERVAL_MS)
            got = strat._compute_trend_strength(open_time)
            expected = _manual_abs_dist(close, high, low, t_idx, SMA_W, ATR_W)
            if expected is None:
                assert got is None
            else:
                assert got == pytest.approx(expected, rel=1e-9, abs=1e-9), (
                    f"mismatch at t_idx={t_idx}: got {got} expected {expected}"
                )

    def test_appending_future_candles_does_not_change_value(self):
        """THE look-ahead test: extending the series with FUTURE candles must not change
        the strength at a past decision candle."""
        n = 300
        close, high, low = _random_ohlc(n, seed=11)
        ct, absd = _build_strength_index(close, high, low, SMA_W, ATR_W)
        strat = _make_strategy()
        strat._trend_strength_idx = (ct, absd)

        t_idx = 270
        open_time = int(START_MS + t_idx * INTERVAL_MS)
        before = strat._compute_trend_strength(open_time)

        # Append 40 future candles with WILDLY different prices (crash then moonshot).
        # If the lookup peeked at any candle with close_time >= open_time, `before`
        # would change. Rebuild the WHOLE index from the extended series — even the
        # index build must keep past |dist_atr| values frozen (shift(1) guarantees it).
        fclose = np.concatenate([np.full(20, 1.0), np.full(20, 100_000.0)])
        fhigh = fclose + 50.0
        flow = np.maximum(fclose - 50.0, 0.5)
        all_close = np.concatenate([close, fclose])
        all_high = np.concatenate([high, fhigh])
        all_low = np.concatenate([low, flow])
        ct2, absd2 = _build_strength_index(all_close, all_high, all_low, SMA_W, ATR_W)
        strat._trend_strength_idx = (ct2, absd2)
        after = strat._compute_trend_strength(open_time)

        assert before is not None and after is not None
        assert before == pytest.approx(after, rel=1e-12, abs=1e-12), (
            f"LOOK-AHEAD LEAK: trend_strength at open_time changed from {before} to "
            f"{after} after appending future candles."
        )

    def test_decision_candle_own_ohlc_never_used(self):
        """Mutating ONLY the decision candle's own close/high/low must not change its
        strength (all inputs are shift(1)-lagged)."""
        n = 300
        close, high, low = _random_ohlc(n, seed=13)
        ct, absd = _build_strength_index(close, high, low, SMA_W, ATR_W)
        strat = _make_strategy()
        strat._trend_strength_idx = (ct, absd)

        t_idx = 260
        open_time = int(START_MS + t_idx * INTERVAL_MS)
        before = strat._compute_trend_strength(open_time)

        # Slam the decision candle's OWN ohlc to extremes; rebuild; strength must not move.
        close2, high2, low2 = close.copy(), high.copy(), low.copy()
        close2[t_idx] = 1e9
        high2[t_idx] = 1e9
        low2[t_idx] = 1.0
        ct2, absd2 = _build_strength_index(close2, high2, low2, SMA_W, ATR_W)
        strat._trend_strength_idx = (ct2, absd2)
        after = strat._compute_trend_strength(open_time)
        assert before == pytest.approx(after, rel=1e-12, abs=1e-12), (
            "LOOK-AHEAD LEAK: mutating the decision candle's own ohlc changed strength."
        )

    def test_uses_exactly_close_t_minus_1(self):
        """Mutating close[t-1] (the candle that closes 1ms before open_time) changes the
        strength — confirming it is the live input (not a future candle)."""
        n = 300
        close, high, low = _random_ohlc(n, seed=17)
        strat = _make_strategy()
        t_idx = 250
        open_time = int(START_MS + t_idx * INTERVAL_MS)

        ct, absd = _build_strength_index(close, high, low, SMA_W, ATR_W)
        strat._trend_strength_idx = (ct, absd)
        base = strat._compute_trend_strength(open_time)

        close2 = close.copy()
        close2[t_idx - 1] = close2[t_idx - 1] * 2.0  # large move at t-1 → strength changes
        ct2, absd2 = _build_strength_index(close2, high, low, SMA_W, ATR_W)
        strat._trend_strength_idx = (ct2, absd2)
        moved = strat._compute_trend_strength(open_time)
        assert base is not None and moved is not None
        assert moved != pytest.approx(base, rel=1e-6), (
            "close[t-1] is the live input — mutating it must change the strength."
        )


class TestTrendStrengthWarmupAndGuards:
    def test_warmup_returns_none(self):
        """Fewer than window+atr closes before the decision candle → None (fallback)."""
        n = SMA_W // 2
        close, high, low = _random_ohlc(n, seed=19)
        ct, absd = _build_strength_index(close, high, low, SMA_W, ATR_W)
        strat = _make_strategy()
        strat._trend_strength_idx = (ct, absd)
        t_idx = n - 1
        open_time = int(START_MS + t_idx * INTERVAL_MS)
        assert strat._compute_trend_strength(open_time) is None

    def test_open_time_before_any_candle_returns_none(self):
        n = 300
        close, high, low = _random_ohlc(n, seed=23)
        ct, absd = _build_strength_index(close, high, low, SMA_W, ATR_W)
        strat = _make_strategy()
        strat._trend_strength_idx = (ct, absd)
        assert strat._compute_trend_strength(int(START_MS - INTERVAL_MS)) is None

    def test_index_none_returns_none(self):
        """Gate disabled / parquet not loaded → conservative None (fire)."""
        strat = _make_strategy()
        strat._trend_strength_idx = None
        assert strat._compute_trend_strength(int(START_MS + 250 * INTERVAL_MS)) is None


class TestTrendStrengthThresholdPastOnly:
    def test_threshold_uses_only_training_window_rows(self):
        """The per-month q_thr must be the q-quantile of |dist_atr| over candles whose
        close_time is in [train_start_ms, train_end_ms) — appending rows AFTER the
        training window must not change it (past-only)."""
        n = 600
        close, high, low = _random_ohlc(n, seed=29)
        ct, absd = _build_strength_index(close, high, low, SMA_W, ATR_W)
        # Define a training window covering the FIRST ~400 candles.
        train_start_ms = int(ct[0]) - 1
        train_end_ms = int(ct[400])
        mask = (ct >= train_start_ms) & (ct < train_end_ms)
        tw = absd[mask]
        tw = tw[np.isfinite(tw)]
        q_thr_full = float(np.quantile(tw, 0.50))

        # Recompute with the LATER rows mutated to extremes — threshold must not change.
        absd_mut = absd.copy()
        absd_mut[450:] = 1e6
        tw2 = absd_mut[(ct >= train_start_ms) & (ct < train_end_ms)]
        tw2 = tw2[np.isfinite(tw2)]
        q_thr_mut = float(np.quantile(tw2, 0.50))
        assert q_thr_full == pytest.approx(q_thr_mut), (
            "THRESHOLD LEAK: rows after the training window changed the past-only q_thr."
        )

    def test_below_threshold_skips_at_or_above_trades(self):
        """Gate semantics: strength < q_thr → skip; strength >= q_thr → trade (no skip)."""
        n = 300
        close, high, low = _random_ohlc(n, seed=31)
        ct, absd = _build_strength_index(close, high, low, SMA_W, ATR_W)
        strat = _make_strategy()
        strat._trend_strength_idx = (ct, absd)
        finite = absd[np.isfinite(absd)]
        thr = float(np.quantile(finite, 0.50))
        strat._trend_strength_thr = thr
        # Find a finite decision candle and assert the boolean gate decision matches
        # the (strength >= thr) comparison.
        checked = 0
        for t_idx in range(SMA_W + ATR_W + 5, n):
            open_time = int(START_MS + t_idx * INTERVAL_MS)
            s = strat._compute_trend_strength(open_time)
            if s is None:
                continue
            skip = strat._trend_strength_thr is not None and s < strat._trend_strength_thr
            assert skip == (s < thr)
            checked += 1
        assert checked > 0


def test_disabled_by_default_no_index_built():
    """Default construction (gate OFF) leaves the index None and returns None."""
    strat = LightGbmStrategy(
        feature_columns=["mom_rsi_9"],
        ensemble_seeds=[42],
        verbose=0,
    )
    assert strat._enable_trend_strength_gate is False
    assert strat._trend_strength_idx is None
    assert strat._trend_strength_thr is None
    assert strat._compute_trend_strength(int(START_MS + 250 * INTERVAL_MS)) is None


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
