"""Look-ahead safety regression tests for the iter-v1/032 SHORT-HORIZON MEAN-REVERSION edge.

The reversion override replaces the EXECUTED entry direction with a deterministic,
PAST-ONLY z-score FADE sign:

    price_z[t-1] = (close[t-1] - SMA_W(close)[t-1]) / std_W(close)[t-1]
    dir          = -sign(price_z[t-1])     # short the up-stretch, long the down-stretch

computed PAST-ONLY (only candles whose close_time < open_time(t)). SMA_W / std_W are
the simple mean / SAMPLE std (ddof=1, matching pandas rolling(W).std()) of the W closes
ENDING at t-1 (closes of candles t-W .. t-1). A look-ahead bug here would invalidate the
whole iteration — the direction (or the trigger magnitude) would peek at the decision
candle's own (or a future) close. These tests are the safety net.

The vol-regime gate also reads a past-only ``natr[t-1]`` (the parquet natr column
`.shift(1)`-lagged) keyed on open_time, plus a past-only per-month q40 threshold built
ONLY from training-window rows. The gate's CONSERVATIVE behavior is ABSTAIN (skip) when
the value is undefined — the OPPOSITE of the trend-strength gate's conservative-FIRE.

What is protected:

1. ``_compute_reversion_state(open_time)`` direction equals ``-sign`` of the manually
   computed past-only z (closes of candles t-W .. t-1).
2. APPENDING future candles (close_time >= open_time) does NOT change the value — the
   decisive look-ahead property.
3. The decision candle's OWN close (close_time = open_time + 8h - 1ms) is NEVER used —
   mutating it does not change the result.
4. close[t-1] (the candle that closes 1ms before open_time) IS the live input — nudging
   it across the z=0 boundary flips the direction and moves the z.
5. Warmup (< W closes before the decision candle) → None.
6. Default-off (enable_reversion_dir=False) → no reversion index built / direction path
   unchanged (byte-identity for all existing iterations).
7. (Gate) the natr index built by the EXACT `.shift(1)` construction is past-only; the
   per-month threshold uses ONLY training-window rows; appending future candles does not
   change the gate's natr[t-1].

The tests bypass the parquet load by setting ``_reversion_close_idx`` /
``_reversion_natr_idx`` directly to synthetic sorted indices — exactly the structures
``compute_features()`` builds.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

# 8h candle geometry (matches the real parquets):
#   open_time[i]  = START_MS + i * INTERVAL_MS
#   close_time[i] = open_time[i] + INTERVAL_MS - 1   (Binance: 1ms before next open)
INTERVAL_MS = 8 * 60 * 60 * 1000  # 28_800_000
START_MS = 1_577_836_800_000  # 2020-01-01 00:00:00 UTC
Z_W = 10  # reversion z window (iter-v1/032 default)


def _make_strategy(window: int = Z_W) -> LightGbmStrategy:
    """Minimal valid LightGbmStrategy with the reversion direction override enabled.

    We do NOT call compute_features() (no parquet) — the tests set
    ``_reversion_close_idx`` directly, mirroring exactly what compute_features builds.
    """
    return LightGbmStrategy(
        feature_columns=["mom_rsi_9"],  # any non-empty list (constructor requires it)
        ensemble_seeds=[42],
        enable_reversion_dir=True,
        reversion_z_window=window,
        trend_state_symbol="ETHUSDT",  # reversion reuses the trend_state_symbol parquet path
        verbose=0,
    )


def _make_gate_strategy(
    window: int = Z_W, z_threshold: float = 1.5, natr_q: float = 0.40
) -> LightGbmStrategy:
    """LightGbmStrategy with BOTH the reversion direction AND the vol-regime gate enabled."""
    return LightGbmStrategy(
        feature_columns=["mom_rsi_9"],
        ensemble_seeds=[42],
        enable_reversion_dir=True,
        reversion_z_window=window,
        enable_reversion_trigger_gate=True,
        reversion_z_threshold=z_threshold,
        reversion_natr_quantile=natr_q,
        reversion_natr_col="vol_natr_14",
        trend_state_symbol="ETHUSDT",
        verbose=0,
    )


def _build_close_index(closes: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Build the sorted (close_time_ms, close) index for `len(closes)` 8h candles."""
    n = len(closes)
    open_times = START_MS + np.arange(n, dtype=np.int64) * INTERVAL_MS
    close_times = open_times + INTERVAL_MS - 1  # Binance: close = next_open - 1ms
    return close_times.astype(np.int64), closes.astype(np.float64)


def _manual_reversion_z(closes: np.ndarray, t_idx: int, window: int) -> float | None:
    """Reference: (close[t-1] - mean(window)) / std(window, ddof=1) over closes t-W .. t-1.

    `t_idx` is the index of the DECISION candle. Uses ONLY closes strictly before
    `t_idx` (indices t_idx-window .. t_idx-1). Returns None on warmup / degenerate std.
    """
    lo = t_idx - window
    if lo < 0:
        return None
    window_closes = closes[lo:t_idx]  # indices t-window .. t-1 (PAST-ONLY)
    close_prev = closes[t_idx - 1]
    sma_prev = float(np.mean(window_closes))
    std_prev = float(np.std(window_closes, ddof=1))
    if std_prev <= 0.0:
        return None
    return (close_prev - sma_prev) / std_prev


def _manual_reversion_dir(closes: np.ndarray, t_idx: int, window: int) -> int | None:
    z = _manual_reversion_z(closes, t_idx, window)
    if z is None:
        return None
    return -1 if z > 0.0 else 1


class TestReversionStatePastOnly:
    def test_matches_manual_zscore_uptrend(self):
        """A clean rising series → close[t-1] above its trailing mean → z>0 → fade SHORT (-1)."""
        n = 60
        closes = np.linspace(100.0, 200.0, n)  # strictly increasing
        ct, cl = _build_close_index(closes)
        strat = _make_strategy()
        strat._reversion_close_idx = (ct, cl)

        t_idx = 50  # >= window so not warmup
        open_time = int(START_MS + t_idx * INTERVAL_MS)
        got_dir = strat._compute_reversion_state(open_time)
        got_z = strat._reversion_price_z(open_time)
        exp_z = _manual_reversion_z(closes, t_idx, Z_W)
        exp_dir = _manual_reversion_dir(closes, t_idx, Z_W)
        assert exp_z is not None and exp_z > 0  # overextended UP
        assert exp_dir == -1  # FADE → short
        assert got_dir == exp_dir
        assert got_z == pytest.approx(exp_z)
        # The override is the FADE sign — opposite the trend (which would be +1 here).
        assert got_dir == -int(np.sign(exp_z))

    def test_matches_manual_zscore_downtrend(self):
        """A clean falling series → close[t-1] below its trailing mean → z<0 → fade LONG (+1)."""
        n = 60
        closes = np.linspace(200.0, 100.0, n)  # strictly decreasing
        ct, cl = _build_close_index(closes)
        strat = _make_strategy()
        strat._reversion_close_idx = (ct, cl)

        t_idx = 50
        open_time = int(START_MS + t_idx * INTERVAL_MS)
        got_dir = strat._compute_reversion_state(open_time)
        got_z = strat._reversion_price_z(open_time)
        exp_z = _manual_reversion_z(closes, t_idx, Z_W)
        assert exp_z is not None and exp_z < 0  # overextended DOWN
        assert got_dir == 1  # FADE → long
        assert got_z == pytest.approx(exp_z)
        assert got_dir == -int(np.sign(exp_z))

    def test_matches_manual_across_a_path(self):
        """Noisy path → dir == -sign(manual z) at every non-warmup candle."""
        rng = np.random.default_rng(13)
        n = 200
        base = np.concatenate([np.linspace(200, 100, n // 2), np.linspace(100, 220, n - n // 2)])
        closes = base + rng.normal(0, 1.5, n)
        closes = np.maximum(closes, 1.0)
        ct, cl = _build_close_index(closes)
        strat = _make_strategy()
        strat._reversion_close_idx = (ct, cl)

        for t_idx in range(Z_W, n):
            open_time = int(START_MS + t_idx * INTERVAL_MS)
            got = strat._compute_reversion_state(open_time)
            expected = _manual_reversion_dir(closes, t_idx, Z_W)
            assert got == expected, f"mismatch at t_idx={t_idx}: got {got} expected {expected}"

    def test_appending_future_candles_does_not_change_value(self):
        """THE look-ahead test: extending the series with FUTURE candles (close_time
        >= decision open_time) must not change the reversion dir/z at the decision candle."""
        n = 60
        rng = np.random.default_rng(11)
        closes = 150.0 + np.cumsum(rng.normal(0, 2.0, n))
        closes = np.maximum(closes, 1.0)
        ct, cl = _build_close_index(closes)
        strat = _make_strategy()
        strat._reversion_close_idx = (ct, cl)

        t_idx = 45
        open_time = int(START_MS + t_idx * INTERVAL_MS)
        before_dir = strat._compute_reversion_state(open_time)
        before_z = strat._reversion_price_z(open_time)

        # Append 50 future candles with WILDLY different closes (crash then moonshot).
        future_closes = np.concatenate([np.full(25, 1.0), np.full(25, 10_000.0)])
        all_closes = np.concatenate([closes, future_closes])
        ct2, cl2 = _build_close_index(all_closes)
        strat._reversion_close_idx = (ct2, cl2)
        after_dir = strat._compute_reversion_state(open_time)
        after_z = strat._reversion_price_z(open_time)

        assert before_dir == after_dir, (
            f"LOOK-AHEAD LEAK: reversion dir at open_time changed from {before_dir} to "
            f"{after_dir} after appending future candles."
        )
        assert before_z == pytest.approx(after_z), (
            f"LOOK-AHEAD LEAK: reversion z changed from {before_z} to {after_z}."
        )

    def test_decision_candle_own_bar_never_used(self):
        """The decision candle's OWN close must be excluded. Mutating ONLY the decision
        candle's close must not change the dir/z (every primitive is shift(1)-lagged)."""
        n = 60
        closes = np.linspace(100.0, 200.0, n)
        ct, cl = _build_close_index(closes)
        strat = _make_strategy()
        strat._reversion_close_idx = (ct.copy(), cl.copy())

        t_idx = 50
        open_time = int(START_MS + t_idx * INTERVAL_MS)
        before_dir = strat._compute_reversion_state(open_time)
        before_z = strat._reversion_price_z(open_time)

        cl_mut = cl.copy()
        cl_mut[t_idx] = 1e9  # slam the decision candle's OWN close
        strat._reversion_close_idx = (ct.copy(), cl_mut)
        after_dir = strat._compute_reversion_state(open_time)
        after_z = strat._reversion_price_z(open_time)
        assert before_dir == after_dir, (
            "LOOK-AHEAD LEAK: mutating the decision candle's own close changed the "
            "reversion direction — close[t] must never be read."
        )
        assert before_z == pytest.approx(after_z)

    def test_uses_exactly_close_t_minus_1(self):
        """close[t-1] IS used: nudging it across the z=0 boundary flips the fade sign and
        moves the z. Use a flat window so close[t-1] alone sets the sign."""
        n = 60
        t_idx = 50
        open_time = int(START_MS + t_idx * INTERVAL_MS)

        # Flat-ish window so the SMA ~ 100; close[t-1] above → z>0 → fade SHORT (-1).
        closes = np.full(n, 100.0)
        ct, cl = _build_close_index(closes)
        cl_up = cl.copy()
        cl_up[t_idx - 1] = 101.0  # close[t-1] above the window mean → z>0
        strat = _make_strategy()
        strat._reversion_close_idx = (ct.copy(), cl_up)
        z_up = strat._reversion_price_z(open_time)
        assert z_up is not None and z_up > 0
        assert strat._compute_reversion_state(open_time) == -1  # fade short

        cl_dn = cl.copy()
        cl_dn[t_idx - 1] = 99.0  # close[t-1] below the window mean → z<0
        strat._reversion_close_idx = (ct.copy(), cl_dn)
        z_dn = strat._reversion_price_z(open_time)
        assert z_dn is not None and z_dn < 0
        assert strat._compute_reversion_state(open_time) == 1  # fade long


class TestReversionStateWarmupAndGuards:
    def test_warmup_returns_none(self):
        """Fewer than `window` closes before the decision candle → None (fallback)."""
        n = 8  # < Z_W + 1
        closes = np.linspace(100.0, 200.0, n)
        ct, cl = _build_close_index(closes)
        strat = _make_strategy()
        strat._reversion_close_idx = (ct, cl)

        t_idx = 7
        open_time = int(START_MS + t_idx * INTERVAL_MS)
        assert strat._compute_reversion_state(open_time) is None
        assert strat._reversion_price_z(open_time) is None

    def test_exactly_window_history_is_not_warmup(self):
        """With exactly `window` past closes available, the value is defined (not None)."""
        n = Z_W + 5
        closes = np.linspace(100.0, 200.0, n)
        ct, cl = _build_close_index(closes)
        strat = _make_strategy()
        strat._reversion_close_idx = (ct, cl)

        # Earliest non-warmup decision candle: t_idx = window (idx_lo = (t-1) - W + 1 = 0).
        t_idx = Z_W
        open_time = int(START_MS + t_idx * INTERVAL_MS)
        got = strat._compute_reversion_state(open_time)
        assert got in (1, -1)
        assert got == _manual_reversion_dir(closes, t_idx, Z_W)

    def test_degenerate_std_returns_none(self):
        """A perfectly flat window → std==0 → z undefined → None (CONSERVATIVE)."""
        n = 60
        closes = np.full(n, 123.0)  # flat → std10 == 0 everywhere
        ct, cl = _build_close_index(closes)
        strat = _make_strategy()
        strat._reversion_close_idx = (ct, cl)
        t_idx = 50
        open_time = int(START_MS + t_idx * INTERVAL_MS)
        assert strat._reversion_price_z(open_time) is None
        assert strat._compute_reversion_state(open_time) is None

    def test_nan_or_nonpositive_close_returns_none(self):
        n = 60
        closes = np.linspace(100.0, 200.0, n)
        closes[45] = np.nan  # NaN inside the z window of t_idx=50
        ct, cl = _build_close_index(closes)
        strat = _make_strategy()
        strat._reversion_close_idx = (ct, cl)
        t_idx = 50
        open_time = int(START_MS + t_idx * INTERVAL_MS)
        assert strat._compute_reversion_state(open_time) is None

    def test_open_time_before_any_candle_returns_none(self):
        n = 60
        closes = np.linspace(100.0, 200.0, n)
        ct, cl = _build_close_index(closes)
        strat = _make_strategy()
        strat._reversion_close_idx = (ct, cl)
        assert strat._compute_reversion_state(int(START_MS - INTERVAL_MS)) is None

    def test_index_none_returns_none(self):
        """Override disabled / parquet not loaded → conservative None."""
        strat = _make_strategy()
        strat._reversion_close_idx = None
        assert strat._compute_reversion_state(int(START_MS + 50 * INTERVAL_MS)) is None
        assert strat._reversion_price_z(int(START_MS + 50 * INTERVAL_MS)) is None


def test_default_off_byte_identity():
    """Default construction (override OFF) builds NO reversion index and the direction
    path is unchanged → byte-identity for all existing iterations (iter-016→031, v2/v3)."""
    strat = LightGbmStrategy(
        feature_columns=["mom_rsi_9"],
        ensemble_seeds=[42],
        verbose=0,
    )
    assert strat._enable_reversion_dir is False
    assert strat._enable_reversion_trigger_gate is False
    assert strat._reversion_close_idx is None
    assert strat._reversion_natr_idx is None
    assert strat._reversion_natr_thr is None
    # The reversion methods return conservative None when the override is off.
    assert strat._compute_reversion_state(int(START_MS + 50 * INTERVAL_MS)) is None
    assert strat._reversion_price_z(int(START_MS + 50 * INTERVAL_MS)) is None
    assert strat._compute_reversion_natr(int(START_MS + 50 * INTERVAL_MS)) is None


# ---------------------------------------------------------------------------
# Vol-regime gate (natr[t-1]) look-ahead — the gate has its OWN open_time-keyed index.
# ---------------------------------------------------------------------------


def _build_natr_index(natr_per_candle: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Build the (open_time_ms, natr[t-1]) index EXACTLY as compute_features does:
    the parquet natr column is `.shift(1)`-lagged so row t holds natr[t-1]."""
    n = len(natr_per_candle)
    open_times = (START_MS + np.arange(n, dtype=np.int64) * INTERVAL_MS).astype(np.int64)
    natr_lagged = pd.Series(natr_per_candle.astype(np.float64)).shift(1).to_numpy()
    return open_times, natr_lagged.astype(np.float64)


class TestReversionVolGatePastOnly:
    def test_natr_index_is_shift1_past_only(self):
        """natr[t] in the index == the parquet natr at candle t-1 (the `.shift(1)`)."""
        natr_raw = np.linspace(1.0, 5.0, 40)
        ot, natr_idx = _build_natr_index(natr_raw)
        strat = _make_gate_strategy()
        strat._reversion_natr_idx = (ot, natr_idx)

        t_idx = 20
        open_time = int(ot[t_idx])
        got = strat._compute_reversion_natr(open_time)
        # Row t holds natr at candle t-1 (the raw value at index t-1).
        assert got == pytest.approx(natr_raw[t_idx - 1])

    def test_natr_appending_future_does_not_change_value(self):
        """Appending future candles (open_time > decision) must not change natr[t-1]."""
        natr_raw = np.linspace(1.0, 5.0, 40)
        ot, natr_idx = _build_natr_index(natr_raw)
        strat = _make_gate_strategy()
        strat._reversion_natr_idx = (ot, natr_idx)
        t_idx = 18
        open_time = int(ot[t_idx])
        before = strat._compute_reversion_natr(open_time)

        natr_raw2 = np.concatenate([natr_raw, np.full(20, 999.0)])
        ot2, natr_idx2 = _build_natr_index(natr_raw2)
        strat._reversion_natr_idx = (ot2, natr_idx2)
        after = strat._compute_reversion_natr(open_time)
        assert before == pytest.approx(after), (
            f"LOOK-AHEAD LEAK: gate natr[t-1] changed from {before} to {after}."
        )

    def test_natr_warmup_returns_none(self):
        """Row 0 has no prior candle → natr[t-1] is NaN → None (gate ABSTAINS)."""
        natr_raw = np.linspace(1.0, 5.0, 40)
        ot, natr_idx = _build_natr_index(natr_raw)
        strat = _make_gate_strategy()
        strat._reversion_natr_idx = (ot, natr_idx)
        assert strat._compute_reversion_natr(int(ot[0])) is None  # natr[-1] is NaN

    def test_per_month_threshold_is_training_window_only(self):
        """The per-month q40 natr threshold is computed ONLY from training-window rows;
        appending FUTURE (test-month) rows does not change it — past-only by construction."""
        # natr known so q40 is deterministic over a training window.
        n = 120
        natr_raw = np.linspace(1.0, 10.0, n)  # increasing
        ot, natr_idx = _build_natr_index(natr_raw)
        strat = _make_gate_strategy()
        strat._reversion_natr_idx = (ot, natr_idx)

        # Training window = first 100 candles' open_times; replicate the runner mask.
        train_start = int(ot[0])
        train_end = int(ot[100])  # exclusive
        tw_mask = (ot >= train_start) & (ot < train_end)
        tw = natr_idx[tw_mask]
        tw = tw[np.isfinite(tw)]
        assert len(tw) >= 50
        expected_thr = float(np.quantile(tw, 0.40))

        # Mutate FUTURE (>= train_end) rows to extreme values; the threshold must be
        # unchanged because it only reads training-window rows.
        natr_idx_mut = natr_idx.copy()
        natr_idx_mut[ot >= train_end] = 1e6
        tw_mut = natr_idx_mut[tw_mask]
        tw_mut = tw_mut[np.isfinite(tw_mut)]
        thr_mut = float(np.quantile(tw_mut, 0.40))
        assert thr_mut == pytest.approx(expected_thr), (
            "LOOK-AHEAD LEAK: per-month natr threshold changed when FUTURE rows were "
            "mutated — the training-window mask must exclude test-month rows."
        )

    def test_natr_index_none_returns_none(self):
        strat = _make_gate_strategy()
        strat._reversion_natr_idx = None
        assert strat._compute_reversion_natr(int(START_MS + 20 * INTERVAL_MS)) is None


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
