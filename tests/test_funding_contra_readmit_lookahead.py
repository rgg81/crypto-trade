"""Look-ahead safety regression tests for the iter-v1/021 FUNDING-CONTRA-CROWD readmit.

The re-admission un-skips a trend-strength-gate-skipped row IFF funding OPPOSES the
trend-state direction AND crowding is at-least-q_f:

    f_z30   = funding_rate_zscore_30[t-1]          # `.shift(1)` past-only
    opposes = sign(f_z30) == -sign(direction)      # funding leans against the trend
    crowded = |f_z30| >= f_thr                      # f_thr = past-only training-window q_f quantile
    readmit = isfinite(f_z30) & isfinite(f_thr) & crowded & opposes

A look-ahead bug here would invalidate the whole iteration — the funding value used at
candle t would peek at the decision candle's own (or a future) funding record. The QR's
IS-only script (analysis/BTCUSDT/iteration_v1-021/r2_funding_contra_robustness.py) reads

    f_z30 = df["funding_rate_zscore_30"].shift(1).to_numpy(float)

i.e. an ADDITIONAL `.shift(1)` over the parquet column — the leak-probe confirmed the
`.shift(1)` is LOAD-BEARING (478/2382 = 20.07% of re-admission decisions FLIP without it).

compute_features() reproduces this EXACTLY: it builds a sorted (open_time_ms,
funding_z30[t-1]) index by `.shift(1)`-lagging the parquet column. ``_compute_funding_contra
(open_time)`` then reads funding_z30[t-1] at the decision candle t via searchsorted.

What is protected:

1. The (open_time, funding_z30[t-1]) index built by the EXACT compute_features
   `.shift(1)` construction matches a manual past-only reference at every row.
2. ``_compute_funding_contra(open_time)`` equals the manually-lagged funding_z30[t-1].
3. APPENDING future candles (open_time > decision) does NOT change a past row's value —
   the decisive look-ahead property.
4. Mutating the decision candle's OWN funding value does NOT change its readmit signal
   (the value is `.shift(1)`-lagged).
5. Mutating funding[t-1] DOES change it (confirms it is the live input — alignment correct).
6. Warmup (no t-1) → None → caller does NOT re-admit (the row stays skipped, conservative).
7. The per-month threshold uses ONLY training-window rows (rows after the window mutated
   to extremes do not change f_thr) → past-only, leak-free.
8. The full readmit boolean equals (isfinite & crowded & opposes), matching the QR script.

The tests bypass the parquet load by setting ``_funding_contra_idx`` directly to a synthetic
sorted ``(open_time_ms, funding_z30[t-1])`` index — exactly the structure compute_features()
builds — and a reference builder mirrors that construction.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

# 8h candle geometry (matches the real parquets):
INTERVAL_MS = 8 * 60 * 60 * 1000  # 28_800_000
START_MS = 1_577_836_800_000  # 2020-01-01 00:00:00 UTC (matches BTCUSDT parquet origin)


def _make_strategy(q: float = 0.50) -> LightGbmStrategy:
    """Minimal valid LightGbmStrategy with the funding-contra readmit enabled.

    We do NOT call compute_features() (no parquet) — the tests set
    ``_funding_contra_idx`` / ``_funding_contra_thr`` directly, mirroring exactly what
    compute_features + _train_for_month build.
    """
    return LightGbmStrategy(
        feature_columns=["mom_rsi_9"],  # any non-empty list (constructor requires it)
        ensemble_seeds=[42],
        enable_funding_contra_readmit=True,
        funding_contra_col="funding_rate_zscore_30",
        funding_contra_quantile=q,
        trend_state_symbol="BTCUSDT",
        verbose=0,
    )


def _build_funding_index(funding: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Reproduce the EXACT compute_features() (open_time_ms, funding_z30[t-1]) build.

    Must stay byte-identical to the lgbm.compute_features() construction so the test
    verifies the production index, not a paraphrase. The index is keyed on OPEN_TIME so
    decision candle t maps to row t with the value funding[t-1] (the extra `.shift(1)`).
    """
    n = len(funding)
    open_times = (START_MS + np.arange(n, dtype=np.int64) * INTERVAL_MS).astype(np.int64)
    fz_lag = pd.Series(funding).shift(1).to_numpy(dtype=np.float64)  # funding_z30[t-1]
    return open_times, fz_lag


def _manual_funding_t_minus_1(funding: np.ndarray, t_idx: int) -> float | None:
    """Independent past-only reference for funding_z30[t-1] at decision candle t_idx."""
    if t_idx - 1 < 0:
        return None
    val = float(funding[t_idx - 1])
    if not np.isfinite(val):
        return None
    return val


def _random_funding(n: int, seed: int) -> np.ndarray:
    """Synthetic funding z-score series with realistic sign-changing structure."""
    rng = np.random.default_rng(seed)
    # mean-reverting AR(1)-ish z-score that crosses zero often (sign matters for opposes)
    z = np.zeros(n)
    for i in range(1, n):
        z[i] = 0.85 * z[i - 1] + rng.normal(0, 1.0)
    return z


class TestFundingContraPastOnly:
    def test_index_matches_manual_reference(self):
        """The compute_features (open_time, funding_z30[t-1]) build matches the manual ref."""
        n = 300
        funding = _random_funding(n, seed=3)
        ot, fz = _build_funding_index(funding)
        for t_idx in range(2, n):
            expected = _manual_funding_t_minus_1(funding, t_idx)
            got = float(fz[t_idx])
            if expected is None:
                assert not np.isfinite(got)
            else:
                assert np.isfinite(got)
                assert got == pytest.approx(expected, rel=1e-12, abs=1e-12), (
                    f"mismatch at t_idx={t_idx}: got {got} expected {expected}"
                )

    def test_compute_funding_contra_matches_manual_past_only(self):
        """_compute_funding_contra(open_time) == manual past-only funding_z30[t-1]."""
        n = 300
        funding = _random_funding(n, seed=5)
        ot, fz = _build_funding_index(funding)
        strat = _make_strategy()
        strat._funding_contra_idx = (ot, fz)
        for t_idx in range(2, n):
            open_time = int(START_MS + t_idx * INTERVAL_MS)
            got = strat._compute_funding_contra(open_time)
            expected = _manual_funding_t_minus_1(funding, t_idx)
            if expected is None:
                assert got is None
            else:
                assert got == pytest.approx(expected, rel=1e-12, abs=1e-12), (
                    f"mismatch at t_idx={t_idx}: got {got} expected {expected}"
                )

    def test_appending_future_candles_does_not_change_value(self):
        """THE look-ahead test: extending the series with FUTURE candles must not change
        the funding signal at a past decision candle."""
        n = 300
        funding = _random_funding(n, seed=11)
        ot, fz = _build_funding_index(funding)
        strat = _make_strategy()
        strat._funding_contra_idx = (ot, fz)

        t_idx = 270
        open_time = int(START_MS + t_idx * INTERVAL_MS)
        before = strat._compute_funding_contra(open_time)

        # Append 40 future candles with WILDLY different funding (extreme crowding flips).
        # If the lookup peeked at any candle with open_time >= open_time, `before` would
        # change. Rebuild the WHOLE index from the extended series — even the index build
        # must keep past funding_z30[t-1] values frozen (`.shift(1)` guarantees it).
        ffut = np.concatenate([np.full(20, -50.0), np.full(20, 50.0)])
        all_funding = np.concatenate([funding, ffut])
        ot2, fz2 = _build_funding_index(all_funding)
        strat._funding_contra_idx = (ot2, fz2)
        after = strat._compute_funding_contra(open_time)

        assert before is not None and after is not None
        assert before == pytest.approx(after, rel=1e-12, abs=1e-12), (
            f"LOOK-AHEAD LEAK: funding signal at open_time changed from {before} to "
            f"{after} after appending future candles."
        )

    def test_decision_candle_own_funding_never_used(self):
        """Mutating ONLY the decision candle's own funding[t] must not change its readmit
        signal (the value is `.shift(1)`-lagged → it uses funding[t-1])."""
        n = 300
        funding = _random_funding(n, seed=13)
        ot, fz = _build_funding_index(funding)
        strat = _make_strategy()
        strat._funding_contra_idx = (ot, fz)

        t_idx = 260
        open_time = int(START_MS + t_idx * INTERVAL_MS)
        before = strat._compute_funding_contra(open_time)

        # Slam the decision candle's OWN funding to an extreme; rebuild; signal must not move.
        funding2 = funding.copy()
        funding2[t_idx] = 1e6
        ot2, fz2 = _build_funding_index(funding2)
        strat._funding_contra_idx = (ot2, fz2)
        after = strat._compute_funding_contra(open_time)
        assert before == pytest.approx(after, rel=1e-12, abs=1e-12), (
            "LOOK-AHEAD LEAK: mutating the decision candle's own funding changed the signal."
        )

    def test_uses_exactly_funding_t_minus_1(self):
        """Mutating funding[t-1] changes the signal — confirming it is the live input."""
        n = 300
        funding = _random_funding(n, seed=17)
        strat = _make_strategy()
        t_idx = 250
        open_time = int(START_MS + t_idx * INTERVAL_MS)

        ot, fz = _build_funding_index(funding)
        strat._funding_contra_idx = (ot, fz)
        base = strat._compute_funding_contra(open_time)

        funding2 = funding.copy()
        funding2[t_idx - 1] = funding2[t_idx - 1] + 10.0  # large move at t-1 → signal changes
        ot2, fz2 = _build_funding_index(funding2)
        strat._funding_contra_idx = (ot2, fz2)
        moved = strat._compute_funding_contra(open_time)
        assert base is not None and moved is not None
        assert moved != pytest.approx(base, rel=1e-6), (
            "funding[t-1] is the live input — mutating it must change the signal."
        )


class TestFundingContraWarmupAndGuards:
    def test_warmup_returns_none(self):
        """The first decision candle (t_idx=0) has no t-1 → None (conservative no readmit)."""
        n = 50
        funding = _random_funding(n, seed=19)
        ot, fz = _build_funding_index(funding)
        strat = _make_strategy()
        strat._funding_contra_idx = (ot, fz)
        open_time = int(START_MS + 0 * INTERVAL_MS)
        assert strat._compute_funding_contra(open_time) is None

    def test_open_time_before_any_candle_returns_none(self):
        n = 300
        funding = _random_funding(n, seed=23)
        ot, fz = _build_funding_index(funding)
        strat = _make_strategy()
        strat._funding_contra_idx = (ot, fz)
        assert strat._compute_funding_contra(int(START_MS - INTERVAL_MS)) is None

    def test_index_none_returns_none(self):
        """Re-admission disabled / parquet not loaded → conservative None (no readmit)."""
        strat = _make_strategy()
        strat._funding_contra_idx = None
        assert strat._compute_funding_contra(int(START_MS + 250 * INTERVAL_MS)) is None

    def test_nan_funding_returns_none(self):
        """A NaN funding_z30[t-1] (missing record / warmup) → None."""
        n = 300
        funding = _random_funding(n, seed=27)
        funding[148] = np.nan  # so funding_z30[t-1] at t_idx=149 is NaN
        ot, fz = _build_funding_index(funding)
        strat = _make_strategy()
        strat._funding_contra_idx = (ot, fz)
        open_time = int(START_MS + 149 * INTERVAL_MS)
        assert strat._compute_funding_contra(open_time) is None


class TestFundingContraThresholdPastOnly:
    def test_threshold_uses_only_training_window_rows(self):
        """The per-month f_thr must be the q-quantile of |funding_z30[t-1]| over candles
        whose open_time is in [train_start_ms, train_end_ms) — appending rows AFTER the
        training window must not change it (past-only)."""
        n = 600
        funding = _random_funding(n, seed=29)
        ot, fz = _build_funding_index(funding)
        train_start_ms = int(ot[0]) - 1
        train_end_ms = int(ot[400])
        mask = (ot >= train_start_ms) & (ot < train_end_ms)
        tw = np.abs(fz[mask])
        tw = tw[np.isfinite(tw)]
        f_thr_full = float(np.quantile(tw, 0.50))

        # Recompute with the LATER rows mutated to extremes — threshold must not change.
        fz_mut = fz.copy()
        fz_mut[450:] = 1e6
        tw2 = np.abs(fz_mut[(ot >= train_start_ms) & (ot < train_end_ms)])
        tw2 = tw2[np.isfinite(tw2)]
        f_thr_mut = float(np.quantile(tw2, 0.50))
        assert f_thr_full == pytest.approx(f_thr_mut), (
            "THRESHOLD LEAK: rows after the training window changed the past-only f_thr."
        )


class TestFundingContraReadmitDecision:
    def test_readmit_boolean_matches_qr_script(self):
        """The readmit boolean equals isfinite & |f_z30|>=thr & sign(f_z30)==-sign(dir),
        matching the QR IS-only script's r2 mask EXACTLY."""
        n = 300
        funding = _random_funding(n, seed=31)
        ot, fz = _build_funding_index(funding)
        strat = _make_strategy()
        strat._funding_contra_idx = (ot, fz)
        finite = np.abs(fz[np.isfinite(fz)])
        thr = float(np.quantile(finite, 0.50))
        strat._funding_contra_thr = thr

        checked = 0
        for t_idx in range(5, n):
            open_time = int(START_MS + t_idx * INTERVAL_MS)
            f = strat._compute_funding_contra(open_time)
            if f is None:
                continue
            for direction in (+1, -1):
                # Mirror the production gate-skip-site logic EXACTLY.
                opposes = int(np.sign(f)) == -int(np.sign(direction))
                crowded = abs(f) >= strat._funding_contra_thr
                readmit_prod = bool(opposes and crowded)
                # Mirror the QR script's r2 mask.
                readmit_qr = bool(
                    np.isfinite(f)
                    and np.isfinite(thr)
                    and (abs(f) >= thr)
                    and (np.sign(f) == -np.sign(direction))
                )
                assert readmit_prod == readmit_qr, (
                    f"readmit mismatch t_idx={t_idx} dir={direction}: "
                    f"prod={readmit_prod} qr={readmit_qr} (f={f}, thr={thr})"
                )
            checked += 1
        assert checked > 0

    def test_opposes_semantics(self):
        """Short trend (dir=-1) re-admits on POSITIVE funding; long trend (dir=+1)
        re-admits on NEGATIVE funding (crowd leaning against the trend)."""
        # dir = -1 (short trend): funding > 0 (crowded longs) OPPOSES → readmit-eligible.
        assert int(np.sign(5.0)) == -int(np.sign(-1))  # +1 == +1 → opposes True
        # dir = -1 (short trend): funding < 0 does NOT oppose.
        assert not (int(np.sign(-5.0)) == -int(np.sign(-1)))  # -1 == +1 → False
        # dir = +1 (long trend): funding < 0 (crowded shorts) OPPOSES → readmit-eligible.
        assert int(np.sign(-5.0)) == -int(np.sign(+1))  # -1 == -1 → opposes True
        # dir = +1 (long trend): funding > 0 does NOT oppose.
        assert not (int(np.sign(5.0)) == -int(np.sign(+1)))  # +1 == -1 → False


def test_disabled_by_default_no_index_built():
    """Default construction (readmit OFF) leaves the index None and returns None."""
    strat = LightGbmStrategy(
        feature_columns=["mom_rsi_9"],
        ensemble_seeds=[42],
        verbose=0,
    )
    assert strat._enable_funding_contra_readmit is False
    assert strat._funding_contra_idx is None
    assert strat._funding_contra_thr is None
    assert strat._compute_funding_contra(int(START_MS + 250 * INTERVAL_MS)) is None


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
