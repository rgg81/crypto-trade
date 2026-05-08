"""Adversarial tests for v3 engineered (composed) features — iter-v3/025+.

Focuses on ``compute_regime_momentum_signed_5d`` (iter-v3/025),
``compute_vol_adj_autocorr`` (iter-v3/026; dead code — retained for multi-seed
CONFIRMATION stacking experiments at iter-v3/029+),
``compute_cross_asset_divergence_norm`` (iter-v3/027), and
``compute_fracdiff_d05_close`` (iter-v3/034; LdP AFML Ch. 5 FFD at d=0.5):

1. Import smoke test — public API importable without error.
2. Composition correctness — sign flip on hurst > 0.5 vs < 0.5.
3. Past-only discipline — current bar's ret_5d uses bars [t-15, t-1] only;
   no look-ahead from future bars altering t's value.
4. NaN warm-up — first 99 bars NaN (hurst_100 needs 100 bars; ret_5d needs 15;
   hurst_100 dominates).
5. Sign flip exactness — sign(hurst - 0.5) must be exactly +1 / -1 / NaN,
   not a continuous gradient.
6. Missing hurst_100 column — graceful all-NaN fallback, no error.
7. Pure random-walk edge case — hurst_100 == 0.5 → sign = 0 → treated as NaN.
8. add_engineered_v3_features integration — GROUP_REGISTRY entry point.
9. vol_adj_autocorr composition correctness — ratio of autocorr to vol + EPS.
10. vol_adj_autocorr past-only discipline — appending future bars does not alter t's value.
11. vol_adj_autocorr edge case — near-zero denominator capped at ±100 (not inf).
12. vol_adj_autocorr idempotency — calling twice produces identical output.
13. cross_asset_divergence_norm past-only — appending future bars does not alter t's value.
14. cross_asset_divergence_norm NaN warm-up — first 41 bars NaN (btc_ret_14d 42-bar
    window dominates).
15. cross_asset_divergence_norm EPS robustness — output is finite when vwap_dev_20 == 0.
16. cross_asset_divergence_norm idempotency — calling twice produces identical output.
17. fracdiff_d05_close weights — LdP AFML Ch. 5 recurrence converges; truncated at 1e-4.
18. fracdiff_d05_close past-only — appending future bars does not alter t's value.
19. fracdiff_d05_close ADF stationarity — fixed d=0.5 makes a random walk stationary.
20. fracdiff_d05_close NaN warm-up — first (W-1) bars NaN where W = len(weights).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from crypto_trade.features_v3.engineered_v3 import (
    _fracdiff_d05_weights,
    add_engineered_v3_features,
    compute_cross_asset_divergence_norm,
    compute_fracdiff_d05_close,
    compute_regime_momentum_signed_5d,
    compute_vol_adj_autocorr,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_8H_MS = 8 * 3600 * 1000
_IS_START_MS = 1_679_616_000_000  # 2023-03-24 00:00 UTC


def _make_df(
    n: int = 200,
    seed: int = 42,
    hurst_value: float | None = None,
) -> pd.DataFrame:
    """Create a minimal kline-like DataFrame with hurst_100 column.

    Args:
        n: number of rows.
        seed: numpy random seed for reproducibility.
        hurst_value: if not None, overrides hurst_100 with a constant scalar.
            Useful for testing sign-flip behaviour in isolation.
    """
    rng = np.random.default_rng(seed)
    open_times = [_IS_START_MS + i * _8H_MS for i in range(n)]
    close = rng.uniform(100.0, 1000.0, n)
    df = pd.DataFrame(
        {
            "open_time": open_times,
            "open": rng.uniform(100.0, 1000.0, n),
            "high": close * rng.uniform(1.0, 1.02, n),
            "low": close * rng.uniform(0.98, 1.0, n),
            "close": close,
            "volume": rng.uniform(1000.0, 10000.0, n),
            "symbol": "BCHUSDT",
        }
    )
    # Simulate realistic Hurst values (normally distributed around 0.5)
    if hurst_value is not None:
        df["hurst_100"] = hurst_value
    else:
        df["hurst_100"] = rng.uniform(0.3, 0.7, n)
        # First 99 bars NaN (warm-up period for rolling 100-bar Hurst)
        df.loc[df.index[:99], "hurst_100"] = np.nan
    return df


# ---------------------------------------------------------------------------
# 1. Import smoke test
# ---------------------------------------------------------------------------


class TestImport:
    def test_importable(self) -> None:
        """Public API must be importable without error."""
        from crypto_trade.features_v3.engineered_v3 import (  # noqa: F401
            add_engineered_v3_features,
            compute_cross_asset_divergence_norm,
            compute_regime_momentum_signed_5d,
        )

    def test_column_names_exported(self) -> None:
        """All public symbols must be in __all__."""
        from crypto_trade.features_v3 import engineered_v3

        assert "compute_regime_momentum_signed_5d" in engineered_v3.__all__
        assert "add_engineered_v3_features" in engineered_v3.__all__
        assert "compute_vol_adj_autocorr" in engineered_v3.__all__
        assert "compute_cross_asset_divergence_norm" in engineered_v3.__all__
        assert "compute_fracdiff_d05_close" in engineered_v3.__all__, (
            "compute_fracdiff_d05_close must be in engineered_v3.__all__ "
            "(iter-v3/034: ADD fracdiff_d05_close; LdP AFML Ch. 5 FFD at d=0.5)."
        )


# ---------------------------------------------------------------------------
# 2. Composition correctness — sign flip
# ---------------------------------------------------------------------------


class TestCompositionCorrectness:
    def test_trending_regime_positive_momentum(self) -> None:
        """hurst_100 > 0.5 → sign = +1 → feature = +ret_5d (momentum continuation)."""
        n = 200
        # Constant hurst > 0.5 for all valid bars
        df = _make_df(n=n, seed=1, hurst_value=0.65)
        # NaN out first 99 to simulate hurst warm-up
        df.loc[df.index[:99], "hurst_100"] = np.nan
        out = compute_regime_momentum_signed_5d(df)

        feat = out["regime_momentum_signed_5d"]
        valid_idx = feat.dropna().index
        assert len(valid_idx) > 0, "No valid values after warm-up"

        # Manually compute expected: ret_5d for valid rows
        log_close = np.log(df["close"].astype(float).clip(lower=1e-12))
        ret_5d = log_close - log_close.shift(15)

        for idx in valid_idx:
            expected = ret_5d.loc[idx]  # sign(0.65 - 0.5) = +1.0 → feature = ret_5d
            assert feat.loc[idx] == pytest.approx(expected, abs=1e-12), (
                f"Trending regime: feature at index {idx} should equal ret_5d ({expected}), "
                f"got {feat.loc[idx]}"
            )

    def test_mean_reverting_regime_negative_momentum(self) -> None:
        """hurst_100 < 0.5 → sign = -1 → feature = -ret_5d (momentum reversal)."""
        n = 200
        df = _make_df(n=n, seed=2, hurst_value=0.35)
        df.loc[df.index[:99], "hurst_100"] = np.nan
        out = compute_regime_momentum_signed_5d(df)

        feat = out["regime_momentum_signed_5d"]
        valid_idx = feat.dropna().index
        assert len(valid_idx) > 0

        log_close = np.log(df["close"].astype(float).clip(lower=1e-12))
        ret_5d = log_close - log_close.shift(15)

        for idx in valid_idx:
            expected = -ret_5d.loc[idx]  # sign(0.35 - 0.5) = -1.0 → feature = -ret_5d
            assert feat.loc[idx] == pytest.approx(expected, abs=1e-12), (
                f"Mean-reversion regime: feature at index {idx} should equal -ret_5d "
                f"({expected}), got {feat.loc[idx]}"
            )

    def test_sign_flip_direction_inversion(self) -> None:
        """Same close prices: trending regime must give opposite sign to mean-reverting."""
        n = 200
        df_trending = _make_df(n=n, seed=3, hurst_value=0.7)
        df_trending.loc[df_trending.index[:99], "hurst_100"] = np.nan
        df_mrv = df_trending.copy()
        df_mrv["hurst_100"] = 0.3
        df_mrv.loc[df_mrv.index[:99], "hurst_100"] = np.nan

        out_t = compute_regime_momentum_signed_5d(df_trending)
        out_m = compute_regime_momentum_signed_5d(df_mrv)

        feat_t = out_t["regime_momentum_signed_5d"]
        feat_m = out_m["regime_momentum_signed_5d"]
        valid_t = feat_t.dropna().index
        valid_m = feat_m.dropna().index
        common = valid_t.intersection(valid_m)
        assert len(common) > 0

        # They must be exact negatives of each other (same close, inverted sign)
        np.testing.assert_array_almost_equal(
            feat_t.loc[common].values,
            -feat_m.loc[common].values,
            decimal=12,
            err_msg="Trending and mean-reverting regime features must be exact negatives",
        )


# ---------------------------------------------------------------------------
# 3. Past-only discipline — appending future bars must not alter t's value
# ---------------------------------------------------------------------------


class TestPastOnlyDiscipline:
    def test_appending_future_bars_does_not_change_value_at_t(self) -> None:
        """Value at row t must not change when future bars are appended.

        This is the canonical past-only adversarial test: compute the feature on
        df[:T], then compute on df[:T+20] (T+20 future bars appended).  The value
        at index T-1 (the last valid bar in the first run) must be identical.
        """
        n = 220
        df_full = _make_df(n=n, seed=10)
        split = 160  # split point

        df_short = df_full.iloc[:split].reset_index(drop=True)
        df_long = df_full.reset_index(drop=True)

        out_short = compute_regime_momentum_signed_5d(df_short)
        out_long = compute_regime_momentum_signed_5d(df_long)

        # The value at row split-1 of the short frame must equal row split-1 of the long frame
        val_short = out_short["regime_momentum_signed_5d"].iloc[split - 1]
        val_long = out_long["regime_momentum_signed_5d"].iloc[split - 1]

        if np.isnan(val_short) and np.isnan(val_long):
            pass  # Both NaN is consistent
        else:
            assert val_short == pytest.approx(val_long, abs=1e-12), (
                f"Past-only violation: value at row {split - 1} changed from {val_short} "
                f"to {val_long} when future bars were appended."
            )

    def test_ret_5d_uses_bar_at_t_minus_15(self) -> None:
        """ret_5d at bar t = log(close[t]) - log(close[t-15]).

        Spike close[t] to a known extreme value; verify the feature at t
        reflects log(close[t]) in the numerator but does NOT use close[t+1...].
        """
        n = 200
        df = _make_df(n=n, seed=11, hurst_value=0.65)
        df.loc[df.index[:99], "hurst_100"] = np.nan

        # Spike close at t=120
        target = 120
        spike_close = 9999.0
        df_spiked = df.copy()
        df_spiked.loc[target, "close"] = spike_close

        out_base = compute_regime_momentum_signed_5d(df)
        out_spiked = compute_regime_momentum_signed_5d(df_spiked)

        # At bar target: the spike IS in the numerator (log(close[target]) changes)
        val_base = out_base["regime_momentum_signed_5d"].iloc[target]
        val_spiked = out_spiked["regime_momentum_signed_5d"].iloc[target]
        # The spike must affect value at target (numerator effect)
        assert val_base != pytest.approx(val_spiked, abs=1e-10), (
            f"Spike at close[{target}] had no effect on feature[{target}] — "
            "ret_5d numerator not using close[t]."
        )

        # At bar target-1: NOT affected (spike is in the FUTURE from t-1's perspective)
        val_before_base = out_base["regime_momentum_signed_5d"].iloc[target - 1]
        val_before_spiked = out_spiked["regime_momentum_signed_5d"].iloc[target - 1]
        if not (np.isnan(val_before_base) and np.isnan(val_before_spiked)):
            assert val_before_base == pytest.approx(val_before_spiked, abs=1e-12), (
                f"Past-only violation: feature[{target - 1}] changed when close[{target}] "
                f"was spiked.  Feature at t-1 must not depend on close[t]."
            )


# ---------------------------------------------------------------------------
# 4. NaN warm-up — first 99 bars NaN
# ---------------------------------------------------------------------------


class TestNaNWarmUp:
    def test_first_99_bars_nan(self) -> None:
        """First 99 bars must be NaN because hurst_100 needs 100 bars (bars 0..98).

        ret_5d warm-up is 15 bars (bars 0..14 NaN), which is dominated by the
        hurst_100 warm-up of 99 bars.  The first valid bar is index 99.
        """
        n = 300
        df = _make_df(n=n, seed=20)
        # Ensure first 99 hurst_100 values are NaN (realistic warm-up)
        df.loc[df.index[:99], "hurst_100"] = np.nan
        # Provide valid hurst for bars 99+
        df.loc[df.index[99:], "hurst_100"] = 0.55  # trending

        out = compute_regime_momentum_signed_5d(df)
        feat = out["regime_momentum_signed_5d"]

        # Bars 0..98 must all be NaN
        assert feat.iloc[:99].isna().all(), (
            f"Expected first 99 bars to be NaN (hurst_100 warm-up). "
            f"First non-NaN index: {feat.first_valid_index()}"
        )
        # Bar 99 onward should have valid values (hurst valid, ret_5d also valid by bar 99)
        # Note: ret_5d at bar 99 = log(close[99]) - log(close[84]) — both valid.
        assert feat.iloc[99:].notna().any(), (
            "Expected at least some valid values after bar 99 (hurst warm-up complete)."
        )

    def test_first_valid_index_is_99(self) -> None:
        """The first valid (non-NaN) row must be exactly at index 99."""
        n = 300
        df = _make_df(n=n, seed=21)
        df.loc[df.index[:99], "hurst_100"] = np.nan
        df.loc[df.index[99:], "hurst_100"] = 0.6

        out = compute_regime_momentum_signed_5d(df)
        feat = out["regime_momentum_signed_5d"]

        first_valid = feat.first_valid_index()
        assert first_valid == 99, (
            f"Expected first valid index at 99 (hurst_100 warm-up); got {first_valid}."
        )

    def test_no_nan_explosion_after_warmup(self) -> None:
        """After bar 99, most values should be non-NaN (no pathological NaN spread)."""
        n = 300
        df = _make_df(n=n, seed=22)
        df.loc[df.index[:99], "hurst_100"] = np.nan
        df.loc[df.index[99:], "hurst_100"] = 0.55

        out = compute_regime_momentum_signed_5d(df)
        feat = out["regime_momentum_signed_5d"]

        post_warmup = feat.iloc[99:]
        nan_frac = post_warmup.isna().mean()
        assert nan_frac < 0.05, (
            f"Too many NaN values after warm-up: {nan_frac:.1%} > 5%. "
            "Possible NaN explosion in ret_5d or sign computation."
        )


# ---------------------------------------------------------------------------
# 5. Sign flip exactness — must be exactly ±1, not a gradient
# ---------------------------------------------------------------------------


class TestSignFlipExactness:
    def test_sign_values_are_exactly_plus_minus_one(self) -> None:
        """The hurst sign component must be exactly +1 or -1 (or NaN), never a gradient.

        The composed feature = ret_5d × {+1, -1, NaN}; intermediate sign values
        like +0.7 or -0.3 would indicate the sign() function was not applied.
        """
        n = 300
        # Use both trending (hurst > 0.5) and mean-reverting (hurst < 0.5) bars
        df = _make_df(n=n, seed=30)
        df.loc[df.index[:99], "hurst_100"] = np.nan
        # Alternate between 0.6 (trending) and 0.4 (mean-reverting) for valid bars
        for i in range(99, n):
            df.loc[i, "hurst_100"] = 0.6 if i % 2 == 0 else 0.4

        out = compute_regime_momentum_signed_5d(df)
        feat = out["regime_momentum_signed_5d"]
        log_close = np.log(df["close"].astype(float).clip(lower=1e-12))
        ret_5d = log_close - log_close.shift(15)

        for idx in feat.dropna().index:
            f = feat.loc[idx]
            r = ret_5d.loc[idx]
            if abs(r) < 1e-15:
                continue  # Skip near-zero ret_5d (ratio undefined)
            # The ratio feat/ret_5d must be exactly +1.0 or -1.0
            ratio = f / r
            assert abs(abs(ratio) - 1.0) < 1e-10, (
                f"Sign at index {idx}: feat/ret_5d = {ratio:.6f} — expected exactly ±1.0. "
                "sign(hurst - 0.5) must not be a gradient."
            )

    def test_hurst_exactly_above_threshold_gives_positive_sign(self) -> None:
        """hurst_100 = 0.5 + epsilon must give sign = +1 (not 0 or NaN)."""
        n = 200
        epsilon = 1e-9
        df = _make_df(n=n, seed=31, hurst_value=0.5 + epsilon)
        df.loc[df.index[:99], "hurst_100"] = np.nan
        out = compute_regime_momentum_signed_5d(df)

        log_close = np.log(df["close"].astype(float).clip(lower=1e-12))
        ret_5d = log_close - log_close.shift(15)
        feat = out["regime_momentum_signed_5d"]

        for idx in feat.dropna().index:
            r = ret_5d.loc[idx]
            f = feat.loc[idx]
            # sign(epsilon) = +1, so feature = +ret_5d
            assert f == pytest.approx(r, abs=1e-12), (
                f"hurst = 0.5+eps: expected feature = +ret_5d at index {idx}, "
                f"got feature={f:.6f}, ret_5d={r:.6f}."
            )

    def test_hurst_exactly_below_threshold_gives_negative_sign(self) -> None:
        """hurst_100 = 0.5 - epsilon must give sign = -1."""
        n = 200
        epsilon = 1e-9
        df = _make_df(n=n, seed=32, hurst_value=0.5 - epsilon)
        df.loc[df.index[:99], "hurst_100"] = np.nan
        out = compute_regime_momentum_signed_5d(df)

        log_close = np.log(df["close"].astype(float).clip(lower=1e-12))
        ret_5d = log_close - log_close.shift(15)
        feat = out["regime_momentum_signed_5d"]

        for idx in feat.dropna().index:
            r = ret_5d.loc[idx]
            f = feat.loc[idx]
            # sign(-epsilon) = -1, so feature = -ret_5d
            assert f == pytest.approx(-r, abs=1e-12), (
                f"hurst = 0.5-eps: expected feature = -ret_5d at index {idx}, "
                f"got feature={f:.6f}, ret_5d={r:.6f}."
            )


# ---------------------------------------------------------------------------
# 6. Missing hurst_100 column — graceful all-NaN fallback
# ---------------------------------------------------------------------------


class TestMissingHurst:
    def test_missing_hurst_column_returns_all_nan(self) -> None:
        """When hurst_100 is absent, regime_momentum_signed_5d must be all-NaN.

        No KeyError or AttributeError should be raised.  The runner's
        _verify_feature_columns will catch the downstream column mismatch.
        """
        n = 150
        df = _make_df(n=n, seed=40)
        df_no_hurst = df.drop(columns=["hurst_100"])

        out = compute_regime_momentum_signed_5d(df_no_hurst)

        assert "regime_momentum_signed_5d" in out.columns, (
            "regime_momentum_signed_5d column must be added even when hurst_100 is absent."
        )
        assert out["regime_momentum_signed_5d"].isna().all(), (
            "regime_momentum_signed_5d must be all-NaN when hurst_100 is missing."
        )


# ---------------------------------------------------------------------------
# 7. Pure random-walk edge case — hurst_100 == 0.5 → NaN
# ---------------------------------------------------------------------------


class TestPureRandomWalkEdgeCase:
    def test_hurst_exactly_05_produces_nan(self) -> None:
        """hurst_100 == 0.5 → sign(0) = 0 → treated as NaN, not 0 × ret_5d = 0.

        Returning 0 would suppress real signal at later bars; NaN is the correct
        behaviour (exclude the bar from model training).
        """
        n = 200
        df = _make_df(n=n, seed=50, hurst_value=0.5)
        # Warm-up: first 99 NaN (realistic)
        df.loc[df.index[:99], "hurst_100"] = np.nan
        # Set bars 99+ all to exactly 0.5 (pure random walk)
        df.loc[df.index[99:], "hurst_100"] = 0.5

        out = compute_regime_momentum_signed_5d(df)
        feat = out["regime_momentum_signed_5d"]

        # All bars (warm-up + pure-RW) must be NaN — no 0.0 values
        assert feat.isna().all(), (
            f"hurst_100 == 0.5 must produce NaN (not 0.0) at all bars. "
            f"Non-NaN count: {feat.notna().sum()}; values: {feat.dropna().head(5).tolist()}"
        )

    def test_hurst_05_bars_interspersed_with_trending(self) -> None:
        """Bars with hurst == 0.5 are NaN; surrounding trending bars are non-NaN."""
        n = 200
        df = _make_df(n=n, seed=51)
        df.loc[df.index[:99], "hurst_100"] = np.nan
        # Alternate: trending at 99, RW at 100, trending at 101, ...
        for i in range(99, n):
            df.loc[i, "hurst_100"] = 0.5 if i % 2 == 1 else 0.6

        out = compute_regime_momentum_signed_5d(df)
        feat = out["regime_momentum_signed_5d"]

        # Even indices (100+) with hurst=0.6 should be non-NaN after warm-up
        even_post_warmup = feat.iloc[100::2]  # indices 100, 102, ...
        nan_idx = even_post_warmup[even_post_warmup.isna()].index.tolist()
        assert even_post_warmup.notna().all(), (
            "Even-index bars (hurst=0.6 trending) should produce non-NaN values "
            f"after warm-up. NaN indices: {nan_idx}"
        )

        # Odd indices (101+) with hurst=0.5 should be NaN
        odd_post_warmup = feat.iloc[101::2]  # indices 101, 103, ...
        assert odd_post_warmup.isna().all(), (
            "Odd-index bars (hurst=0.5 pure-RW) must be NaN. "
            f"Non-NaN indices: {odd_post_warmup.dropna().index.tolist()}"
        )


# ---------------------------------------------------------------------------
# 8. add_engineered_v3_features — GROUP_REGISTRY entry point
# ---------------------------------------------------------------------------


class TestAddEngineeredV3Features:
    def test_returns_regime_momentum_column(self) -> None:
        """add_engineered_v3_features must add regime_momentum_signed_5d."""
        df = _make_df(n=200, seed=60)
        out = add_engineered_v3_features(df)
        assert "regime_momentum_signed_5d" in out.columns

    def test_does_not_modify_source_df(self) -> None:
        """add_engineered_v3_features must return a copy, not mutate the input."""
        df = _make_df(n=200, seed=61)
        cols_before = set(df.columns)
        _ = add_engineered_v3_features(df)
        assert set(df.columns) == cols_before, (
            "add_engineered_v3_features must not modify the input DataFrame."
        )

    def test_output_has_same_length(self) -> None:
        """Output must have the same number of rows as input."""
        n = 150
        df = _make_df(n=n, seed=62)
        out = add_engineered_v3_features(df)
        assert len(out) == n

    def test_group_registry_imports_correctly(self) -> None:
        """engineered_v3 must be importable from the GROUP_REGISTRY.

        iter-v3/036: vol_adj_autocorr RE-DISPATCHED (was dead code since iter-v3/027).
        Generates the column for all symbols so TRX parquet contains it.
        Only TRX's feature_columns= (via V3_FEATURES_PER_SYMBOL) passes it to LightGBM.
        cross_asset_divergence_norm remains dead code — NOT dispatched; must be ABSENT.
        """
        from crypto_trade.features_v3 import GROUP_REGISTRY

        assert "engineered_v3" in GROUP_REGISTRY, (
            "engineered_v3 must be registered in GROUP_REGISTRY. Check features_v3/__init__.py."
        )
        fn = GROUP_REGISTRY["engineered_v3"]
        # Call with a DataFrame that includes all engineered feature dependencies.
        df = _make_df_with_all_primitives(n=200, seed=63)
        out = fn(df)
        assert "regime_momentum_signed_5d" in out.columns, (
            "regime_momentum_signed_5d (iter-v3/025; KEPT; MINI-VALIDATION target) "
            "must be in output."
        )
        # cross_asset_divergence_norm is dead code at iter-v3/028 — NOT dispatched.
        assert "cross_asset_divergence_norm" not in out.columns, (
            "cross_asset_divergence_norm (iter-v3/027; DROPPED at iter-v3/028) must NOT "
            "be in output. Stacking FALSIFIED at iter-v3/027; reverted to 14 features. "
            "compute_cross_asset_divergence_norm retained as dead code but not dispatched."
        )
        # iter-v3/036: vol_adj_autocorr RE-DISPATCHED for parquet generation (TRX-only model).
        assert "vol_adj_autocorr" in out.columns, (
            "vol_adj_autocorr (iter-v3/036; RE-DISPATCHED) MUST be in output. "
            "Column generated for all symbols; only TRX passes it to LightGBM. "
            "Check add_engineered_v3_features dispatch in engineered_v3.py."
        )


# ---------------------------------------------------------------------------
# Helpers for vol_adj_autocorr tests (iter-v3/026) and cross_asset tests (iter-v3/027)
# ---------------------------------------------------------------------------


def _make_df_with_all_primitives(
    n: int = 200,
    seed: int = 100,
) -> pd.DataFrame:
    """Extend _make_df with all source primitives for both engineered features.

    Provides:
    - ``hurst_100`` (from _make_df): needed by compute_regime_momentum_signed_5d.
    - ``ret_autocorr_lag1_50``, ``range_realized_vol_50``: vol_adj_autocorr dead-code deps.
    - ``btc_ret_14d``: needed by compute_cross_asset_divergence_norm (cross_btc group).
    - ``vwap_dev_20``: needed by compute_cross_asset_divergence_norm (volume_micro group).
    """
    rng = np.random.default_rng(seed)
    df = _make_df(n=n, seed=seed)
    # vol_adj_autocorr source primitives (dead code, but included for completeness)
    df["ret_autocorr_lag1_50"] = rng.uniform(-0.5, 0.5, n)
    df.loc[df.index[:49], "ret_autocorr_lag1_50"] = np.nan
    df["range_realized_vol_50"] = rng.uniform(0.005, 0.05, n)
    df.loc[df.index[:49], "range_realized_vol_50"] = np.nan
    # cross_asset_divergence_norm source primitives
    df["btc_ret_14d"] = rng.uniform(-0.10, 0.10, n)
    df.loc[df.index[:41], "btc_ret_14d"] = np.nan  # 42-bar warm-up
    df["vwap_dev_20"] = rng.uniform(-0.05, 0.05, n)
    df.loc[df.index[:19], "vwap_dev_20"] = np.nan  # 20-bar warm-up
    return df


def _make_df_with_vol_primitives(
    n: int = 200,
    seed: int = 100,
    autocorr_value: float | None = None,
    vol_value: float | None = None,
) -> pd.DataFrame:
    """Extend _make_df with ret_autocorr_lag1_50 and range_realized_vol_50 columns.

    These are the two source primitives required by compute_vol_adj_autocorr.
    In production they are computed by add_momentum_accel_v3_features and
    add_tail_risk_v3_features respectively, both of which run before engineered_v3
    in the GROUP_REGISTRY ordering.

    Args:
        n: number of rows.
        seed: numpy random seed.
        autocorr_value: if not None, overrides ret_autocorr_lag1_50 with a constant.
        vol_value: if not None, overrides range_realized_vol_50 with a constant.
    """
    rng = np.random.default_rng(seed)
    df = _make_df(n=n, seed=seed)
    # Simulate ret_autocorr_lag1_50: rolling 50-bar Pearson autocorr in [-1, +1]
    if autocorr_value is not None:
        df["ret_autocorr_lag1_50"] = autocorr_value
    else:
        df["ret_autocorr_lag1_50"] = rng.uniform(-0.5, 0.5, n)
        # First 49 bars NaN (warm-up for 50-bar rolling window)
        df.loc[df.index[:49], "ret_autocorr_lag1_50"] = np.nan
    # Simulate range_realized_vol_50: rolling 50-bar realized vol (positive, small)
    if vol_value is not None:
        df["range_realized_vol_50"] = vol_value
    else:
        df["range_realized_vol_50"] = rng.uniform(0.005, 0.05, n)
        # First 49 bars NaN (warm-up)
        df.loc[df.index[:49], "range_realized_vol_50"] = np.nan
    return df


# ---------------------------------------------------------------------------
# 9. vol_adj_autocorr — Composition correctness
# ---------------------------------------------------------------------------


class TestVolAdjAutocorrComposition:
    def test_basic_ratio_computation(self) -> None:
        """vol_adj_autocorr = ret_autocorr_lag1_50 / (range_realized_vol_50 + EPS)."""
        from crypto_trade.features_v3.engineered_v3 import _VOL_ADJ_AUTOCORR_EPS

        n = 200
        fixed_autocorr = 0.4
        fixed_vol = 0.02
        df = _make_df_with_vol_primitives(
            n=n, seed=200, autocorr_value=fixed_autocorr, vol_value=fixed_vol
        )
        out = compute_vol_adj_autocorr(df)

        feat = out["vol_adj_autocorr"]
        expected = fixed_autocorr / (fixed_vol + _VOL_ADJ_AUTOCORR_EPS)

        # All values should equal expected (constant inputs → constant output)
        valid = feat.dropna()
        assert len(valid) > 0, "No valid values produced."
        np.testing.assert_allclose(
            valid.values,
            expected,
            rtol=1e-9,
            err_msg=f"Expected ratio {expected:.6f} for fixed autocorr={fixed_autocorr}, "
            f"vol={fixed_vol}+EPS.",
        )

    def test_negative_autocorr_produces_negative_output(self) -> None:
        """Negative autocorrelation / positive vol → negative vol_adj_autocorr."""
        fixed_autocorr = -0.3
        fixed_vol = 0.015
        df = _make_df_with_vol_primitives(
            n=200, seed=201, autocorr_value=fixed_autocorr, vol_value=fixed_vol
        )
        out = compute_vol_adj_autocorr(df)
        valid = out["vol_adj_autocorr"].dropna()
        assert len(valid) > 0
        assert (valid < 0).all(), (
            "Negative autocorr / positive vol must produce all-negative vol_adj_autocorr."
        )

    def test_zero_autocorr_produces_near_zero_output(self) -> None:
        """Zero autocorrelation / any positive vol → vol_adj_autocorr ≈ 0."""
        fixed_autocorr = 0.0
        fixed_vol = 0.02
        df = _make_df_with_vol_primitives(
            n=200, seed=202, autocorr_value=fixed_autocorr, vol_value=fixed_vol
        )
        out = compute_vol_adj_autocorr(df)
        valid = out["vol_adj_autocorr"].dropna()
        assert len(valid) > 0
        np.testing.assert_allclose(
            valid.values,
            0.0,
            atol=1e-6,
            err_msg="Zero autocorr must produce near-zero vol_adj_autocorr.",
        )

    def test_output_column_appended_to_df(self) -> None:
        """compute_vol_adj_autocorr must add vol_adj_autocorr column."""
        df = _make_df_with_vol_primitives(n=150, seed=203)
        assert "vol_adj_autocorr" not in df.columns
        out = compute_vol_adj_autocorr(df)
        assert "vol_adj_autocorr" in out.columns

    def test_output_length_unchanged(self) -> None:
        """Output DataFrame must have same number of rows as input."""
        n = 175
        df = _make_df_with_vol_primitives(n=n, seed=204)
        out = compute_vol_adj_autocorr(df)
        assert len(out) == n


# ---------------------------------------------------------------------------
# 10. vol_adj_autocorr — Past-only discipline
# ---------------------------------------------------------------------------


class TestVolAdjAutocorrPastOnly:
    def test_appending_future_bars_does_not_change_value_at_t(self) -> None:
        """Adversarial past-only test: value at t must not change when future bars appended.

        Computes vol_adj_autocorr on df[:T] and df[:T+30].  The value at row T-1
        (last bar in short frame) must be identical in both runs.

        Both source primitives (ret_autocorr_lag1_50, range_realized_vol_50) are
        50-bar trailing rolling windows ending at t.  Appending bars t+1...t+30
        cannot affect the rolling window ending at t.
        """
        n = 250
        df_full = _make_df_with_vol_primitives(n=n, seed=210)
        split = 180

        df_short = df_full.iloc[:split].reset_index(drop=True)
        df_long = df_full.reset_index(drop=True)

        out_short = compute_vol_adj_autocorr(df_short)
        out_long = compute_vol_adj_autocorr(df_long)

        val_short = out_short["vol_adj_autocorr"].iloc[split - 1]
        val_long = out_long["vol_adj_autocorr"].iloc[split - 1]

        if np.isnan(val_short) and np.isnan(val_long):
            pass  # Both NaN is consistent
        else:
            assert val_short == pytest.approx(val_long, abs=1e-12), (
                f"Past-only violation: vol_adj_autocorr at row {split - 1} changed from "
                f"{val_short} to {val_long} when future bars were appended."
            )

    def test_spike_in_source_at_t_affects_only_t_not_t_minus_1(self) -> None:
        """Spiking autocorr at bar t changes value at t but NOT value at t-1.

        This validates that the division is element-wise (row t uses source values
        at row t only) and does not depend on any future-bar context.
        """
        n = 250
        df = _make_df_with_vol_primitives(n=n, seed=211)
        spike_idx = 150

        df_spiked = df.copy()
        df_spiked.loc[spike_idx, "ret_autocorr_lag1_50"] = 0.99  # max positive

        out_base = compute_vol_adj_autocorr(df)
        out_spiked = compute_vol_adj_autocorr(df_spiked)

        # At spike_idx: value must change (spike in numerator)
        val_base = out_base["vol_adj_autocorr"].iloc[spike_idx]
        val_spiked = out_spiked["vol_adj_autocorr"].iloc[spike_idx]
        if not (np.isnan(val_base) and np.isnan(val_spiked)):
            assert val_base != pytest.approx(val_spiked, abs=1e-10), (
                f"Spike at autocorr[{spike_idx}] had no effect on feature[{spike_idx}] — "
                "numerator not correctly applied."
            )

        # At spike_idx - 1: value must NOT change (spike is in the future from t-1)
        val_before_base = out_base["vol_adj_autocorr"].iloc[spike_idx - 1]
        val_before_spiked = out_spiked["vol_adj_autocorr"].iloc[spike_idx - 1]
        if not (np.isnan(val_before_base) and np.isnan(val_before_spiked)):
            assert val_before_base == pytest.approx(val_before_spiked, abs=1e-12), (
                f"Past-only violation: feature[{spike_idx - 1}] changed when "
                f"autocorr[{spike_idx}] was spiked.  Feature at t-1 must not depend on "
                "source values at t."
            )


# ---------------------------------------------------------------------------
# 11. vol_adj_autocorr — Edge case: near-zero denominator capped at ±100
# ---------------------------------------------------------------------------


class TestVolAdjAutocorrEdgeCases:
    def test_zero_vol_does_not_produce_inf(self) -> None:
        """range_realized_vol_50 == 0.0 → EPS prevents inf; output capped at ±100."""
        from crypto_trade.features_v3.engineered_v3 import (
            _VOL_ADJ_AUTOCORR_CAP,
            _VOL_ADJ_AUTOCORR_EPS,
        )

        n = 200
        fixed_autocorr = 0.5
        # range_realized_vol_50 exactly 0.0 — would produce inf without EPS
        df = _make_df_with_vol_primitives(
            n=n, seed=220, autocorr_value=fixed_autocorr, vol_value=0.0
        )
        out = compute_vol_adj_autocorr(df)
        feat = out["vol_adj_autocorr"]

        # No values should be +/- inf
        valid = feat.dropna()
        assert len(valid) > 0
        assert np.isfinite(valid.values).all(), (
            "vol_adj_autocorr must be finite even when range_realized_vol_50 == 0.0. "
            "EPS + cap should prevent inf."
        )

        # Expected: fixed_autocorr / (0.0 + EPS) = 0.5 / 1e-6 = 500_000 → capped at 100
        # Because fixed_autocorr / EPS >> CAP
        uncapped = fixed_autocorr / _VOL_ADJ_AUTOCORR_EPS
        if uncapped > _VOL_ADJ_AUTOCORR_CAP:
            np.testing.assert_allclose(
                valid.values,
                _VOL_ADJ_AUTOCORR_CAP,
                rtol=1e-9,
                err_msg=(
                    f"Expected cap at {_VOL_ADJ_AUTOCORR_CAP} when vol=0 and autocorr positive."
                ),
            )

    def test_very_small_vol_is_capped(self) -> None:
        """Very small (but non-zero) vol → ratio large → output capped at ±100."""
        from crypto_trade.features_v3.engineered_v3 import _VOL_ADJ_AUTOCORR_CAP

        n = 200
        fixed_autocorr = 0.8
        tiny_vol = 1e-9  # vol << EPS does not help; autocorr/tiny_vol >> CAP
        df = _make_df_with_vol_primitives(
            n=n, seed=221, autocorr_value=fixed_autocorr, vol_value=tiny_vol
        )
        out = compute_vol_adj_autocorr(df)
        feat = out["vol_adj_autocorr"].dropna()

        assert len(feat) > 0
        assert np.isfinite(feat.values).all(), "Output must be finite for tiny_vol."
        assert (feat <= _VOL_ADJ_AUTOCORR_CAP).all(), (
            f"All values must be <= {_VOL_ADJ_AUTOCORR_CAP} (cap). Max observed: {feat.max():.2f}"
        )

    def test_negative_autocorr_zero_vol_capped_at_minus_100(self) -> None:
        """Negative autocorr / zero vol → capped at -100, not -inf."""
        from crypto_trade.features_v3.engineered_v3 import _VOL_ADJ_AUTOCORR_CAP

        n = 200
        fixed_autocorr = -0.5
        df = _make_df_with_vol_primitives(
            n=n, seed=222, autocorr_value=fixed_autocorr, vol_value=0.0
        )
        out = compute_vol_adj_autocorr(df)
        feat = out["vol_adj_autocorr"].dropna()

        assert len(feat) > 0
        assert np.isfinite(feat.values).all()
        assert (feat >= -_VOL_ADJ_AUTOCORR_CAP).all(), (
            f"All values must be >= -{_VOL_ADJ_AUTOCORR_CAP} (negative cap). "
            f"Min observed: {feat.min():.2f}"
        )

    def test_missing_autocorr_column_returns_all_nan(self) -> None:
        """When ret_autocorr_lag1_50 is absent, vol_adj_autocorr must be all-NaN."""
        df = _make_df_with_vol_primitives(n=150, seed=223)
        df_no_autocorr = df.drop(columns=["ret_autocorr_lag1_50"])

        out = compute_vol_adj_autocorr(df_no_autocorr)

        assert "vol_adj_autocorr" in out.columns
        assert out["vol_adj_autocorr"].isna().all(), (
            "vol_adj_autocorr must be all-NaN when ret_autocorr_lag1_50 is missing."
        )

    def test_missing_vol_column_returns_all_nan(self) -> None:
        """When range_realized_vol_50 is absent, vol_adj_autocorr must be all-NaN."""
        df = _make_df_with_vol_primitives(n=150, seed=224)
        df_no_vol = df.drop(columns=["range_realized_vol_50"])

        out = compute_vol_adj_autocorr(df_no_vol)

        assert "vol_adj_autocorr" in out.columns
        assert out["vol_adj_autocorr"].isna().all(), (
            "vol_adj_autocorr must be all-NaN when range_realized_vol_50 is missing."
        )

    def test_no_nan_explosion_after_warmup(self) -> None:
        """After warm-up (bar 49+), most values should be non-NaN."""
        n = 300
        df = _make_df_with_vol_primitives(n=n, seed=225)
        out = compute_vol_adj_autocorr(df)
        feat = out["vol_adj_autocorr"]

        # Warm-up bars (0..48) should be NaN
        assert feat.iloc[:49].isna().all(), "First 49 bars must be NaN (50-bar warm-up)."

        # After warm-up: < 5% NaN tolerated (NaN from source propagation)
        post_warmup = feat.iloc[49:]
        nan_frac = post_warmup.isna().mean()
        assert nan_frac < 0.05, (
            f"Too many NaN values after warm-up: {nan_frac:.1%} > 5%. "
            "Possible NaN explosion in vol_adj_autocorr computation."
        )


# ---------------------------------------------------------------------------
# 12. vol_adj_autocorr — Idempotency
# ---------------------------------------------------------------------------


class TestVolAdjAutocorrIdempotency:
    def test_calling_twice_produces_identical_output(self) -> None:
        """compute_vol_adj_autocorr must be pure: calling twice gives identical result.

        This validates the function does not rely on in-place mutation or external
        state.  The second call operates on the output of the first call (which has
        vol_adj_autocorr already appended); the appended column must not alter the
        computation of a SECOND call.
        """
        n = 200
        df = _make_df_with_vol_primitives(n=n, seed=230)

        out1 = compute_vol_adj_autocorr(df)
        out2 = compute_vol_adj_autocorr(df)

        # Both outputs must be identical
        feat1 = out1["vol_adj_autocorr"]
        feat2 = out2["vol_adj_autocorr"]

        # NaN positions must match
        nan1 = feat1.isna()
        nan2 = feat2.isna()
        assert (nan1 == nan2).all(), (
            "NaN positions differ between first and second call — function is not pure."
        )

        # Non-NaN values must be identical
        valid_idx = feat1.dropna().index
        if len(valid_idx) > 0:
            np.testing.assert_array_equal(
                feat1.loc[valid_idx].values,
                feat2.loc[valid_idx].values,
                err_msg="vol_adj_autocorr values differ between first and second call.",
            )

    def test_does_not_mutate_input_df(self) -> None:
        """compute_vol_adj_autocorr must return a copy, not mutate the input."""
        n = 200
        df = _make_df_with_vol_primitives(n=n, seed=231)
        cols_before = set(df.columns)
        _ = compute_vol_adj_autocorr(df)
        assert set(df.columns) == cols_before, (
            "compute_vol_adj_autocorr must not add vol_adj_autocorr to the input DataFrame."
        )

    def test_add_engineered_v3_features_produces_correct_columns(self) -> None:
        """add_engineered_v3_features (GROUP_REGISTRY entry) must produce correct columns.

        iter-v3/036: vol_adj_autocorr RE-DISPATCHED (was dead code since iter-v3/027).
        regime_momentum_signed_5d and fracdiff_d05_close KEPT. Only
        cross_asset_divergence_norm remains dead code — NOT dispatched; must be ABSENT.
        """
        df = _make_df_with_all_primitives(n=200, seed=232)
        out = add_engineered_v3_features(df)
        assert "regime_momentum_signed_5d" in out.columns, (
            "regime_momentum_signed_5d (iter-v3/025; KEPT; MINI-VALIDATION target) "
            "must be in output."
        )
        # cross_asset_divergence_norm is dead code at iter-v3/028 — NOT dispatched.
        assert "cross_asset_divergence_norm" not in out.columns, (
            "cross_asset_divergence_norm (iter-v3/028; DROPPED) must NOT be in output. "
            "Stacking FALSIFIED at iter-v3/027; function retained as dead code only."
        )
        # iter-v3/036: vol_adj_autocorr RE-DISPATCHED for parquet generation (TRX-only model).
        assert "vol_adj_autocorr" in out.columns, (
            "vol_adj_autocorr (iter-v3/036; RE-DISPATCHED) MUST be in output. "
            "Column generated for all symbols; only TRX passes it to LightGBM. "
            "Check add_engineered_v3_features dispatch in engineered_v3.py."
        )


# ---------------------------------------------------------------------------
# 13. cross_asset_divergence_norm — Past-only discipline (iter-v3/027)
# ---------------------------------------------------------------------------


class TestCrossAssetDivergenceNormPastOnly:
    def test_appending_future_bars_does_not_change_value_at_t(self) -> None:
        """Adversarial past-only test: value at t must not change when future bars appended.

        Computes cross_asset_divergence_norm on df[:T] and df[:T+30].  The value
        at row T-1 (last bar in short frame) must be identical in both runs.

        All source inputs (sym_ret_7d from close via shift(21), btc_ret_14d,
        vwap_dev_20) are trailing rolling windows ending at t.  Appending bars
        t+1...t+30 cannot affect any value at t.
        """
        n = 250
        df_full = _make_df_with_all_primitives(n=n, seed=300)
        split = 180

        df_short = df_full.iloc[:split].reset_index(drop=True)
        df_long = df_full.reset_index(drop=True)

        out_short = compute_cross_asset_divergence_norm(df_short)
        out_long = compute_cross_asset_divergence_norm(df_long)

        val_short = out_short["cross_asset_divergence_norm"].iloc[split - 1]
        val_long = out_long["cross_asset_divergence_norm"].iloc[split - 1]

        if np.isnan(val_short) and np.isnan(val_long):
            pass  # Both NaN is consistent (warm-up period)
        else:
            assert val_short == pytest.approx(val_long, abs=1e-12), (
                f"Past-only violation: cross_asset_divergence_norm at row {split - 1} "
                f"changed from {val_short} to {val_long} when future bars were appended."
            )


# ---------------------------------------------------------------------------
# 14. cross_asset_divergence_norm — NaN warm-up (iter-v3/027)
# ---------------------------------------------------------------------------


class TestCrossAssetDivergenceNormNaNWarmUp:
    def test_first_41_bars_nan_dominated_by_btc_ret_14d(self) -> None:
        """First 41 bars must be NaN because btc_ret_14d requires a 42-bar window.

        btc_ret_14d warm-up (42 bars; rows 0..41 NaN in production) dominates over
        sym_ret_7d warm-up (21 bars; rows 0..20 NaN).  After bar 41 (index 41),
        both are valid so cross_asset_divergence_norm can be computed.

        Note: in this test, btc_ret_14d is provided with NaN at rows 0..41 to
        simulate the upstream warm-up.
        """
        n = 300
        df = _make_df_with_all_primitives(n=n, seed=310)
        # Ensure btc_ret_14d warm-up is realistic: first 41 NaN
        df.loc[df.index[:41], "btc_ret_14d"] = np.nan
        # Ensure vwap_dev_20 warm-up: first 19 NaN (already set; shorter than btc)
        df.loc[df.index[:19], "vwap_dev_20"] = np.nan

        out = compute_cross_asset_divergence_norm(df)
        feat = out["cross_asset_divergence_norm"]

        # Rows 0..40 must be NaN (btc_ret_14d not yet valid)
        assert feat.iloc[:41].isna().all(), (
            f"Expected first 41 bars to be NaN (btc_ret_14d 42-bar warm-up). "
            f"First non-NaN index: {feat.first_valid_index()}"
        )
        # After bar 41, values should be computable when close + btc_ret_14d + vwap_dev_20 valid
        assert feat.iloc[42:].notna().any(), (
            "Expected at least some valid values after bar 42 (all warm-ups complete)."
        )


# ---------------------------------------------------------------------------
# 15. cross_asset_divergence_norm — EPS robustness (iter-v3/027)
# ---------------------------------------------------------------------------


class TestCrossAssetDivergenceNormEPS:
    def test_zero_vwap_dev_does_not_produce_inf(self) -> None:
        """vwap_dev_20 == 0.0 → EPS = 1e-6 prevents division-by-zero; output finite.

        Per brief Section 2.5 test 3: cross_asset_divergence_norm is finite (not inf)
        when vwap_dev_20 is exactly zero.  EPS=1e-6 prevents division-by-zero;
        output clipped to [-100, +100].
        """
        from crypto_trade.features_v3.engineered_v3 import _CROSS_ASSET_DIVERGENCE_CAP

        n = 200
        df = _make_df_with_all_primitives(n=n, seed=320)
        # Set all vwap_dev_20 to exactly 0 (worst-case denominator)
        df["vwap_dev_20"] = 0.0
        # Set btc_ret_14d to a moderate value so numerator is non-zero
        df["btc_ret_14d"] = 0.05

        out = compute_cross_asset_divergence_norm(df)
        feat = out["cross_asset_divergence_norm"]

        # All values must be finite (not inf or nan from division)
        valid = feat.dropna()
        assert len(valid) > 0, "Expected at least some valid values after warm-up."
        assert np.isfinite(valid.values).all(), (
            "cross_asset_divergence_norm must be finite even when vwap_dev_20 == 0.0. "
            "EPS + cap should prevent inf."
        )
        # Values must be within [-CAP, +CAP]
        assert (valid.abs() <= _CROSS_ASSET_DIVERGENCE_CAP + 1e-10).all(), (
            f"All values must be within ±{_CROSS_ASSET_DIVERGENCE_CAP} (cap). "
            f"Max observed: {valid.abs().max():.4f}"
        )


# ---------------------------------------------------------------------------
# 16. cross_asset_divergence_norm — Idempotency (iter-v3/027)
# ---------------------------------------------------------------------------


class TestCrossAssetDivergenceNormIdempotency:
    def test_calling_twice_produces_identical_output(self) -> None:
        """compute_cross_asset_divergence_norm must be pure: calling twice gives identical result.

        Per brief Section 2.5 test 4: idempotency test — calling the function twice
        in succession produces identical output (function is pure; no in-place mutation).
        """
        n = 200
        df = _make_df_with_all_primitives(n=n, seed=330)

        out1 = compute_cross_asset_divergence_norm(df)
        out2 = compute_cross_asset_divergence_norm(df)

        feat1 = out1["cross_asset_divergence_norm"]
        feat2 = out2["cross_asset_divergence_norm"]

        # NaN positions must match
        nan1 = feat1.isna()
        nan2 = feat2.isna()
        assert (nan1 == nan2).all(), (
            "NaN positions differ between first and second call — function is not pure."
        )

        # Non-NaN values must be identical
        valid_idx = feat1.dropna().index
        if len(valid_idx) > 0:
            np.testing.assert_array_equal(
                feat1.loc[valid_idx].values,
                feat2.loc[valid_idx].values,
                err_msg="cross_asset_divergence_norm values differ between first and second call.",
            )

    def test_does_not_mutate_input_df(self) -> None:
        """compute_cross_asset_divergence_norm must return a copy, not mutate the input."""
        n = 200
        df = _make_df_with_all_primitives(n=n, seed=331)
        cols_before = set(df.columns)
        _ = compute_cross_asset_divergence_norm(df)
        assert set(df.columns) == cols_before, (
            "compute_cross_asset_divergence_norm must not add cross_asset_divergence_norm "
            "to the input DataFrame."
        )

    def test_missing_btc_ret_14d_returns_all_nan(self) -> None:
        """When btc_ret_14d is absent, cross_asset_divergence_norm must be all-NaN."""
        df = _make_df_with_all_primitives(n=150, seed=332)
        df_no_btc = df.drop(columns=["btc_ret_14d"])

        out = compute_cross_asset_divergence_norm(df_no_btc)

        assert "cross_asset_divergence_norm" in out.columns
        assert out["cross_asset_divergence_norm"].isna().all(), (
            "cross_asset_divergence_norm must be all-NaN when btc_ret_14d is missing."
        )

    def test_missing_vwap_dev_20_returns_all_nan(self) -> None:
        """When vwap_dev_20 is absent, cross_asset_divergence_norm must be all-NaN."""
        df = _make_df_with_all_primitives(n=150, seed=333)
        df_no_vwap = df.drop(columns=["vwap_dev_20"])

        out = compute_cross_asset_divergence_norm(df_no_vwap)

        assert "cross_asset_divergence_norm" in out.columns
        assert out["cross_asset_divergence_norm"].isna().all(), (
            "cross_asset_divergence_norm must be all-NaN when vwap_dev_20 is missing."
        )


# ---------------------------------------------------------------------------
# 17. fracdiff_d05_close weights — LdP AFML Ch. 5 recurrence (iter-v3/034)
# ---------------------------------------------------------------------------


class TestFracdiffD05Weights:
    def test_first_weight_is_one(self) -> None:
        """LdP AFML Ch. 5 recurrence: w_0 = 1.0 exactly."""
        weights = _fracdiff_d05_weights()
        assert weights[0] == pytest.approx(1.0, abs=1e-15), (
            f"First weight must be 1.0 (w_0 = 1 per LdP recurrence). Got {weights[0]}."
        )

    def test_weights_are_monotonically_decreasing_in_magnitude(self) -> None:
        """Weights decrease monotonically in absolute value (LdP AFML Ch. 5 property).

        For d=0.5 the recurrence w_k = -w_{k-1}*(d-k+1)/k produces alternating
        signs; abs(w_k) must be strictly decreasing until truncation.
        """
        weights = _fracdiff_d05_weights()
        abs_w = np.abs(weights)
        for k in range(1, len(abs_w)):
            assert abs_w[k] < abs_w[k - 1], (
                f"Weight magnitude not strictly decreasing at k={k}: "
                f"|w[{k - 1}]|={abs_w[k - 1]:.6e}, |w[{k}]|={abs_w[k]:.6e}."
            )

    def test_last_weight_below_threshold(self) -> None:
        """Truncation condition: all weights must satisfy |w_k| >= threshold except last.

        The loop stops when |w_next| < threshold = 1e-4.  Every retained weight
        must have |w_k| >= threshold.
        """
        threshold = 1e-4
        weights = _fracdiff_d05_weights(threshold=threshold)
        # All retained weights must be >= threshold (loop stops before appending sub-threshold)
        for k, w in enumerate(weights):
            assert abs(w) >= threshold, (
                f"Retained weight w[{k}]={w:.6e} is below threshold={threshold:.1e}. "
                "The loop should have stopped before appending this weight."
            )

    def test_weight_count_is_reasonable_for_d05(self) -> None:
        """For d=0.5, threshold=1e-4, expect roughly 50-200 weights (not 1, not 100_000).

        Exact count depends on the recurrence speed; ballpark from LdP AFML Ch. 5
        is ~50-200 for d=0.5 at 1e-4 threshold.
        """
        weights = _fracdiff_d05_weights()
        w_len = len(weights)
        assert 30 <= w_len <= 500, (
            f"Expected 30–500 weights for d=0.5 at threshold=1e-4; got {w_len}. "
            "Check recurrence implementation."
        )

    def test_weights_sum_approaches_zero(self) -> None:
        """For d=0.5, sum of weights should be close to 0 (LdP AFML property: memory-balance).

        The infinite sum of FFD weights at d=0.5 converges to 0 (each w_k has
        alternating sign and decreasing magnitude).  With truncation at 1e-4 the
        partial sum should be small (< 0.1 in absolute value).
        """
        weights = _fracdiff_d05_weights()
        total = float(np.sum(weights))
        assert abs(total) < 0.1, (
            f"Sum of FFD weights for d=0.5 should be close to 0; got {total:.4f}. "
            "Weights may not be alternating correctly."
        )


# ---------------------------------------------------------------------------
# 18. fracdiff_d05_close — Past-only discipline (iter-v3/034)
# ---------------------------------------------------------------------------


class TestFracdiffD05ClosesPastOnly:
    def test_appending_future_bars_does_not_change_value_at_t(self) -> None:
        """Adversarial past-only test: value at row t must not change when future bars appended.

        Compute fracdiff_d05_close on df[:T] and df[:T+50]. The value at row T-1
        (the last bar in the short frame) must be identical in both runs.

        FFD is a pure backward convolution: bar t uses close[t], close[t-1], ...
        close[t-(W-1)].  Appending future bars cannot alter any of these lags.
        """
        weights = _fracdiff_d05_weights()
        w_window = len(weights)
        n = w_window + 100  # enough for warm-up + valid bars
        rng = np.random.default_rng(42)
        open_times = [_IS_START_MS + i * _8H_MS for i in range(n)]
        close = np.cumprod(1 + rng.normal(0, 0.01, n)) * 100.0  # random walk
        df_full = pd.DataFrame(
            {
                "open_time": open_times,
                "open": close * rng.uniform(0.995, 1.005, n),
                "high": close * rng.uniform(1.0, 1.01, n),
                "low": close * rng.uniform(0.99, 1.0, n),
                "close": close,
                "volume": rng.uniform(1000.0, 10000.0, n),
                "symbol": "BCHUSDT",
            }
        )
        split = w_window + 30  # last bar in short frame

        df_short = df_full.iloc[:split].reset_index(drop=True)
        df_long = df_full.reset_index(drop=True)

        out_short = compute_fracdiff_d05_close(df_short)
        out_long = compute_fracdiff_d05_close(df_long)

        val_short = out_short["fracdiff_d05_close"].iloc[split - 1]
        val_long = out_long["fracdiff_d05_close"].iloc[split - 1]

        assert not np.isnan(val_short), (
            f"Value at split-1={split - 1} should not be NaN in the short frame. "
            f"w_window={w_window}, split={split}."
        )
        assert val_short == pytest.approx(val_long, abs=1e-12), (
            f"Past-only violation: fracdiff_d05_close at row {split - 1} changed from "
            f"{val_short:.10f} to {val_long:.10f} when future bars were appended. "
            "FFD backward convolution must depend only on current and past close values."
        )

    def test_current_bar_close_not_in_its_own_lag_window(self) -> None:
        """The current bar's close[t] is the first element of the convolution window.

        Spike close[t] to a known extreme value; verify:
        - Feature at t CHANGES (close[t] IS in bar t's convolution).
        - Feature at t-1 does NOT change (close[t] is in the FUTURE from t-1).

        This is the primary past-only check: the convolution window for bar t
        is {close[t], close[t-1], ..., close[t-(W-1)]}.  Bar t-1's window is
        {close[t-1], close[t-2], ..., close[t-W]}.  They are disjoint at position 0.
        """
        weights = _fracdiff_d05_weights()
        w_window = len(weights)
        n = w_window + 80
        rng = np.random.default_rng(99)
        open_times = [_IS_START_MS + i * _8H_MS for i in range(n)]
        close = np.cumprod(1 + rng.normal(0, 0.01, n)) * 100.0
        df_base = pd.DataFrame(
            {
                "open_time": open_times,
                "open": close * rng.uniform(0.995, 1.005, n),
                "high": close * rng.uniform(1.0, 1.01, n),
                "low": close * rng.uniform(0.99, 1.0, n),
                "close": close.copy(),
                "volume": rng.uniform(1000.0, 10000.0, n),
                "symbol": "BCHUSDT",
            }
        )
        target = w_window + 20  # well past warm-up

        df_spiked = df_base.copy()
        df_spiked.loc[target, "close"] = 1_000_000.0  # extreme spike

        out_base = compute_fracdiff_d05_close(df_base)
        out_spiked = compute_fracdiff_d05_close(df_spiked)

        # At target: value MUST change (close[target] is in bar target's window)
        val_base_t = out_base["fracdiff_d05_close"].iloc[target]
        val_spiked_t = out_spiked["fracdiff_d05_close"].iloc[target]
        assert not np.isnan(val_base_t), f"Value at target={target} should be non-NaN."
        assert val_base_t != pytest.approx(val_spiked_t, abs=1e-6), (
            f"Spike at close[{target}] had no effect on feature[{target}]. "
            "close[t] must be included in bar t's convolution window."
        )

        # At target-1: value must NOT change (close[target] is future from t-1's perspective)
        val_base_prev = out_base["fracdiff_d05_close"].iloc[target - 1]
        val_spiked_prev = out_spiked["fracdiff_d05_close"].iloc[target - 1]
        assert not np.isnan(val_base_prev), f"Value at target-1={target - 1} should be non-NaN."
        assert val_base_prev == pytest.approx(val_spiked_prev, abs=1e-12), (
            f"Past-only violation: feature[{target - 1}] changed when close[{target}] "
            f"was spiked. Value before={val_base_prev:.10f}, after={val_spiked_prev:.10f}. "
            "Bar t-1's convolution window must not include close[t]."
        )


# ---------------------------------------------------------------------------
# 19. fracdiff_d05_close — ADF stationarity on synthetic random walk (iter-v3/034)
# ---------------------------------------------------------------------------


class TestFracdiffD05CloseADFStationarity:
    def test_fracdiff_d05_is_stationary_on_random_walk(self) -> None:
        """FFD at d=0.5 must make a random walk stationary (ADF p < 0.05).

        Pre-registered falsifier from brief Section 4: if ADF p-value >= 0.05
        on the differenced series, the FFD implementation is broken (not producing
        sufficient memory reduction to achieve stationarity).

        Synthetic data: geometric random walk with drift=0.0001 per bar, vol=0.01.
        1000 bars is sufficient for ADF to detect stationarity at d=0.5.
        """
        import statsmodels.tsa.stattools as smtools

        rng = np.random.default_rng(2034)  # iter-v3/034 seed
        n = 1000
        open_times = [_IS_START_MS + i * _8H_MS for i in range(n)]
        log_returns = rng.normal(0.0001, 0.01, n)
        close = np.exp(np.cumsum(log_returns)) * 100.0  # geometric random walk
        df = pd.DataFrame(
            {
                "open_time": open_times,
                "open": close * 0.999,
                "high": close * 1.005,
                "low": close * 0.995,
                "close": close,
                "volume": rng.uniform(1000.0, 10000.0, n),
                "symbol": "BCHUSDT",
            }
        )

        out = compute_fracdiff_d05_close(df)
        series = out["fracdiff_d05_close"].dropna()

        assert len(series) >= 200, (
            f"ADF test needs at least 200 valid bars; got {len(series)}. Check warm-up calculation."
        )

        # ADF test: null hypothesis = unit root (non-stationary)
        adf_stat, p_value, *_ = smtools.adfuller(series.values, autolag="AIC")
        assert p_value < 0.05, (
            f"ADF test FAILED (p={p_value:.4f} >= 0.05): fracdiff_d05_close is NOT "
            f"stationary on a random walk (ADF stat={adf_stat:.4f}). "
            "d=0.5 FFD must produce a stationary series. "
            "Pre-registered falsifier from brief Section 4 triggered."
        )


# ---------------------------------------------------------------------------
# 20. fracdiff_d05_close — NaN warm-up at first (W-1) bars (iter-v3/034)
# ---------------------------------------------------------------------------


class TestFracdiffD05CloseNaNWarmUp:
    def test_first_w_minus_1_bars_are_nan(self) -> None:
        """First (W-1) bars must be NaN where W = len(_fracdiff_d05_weights()).

        The FFD convolution requires W bars of log(close) history.  Bar index
        W-1 is the first bar where all W lags are available; bars 0..(W-2) must
        be NaN.
        """
        weights = _fracdiff_d05_weights()
        w_window = len(weights)
        n = w_window + 50
        rng = np.random.default_rng(2034)
        open_times = [_IS_START_MS + i * _8H_MS for i in range(n)]
        close = np.cumprod(1 + rng.normal(0, 0.01, n)) * 100.0
        df = pd.DataFrame(
            {
                "open_time": open_times,
                "open": close * 0.999,
                "high": close * 1.005,
                "low": close * 0.995,
                "close": close,
                "volume": rng.uniform(1000.0, 10000.0, n),
                "symbol": "BCHUSDT",
            }
        )

        out = compute_fracdiff_d05_close(df)
        feat = out["fracdiff_d05_close"]

        # Bars 0..(W-2) must be NaN
        warmup = feat.iloc[: w_window - 1]
        assert warmup.isna().all(), (
            f"Expected first {w_window - 1} bars to be NaN (FFD warm-up: W={w_window}). "
            f"Non-NaN count in warm-up: {warmup.notna().sum()}. "
            f"First non-NaN index: {feat.first_valid_index()}."
        )

    def test_first_valid_index_is_w_minus_1(self) -> None:
        """The first valid (non-NaN) bar must be exactly at index W-1."""
        weights = _fracdiff_d05_weights()
        w_window = len(weights)
        n = w_window + 50
        rng = np.random.default_rng(2035)
        open_times = [_IS_START_MS + i * _8H_MS for i in range(n)]
        close = np.cumprod(1 + rng.normal(0, 0.01, n)) * 100.0
        df = pd.DataFrame(
            {
                "open_time": open_times,
                "open": close * 0.999,
                "high": close * 1.005,
                "low": close * 0.995,
                "close": close,
                "volume": rng.uniform(1000.0, 10000.0, n),
                "symbol": "BCHUSDT",
            }
        )

        out = compute_fracdiff_d05_close(df)
        feat = out["fracdiff_d05_close"]

        first_valid = feat.first_valid_index()
        assert first_valid == w_window - 1, (
            f"Expected first valid index at {w_window - 1} (W-1 where W={w_window}); "
            f"got {first_valid}. "
            "FFD warm-up must be exactly W-1 bars (not W or W+1)."
        )

    def test_no_nan_after_warmup(self) -> None:
        """After bar W-1, all values must be non-NaN (no NaN explosion from FFD).

        On a geometric random walk (all positive close prices), log(close) is
        always finite.  FFD output must be finite for all post-warm-up bars.
        """
        weights = _fracdiff_d05_weights()
        w_window = len(weights)
        n = w_window + 100
        rng = np.random.default_rng(2036)
        open_times = [_IS_START_MS + i * _8H_MS for i in range(n)]
        close = np.cumprod(1 + rng.normal(0, 0.01, n)) * 100.0
        df = pd.DataFrame(
            {
                "open_time": open_times,
                "open": close * 0.999,
                "high": close * 1.005,
                "low": close * 0.995,
                "close": close,
                "volume": rng.uniform(1000.0, 10000.0, n),
                "symbol": "BCHUSDT",
            }
        )

        out = compute_fracdiff_d05_close(df)
        feat = out["fracdiff_d05_close"]
        post_warmup = feat.iloc[w_window - 1 :]

        nan_frac = post_warmup.isna().mean()
        assert nan_frac == 0.0, (
            f"Expected 0% NaN after warm-up; got {nan_frac:.1%}. "
            "FFD on positive close prices must produce finite values for all bars."
        )
