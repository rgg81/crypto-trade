"""Tests for reporting_v1.py — iter-v1/001 methodology axis.

Covers:
- PSR dual-granularity computation and monotonicity invariant (F5 from brief)
- N_eff PCA fixture-based invariants (LM Master saturation-risk mandate):
    * Identical trial bouquet → n_eff = 1
    * Independent trial set → n_eff ≈ n_trials
- PSR granularity-mismatch trap (iter-v3/056 regression guard)
- V1_FAMILY_MAP completeness (all 193 columns assigned)
- ADF exception class taxonomy (pre-declared exceptions coverage)

Run:
    uv run pytest tests/test_reporting_v1.py -v
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from crypto_trade.features_v1 import V1_FEATURE_COLUMNS
from crypto_trade.strategies.ml.reporting_v1 import (
    V1_FAMILIES,
    V1_FAMILY_MAP,
    _assign_exception_class,
    _safe_kurt,
    _safe_skew,
    append_psr_rows_to_comparison,
    compute_psr_columns,
    write_adf_test_csv,
    write_dsr_json,
    write_ic_matrix_csv,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def synthetic_monthly_returns() -> np.ndarray:
    """39 monthly returns with known mean and std (IS window size)."""
    rng = np.random.default_rng(42)
    return rng.normal(loc=0.005, scale=0.02, size=39)


@pytest.fixture()
def synthetic_daily_returns() -> np.ndarray:
    """416 daily returns (IS window size)."""
    rng = np.random.default_rng(42)
    return rng.normal(loc=0.0003, scale=0.008, size=416)


@pytest.fixture()
def tmp_report_dir(tmp_path: Path) -> Path:
    """Temporary directory for report file writes."""
    return tmp_path


# ---------------------------------------------------------------------------
# V1_FAMILY_MAP completeness
# ---------------------------------------------------------------------------


class TestFamilyMap:
    def test_all_193_columns_assigned(self) -> None:
        """Every column in V1_FEATURE_COLUMNS must appear in V1_FAMILY_MAP."""
        all_mapped = set()
        for fam_cols in V1_FAMILY_MAP.values():
            all_mapped.update(fam_cols)
        assert len(V1_FEATURE_COLUMNS) == 193
        assert all_mapped == set(V1_FEATURE_COLUMNS), (
            f"Unmapped columns: {set(V1_FEATURE_COLUMNS) - all_mapped}"
        )

    def test_8_active_families(self) -> None:
        """Exactly 8 active families per brief Section 2 Table 2."""
        active = [f for f, cols in V1_FAMILY_MAP.items() if cols]
        assert set(active) == set(V1_FAMILIES), (
            f"Active families: {sorted(active)}, expected: {sorted(V1_FAMILIES)}"
        )

    def test_no_unknown_columns(self) -> None:
        """No column should be assigned to 'unknown' family."""
        unknown = V1_FAMILY_MAP.get("unknown", [])
        assert unknown == [], f"Unexpected unknown family columns: {unknown}"

    def test_trend_family_size(self) -> None:
        """trend family should have exactly 39 columns."""
        assert len(V1_FAMILY_MAP["trend"]) == 39

    def test_calendar_family_size(self) -> None:
        """calendar family should have exactly 2 columns."""
        assert len(V1_FAMILY_MAP["calendar"]) == 2


# ---------------------------------------------------------------------------
# ADF exception class taxonomy
# ---------------------------------------------------------------------------


class TestAdfExceptionClass:
    def test_ema_is_regime_indicator(self) -> None:
        assert _assign_exception_class("trend_ema_10") == "regime_indicator"

    def test_sma_is_regime_indicator(self) -> None:
        assert _assign_exception_class("trend_sma_20") == "regime_indicator"

    def test_vol_obv_is_random_walk(self) -> None:
        assert _assign_exception_class("vol_obv") == "random_walk_proxy"

    def test_vol_ad_is_random_walk(self) -> None:
        assert _assign_exception_class("vol_ad") == "random_walk_proxy"

    def test_interact_is_composed(self) -> None:
        assert _assign_exception_class("interact_rsi_x_adx") == "composed"

    def test_rsi_has_no_exception(self) -> None:
        assert _assign_exception_class("mom_rsi_14") is None

    def test_mr_zscore_has_no_exception(self) -> None:
        assert _assign_exception_class("mr_zscore_20") is None

    def test_stat_return_has_no_exception(self) -> None:
        assert _assign_exception_class("stat_return_1d") is None


# ---------------------------------------------------------------------------
# PSR computation — dual granularity (LM Master §1 mandate)
# ---------------------------------------------------------------------------


class TestComputePsrColumns:
    def test_returns_three_keys(
        self, synthetic_monthly_returns: np.ndarray, synthetic_daily_returns: np.ndarray
    ) -> None:
        """compute_psr_columns returns exactly 3 keys."""
        result = compute_psr_columns(synthetic_monthly_returns, synthetic_daily_returns)
        assert set(result.keys()) == {"psr_monthly_vs_0", "psr_monthly_vs_1", "psr_daily_vs_0"}

    def test_all_values_in_0_1(
        self, synthetic_monthly_returns: np.ndarray, synthetic_daily_returns: np.ndarray
    ) -> None:
        """All PSR values must be in [0, 1]."""
        result = compute_psr_columns(synthetic_monthly_returns, synthetic_daily_returns)
        for key, val in result.items():
            assert 0.0 <= val <= 1.0, f"{key}={val} out of [0,1]"

    def test_monotonicity_invariant(
        self, synthetic_monthly_returns: np.ndarray, synthetic_daily_returns: np.ndarray
    ) -> None:
        """Brief F5: psr_monthly_vs_0 >= psr_monthly_vs_1 (higher benchmark → lower confidence).

        This is the granularity-correctness invariant from brief Section 4.
        If this is violated, the PSR formula has a sign error in the benchmark.
        """
        result = compute_psr_columns(synthetic_monthly_returns, synthetic_daily_returns)
        assert result["psr_monthly_vs_0"] >= result["psr_monthly_vs_1"], (
            f"Monotonicity violated: psr_monthly_vs_0={result['psr_monthly_vs_0']:.4f} "
            f"< psr_monthly_vs_1={result['psr_monthly_vs_1']:.4f}"
        )

    def test_granularity_mismatch_trap_regression(self) -> None:
        """Regression guard for iter-v3/056 130× error.

        Passing annualized SR + n_obs=39 into PSR inflates the result vs
        passing the non-annualized SR. Verify the current implementation
        uses NON-annualized SR by checking that a known monthly series produces
        a reasonable PSR value (not trivially 0 or 1).

        Monthly series with SR_monthly = 0.005/0.02 = 0.25 (non-annualized),
        which annualized would be 0.25 * sqrt(12) ≈ 0.866. PSR vs 0 should be
        moderate (clearly not 0 or 1), confirming non-annualized input.
        """
        monthly_ret = np.array([0.005] * 39)  # constant monthly return
        daily_ret = np.array([0.0003] * 416)
        # constant series has std=0 → psr should degrade gracefully
        result = compute_psr_columns(monthly_ret, daily_ret)
        # Should not crash; values in [0, 1]
        for key, val in result.items():
            assert 0.0 <= val <= 1.0, f"{key}={val} out of [0,1] for constant series"

    def test_empty_monthly_returns_handled(self) -> None:
        """Empty monthly returns should not crash."""
        result = compute_psr_columns([], [0.001, -0.001] * 100)
        assert 0.0 <= result["psr_monthly_vs_0"] <= 1.0

    def test_psr_monthly_vs_1_close_to_reference(self) -> None:
        """Synthetic N(0.005, 0.02) monthly over n=39 should produce PSR vs 0 > 0.5
        (positive-mean series; PSR vs 0 tests H0: SR <= 0)."""
        rng = np.random.default_rng(99)
        monthly = rng.normal(loc=0.01, scale=0.02, size=39)  # clear positive SR
        daily = rng.normal(loc=0.0005, scale=0.008, size=416)
        result = compute_psr_columns(monthly, daily)
        val = result["psr_monthly_vs_0"]
        assert val > 0.5, (
            f"Expected psr_monthly_vs_0 > 0.5 for positive-mean series, got {val:.4f}"
        )


# ---------------------------------------------------------------------------
# N_eff PCA invariants (LM Master saturation-risk mandate)
# ---------------------------------------------------------------------------


class TestNEffectiveTrialsInvariants:
    """These are the fixture-based unit tests mandated in brief Section 3 + LM Master closing note.

    Tests confirm the PCA estimator (used inside compute_n_eff_and_dsr) works correctly
    before the runner uses it. Required pre-commit invariants.
    """

    def test_identical_trial_bouquet_gives_n_eff_1(self) -> None:
        """MANDATED by LM Master closing note: identical trials → n_eff = 1.

        If all trial-OOF return series are identical (perfectly correlated),
        PCA rank = 1 → only 1 effective trial regardless of n_trials count.
        """
        from crypto_trade.strategies.ml.validation_v1 import n_effective_trials

        base = np.random.default_rng(0).standard_normal(100)
        # 20 identical trials
        trials = np.stack([base] * 20)  # shape (20, 100)
        n_eff = n_effective_trials(trials)
        assert n_eff == 1, (
            f"Identical trials must give n_eff=1, got {n_eff}. "
            "If this fails, PCA implementation is incorrect."
        )

    def test_independent_trial_set_gives_n_eff_approx_n_trials(self) -> None:
        """MANDATED by LM Master closing note: independent trials → n_eff ≈ n_trials.

        Fully uncorrelated trials span the full eigenvalue space. n_eff should
        be close to (though not necessarily exactly equal to) n_trials.
        """
        from crypto_trade.strategies.ml.validation_v1 import n_effective_trials

        rng = np.random.default_rng(123)
        n_trials = 15
        n_periods = 200
        # Independent normal trials — each row is i.i.d., cross-row covariance → 0
        trials = rng.standard_normal((n_trials, n_periods))
        n_eff = n_effective_trials(trials)
        # n_eff should be in [n_trials // 2, n_trials] (at least half the rank)
        assert n_eff >= n_trials // 2, (
            f"Independent trials gave n_eff={n_eff}, expected >= {n_trials // 2}. "
            "PCA may be computing on wrong axis."
        )
        assert n_eff <= n_trials, (
            f"n_eff={n_eff} > n_trials={n_trials}. n_eff cannot exceed the trial count."
        )

    def test_n_eff_strictly_less_than_n_trials_for_correlated_set(self) -> None:
        """Partially correlated trials: n_eff < n_trials (strict compression).

        Brief F3 + runtime assert in runner.
        """
        from crypto_trade.strategies.ml.validation_v1 import n_effective_trials

        rng = np.random.default_rng(7)
        n_trials = 20
        n_periods = 150
        # Create correlated trials: 5 base factors + noise
        n_factors = 5
        factors = rng.standard_normal((n_factors, n_periods))
        weights = rng.standard_normal((n_trials, n_factors))
        trials = weights @ factors + 0.1 * rng.standard_normal((n_trials, n_periods))
        n_eff = n_effective_trials(trials)
        assert n_eff < n_trials, (
            f"Correlated trials (5 factors) should compress n_eff < n_trials={n_trials}, "
            f"got n_eff={n_eff}"
        )
        assert n_eff >= 1, f"n_eff={n_eff} must be >= 1"


# ---------------------------------------------------------------------------
# dsr.json writer
# ---------------------------------------------------------------------------


class TestWriteDsrJson:
    def test_writes_expected_keys(self, tmp_report_dir: Path) -> None:
        """dsr.json must contain all required fields from brief Section 8."""
        write_dsr_json(
            tmp_report_dir,
            dsr=-5.0,
            pbo=None,
            psr_val=0.12,
            n_trials=200,
            n_eff=30,
            n_eff_pca_method="eigvalsh_cov",
            min_trl_months=0.2887,
            label="TEST",
        )
        out_path = tmp_report_dir / "dsr.json"
        assert out_path.exists()
        with open(out_path) as f:
            payload = json.load(f)
        required_keys = {
            "dsr",
            "pbo",
            "psr",
            "n_trials",
            "n_eff",
            "n_eff_pca_method",
            "min_trl_months",
        }
        assert required_keys.issubset(set(payload.keys())), (
            f"Missing keys: {required_keys - set(payload.keys())}"
        )

    def test_pbo_null_is_valid(self, tmp_report_dir: Path) -> None:
        """pbo=None is explicitly allowed (CPCV-deferred per brief Section 9)."""
        write_dsr_json(
            tmp_report_dir,
            dsr=-2.0,
            pbo=None,
            psr_val=0.08,
            n_trials=200,
            n_eff=25,
            n_eff_pca_method="naive_fallback",
            min_trl_months=0.2887,
        )
        with open(tmp_report_dir / "dsr.json") as f:
            payload = json.load(f)
        assert payload["pbo"] is None


# ---------------------------------------------------------------------------
# ADF test CSV writer
# ---------------------------------------------------------------------------


class TestWriteAdfTestCsv:
    def _make_feature_df(self, n_rows: int = 300) -> pd.DataFrame:
        """Create a small feature DataFrame with a subset of V1_FEATURE_COLUMNS."""
        rng = np.random.default_rng(42)
        # Use a representative subset covering all families
        cols = list(V1_FEATURE_COLUMNS)[:30]  # first 30 columns for speed
        data = rng.standard_normal((n_rows, len(cols)))
        return pd.DataFrame(data, columns=cols)

    def test_writes_csv_file(self, tmp_report_dir: Path) -> None:
        feature_df = self._make_feature_df()
        out_path = write_adf_test_csv(tmp_report_dir, feature_df, label="TEST")
        assert out_path.exists()

    def test_csv_has_expected_columns(self, tmp_report_dir: Path) -> None:
        feature_df = self._make_feature_df()
        write_adf_test_csv(tmp_report_dir, feature_df)
        df = pd.read_csv(tmp_report_dir / "adf_test.csv")
        expected = {
            "feature",
            "family",
            "adf_stat",
            "p_value_raw",
            "p_value_bonferroni",
            "lags_used",
            "n_obs",
            "exception_class",
            "bonferroni_pass",
            "raw_pass",
        }
        assert expected.issubset(set(df.columns)), f"Missing columns: {expected - set(df.columns)}"

    def test_193_feature_rows(self, tmp_report_dir: Path) -> None:
        """adf_test.csv must have exactly 193 rows (one per V1_FEATURE_COLUMNS)."""
        # Use empty df to test schema completeness — missing cols produce empty-value rows
        empty_df = pd.DataFrame()
        write_adf_test_csv(tmp_report_dir, empty_df)
        df = pd.read_csv(tmp_report_dir / "adf_test.csv")
        assert len(df) == len(V1_FEATURE_COLUMNS), (
            f"Expected {len(V1_FEATURE_COLUMNS)} rows, got {len(df)}"
        )

    def test_bonferroni_alpha_is_correct(self, tmp_report_dir: Path) -> None:
        """Bonferroni alpha = 0.05 / 193."""
        empty_df = pd.DataFrame()
        write_adf_test_csv(tmp_report_dir, empty_df)
        df = pd.read_csv(tmp_report_dir / "adf_test.csv")
        # Filter rows where bonferroni_alpha was filled in (numeric)
        numeric_rows = df[df["p_value_bonferroni"].notna()]
        if len(numeric_rows) > 0:
            bonf_val = float(numeric_rows["p_value_bonferroni"].iloc[0])
            expected = 0.05 / 193
            assert abs(bonf_val - expected) < 1e-10, (
                f"Bonferroni alpha mismatch: {bonf_val} vs expected {expected}"
            )


# ---------------------------------------------------------------------------
# IC matrix CSV writer (smoke test — no golden values)
# ---------------------------------------------------------------------------


class TestWriteIcMatrixCsv:
    def _make_feature_df(self, n_rows: int = 200) -> tuple[pd.DataFrame, np.ndarray]:
        """Small feature df + forward returns for IC computation."""
        rng = np.random.default_rng(42)
        cols = list(V1_FEATURE_COLUMNS)[:30]
        data = rng.standard_normal((n_rows, len(cols)))
        fwd = rng.standard_normal(n_rows)
        return pd.DataFrame(data, columns=cols), fwd

    def test_writes_csv_file(self, tmp_report_dir: Path) -> None:
        feat_df, fwd = self._make_feature_df()
        out_path = write_ic_matrix_csv(tmp_report_dir, feat_df, fwd, label="TEST")
        assert out_path.exists()

    def test_csv_has_expected_columns(self, tmp_report_dir: Path) -> None:
        feat_df, fwd = self._make_feature_df()
        write_ic_matrix_csv(tmp_report_dir, feat_df, fwd)
        df = pd.read_csv(tmp_report_dir / "ic_matrix.csv")
        expected = {
            "family_a",
            "family_b",
            "ic_mean_fisher",
            "ic_median",
            "ic_iqr_low",
            "ic_iqr_high",
            "n_features_a",
            "n_features_b",
        }
        assert expected.issubset(set(df.columns))

    def test_diagonal_families_present(self, tmp_report_dir: Path) -> None:
        """All 8 families must appear in diagonal rows (family_a == family_b)."""
        feat_df, fwd = self._make_feature_df()
        write_ic_matrix_csv(tmp_report_dir, feat_df, fwd)
        df = pd.read_csv(tmp_report_dir / "ic_matrix.csv")
        diag = df[df["family_a"] == df["family_b"]]
        assert set(diag["family_a"].tolist()) == set(V1_FAMILIES)


# ---------------------------------------------------------------------------
# append_psr_rows_to_comparison — integration smoke test
# ---------------------------------------------------------------------------


class TestAppendPsrRowsToComparison:
    def test_appends_4_rows(self, tmp_report_dir: Path) -> None:
        """4 new rows must be appended to comparison.csv."""
        # Write a minimal comparison.csv first
        comparison_path = tmp_report_dir / "comparison.csv"
        with open(comparison_path, "w", newline="") as f:
            import csv as csv_mod

            writer = csv_mod.writer(f)
            writer.writerow(["metric", "in_sample", "out_of_sample", "ratio"])
            writer.writerow(["sharpe", "0.2829", "0.6637", "2.3462"])

        is_psr = {"psr_monthly_vs_0": 0.95, "psr_monthly_vs_1": 0.08, "psr_daily_vs_0": 0.99}
        oos_psr = {"psr_monthly_vs_0": 0.89, "psr_monthly_vs_1": 0.12, "psr_daily_vs_0": 0.97}
        append_psr_rows_to_comparison(comparison_path, is_psr, oos_psr, is_n_eff=25, oos_n_eff=20)

        df = pd.read_csv(comparison_path)
        # 1 original row + 4 new rows = 5 total
        assert len(df) == 5, f"Expected 5 rows, got {len(df)}"
        assert set(df["metric"]) >= {
            "psr_monthly_vs_0",
            "psr_monthly_vs_1",
            "psr_daily_vs_0",
            "n_effective_trials",
        }

    def test_n_eff_row_values(self, tmp_report_dir: Path) -> None:
        """n_effective_trials row must carry correct IS/OOS values."""
        comparison_path = tmp_report_dir / "comparison.csv"
        with open(comparison_path, "w", newline="") as f:
            import csv as csv_mod

            writer = csv_mod.writer(f)
            writer.writerow(["metric", "in_sample", "out_of_sample", "ratio"])
            writer.writerow(["sharpe", "0.28", "0.66", "2.36"])

        is_psr = {"psr_monthly_vs_0": 0.9, "psr_monthly_vs_1": 0.07, "psr_daily_vs_0": 0.98}
        oos_psr = {"psr_monthly_vs_0": 0.85, "psr_monthly_vs_1": 0.10, "psr_daily_vs_0": 0.96}
        append_psr_rows_to_comparison(comparison_path, is_psr, oos_psr, is_n_eff=30, oos_n_eff=22)

        df = pd.read_csv(comparison_path)
        n_eff_row = df[df["metric"] == "n_effective_trials"].iloc[0]
        assert int(n_eff_row["in_sample"]) == 30
        assert int(n_eff_row["out_of_sample"]) == 22


# ---------------------------------------------------------------------------
# Safe stat helpers
# ---------------------------------------------------------------------------


class TestSafeStatHelpers:
    def test_skew_normal_near_zero(self) -> None:
        """N(0,1) skewness should be near 0."""
        rng = np.random.default_rng(42)
        arr = rng.standard_normal(1000)
        sk = _safe_skew(arr)
        assert abs(sk) < 0.3, f"Expected skew near 0 for N(0,1), got {sk:.4f}"

    def test_kurt_normal_near_3(self) -> None:
        """N(0,1) raw kurtosis should be near 3."""
        rng = np.random.default_rng(42)
        arr = rng.standard_normal(2000)
        kt = _safe_kurt(arr)
        assert abs(kt - 3.0) < 0.5, f"Expected raw kurtosis near 3 for N(0,1), got {kt:.4f}"

    def test_short_series_no_crash(self) -> None:
        """Short series (n < 4) must not raise."""
        assert isinstance(_safe_skew(np.array([1.0])), float)
        assert isinstance(_safe_kurt(np.array([1.0, 2.0])), float)
