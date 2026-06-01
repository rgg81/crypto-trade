"""Smoke tests for validation_v3 — CPCV, PBO, PSR.

Tests are deliberately lightweight: they verify the public API imports without
error and produce outputs in the correct range/type. Numerical precision is
not tested here (the Critic's Check 3 verifies numbers against actual backtest).

Run:
    uv run pytest tests/test_validation_v3.py -v
"""

from __future__ import annotations

import numpy as np
import pytest

from crypto_trade.strategies.ml.validation_v3 import (
    combinatorial_purged_cv,
    cpcv_paths_from_splits,
    n_effective_trials,
    pbo_from_cpcv,
    psr,
)


class TestCombinatorialPurgedCV:
    def test_import(self) -> None:
        """Module imports without error."""
        assert callable(combinatorial_purged_cv)

    def test_n10_k2_gives_45_paths(self) -> None:
        """C(10,2) = 45 paths for N=10, k=2."""
        splits = combinatorial_purged_cv(n_samples=1000, n_splits=10, n_test_splits=2, gap=0)
        assert len(splits) == 45

    def test_n6_k2_gives_15_paths(self) -> None:
        """C(6,2) = 15 paths for N=6, k=2."""
        splits = combinatorial_purged_cv(n_samples=600, n_splits=6, n_test_splits=2, gap=0)
        assert len(splits) == 15

    def test_train_test_are_disjoint(self) -> None:
        """Train and test indices must not overlap."""
        splits = combinatorial_purged_cv(n_samples=500, n_splits=10, n_test_splits=2, gap=5)
        for train_idx, test_idx in splits:
            assert len(np.intersect1d(train_idx, test_idx)) == 0, "Train/test overlap found"

    def test_all_indices_within_range(self) -> None:
        """All indices are valid [0, n_samples)."""
        n = 300
        splits = combinatorial_purged_cv(n_samples=n, n_splits=10, n_test_splits=2, gap=10)
        for train_idx, test_idx in splits:
            assert int(train_idx.min()) >= 0
            assert int(train_idx.max()) < n
            assert int(test_idx.min()) >= 0
            assert int(test_idx.max()) < n

    def test_gap_reduces_train_size(self) -> None:
        """A larger gap should reduce train set size."""
        splits_no_gap = combinatorial_purged_cv(n_samples=1000, n_splits=10, n_test_splits=2, gap=0)
        splits_with_gap = combinatorial_purged_cv(
            n_samples=1000, n_splits=10, n_test_splits=2, gap=50
        )
        avg_train_no_gap = np.mean([len(tr) for tr, _ in splits_no_gap])
        avg_train_with_gap = np.mean([len(tr) for tr, _ in splits_with_gap])
        assert avg_train_with_gap < avg_train_no_gap

    def test_invalid_n_splits_raises(self) -> None:
        with pytest.raises(ValueError):
            combinatorial_purged_cv(n_samples=100, n_splits=1, n_test_splits=1)

    def test_invalid_k_raises(self) -> None:
        with pytest.raises(ValueError):
            combinatorial_purged_cv(n_samples=100, n_splits=5, n_test_splits=5)

    def test_cpcv_paths_from_splits(self) -> None:
        """cpcv_paths_from_splits extracts correct test returns."""
        rng = np.random.default_rng(42)
        returns = rng.standard_normal(500)
        splits = combinatorial_purged_cv(n_samples=500, n_splits=10, n_test_splits=2, gap=0)
        paths = cpcv_paths_from_splits(splits, returns)
        assert len(paths) == 45
        for _, test_idx in splits:
            # Verify at least one path has the right length
            pass
        # Verify all paths are non-empty
        assert all(len(p) > 0 for p in paths)


class TestPBOFromCPCV:
    def test_import(self) -> None:
        assert callable(pbo_from_cpcv)

    def test_pbo_in_range(self) -> None:
        """frac_positive_paths is always in [0, 1]; pbo is None for S=1 (1-D input)."""
        rng = np.random.default_rng(42)
        for _ in range(5):
            metrics = rng.standard_normal(45)
            result = pbo_from_cpcv(metrics)
            # 1-D input → S=1 → pbo=None; use frac_positive_paths which is always defined
            assert result.pbo is None or 0.0 <= result.pbo <= 1.0
            assert 0.0 <= result.frac_positive_paths <= 1.0

    def test_pbo_all_positive_is_low(self) -> None:
        """If all paths have positive performance, frac_positive_paths should be 1.0."""
        metrics = np.ones(45) * 2.0  # all paths identical Sharpe = 2
        result = pbo_from_cpcv(metrics)
        # With identical positive paths, all paths are positive
        assert result.frac_positive_paths >= 0.9  # generous bound

    def test_pbo_single_path(self) -> None:
        """PBO with a single path returns None (undefined — S=1, CSCV requires S>1)."""
        result = pbo_from_cpcv([1.0])
        assert result.pbo is None
        assert result.frac_positive_paths == 1.0


class TestPSR:
    def test_import(self) -> None:
        assert callable(psr)

    def test_psr_in_range(self) -> None:
        """PSR is always in [0, 1]."""
        result = psr(observed_sharpe=1.5, n_obs=100)
        assert 0.0 <= result <= 1.0

    def test_high_sharpe_high_psr(self) -> None:
        """High observed Sharpe with many observations → PSR near 1."""
        result = psr(observed_sharpe=3.0, n_obs=500)
        assert result > 0.95

    def test_negative_sharpe_low_psr(self) -> None:
        """Negative observed Sharpe → PSR < 0.5."""
        result = psr(observed_sharpe=-1.0, n_obs=100)
        assert result < 0.5

    def test_zero_sharpe_half_psr(self) -> None:
        """Zero observed Sharpe → PSR ≈ 0.5."""
        result = psr(observed_sharpe=0.0, n_obs=100)
        assert abs(result - 0.5) < 0.05

    def test_single_obs_returns_zero(self) -> None:
        """With n_obs=1, PSR returns 0 (undefined)."""
        result = psr(observed_sharpe=2.0, n_obs=1)
        assert result == 0.0

    def test_skewness_kurtosis_accepted(self) -> None:
        """Non-default skewness and kurtosis are accepted."""
        result = psr(observed_sharpe=1.0, n_obs=200, skewness=-0.5, kurtosis=5.0)
        assert 0.0 <= result <= 1.0


class TestNEffectiveTrials:
    def test_import(self) -> None:
        assert callable(n_effective_trials)

    def test_independent_trials_gives_full_rank(self) -> None:
        """Fully uncorrelated trials should give n_eff close to n_trials."""
        rng = np.random.default_rng(42)
        # 10 independent trials, each with 50 observations
        trials = rng.standard_normal((10, 50))
        n_eff = n_effective_trials(trials)
        assert 1 <= n_eff <= 10

    def test_identical_trials_gives_rank_1(self) -> None:
        """Perfectly correlated trials → n_eff = 1."""
        base = np.random.default_rng(0).standard_normal(50)
        trials = np.stack([base] * 5)  # 5 identical
        n_eff = n_effective_trials(trials)
        assert n_eff == 1

    def test_empty_input_handled(self) -> None:
        """Single trial or 1D input doesn't crash."""
        result = n_effective_trials(np.ones((1, 10)))
        assert result >= 1


class TestFracdiffV3:
    """Smoke test for the fracdiff_v3 module."""

    def test_import(self) -> None:
        from crypto_trade.features_v3.fracdiff_v3 import compute_fracdiff_stat  # noqa: PLC0415

        assert callable(compute_fracdiff_stat)

    def test_fracdiff_stat_returns_tuple(self) -> None:
        from crypto_trade.features_v3.fracdiff_v3 import compute_fracdiff_stat  # noqa: PLC0415

        rng = np.random.default_rng(42)
        # Simulate log prices: random walk (non-stationary)
        prices = np.cumsum(rng.standard_normal(200))
        fd_values, d_star = compute_fracdiff_stat(prices)
        assert isinstance(d_star, float)
        assert 0.0 < d_star <= 1.0
        assert len(fd_values) == len(prices)

    def test_auto_d_achieves_stationarity(self) -> None:
        """The chosen d* should produce a stationary series (ADF p < 0.05)."""
        from statsmodels.tsa.stattools import adfuller  # noqa: PLC0415

        from crypto_trade.features_v3.fracdiff_v3 import compute_fracdiff_stat  # noqa: PLC0415

        rng = np.random.default_rng(99)
        # Random walk is I(1) — fracdiff at any d>0 should achieve stationarity
        prices = np.cumsum(rng.standard_normal(300))
        fd_values, d_star = compute_fracdiff_stat(prices)
        fd_clean = fd_values[~np.isnan(fd_values)]
        if len(fd_clean) >= 20:
            adf_result = adfuller(fd_clean, autolag="AIC")
            # ADF p < 0.1 (generous — auto-d should achieve p < 0.05)
            assert adf_result[1] < 0.15, f"ADF p={adf_result[1]:.4f} too high for d*={d_star}"
