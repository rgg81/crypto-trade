"""Adversarial tests for v3 engineered (composed) features — iter-v3/025.

Focuses on ``compute_regime_momentum_signed_5d``:

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
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from crypto_trade.features_v3.engineered_v3 import (
    add_engineered_v3_features,
    compute_regime_momentum_signed_5d,
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
            compute_regime_momentum_signed_5d,
        )

    def test_column_names_exported(self) -> None:
        """Both public symbols must be in __all__."""
        from crypto_trade.features_v3 import engineered_v3

        assert "compute_regime_momentum_signed_5d" in engineered_v3.__all__
        assert "add_engineered_v3_features" in engineered_v3.__all__


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
        """engineered_v3 must be importable from the GROUP_REGISTRY."""
        from crypto_trade.features_v3 import GROUP_REGISTRY

        assert "engineered_v3" in GROUP_REGISTRY, (
            "engineered_v3 must be registered in GROUP_REGISTRY. Check features_v3/__init__.py."
        )
        fn = GROUP_REGISTRY["engineered_v3"]
        # Call it with a valid DataFrame
        df = _make_df(n=200, seed=63)
        out = fn(df)
        assert "regime_momentum_signed_5d" in out.columns
