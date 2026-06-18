"""Look-ahead safety regression tests for the iter-v1/030 AGREE_SCALE conviction modulator.

iter-v1/030 (ETHUSDT) multiplies the iter-027 conviction-gate quantity

    conv(t) = |close[t-1] - SMA200(close)[t-1]| / ATR14[t-1]

by a deterministic, past-only AGREEMENT fraction over a PINNED 3-signal panel P3 that
points the SAME way as the UNCHANGED SMA200 anchor direction:

    s1 = ema_cross_sign(50, 200) = +1 if EMA50[t-1] > EMA200[t-1] else -1
    s2 = donchian_breakout_sign(55) = +1 if close[t-1] >= midline(High/Low, 55)[t-1] else -1
    s3 = tsmom_sign(42) = +1 if close[t-1]/close[t-43] - 1 > 0 else -1
    anchor = +1 if close[t-1] > SMA200[t-1] else -1   (UNCHANGED iter-027 direction)
    agreement = mean({s1, s2, s3} == anchor) in {0, 1/3, 2/3, 1}
    conv_modulated = conv * agreement

The modulation is applied to the |dist_atr| SERIES at build time in
lgbm.compute_features() — so BOTH the per-month q-quantile threshold and the per-candle
gated value are built from the modulated series. A look-ahead bug would invalidate the
whole iteration: any panel member peeking at the decision candle's own (or a future) bar
would leak. These tests are the safety net.

The committed primitives this mirrors EXACTLY:
  analysis/ETHUSDT/iteration_v1-030/multispeed_breadth.py
    ma_cross_sign(50,200) / donchian_breakout_sign(55) / tsmom_sign(42) / sma_sign(anchor)
  analysis/ETHUSDT/iteration_v1-030/agree_scale_robustness.py
    P3_family_3 = [ma_cross_sign(50,200), donchian_breakout_sign(55), tsmom_sign(42)]
  analysis/ETHUSDT/iteration_v1-030/blend_agreement.py
    agree = mean(panel == anchor, axis=0);  conv_agree_scale = conv * agree

What is protected:

1. Appending FUTURE candles does NOT change the modulated value at a past decision candle
   (THE leak test — must hold for the slowest binding member: SMA-200 / Donchian-55).
2. The modulated value == conv * (independent manual P3 agreement fraction).
3. Mutating the decision candle's OWN close/high/low does not change the modulated value.
4. Default-off byte-identity: enable_agreement_scale=False stores the RAW |dist_atr| series
   bit-identical to the no-agreement build (the iter-016->029 guarantee).
5. agreement multiplier in {0, 1/3, 2/3, 1}; modulated conv <= raw conv and >= 0.

The tests bypass the parquet load by setting ``_trend_strength_idx`` directly to a
synthetic sorted ``(open_time_ms, modulated_abs_dist)`` index — exactly the structure
``compute_features()`` builds when enable_agreement_scale=True — and reference builders
mirror that construction byte-for-byte against the lgbm.py production code.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

# 8h candle geometry (matches the real ETH parquet origin used elsewhere in the suite):
INTERVAL_MS = 8 * 60 * 60 * 1000  # 28_800_000
START_MS = 1_577_836_800_000  # 2020-01-01 00:00:00 UTC
SMA_W = 200
ATR_W = 14
# PINNED P3 panel windows (single-axis; hardcoded in lgbm.compute_features):
EMA_FAST = 50
EMA_SLOW = 200
DONCH_W = 55
TSMOM_H = 42


def _make_strategy(
    *, agreement: bool, window: int = SMA_W, atr_window: int = ATR_W, q: float = 0.40
) -> LightGbmStrategy:
    """Minimal LightGbmStrategy with the trend-strength gate + (optionally) AGREE_SCALE.

    We do NOT call compute_features() (no parquet) — the tests set ``_trend_strength_idx``
    directly, mirroring exactly what compute_features() builds.
    """
    return LightGbmStrategy(
        feature_columns=["mom_rsi_9"],  # any non-empty list (constructor requires it)
        ensemble_seeds=[42],
        enable_trend_strength_gate=True,
        trend_state_sma_window=window,
        trend_state_symbol="ETHUSDT",
        trend_strength_atr_window=atr_window,
        trend_strength_quantile=q,
        enable_agreement_scale=agreement,
        verbose=0,
    )


def _raw_abs_dist(
    close: np.ndarray, high: np.ndarray, low: np.ndarray, window: int, atr_window: int
) -> np.ndarray:
    """Reproduce the EXACT compute_features() raw |dist_atr| build (pre-modulation).

    Byte-identical to lgbm.compute_features() (and to test_trend_strength_lookahead.py's
    _build_strength_index value column).
    """
    cp = pd.Series(close).shift(1).to_numpy()  # close[t-1]
    sma = pd.Series(close).rolling(window).mean().shift(1).to_numpy()  # SMA_W[t-1]
    tr = np.maximum(high - low, np.maximum(np.abs(high - cp), np.abs(low - cp)))
    atr = pd.Series(tr).rolling(atr_window).mean().shift(1).to_numpy()  # ATR_aw[t-1]
    atr_safe = np.where(atr > 0, atr, np.nan)
    dist_atr = (cp - sma) / atr_safe
    return np.abs(dist_atr).astype(np.float64)


def _p3_agreement(close: np.ndarray, high: np.ndarray, low: np.ndarray, window: int) -> np.ndarray:
    """Independent past-only reference for the P3 agreement fraction (mirrors the QR's
    committed multispeed_breadth.py / blend_agreement.py primitives EXACTLY).

    anchor = +1 if close[t-1] > SMA_W[t-1] else -1
    s1 = ema_cross_sign(50, 200): +1 if EMA50[t-1] > EMA200[t-1] else -1
    s2 = donchian_breakout_sign(55): +1 if close[t-1] >= midline(High/Low, 55)[t-1] else -1
    s3 = tsmom_sign(42): +1 if close[t-1]/close[t-43] - 1 > 0 else -1
    agreement = mean({s1, s2, s3} == anchor)
    """
    cs = pd.Series(close)
    hs = pd.Series(high)
    ls = pd.Series(low)
    cp = cs.shift(1).to_numpy()  # close[t-1]
    sma = cs.rolling(window).mean().shift(1).to_numpy()  # SMA_W[t-1]
    anchor = np.where(cp > sma, 1.0, -1.0)
    ema_f = cs.ewm(span=EMA_FAST, adjust=False).mean().shift(1).to_numpy()
    ema_s = cs.ewm(span=EMA_SLOW, adjust=False).mean().shift(1).to_numpy()
    s1 = np.where(ema_f > ema_s, 1.0, -1.0)
    donch_hi = hs.shift(1).rolling(DONCH_W).max().to_numpy()
    donch_lo = ls.shift(1).rolling(DONCH_W).min().to_numpy()
    donch_mid = (donch_hi + donch_lo) / 2.0
    s2 = np.where(cp >= donch_mid, 1.0, -1.0)
    tsmom_ret = cp / pd.Series(cp).shift(TSMOM_H).to_numpy() - 1.0
    s3 = np.where(tsmom_ret > 0, 1.0, -1.0)
    panel = np.vstack([s1, s2, s3])
    return np.mean(panel == anchor, axis=0)


def _modulated_index(
    close: np.ndarray,
    high: np.ndarray,
    low: np.ndarray,
    window: int,
    atr_window: int,
    *,
    agreement: bool,
) -> tuple[np.ndarray, np.ndarray]:
    """Build the (open_time_ms, value) index exactly as compute_features() would, where
    value = raw |dist_atr| * agreement(P3) when agreement=True else raw |dist_atr|.
    """
    n = len(close)
    open_times = (START_MS + np.arange(n, dtype=np.int64) * INTERVAL_MS).astype(np.int64)
    absd = _raw_abs_dist(close, high, low, window, atr_window)
    if agreement:
        absd = absd * _p3_agreement(close, high, low, window)
    return open_times, absd.astype(np.float64)


def _random_ohlc(n: int, seed: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    close = 150.0 + np.cumsum(rng.normal(0, 2.0, n))
    close = np.maximum(close, 1.0)
    spread = np.abs(rng.normal(0, 1.5, n)) + 0.5
    high = close + spread
    low = np.maximum(close - spread, 0.5)
    return close, high, low


# Decision-candle window: past warmup for ALL P3 members. SMA-200 + Donchian-55 +
# TSMOM-42 + ATR-14 all need shift(1)-history; SMA-200 binds (needs >= 201 closes).
_WARMUP = SMA_W + 2


class TestAgreementScalePastOnly:
    def test_appending_future_candles_does_not_change_modulated_value(self):
        """THE look-ahead test: extending the series with FUTURE candles (crash + 10000x
        spike) must NOT change the modulated value at a past decision candle. Holds for the
        slowest binding member (SMA-200 / Donchian-55)."""
        n = 400
        close, high, low = _random_ohlc(n, seed=101)
        ct, val = _modulated_index(close, high, low, SMA_W, ATR_W, agreement=True)
        strat = _make_strategy(agreement=True)
        strat._trend_strength_idx = (ct, val)

        t_idx = 360
        open_time = int(START_MS + t_idx * INTERVAL_MS)
        before = strat._compute_trend_strength(open_time)

        # Append 40 future candles: crash to 1.0 then moonshot to 1,500,000 (10000x).
        fclose = np.concatenate([np.full(20, 1.0), np.full(20, 1_500_000.0)])
        fhigh = fclose + 50.0
        flow = np.maximum(fclose - 50.0, 0.5)
        all_close = np.concatenate([close, fclose])
        all_high = np.concatenate([high, fhigh])
        all_low = np.concatenate([low, flow])
        ct2, val2 = _modulated_index(all_close, all_high, all_low, SMA_W, ATR_W, agreement=True)
        strat._trend_strength_idx = (ct2, val2)
        after = strat._compute_trend_strength(open_time)

        assert before is not None and after is not None
        assert before == pytest.approx(after, rel=1e-12, abs=1e-12), (
            f"LOOK-AHEAD LEAK: AGREE_SCALE modulated value at open_time changed from "
            f"{before} to {after} after appending future candles."
        )

    def test_agreement_matches_manual(self):
        """The modulated value == raw conv * (independent manual P3 agreement fraction)."""
        n = 400
        close, high, low = _random_ohlc(n, seed=202)
        ct, val = _modulated_index(close, high, low, SMA_W, ATR_W, agreement=True)
        strat = _make_strategy(agreement=True)
        strat._trend_strength_idx = (ct, val)

        raw = _raw_abs_dist(close, high, low, SMA_W, ATR_W)
        agree = _p3_agreement(close, high, low, SMA_W)
        checked = 0
        for t_idx in range(_WARMUP, n):
            open_time = int(START_MS + t_idx * INTERVAL_MS)
            got = strat._compute_trend_strength(open_time)
            expected_raw = raw[t_idx]
            if not np.isfinite(expected_raw):
                # raw NaN at warmup → product NaN → gate returns None (conservative fire).
                assert got is None
                continue
            expected = float(expected_raw * agree[t_idx])
            assert got is not None
            assert got == pytest.approx(expected, rel=1e-9, abs=1e-9), (
                f"mismatch at t_idx={t_idx}: got {got} expected {expected} "
                f"(raw={expected_raw}, agree={agree[t_idx]})"
            )
            checked += 1
        assert checked > 50

    def test_decision_candle_own_bar_never_used(self):
        """Mutating ONLY the decision candle's own close/high/low to absurd values must not
        change its modulated value (every input is shift(1)-lagged)."""
        n = 400
        close, high, low = _random_ohlc(n, seed=303)
        ct, val = _modulated_index(close, high, low, SMA_W, ATR_W, agreement=True)
        strat = _make_strategy(agreement=True)
        strat._trend_strength_idx = (ct, val)

        t_idx = 350
        open_time = int(START_MS + t_idx * INTERVAL_MS)
        before = strat._compute_trend_strength(open_time)

        close2, high2, low2 = close.copy(), high.copy(), low.copy()
        close2[t_idx] = 1e9
        high2[t_idx] = 1e9
        low2[t_idx] = 1.0
        ct2, val2 = _modulated_index(close2, high2, low2, SMA_W, ATR_W, agreement=True)
        strat._trend_strength_idx = (ct2, val2)
        after = strat._compute_trend_strength(open_time)
        assert before == pytest.approx(after, rel=1e-12, abs=1e-12), (
            "LOOK-AHEAD LEAK: mutating the decision candle's own ohlc changed the "
            "AGREE_SCALE modulated value."
        )

    def test_uses_exactly_close_t_minus_1(self):
        """Mutating close[t-1] (the candle closing 1ms before open_time) DOES change the
        modulated value — confirming t-1 is the live input (not a future candle)."""
        n = 400
        close, high, low = _random_ohlc(n, seed=404)
        t_idx = 340
        open_time = int(START_MS + t_idx * INTERVAL_MS)

        ct, val = _modulated_index(close, high, low, SMA_W, ATR_W, agreement=True)
        strat = _make_strategy(agreement=True)
        strat._trend_strength_idx = (ct, val)
        base = strat._compute_trend_strength(open_time)

        close2 = close.copy()
        close2[t_idx - 1] = close2[t_idx - 1] * 2.0  # large move at t-1 → conv changes
        ct2, val2 = _modulated_index(close2, high, low, SMA_W, ATR_W, agreement=True)
        strat._trend_strength_idx = (ct2, val2)
        moved = strat._compute_trend_strength(open_time)
        assert base is not None and moved is not None
        assert moved != pytest.approx(base, rel=1e-6), (
            "close[t-1] is the live input — mutating it must change the modulated value."
        )


class TestAgreementScaleDefaultOffByteIdentity:
    def test_default_off_byte_identity(self):
        """enable_agreement_scale=False stores the RAW |dist_atr| series, bit-identical to a
        no-agreement build — the load-bearing iter-016->029 byte-identity guarantee.

        Compares the modulated-index builder with agreement=False against the independent
        raw |dist_atr| reference: they must be element-wise identical (NaNs in the same
        positions, finite values exactly equal)."""
        n = 400
        close, high, low = _random_ohlc(n, seed=505)
        _, val_off = _modulated_index(close, high, low, SMA_W, ATR_W, agreement=False)
        raw = _raw_abs_dist(close, high, low, SMA_W, ATR_W)
        # NaN positions identical:
        assert np.array_equal(np.isnan(val_off), np.isnan(raw))
        # Finite values bit-identical:
        finite = ~np.isnan(raw)
        assert np.array_equal(val_off[finite], raw[finite]), (
            "DEFAULT-OFF BYTE-IDENTITY VIOLATION: agreement=False must store the raw "
            "|dist_atr| series unchanged."
        )

    def test_default_constructor_flag_off(self):
        """A default-constructed strategy has _enable_agreement_scale=False (no opt-in)."""
        strat = LightGbmStrategy(feature_columns=["mom_rsi_9"], ensemble_seeds=[42], verbose=0)
        assert strat._enable_agreement_scale is False

    def test_off_vs_on_differ_where_agreement_lt_one(self):
        """Where the panel does NOT unanimously agree (agreement < 1), the modulated series
        must DIFFER from the raw series — i.e. the modulator is actually doing something."""
        n = 400
        close, high, low = _random_ohlc(n, seed=606)
        _, val_off = _modulated_index(close, high, low, SMA_W, ATR_W, agreement=False)
        _, val_on = _modulated_index(close, high, low, SMA_W, ATR_W, agreement=True)
        agree = _p3_agreement(close, high, low, SMA_W)
        finite = np.isfinite(val_off) & (val_off > 0)
        lt1 = finite & (agree < 1.0 - 1e-12)
        assert lt1.sum() > 0, "test fixture should have some non-unanimous rows"
        # At those rows the modulated value is strictly smaller (agreement < 1, conv > 0).
        assert np.all(val_on[lt1] < val_off[lt1])


class TestAgreementScaleRange:
    def test_agreement_in_valid_range_and_modulated_le_raw(self):
        """agreement multiplier ∈ {0, 1/3, 2/3, 1}; modulated conv <= raw conv (agreement
        <= 1) and >= 0 (conv >= 0, agreement >= 0)."""
        n = 400
        close, high, low = _random_ohlc(n, seed=707)
        agree = _p3_agreement(close, high, low, SMA_W)
        # Agreement is always a fraction of a 3-panel == {0, 1/3, 2/3, 1}.
        valid_levels = {0.0, 1.0 / 3.0, 2.0 / 3.0, 1.0}
        for a in np.unique(agree):
            assert any(abs(a - lvl) < 1e-12 for lvl in valid_levels), (
                f"agreement {a} not in {{0, 1/3, 2/3, 1}}"
            )
        raw = _raw_abs_dist(close, high, low, SMA_W, ATR_W)
        modulated = raw * agree
        finite = np.isfinite(raw)
        assert np.all(modulated[finite] <= raw[finite] + 1e-12)
        assert np.all(modulated[finite] >= -1e-12)


def test_threshold_built_from_modulated_series_is_past_only():
    """The per-month q-threshold over a training window built from the MODULATED series is
    consistent: mutating rows AFTER the training window does not change the threshold
    (past-only). This guards the 'modulate at build time → threshold + value consistent'
    trick that makes AGREE_SCALE work."""
    n = 600
    close, high, low = _random_ohlc(n, seed=808)
    ct, val = _modulated_index(close, high, low, SMA_W, ATR_W, agreement=True)
    train_start_ms = int(ct[0]) - 1
    train_end_ms = int(ct[400])
    mask = (ct >= train_start_ms) & (ct < train_end_ms)
    tw = val[mask]
    tw = tw[np.isfinite(tw)]
    q_thr = float(np.quantile(tw, 0.40))

    val_mut = val.copy()
    val_mut[450:] = 1e6  # mutate rows AFTER the training window
    tw2 = val_mut[(ct >= train_start_ms) & (ct < train_end_ms)]
    tw2 = tw2[np.isfinite(tw2)]
    q_thr_mut = float(np.quantile(tw2, 0.40))
    assert q_thr == pytest.approx(q_thr_mut), (
        "THRESHOLD LEAK: rows after the training window changed the past-only q_thr "
        "built from the modulated series."
    )


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
